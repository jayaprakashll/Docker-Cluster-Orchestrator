"""Legacy state module.

Container reconciliation/self-healing is intentionally disabled.
This module only contains an optional machine-status refresh helper and is
NOT started by the Manager application.
"""

from __future__ import annotations

from datetime import datetime, timezone

from manager.app.core.config import settings
from manager.app.database.database import SessionLocal
from manager.app.database.repository import list_machines


def mark_stale_machines() -> None:
    """Update the cached Machine.status field from heartbeat age.

    The API also calculates health dynamically, so this function is optional.
    It never starts, stops, recreates, or removes containers.
    """
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        changed = False
        for machine in list_machines(db):
            last = machine.last_heartbeat
            if last is None:
                new_status = "offline"
            else:
                if last.tzinfo is None:
                    last = last.replace(tzinfo=timezone.utc)
                age = (now - last).total_seconds()
                if age > settings.heartbeat_offline_seconds:
                    new_status = "offline"
                elif age > settings.heartbeat_warning_seconds:
                    new_status = "warning"
                else:
                    new_status = "healthy"

            if machine.status != new_status:
                machine.status = new_status
                changed = True

        if changed:
            db.commit()


async def reconciler_loop(stop_event):
    """Compatibility stub. No container reconciliation is performed."""
    await stop_event.wait()
