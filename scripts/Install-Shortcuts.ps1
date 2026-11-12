param([Parameter(Mandatory=$true)][string]$Executable, [switch]$Remove)
$ErrorActionPreference = 'Stop'
$desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) 'ZIVRA.lnk'
$programs = Join-Path ([Environment]::GetFolderPath('Programs')) 'ZIVRA.lnk'
if ($Remove) {
    foreach ($link in @($desktop, $programs)) {
        if (Test-Path $link) { Remove-Item -LiteralPath $link }
    }
    Write-Host 'ZIVRA shortcuts removed. Disable startup in ZIVRA Settings before deleting the app.'
    exit 0
}
$app = (Resolve-Path -LiteralPath $Executable).Path
if ([IO.Path]::GetFileName($app) -ne 'ZIVRA.exe') { throw 'Select the packaged ZIVRA.exe.' }
$shell = New-Object -ComObject WScript.Shell
foreach ($link in @($desktop, $programs)) {
    if (Test-Path $link) { throw "Shortcut already exists: $link. Remove it first if replacing it." }
}
foreach ($link in @($desktop, $programs)) {
    $shortcut = $shell.CreateShortcut($link)
    $shortcut.TargetPath = $app
    $shortcut.WorkingDirectory = Split-Path $app -Parent
    $shortcut.IconLocation = "$app,0"
    $shortcut.Save()
}
Write-Host 'Desktop and Start Menu shortcuts created for the current user.'
