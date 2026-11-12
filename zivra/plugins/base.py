from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Manifest:
    identifier: str
    name: str
    version: str
    description: str
    commands: tuple[str, ...]
    permissions: tuple[str, ...]
    dependencies: tuple[str, ...] = ()
    configuration_schema: dict = field(default_factory=dict)


class Plugin:
    def __init__(self, manifest: Manifest, handler: Callable):
        self.manifest = manifest
        self.handler = handler

    def initialize(self):
        """Allocate resources here when a bundled plugin needs them."""

    def shutdown(self):
        """Release any owned resources. Builtins are stateless."""

    def health(self):
        return "Loaded locally; external connections are not established"

    def execute(self, intent):
        return self.handler(intent)
