from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import os
import uuid
import yaml


CONFIG_PATH = Path(os.getenv("AGENT_CONFIG", "agent.yaml"))


@dataclass
class AgentConfig:
    machine_id: str
    name: str
    manager_address: str
    token: str
    port: int = 9001

    def save(self, path: Path = CONFIG_PATH) -> None:
        path.write_text(yaml.safe_dump(asdict(self), sort_keys=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "AgentConfig":
        if not path.exists():
            raise FileNotFoundError(f"Agent is not joined. Run 'orchestrator-agent join ...' first. Missing {path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(**data)

    @classmethod
    def new(cls, name: str, manager_address: str, token: str, port: int = 9001) -> "AgentConfig":
        return cls(machine_id=str(uuid.uuid4()), name=name, manager_address=manager_address, token=token, port=port)
