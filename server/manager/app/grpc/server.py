from __future__ import annotations

import logging
from concurrent import futures
from datetime import datetime, timezone

import grpc

from common.rpc import dumps, loads
from manager.app.core.config import settings
from manager.app.database.database import SessionLocal
from manager.app.database.repository import save_heartbeat, upsert_machine

LOG = logging.getLogger(__name__)


class ManagerGrpcService:
    def __init__(self, token: str):
        self.token = token

    def _authorized(self, request: dict, context: grpc.ServicerContext) -> None:
        if request.get("token") != self.token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid cluster token")

    def register(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._authorized(request, context)
        required = ["machine_id", "name", "hostname", "ip"]
        missing = [x for x in required if not request.get(x)]
        if missing:
            context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                f"missing fields: {', '.join(missing)}",
            )
        try:
            with SessionLocal() as db:
                machine = upsert_machine(db, request)
        except ValueError as exc:
            context.abort(grpc.StatusCode.ALREADY_EXISTS, str(exc))
        except Exception as exc:
            LOG.exception("agent registration failed")
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

        LOG.info(
            "registered agent %s at %s:%s",
            machine.name,
            machine.ip,
            machine.agent_port,
        )
        return {
            "ok": True,
            "message": "registered",
            "machine_id": machine.id,
        }

    def heartbeat(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._authorized(request, context)
        if not request.get("machine_id"):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "machine_id required")
        try:
            with SessionLocal() as db:
                saved = save_heartbeat(db, request)
        except Exception as exc:
            LOG.exception("heartbeat persistence failed")
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

        if not saved:
            context.abort(grpc.StatusCode.NOT_FOUND, "machine is not registered")

        return {
            "ok": True,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }


def build_server() -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    service = ManagerGrpcService(settings.cluster_token)
    handlers = {
        "Register": grpc.unary_unary_rpc_method_handler(
            service.register,
            request_deserializer=loads,
            response_serializer=dumps,
        ),
        "Heartbeat": grpc.unary_unary_rpc_method_handler(
            service.heartbeat,
            request_deserializer=loads,
            response_serializer=dumps,
        ),
    }
    generic = grpc.method_handlers_generic_handler(
        "orchestrator.ManagerService",
        handlers,
    )
    server.add_generic_rpc_handlers((generic,))
    bound = server.add_insecure_port(f"{settings.host}:{settings.grpc_port}")
    if bound == 0:
        raise RuntimeError(
            f"Could not bind Manager gRPC to {settings.host}:{settings.grpc_port}"
        )
    return server
