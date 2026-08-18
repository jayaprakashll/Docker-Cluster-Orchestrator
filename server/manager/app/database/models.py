from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from manager.app.database.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    ip: Mapped[str] = mapped_column(String(64))
    agent_port: Mapped[int] = mapped_column(Integer, default=9001)
    cpu_count: Mapped[int] = mapped_column(Integer, default=0)
    memory_mb: Mapped[int] = mapped_column(Integer, default=0)
    docker_version: Mapped[str] = mapped_column(String(128), default="unknown")
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class ContainerRecord(Base):
    """A record of a container created through the Manager.

    There is deliberately NO desired-state/reconciliation field here.
    Docker is controlled only by explicit user actions.
    """

    __tablename__ = "containers"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True)
    image: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="unknown")
    deployment_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True)
    image: Mapped[str] = mapped_column(String(255))
    replicas: Mapped[int] = mapped_column(Integer)
    name_prefix: Mapped[str] = mapped_column(String(128))
    env_json: Mapped[str] = mapped_column(Text, default="[]")
    ports_json: Mapped[str] = mapped_column(Text, default="{}")
    volumes_json: Mapped[str] = mapped_column(Text, default="[]")
    network: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Heartbeat(Base):
    __tablename__ = "heartbeats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    cpu_percent: Mapped[float] = mapped_column(Float, default=0.0)
    memory_percent: Mapped[float] = mapped_column(Float, default=0.0)
    running_containers: Mapped[int] = mapped_column(Integer, default=0)
    health: Mapped[str] = mapped_column(String(32), default="unknown")
