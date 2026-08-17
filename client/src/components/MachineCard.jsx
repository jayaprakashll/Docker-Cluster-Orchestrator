import Gauge from "./Gauge";
import EcgChart from "./EcgChart";
import ResourceBar from "./ResourceBar";
import StatusBadge from "./StatusBadge";

function formatAge(seconds) {
  if (
    seconds === null ||
    seconds === undefined
  ) {
    return "Never";
  }

  const value = Math.max(
    0,
    Number(seconds) || 0
  );

  if (value < 60) {
    return `${value.toFixed(1)}s ago`;
  }

  if (value < 3600) {
    return `${(value / 60).toFixed(1)}m ago`;
  }

  return `${(value / 3600).toFixed(1)}h ago`;
}

export default function MachineCard({
  machine,
  scoreInfo = {},
  detailed = false,
}) {
  const status = String(
    machine?.status || "unknown"
  ).toLowerCase();

  const name =
    machine?.name ||
    machine?.machine_id ||
    "unknown";

  const score =
    Number(scoreInfo?.score) || 0;

  if (!detailed) {
    return (
      <div className="machine-card">
        <div className="machine-card-header">
          <div>
            <div className="machine-title">
              {name}
            </div>

            <div className="machine-meta">
              {machine?.ip || "—"}
            </div>
          </div>

          <StatusBadge status={status} />
        </div>

        <Gauge
          score={score}
          title="MACHINE SUITABILITY"
        />

        <EcgChart
          active={status !== "offline"}
        />

        <ResourceBar
          label="CPU LOAD"
          value={machine?.cpu_percent}
        />

        <ResourceBar
          label="MEMORY"
          value={machine?.memory_percent}
        />

        <div className="machine-meta machine-container-count">
          CONTAINERS:
          <strong>
            {machine?.running_containers || 0}
          </strong>
        </div>
      </div>
    );
  }

  return (
    <div className="machine-card machine-detail">
      <div className="machine-detail-header">
        <div>
          <div className="machine-title large">
            {name}
          </div>

          <div className="machine-meta">
            HOST: {machine?.hostname || "—"}
            {" • "}
            IP: {machine?.ip || "—"}
          </div>
        </div>

        <StatusBadge status={status} />
      </div>

      <div className="machine-detail-grid">
        <Gauge
          score={score}
          title="MACHINE SCORE"
        />

        <div>
          <ResourceBar
            label="CPU"
            value={machine?.cpu_percent}
          />

          <ResourceBar
            label="MEMORY"
            value={machine?.memory_percent}
          />

          <div className="machine-meta detail-spacing">
            RUNNING CONTAINERS:
            <strong>
              {machine?.running_containers || 0}
            </strong>
          </div>
        </div>

        <div>
          <EcgChart
            active={status !== "offline"}
          />

          <div className="machine-meta detail-spacing">
            LAST HEARTBEAT
            <br />

            <span className="light-text">
              {machine?.last_heartbeat || "—"}
            </span>
          </div>

          <div className="machine-meta detail-spacing">
            HEARTBEAT AGE
            <br />

            <span className="light-text">
              {formatAge(
                machine?.heartbeat_age_seconds
              )}
            </span>
          </div>
        </div>
      </div>

      <div className="machine-information-grid">
        <Info
          label="MACHINE ID"
          value={machine?.machine_id}
        />

        <Info
          label="HOSTNAME"
          value={machine?.hostname}
        />

        <Info
          label="ADDRESS"
          value={machine?.ip}
        />

        <Info
          label="AGENT PORT"
          value={machine?.port}
        />

        <Info
          label="CPU CORES"
          value={machine?.cpu_count}
        />

        <Info
          label="RAM"
          value={
            machine?.memory_mb
              ? `${(
                  Number(machine.memory_mb) /
                  1024
                ).toFixed(1)} GB`
              : "0 GB"
          }
        />

        <Info
          label="DOCKER"
          value={machine?.docker_version}
        />

        <Info
          label="REGISTERED"
          value={machine?.registered_at}
        />
      </div>
    </div>
  );
}

function Info({ label, value }) {
  return (
    <div className="info-item">
      <div className="metric-label">
        {label}
      </div>

      <div className="info-value">
        {value ?? "—"}
      </div>
    </div>
  );
}

export { formatAge };