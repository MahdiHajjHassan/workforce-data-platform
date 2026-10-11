"""Transactional ingestion, warehouse reporting and scoped dataset delivery."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from domain import AS_OF, FIELDS, COUNTRIES, CONTRACTS, DEPARTMENTS, normalize, prepare, csv_text

ROOT = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


class Product:
    def __init__(self, data_dir):
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / 'workforce.sqlite3'
        with self.db() as db:
            db.executescript((ROOT / 'migrations/001_initial.sql').read_text())
            db.execute('INSERT OR IGNORE INTO schema_migrations VALUES(1,?)', (now(),))
            empty = db.execute('SELECT COUNT(*) FROM runs').fetchone()[0] == 0
        if empty:
            self.import_csv((ROOT / 'fixtures/workforce.csv').read_text(), 'Workforce baseline · October 2026')
            self.import_csv((ROOT / 'fixtures/adjustments.csv').read_text(), 'October workforce adjustments')

    @contextmanager
    def db(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _persist(self, db, prepared, label, mapping, digest):
        accepted = sum(x['record'] is not None for x in prepared)
        rejected = len(prepared) - accepted
        run_id = db.execute('INSERT INTO runs(label,created_at,status,received,accepted,quarantined,mapping,source_sha256,trace) VALUES(?,?,?,?,?,?,?,?,?)',
            (label[:120], now(), 'completed_with_warning' if rejected else 'completed', len(prepared), accepted, rejected, json.dumps(mapping), digest, '[]')).lastrowid
        duplicates = promoted = superseded = 0
        for item in prepared:
            record = item['record']
            status = 'quarantined'
            if record:
                old = db.execute('SELECT updated_at FROM workforce WHERE worker_id=?', (record['worker_id'],)).fetchone()
                duplicates += int(old is not None)
                if old is None or record['updated_at'] >= old['updated_at']:
                    columns = FIELDS + ['tenure_months', 'source_run_id']
                    db.execute(f"INSERT OR REPLACE INTO workforce({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", tuple(record[k] for k in columns[:-1]) + (run_id,))
                    promoted += 1
                    status = 'promoted'
                else:
                    superseded += 1
                    status = 'superseded'
            db.execute('INSERT INTO staging(run_id,row_number,raw,status,reason) VALUES(?,?,?,?,?)', (run_id, item['row_number'], json.dumps(item['raw']), status, item['reason']))
        # Execute each statement within the same transaction as ingestion.
        for sql in (ROOT / 'warehouse.sql').read_text().split(';'):
            if sql.strip():
                db.execute(sql)
        count = db.execute('SELECT COUNT(*) FROM workforce').fetchone()[0]
        trace = [
            {'stage': 'Receive', 'status': 'completed', 'detail': f'{len(prepared)} source rows staged; source checksum saved'},
            {'stage': 'Validate', 'status': 'warning' if rejected else 'completed', 'detail': f'{accepted} valid records; {rejected} quarantined'},
            {'stage': 'Reconcile', 'status': 'completed', 'detail': f'{promoted} promoted; {superseded} older records retained in staging'},
            {'stage': 'Warehouse', 'status': 'completed', 'detail': f'{count} unique workers; department and country measures rebuilt in SQL'},
        ]
        db.execute('UPDATE runs SET duplicates=?,promoted=?,superseded=?,trace=? WHERE id=?', (duplicates, promoted, superseded, json.dumps(trace), run_id))
        return {'run_id': run_id, 'received': len(prepared), 'accepted': accepted, 'quarantined': rejected, 'promoted': promoted, 'duplicates': duplicates, 'superseded': superseded, 'status': 'completed_with_warning' if rejected else 'completed'}

    def import_csv(self, content, label='Workforce CSV import', mapping=None):
        _, mapping, rows = prepare(content, mapping)
        if not isinstance(label, str) or not label.strip():
            raise ValueError('Provide a batch label')
        with self.db() as db:
            return self._persist(db, rows, label, mapping, hashlib.sha256(content.encode()).hexdigest())

    def recover(self, payload):
        if not isinstance(payload.get('record'), dict) or not isinstance(payload.get('id'), int):
            raise ValueError('Provide the quarantine row id and corrected field values')
        if set(payload['record']) - set(FIELDS):
            raise ValueError('Unknown corrected field')
        with self.db() as db:
            item = db.execute("SELECT * FROM staging WHERE id=? AND status='quarantined'", (payload['id'],)).fetchone()
            if not item:
                raise ValueError('This row is no longer in quarantine')
            raw = {**json.loads(item['raw']), **payload['record']}
            record = normalize(raw)
            result = self._persist(db, [{'row_number': item['row_number'], 'raw': raw, 'record': record, 'reason': ''}], f"Recovered row {item['id']} from batch {item['run_id']}", {x: x for x in FIELDS}, hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest())
            db.execute("UPDATE staging SET status='recovered',recovered_run_id=? WHERE id=?", (result['run_id'], item['id']))
        return {**result, 'recovered_id': item['id']}

    def delivery(self, payload, kind):
        recipient = 'training' if kind == 'training' else payload.get('recipient')
        if recipient not in CONTRACTS:
            raise ValueError('Choose an approved recipient')
        countries = payload.get('countries')
        if not isinstance(countries, list) or not countries or any(not isinstance(x, str) for x in countries):
            raise ValueError('Select at least one country')
        countries = list(dict.fromkeys(x.upper() for x in countries))
        contract = CONTRACTS[recipient]
        fields = payload.get('fields', contract['fields'])
        if kind == 'training':
            fields = contract['fields']
        if not isinstance(fields, list) or not fields or any(not isinstance(x, str) for x in fields):
            raise ValueError('Select at least one field')
        fields = list(dict.fromkeys(fields))
        reason = ''
        if set(countries) - set(contract['countries']):
            reason = 'Country scope denied: ' + ', '.join(sorted(set(countries) - set(contract['countries'])))
        elif set(fields) - set(contract['fields']):
            reason = 'Field scope denied: ' + ', '.join(sorted(set(fields) - set(contract['fields'])))
        with self.db() as db:
            source = [dict(x) for x in db.execute('SELECT * FROM workforce ORDER BY worker_id')]
            rows = [{field: row[field] for field in fields} for row in source if row['country'] in countries] if not reason else []
            if kind == 'training' and not reason:
                scoped = [row for row in source if row['country'] in countries]
                rows = [{**row, 'split': 'validation' if int(hashlib.sha256(scoped[i]['worker_id'].encode()).hexdigest()[:8], 16) % 5 == 0 else 'train'} for i, row in enumerate(rows)]
            columns = fields + (['split'] if kind == 'training' else [])
            content = csv_text(rows, columns)
            manifest = {'format_version': 1, 'dataset': 'workforce-training' if kind == 'training' else f'workforce-{recipient}', 'as_of': AS_OF.isoformat(), 'recipient': recipient, 'purpose': contract['purpose'], 'countries': countries, 'columns': columns, 'row_count': len(rows), 'sha256': hashlib.sha256(content.encode()).hexdigest(), 'source_run_ids': sorted({x['source_run_id'] for x in source if x['country'] in countries}) if not reason else [], 'implementation': 'Independent local HR Data Platform', 'data_origin': 'Fictional fixtures and local imports'}
            if kind == 'training':
                manifest.update({'excluded_fields': ['worker_id', 'name', 'annual_salary', 'hire_date', 'updated_at'], 'splits': {split: sum(x['split'] == split for x in rows) for split in ['train', 'validation']}, 'split_rule': 'SHA-256(worker_id) modulo 5; bucket 0 is validation; identifier omitted from output', 'feature_types': {'country': 'categorical', 'department': 'categorical', 'employment_type': 'categorical', 'fte': 'float', 'tenure_months': 'integer', 'split': 'categorical'}})
            delivery_id = db.execute('INSERT INTO deliveries(created_at,recipient,countries,fields,decision,row_count,reason,kind,manifest) VALUES(?,?,?,?,?,?,?,?,?)', (now(), recipient, json.dumps(countries), json.dumps(fields), 'denied' if reason else 'approved', len(rows), reason or contract['purpose'], kind, json.dumps(manifest))).lastrowid
        if reason:
            raise PermissionError(reason + '. The entire dataset request was refused.')
        return {'delivery_id': delivery_id, 'recipient': recipient, 'countries': countries, 'fields': columns, 'rows': rows, 'filename': manifest['dataset'] + '.csv', 'content': content, 'mime': 'text/csv', 'manifest': manifest}

    def _run(self, row):
        return {**dict(row), 'mapping': json.loads(row['mapping']), 'trace': json.loads(row['trace'])}

    def state(self):
        with self.db() as db:
            runs = [self._run(x) for x in db.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 100')]
            workforce = [dict(x) for x in db.execute('SELECT * FROM workforce ORDER BY worker_id')]
            quarantine = [{**dict(x), 'raw': json.loads(x['raw'])} for x in db.execute("SELECT * FROM staging WHERE status='quarantined' ORDER BY id DESC")]
            deliveries = [{**dict(x), 'countries': json.loads(x['countries']), 'fields': json.loads(x['fields']), 'manifest': json.loads(x['manifest'])} for x in db.execute('SELECT * FROM deliveries ORDER BY id DESC LIMIT 100')]
            departments = [dict(x) for x in db.execute('SELECT * FROM warehouse_department ORDER BY headcount DESC, department')]
            countries = [dict(x) for x in db.execute('SELECT * FROM warehouse_country ORDER BY country')]
        return {'as_of': AS_OF.isoformat(), 'fields': FIELDS, 'country_names': COUNTRIES, 'department_names': DEPARTMENTS, 'contracts': CONTRACTS, 'workforce': workforce, 'ods': workforce, 'quarantine': quarantine, 'runs': runs, 'deliveries': deliveries, 'departments': departments, 'countries': countries, 'summary': {'headcount': len(workforce), 'fte': round(sum(x['fte'] for x in workforce), 2), 'quarantined': len(quarantine), 'recovered': sum(1 for x in runs if x['label'].startswith('Recovered')), 'last_run': runs[0]['id'] if runs else None}, 'sample_csv': (ROOT / 'fixtures/adjustments.csv').read_text(), 'mapped_csv': (ROOT / 'fixtures/vendor-mapping.csv').read_text(), 'sql': (ROOT / 'warehouse.sql').read_text()}

    def action(self, name, payload):
        if not isinstance(payload, dict):
            raise ValueError('Provide an object payload')
        if name == 'inspect_csv':
            columns, mapping, rows = prepare(payload.get('csv'), payload.get('mapping'))
            return {'columns': columns, 'mapping': mapping, 'received': len(rows), 'accepted': sum(x['record'] is not None for x in rows), 'quarantined': sum(x['record'] is None for x in rows), 'rows': rows[:12]}
        if name == 'import_csv':
            return self.import_csv(payload.get('csv'), payload.get('label', 'Workforce CSV import'), payload.get('mapping'))
        if name == 'recover':
            return self.recover(payload)
        if name in ('preview', 'export', 'training_export'):
            return self.delivery(payload, 'training' if name == 'training_export' else name)
        if name == 'run_detail':
            if not isinstance(payload.get('id'), int):
                raise ValueError('Provide a run id')
            with self.db() as db:
                run = db.execute('SELECT * FROM runs WHERE id=?', (payload['id'],)).fetchone()
                if not run:
                    raise ValueError('Run not found')
                rows = [{**dict(x), 'raw': json.loads(x['raw'])} for x in db.execute('SELECT * FROM staging WHERE run_id=? ORDER BY row_number', (payload['id'],))]
            return {'run': self._run(run), 'rows': rows}
        if name == 'reset':
            with self.db() as db:
                for table in ['deliveries', 'staging', 'workforce', 'warehouse_department', 'warehouse_country', 'runs']:
                    db.execute(f'DELETE FROM {table}')
            result = self.import_csv((ROOT / 'fixtures/workforce.csv').read_text(), 'Workforce baseline · October 2026')
            return self.import_csv((ROOT / 'fixtures/adjustments.csv').read_text(), 'October workforce adjustments')
        raise ValueError('Unknown HR action')
