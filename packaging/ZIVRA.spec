# Build on Windows for a Windows executable. Linux builds only validate this recipe.
from pathlib import Path
root = Path(SPECPATH).parent
resources = root / 'zivra' / 'resources'
a = Analysis(
    [str(root / 'scripts/run_zivra.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(resources), 'zivra/resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtQuick', 'PySide6.QtQml'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ZIVRA',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(resources / 'zivra.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ZIVRA')
