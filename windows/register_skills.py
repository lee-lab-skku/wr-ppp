"""Interactive Codex/Claude skill registration for a source checkout."""
from pathlib import Path
import sys


# Allow this file to run directly from a freshly cloned repository.
WINDOWS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(WINDOWS_ROOT))

from wr.skills import install  # noqa: E402


CHOICES = {
    '1': ('Codex', 'codex'),
    '2': ('Claude', 'claude'),
}


def main(read=input, write=print, home=None):
    write('사용할 AI를 선택하세요.')
    write('  1. Codex')
    write('  2. Claude')

    while True:
        try:
            choice = read('번호 입력 (1/2): ').strip()
        except (EOFError, KeyboardInterrupt):
            write('\n등록을 취소했습니다.')
            return 1
        if choice in CHOICES:
            break
        write('1 또는 2를 입력하세요.')

    label, service = CHOICES[choice]
    try:
        result = install([service], administrator=True, home=home)
    except (OSError, ValueError) as error:
        write(f'등록하지 못했습니다: {error}')
        return 1

    if result['installed']:
        write(f'{label}에 wr-wr, admin-wr 스킬을 등록했습니다.')
        for path in result['installed']:
            write(f'  {path}')
    else:
        write(f'{label}에 두 스킬이 이미 등록되어 있습니다.')
    write('VS Code의 AI 확장을 다시 시작하면 스킬 목록이 갱신됩니다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
