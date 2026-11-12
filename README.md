# ZIVRA

ZIVRA 0.3.0 is Phase 1 of the continuing Windows assistant, migrated from the
user-supplied V2 Python console. It works without an AI model, cloud account,
API key, Rainmeter, or administrator privileges.

## Start on Windows 11

Install Python 3.11–3.14 (3.12 is used in CI). Open PowerShell in this folder:

```powershell
.\scripts\Setup-Dev.ps1
```

Then double-click **Launch-Zivra.cmd**, or run:

```powershell
.\.venv\Scripts\python.exe -m zivra
```

If PowerShell policy blocks a script, use the equivalent Python commands below
in PowerShell with `.venv\Scripts\python.exe` after creating the venv. Follow
your organization's script policy; disabling verification is unnecessary.

Try `help`, `system status`, `what's using my ram`, `open files`, `open spotify`,
`open phone link`, `open chrome`, `pause music`, or `next song`.
Failures are shown in the command conversation. Commands are explicit matches;
there is no shell execution or model-generated action execution.

## Development in the cloud / Linux

The cloud environment is Linux. Core development, read-only monitoring, Qt
offscreen tests and a Linux packaging smoke test work here. Windows launch,
registry, media, microphone, tray interaction and executable behavior require
Windows validation. No external service credentials are needed for Phase 1.

```bash
cd /workspace/zivra-assistant
python -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps --no-build-isolation -e .
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q
QT_QPA_PLATFORM=offscreen ZIVRA_DATA_DIR=/tmp/zivra-smoke .venv/bin/python -m zivra --smoke-test
ZIVRA_DATA_DIR=/workspace/scratch/zivra-data .venv/bin/python -m zivra --diagnose
```

Use `QT_QPA_PLATFORM=offscreen` only for headless tests. To interact with the app
on the cloud desktop, run `ZIVRA_DATA_DIR=/workspace/scratch/zivra-data XDG_CACHE_HOME=/tmp/zivra-cache .venv/bin/python -m zivra`
with the normal Qt platform. The cloud home directory is read-only, so use this
workspace data override for interactive startup and diagnostics. These commands
use the existing checkout; an isolated cloud task needs no extra Git worktree.

`requirements-lock.txt` pins the development dependency graph with artifact
hashes and platform markers. To intentionally refresh it, use
`uv pip compile pyproject.toml --extra dev --universal --generate-hashes --output-file requirements-lock.txt`,
review the changes, reinstall, and rerun the checks. The short requirements files
list direct dependencies for reference; use the hash-verified lock for setup.

## What Phase 1 provides

- A resizable, monochrome PySide6 desktop with dashboard, command conversation,
  system metrics, recent commands, application aliases and feature controls.
- CPU, RAM, disk, network, optional battery and ZIVRA process RSS. Largest visible
  processes are reported by resident memory; this is not a leak diagnosis.
- The V2 shortcuts for Windows apps, folders, Spotify, Phone Link and Instagram;
  Windows media keys control the active session, not Spotify specifically.
- Configurable trusted `.exe` aliases, Chrome/Roblox Studio detection, and truthful
  missing-app errors. Launching a process is not proof that it became ready.
- Bundled plugin manifests, initialization/shutdown, health reporting, capability
  checks, persisted enable/disable controls and optional-feature error isolation.
- SQLite schema migration, local preferences, opt-in bounded command history,
  history deletion, preference export and reset.
- Single-instance window restoration, tray restore/quit where a tray is available,
  and an explicit, reversible current-user Windows sign-in startup toggle.
- A manual read-only system-report workflow with step results and stop-on-failure.
- Background workers for commands, metrics and retained experimental V2 speech;
  quit waits for owned work to finish (speech subprocess timeout: 19 seconds).
- Windows packaging recipe, launch/setup/build scripts, shortcut installation
  script, and CI for tests plus Windows package smoke testing.

Some navigation pages deliberately describe later work: AI Chat currently routes
local commands, File Manager offers folder shortcuts, Automation runs the single
read-only workflow, and Integrations contains launch shortcuts with no account
connections. They do not pretend to implement model conversations, file browsing,
workflow editing, or connected-service status.

## Preferences, privacy and compatibility

Preferences live in `%LOCALAPPDATA%\ZIVRA\settings.sqlite3`, separate from the
installation. Linux uses `$XDG_DATA_HOME/zivra` (default `~/.local/share/zivra`).
`ZIVRA_DATA_DIR` overrides this for isolated testing. History is off by default;
enabling it stores at most 200 command/response pairs locally. Disabling it deletes
stored pairs. Preferences can be exported from Settings; history is excluded.
No account tokens are stored, and there are no automatic cloud requests.
Opening a web shortcut uses your browser and its normal network connection.

Schema 1 is created transactionally; existing keys survive supported migrations.
A database from a newer schema is rejected, never reset automatically. V2 had
no structured preference database to migrate. Startup is read directly from
Windows, not inferred from a saved checkbox; resetting preferences leaves it alone.
The startup toggle operates on `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
under the `ZIVRA` name. Existing V2 scheduled tasks or other startup shortcuts must
be removed manually if present; they were not included in the ZIP.

Aliases must be trusted absolute executable paths. Saving one requests approval;
commands invoke an argument vector with `shell=False`. This does not sandbox the
chosen application. Third-party Python plugin discovery is disabled: only the
explicit factories in `zivra/plugins/manager.py` are loaded. Capability checks do
not make untrusted in-process code safe. Windows startup changes require separate
confirmation. No destructive commands are implemented.

## Preserved V2 and migration

The original four source/script files are byte-for-byte preserved under
`legacy/v2/` in the initial Git commit. Do not launch the legacy and migrated
apps together: the old app has no new single-instance guard.
See [migration notes](docs/MIGRATION.md) for the source inventory and deliberate
safety and compatibility changes. Rainmeter and the GhostLink backend were absent
from the supplied ZIP; neither has been migrated or tested.

## Windows packaging and installation

On Windows after setup:

```powershell
.\scripts\Build-Windows.ps1
```

The recipe produces `dist\ZIVRA\ZIVRA.exe` and companion files. Keep the **whole
ZIVRA folder** together; this is a portable folder distribution. PyInstaller is
platform-specific: a Linux build is not a Windows executable. No working Windows
artifact is claimed until the Windows build and smoke test run successfully.

Copy that folder to a permanent user-owned location, for example
`%LOCALAPPDATA%\Programs\ZIVRA`, and launch `ZIVRA.exe`. To create shortcuts:

```powershell
.\scripts\Install-Shortcuts.ps1 -Executable "$env:LOCALAPPDATA\Programs\ZIVRA\ZIVRA.exe"
```

Enable sign-in startup in ZIVRA Settings if desired. Only one instance per user
data directory runs; opening another copy restores the first window. Close
minimizes to tray when supported and enabled; Quit in the tray exits. Without a
tray, closing exits normally. Qt 6 supplies automatic high-DPI scaling.

To uninstall, disable startup in Settings, quit, run the shortcut script with
`-Executable <path> -Remove`, and delete the portable app folder. Optionally delete
`%LOCALAPPDATA%\ZIVRA` to remove preferences/history. If the app has already been
deleted, remove only the `ZIVRA` value in the HKCU Run key shown above. An installer
wizard, code signing and automatic updates are not implemented.

## Continue the same application

See [architecture](docs/ARCHITECTURE.md), [release process](docs/RELEASING.md), and
[CHANGELOG](CHANGELOG.md). Add features on feature branches, preserve settings,
update tests/docs/changelog and increment the version. Run tests before a PR to
`main`. Do not replace ZIVRA to add an integration.
