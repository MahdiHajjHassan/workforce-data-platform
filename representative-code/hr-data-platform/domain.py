"""Workforce validation and dataset contracts for the independent local product."""
import csv
from datetime import date, datetime, timezone
import io
import math
import re

AS_OF = date(2026, 10, 11)
FIELDS = ['worker_id', 'name', 'country', 'department', 'employment_type', 'fte', 'annual_salary', 'hire_date', 'updated_at']
COUNTRIES = {'LB': 'Lebanon', 'FR': 'France', 'DE': 'Germany'}
DEPARTMENTS = ['Engineering', 'Operations', 'Finance', 'People', 'Product']
CONTRACTS = {
    'hr': {'label': 'HR analytics', 'purpose': 'Workforce reporting', 'countries': list(COUNTRIES), 'fields': FIELDS + ['tenure_months']},
    'operations': {'label': 'Operations planning', 'purpose': 'Approved workforce planning', 'countries': ['LB', 'FR'], 'fields': ['worker_id', 'country', 'department', 'employment_type', 'fte']},
    'training': {'label': 'Model development', 'purpose': 'Training dataset preparation', 'countries': list(COUNTRIES), 'fields': ['country', 'department', 'employment_type', 'fte', 'tenure_months']},
}
ALIASES = dict(zip(FIELDS, ['worker_code', 'full_name', 'location', 'team', 'contract', 'workload', 'salary', 'started', 'modified']))


def csv_text(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: "'" + value if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')) else value for key, value in row.items()})
    return stream.getvalue()


def normalize(row):
    if None in row or any(row.get(key) is None for key in FIELDS):
        raise ValueError('Row has an incorrect number of columns')
    result = {key: str(row[key]).strip() for key in FIELDS}
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,30}', result['worker_id']):
        raise ValueError('worker_id must be a short alphanumeric key')
    if not result['name'] or len(result['name']) > 80:
        raise ValueError('name is required and limited to 80 characters')
    result['country'] = result['country'].upper()
    if result['country'] not in COUNTRIES:
        raise ValueError('country must be LB, FR, or DE')
    if result['department'] not in DEPARTMENTS:
        raise ValueError('department must match an approved department')
    result['employment_type'] = result['employment_type'].lower()
    if result['employment_type'] not in ('employee', 'contractor', 'intern'):
        raise ValueError('employment_type must be employee, contractor, or intern')
    for key, low, high in [('fte', 0, 1), ('annual_salary', 0, 1000000)]:
        try:
            value = float(result[key])
        except (TypeError, ValueError):
            raise ValueError(f'{key} must be numeric') from None
        if not math.isfinite(value) or not low <= value <= high or (key == 'fte' and value == 0):
            raise ValueError(f'{key} is outside the accepted range')
        result[key] = value
    try:
        hired = date.fromisoformat(result['hire_date'])
        updated = datetime.fromisoformat(result['updated_at'].replace('Z', '+00:00'))
        if hired > AS_OF or hired.year < 1950 or updated.tzinfo is None:
            raise ValueError
        updated = updated.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise ValueError('hire_date must precede 2026-10-11; updated_at must include a timezone') from None
    result['updated_at'] = updated.isoformat()
    result['tenure_months'] = max(0, (AS_OF.year - hired.year) * 12 + AS_OF.month - hired.month - (AS_OF.day < hired.day))
    return result


def prepare(content, mapping=None):
    if not isinstance(content, str) or not content.strip() or len(content) > 300000:
        raise ValueError('Supply a nonempty CSV under 300,000 characters')
    try:
        reader = csv.DictReader(io.StringIO(content.lstrip('\ufeff')), strict=True)
        columns = reader.fieldnames
        if not columns or len(set(columns)) != len(columns):
            raise ValueError('CSV headers must be present and unique')
        if mapping is None:
            mapping = {field: field if field in columns else ALIASES[field] if ALIASES[field] in columns else '' for field in FIELDS}
        if not isinstance(mapping, dict) or set(mapping) != set(FIELDS) or any(value not in columns for value in mapping.values()) or len(set(mapping.values())) != len(FIELDS):
            raise ValueError('Map every required field to a unique CSV column')
        raw_rows = list(reader)
    except csv.Error:
        raise ValueError('CSV quoting is malformed') from None
    if not 1 <= len(raw_rows) <= 2000:
        raise ValueError('Supply between 1 and 2,000 rows')
    prepared = []
    for index, source in enumerate(raw_rows, 2):
        raw = {key: source.get(value) for key, value in mapping.items()}
        try:
            if None in source:
                raise ValueError('Row has more values than its header')
            prepared.append({'row_number': index, 'raw': raw, 'record': normalize(raw), 'reason': ''})
        except ValueError as error:
            prepared.append({'row_number': index, 'raw': raw, 'record': None, 'reason': str(error)})
    return columns, mapping, prepared
