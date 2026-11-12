# Development and release process

1. Inspect the current application before each feature. Branch from `main` using
   `feature/<name>`, preserve unrelated modules and settings, and implement tests.
2. Increment `zivra.__version__`, `pyproject.toml` and builtin manifest versions as
   appropriate, update CHANGELOG and documentation, and run pytest/UI smoke checks.
3. Open a PR to main. CI runs Python 3.12 tests on Linux and Windows and builds a
   Windows folder artifact with an actual packaged UI smoke test. Workflow files
   are instructions, not evidence that CI has run.
4. On a Windows 11 test machine run `scripts/Build-Windows.ps1`. Manually exercise
   the real apps/media, start twice, close/restore tray, toggle startup and sign in,
   and check scaling at 100%, 150%, 200%. Test the speech experiment only after
   microphone permission. Verify no settings loss when replacing the application.
5. After successful review/validation, merge, tag a version (`v0.3.0` for this
   release), and package the entire dist/ZIVRA folder as a versioned ZIP. Publish a
   SHA-256 checksum from a trusted release channel; use Windows code signing when
   available. Do not claim unsigned code is authenticated by a checksum alone.
6. End users approve updates, quit ZIVRA, back up their settings, verify the release
   source and checksum/signature, then replace the app folder. Settings remain in
   LocalAppData. For rollback, keep the previous folder and settings backup; a newer
   settings schema may require the matching app version. Never overwrite a running
   executable or silently run downloaded code.

Development Git updates and end-user releases are separate. An automatic updater
is planned, not implemented. No remote push, PR, tag or release is implied by a
local commit. Initial migration commits can exist locally before remote publication.
