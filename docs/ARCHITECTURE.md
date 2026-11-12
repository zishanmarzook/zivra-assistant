# Architecture

`python -m zivra` loads Settings, the per-user instance guard, then the Qt window.
The UI owns a bounded QThreadPool and a 2-second metrics timer. Worker results
return through Qt signals; widgets are only updated on the main thread. Shutdown
stops sampling, waits for owned jobs, then shuts down features and releases IPC.
Microphone work starts only on Listen once and has a subprocess timeout.

- `config.py`: per-user storage, validated settings and schema version migrations.
- `core/commands.py`: intent classification refactored from V2, without side effects.
- `core/assistant.py`: routing, feature dispatch, truthful fallback and optional history.
- `core/permissions.py`: builtin capabilities and explicit consent boundary.
- `core/workflows.py`: manual typed steps, permissions and stop-on-failure results.
- `plugins/base.py`: feature manifest and initialize/execute/health/shutdown interface.
- `plugins/manager.py`: explicit builtin factory registry, lifecycle, capability checks,
  enable/disable persistence, load failure isolation and serialized dispatch.
- `system/`: platform adapters and read-only sampling, independently testable.
- `ui/`: presentation, job transport, single-instance restoration, no command IPC.
- `voice.py` and `resources/recognize_once.ps1`: optional retained V2 speech experiment.

Add a trusted builtin by declaring its manifest, factory and permissions, then
adding explicit intent routes and tests. Update settings validation/migration if
the plugin has persistent preferences. No filesystem plugin discovery or execution
of downloaded modules. Future untrusted extensions need a separate process and
narrow message interface; the current Python allowlist is not a sandbox.

The rule-based provider is the only current command mode. Future local/cloud model
providers must propose typed intents through the same router and approval layer;
they must not issue shell strings. No generalized event bus, model inference,
workflow editor, scheduler, updater or network service runs in Phase 1.
