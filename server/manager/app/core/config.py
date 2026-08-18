from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("MANAGER_HOST", "0.0.0.0")
    http_port: int = int(os.getenv("MANAGER_HTTP_PORT", "8000"))
    grpc_port: int = int(os.getenv("MANAGER_GRPC_PORT", "9000"))
    db_url: str = os.getenv("MANAGER_DB_URL", "sqlite:///./orchestrator.db")
    cluster_token: str = os.getenv("CLUSTER_TOKEN", "dev-token-change-me")
    reconcile_interval: int = int(os.getenv("RECONCILE_INTERVAL", "10"))
    heartbeat_warning_seconds: int = int(os.getenv("HEARTBEAT_WARNING_SECONDS", "10"))
    heartbeat_offline_seconds: int = int(os.getenv("HEARTBEAT_OFFLINE_SECONDS", "15"))


settings = Settings()
