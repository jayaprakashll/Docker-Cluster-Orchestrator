from __future__ import annotations

import docker
from docker.errors import DockerException


class DockerClient:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except DockerException as exc:
            raise RuntimeError(f"Cannot connect to Docker Engine: {exc}") from exc

    def version(self) -> str:
        return str(self.client.version().get("Version", "unknown"))
