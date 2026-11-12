@echo off
setlocal
cd /d "%~dp0"
where pyw >nul 2>&1
if not errorlevel 1 (
  start "" pyw -3 "%~dp0zivra_app.py"
  exit /b 0
)
where pythonw >nul 2>&1
if not errorlevel 1 (
  start "" pythonw "%~dp0zivra_app.py"
  exit /b 0
)
where py >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp0zivra_app.py"
  exit /b 0
)
echo Python not found. Install Python 3 with Tkinter, then run again.
pause
