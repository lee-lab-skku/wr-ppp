@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 (
  echo Install Python 3.11 or newer from python.org, including Tcl/Tk and pip.
  echo Then run this file again.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  if exist ".venv" (
    echo Existing .venv uses a different Python layout. It has been preserved.
    echo Use Start-Weekly-Report.cmd or see windows\README.md.
    pause
    exit /b 1
  )
  py -3 -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" -m pip install -r windows\requirements.txt
if errorlevel 1 goto failed
echo Ready. Open Start-Weekly-Report.cmd and configure Windows TeX Live.
pause
exit /b 0
:failed
echo Setup failed. See the error above.
pause
exit /b 1
