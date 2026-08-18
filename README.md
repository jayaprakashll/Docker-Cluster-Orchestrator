# Docker Cluster Orchestrator — Python Manager + Agents + Streamlit UI

A small Docker cluster orchestrator that uses **FastAPI + gRPC + SQLite + Docker SDK + Streamlit**. It does not use SSH and agents discover their own IP address.

## Architecture

```text

                     
                     ┌─────────────────────────────────────────────┐
                     │           ORCHESTRATOR MANAGER              │
                     │                                             │
                     │  FastAPI • Machine Registry • Database      │
                     │  Deployment Controller • Health Monitor     │
                     └──────────────────┬──────────────────────────┘
                                       │
                                       ▼
                           WEIGHTED RESOURCE SCHEDULER
                                       │
                           ┌──────────┼──────────┐
                           │          │          │
                           ▼          ▼          ▼
                        Machine-1  Machine-2  Machine-N
                           Score 82    Score 91    Score 65
                           │          │          │
                           │          ▼          │
                           │    BEST MACHINE     │
                           │       SELECTED      │
                           │          │          │
                           ▼          ▼          ▼
                        Agent       Agent       Agent
                           :9001       :9001       :9001
                           │          │          │
                           ▼          ▼          ▼
                        Docker      Docker      Docker
                           │          │          │
                           ▼          ▼          ▼
                        Containers  Containers  Containers
```

### Networking

- Manager TCP `9000`: Agent -> Manager registration/heartbeat.
- Manager TCP `8000`: Dashboard/CLI -> Manager REST API.
- Agent TCP `9001`: Manager -> Agent Docker commands.
- Only the Manager stores the SQLite database.
- Agents do not need a local database.
- Agents discover their own LAN IP; do not pass `--ip`.

## Installation

### Manager PC

```bash
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Git Bash: source .venv/Scripts/activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

Set the same cluster token on every agent:

```powershell
$env:CLUSTER_TOKEN="my-secret-token"
```

Start:

```bash
uvicorn manager.app.main:app --host 0.0.0.0 --port 8000
```

Manager:

- REST API: `http://MANAGER-IP:8000`
- Swagger: `http://MANAGER-IP:8000/docs`
- gRPC: `MANAGER-IP:9000`
- SQLite: `./orchestrator.db`

### Agent PC

Verify Docker first:

```bash
docker ps
```

Install the same project dependencies and package:

```bash
pip install -r requirements.txt
pip install -e .
```

Join the cluster once:

```bash
orchestrator-agent join --manager 10.200.5.45:9000 --name machine-2 --token my-secret-token
```

Start:

```bash
orchestrator-agent start
```

The agent will discover its own IP, register, listen on `9001`, and send a heartbeat every 5 seconds.

### Second Agent PC

Use a unique name:

```bash
orchestrator-agent join --manager 10.200.5.45:9000 --name machine-3 --token my-secret-token
orchestrator-agent start
```

If the same PC is re-joined, the Manager preserves the existing machine identity and the Agent updates its local `agent.yaml` with the canonical machine ID.

## Streamlit Dashboard

Install dashboard dependencies on the Manager/UI PC:

```bash
pip install -r dashboard/requirements.txt
```

If Streamlit is running on the Manager PC:

```bash
streamlit run dashboard/app.py
```

If Streamlit is on another PC:

PowerShell:

```powershell
$env:ORCHESTRATOR_MANAGER_URL="http://10.200.5.45:8000"
streamlit run dashboard/app.py
```

The dashboard includes:

- cluster overview
- machine health and heartbeat ag
- CPU/RAM utilization
- agent connectivity test
- live container state and Docker healthcheck state
- start/stop/restart/remove/inspect
- container logs
- deployment form
- Docker image inventory
- deployment/desired-state view
- SQLite database statistics
- automatic refresh

## CLI

```bash
orchestrator machines
orchestrator health
orchestrator images
orchestrator ps --machine machine-2
orchestrator run --machine machine-2 --replicas 1 --image nginx:latest
orchestrator start CONTAINER
orchestrator stop CONTAINER
orchestrator restart CONTAINER
orchestrator rm CONTAINER --force
orchestrator inspect CONTAINER
orchestrator logs CONTAINER --tail 200
```

Set the remote Manager URL:

```powershell
$env:ORCHESTRATOR_MANAGER="http://10.200.5.45:8000"
```

## REST API

All API endpoints are under `/api`:

```text
GET  /api/health
GET  /api/health/machines
GET  /api/stats
GET  /api/database
GET  /api/machines
GET  /api/deployments
GET  /api/containers?machine=machine-2
GET  /api/images?machine=machine-2
POST /api/deployments
POST /api/machines/{machine}/ping
POST /api/containers/{ref}/start
POST /api/containers/{ref}/stop
POST /api/containers/{ref}/restart
DELETE /api/containers/{ref}
GET  /api/containers/{ref}/inspect
GET  /api/containers/{ref}/logs
```

## Health model

Machine status is based on heartbeat age:

```text
0-10 seconds   -> healthy
10-15 seconds  -> warning
>15 seconds    -> offline
```

These thresholds can be changed with:

```text
HEARTBEAT_WARNING_SECONDS
HEARTBEAT_OFFLINE_SECONDS
```

Container health comes from Docker's `State.Health.Status` when the image has a Docker `HEALTHCHECK`; otherwise the UI displays `no-healthcheck`.

## Database

Only the Manager uses SQLite. Agents do not install or maintain a database.

The Manager creates `orchestrator.db` automatically on startup. Do not copy the database file between machines while the Manager is running.

## Security

This project intentionally keeps the MVP transport simple: shared token + insecure gRPC. Keep ports 8000/9000/9001 on a trusted LAN/VPN. Do not expose them directly to the public Internet. A production implementation should use TLS/mTLS and stronger credential rotation.


## Deploy to every active machine

Use broadcast deployment when the same image should run on every currently active agent:

```bash
orchestrator run --machine all --image nginx:latest --replicas 1
```

`--replicas` is applied **per machine**. For example, with 3 active machines and `--replicas 2`, the manager creates 6 containers in total. Offline or stale machines are skipped. The response reports success or failure for each machine.
