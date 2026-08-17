import { useState } from "react";
import { api } from "../api";
import StatusBadge from "./StatusBadge";

function containerName(container) {
  return (
    container?.name ||
    container?.container_name ||
    container?.id ||
    container?.container_id ||
    "unknown"
  );
}

function healthIcon(status) {
  const value = String(
    status || ""
  ).toLowerCase();

  return {
    healthy: "🟢",
    unhealthy: "🔴",
    starting: "🟡",
  }[value] || "⚪";
}

export default function ContainerCard({
  container,
  onChanged,
}) {
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [inspect, setInspect] = useState(null);
  const [logs, setLogs] = useState("");
  const [showLogs, setShowLogs] =
    useState(false);
  const [tail, setTail] = useState(200);

  const name = containerName(container);

  const containerId =
    container?.id || name;

  const status = String(
    container?.status ||
      container?.state ||
      "unknown"
  ).toLowerCase();

  const health =
    container?.health ||
    "no-healthcheck";

  async function action(name, fn) {
    setBusy(name);
    setError("");

    try {
      await fn();

      if (onChanged) {
        await onChanged();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  }

  async function fetchLogs() {
    setBusy("logs");
    setError("");

    try {
      const data =
        await api.getContainerLogs(
          containerId,
          tail
        );

      setLogs(data?.logs || "");
      setShowLogs(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  }

  async function inspectContainer() {
    setBusy("inspect");
    setError("");

    try {
      const data =
        await api.inspectContainer(
          containerId
        );

      setInspect(
        data?.inspect || data
      );
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="container-card">
      <div className="container-top">
        <div className="container-info">
          <div className="container-name">
            {healthIcon(health)} {name}
          </div>

          <div className="machine-meta">
            {container?.machine || "—"}
            {" • "}
            {String(containerId).slice(
              0,
              12
            )}
          </div>
        </div>

        <div className="container-stat">
          <span className="metric-label">
            STATE
          </span>

          <strong>
            {status.toUpperCase()}
          </strong>
        </div>

        <div className="container-stat">
          <span className="metric-label">
            HEALTH
          </span>

          <strong>
            {String(
              health
            ).toUpperCase()}
          </strong>
        </div>

        <div className="container-stat">
          <span className="metric-label">
            RESTARTS
          </span>

          <strong>
            {container?.restart_count || 0}
          </strong>
        </div>
      </div>

      <div className="container-image">
        IMAGE:{" "}
        <span>
          {container?.image || "-"}
        </span>
      </div>

      {container?.error && (
        <div className="error-box">
          {container.error}
        </div>
      )}

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <div className="container-actions">
        <button
          disabled={
            busy ||
            status === "running"
          }
          onClick={() =>
            action("start", () =>
              api.startContainer(
                containerId
              )
            )
          }
        >
          ▶ Start
        </button>

        <button
          disabled={
            busy ||
            status !== "running"
          }
          onClick={() =>
            action("stop", () =>
              api.stopContainer(
                containerId
              )
            )
          }
        >
          ⏹ Stop
        </button>

        <button
          disabled={!!busy}
          onClick={() =>
            action("restart", () =>
              api.restartContainer(
                containerId
              )
            )
          }
        >
          🔄 Restart
        </button>

        <button
          disabled={!!busy}
          onClick={inspectContainer}
        >
          🔍 Inspect
        </button>

        <button
          className="danger-button"
          disabled={!!busy}
          onClick={() => {
            if (
              !window.confirm(
                `Permanently remove ${name}?`
              )
            ) {
              return;
            }

            action("remove", () =>
              api.removeContainer(
                containerId,
                true
              )
            );
          }}
        >
          🗑 Remove
        </button>
      </div>

      {inspect && (
        <div className="json-panel">
          <div className="panel-title">
            INSPECT RESPONSE
          </div>

          <pre>
            {JSON.stringify(
              inspect,
              null,
              2
            )}
          </pre>

          <button
            onClick={() =>
              setInspect(null)
            }
          >
            CLOSE
          </button>
        </div>
      )}

      <div className="logs-section">
        <button
          className="logs-toggle"
          onClick={() =>
            setShowLogs(!showLogs)
          }
        >
          📜 Logs
          <span>
            {showLogs ? "▲" : "▼"}
          </span>
        </button>

        {showLogs && (
          <div className="logs-panel">
            <div className="logs-controls">
              <label>
                Lines

                <input
                  type="number"
                  min="10"
                  max="10000"
                  step="50"
                  value={tail}
                  onChange={(e) =>
                    setTail(
                      Number(e.target.value)
                    )
                  }
                />
              </label>

              <button
                disabled={!!busy}
                onClick={fetchLogs}
              >
                Refresh logs
              </button>
            </div>

            <pre className="log-output">
              {logs ||
                "Press Refresh logs to fetch container output."}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}