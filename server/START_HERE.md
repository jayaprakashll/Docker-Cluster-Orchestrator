# Start Here - Docker Cluster Orchestrator

This build uses a **Manager + Agent** architecture and deliberately has **no container self-healing**.

```text
React Dashboard (client)
        |
      HTTP :8000
        |
     Manager
        |
     gRPC :9000
        |
     Agent :9001
        |
   Docker Engine
```

## Project Structure

```text
project/
├── client/        # React Dashboard
└── server/        # Manager, Agent, API Backend
```

## 1. Manager PC

Navigate to the server folder:

```bash
cd server
```

Create a virtual environment:

```bash
python -m venv env
```

Windows:

```powershell
env\Scripts\activate
```

Git Bash:

```bash
source env/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the Manager:

```powershell
$env:CLUSTER_TOKEN="<machine-password>"
```

```bash
uvicorn manager.app.main:app --host 0.0.0.0 --port 8000
```

The Manager API endpoint is:

```text
http://MANAGER_IP:8000
```

The Manager gRPC endpoint is:

```text
MANAGER_IP:9000
```

---

## 2. Agent PC

Clone or copy the same project to the Agent PC.

Navigate to the server folder:

```bash
cd server
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment:

Windows:

```powershell
venv\Scripts\activate
```

Git Bash:

```bash
source env/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
pip install -e .
```

Join the cluster:

```bash
orchestrator-agent join --manager MANAGER_IP:9000 --name machine-2 --token <machine-password>
```

Start the Agent:

```bash
orchestrator-agent start
```

The Agent listens on port:

```text
9001
```

---

## 3. React Dashboard

Navigate to the client folder:

```bash
cd client
```

Build and start the React application:

```bash
docker compose up --build
```

The dashboard communicates with the Manager backend running at:

```text
http://MANAGER_IP:8000
```

---

## 4. Lifecycle Behavior

### Stop

```text
UI -> Manager -> Agent -> docker stop
```

There is no reconciler and no Docker restart policy, so it stays stopped.

### Start

```text
UI -> Manager -> Agent -> docker start
```

It starts only because the user explicitly requested it.

### Remove

```text
UI -> Manager -> Agent -> docker rm
                     |
                     +-> delete DB container record
```

It is permanently deleted from Docker and the Manager does not recreate it.

### Unexpected Docker Failure

The Manager does **not** recreate the container. This is intentional in this version.

---

## 5. Machine Visibility

The dashboard only displays machines with a fresh heartbeat.

```text
Agent -> Manager -> Heartbeat
```

Machines that stop sending heartbeats are considered offline.

Old/offline machines remain in the database but are hidden from the dashboard.

---

## Ports

| Component | Port |
|------------|------|
| Manager API | 8000 |
| Manager gRPC | 9000 |
| Agent | 9001 |

---

## Startup Order

1. Start the Manager backend from the `server` folder.
2. Join and start Agents on worker machines.
3. Start the React dashboard from the `client` folder:

```bash
docker compose up --build
```

4. Open the dashboard and manage machines, containers, deployments, images, and logs through the Manager.