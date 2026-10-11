PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
 id INTEGER PRIMARY KEY, label TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL,
 received INTEGER NOT NULL, accepted INTEGER NOT NULL, quarantined INTEGER NOT NULL,
 duplicates INTEGER NOT NULL DEFAULT 0, promoted INTEGER NOT NULL DEFAULT 0, superseded INTEGER NOT NULL DEFAULT 0,
 mapping TEXT NOT NULL, source_sha256 TEXT NOT NULL, trace TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS staging(
 id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id), row_number INTEGER NOT NULL,
 raw TEXT NOT NULL, status TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '', recovered_run_id INTEGER REFERENCES runs(id)
);
CREATE INDEX IF NOT EXISTS staging_run ON staging(run_id);
CREATE TABLE IF NOT EXISTS workforce(
 worker_id TEXT PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL, department TEXT NOT NULL,
 employment_type TEXT NOT NULL, fte REAL NOT NULL CHECK(fte > 0 AND fte <= 1), annual_salary REAL NOT NULL,
 hire_date TEXT NOT NULL, updated_at TEXT NOT NULL, tenure_months INTEGER NOT NULL,
 source_run_id INTEGER NOT NULL REFERENCES runs(id)
);
CREATE INDEX IF NOT EXISTS workforce_scope ON workforce(country, department);
CREATE TABLE IF NOT EXISTS warehouse_department(department TEXT PRIMARY KEY, headcount INTEGER NOT NULL, fte REAL NOT NULL, employees INTEGER NOT NULL, contractors INTEGER NOT NULL, interns INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS warehouse_country(country TEXT PRIMARY KEY, headcount INTEGER NOT NULL, fte REAL NOT NULL);
CREATE TABLE IF NOT EXISTS deliveries(
 id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, recipient TEXT NOT NULL, countries TEXT NOT NULL,
 fields TEXT NOT NULL, decision TEXT NOT NULL, row_count INTEGER NOT NULL, reason TEXT NOT NULL,
 kind TEXT NOT NULL, manifest TEXT NOT NULL
);
