"""Exercise actual CLI processes after copying the package out of the workspace."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def verify():
    with tempfile.TemporaryDirectory() as task_dir:
        destination = Path(task_dir) / 'standalone'
        destination.mkdir()
        for item in ['service.py', 'domain.py', 'cli.py', 'warehouse.sql', 'migrations', 'fixtures']:
            source = ROOT / item
            if source.is_dir():
                shutil.copytree(source, destination / item, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copy2(source, destination / item)
        data_dir = Path(task_dir) / 'data'
        output = Path(task_dir) / 'delivery'

        def cli(*arguments):
            process = subprocess.run([sys.executable, str(destination / 'cli.py'), '--data-dir', str(data_dir), *arguments], cwd=destination, text=True, capture_output=True, check=True)
            return json.loads(process.stdout)

        initial = cli('status')
        assert initial['summary']['headcount'] == 50
        imported = cli('import', 'fixtures/vendor-mapping.csv', '--label', 'Verified CLI vendor feed')
        assert imported['accepted'] == 3
        rejected = initial['quarantine'][0]
        corrected = {'country': 'DE'} if rejected['raw']['country'] == 'GER' else {'fte': 1}
        patch = Path(task_dir) / 'correction.json'
        patch.write_text(json.dumps(corrected))
        result = cli('recover', str(rejected['id']), '--record', str(patch))
        assert result['promoted'] == 1
        delivery = cli('export', '--recipient', 'operations', '--countries', 'LB', 'FR', '--output', str(output))
        assert delivery['row_count'] > 0
        training = cli('training', '--output', str(output))
        dataset = Path(training['dataset_file'])
        manifest = json.loads(Path(training['manifest_file']).read_text())
        assert hashlib.sha256(dataset.read_bytes()).hexdigest() == manifest['sha256']
        assert sum(manifest['splits'].values()) == manifest['row_count']
        state = cli('status')
        assert state['summary']['headcount'] == 51
        assert state['summary']['quarantined'] == 1
        print(json.dumps({'standalone_cli': 'passed', 'imported': imported['received'], 'recovered_run': result['run_id'], 'scoped_rows': delivery['row_count'], 'training_rows': training['row_count'], 'csv_manifest_sha256': 'matched'}, indent=2))


if __name__ == '__main__':
    verify()
