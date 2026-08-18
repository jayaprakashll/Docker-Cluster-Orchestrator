from __future__ import annotations

import shutil
import typer

from agent.app.core.config import AgentConfig, CONFIG_PATH
from agent.app.main import main as run_agent

app = typer.Typer(help="Docker cluster agent")


@app.command()
def join(
    manager: str = typer.Option(..., "--manager", help="Manager gRPC address, e.g. 192.168.1.10:9000"),
    token: str = typer.Option(..., "--token"),
    name: str = typer.Option(..., "--name"),
    port: int = typer.Option(9001, "--port"),
):
    """Join the cluster. The agent discovers its own IP and registers with the manager when started."""
    config = AgentConfig.new(name=name, manager_address=manager, token=token, port=port)
    config.save()
    typer.echo(f"Joined configuration saved to {CONFIG_PATH}")
    typer.echo(f"machine_id={config.machine_id}")
    typer.echo("Start the agent with: orchestrator-agent start")


@app.command()
def start():
    """Start the agent service."""
    run_agent()


@app.command()
def status():
    """Show local agent configuration."""
    config = AgentConfig.load()
    typer.echo(f"name: {config.name}")
    typer.echo(f"machine_id: {config.machine_id}")
    typer.echo(f"manager: {config.manager_address}")
    typer.echo(f"port: {config.port}")


@app.command()
def leave():
    """Remove local agent configuration."""
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
    typer.echo("Agent configuration removed.")


if __name__ == "__main__":
    app()
