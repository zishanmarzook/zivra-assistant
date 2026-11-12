"""Refactored V2 intents, using exact matches to prevent accidental actions."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Intent:
    action: str
    detail: str = ""


APPLICATIONS = {
    "spotify": "spotify", "instagram": "instagram", "phone link": "phonelink",
    "phone": "phonelink", "iphone": "phonelink", "ghostlink": "ghostlink",
    "files": "files", "file explorer": "files", "downloads": "downloads",
    "settings": "settings", "task manager": "taskmanager", "chrome": "chrome",
    "browser": "browser", "chatgpt": "chatgpt", "notepad": "notepad",
    "calculator": "calculator", "roblox studio": "roblox", "roblox": "roblox",
}
MEDIA = {
    "media_toggle": ("pause music", "resume music", "play music", "pause", "resume", "music pause", "pause the music", "pause spotify", "stop spotify", "resume spotify", "play spotify"),
    "media_next": ("next track", "next song", "skip track", "skip song", "next spotify track"),
    "media_previous": ("previous track", "previous song", "last song"),
    "volume_up": ("volume up", "increase volume", "louder"),
    "volume_down": ("volume down", "decrease volume", "quieter"),
    "volume_mute": ("mute volume", "unmute", "mute audio", "mute"),
}


def classify(command: str, aliases=()) -> Intent:
    if not isinstance(command, str) or len(command) > 512:
        return Intent("blocked")
    s = re.sub(r"\s+", " ", command.strip().lower())
    s = re.sub(r"^(?:(?:hey|okay|ok) )?zivra\b[,.:! ]*", "", s).strip().rstrip(".!?")
    if not s or s in ("help", "commands", "what can you do", "show commands"):
        return Intent("help")
    if re.search(r"\b(delete|wipe|format|shutdown|password|execute|terminal|powershell)\b", s) or any(c in s for c in ";\n&|`<>"):
        return Intent("blocked")
    if s in ("read my messages", "read instagram messages", "read my dms", "read my instagram", "read my texts"):
        return Intent("messages_info")
    if s in ("organize downloads", "organize my downloads", "organize files", "organize my files"):
        return Intent("organize_info")
    if s in ("status", "system status", "show system status", "system info", "ram", "memory", "cpu", "processor", "how much ram", "check ram", "what's using my ram", "what is using my ram"):
        return Intent("status")
    if s in ("connect to my phone", "connect my phone", "connect to my iphone"):
        return Intent("launch", "phonelink")
    for action, phrases in MEDIA.items():
        if s in phrases:
            return Intent(action)
    target = re.sub(r"^(open|launch|start) ", "", s)
    if target in aliases and s != target:
        return Intent("launch", target)
    if target in APPLICATIONS:
        return Intent("launch", APPLICATIONS[target])
    return Intent("unknown")
