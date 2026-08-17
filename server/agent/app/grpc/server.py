from __future__ import annotations

import logging
from concurrent import futures

import grpc

from common.rpc import dumps, loads
from agent.app.core.config import AgentConfig
from agent.app.docker.container_manager import ContainerManager
from agent.app.docker.docker_client import DockerClient

LOG = logging.getLogger(__name__)


class AgentGrpcService:
    def __init__(self, config: AgentConfig, containers: ContainerManager, docker_client: DockerClient):
        self.config = config
        self.containers = containers
        self.docker_client = docker_client

    def _auth(self, request: dict, context: grpc.ServicerContext):
        if request.get("token") != self.config.token:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid cluster token")

    def ping(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            version = self.docker_client.version()
        except Exception as exc:
            context.abort(grpc.StatusCode.UNAVAILABLE, str(exc))
        return {
            "ok": True,
            "machine_id": self.config.machine_id,
            "name": self.config.name,
            "docker_version": version,
        }

    def list_containers(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        return {
            "ok": True,
            "containers": self.containers.list_containers(
                bool(request.get("all", True))
            ),
        }

    def list_images(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        return {"ok": True, "images": self.containers.list_images()}

    def create_containers(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            items = self.containers.create_containers(
                image=request["image"],
                replicas=int(request["replicas"]),
                name_prefix=request["name_prefix"],
                env=request.get("env"),
                ports=request.get("ports"),
                volumes=request.get("volumes"),
                network=request.get("network"),
                labels=request.get("labels"),
            )
            return {"ok": True, "containers": items}
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except Exception as exc:
            LOG.exception("create containers failed")
            context.abort(grpc.StatusCode.INTERNAL, str(exc))

    def start_container(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {"ok": True, "container": self.containers.start(request["container_id"])}
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def stop_container(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {"ok": True, "container": self.containers.stop(request["container_id"])}
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def restart_container(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {"ok": True, "container": self.containers.restart(request["container_id"])}
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def remove_container(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {
                "ok": True,
                "container": self.containers.remove(
                    request["container_id"],
                    bool(request.get("force", False)),
                ),
            }
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def inspect_container(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {"ok": True, "inspect": self.containers.inspect(request["container_id"])}
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))

    def logs(self, request: dict, context: grpc.ServicerContext) -> dict:
        self._auth(request, context)
        try:
            return {
                "ok": True,
                "logs": self.containers.logs(
                    request["container_id"],
                    int(request.get("tail", 200)),
                ),
            }
        except Exception as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))


def build_server(config: AgentConfig, containers: ContainerManager, docker_client: DockerClient) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    service = AgentGrpcService(config, containers, docker_client)
    handlers = {
        "Ping": grpc.unary_unary_rpc_method_handler(service.ping, request_deserializer=loads, response_serializer=dumps),
        "ListContainers": grpc.unary_unary_rpc_method_handler(service.list_containers, request_deserializer=loads, response_serializer=dumps),
        "ListImages": grpc.unary_unary_rpc_method_handler(service.list_images, request_deserializer=loads, response_serializer=dumps),
        "CreateContainers": grpc.unary_unary_rpc_method_handler(service.create_containers, request_deserializer=loads, response_serializer=dumps),
        "StartContainer": grpc.unary_unary_rpc_method_handler(service.start_container, request_deserializer=loads, response_serializer=dumps),
        "StopContainer": grpc.unary_unary_rpc_method_handler(service.stop_container, request_deserializer=loads, response_serializer=dumps),
        "RestartContainer": grpc.unary_unary_rpc_method_handler(service.restart_container, request_deserializer=loads, response_serializer=dumps),
        "RemoveContainer": grpc.unary_unary_rpc_method_handler(service.remove_container, request_deserializer=loads, response_serializer=dumps),
        "InspectContainer": grpc.unary_unary_rpc_method_handler(service.inspect_container, request_deserializer=loads, response_serializer=dumps),
        "Logs": grpc.unary_unary_rpc_method_handler(service.logs, request_deserializer=loads, response_serializer=dumps),
    }
    server.add_generic_rpc_handlers(
        (grpc.method_handlers_generic_handler("orchestrator.AgentService", handlers),)
    )
    bound = server.add_insecure_port(f"0.0.0.0:{config.port}")
    if bound == 0:
        raise RuntimeError(f"Could not bind agent port {config.port}")
    return server
