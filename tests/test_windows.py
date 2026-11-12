from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from zivra.system import windows


def test_launch_alias_uses_argument_vector_without_shell(tmp_path, monkeypatch):
    exe = tmp_path / "Trusted App.exe"
    exe.touch()
    popen = Mock()
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    monkeypatch.setattr(windows.subprocess, "Popen", popen)
    windows.launch_app("editor", {"editor": str(exe)})
    popen.assert_called_once_with([str(exe)], shell=False)


def test_unknown_or_missing_app_does_not_launch(tmp_path, monkeypatch):
    popen = Mock()
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    monkeypatch.setattr(windows.subprocess, "Popen", popen)
    with pytest.raises(FileNotFoundError):
        windows.launch_app("editor", {"editor": str(tmp_path / "missing.exe")})
    with pytest.raises(ValueError):
        windows.launch_app("untrusted shell command", {})
    popen.assert_not_called()


def test_chrome_never_claims_default_browser_is_chrome(monkeypatch, tmp_path):
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        monkeypatch.setenv(key, str(tmp_path))
    with pytest.raises(FileNotFoundError, match="Chrome was not found"):
        windows.launch_app("chrome", {})


def test_spotify_protocol_failure_uses_browser_fallback(monkeypatch):
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    monkeypatch.setattr(windows.os, "startfile", Mock(side_effect=OSError("No protocol")), raising=False)
    browser = Mock(return_value=True)
    monkeypatch.setattr(windows.webbrowser, "open", browser)
    assert "Spotify web" in windows.launch_app("spotify", {})
    browser.assert_called_once_with("https://open.spotify.com/")


def test_non_windows_rejects_platform_actions(monkeypatch):
    monkeypatch.setattr(windows, "IS_WINDOWS", False)
    with pytest.raises(OSError, match="requires Windows"):
        windows.launch_app("notepad", {})
    with pytest.raises(OSError, match="requires Windows"):
        windows.media_key("media_toggle")


def test_media_key_sends_down_and_up(monkeypatch):
    key = Mock()
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    monkeypatch.setattr(windows.ctypes, "windll", SimpleNamespace(user32=SimpleNamespace(keybd_event=key)), raising=False)
    assert "not Spotify-specific" in windows.media_key("media_toggle")
    assert key.call_args_list[0].args == (0xB3, 0, 0, 0)
    assert key.call_args_list[1].args == (0xB3, 0, 2, 0)


def test_startup_registry_requires_confirmation_and_is_reversible(monkeypatch):
    import sys
    registry = {}
    context = Mock()
    context.__enter__ = Mock(return_value="key")
    context.__exit__ = Mock(return_value=False)
    winreg = SimpleNamespace(HKEY_CURRENT_USER="user", REG_SZ=1,
        CreateKey=Mock(return_value=context), OpenKey=Mock(return_value=context),
        SetValueEx=lambda key, name, reserved, type_, value: registry.update({name: value}),
        DeleteValue=lambda key, name: registry.pop(name),
        QueryValueEx=lambda key, name: (registry[name], 1))
    monkeypatch.setitem(sys.modules, "winreg", winreg)
    monkeypatch.setattr(windows, "IS_WINDOWS", True)
    startup = windows.Startup()
    with pytest.raises(PermissionError):
        startup.set_enabled(True)
    assert not registry
    startup.set_enabled(True, approved=True)
    assert startup.enabled()
    assert "zivra" in registry["ZIVRA"]
    startup.set_enabled(False, approved=True)
    assert not registry
