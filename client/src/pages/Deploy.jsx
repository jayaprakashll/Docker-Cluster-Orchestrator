import { useState } from "react";
import { api } from "../api";

export default function Deploy({
  machines,
}) {
  const [image, setImage] =
    useState("nginx:latest");

  const [prefix, setPrefix] =
    useState("web");

  const [replicas, setReplicas] =
    useState(1);

  const [mode, setMode] = useState(
    "Automatic — weighted scheduler"
  );

  const [selectedMachines, setSelectedMachines] =
    useState([]);

  const [loading, setLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [result, setResult] =
    useState(null);

  const machineNames = machines
    .map((machine) => machine.name)
    .filter(Boolean);

  function toggleMachine(name) {
    setSelectedMachines((current) =>
      current.includes(name)
        ? current.filter(
            (item) => item !== name
          )
        : [...current, name]
    );
  }

  async function deploy() {
    setMessage("");
    setError("");
    setResult(null);

    if (!image.trim()) {
      setError(
        "Docker image is required."
      );
      return;
    }

    if (
      mode === "Select machines" &&
      selectedMachines.length === 0
    ) {
      setError(
        "Select at least one machine."
      );
      return;
    }

    let target = null;

    if (mode === "All active machines") {
      target = "all";
    } else if (
      mode === "Select machines"
    ) {
      target = selectedMachines;
    }

    const payload = {
      machine: target,
      replicas: Number(replicas),
      image: image.trim(),
      name_prefix:
        prefix.trim() || null,
      env: [],
      ports: {},
      volumes: [],
      network: null,
    };

    try {
      setLoading(true);

      const response =
        await api.runContainer(
          payload
        );

      setResult(response);

      if (
        response?.mode ===
        "all-machines"
      ) {
        setMessage(
          `Deployment completed for all active machines. Success: ${
            response.successful_machines ||
            0
          }, Failed: ${
            response.failed_machines ||
            0
          }.`
        );
      } else if (
        response?.mode ===
        "selected-machines"
      ) {
        setMessage(
          `Deployment completed for ${
            response.successful_machines ||
            0
          } selected machine(s).`
        );
      } else {
        setMessage(
          "Deployment submitted successfully."
        );
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="WORKLOAD PROVISIONING"
        title="Deploy workload"
        subtitle="Choose automatic scheduling, every active machine, or a custom machine set."
      />

      <div className="panel deploy-panel">
        <label className="form-field">
          <span>Docker image</span>

          <input
            value={image}
            onChange={(e) =>
              setImage(e.target.value)
            }
            placeholder="nginx:latest"
          />
        </label>

        <label className="form-field">
          <span>Instance prefix</span>

          <input
            value={prefix}
            onChange={(e) =>
              setPrefix(e.target.value)
            }
            placeholder="web"
          />
        </label>

        <label className="form-field">
          <span>
            Instances / replicas per target
            machine
          </span>

          <input
            type="number"
            min="1"
            max="100"
            value={replicas}
            onChange={(e) =>
              setReplicas(
                Math.max(
                  1,
                  Math.min(
                    100,
                    Number(e.target.value)
                  )
                )
              )
            }
          />

          <small>
            For multiple/all machines, this
            many replicas are created on each
            target machine.
          </small>
        </label>

        <div className="form-field">
          <span>Placement mode</span>

          <div className="radio-group">
            {[
              "Automatic — weighted scheduler",
              "All active machines",
              "Select machines",
            ].map((item) => (
              <label
                className={
                  mode === item
                    ? "radio-option selected"
                    : "radio-option"
                }
                key={item}
              >
                <input
                  type="radio"
                  name="placement"
                  checked={mode === item}
                  onChange={() =>
                    setMode(item)
                  }
                />

                {item}
              </label>
            ))}
          </div>
        </div>

        {mode === "Select machines" && (
          <div className="machine-selection">
            <div className="metric-label">
              MACHINES
            </div>

            {machineNames.length === 0 ? (
              <div className="empty-state">
                No active machines available.
              </div>
            ) : (
              machineNames.map((name) => (
                <label
                  className="machine-checkbox"
                  key={name}
                >
                  <input
                    type="checkbox"
                    checked={selectedMachines.includes(
                      name
                    )}
                    onChange={() =>
                      toggleMachine(name)
                    }
                  />

                  {name}
                </label>
              ))
            )}

            {selectedMachines.length >
              0 && (
              <div className="info-box">
                {selectedMachines.length}{" "}
                machine(s) selected.{" "}
                {replicas} replica(s) will be
                created on each selected
                machine.
              </div>
            )}
          </div>
        )}

        {mode === "All active machines" && (
          <div className="success-box">
            The deployment will be sent to all{" "}
            {machineNames.length} active
            machine(s). {replicas} replica(s)
            per machine.
          </div>
        )}

        {mode ===
          "Automatic — weighted scheduler" && (
          <div className="hint">
            Weighted scheduler: CPU 40% •
            Memory 35% • Container capacity 15%
            • Health 10%
          </div>
        )}

        {error && (
          <div className="error-box">
            {error}
          </div>
        )}

        {message && (
          <div className="success-box">
            {message}
          </div>
        )}

        <button
          className="primary-button deploy-button"
          disabled={loading}
          onClick={deploy}
        >
          {loading
            ? "DEPLOYING..."
            : "DEPLOY WORKLOAD"}
        </button>
      </div>

      {result?.results?.length > 0 && (
        <div className="panel">
          <div className="panel-title">
            DEPLOYMENT RESULTS
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Machine</th>
                  <th>Status</th>
                  <th>Deployment ID</th>
                  <th>Containers</th>
                  <th>Error</th>
                </tr>
              </thead>

              <tbody>
                {result.results.map(
                  (item, index) => (
                    <tr key={index}>
                      <td>
                        {item.machine ||
                          "—"}
                      </td>

                      <td>
                        {item.ok
                          ? "SUCCESS"
                          : "FAILED"}
                      </td>

                      <td>
                        {item.deployment_id ||
                          "—"}
                      </td>

                      <td>
                        {item.containers
                          ?.length || 0}
                      </td>

                      <td>
                        {item.error || ""}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
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