"""An explicit allowlist, never imports from user-writable plugin directories.

Python builtins run in-process and are trusted application code. Capability checks
are an additional command boundary, not isolation for untrusted Python code.
"""
import threading
from zivra.core.permissions import Permissions
from zivra.plugins.base import Manifest, Plugin
from zivra.system.performance import system_report
from zivra.system.windows import launch_app, media_key, MEDIA_KEYS


def bundled(settings):
    return {
        "system": lambda: Plugin(Manifest("system", "System monitor", "0.3.0", "Read-only system information", ("status",), ("system.read",), ("psutil",)), lambda _: system_report()),
        "applications": lambda: Plugin(Manifest("applications", "Applications", "0.3.0", "Known Windows applications and approved executable aliases", ("launch",), ("applications.launch",), configuration_schema={"application_aliases": "alias → absolute .exe path"}), lambda intent: launch_app(intent.detail, settings.get("application_aliases"))),
        "media": lambda: Plugin(Manifest("media", "Windows media", "0.3.0", "Media keys for the active Windows session", tuple(MEDIA_KEYS), ("media.control",)), lambda intent: media_key(intent.action)),
    }


class PluginManager:
    def __init__(self, settings):
        self.settings = settings
        self.factories = bundled(settings)
        self.plugins = {}
        self.errors = {}
        self.lock = threading.RLock()
        for identifier in settings.get("enabled_plugins"):
            self._load(identifier)

    def _load(self, identifier):
        plugin = None
        try:
            plugin = self.factories[identifier]()
            if plugin.manifest.identifier != identifier:
                raise ValueError("Plugin identifier mismatch")
            Permissions().require(plugin.manifest.permissions)
            claimed = {c for p in self.plugins.values() for c in p.manifest.commands}
            if claimed.intersection(plugin.manifest.commands):
                raise ValueError("Plugin command conflict")
            plugin.initialize()
            self.plugins[identifier] = plugin
            self.errors.pop(identifier, None)
        except Exception as error:
            self.errors[identifier] = str(error)
            if plugin:
                try:
                    plugin.shutdown()
                except Exception:
                    pass

    def set_enabled(self, identifier, enabled):
        with self.lock:
            if identifier not in self.factories:
                raise PermissionError("Only bundled allowlisted plugins are supported")
            if enabled and identifier not in self.plugins:
                self._load(identifier)
                if identifier not in self.plugins:
                    raise RuntimeError(self.errors[identifier])
            elif not enabled:
                plugin = self.plugins.pop(identifier, None)
                if plugin:
                    plugin.shutdown()
                self.errors.pop(identifier, None)
            configured = set(self.settings.get("enabled_plugins"))
            configured.add(identifier) if enabled else configured.discard(identifier)
            self.settings.set("enabled_plugins", sorted(configured))

    def execute(self, intent):
        with self.lock:
            for plugin in self.plugins.values():
                if intent.action in plugin.manifest.commands:
                    Permissions().require(plugin.manifest.permissions)
                    return plugin.execute(intent)
        raise RuntimeError("Required plugin is disabled or unavailable. Check Plugins for its status")

    def status(self):
        with self.lock:
            return {identifier: self.errors.get(identifier) or (self.plugins[identifier].health() if identifier in self.plugins else "Disabled") for identifier in self.factories}

    def shutdown(self):
        with self.lock:
            for identifier, plugin in list(self.plugins.items()):
                try:
                    plugin.shutdown()
                except Exception as error:
                    self.errors[identifier] = str(error)
            self.plugins.clear()
