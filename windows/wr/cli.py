import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sys

from . import admin, core


def notifications():
    # Reuse canonical notification policy, transport and deduplication logic.
    loader = importlib.machinery.SourceFileLoader('wr_notify_held', str(core.ROOT / 'scripts/notify-held'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description='Weekly Report — Windows native tools')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('gui')
    setup = commands.add_parser('setup')
    for key in ('pdf-output', 'admin-output', 'admin-data', 'tex-bin'):
        setup.add_argument('--' + key)
    commands.add_parser('preflight')
    diagnostic = commands.add_parser('self-test')
    diagnostic.add_argument('--output', type=Path, required=True)
    skills = commands.add_parser('install-skills')
    skills.add_argument('--services', required=True, help='agents,claude,antigravity (codex,gemini,copilot alias agents)')
    skills.add_argument('--admin', action='store_true')
    skills.add_argument('--replace-existing', action='store_true')
    meta = commands.add_parser('report-metadata')
    meta.add_argument('--date')
    build = commands.add_parser('report-build')
    build.add_argument('source', nargs='?', default='main.tex')
    build.add_argument('--here', action='store_true')
    build.add_argument('--date')
    build.add_argument('--serial')
    commands.add_parser('test')
    commands.add_parser('admin-paths')
    commands.add_parser('discover')
    probe = commands.add_parser('probe-report')
    probe.add_argument('--storage-root', required=True)
    probe.add_argument('--file', required=True)
    bundle = commands.add_parser('build-bundle')
    bundle.add_argument('--storage-root', required=True)
    bundle.add_argument('--plan', required=True)
    bundle.add_argument('--date', required=True)
    bundle.add_argument('--output-dir')
    bundle.add_argument('--draft', action='store_true')
    bundle.add_argument('--approved-with-issues', action='store_true')
    bundle.add_argument('--review', help='Review JSON created with the unchanged draft')
    opener = commands.add_parser('open-bundle')
    opener.add_argument('file')
    notify = commands.add_parser('notify-held')
    notify.add_argument('--configure', action='store_true')
    notify.add_argument('--manifest', type=Path)
    notify.add_argument('--held', action='store_true')
    notify.add_argument('--send', action='store_true')
    args = parser.parse_args(argv)
    try:
        config = core.read_config(validate=args.command != 'setup')
        if args.command == 'gui':
            from .gui import run
            run()
        elif args.command == 'setup':
            for key in ('pdf_output', 'admin_output', 'admin_data', 'tex_bin'):
                value = getattr(args, key)
                if value is not None:
                    config[key] = value
            core.save_config(config)
            print(core.config_path())
        elif args.command == 'preflight':
            print(json.dumps(core.preflight(config), ensure_ascii=False, indent=2))
        elif args.command == 'self-test':
            import tkinter as tk
            from .gui import App
            from pypdf import PdfReader
            root = tk.Tk()
            root.withdraw()
            app = App(root)
            root.update()
            assert len(app.texts) == 5
            assert (core.ROOT / 'weekly-report.sty').is_file()
            notifications()
            core.atomic_write(args.output, json.dumps({'gui': 'ok', 'pdf_library': PdfReader.__name__,
                               'resources': str(core.ROOT), 'date': core.metadata('2026-08-31')}, ensure_ascii=False))
            root.destroy()
        elif args.command == 'install-skills':
            from .skills import install
            print(json.dumps(install(args.services.split(','), args.admin, args.replace_existing), ensure_ascii=False, indent=2))
        elif args.command == 'report-metadata':
            print(core.tsv([['schema', 'report-metadata/v1'], *core.metadata(args.date).items()]), end='')
        elif args.command == 'report-build':
            print(core.build_report(args.source, config, args.date, args.serial, args.here)['pdf'])
        elif args.command == 'test':
            import tempfile
            import shutil
            with tempfile.TemporaryDirectory(prefix='wr-template-') as tmp:
                source = Path(tmp) / 'template' / 'template.tex'
                source.parent.mkdir()
                shutil.copyfile(core.ROOT / 'template.tex', source)
                result = core.build_report(source, dict(config, pdf_output=tmp), serial=1)
                core.atomic_write(core.ROOT / 'template.pdf', Path(result['pdf']).read_bytes())
                print(core.ROOT / 'template.pdf')
        elif args.command == 'admin-paths':
            manifest, output, history = admin.paths(config)
            print(core.tsv([['manager-manifest', str(manifest)], ['history-output', str(output)],
                            *[['history', week, str(file)] for week, file in history.items()]]), end='')
        elif args.command == 'discover':
            manager = admin.load_manager(config)
            print(json.dumps(admin.discover(manager), default=str, ensure_ascii=False, indent=2))
        elif args.command == 'probe-report':
            info = core.probe(args.storage_root, args.file)
            rows = [['schema', 'admin-wr-probe/v1'], *[[k, str(info[k])] for k in ('file', 'mtime', 'sha256')],
                    ['readable', 'yes'], ['pages', str(info['pages'])], ['encrypted', 'no'],
                    ['creation-date', info['creation-date']], ['text-status', 'extracted' if info['text'].strip() else 'empty']]
            print(core.tsv(rows) + 'text-begin\n' + info['text'] + '\ntext-end')
        elif args.command == 'build-bundle':
            result = admin.build_bundle(core.read_tsv(args.plan), args.storage_root, config, args.date,
                                        args.output_dir, args.draft, args.approved_with_issues, args.review)
            print(result['pdf'])
            print(result['manifest'])
            if result['review']:
                print('review: ' + result['review'], file=sys.stderr)
        elif args.command == 'open-bundle':
            import os
            file = Path(args.file).resolve()
            core.inspect_pdf(file)
            os.startfile(file)
        elif args.command == 'notify-held':
            module = notifications()
            directory = admin.paths(config)[1].parent
            if args.configure:
                if args.manifest or args.send or args.held:
                    raise ValueError('--configure는 다른 알림 옵션과 함께 사용할 수 없습니다.')
                module.configure(directory)
            else:
                if not args.manifest or (args.send and not args.held):
                    raise ValueError('--manifest가 필요하며, 발송은 --held --send를 함께 지정해야 합니다.')
                payload, fingerprint = module.notice(args.manifest)
                if args.send:
                    module.send(directory, payload, fingerprint)
                else:
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(f'{type(error).__name__}: {error}', file=sys.stderr)
        return 1
