# V2 → 0.3.0 / Phase 1

## Source inventory and plan

The supplied `ZIVRA.zip` contained `zivra_app.py` (Tkinter UI, Windows adapters,
metrics, voice subprocess), `zivra_core.py` (intent parser), `Launch-Zivra.cmd`,
`recognize_once.ps1`, and a generated `.pyc` cache. Four original files are
preserved in `legacy/v2`; the generated cache was excluded. No Rainmeter skin,
GhostLink server, startup registration script, tests or dependencies were supplied.

Migration steps: preserve the source baseline; extract and constrain routing and
Windows actions; introduce SQLite and bundled feature interfaces; build the Qt
desktop around the same commands; add core/UI tests and Windows packaging.

## Preservation and deliberate changes

| V2 behavior | Migrated behavior |
| --- | --- |
| Local command parser | Same original speech phrases tested against V2; exact intent matches |
| Tkinter black console | PySide6 monochrome navigation, command log and dashboard |
| Windows ctypes CPU/RAM | psutil metrics across development platforms; optional sensors isolated |
| App quick actions | Same known targets, alias overrides and explicit errors |
| Chrome opened default browser | Detect Chrome specifically; `open browser` uses default |
| Spotify URI/web fallback | Preserved; no API connection claimed |
| Media key toggle | Preserved; active Windows session limitation displayed |
| Instagram inbox shortcut | Preserved; no private message access |
| Phone Link shortcut | Preserved; pairing happens in Phone Link |
| GhostLink batch search in Downloads | Replaced by explicit trusted .exe alias; backend not supplied |
| Roblox web fallback | Installed Studio detected or actionable error; no fake launch success |
| Push-to-talk PowerShell | Original speech script retained, worker timeout, no execution-policy bypass; experimental |
| Close iconified window | Optional tray close with restore/quit; exits if no tray |
| No structured settings | Versioned SQLite, no existing V2 settings to import |
| Unknown / risky commands | No arbitrary execution; ambiguous multi-action text rejected |

## Validation boundaries

Automated tests cover the original voice phrase mapping, refusal/ambiguity,
application launch argument vectors, missing apps, media call mocks, startup
registry mocks and consent, persistence/migrations/history deletion, feature
failure isolation, workflow failure, Qt navigation/workers, and single-instance
restoration. Headless smoke tests check a real system report and rendered metrics.

Actual Windows registry, app launches, media sessions, tray, microphone and
packaged Windows executable need a Windows machine. External account APIs, iPhone
pairing, GhostLink transfers and Rainmeter were not exercised. No optional model
or external service is downloaded or connected.
