import importlib.util
from pathlib import Path
import pytest
from zivra.core.commands import Intent, classify


@pytest.mark.parametrize("query,expected", [
    ("Zivra, open Spotify.", Intent("launch", "spotify")),
    ("Zivra, what's using my RAM?", Intent("status")),
    ("open roblox", Intent("launch", "roblox")),
    ("connect to my phone", Intent("launch", "phonelink")),
    ("pause the music", Intent("media_toggle")),
    ("read my dms", Intent("messages_info")),
    ("organize my downloads", Intent("organize_info")),
    ("open editor", Intent("launch", "editor")),
    ("zivrahelp", Intent("unknown")),
    ("do not open spotify", Intent("unknown")),
    ("explain spotify", Intent("unknown")),
    ("delete files then open spotify", Intent("blocked")),
    ("open notepad & calc", Intent("blocked")),
    ("open notepad; shutdown", Intent("blocked")),
    ("a" * 513, Intent("blocked")),
])
def test_routing(query, expected):
    assert classify(query, {"editor": r"C:\Apps\editor.exe"}) == expected


def test_all_original_v2_voice_commands_preserved():
    # Load the supplied, untouched V2 parser as the migration reference.
    source = Path(__file__).parents[1] / "legacy/v2/zivra_core.py"
    spec = importlib.util.spec_from_file_location("original_v2", source)
    import sys
    original = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = original
    spec.loader.exec_module(original)
    for query in original.SUPPORTED_VOICE:
        old = original.classify(query)
        new = classify(query)
        assert (new.detail if new.action == "launch" else new.action) == old.action, query


def test_configured_alias_can_override_builtin_synonym():
    assert classify("open roblox studio", {"roblox studio": r"D:\Studio.exe"}) == Intent("launch", "roblox studio")
