from __future__ import annotations

from typing import Any

from docker.errors import NotFound


class ContainerManager:
    """Direct Docker lifecycle operations.

    There is intentionally no self-healing or desired-state logic here.
    A container is changed only when the Manager explicitly asks the Agent
    to create, start, stop, restart, or remove it.
    """

    def __init__(self, docker_client):
        self.client = docker_client

    @staticmethod
    def _normalize_env(env: list[str] | None) -> list[str]:
        return env or []

    @staticmethod
    def _normalize_volumes(
        volumes: list[str] | None,
    ) -> dict[str, dict[str, str]]:
        result: dict[str, dict[str, str]] = {}
        for volume in volumes or []:
            parts = volume.split(":")
            if len(parts) == 2:
                source, target = parts
                result[source] = {"bind": target, "mode": "rw"}
            elif len(parts) == 3:
                source, target, mode = parts
                result[source] = {"bind": target, "mode": mode}
            else:
                raise ValueError(
                    f"Invalid volume '{volume}'. Use source:target[:ro]"
                )
        return result

    @staticmethod
    def _normalize_ports(
        ports: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for container_port, host_port in (ports or {}).items():
            if isinstance(host_port, str) and ":" in host_port:
                host_ip, host = host_port.rsplit(":", 1)
                result[container_port] = (host_ip, int(host))
            else:
                result[container_port] = int(host_port)
        return result

    def create_containers(
        self,
        image: str,
        replicas: int,
        name_prefix: str,
        env: list[str] | None = None,
        ports: dict[str, Any] | None = None,
        volumes: list[str] | None = None,
        network: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> list[dict]:
        """Create and start exactly ``replicas`` new containers.

        Existing containers are NEVER started automatically. If a requested
        name already exists, the operation fails instead of changing it.
        """
        if replicas < 1:
            raise ValueError("replicas must be >= 1")
        if not image.strip():
            raise ValueError("image is required")
        if not name_prefix.strip():
            raise ValueError("name_prefix is required")

        self.client.images.pull(image)

        normalized_env = self._normalize_env(env)
        normalized_ports = self._normalize_ports(ports)
        normalized_volumes = self._normalize_volumes(volumes)

        created: list[dict] = []

        for index in range(1, replicas + 1):
            name = f"{name_prefix}-{index}"

            try:
                self.client.containers.get(name)
            except NotFound:
                pass
            else:
                raise ValueError(
                    f"Container '{name}' already exists. "
                    "Choose a different deployment/name prefix."
                )

            container = self.client.containers.create(
                image=image,
                name=name,
                environment=normalized_env,
                ports=normalized_ports,
                volumes=normalized_volumes,
                network=network,
                labels=labels or {},
                detach=True,
                restart_policy={"Name": "no"},
            )

            try:
                container.start()
                container.reload()
                created.append(self.serialize(container))
            except Exception:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
                raise

        return created

    def list_containers(self, all_containers: bool = True) -> list[dict]:
        return [
            self.serialize(c)
            for c in self.client.containers.list(all=all_containers)
        ]

    def list_images(self) -> list[dict]:
        images = []
        for image in self.client.images.list():
            attrs = image.attrs or {}
            tags = list(image.tags or [])
            repository = (
                tags[0].rsplit(":", 1)[0] if tags else "<none>"
            )
            images.append(
                {
                    "id": image.id,
                    "short_id": getattr(image, "short_id", image.id[:19]),
                    "tags": tags,
                    "repository": repository,
                    "size": attrs.get("Size", 0),
                    "created": attrs.get("Created"),
                }
            )
        return images

    def get(self, container_id: str):
        try:
            return self.client.containers.get(container_id)
        except NotFound as exc:
            raise ValueError(
                f"Container '{container_id}' not found"
            ) from exc

    def start(self, container_id: str) -> dict:
        container = self.get(container_id)
        container.start()
        container.reload()
        return self.serialize(container)

    def stop(self, container_id: str) -> dict:
        container = self.get(container_id)
        container.stop()
        container.reload()
        return self.serialize(container)

    def restart(self, container_id: str) -> dict:
        container = self.get(container_id)
        container.restart()
        container.reload()
        return self.serialize(container)

    def remove(self, container_id: str, force: bool = False) -> dict:
        container = self.get(container_id)
        info = self.serialize(container)
        container.remove(force=force)
        return info

    def inspect(self, container_id: str) -> dict:
        return self.get(container_id).attrs

    def logs(self, container_id: str, tail: int = 200) -> str:
        tail = max(1, min(int(tail), 10000))
        return self.get(container_id).logs(tail=tail).decode(
            "utf-8",
            errors="replace",
        )

    @staticmethod
    def serialize(container) -> dict:
        container.reload()
        attrs = container.attrs or {}
        state = attrs.get("State") or {}
        health_block = state.get("Health") or {}

        image = None
        try:
            image = (container.image.tags or [None])[0]
        except Exception:
            pass

        return {
            "id": container.id,
            "short_id": container.short_id,
            "name": container.name,
            "image": image or getattr(container.image, "id", "unknown"),
            "status": state.get("Status", container.status),
            "state": state.get("Status", container.status),
            "health": health_block.get("Status", "no-healthcheck"),
            "health_log": health_block.get("Log", [])[-5:],
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
            "exit_code": state.get("ExitCode"),
            "restart_count": attrs.get("RestartCount", 0),
            "labels": dict(container.labels or {}),
            "ports": container.ports or {},
        }
