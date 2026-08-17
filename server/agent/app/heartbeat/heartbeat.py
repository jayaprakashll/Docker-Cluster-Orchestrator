from __future__ import annotations

import logging
import threading

import grpc

from common.rpc import dumps, loads
from agent.app.core.config import AgentConfig
from agent.app.docker.container_manager import ContainerManager
from agent.app.docker.docker_client import DockerClient
from agent.app.system.system_info import collect_system_info

LOG = logging.getLogger(__name__)


class HeartbeatWorker:
    def __init__(
        self,
        config: AgentConfig,
        docker_client: DockerClient,
        containers: ContainerManager,
        interval: int = 5,
    ):
        self.config = config
        self.docker_client = docker_client
        self.containers = containers
        self.interval = max(2, interval)
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None

    def _manager_call(self, method: str, payload: dict):
        channel = grpc.insecure_channel(self.config.manager_address)
        try:
            rpc = channel.unary_unary(
                f"/orchestrator.ManagerService/{method}",
                request_serializer=dumps,
                response_deserializer=loads,
            )
            request = dict(payload)
            request["token"] = self.config.token
            return rpc(request, timeout=5)
        finally:
            channel.close()

    def register(self) -> None:
        info = collect_system_info(self.config.manager_address)
        payload = {
            "machine_id": self.config.machine_id,
            "name": self.config.name,
            "hostname": info["hostname"],
            "ip": info["ip"],
            "agent_port": self.config.port,
            "cpu_count": info["cpu_count"],
            "memory_mb": info["memory_mb"],
            "docker_version": self.docker_client.version(),
        }
        response = self._manager_call("Register", payload)
        if not response.get("ok"):
            raise RuntimeError(f"Registration failed: {response}")

        canonical_id = response.get("machine_id")
        if canonical_id and canonical_id != self.config.machine_id:
            LOG.warning(
                "Manager canonicalized machine_id from %s to %s",
                self.config.machine_id,
                canonical_id,
            )
            self.config.machine_id = str(canonical_id)
            self.config.save()

        LOG.info(
            "registered with manager %s as %s (%s)",
            self.config.manager_address,
            self.config.name,
            info["ip"],
        )

    def send_once(self) -> None:
        info = collect_system_info(self.config.manager_address)
        running = len(self.containers.list_containers(all_containers=False))
        self._manager_call(
            "Heartbeat",
            {
                "machine_id": self.config.machine_id,
                "name": self.config.name,
                "hostname": info["hostname"],
                "ip": info["ip"],
                "agent_port": self.config.port,
                "cpu_count": info["cpu_count"],
                "memory_mb": info["memory_mb"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": info["memory_percent"],
                "running_containers": running,
                "health": "healthy",
                "docker_version": self.docker_client.version(),
            },
        )

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.send_once()
            except Exception:
                LOG.exception("heartbeat failed")
            self.stop_event.wait(self.interval)

    def start(self):
        self.register()
        self.thread = threading.Thread(
            target=self._run,
            name="heartbeat",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)
