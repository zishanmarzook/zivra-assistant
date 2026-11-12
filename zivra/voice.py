"""Retained V2 Windows speech experiment. Never listens until called by the UI."""
from pathlib import Path
import os
import subprocess
from zivra.system.windows import require_windows


def listen_once():
    require_windows()
    script = Path(__file__).with_name("resources") / "recognize_once.ps1"
    powershell = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    result = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-File", str(script)],
                            capture_output=True, text=True, timeout=19,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for line in result.stdout.splitlines():
        if line.startswith("RESULT::") and result.returncode == 0:
            return line[8:]
        if line.startswith("ERROR::"):
            raise RuntimeError(line[7:])
    raise RuntimeError("Speech recognition unavailable or script policy blocked it. Use typing or Windows dictation (Win+H).")
