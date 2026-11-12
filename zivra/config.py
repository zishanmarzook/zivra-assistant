"""Versioned local preferences. Credentials do not belong in this database."""
from contextlib import contextmanager
import json
import ntpath
import os
from pathlib import Path
import re
import sqlite3

DEFAULTS = {"enabled_plugins": ["system", "applications", "media"],
            "application_aliases": {}, "remember_history": False,
            "minimize_to_tray": True}


def data_directory() -> Path:
    if os.environ.get("ZIVRA_DATA_DIR"):
        return Path(os.environ["ZIVRA_DATA_DIR"]).expanduser().resolve()
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "ZIVRA"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "zivra"


def validate_setting(key, value):
    if key not in DEFAULTS:
        raise ValueError(f"Unknown setting: {key}")
    if key in ("remember_history", "minimize_to_tray") and type(value) is not bool:
        raise ValueError("Expected a boolean preference")
    if key == "enabled_plugins" and (not isinstance(value, list) or
            any(x not in {"system", "applications", "media"} for x in value)):
        raise ValueError("Only bundled plugins may be enabled")
    if key == "application_aliases":
        if not isinstance(value, dict):
            raise ValueError("Expected application aliases")
        for alias, path in value.items():
            if not re.fullmatch(r"[a-z0-9][a-z0-9 _-]{0,39}", alias):
                raise ValueError("Use 1–40 lowercase letters, numbers, spaces, _ or - for an alias")
            if not isinstance(path, str) or not ntpath.isabs(path) or not ntpath.splitdrive(path)[0] or ntpath.splitext(path)[1].lower() != ".exe" or '"' in path or "\x00" in path:
                raise ValueError("Select an absolute .exe path; command arguments and scripts are not supported")


class Settings:
    def __init__(self, directory=None):
        self.directory = Path(directory) if directory else data_directory()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "settings.sqlite3"
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("Settings were created by a newer ZIVRA; use that version")
            if version == 0:
                db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                db.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, command TEXT NOT NULL, response TEXT NOT NULL)")
                db.execute("PRAGMA user_version=1")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, key):
        if key not in DEFAULTS:
            raise KeyError(key)
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        value = json.loads(row[0]) if row else json.loads(json.dumps(DEFAULTS[key]))
        validate_setting(key, value)
        return value

    def set(self, key, value):
        validate_setting(key, value)
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, json.dumps(value)))
            if key == "remember_history" and not value:
                db.execute("DELETE FROM history")

    def record(self, command, response):
        with self.connect() as db:
            # Read consent in the same transaction as the write.
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT value FROM settings WHERE key='remember_history'").fetchone()
            if row and json.loads(row[0]) is True:
                db.execute("INSERT INTO history(command,response) VALUES (?,?)", (command, response))
                db.execute("DELETE FROM history WHERE id NOT IN (SELECT id FROM history ORDER BY id DESC LIMIT 200)")

    def history(self):
        if not self.get("remember_history"):
            return []
        with self.connect() as db:
            return db.execute("SELECT command,response FROM history ORDER BY id").fetchall()

    def clear_history(self):
        with self.connect() as db:
            db.execute("DELETE FROM history")

    def export(self, destination):
        Path(destination).write_text(json.dumps({key: self.get(key) for key in DEFAULTS}, indent=2), encoding="utf-8")

    def reset(self):
        with self.connect() as db:
            db.execute("DELETE FROM settings")
            db.execute("DELETE FROM history")
