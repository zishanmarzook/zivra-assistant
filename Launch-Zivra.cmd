@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo First run scripts\Setup-Dev.ps1 from PowerShell to install ZIVRA.
  pause
  exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" -m zivra
