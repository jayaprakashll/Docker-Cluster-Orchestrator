import { useEffect, useState } from "react";
import { api } from "../api";

export default function Logs() {
  const [containers, setContainers] =
    useState([]);

  const [selected, setSelected] =
    useState("");

  const [tail, setTail] =
    useState(200);

  const [logs, setLogs] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function load() {
      try {
        const data =
          await api.getContainers(
            null,
            true
          );

        const items =
          data?.containers || [];

        setContainers(items);

        if (items.length > 0) {
          setSelected(
            items[0].name || ""
          );
        }
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, []);

  async function fetchLogs() {
    if (!selected) return;

    setLoading(true);
    setError("");

    try {
      const data =
        await api.getContainerLogs(
          selected,
          tail
        );

      setLogs(data?.logs || "");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="CONTAINER OBSERVABILITY"
        title="Runtime logs"
        subtitle="Inspect recent output from workloads."
      />

      <div className="panel logs-page">
        {containers.length === 0 ? (
          <div className="empty-state">
            No containers available.
          </div>
        ) : (
          <>
            <label className="form-field">
              <span>Container</span>

              <select
                value={selected}
                onChange={(e) =>
                  setSelected(
                    e.target.value
                  )
                }
              >
                {containers
                  .filter((x) => x.name)
                  .map((container) => (
                    <option
                      key={container.name}
                      value={container.name}
                    >
                      {container.name}
                    </option>
                  ))}
              </select>
            </label>

            <label className="form-field">
              <span>
                Lines: {tail}
              </span>

              <input
                type="range"
                min="20"
                max="2000"
                value={tail}
                onChange={(e) =>
                  setTail(
                    Number(e.target.value)
                  )
                }
              />
            </label>

            <button
              className="primary-button"
              disabled={loading}
              onClick={fetchLogs}
            >
              {loading
                ? "FETCHING..."
                : "FETCH LOGS"}
            </button>

            {error && (
              <div className="error-box">
                {error}
              </div>
            )}

            {logs && (
              <pre className="log-output large">
                {logs}
              </pre>
            )}
          </>
        )}
      </div>
    </>
  );
}

function PageHeader({
  eyebrow,
  title,
  subtitle,
}) {
  return (
    <header className="page-header">
      <div className="eyebrow">
        {eyebrow}
      </div>

      <h1>{title}</h1>

      <p>{subtitle}</p>
    </header>
  );
}