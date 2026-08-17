import MachineCard from "../components/MachineCard";

export default function Machines({
  machines,
  scores,
}) {
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
        eyebrow="LIVE AGENT TELEMETRY"
        title="Machine health"
        subtitle="Heartbeat, scheduler score and resource utilisation."
      />

      {machines.length === 0 ? (
        <div className="empty-state">
          No active machines are currently
          registered.
        </div>
      ) : (
        <div className="vertical-stack">
          {machines.map((machine) => (
            <MachineCard
              key={
                machine.machine_id ||
                machine.name
              }
              machine={machine}
              scoreInfo={
                scoreMap[
                  machine.machine_id
                ] || {}
              }
              detailed
            />
          ))}
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