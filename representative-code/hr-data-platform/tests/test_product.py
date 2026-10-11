import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service import Product
from domain import FIELDS, csv_text


class ProductTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.product = Product(Path(self.temp.name))

    def tearDown(self):
        self.temp.cleanup()

    def row(self, **patch):
        return {**self.product.state()['workforce'][0], **patch}

    def test_latest_timestamp_wins_and_warehouse_reconciles(self):
        row = self.row(fte=.4, updated_at='2026-10-11T09:00:00Z')
        newer = self.product.action('import_csv', {'csv': csv_text([row], FIELDS)})
        stale = self.product.action('import_csv', {'csv': csv_text([self.row(fte=.8, updated_at='2025-01-01T08:00:00Z')], FIELDS)})
        state = Product(Path(self.temp.name)).state()
        self.assertEqual(newer['promoted'], 1)
        self.assertEqual(stale['superseded'], 1)
        self.assertEqual(state['workforce'][0]['fte'], .4)
        self.assertAlmostEqual(sum(x['fte'] for x in state['departments']), state['summary']['fte'])
        self.assertEqual(sum(x['headcount'] for x in state['departments']), len(state['workforce']))

    def test_quarantine_repair_is_validated_and_persisted(self):
        result = self.product.action('import_csv', {'csv': csv_text([self.row(worker_id='W999', fte='broken')], FIELDS)})
        self.assertEqual(result['quarantined'], 1)
        item = next(x for x in self.product.state()['quarantine'] if x['raw']['worker_id'] == 'W999')
        with self.assertRaises(ValueError):
            self.product.action('recover', {'id': item['id'], 'record': {'fte': 2}})
        self.assertTrue(any(x['id'] == item['id'] for x in self.product.state()['quarantine']))
        self.product.action('recover', {'id': item['id'], 'record': {'fte': .75}})
        state = Product(Path(self.temp.name)).state()
        self.assertTrue(any(x['worker_id'] == 'W999' and x['fte'] == .75 for x in state['workforce']))
        self.assertFalse(any(x['id'] == item['id'] for x in state['quarantine']))
        with self.assertRaises(ValueError):
            self.product.action('recover', {'id': item['id'], 'record': {'fte': .75}})

    def test_mapping_preview_has_no_side_effect_and_import_uses_mapping(self):
        row = self.row(worker_id='M001')
        aliases = {field: f'input_{field}' for field in FIELDS}
        content = csv_text([{aliases[k]: row[k] for k in FIELDS}], list(aliases.values()))
        before = len(self.product.state()['runs'])
        preview = self.product.action('inspect_csv', {'csv': content, 'mapping': aliases})
        self.assertEqual(preview['accepted'], 1)
        self.assertEqual(len(self.product.state()['runs']), before)
        result = self.product.action('import_csv', {'csv': content, 'mapping': aliases})
        self.assertEqual(result['promoted'], 1)
        self.assertTrue(any(x['worker_id'] == 'M001' for x in self.product.state()['workforce']))

    def test_scope_denial_is_atomic_and_audited(self):
        with self.assertRaises(PermissionError):
            self.product.action('export', {'recipient': 'operations', 'countries': ['LB', 'DE']})
        delivery = self.product.state()['deliveries'][0]
        self.assertEqual(delivery['decision'], 'denied')
        self.assertEqual(delivery['row_count'], 0)
        with self.assertRaises(PermissionError):
            self.product.action('preview', {'recipient': 'training', 'countries': ['LB'], 'fields': ['name']})

    def test_training_dataset_manifest_matches_bytes_and_no_identity(self):
        result = self.product.action('training_export', {'countries': ['LB', 'FR', 'DE']})
        rows = list(csv.DictReader(io.StringIO(result['content'])))
        self.assertNotIn('worker_id', rows[0])
        self.assertNotIn('name', rows[0])
        self.assertNotIn('annual_salary', rows[0])
        self.assertEqual(result['manifest']['sha256'], hashlib.sha256(result['content'].encode()).hexdigest())
        self.assertEqual(result['manifest']['row_count'], len(rows))
        self.assertEqual(sum(result['manifest']['splits'].values()), len(rows))
        again = self.product.action('training_export', {'countries': ['LB', 'FR', 'DE']})
        self.assertEqual(result['content'], again['content'])
        self.assertEqual(result['manifest']['sha256'], again['manifest']['sha256'])

    def test_invalid_batch_header_writes_no_run(self):
        before = len(self.product.state()['runs'])
        with self.assertRaises(ValueError):
            self.product.action('import_csv', {'csv': 'worker_id,worker_id\nW01,W02'})
        self.assertEqual(len(self.product.state()['runs']), before)

    def test_csv_export_escapes_spreadsheet_formula(self):
        result = self.product.action('import_csv', {'csv': csv_text([self.row(worker_id='SAFE1', name='=2+2')], FIELDS).replace("'=2+2", '=2+2')})
        export = self.product.action('export', {'recipient': 'hr', 'countries': ['LB', 'FR', 'DE']})
        self.assertIn("'=2+2", export['content'])

    def test_staging_reports_promoted_and_superseded_rows(self):
        result = self.product.action('import_csv', {'csv': csv_text([self.row(updated_at='2020-01-01T00:00:00Z')], FIELDS)})
        detail = self.product.action('run_detail', {'id': result['run_id']})
        self.assertEqual(detail['rows'][0]['status'], 'superseded')
        self.assertTrue(detail['run']['trace'])


if __name__ == '__main__':
    unittest.main()
