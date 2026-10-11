"""Rebuild the product's deterministic fictional input files."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from domain import FIELDS, ALIASES, csv_text

first = ['Mira', 'Nora', 'Eli', 'Sami', 'Lea', 'Adam', 'Lina', 'Noel', 'Yara', 'Theo', 'Rami', 'Dana']
last = ['Cedar', 'Birch', 'Pine', 'Vale']
teams = ['Engineering'] * 16 + ['Operations'] * 10 + ['Product'] * 8 + ['Finance'] * 8 + ['People'] * 6
rows = []
for i in range(48):
    kind = 'intern' if i % 12 == 11 else 'contractor' if i % 6 == 4 else 'employee'
    rows.append({'worker_id': f'W{i+1:03}', 'name': f'{first[i % 12]} {last[i // 12]}', 'country': 'LB' if i < 24 else 'FR' if i < 38 else 'DE', 'department': teams[i], 'employment_type': kind, 'fte': .6 if kind == 'intern' else .8 if kind == 'contractor' else 1, 'annual_salary': 24000 + (i % 16) * 2400, 'hire_date': f'202{1+i%5}-{1+i%9:02}-15', 'updated_at': '2026-10-01T08:00:00Z'})
(ROOT / 'fixtures/workforce.csv').write_text(csv_text(rows, FIELDS), encoding='utf-8')
changes = [
    {**rows[0], 'annual_salary': 42000, 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[5], 'fte': .8, 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[27], 'department': 'Product', 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[2], 'worker_id': 'W049', 'name': 'Lara Ash', 'department': 'People', 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[39], 'worker_id': 'W050', 'name': 'Paul Reed', 'department': 'Engineering', 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[10], 'worker_id': 'W051', 'name': 'Rita Elm', 'fte': 'full-time', 'updated_at': '2026-10-11T09:00:00Z'},
    {**rows[40], 'worker_id': 'W052', 'name': 'Alex Maple', 'country': 'GER', 'updated_at': '2026-10-11T09:00:00Z'},
]
(ROOT / 'fixtures/adjustments.csv').write_text(csv_text(changes, FIELDS), encoding='utf-8')
(ROOT / 'fixtures/vendor-mapping.csv').write_text(csv_text([{ALIASES[k]: row[k] for k in FIELDS} for row in changes[:3]], list(ALIASES.values())), encoding='utf-8')
