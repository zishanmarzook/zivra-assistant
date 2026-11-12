"""V2 app/media actions, separated from UI and checked before execution."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import webbrowser
from zivra.core.permissions import Permissions

IS_WINDOWS = os.name == "nt"
MEDIA_KEYS = {"media_toggle": 0xB3, "media_next": 0xB0, "media_previous": 0xB1,
              "volume_up": 0xAF, "volume_down": 0xAE, "volume_mute": 0xAD}


def require_windows():
    if not IS_WINDOWS:
        raise OSError("This action requires Windows 11. Core commands and monitoring also run on Linux.")


def open_url(url):
    if not webbrowser.open(url):
        raise OSError("No browser accepted the request")


def launch_app(name, aliases):
    require_windows()
    if name in aliases:
        path = Path(aliases[name])
        if not path.is_file() or path.suffix.lower() != ".exe":
            raise FileNotFoundError("Configured executable is missing; update its path in Applications")
        subprocess.Popen([str(path)], shell=False)
    elif name in {"files", "taskmanager", "notepad", "calculator"}:
        executable = {"files": "explorer.exe", "taskmanager": "taskmgr.exe", "notepad": "notepad.exe", "calculator": "calc.exe"}[name]
        # Do not resolve executables from an untrusted current working directory.
        root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        path = root / executable if name == "files" else root / "System32" / executable
        subprocess.Popen([str(path)], shell=False)
    elif name == "downloads":
        folder = Path.home() / "Downloads"
        if not folder.is_dir():
            raise FileNotFoundError("Downloads is not at the standard location on this PC; open it in File Explorer")
        os.startfile(str(folder))
    elif name == "settings":
        os.startfile("ms-settings:")
    elif name == "chrome":
        candidates = [Path(os.environ.get(base, "")) / "Google/Chrome/Application/chrome.exe" for base in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA") if os.environ.get(base)]
        chrome = next((p for p in candidates if p.is_file()), None)
        if chrome:
            subprocess.Popen([str(chrome), "https://www.google.com/"], shell=False)
        else:
            raise FileNotFoundError("Chrome was not found. Configure a chrome alias or use 'open browser'")
    elif name in {"browser", "chatgpt", "instagram"}:
        open_url({"browser": "https://www.google.com/", "chatgpt": "https://chatgpt.com/", "instagram": "https://www.instagram.com/direct/inbox/"}[name])
    elif name == "spotify":
        try:
            os.startfile("spotify:")
        except OSError:
            open_url("https://open.spotify.com/")
            return "Opened Spotify web because its desktop protocol was unavailable. No Spotify API is connected."
    elif name == "phonelink":
        os.startfile(r"shell:AppsFolder\Microsoft.YourPhone_8wekyb3d8bbwe!App")
        return "Requested Phone Link. Pair your iPhone there; ZIVRA has no phone data connection."
    elif name == "roblox":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        paths = sorted((root / "Roblox/Versions").glob("*/RobloxStudioBeta.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not paths:
            raise FileNotFoundError("Roblox Studio not detected. Configure its executable in Applications")
        subprocess.Popen([str(paths[0])], shell=False)
    elif name == "ghostlink":
        raise FileNotFoundError("GhostLink backend was not supplied. Configure a trusted GhostLink .exe alias; V2 batch autodiscovery is disabled")
    else:
        raise ValueError("Unknown application")
    suffix = " This opens your browser; ZIVRA cannot read messages." if name == "instagram" else ""
    return f"Launch request sent for {name}; application readiness is not verified." + suffix


def media_key(action):
    require_windows()
    code = MEDIA_KEYS[action]
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, 2, 0)
    return "Sent Windows media key to the active session; this is not Spotify-specific. Play/pause and mute are toggles."


class Startup:
    KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def enabled(self):
        if not IS_WINDOWS:
            return False
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.KEY) as key:
                return bool(winreg.QueryValueEx(key, "ZIVRA")[0])
        except FileNotFoundError:
            return False

    def set_enabled(self, enabled, *, approved=False):
        Permissions.confirm(approved)
        require_windows()
        import winreg
        executable = Path(sys.executable)
        windowed = executable.with_name("pythonw.exe")
        if not getattr(sys, "frozen", False) and windowed.is_file():
            executable = windowed
        argv = [str(executable)] if getattr(sys, "frozen", False) else [str(executable), "-m", "zivra"]
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, self.KEY) as key:
            if enabled:
                winreg.SetValueEx(key, "ZIVRA", 0, winreg.REG_SZ, subprocess.list2cmdline(argv))
            else:
                try:
                    winreg.DeleteValue(key, "ZIVRA")
                except FileNotFoundError:
                    pass
