from __future__ import annotations

from sqlalchemy.orm import Session

from manager.app.database.repository import delete_machine, get_machine, list_machines


def machine_to_dict(machine) -> dict:
    return {
        "id": str(machine.id),
        "machine_id": str(machine.id),
        "name": machine.name,
        "hostname": machine.hostname,
        "ip": machine.ip,
        "agent_port": machine.agent_port,
        "port": machine.agent_port,
        "cpu_count": machine.cpu_count,
        "memory_mb": machine.memory_mb,
        "docker_version": machine.docker_version,
        "status": machine.status,
        "last_heartbeat": machine.last_heartbeat.isoformat() if machine.last_heartbeat else None,
        "registered_at": machine.registered_at.isoformat() if machine.registered_at else None,
    }


def resolve_machine(db: Session, ref: str):
    machine = get_machine(db, ref)
    if not machine:
        raise ValueError(f"Machine '{ref}' not found")
    return machine


def all_machines(db: Session) -> list[dict]:
    return [machine_to_dict(m) for m in list_machines(db)]


def remove_machine(db: Session, ref: str) -> None:
    if not delete_machine(db, ref):
        raise ValueError(f"Machine '{ref}' not found")
