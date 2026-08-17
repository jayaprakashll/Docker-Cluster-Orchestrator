import { useEffect, useState } from "react";
import { api } from "../api";
import Gauge from "../components/Gauge";
import EcgChart from "../components/EcgChart";
import ResourceBar from "../components/ResourceBar";
import StatusBadge from "../components/StatusBadge";

export default function Overview({
  machines,
  scores,
  loading,
}) {
  const [
    runningContainers,
    setRunningContainers,
  ] = useState(0);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const data =
          await api.getContainers(
            null,
            true
          );

        if (!mounted) return;

        const containers =
          data?.containers || [];

        setRunningContainers(
          containers.filter(
            (container) =>
              String(
                container?.status || ""
              ).toLowerCase() ===
              "running"
          ).length
        );
      } catch {
        if (mounted) {
          setRunningContainers(0);
        }
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, [machines]);

  const healthy = machines.filter(
    (m) =>
      String(m?.status).toLowerCase() ===
      "healthy"
  ).length;

  const warning = machines.filter(
    (m) =>
      String(m?.status).toLowerCase() ===
      "warning"
  ).length;

  const offline = machines.filter(
    (m) =>
      String(m?.status).toLowerCase() ===
      "offline"
  ).length;

  const scoreMap = Object.fromEntries(
    (scores?.ranking || []).map(
      (item) => [
        item.machine_id,
        item,
      ]
    )
  );

  return (
    <>
      <PageHeader
        eyebrow="CLUSTER OPERATIONS"
        title="Command center"
        subtitle="Live machine health, workload activity and scheduler intelligence."
      />

      {loading && (
        <div className="loading-bar">
          Loading cluster telemetry...
        </div>
      )}

      <div className="metric-grid">
        <Metric
          label="ACTIVE MACHINES"
          value={machines.length}
          description="live agent nodes"
        />

        <Metric
          label="HEALTHY"
          value={healthy}
          description="heartbeat nominal"
        />

        <Metric
          label="CONTAINERS"
          value={runningContainers}
          description="currently running"
        />

        <Metric
          label="WARNINGS"
          value={warning + offline}
          description="attention required"
        />
      </div>

      <SectionTitle>
        MACHINE HEALTH MATRIX
      </SectionTitle>

      {machines.length === 0 ? (
        <Empty>
          No active machines are currently
          registered.
        </Empty>
      ) : (
        <div className="machine-grid">
          {machines.map((machine) => {
            const scoreInfo =
              scoreMap[
                machine.machine_id
              ] || {};

            return (
              <div
                className="machine-card"
                key={
                  machine.machine_id ||
                  machine.name
                }
              >
                <div className="machine-card-header">
                  <div>
                    <div className="machine-title">
                      {machine.name ||
                        "Unknown"}
                    </div>

                    <div className="machine-meta">
                      {machine.ip || "—"}
                    </div>
                  </div>

                  <StatusBadge
                    status={
                      machine.status
                    }
                  />
                </div>

                <Gauge
                  score={
                    scoreInfo.score
                  }
                  title="MACHINE SUITABILITY"
                />

                <EcgChart
                  active={
                    String(
                      machine.status
                    ).toLowerCase() !==
                    "offline"
                  }
                />

                <ResourceBar
                  label="CPU LOAD"
                  value={
                    machine.cpu_percent
                  }
                />

                <ResourceBar
                  label="MEMORY"
                  value={
                    machine.memory_percent
                  }
                />

                <div className="machine-meta machine-container-count">
                  CONTAINERS:
                  <strong>
                    {machine.running_containers ||
                      0}
                  </strong>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {scores?.selected && (
        <>
          <SectionTitle>
            SCHEDULER INTELLIGENCE
          </SectionTitle>

          <div className="scheduler-intelligence">
            <div className="panel">
              <div className="metric-label">
                RECOMMENDED NODE
              </div>

              <div className="machine-title">
                {scores.selected.name ||
                  "—"}
              </div>

              <div className="score">
                {scores.selected.score ||
                  0}
              </div>

              <div className="score-caption">
                WEIGHTED SUITABILITY / 100
              </div>
            </div>

            <ScoreChart
              selected={scores.selected}
            />
          </div>
        </>
      )}
    </>
  );
}

function ScoreChart({ selected }) {
  const items = [
    ["CPU", selected.cpu_score],
    ["MEMORY", selected.memory_score],
    [
      "CONTAINERS",
      selected.container_score,
    ],
    ["HEALTH", selected.health_score],
  ];

  return (
    <div className="panel chart-panel">
      <div className="bar-chart">
        {items.map(([label, value]) => (
          <div
            className="bar-column"
            key={label}
          >
            <div className="bar-value">
              {Number(value || 0).toFixed(0)}
            </div>

            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  height: `${Math.min(
                    100,
                    Math.max(
                      0,
                      Number(value) || 0
                    )
                  )}%`,
                }}
              />
            </div>

            <div className="bar-label">
              {label}
            </div>
          </div>
        ))}
      </div>
    </div>
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

export function SectionTitle({
  children,
}) {
  return (
    <div className="section-wrapper">
      <div className="section-title">
        {children}
      </div>

      <div className="section-line" />
    </div>
  );
}

export function Metric({
  label,
  value,
  description,
}) {
  return (
    <div className="metric-card">
      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
      </div>

      <div className="metric-description">
        {description}
      </div>
    </div>
  );
}

export function Empty({ children }) {
  return (
    <div className="empty-state">
      {children}
    </div>
  );
}