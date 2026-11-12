import json
import sqlite3
import pytest
from zivra.config import Settings


def test_preferences_persist_and_history_is_opt_in(tmp_path):
    settings = Settings(tmp_path)
    settings.record("private command", "answer")
    assert settings.history() == []
    settings.set("application_aliases", {"editor": r"C:\Apps\editor.exe"})
    settings.set("remember_history", True)
    settings.record("help", "commands")
    restored = Settings(tmp_path)
    assert restored.get("application_aliases") == {"editor": r"C:\Apps\editor.exe"}
    assert restored.history() == [("help", "commands")]
    restored.set("remember_history", False)
    with restored.connect() as db:
        assert db.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0


def test_export_and_reset(tmp_path):
    settings = Settings(tmp_path)
    settings.set("remember_history", True)
    settings.record("do not export me", "private")
    export = tmp_path / "export.json"
    settings.export(export)
    assert "do not export me" not in export.read_text()
    assert json.loads(export.read_text())["remember_history"] is True
    settings.reset()
    assert settings.history() == []
    assert settings.get("remember_history") is False


@pytest.mark.parametrize("value", [{"bad": "cmd /c calc"}, {"app": r"C:\run.bat"}, {"app": "relative.exe"}, {"app": r"\relative.exe"}, {"app": 'C:\\run.exe" --bad'}, {"Bad Alias": r"C:\run.exe"}])
def test_invalid_aliases_rejected(tmp_path, value):
    with pytest.raises(ValueError):
        Settings(tmp_path).set("application_aliases", value)


def test_schema_migrates_without_erasing_preferences_and_rejects_future(tmp_path):
    settings = Settings(tmp_path)
    settings.set("remember_history", True)
    with settings.connect() as db:
        db.execute("PRAGMA user_version=0")
    assert Settings(tmp_path).get("remember_history") is True
    with settings.connect() as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(RuntimeError, match="newer ZIVRA"):
        Settings(tmp_path)


def test_history_is_bounded(tmp_path):
    settings = Settings(tmp_path)
    settings.set("remember_history", True)
    for i in range(205):
        settings.record(str(i), "answer")
    assert len(settings.history()) == 200
    assert settings.history()[0][0] == "5"
