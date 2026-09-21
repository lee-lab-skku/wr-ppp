"""Register canonical skills without copying or silently replacing user files."""
from pathlib import Path
import os
import subprocess

from .core import ROOT

SERVICES = {'agents': '.agents', 'claude': '.claude', 'antigravity': '.gemini/config'}
ALIASES = {'codex': 'agents', 'gemini': 'agents', 'copilot': 'agents'}


def _is_link(path):
    """Recognize both directory symlinks and Windows junctions."""
    if path.is_symlink():
        return True
    junction_check = getattr(os.path, 'isjunction', None)
    if callable(junction_check):
        return bool(junction_check(path))
    # os.path.isjunction was added after the oldest supported Python.  Windows
    # has exposed the reparse tag on stat_result since Python 3.8.
    try:
        return path.stat(follow_symlinks=False).st_reparse_tag == 0xA0000003
    except (AttributeError, OSError):
        return False


def _create_link(source, destination):
    symlink_failure = None
    try:
        destination.symlink_to(source, target_is_directory=True)
        return
    except OSError as error:
        if os.name != 'nt':
            raise
        symlink_failure = error
    # Directory junctions do not require Developer Mode.  Carry paths in the
    # environment so PowerShell never parses path metacharacters as code.
    command = ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
               "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
               "-Path $env:WR_SKILL_LINK -Target $env:WR_SKILL_SOURCE | Out-Null"]
    environment = dict(os.environ, WR_SKILL_LINK=str(destination), WR_SKILL_SOURCE=str(source))
    result = subprocess.run(command, env=environment, capture_output=True, text=True,
                            encoding='utf-8', errors='replace',
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode or not _is_link(destination):
        detail = (result.stderr or result.stdout).strip()
        raise OSError(f'{symlink_failure}; junction 생성 실패: {detail}') from symlink_failure


def _remove_link(path):
    if path.is_symlink():
        path.unlink()
    else:
        # os.rmdir removes the junction itself, never its target contents.
        os.rmdir(path)


def install(services, administrator=False, replace=False, home=None):
    home = Path(home or Path.home())
    names = ['wr-wr', 'admin-wr'] if administrator else ['wr-wr']
    normalized = list(dict.fromkeys(ALIASES.get(value, value) for value in services))
    if not normalized or any(x not in SERVICES for x in normalized):
        raise ValueError('agents, claude, antigravity 중 선택하세요. codex, gemini, copilot은 agents의 별칭입니다.')
    operations = []
    for service in normalized:
        for name in names:
            source = ROOT / 'skills' / name
            destination = home / SERVICES[service] / 'skills' / name
            if not source.is_dir():
                raise ValueError(f'스킬 원본 폴더가 없습니다: {source}')
            for parent in destination.parents:
                if os.path.lexists(parent) and not parent.is_dir():
                    raise ValueError(f'설치 상위 경로가 폴더가 아닙니다: {parent}')
            if _is_link(destination) and destination.resolve() == source.resolve():
                continue
            if os.path.lexists(destination):
                if destination.is_dir() and not _is_link(destination):
                    raise ValueError(f'기존 디렉터리는 교체하지 않습니다: {destination}')
                if not replace:
                    raise ValueError(f'기존 항목을 보존했습니다: {destination}. 명시적 교체 옵션이 필요합니다.')
            operations.append((source, destination))
    completed, backups = [], []
    try:
        for source, destination in operations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(destination):
                backup = destination.with_name(destination.name + '.backup')
                index = 0
                while os.path.lexists(backup):
                    index += 1
                    backup = destination.with_name(destination.name + f'.backup.{index}')
                destination.rename(backup)
                backups.append((destination, backup))
            _create_link(source, destination)
            completed.append((source, destination))
    except OSError as error:
        failures = []
        for source, destination in reversed(completed):
            try:
                # A concurrent user edit is not ours to undo.
                if not _is_link(destination) or destination.resolve() != source.resolve():
                    raise ValueError(f'설치 후 변경된 항목을 보존했습니다: {destination}')
                _remove_link(destination)
            except (OSError, ValueError) as failure:
                failures.append(str(failure))
        for destination, backup in reversed(backups):
            try:
                if os.path.lexists(destination):
                    raise ValueError(f'충돌 항목을 보존했습니다: {destination}; 백업: {backup}')
                backup.rename(destination)
            except (OSError, ValueError) as failure:
                failures.append(f'{failure}; 백업: {backup}')
        detail = '\n'.join(failures) if failures else '링크 변경을 되돌렸습니다.'
        raise ValueError('스킬 연결 실패. 심볼릭 링크와 Windows junction을 만들 수 있는지 확인하세요. '
                         + str(error) + '\n' + detail) from error
    return {'installed': [str(p) for _, p in completed], 'backups': [str(b) for _, b in backups]}
