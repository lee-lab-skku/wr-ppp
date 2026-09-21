# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

repo = Path(SPECPATH).parent
datas = [(str(repo / name), str(Path(name).parent)) for name in
         ('template.tex', 'weekly-report.sty', 'README.md', 'CONTRIBUTING.md',
          'windows/README.md', 'windows/install-tex.ps1', 'windows/common.ps1', 'scripts/notify-held',
          'report_editor/assets/editor.html')]
datas.append((str(repo / 'skills'), 'skills'))
binaries, hiddenimports = [], ['getpass', 'urllib.request', 'urllib.error']
for package in ('tzdata', 'pypdf'):
    data, binary, hidden = collect_all(package)
    datas += data
    binaries += binary
    hiddenimports += hidden
a = Analysis([str(repo / 'windows/weekly_report.py')], pathex=[str(repo / 'windows'), str(repo)],
             binaries=binaries, datas=datas, hiddenimports=hiddenimports,
             hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='WeeklyReport', console=False, upx=False)
cli = EXE(pyz, a.scripts, [], exclude_binaries=True, name='WeeklyReportCLI', console=True, upx=False)
coll = COLLECT(gui, cli, a.binaries, a.datas, strip=False, upx=False, name='WeeklyReport')
