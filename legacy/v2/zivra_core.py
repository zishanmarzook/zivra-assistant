"""ZIVRA v2 command classification: deliberately restricted to explicit safe commands.
No arbitrary shell execution, message scraping, or access to private accounts.
"""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Intent:
    action: str
    detail: str = ""


def classify(command: str) -> Intent:
    s = re.sub(r"\s+", " ", command.strip().lower())
    s = re.sub(r"^(?:hey |okay |ok )?(?:zivra|zivra,|zivra:)[,.:! ]*", "", s).strip()
    if not s:
        return Intent("help")
    if s in ("help", "commands", "what can you do", "show commands"):
        return Intent("help")
    if any(x in s for x in ("read my messages", "read instagram messages", "read my dms", "read my instagram", "read my texts")):
        return Intent("messages_info")
    if "instagram" in s or "dms" in s or "inbox" in s:
        return Intent("instagram")
    if "phone" in s and any(x in s for x in ("connect", "link", "open", "launch", "iphone", "my")):
        return Intent("phonelink")
    if "ghostlink" in s or "send files" in s or "transfer files" in s:
        return Intent("ghostlink")
    if "spotify" in s:
        if any(x in s for x in ("pause", "stop", "mute")):
            return Intent("media_toggle")
        if "next" in s or "skip" in s:
            return Intent("media_next")
        if "previous" in s or "back" in s:
            return Intent("media_previous")
        return Intent("spotify")
    for action, expressions in (
        ("media_next", ("next track", "next song", "skip track", "skip song")),
        ("media_previous", ("previous track", "previous song", "last song")),
        ("media_toggle", ("pause music", "resume music", "play music", "pause", "resume", "music pause")),
        ("volume_up", ("volume up", "increase volume", "louder")),
        ("volume_down", ("volume down", "decrease volume", "quieter")),
        ("volume_mute", ("mute volume", "unmute", "mute audio", "mute")),
        ("status", ("status", "system status", "system info", "ram", "memory", "cpu", "processor", "how much ram", "check ram")),
    ):
        if any(s == e or s.endswith(" " + e) for e in expressions):
            return Intent(action)
    for target, action in (
        ("task manager", "taskmanager"),
        ("file explorer", "files"),
        ("files", "files"),
        ("downloads", "downloads"),
        ("settings", "settings"),
        ("chrome", "chrome"),
        ("browser", "browser"),
        ("chatgpt", "chatgpt"),
        ("notepad", "notepad"),
        ("calculator", "calculator"),
        ("roblox studio", "roblox"),
    ):
        if s == target or s in ("open " + target, "launch " + target, "start " + target):
            return Intent(action)
    if "organize" in s and any(w in s for w in ("download", "file", "folder")):
        return Intent("organize_info")
    if any(w in s for w in ("delete", "wipe", "format", "shutdown", "password", "execute", "terminal", "powershell")):
        return Intent("blocked")
    return Intent("unknown", command.strip())

SUPPORTED_VOICE = (
    "hey zivra open spotify", "hey zivra open chrome", "hey zivra open files",
    "hey zivra open settings", "hey zivra open chatgpt", "hey zivra open ghostlink",
    "hey zivra open instagram", "hey zivra open phone link",
    "hey zivra system status", "hey zivra pause music", "hey zivra next song",
    "hey zivra previous song", "hey zivra volume up", "hey zivra volume down",
    "hey zivra mute", "hey zivra help",
    "open spotify", "open chrome", "open files", "open settings",
    "open chatgpt", "open ghostlink", "open instagram", "open phone link",
    "system status", "pause music", "next song", "previous song",
    "volume up", "volume down", "mute", "help"
)
