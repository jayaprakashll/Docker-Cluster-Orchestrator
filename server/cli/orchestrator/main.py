from __future__ import annotations

import json
import os
from typing import Optional

import httpx
import typer

app = typer.Typer(help="CLI for the Simple Docker Cluster Orchestrator")

MANAGER_HTTP = os.getenv("ORCHESTRATOR_MANAGER", "http://127.0.0.1:8000")


def request(method: str, path: str, **kwargs):
    url = MANAGER_HTTP.rstrip("/") + path
    try:
        response = httpx.request(method, url, timeout=30, **kwargs)
    except httpx.HTTPError as exc:
        raise typer.BadParameter(f"Cannot reach manager at {MANAGER_HTTP}: {exc}")
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise typer.BadParameter(str(detail))
    return response.json()


@app.command()
def machines():
    """List registered Docker machines."""
    data = request("GET", "/api/machines")
    typer.echo(json.dumps(data["machines"], indent=2))




@app.command(name="health")
def health():
    """Show manager and machine health."""
    data = request("GET", "/api/health/machines")
    typer.echo(json.dumps(data, indent=2))


@app.command(name="images")
def images(machine: Optional[str] = typer.Option(None, "--machine", "-m")):
    """List Docker images from agents."""
    params = {"machine": machine} if machine else {}
    data = request("GET", "/api/images", params=params)
    typer.echo(json.dumps(data["images"], indent=2))


@app.command()
def run(
    image: str = typer.Option(..., "--image", "-i"),
    replicas: int = typer.Option(1, "--replicas", "-r"),
    machine: str = typer.Option(..., "--machine", "-m", help="Machine name, machine ID, or all"),
    name_prefix: Optional[str] = typer.Option(None, "--name-prefix"),
    env: list[str] = typer.Option([], "--env", help="KEY=value; repeat option"),
    publish: list[str] = typer.Option([], "--publish", "-p", help="host:container or host_ip:host:container"),
    volume: list[str] = typer.Option([], "--volume", "-v", help="source:target[:ro]"),
    network: Optional[str] = typer.Option(None, "--network"),
):
    """Deploy containers to one machine, or use --machine all for every active machine."""
    ports = {}
    for item in publish:
        parts = item.split(":")
        if len(parts) == 2:
            host, container = parts
            ports[f"{container}/tcp"] = int(host)
        elif len(parts) == 3:
            host_ip, host, container = parts
            ports[f"{container}/tcp"] = f"{host_ip}:{host}"
        else:
            raise typer.BadParameter(f"Invalid --publish '{item}'")

    data = request("POST", "/api/deployments", json={
        "machine": machine,
        "replicas": replicas,
        "image": image,
        "name_prefix": name_prefix,
        "env": env,
        "ports": ports,
        "volumes": volume,
        "network": network,
    })
    typer.echo(json.dumps(data, indent=2))


@app.command(name="ps")
def ps(machine: Optional[str] = typer.Option(None, "--machine", "-m")):
    """List containers, optionally on one machine."""
    params = {"machine": machine} if machine else {}
    data = request("GET", "/api/containers", params=params)
    typer.echo(json.dumps(data["containers"], indent=2))


@app.command()
def start(container: str):
    typer.echo(json.dumps(request("POST", f"/api/containers/{container}/start"), indent=2))


@app.command()
def stop(container: str):
    typer.echo(json.dumps(request("POST", f"/api/containers/{container}/stop"), indent=2))


@app.command()
def restart(container: str):
    typer.echo(json.dumps(request("POST", f"/api/containers/{container}/restart"), indent=2))


@app.command()
def rm(container: str, force: bool = typer.Option(False, "--force", "-f")):
    typer.echo(json.dumps(request("DELETE", f"/api/containers/{container}", params={"force": force}), indent=2))


@app.command()
def inspect(container: str):
    typer.echo(json.dumps(request("GET", f"/api/containers/{container}/inspect"), indent=2))


@app.command()
def logs(container: str, tail: int = typer.Option(200, "--tail")):
    data = request("GET", f"/api/containers/{container}/logs", params={"tail": tail})
    typer.echo(data.get("logs", ""), nl=False)


if __name__ == "__main__":
    app()
