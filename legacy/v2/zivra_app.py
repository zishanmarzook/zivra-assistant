"""ZIVRA v2, private local Windows command console. Python stdlib only.
Microphone listens only upon an explicit click. This app never reads Instagram DMs.
"""
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

from zivra_core import classify

BG = "#090A0C"
PANEL = "#121418"
PANEL2 = "#1C1F24"
EDGE = "#32363C"
WHITE = "#F4F5F6"
SOFT = "#B9BDC3"
MUTED = "#818790"


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]
    def value(self):
        return (self.dwHighDateTime << 32) | self.dwLowDateTime


class CpuSampler:
    def __init__(self):
        self.last = None

    def sample(self):
        if os.name != "nt":
            return None
        idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        current = (idle.value(), kernel.value(), user.value())
        previous, self.last = self.last, current
        if previous is None:
            return None
        idle_diff = current[0] - previous[0]
        total = current[1] - previous[1] + current[2] - previous[2]
        return max(0, min(100, round(100 * (1 - idle_diff / total)))) if total > 0 else None


def memory_usage():
    if os.name != "nt":
        return None
    state = MEMORYSTATUSEX()
    state.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
        return int(state.dwMemoryLoad)
    return None


def media_key(virtual_code):
    if os.name != "nt":
        return False
    # Windows hardware media keys; controls the currently focused media session.
    ctypes.windll.user32.keybd_event(virtual_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(virtual_code, 0, 2, 0)
    return True


def start_known_app(name):
    if name == "files":
        subprocess.Popen(["explorer.exe"])
    elif name == "downloads":
        os.startfile(str(Path.home() / "Downloads"))
    elif name == "settings":
        os.startfile("ms-settings:")
    elif name == "taskmanager":
        subprocess.Popen(["taskmgr.exe"])
    elif name == "notepad":
        subprocess.Popen(["notepad.exe"])
    elif name == "calculator":
        subprocess.Popen(["calc.exe"])
    elif name == "chrome":
        # Windows default browser, previously set to Chrome by the user.
        webbrowser.open("https://www.google.com/")
    elif name == "browser":
        webbrowser.open("https://www.google.com/")
    elif name == "chatgpt":
        webbrowser.open("https://chatgpt.com/")
    elif name == "spotify":
        # Local application protocol if Spotify installed, otherwise Spotify web app.
        try:
            os.startfile("spotify:")
        except OSError:
            webbrowser.open("https://open.spotify.com/")
    elif name == "instagram":
        webbrowser.open("https://www.instagram.com/direct/inbox/")
    elif name == "phonelink":
        # The built-in Windows 11 Phone Link UWP package.
        subprocess.Popen(["explorer.exe", r"shell:AppsFolder\Microsoft.YourPhone_8wekyb3d8bbwe!App"])
    elif name == "ghostlink":
        downloads = Path.home() / "Downloads"
        candidates = [downloads / "GhostLink" / "start_windows.bat"]
        candidates.extend(downloads.glob("GhostLink*/*/start_windows.bat"))
        candidates.extend(downloads.glob("GhostLink*/start_windows.bat"))
        for candidate in candidates:
            if candidate.is_file():
                os.startfile(str(candidate))
                return
        raise FileNotFoundError("GhostLink not located in Downloads. Launch it manually or place its folder there.")
    elif name == "roblox":
        binaries = sorted((Path.home() / "AppData/Local/Roblox/Versions").glob("*/RobloxStudioBeta.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
        if binaries:
            subprocess.Popen([str(binaries[0])])
        else:
            webbrowser.open("https://create.roblox.com/")
    else:
        raise ValueError("Unrecognized action")


class Zivra:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ZIVRA / Personal Console v2")
        self.root.geometry("558x790")
        self.root.minsize(490, 750)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.root.iconify)
        self.root.bind("<Escape>", lambda event: self.root.iconify())
        self.cpu = CpuSampler()
        self.listening = False
        self.reactor_rotation = 0
        self.build()
        self.tick()
        self.log("ZIVRA", "Command core ready. Private, local, no API key required.")
        self.log("ZIVRA", "Voice is push-to-talk. Tap LISTEN to activate your microphone.")

    def label(self, parent, text, size=10, fg=WHITE, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=fg,
                        font=("Consolas", size, "bold" if bold else "normal"), **kw)

    def button(self, parent, text, command, width=16):
        b = tk.Button(parent, text=text, command=command, bg=PANEL2, fg=WHITE,
                      activebackground="#343941", activeforeground=WHITE,
                      relief="flat", bd=0, cursor="hand2", width=width, pady=7,
                      font=("Consolas", 10, "bold"))
        return b

    def build(self):
        outer = tk.Frame(self.root, bg=BG, padx=26, pady=20)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x")
        self.label(header, "Z / I / V / R / A", 21, WHITE, True).pack(anchor="w")
        self.label(header, "PERSONAL SYSTEM  //  BUILD 02  //  LOCAL-FIRST", 9, MUTED).pack(anchor="w", pady=(3, 0))
        tk.Frame(outer, height=1, bg=EDGE).pack(fill="x", pady=(18, 10))

        hero = tk.Frame(outer, bg=BG)
        hero.pack(fill="x")
        self.orb = tk.Canvas(hero, width=125, height=125, bg=BG, highlightthickness=0)
        self.orb.pack(side="left")
        right = tk.Frame(hero, bg=BG)
        right.pack(side="left", padx=(19, 0), fill="both", expand=True)
        self.label(right, "SYSTEM CORE", 11, SOFT, True).pack(anchor="w", pady=(10, 4))
        self.label(right, "ONLINE / OFFLINE COMMANDS", 9, MUTED).pack(anchor="w")
        self.cpu_label = self.label(right, "CPU  --%  /  RAM  --%", 10, WHITE)
        self.cpu_label.pack(anchor="w", pady=(12, 0))
        self.label(right, "NO CLOUD CONNECTION REQUIRED", 8, MUTED).pack(anchor="w", pady=(6, 0))

        tk.Frame(outer, height=1, bg=EDGE).pack(fill="x", pady=(12, 13))
        self.label(outer, "01 / COMMAND INPUT", 10, SOFT, True).pack(anchor="w", pady=(0, 7))
        entryrow = tk.Frame(outer, bg=BG)
        entryrow.pack(fill="x")
        self.entry = tk.Entry(entryrow, bg=PANEL2, fg=WHITE, insertbackground=WHITE,
                              relief="flat", font=("Consolas", 11), bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=13, padx=(0, 7))
        self.entry.bind("<Return>", lambda event: self.submit())
        self.button(entryrow, "SEND", self.submit, 8).pack(side="right")
        self.entry.insert(0, "open spotify")
        voice_row = tk.Frame(outer, bg=BG)
        voice_row.pack(fill="x", pady=(8, 0))
        self.listen_button = self.button(voice_row, "LISTEN ONCE", self.listen, 16)
        self.listen_button.pack(side="left")
        self.label(voice_row, "MIC OFF until you click", 9, MUTED).pack(side="left", padx=13)
        self.label(outer, "02 / QUICK COMMANDS", 10, SOFT, True).pack(anchor="w", pady=(19, 8))
        commands = [
            [("SPOTIFY", "open spotify"), ("PHONE LINK", "open phone link"), ("INSTAGRAM", "open instagram")],
            [("FILES", "open files"), ("GHOSTLINK", "open ghostlink"), ("STATUS", "system status")],
            [("MUSIC  ◀", "previous song"), ("PAUSE / PLAY", "pause music"), ("MUSIC  ▶", "next song")],
        ]
        for group in commands:
            row = tk.Frame(outer, bg=BG)
            row.pack(fill="x", pady=3)
            for text, query in group:
                self.button(row, text, lambda q=query: self.handle(q), 14).pack(side="left", expand=True, fill="x", padx=2)
        self.label(outer, "03 / RESPONSE LOG", 10, SOFT, True).pack(anchor="w", pady=(17, 8))
        self.log_area = tk.Text(outer, height=5, bg=PANEL, fg=WHITE, insertbackground=WHITE,
                                selectbackground="#4B5058", relief="flat", bd=0,
                                font=("Consolas", 10), wrap="word", padx=12, pady=12,
                                state="disabled")
        self.log_area.pack(fill="both", expand=True)
        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(11, 0))
        self.label(footer, "NO BACKGROUND MIC • NO MESSAGE ACCESS", 8, MUTED).pack(side="left")
        self.button(footer, "QUIT", self.quit, 7).pack(side="right")

    def log(self, speaker, message):
        self.log_area.config(state="normal")
        self.log_area.insert("end", f"{speaker}  >  {message}\n\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def submit(self):
        command = self.entry.get().strip()
        self.entry.delete(0, "end")
        self.handle(command)

    def handle(self, command):
        if not command:
            return
        self.log("YOU", command)
        intent = classify(command)
        action = intent.action
        try:
            if action == "help":
                self.log("ZIVRA", "Try: open Spotify / Instagram / Phone Link / GhostLink / Chrome / Files; system status; pause music; next song; volume up. Voice: LISTEN ONCE.")
            elif action in ("files", "downloads", "settings", "taskmanager", "notepad", "calculator", "chrome", "browser", "chatgpt", "spotify", "instagram", "phonelink", "ghostlink", "roblox"):
                start_known_app(action)
                extra = {
                    "instagram": "Opened Instagram inbox in your default browser. I cannot read your private DMs from here.",
                    "phonelink": "Opened Phone Link (if installed). Pair your iPhone via Bluetooth in Phone Link.",
                    "spotify": "Opened Spotify. ZIVRA also supports your PC's media keys.",
                }
                self.log("ZIVRA", extra.get(action, f"Opening {action}..."))
            elif action in ("media_toggle", "media_next", "media_previous", "volume_up", "volume_down", "volume_mute"):
                keys = {"media_toggle":0xB3, "media_next":0xB0, "media_previous":0xB1,
                        "volume_up":0xAF, "volume_down":0xAE, "volume_mute":0xAD}
                if media_key(keys[action]):
                    self.log("ZIVRA", "Sent Windows media key. It controls the current media session, not Spotify specifically.")
                else:
                    self.log("ZIVRA", "Media keys are available on Windows only.")
            elif action == "status":
                ram = memory_usage()
                cpu = self.cpu.sample()
                used = f"Memory: {ram}%" if ram is not None else "Memory: unavailable"
                used += f" | CPU: {cpu}%" if cpu is not None else " | CPU: sampling..."
                try:
                    total, used_disk, free = shutil.disk_usage(Path.home().anchor)
                    used += f" | Disk free: {free / 1024 ** 3:.1f} GB"
                except OSError:
                    pass
                self.log("ZIVRA", used)
            elif action == "messages_info":
                self.log("ZIVRA", "Direct Instagram DM reading isn't connected. The official API requires an eligible professional account and Meta permissions. I can open your inbox, but won't scrape your private account.")
            elif action == "organize_info":
                self.log("ZIVRA", "Automatic file moves aren't enabled yet. We'll add preview-and-confirm before changing folders.")
            elif action == "blocked":
                self.log("ZIVRA", "That command is deliberately disabled. No arbitrary code, destructive actions, or account access.")
            else:
                self.log("ZIVRA", "Not a recognized local command yet. Try 'help'. Conversational AI can be added later with an explicitly connected provider.")
        except Exception as error:
            self.log("ZIVRA", f"Could not complete action: {error}")

    def listen(self):
        if self.listening:
            return
        self.listening = True
        self.listen_button.config(state="disabled", text="LISTENING...")
        self.log("ZIVRA", "Listening for one supported command (8 seconds max).")
        def job():
            script = Path(__file__).with_name("recognize_once.ps1")
            try:
                result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                                        capture_output=True, text=True, timeout=19, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                lines = (result.stdout or "").splitlines()
                recognized = next((s[8:] for s in lines if s.startswith("RESULT::")), None)
                err = next((s[7:] for s in lines if s.startswith("ERROR::")), "Voice recognition unavailable on this Windows installation.")
                self.root.after(0, lambda: self.voice_result(recognized, err))
            except Exception as exc:
                self.root.after(0, lambda message=str(exc): self.voice_result(None, message))
        threading.Thread(target=job, daemon=True).start()

    def voice_result(self, recognized, error):
        self.listening = False
        self.listen_button.config(state="normal", text="LISTEN ONCE")
        if recognized:
            self.handle(recognized)
        else:
            self.log("ZIVRA", error + " You can use Win+H while focused on the text box.")

    def tick(self):
        self.reactor_rotation = (self.reactor_rotation + 7) % 360
        c = self.orb
        c.delete("all")
        for radius, width, dash, offset in ((49, 2, None, 0), (38, 1, None, 0), (22, 1, None, 0)):
            c.create_oval(62-radius, 62-radius, 62+radius, 62+radius,
                          outline="#5A616B" if radius == 49 else "#32373F", width=width)
        c.create_arc(8, 8, 116, 116, start=self.reactor_rotation, extent=115, outline=WHITE,
                     width=3, style="arc")
        c.create_arc(24, 24, 100, 100, start=-self.reactor_rotation*1.5, extent=115,
                     outline=SOFT, width=2, style="arc")
        c.create_oval(53, 53, 71, 71, outline=WHITE, width=2)
        c.create_oval(59, 59, 65, 65, fill=WHITE, outline=WHITE)
        if self.root.winfo_exists():
            ram, cpu = memory_usage(), self.cpu.sample()
            self.cpu_label.config(text=f"CPU  {cpu if cpu is not None else '--'}%  /  RAM  {ram if ram is not None else '--'}%")
            self.root.after(1600, self.tick)

    def quit(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    Zivra().run()
