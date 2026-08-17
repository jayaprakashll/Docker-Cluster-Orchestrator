export default function ResourceBar({
  label,
  value = 0,
}) {
  const percentage = Math.max(
    0,
    Math.min(100, Number(value) || 0)
  );

  let color = "#39d8ff";

  if (percentage >= 85) {
    color = "#ff6175";
  } else if (percentage >= 65) {
    color = "#ffc857";
  }

  return (
    <div className="resource">
      <div className="resource-header">
        <span>{label}</span>

        <span className="resource-value">
          {percentage.toFixed(1)}%
        </span>
      </div>

      <div className="resource-track">
        <div
          className="resource-fill"
          style={{
            width: `${percentage}%`,
            background: color,
          }}
        />
      </div>
    </div>
  );
}