from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from manager.app.core.config import settings
from manager.app.database.database import engine, get_db
from manager.app.database.models import Deployment
from manager.app.database.repository import (
    database_stats,
    delete_container,
    get_container_record,
    list_deployments,
    list_machine_health,
    get_machine,
    list_machines,
    update_container_status,
)
from manager.app.services.container_service import agent_for, deploy
from manager.app.services.scheduler_service import scheduler_snapshot
from manager.app.services.machine_service import (
    all_machines,
    remove_machine,
    resolve_machine,
)

router = APIRouter()


class RunRequest(BaseModel):
    machine: str | list[str] | None = None
    replicas: int = Field(default=1, ge=1, le=100)
    image: str = Field(min_length=1)
    name_prefix: str | None = None
    env: list[str] = Field(default_factory=list)
    ports: dict[str, int | str] = Field(default_factory=dict)
    volumes: list[str] = Field(default_factory=list)
    network: str | None = None


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        database_stats(db)
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "database": db_status,
        "http_port": settings.http_port,
        "grpc_port": settings.grpc_port,
        "reconciliation": False,
    }


@router.get("/health/machines")
def machine_health(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    machines = list_machine_health(
        db,
        warning_after=settings.heartbeat_warning_seconds,
        offline_after=settings.heartbeat_offline_seconds,
    )
    if active_only:
        machines = [m for m in machines if m["active"]]
    return {"machines": machines}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return database_stats(db)


@router.get("/machines")
def machines(db: Session = Depends(get_db)):
    return {"machines": all_machines(db)}


@router.get("/deployments")
def deployments(
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    rows = list_deployments(db, active_only=active_only)
    return {
        "deployments": [
            {
                "id": row.id,
                "machine_id": row.machine_id,
                "image": row.image,
                "replicas": row.replicas,
                "name_prefix": row.name_prefix,
                "network": row.network,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "active": row.active,
            }
            for row in rows
        ]
    }


@router.delete("/machines/{machine_ref}")
def delete_machine(machine_ref: str, db: Session = Depends(get_db)):
    try:
        remove_machine(db, machine_ref)
        return {"ok": True}
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc


def _select_deployment_machine(db: Session, requested: str | list[str] | None):
    """Return (machine_ref, scheduling_info). Manual selection bypasses scoring."""
    if requested:
        # Validate the requested machine through the normal resolver.
        machine = get_machine(db, requested)
        if machine is None:
            raise ValueError(f"Machine '{requested}' not found")
        health = list_machine_health(
            db,
            warning_after=settings.heartbeat_warning_seconds,
            offline_after=settings.heartbeat_offline_seconds,
        )
        current = next((x for x in health if x["machine_id"] == str(machine.id)), None)
        if current and not current["active"]:
            raise ValueError(f"Machine '{machine.name}' is offline")
        return machine.name, {"mode": "manual", "selected": {
            "machine_id": str(machine.id), "name": machine.name,
        }}

    snapshot = scheduler_snapshot(
        db,
        settings.heartbeat_warning_seconds,
        settings.heartbeat_offline_seconds,
    )
    selected = snapshot.get("selected")
    if not selected:
        raise ValueError("No active machine is available for automatic scheduling")
    return selected["name"], {
        "mode": "weighted_resource_scheduler",
        "selected": selected,
        "ranking": snapshot.get("ranking", []),
        "weights": snapshot.get("weights", {}),
    }


def _active_machine_rows(db: Session):
    """Return only machines currently eligible for deployment."""
    health = list_machine_health(
        db,
        warning_after=settings.heartbeat_warning_seconds,
        offline_after=settings.heartbeat_offline_seconds,
    )
    active_ids = {str(item["machine_id"]) for item in health if item.get("active")}
    return [machine for machine in list_machines(db) if str(machine.id) in active_ids]


def _deploy_request(req: RunRequest, db: Session):
    """Deploy to automatic, all-active, one, or an explicit list of machines."""

    # Broadcast to every currently active machine. Replicas are per machine.
    if isinstance(req.machine, str) and req.machine.strip().lower() == "all":
        target_machines = _active_machine_rows(db)
        mode = "all-machines"

    # Explicit multi-machine selection from the UI/HTTP API.
    elif isinstance(req.machine, list):
        if not req.machine:
            raise ValueError("At least one machine must be selected")

        requested = []
        seen = set()
        for ref in req.machine:
            ref = str(ref).strip()
            if not ref or ref in seen:
                continue
            seen.add(ref)
            requested.append(ref)

        target_machines = []
        for ref in requested:
            machine = get_machine(db, ref)
            if machine is None:
                raise ValueError(f"Machine '{ref}' not found")
            health = list_machine_health(
                db,
                warning_after=settings.heartbeat_warning_seconds,
                offline_after=settings.heartbeat_offline_seconds,
            )
            current = next((x for x in health if x["machine_id"] == str(machine.id)), None)
            if not current or not current.get("active"):
                raise ValueError(f"Machine '{machine.name}' is offline")
            target_machines.append(machine)

        mode = "selected-machines"

    else:
        machine_ref, scheduling = _select_deployment_machine(db, req.machine)
        result = deploy(
            db,
            settings.cluster_token,
            machine_ref,
            req.image,
            req.replicas,
            req.name_prefix,
            req.env,
            req.ports,
            req.volumes,
            req.network,
        )
        result["scheduling"] = scheduling
        return result

    if not target_machines:
        raise ValueError("No active machines are available for deployment")

    results = []
    for machine in target_machines:
        try:
            result = deploy(
                db,
                settings.cluster_token,
                machine.name,
                req.image,
                req.replicas,
                req.name_prefix,
                req.env,
                req.ports,
                req.volumes,
                req.network,
            )
            result["ok"] = True
            results.append(result)
        except Exception as exc:
            results.append({
                "machine": machine.name,
                "ok": False,
                "error": str(exc),
            })

    succeeded = sum(1 for item in results if item.get("ok"))
    return {
        "mode": mode,
        "image": req.image,
        "replicas_per_machine": req.replicas,
        "target_machines": [m.name for m in target_machines],
        "successful_machines": succeeded,
        "failed_machines": len(target_machines) - succeeded,
        "results": results,
    }


@router.post("/deployments")
def run(req: RunRequest, db: Session = Depends(get_db)):
    """Deploy manually when machine is supplied, otherwise schedule automatically."""
    try:
        return _deploy_request(req, db)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Agent operation failed: {exc}") from exc


@router.post("/deployments/auto")
def run_auto(req: RunRequest, db: Session = Depends(get_db)):
    """Explicit automatic deployment endpoint used by the dashboard."""
    try:
        # Ignore any manually supplied machine for this endpoint: the scheduler owns placement.
        req.machine = None
        return _deploy_request(req, db)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, f"Agent operation failed: {exc}") from exc


def _target_machines(db: Session, machine: str | None):
    if machine:
        try:
            return [resolve_machine(db, machine)]
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
    return list_machines(db)


@router.get("/containers")
def containers(
    machine: str | None = Query(default=None),
    all_containers: bool = Query(default=True, alias="all"),
    db: Session = Depends(get_db),
):
    result = []

    for machine_row in _target_machines(db, machine):
        client = agent_for(machine_row, settings.cluster_token)
        try:
            response = client.list_containers(all_containers)
            for container in response.get("containers", []):
                container["machine_id"] = machine_row.id
                container["machine"] = machine_row.name
                result.append(container)
        except Exception as exc:
            result.append(
                {
                    "machine": machine_row.name,
                    "machine_id": machine_row.id,
                    "error": str(exc),
                }
            )
        finally:
            client.close()

    return {"containers": result}


@router.get("/images")
def images(
    machine: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    result = []

    for machine_row in _target_machines(db, machine):
        client = agent_for(machine_row, settings.cluster_token)
        try:
            response = client.list_images()
            for image in response.get("images", []):
                image["machine_id"] = machine_row.id
                image["machine"] = machine_row.name
                result.append(image)
        except Exception as exc:
            result.append(
                {
                    "machine": machine_row.name,
                    "machine_id": machine_row.id,
                    "error": str(exc),
                }
            )
        finally:
            client.close()

    return {"images": result}


def _find_container(db: Session, ref: str):
    for machine in list_machines(db):
        client = agent_for(machine, settings.cluster_token)
        try:
            response = client.list_containers(True)
            for container in response.get("containers", []):
                if (
                    container.get("id") == ref
                    or container.get("short_id") == ref
                    or container.get("name") == ref
                ):
                    return machine, container
        except Exception:
            continue
        finally:
            client.close()

    raise HTTPException(
        404,
        f"Container '{ref}' not found",
    )


@router.post("/machines/{machine_ref}/ping")
def ping_machine(machine_ref: str, db: Session = Depends(get_db)):
    try:
        machine = resolve_machine(db, machine_ref)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc

    client = agent_for(machine, settings.cluster_token)
    try:
        response = client.ping()
        return {
            "ok": True,
            "machine": machine.name,
            "agent": response,
        }
    except Exception as exc:
        raise HTTPException(
            503,
            f"Agent unavailable: {exc}",
        ) from exc
    finally:
        client.close()


@router.post("/containers/{ref}/start")
def start_container(
    ref: str,
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    container_id = container["id"]
    client = agent_for(machine, settings.cluster_token)

    try:
        result = client.start_container(container_id)
        update_container_status(db, container_id, "running")
        return {
            "ok": True,
            "action": "start",
            "container_id": container_id,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(502, f"Start failed: {exc}") from exc
    finally:
        client.close()


@router.post("/containers/{ref}/stop")
def stop_container(
    ref: str,
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    container_id = container["id"]
    client = agent_for(machine, settings.cluster_token)

    try:
        result = client.stop_container(container_id)
        update_container_status(db, container_id, "exited")
        return {
            "ok": True,
            "action": "stop",
            "container_id": container_id,
            "result": result,
            "message": "Container stopped. No reconciler will restart it.",
        }
    except Exception as exc:
        raise HTTPException(502, f"Stop failed: {exc}") from exc
    finally:
        client.close()


@router.post("/containers/{ref}/restart")
def restart_container(
    ref: str,
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    container_id = container["id"]
    client = agent_for(machine, settings.cluster_token)

    try:
        result = client.restart_container(container_id)
        update_container_status(db, container_id, "running")
        return {
            "ok": True,
            "action": "restart",
            "container_id": container_id,
            "result": result,
        }
    except Exception as exc:
        raise HTTPException(502, f"Restart failed: {exc}") from exc
    finally:
        client.close()


@router.delete("/containers/{ref}")
def remove_container(
    ref: str,
    force: bool = False,
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    container_id = container["id"]
    client = agent_for(machine, settings.cluster_token)

    try:
        record = get_container_record(db, container_id)
        deployment_id = record.deployment_id if record else None

        result = client.remove_container(
            container_id,
            force,
        )

        # Delete the Manager's record only after Docker confirms removal.
        delete_container(db, container_id)

        # Keep deployment metadata useful without any reconciliation.
        if deployment_id:
            deployment = db.get(
                Deployment,
                deployment_id,
            )
            if deployment:
                deployment.replicas = max(
                    0,
                    deployment.replicas - 1,
                )
                if deployment.replicas == 0:
                    deployment.active = False
                db.commit()

        return {
            "ok": True,
            "action": "remove",
            "container_id": container_id,
            "result": result,
            "message": "Container permanently removed. No reconciler will recreate it.",
        }
    except Exception as exc:
        raise HTTPException(502, f"Remove failed: {exc}") from exc
    finally:
        client.close()


@router.get("/containers/{ref}/inspect")
def inspect_container(
    ref: str,
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    client = agent_for(machine, settings.cluster_token)
    try:
        return client.inspect_container(container["id"])
    finally:
        client.close()


@router.get("/containers/{ref}/logs")
def logs(
    ref: str,
    tail: int = Query(default=200, ge=1, le=10000),
    db: Session = Depends(get_db),
):
    machine, container = _find_container(db, ref)
    client = agent_for(machine, settings.cluster_token)
    try:
        return client.logs(container["id"], tail)
    finally:
        client.close()


@router.get("/database")
def database_info(db: Session = Depends(get_db)):
    counts = database_stats(db)
    database_name = engine.url.database
    size_bytes = None
    resolved_path = None

    if database_name and engine.url.get_backend_name() == "sqlite":
        path = Path(database_name)
        if not path.is_absolute():
            path = Path.cwd() / path
        resolved_path = str(path)
        if path.exists():
            size_bytes = path.stat().st_size

    return {
        "backend": engine.url.get_backend_name(),
        "database": database_name,
        "resolved_path": resolved_path,
        "size_bytes": size_bytes,
        "counts": counts,
        "process_id": os.getpid(),
    }
