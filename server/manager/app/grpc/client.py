from __future__ import annotations

import grpc

from common.rpc import dumps, loads


class AgentClient:
    def __init__(self, address: str, token: str, timeout: float = 8.0):
        self.address = address
        self.token = token
        self.timeout = timeout
        self.channel = grpc.insecure_channel(address)

    def close(self) -> None:
        self.channel.close()

    def _call(self, method: str, payload: dict, timeout: float | None = None) -> dict:
        rpc = self.channel.unary_unary(
            f"/orchestrator.AgentService/{method}",
            request_serializer=dumps,
            response_deserializer=loads,
        )
        request = dict(payload)
        request["token"] = self.token
        return rpc(request, timeout=timeout or self.timeout)

    def ping(self) -> dict:
        return self._call("Ping", {})

    def list_containers(self, all_containers: bool = True) -> dict:
        return self._call("ListContainers", {"all": all_containers})

    def list_images(self) -> dict:
        return self._call("ListImages", {})

    def create_containers(self, **kwargs) -> dict:
        return self._call("CreateContainers", kwargs, timeout=60)

    def start_container(self, container_id: str) -> dict:
        return self._call("StartContainer", {"container_id": container_id})

    def stop_container(self, container_id: str) -> dict:
        return self._call("StopContainer", {"container_id": container_id})

    def restart_container(self, container_id: str) -> dict:
        return self._call("RestartContainer", {"container_id": container_id})

    def remove_container(self, container_id: str, force: bool = False) -> dict:
        return self._call("RemoveContainer", {"container_id": container_id, "force": force})

    def inspect_container(self, container_id: str) -> dict:
        return self._call("InspectContainer", {"container_id": container_id})

    def logs(self, container_id: str, tail: int = 200) -> dict:
        return self._call("Logs", {"container_id": container_id, "tail": tail})
