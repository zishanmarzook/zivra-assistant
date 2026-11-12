$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Build the Windows executable on Windows.' }
$root = Split-Path $PSScriptRoot -Parent
Push-Location $root
try {
    & '.\.venv\Scripts\python.exe' -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed' }
    & '.\.venv\Scripts\python.exe' -m PyInstaller --noconfirm packaging/ZIVRA.spec
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
    if (-not (Test-Path 'dist\ZIVRA\ZIVRA.exe')) { throw 'Expected executable not found' }
    $priorDataDirectory = $env:ZIVRA_DATA_DIR
    $env:ZIVRA_DATA_DIR = Join-Path ([IO.Path]::GetTempPath()) ('zivra-package-smoke-' + [Guid]::NewGuid())
    try {
        $test = Start-Process -FilePath (Join-Path $root 'dist\ZIVRA\ZIVRA.exe') -ArgumentList '--smoke-test' -Wait -PassThru
        if ($test.ExitCode -ne 0) { throw 'Packaged UI smoke test failed' }
    } finally { $env:ZIVRA_DATA_DIR = $priorDataDirectory }
    Write-Host 'Built and smoke-tested dist\ZIVRA\ZIVRA.exe. Keep the whole ZIVRA folder together.'
} finally { Pop-Location }
