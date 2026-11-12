from dataclasses import replace
import pytest
from zivra.config import Settings
from zivra.core.assistant import Assistant
from zivra.core.commands import Intent
from zivra.core.permissions import Permissions
from zivra.core.workflows import SYSTEM_REPORT, Workflow, run_workflow
from zivra.plugins.manager import PluginManager


def test_plugins_disable_persist_and_reenable(tmp_path):
    settings = Settings(tmp_path)
    manager = PluginManager(settings)
    manager.set_enabled("system", False)
    with pytest.raises(RuntimeError, match="disabled"):
        manager.execute(Intent("status"))
    restored = PluginManager(Settings(tmp_path))
    assert restored.status()["system"] == "Disabled"
    restored.set_enabled("system", True)
    assert "RAM:" in restored.execute(Intent("status"))
    with pytest.raises(PermissionError):
        restored.set_enabled("untrusted.py", True)


def test_broken_plugin_does_not_break_other_features(tmp_path):
    manager = PluginManager(Settings(tmp_path))
    manager.set_enabled("media", False)

    def broken():
        raise RuntimeError("Missing optional runtime")

    manager.factories["media"] = broken
    with pytest.raises(RuntimeError, match="Missing optional runtime"):
        manager.set_enabled("media", True)
    assert "Missing optional runtime" in manager.status()["media"]
    assert "RAM:" in manager.execute(Intent("status"))


def test_plugin_capabilities_are_checked_before_initialization(tmp_path):
    manager = PluginManager(Settings(tmp_path))
    manager.set_enabled("media", False)
    plugin = manager.factories["media"]()
    plugin.manifest = replace(plugin.manifest, permissions=("shell.execute",))
    manager.factories["media"] = lambda: plugin
    with pytest.raises(RuntimeError, match="approval"):
        manager.set_enabled("media", True)
    assert "media" not in manager.plugins


def test_permissions_require_explicit_consent():
    with pytest.raises(PermissionError):
        Permissions().require(["shell.execute"])
    with pytest.raises(PermissionError):
        Permissions.confirm(False)
    Permissions.confirm(True)


def test_workflow_stops_on_failure_and_requires_consent():
    calls = []

    def failing(intent):
        calls.append(intent)
        raise OSError("Unavailable")

    workflow = Workflow("test", (Intent("status"), Intent("status")), ("system.read",), confirmation_required=True)
    with pytest.raises(PermissionError):
        run_workflow(workflow, failing)
    assert not calls
    assert "Workflow stopped" in run_workflow(workflow, failing, approved=True)
    assert len(calls) == 1


def test_assistant_error_and_integration_fallbacks(tmp_path):
    assistant = Assistant(Settings(tmp_path))
    assert "does not scrape" in assistant.respond("read my messages")
    assert "rule-based" in assistant.respond("tell me a story")
    assert "No files were changed" in assistant.respond("organize downloads")
    assistant.plugins.set_enabled("applications", False)
    assert "disabled or unavailable" in assistant.respond("open spotify")
    assert "Completed status" in assistant.system_workflow()
