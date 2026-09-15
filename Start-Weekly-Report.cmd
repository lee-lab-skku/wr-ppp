@echo off
setlocal
cd /d "%~dp0"
set "WR_CONFIG=%~dp0.windows-config.json"
if exist "windows\dist\WeeklyReport\WeeklyReport.exe" (
  start "" "windows\dist\WeeklyReport\WeeklyReport.exe"
  exit /b
)
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "windows\weekly_report.py" gui
  if errorlevel 1 pause
  exit /b
)
if exist ".venv\bin\python.exe" (
  ".venv\bin\python.exe" "windows\weekly_report.py" gui
  if errorlevel 1 pause
  exit /b
)
echo Run Windows-Setup.cmd first. See windows\README.md.
pause
