# Current-instance validation

Validated in the Linux cloud environment with Python 3.12 and PySide6 6.10.2.

- Original uploaded V2 source files preserved byte-for-byte in `legacy/v2`.
- Hash-verified development dependency installation and editable app installation.
- Pytest covers command routing and original speech phrases, settings validation,
  history/persistence/schema handling, plugin lifecycle and failure isolation,
  permissions, workflows, mocked Windows adapters, Qt pages, worker thread
  delivery, and single-instance restoration.
- `python -m zivra --smoke-test` creates the desktop and verifies a real command
  worker result plus system metrics before exiting successfully.
- `python -m PyInstaller --noconfirm packaging/ZIVRA.spec` built a Linux artifact;
  `dist/ZIVRA/ZIVRA --smoke-test` successfully exercised the packaged Qt app.
- `python -m pip check` reported no broken requirements.

Brief source and packaged smoke runs measured approximately 74 MB and 81 MB RSS,
respectively. These are Linux process snapshots, not Windows benchmarks or
long-duration idle/resource tests. No large models or background microphone
listeners were loaded.

An initial smoke/test failure revealed the cloud machine had no battery sysfs
interface. Optional sensor exceptions are now handled, and a regression test
confirms missing battery/network sensors do not disable other monitoring.

Windows behavior is covered by adapter mocks and a saved CI workflow, not by an
actual Windows run in this chat. The Windows package, real application launching,
registry startup, tray interaction, DPI scaling, microphone recognition and
external accounts remain unvalidated on their target platform. Rainmeter and
GhostLink sources were not in the ZIP. The cloud setup draft and local commits
do not establish that GitHub CI ran or that a reusable snapshot was published.
