"""Manual, bundled workflows. No user scripts or scheduled execution in Phase 1."""
from dataclasses import dataclass
from zivra.core.commands import Intent
from zivra.core.permissions import Permissions


@dataclass(frozen=True)
class Workflow:
    identifier: str
    actions: tuple[Intent, ...]
    permissions: tuple[str, ...]
    trigger: str = "manual"
    confirmation_required: bool = False
    failure_policy: str = "stop"


SYSTEM_REPORT = Workflow("system-report", (Intent("status"),), ("system.read",))


def run_workflow(workflow, execute, *, approved=False):
    Permissions().require(workflow.permissions)
    if workflow.confirmation_required:
        Permissions.confirm(approved)
    log = []
    for intent in workflow.actions:
        try:
            log.append(f"Completed {intent.action}:\n{execute(intent)}")
        except Exception as error:
            log.append(f"Failed {intent.action}: {error}. Workflow stopped.")
            break
    return "\n".join(log)
