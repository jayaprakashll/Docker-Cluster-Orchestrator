export default function StatusBadge({
  status,
}) {
  const normalized = String(
    status || "unknown"
  ).toLowerCase();

  let className = "badge badge-warning";

  if (normalized === "healthy") {
    className = "badge badge-healthy";
  } else if (
    normalized === "offline" ||
    normalized === "unhealthy"
  ) {
    className = "badge badge-offline";
  }

  return (
    <span className={className}>
      ● {normalized.toUpperCase()}
    </span>
  );
}