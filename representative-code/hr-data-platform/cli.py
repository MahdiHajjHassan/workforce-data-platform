"""Command-line entry to the same persisted workflows as the web workbench."""
import argparse
import json
from pathlib import Path

from service import Product


def main():
    parser = argparse.ArgumentParser(description='HR Data Platform local workflows')
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent / '.product-data')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    imp = commands.add_parser('import')
    imp.add_argument('file', type=Path)
    imp.add_argument('--label', default='CLI workforce import')
    imp.add_argument('--mapping', type=Path, help='JSON object mapping canonical fields to source columns')
    inspect = commands.add_parser('inspect')
    inspect.add_argument('file', type=Path)
    recover = commands.add_parser('recover')
    recover.add_argument('id', type=int)
    recover.add_argument('--record', type=Path, required=True, help='JSON object of corrected fields')
    export = commands.add_parser('export')
    export.add_argument('--recipient', choices=['hr', 'operations', 'training'], default='operations')
    export.add_argument('--countries', nargs='+', default=['LB', 'FR'])
    export.add_argument('--output', type=Path, default=Path('output'))
    train = commands.add_parser('training')
    train.add_argument('--countries', nargs='+', default=['LB', 'FR', 'DE'])
    train.add_argument('--output', type=Path, default=Path('output'))
    detail = commands.add_parser('run')
    detail.add_argument('id', type=int)
    args = parser.parse_args()
    product = Product(args.data_dir)
    if args.command == 'status':
        state = product.state()
        result = {key: state[key] for key in ['summary', 'departments', 'countries', 'quarantine', 'runs']}
    elif args.command in ['import', 'inspect']:
        payload = {'csv': args.file.read_text(encoding='utf-8-sig')}
        if args.command == 'import':
            payload.update({'label': args.label})
            if args.mapping:
                payload['mapping'] = json.loads(args.mapping.read_text())
        result = product.action('import_csv' if args.command == 'import' else 'inspect_csv', payload)
    elif args.command == 'recover':
        result = product.action('recover', {'id': args.id, 'record': json.loads(args.record.read_text())})
    elif args.command == 'run':
        result = product.action('run_detail', {'id': args.id})
    else:
        result = product.action('training_export' if args.command == 'training' else 'export', {'recipient': getattr(args, 'recipient', 'training'), 'countries': args.countries})
        args.output.mkdir(parents=True, exist_ok=True)
        dataset = args.output / result['filename']
        manifest = args.output / (dataset.stem + '.manifest.json')
        dataset.write_bytes(result['content'].encode('utf-8'))
        manifest.write_text(json.dumps(result['manifest'], indent=2), encoding='utf-8')
        result = {**result['manifest'], 'dataset_file': str(dataset.resolve()), 'manifest_file': str(manifest.resolve())}
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
