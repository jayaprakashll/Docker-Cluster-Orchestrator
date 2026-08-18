from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from manager.app.database.models import (
    ContainerRecord,
    Deployment,
    Heartbeat,
    Machine,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def upsert_machine(db: Session, data: dict) -> Machine:
    machine_id = str(data["machine_id"])
    name = str(data["name"]).strip()
    hostname = str(data.get("hostname", "unknown"))
    ip = str(data.get("ip", "127.0.0.1"))

    machine = db.get(Machine, machine_id)

    if machine is None:
        existing_by_name = db.scalar(
            select(Machine).where(Machine.name == name)
        )
        if existing_by_name is not None:
            same_host = (
                existing_by_name.hostname == hostname
                or existing_by_name.ip == ip
            )
            if not same_host:
                raise ValueError(
                    f"Machine name '{name}' is already registered by "
                    f"{existing_by_name.hostname} ({existing_by_name.ip}). "
                    "Choose a unique --name for this PC."
                )
            machine = existing_by_name

    if machine is None:
        machine = Machine(
            id=machine_id,
            name=name,
            hostname=hostname,
            ip=ip,
            agent_port=int(data.get("agent_port", 9001)),
        )
        db.add(machine)

    machine.name = name
    machine.hostname = hostname
    machine.ip = ip
    machine.agent_port = int(data.get("agent_port", 9001))
    machine.cpu_count = int(data.get("cpu_count", 0))
    machine.memory_mb = int(data.get("memory_mb", 0))
    machine.docker_version = str(data.get("docker_version", "unknown"))
    machine.status = "healthy"
    machine.last_heartbeat = utcnow()

    db.commit()
    db.refresh(machine)
    return machine


def get_machine(db: Session, machine_ref: str) -> Machine | None:
    machine = db.get(Machine, machine_ref)
    if machine:
        return machine
    return db.scalar(select(Machine).where(Machine.name == machine_ref))


def list_machines(db: Session) -> list[Machine]:
    return list(db.scalars(select(Machine).order_by(Machine.name)).all())


def delete_machine(db: Session, machine_ref: str) -> bool:
    machine = get_machine(db, machine_ref)
    if not machine:
        return False
    db.delete(machine)
    db.commit()
    return True


def save_heartbeat(db: Session, data: dict) -> bool:
    machine = db.get(Machine, str(data.get("machine_id", "")))

    if machine is None and data.get("name"):
        machine = db.scalar(
            select(Machine).where(Machine.name == str(data["name"]))
        )

    if machine is None:
        return False

    now = utcnow()
    machine.cpu_count = int(data.get("cpu_count", machine.cpu_count))
    machine.memory_mb = int(data.get("memory_mb", machine.memory_mb))
    machine.docker_version = str(
        data.get("docker_version", machine.docker_version)
    )
    machine.ip = str(data.get("ip", machine.ip))
    machine.agent_port = int(data.get("agent_port", machine.agent_port))
    machine.status = "healthy"
    machine.last_heartbeat = now

    db.add(
        Heartbeat(
            machine_id=machine.id,
            timestamp=now,
            cpu_percent=float(data.get("cpu_percent", 0)),
            memory_percent=float(data.get("memory_percent", 0)),
            running_containers=int(data.get("running_containers", 0)),
            health=str(data.get("health", "healthy")),
        )
    )
    db.commit()
    return True


def get_latest_heartbeat(db: Session, machine_id: str) -> Heartbeat | None:
    return db.scalar(
        select(Heartbeat)
        .where(Heartbeat.machine_id == machine_id)
        .order_by(Heartbeat.timestamp.desc())
        .limit(1)
    )


def list_machine_health(
    db: Session,
    warning_after: int = 10,
    offline_after: int = 15,
) -> list[dict]:
    now = utcnow()
    result: list[dict] = []

    for machine in list_machines(db):
        heartbeat = get_latest_heartbeat(db, machine.id)
        timestamp = (
            _aware(heartbeat.timestamp)
            if heartbeat
            else _aware(machine.last_heartbeat)
        )
        age = (now - timestamp).total_seconds() if timestamp else None

        if age is None or age > offline_after:
            status = "offline"
        elif age > warning_after:
            status = "warning"
        else:
            status = "healthy"

        result.append(
            {
                "machine_id": str(machine.id),
                "id": str(machine.id),
                "name": machine.name,
                "hostname": machine.hostname,
                "ip": machine.ip,
                "port": machine.agent_port,
                "agent_port": machine.agent_port,
                "cpu_count": machine.cpu_count,
                "memory_mb": machine.memory_mb,
                "docker_version": machine.docker_version,
                "status": status,
                "active": status != "offline",
                "docker_available": bool(
                    machine.docker_version
                    and machine.docker_version != "unknown"
                ),
                "cpu_percent": heartbeat.cpu_percent if heartbeat else 0.0,
                "memory_percent": heartbeat.memory_percent if heartbeat else 0.0,
                "running_containers": (
                    heartbeat.running_containers if heartbeat else 0
                ),
                "heartbeat_health": heartbeat.health if heartbeat else "unknown",
                "last_heartbeat": timestamp.isoformat() if timestamp else None,
                "heartbeat_age_seconds": age,
                "registered_at": (
                    _aware(machine.registered_at).isoformat()
                    if machine.registered_at
                    else None
                ),
            }
        )

    return result


def save_container(
    db: Session,
    data: dict,
    deployment_id: str | None = None,
) -> ContainerRecord:
    existing = db.get(ContainerRecord, data["id"])

    if existing is None:
        existing = ContainerRecord(
            id=data["id"],
            name=data["name"],
            machine_id=data["machine_id"],
            image=data.get("image", "unknown"),
            status=data.get("status", "unknown"),
            deployment_id=deployment_id,
        )
        db.add(existing)
    else:
        existing.name = data["name"]
        existing.machine_id = data["machine_id"]
        existing.image = data.get("image", existing.image)
        existing.status = data.get("status", existing.status)
        if deployment_id:
            existing.deployment_id = deployment_id

    db.commit()
    db.refresh(existing)
    return existing


def update_container_status(
    db: Session,
    container_id: str,
    status: str,
) -> ContainerRecord | None:
    row = db.get(ContainerRecord, container_id)
    if row is None:
        return None
    row.status = status
    db.commit()
    db.refresh(row)
    return row


def get_container_record(
    db: Session,
    container_id: str,
) -> ContainerRecord | None:
    return db.get(ContainerRecord, container_id)


def delete_container(db: Session, container_id: str) -> bool:
    row = db.get(ContainerRecord, container_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def list_deployments(
    db: Session,
    active_only: bool = False,
) -> list[Deployment]:
    stmt = select(Deployment)
    if active_only:
        stmt = stmt.where(Deployment.active.is_(True))
    return list(
        db.scalars(stmt.order_by(Deployment.created_at.desc())).all()
    )


def database_stats(db: Session) -> dict:
    return {
        "machines": db.scalar(select(func.count()).select_from(Machine)) or 0,
        "containers": db.scalar(select(func.count()).select_from(ContainerRecord)) or 0,
        "deployments": db.scalar(select(func.count()).select_from(Deployment)) or 0,
        "active_deployments": db.scalar(
            select(func.count())
            .select_from(Deployment)
            .where(Deployment.active.is_(True))
        ) or 0,
        "heartbeats": db.scalar(select(func.count()).select_from(Heartbeat)) or 0,
    }
