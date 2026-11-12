$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        py -3 -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required. Install it from python.org.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install --require-hashes -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
    & '.\.venv\Scripts\python.exe' -m pip install --no-deps --no-build-isolation -e .
    if ($LASTEXITCODE -ne 0) { throw 'ZIVRA installation failed' }
    & '.\.venv\Scripts\python.exe' -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed; inspect output before starting ZIVRA' }
    Write-Host 'Ready. Double-click Launch-Zivra.cmd.'
} finally { Pop-Location }
