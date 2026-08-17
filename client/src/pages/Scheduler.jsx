import { SectionTitle } from "./Overview";

export default function Scheduler({
  scores,
}) {
  const selected = scores?.selected;
  const ranking = scores?.ranking || [];

  return (
    <>
      <PageHeader
        eyebrow="WEIGHTED RESOURCE ENGINE"
        title="Scheduler intelligence"
        subtitle="Live ranking of healthy machines for workload placement."
      />

      {selected && (
        <div className="scheduler-intelligence">
          <div className="panel">
            <div className="metric-label">
              BEST AVAILABLE NODE
            </div>

            <div className="machine-title">
              {selected.name || "—"}
            </div>

            <div className="score">
              {selected.score || 0}
            </div>

            <div className="score-caption">
              SCORE / 100
            </div>
          </div>

          <div className="panel">
            <ScoreBars selected={selected} />
          </div>
        </div>
      )}

      {ranking.length > 0 && (
        <>
          <SectionTitle>
            MACHINE RANKING
          </SectionTitle>

          <DataTable
            columns={[
              "name",
              "status",
              "score",
              "cpu_score",
              "memory_score",
              "container_score",
              "health_score",
              "running_containers",
            ]}
            rows={ranking}
          />
        </>
      )}
    </>
  );
}

function ScoreBars({ selected }) {
  const values = [
    [
      "CPU availability",
      selected.cpu_score,
    ],
    [
      "Memory availability",
      selected.memory_score,
    ],
    [
      "Container capacity",
      selected.container_score,
    ],
    ["Health", selected.health_score],
  ];

  return (
    <div className="horizontal-bars">
      {values.map(([label, value]) => (
        <div
          className="horizontal-bar"
          key={label}
        >
          <div className="horizontal-bar-header">
            <span>{label}</span>

            <strong>
              {Number(value || 0).toFixed(1)}
            </strong>
          </div>

          <div className="resource-track">
            <div
              className="resource-fill"
              style={{
                width: `${Math.min(
                  100,
                  Math.max(
                    0,
                    Number(value) || 0
                  )
                )}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function DataTable({
  columns,
  rows,
}) {
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>
                {column.replaceAll(
                  "_",
                  " "
                )}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {columns.map((column) => (
                <td key={column}>
                  {String(
                    row[column] ??
                      "—"
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
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