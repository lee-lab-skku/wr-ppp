"""Validate release metadata and publish only verified, tested Windows artifacts."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TAG = re.compile(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-(beta|rc))?')


def validate_tag(tag):
    if not TAG.fullmatch(tag):
        raise ValueError('Expected vMAJOR.MINOR.PATCH, optionally followed by -beta or -rc (no leading zeroes).')
    return tag.endswith(('-beta', '-rc'))


def release_notes(root, tag):
    """Collect stable and same-version prerelease notes without rewriting the changelog.

    Prerelease publications retain their own incremental notes. A stable release
    includes its optional rc and beta sections, newest stage first, and may have
    no new bullets of its own when it only promotes tested prerelease changes.
    The target section and matching template version are always required.
    """
    prerelease = validate_tag(tag)
    first = (root / 'template.tex').read_text(encoding='utf-8').splitlines()[0]
    if first != f'% Repository version: {tag}':
        raise ValueError(f'template.tex must start with "% Repository version: {tag}".')
    changelog = (root / 'CHANGELOG.md').read_text(encoding='utf-8')
    versions = [tag[1:]]
    if not prerelease:
        versions.extend((tag[1:] + '-rc', tag[1:] + '-beta'))
    sections = []
    for version in versions:
        # Match the version before validating its date so malformed or duplicate
        # selected sections cannot silently disappear from published notes.
        heading = re.compile(r'^## \[' + re.escape(version) + r'\]([^\n]*)$', re.M)
        matches = list(heading.finditer(changelog))
        if not matches and version != tag[1:]:
            continue
        if len(matches) != 1:
            raise ValueError(f'CHANGELOG.md must contain one dated [{version}] release section.')
        date = re.fullmatch(r' &mdash; (\d{4}-\d{2}-\d{2})', matches[0][1])
        if date is None:
            raise ValueError(f'CHANGELOG.md must contain one dated [{version}] release section.')
        dt.date.fromisoformat(date[1])
        body = re.split(r'^## ', changelog[matches[0].end():], maxsplit=1, flags=re.M)[0].strip()
        sections.append((version, date[1], body))
    if not any(re.search(r'^- ', body, re.M) for _, _, body in sections):
        raise ValueError('The release changelog must describe at least one change.')
    if len(sections) == 1:
        return sections[0][2] + '\n'
    return '\n\n'.join(f'## {version} &mdash; {date}\n\n{body}'.rstrip()
                       for version, date, body in sections) + '\n'


def validate_checkout(root, tag, expected_commit):
    validate_tag(tag)
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', expected_commit):
        raise ValueError('Expected the full triggering Git object ID.')
    def git(*arguments):
        return subprocess.check_output(['git', '-C', str(root), *arguments], text=True).strip()
    head = git('rev-parse', 'HEAD')
    if git('rev-parse', '--verify', f'refs/tags/{tag}^{{commit}}') != head:
        raise ValueError('The release tag does not point to the checked-out commit.')
    if git('rev-parse', '--verify', f'{expected_commit}^{{commit}}') != head:
        raise ValueError('The checkout does not match the triggering commit.')
    if git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError('Release builds require a clean tracked checkout.')
    return head


def verify_artifacts(directory, tag, *, development=False):
    """Reject stale installers, renamed assets, and corrupt transfers before upload."""
    if development:
        # Manual CI uses the existing git-describe version, without widening
        # the release-tag policy or accepting dirty builds as CI artifacts.
        if not re.fullmatch(TAG.pattern + r'(-[0-9]+-g[0-9a-f]+)?', tag):
            raise ValueError('Expected a release tag or a clean tag-derived development version.')
    else:
        validate_tag(tag)
    installer = directory / f'WeeklyReport-{tag}-Setup.exe'
    checksum = installer.with_suffix('.exe.sha256')
    if set(directory.iterdir()) != {installer, checksum}:
        raise ValueError('Release artifacts must contain exactly the tagged installer and its SHA256 file.')
    if any(p.is_symlink() or not p.is_file() for p in (installer, checksum)):
        raise ValueError('Release artifacts must be regular files.')
    with installer.open('rb') as stream:
        if stream.read(2) != b'MZ':
            raise ValueError('Installer is not a Windows executable.')
        stream.seek(0)
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if checksum.read_text(encoding='ascii').strip() != f'{digest}  {installer.name}':
        raise ValueError('Installer SHA256 or filename does not match the checksum file.')
    return installer, checksum


def publish(root, tag, commit, directory, repository, run=subprocess.run):
    """Upload to a draft first; retries may repair drafts but never published assets."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Expected a GitHub owner/repository name.')
    prerelease = validate_tag(tag)
    notes = release_notes(root, tag)
    assets = verify_artifacts(directory, tag)
    def gh(*arguments, check=True):
        result = run(['gh', *arguments], capture_output=True, text=True, timeout=300)
        if check and result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result
    existing = gh('api', f'repos/{repository}/releases/tags/{tag}', check=False)
    if existing.returncode:
        if 'HTTP 404' not in existing.stderr:
            raise RuntimeError(existing.stderr)
        release = None
    else:
        release = json.loads(existing.stdout)
        if not release['draft']:
            uploaded = {a['name'] for a in release['assets'] if a['state'] == 'uploaded' and a['size'] > 0}
            if not {p.name for p in assets}.issubset(uploaded):
                raise ValueError('Published release has missing assets; preserve it and publish a new version after review.')
            print(f'{tag} is already published; its assets were preserved.')
            return
        if release['target_commitish'] != commit:
            raise ValueError('Existing draft targets a different commit; inspect it before retrying.')
    with tempfile.TemporaryDirectory(prefix='wr-release-') as tmp:
        notes_file = Path(tmp) / 'notes.md'
        notes_file.write_text(notes, encoding='utf-8')
        options = ['--repo', repository, '--title', tag, '--notes-file', str(notes_file)]
        if release is None:
            gh('release', 'create', tag, '--draft', '--verify-tag', '--target', commit,
               *options, *(['--prerelease', '--latest=false'] if prerelease else []))
        else:
            gh('release', 'edit', tag, *options, f'--prerelease={str(prerelease).lower()}')
        gh('release', 'upload', tag, '--repo', repository, '--clobber', *(str(p) for p in assets))
        gh('release', 'edit', tag, '--repo', repository, '--draft=false',
           *(['--latest=false'] if prerelease else []))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'verify-artifacts', 'publish'))
    version = parser.add_mutually_exclusive_group(required=True)
    version.add_argument('--tag')
    version.add_argument('--version', help='Tag-derived bundle version; only for verify-artifacts.')
    parser.add_argument('--expected-commit')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--repository')
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    if args.command == 'verify-artifacts':
        if not args.directory:
            parser.error('--directory is required')
        verify_artifacts(args.directory, args.version or args.tag, development=args.version is not None)
        print('Installer and SHA256 verified.')
        return
    if not args.tag:
        parser.error('--tag is required for release preparation and publication')
    if not args.expected_commit:
        parser.error('--expected-commit is required')
    commit = validate_checkout(ROOT, args.tag, args.expected_commit)
    release_notes(ROOT, args.tag)
    if args.command == 'prepare':
        if args.github_output:
            with args.github_output.open('a', encoding='utf-8') as stream:
                stream.write(f'commit={commit}\n')
        print(f'Validated {args.tag} at {commit}.')
    else:
        if not args.directory or not args.repository:
            parser.error('--directory and --repository are required')
        publish(ROOT, args.tag, commit, args.directory, args.repository)


if __name__ == '__main__':
    main()
