"""Capabilities describe trusted builtins, not a sandbox for Python plugins."""
SAFE_CAPABILITIES = frozenset({"system.read", "applications.launch", "media.control"})


class Permissions:
    def require(self, capabilities):
        missing = set(capabilities) - SAFE_CAPABILITIES
        if missing:
            raise PermissionError("Capability requires explicit approval: " + ", ".join(sorted(missing)))

    @staticmethod
    def confirm(approved: bool):
        if approved is not True:
            raise PermissionError("Explicit user confirmation is required")
