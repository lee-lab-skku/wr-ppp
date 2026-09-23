"""Collect build-matched notices without treating them as a complete source offer.

Runtime collection runs under the packaging interpreter. TeX preparation reads
package metadata and archives only; it never executes downloaded package code.
"""
import argparse
import hashlib
from importlib import metadata
import json
import lzma
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
from urllib.request import urlopen


LEGAL_NAME = re.compile(r'^(license|licence|copying|copyright|notice|readme|ofl|lppl)([._-]|$)', re.I)
TEX_NOTICES = 'tlpkg/wr-licenses'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative_path(value):
    """Reject archive/manifest paths that could escape or alias Windows targets."""
    path = PurePosixPath(value)
    if not value or '\\' in value or ':' in value or path.is_absolute() or any(
            part in ('', '.', '..') or part.endswith((' ', '.')) for part in value.split('/')):
        raise ValueError(f'Unsafe notice path: {value!r}')
    return path


def inside(root, name):
    path = Path(root).joinpath(*relative_path(name).parts)
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f'Notice path leaves its distribution: {name}')
    return path


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def verify_files(root, files):
    if not files:
        raise ValueError('Notice inventory is empty')
    for name, expected in files.items():
        path = inside(root, name)
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'Missing or changed notice resource: {name}')


def collect_runtime(output, scripts, python_root=None, distributions=None, binaries=()):
    """Return PyInstaller data TOCs for notices from this interpreter and its hooks.

    scripts is Analysis.scripts: hooks are selected by analysis, not a guessed
    fixed list. Source headers are retained along with the upstream full terms.
    """
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    python_root = Path(python_root or sys.base_prefix)
    distributions = distributions or {name: metadata.distribution(name) for name in ('pypdf', 'tzdata', 'pyinstaller')}
    files, components, toc = {}, {}, []

    def copy(source, name):
        source = Path(source)
        if not source.is_file() or not source.stat().st_size:
            raise ValueError(f'Required runtime notice is missing: {source}')
        target = inside(output, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files['licenses/' + name] = digest(target)
        toc.append(('licenses/' + name, str(target), 'DATA'))
        return 'licenses/' + name

    components['python'] = {'version': sys.version.split()[0], 'files': [copy(python_root / 'LICENSE.txt', 'python/LICENSE.txt')]}
    # CPython's Windows combined license is required above. Preserve additional
    # Tcl/Tk notices when the selected provider also supplies them separately.
    for path in sorted((python_root / 'tcl').rglob('*')):
        if path.is_file() and LEGAL_NAME.match(path.name):
            components['python']['files'].append(copy(path, 'python/' + path.relative_to(python_root).as_posix()))
    for name, distribution in distributions.items():
        notices = []
        for entry in distribution.files or []:
            parts = PurePosixPath(str(entry).replace('\\', '/')).parts
            if any(p.endswith('.dist-info') for p in parts) and (
                    'licenses' in parts or LEGAL_NAME.match(parts[-1])):
                suffix = '/'.join(parts[1:])
                notices.append(copy(distribution.locate_file(entry), name + '/' + suffix))
        if not notices:
            raise ValueError(f'No installed license files found for {name}')
        components[name] = {'version': distribution.version, 'files': notices}
    hooks = []
    for name, source, _kind in scripts:
        if Path(source).name.startswith('pyi_rth_'):
            # Keep attribution from exactly the source that Analysis embeds.
            # Full source is small and avoids stripping multiline notices.
            hooks.append(copy(source, 'pyinstaller/runtime-hooks/' + Path(source).name))
    components['pyinstaller']['runtime_hooks'] = hooks
    native_files = {relative_path(name.replace('\\', '/')).as_posix(): digest(source)
                    for name, source, _kind in binaries}
    manifest = {'schema': 1, 'components': components, 'files': files, 'native_files': native_files,
                'build_distributions': sorted((d.metadata['Name'], d.version) for d in metadata.distributions())}
    index = output / 'README.txt'
    index.write_text('Third-party runtime notices\nPaths below are relative to _internal.\n\n' + '\n'.join(
        f'{name} {item["version"]}\n' + '\n'.join(item['files']) for name, item in components.items()) +
        '\n\nPyInstaller runtime-hook sources and attribution: licenses/pyinstaller/runtime-hooks/\n'
        'KaTeX: report_editor/assets/KaTeX-LICENSE.txt\n'
        'Bundled TeX: ../tex/README.WeeklyReport.txt and ../tex/tlpkg/wr-licenses/README.txt\n', encoding='utf-8')
    files['licenses/README.txt'] = digest(index)
    toc.append(('licenses/README.txt', str(index), 'DATA'))
    write_json(output / 'runtime.json', manifest)
    toc.append(('licenses/runtime.json', str(output / 'runtime.json'), 'DATA'))
    return toc


def packages(text):
    """Read the fields and file lists used for notice collection from a tlpdb."""
    result, record, section = {}, None, None
    for line in text.splitlines():
        if line.startswith('name '):
            name = line[5:]
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]*', name) or name in result:
                raise ValueError(f'Invalid or duplicate TeX package: {name}')
            record = result[name] = {}
            section = None
        elif record is not None and line.startswith(' '):
            if section in ('runfiles', 'docfiles', 'srcfiles'):
                value = line.strip().split()[0].replace('RELOC/', 'texmf-dist/', 1)
                relative_path(value)
                record.setdefault(section, []).append(value)
        elif record is not None:
            key, _, value = line.partition(' ')
            section = key
            if key not in ('runfiles', 'docfiles', 'srcfiles'):
                record.setdefault(key, []).append(value)
    return result


def download(url):
    if not url.startswith('https://'):
        raise ValueError('Notice repository must use HTTPS')
    with urlopen(url, timeout=60) as response:
        return response.read()


def prepare_tex(tex, cache, repository='https://mirror.ctan.org/systems/texlive/tlnet', fetch=download):
    """Preserve named legal/readme files from installed packages and matching docs.

    The prepared set lives in TinyTeX and travels with its CI cache. Reuse it
    only for the exact installed tlpdb and unchanged notice bytes. Fresh remote
    metadata must match installed doc-container checksums before it is used.
    """
    tex, cache = Path(tex), Path(cache)
    database = tex / 'tlpkg/texlive.tlpdb'
    database_hash = digest(database)
    destination = tex / TEX_NOTICES
    if (destination / 'manifest.json').is_file():
        saved = json.loads((destination / 'manifest.json').read_text(encoding='utf-8'))
        if saved.get('schema') == 1 and saved['database_sha256'] == database_hash:
            verify_files(tex, saved['files'])
            return
    installed = packages(database.read_text(encoding='utf-8'))
    remote = packages(lzma.decompress(fetch(repository.rstrip('/') + '/tlpkg/texlive.tlpdb.xz')).decode())
    cache.mkdir(parents=True, exist_ok=True)
    files, inventory, index = {}, [], ['TeX package notices', '', 'Package versions and notice hashes: manifest.json', '']
    with tempfile.TemporaryDirectory(prefix='wr-licenses-', dir=tex / 'tlpkg') as temporary:
        staging = Path(temporary)
        for name, info in sorted(installed.items()):
            if name.startswith('00texlive.'):
                continue
            inventory.append({key: value for key, value in {
                'name': name, 'revision': info.get('revision', []),
                'catalogue_license': info.get('catalogue-license', []),
                'source_container_sha512': info.get('srccontainerchecksum', []),
                'run_container_sha512': info.get('containerchecksum', []),
            }.items()})
            for path in info.get('runfiles', []) + info.get('docfiles', []):
                if LEGAL_NAME.match(PurePosixPath(path).name):
                    resource = inside(tex, path)
                    if not resource.is_file():
                        raise ValueError(f'Installed TeX notice missing: {name}: {path}')
                    files[path] = digest(resource)
                    index.append(f'{name}: {path}')
            checksum = next(iter(info.get('doccontainerchecksum', [])), None)
            if checksum is None:
                continue
            if not re.fullmatch(r'[0-9a-f]{128}', checksum):
                raise ValueError(f'Invalid TeX doc checksum: {name}')
            other = remote.get(name, {})
            if other.get('doccontainerchecksum') != [checksum]:
                raise ValueError(f'TeX documentation no longer matches {name}; prepare from a matching repository snapshot.')
            wanted = [p for p in other.get('docfiles', []) if LEGAL_NAME.match(PurePosixPath(p).name)
                      and p not in files]
            if not wanted:
                continue
            archive = cache / (checksum + '.tar.xz')
            if not archive.is_file():
                data = fetch(repository.rstrip('/') + '/archive/' + name + '.doc.tar.xz')
                if hashlib.sha512(data).hexdigest() != checksum:
                    raise ValueError(f'TeX documentation checksum mismatch: {name}')
                archive.write_bytes(data)
            if hashlib.sha512(archive.read_bytes()).hexdigest() != checksum:
                raise ValueError(f'Cached TeX documentation checksum mismatch: {name}')
            found = set()
            with tarfile.open(archive) as contents:
                for member in contents:
                    if not member.isfile():
                        continue
                    member_name = relative_path(member.name).as_posix()
                    original = ('texmf-dist/' if other.get('relocated') == ['1'] else '') + member_name
                    if original not in wanted:
                        continue
                    if original in found:
                        raise ValueError(f'Duplicate TeX archive notice: {name}: {original}')
                    found.add(original)
                    target_name = 'files/' + name + '/' + member_name
                    target = inside(staging, target_name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with contents.extractfile(member) as source, target.open('wb') as output:
                        shutil.copyfileobj(source, output)
                    path = TEX_NOTICES + '/' + target_name
                    files[path] = digest(target)
                    index.append(f'{name}: {path} (upstream {original})')
            if found != set(wanted):
                raise ValueError(f'TeX archive lacks indexed notices: {name}: {set(wanted) - found}')
        for name in ('LICENSE.TL', 'LICENSE.CTAN'):
            files[name] = digest(tex / name)
        (staging / 'README.txt').write_text('\n'.join(index) + '\n', encoding='utf-8')
        files[TEX_NOTICES + '/README.txt'] = digest(staging / 'README.txt')
        write_json(staging / 'manifest.json', {'schema': 1, 'database_sha256': database_hash,
                                             'packages': inventory, 'files': files})
        # Replace only this generator's dedicated directory after all downloads
        # and validation succeed. Never alter upstream files or tlpdb contents.
        if destination.is_symlink():
            raise ValueError('Refusing a linked TeX notice destination')
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(staging, destination)


def verify_distribution(bundle, require_tex=False):
    """Check runtime and optional TeX notice manifests after copy/installation."""
    bundle = Path(bundle)
    resource = bundle / '_internal'
    runtime = json.loads((resource / 'licenses/runtime.json').read_text(encoding='utf-8'))
    if runtime.get('schema') != 1 or not {'python', 'pypdf', 'tzdata', 'pyinstaller'} <= runtime['components'].keys():
        raise ValueError('Incomplete runtime notice inventory')
    for name, component in runtime['components'].items():
        if not component.get('files') or any(p not in runtime['files'] for p in component['files']):
            raise ValueError(f'Runtime component lacks indexed notices: {name}')
    verify_files(resource, runtime['files'])
    if runtime.get('native_files'):
        verify_files(resource, runtime['native_files'])
    tex = bundle / 'tex'
    if require_tex or tex.exists():
        manifest = json.loads((tex / TEX_NOTICES / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('schema') != 1 or manifest['database_sha256'] != digest(tex / 'tlpkg/texlive.tlpdb'):
            raise ValueError('TeX notice inventory differs from the installed package database')
        verify_files(tex, manifest['files'])
        notice = Path(__file__).with_name('TeX-NOTICE.txt')
        if digest(tex / 'README.WeeklyReport.txt') != digest(notice):
            raise ValueError('TeX distribution modification notice is missing or changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    tex = commands.add_parser('prepare-tex')
    tex.add_argument('--tex-root', type=Path, required=True)
    tex.add_argument('--cache', type=Path, required=True)
    tex.add_argument('--repository', default='https://mirror.ctan.org/systems/texlive/tlnet')
    check = commands.add_parser('check')
    check.add_argument('--bundle', type=Path, required=True)
    check.add_argument('--require-tex', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare-tex':
        prepare_tex(args.tex_root, args.cache, args.repository)
    else:
        verify_distribution(args.bundle, args.require_tex)
    print('Distribution notice checks: OK')


if __name__ == '__main__':
    main()
