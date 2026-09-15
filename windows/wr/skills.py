"""Register canonical skills without copying or silently replacing user files."""
from pathlib import Path
import os

from .core import ROOT


def install(services, administrator=False, replace=False, home=None):
    home = Path(home or Path.home())
    names = ['wr-wr', 'admin-wr'] if administrator else ['wr-wr']
    normalized = ['agents' if value == 'codex' else value for value in services]
    if not normalized or len(set(normalized)) != len(normalized) or any(x not in ('agents', 'claude') for x in normalized):
        raise ValueError('agents, claude 중 중복 없이 선택하세요. codex는 agents의 별칭입니다.')
    operations = []
    for service in normalized:
        for name in names:
            source = ROOT / 'skills' / name
            destination = home / ('.agents' if service == 'agents' else '.claude') / 'skills' / name
            if destination.is_symlink() and destination.resolve() == source.resolve():
                continue
            if os.path.lexists(destination):
                if destination.is_dir() and not destination.is_symlink():
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
            destination.symlink_to(source, target_is_directory=True)
            completed.append(destination)
    except OSError as error:
        for destination in reversed(completed):
            destination.unlink()
        for destination, backup in reversed(backups):
            backup.rename(destination)
        raise ValueError('스킬 연결을 생성하지 못해 변경을 되돌렸습니다. Windows 개발자 모드 또는 심볼릭 링크 권한이 필요합니다. ' + str(error)) from error
    return {'installed': [str(p) for p in completed], 'backups': [str(b) for _, b in backups]}
