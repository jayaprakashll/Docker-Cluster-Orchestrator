from __future__ import annotations

import logging
import signal
import time

from agent.app.core.config import AgentConfig
from agent.app.docker.container_manager import ContainerManager
from agent.app.docker.docker_client import DockerClient
from agent.app.grpc.server import build_server
from agent.app.heartbeat.heartbeat import HeartbeatWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
LOG = logging.getLogger(__name__)


def main() -> None:
    config = AgentConfig.load()
    docker_client = DockerClient()
    containers = ContainerManager(docker_client.client)
    heartbeat = HeartbeatWorker(config, docker_client, containers)
    server = build_server(config, containers, docker_client)
    server.start()
    LOG.info("agent %s listening on 0.0.0.0:%s", config.name, config.port)
    try:
        heartbeat.start()
    except Exception:
        server.stop(0)
        raise

    stop = False

    def handle_signal(signum, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while not stop:
        time.sleep(1)
    heartbeat.stop()
    server.stop(3).wait()
    LOG.info("agent stopped")


if __name__ == "__main__":
    main()
