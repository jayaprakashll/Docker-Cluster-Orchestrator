function scoreColor(score) {
  if (score >= 80) return "#43e6a4";
  if (score >= 50) return "#ffc857";
  return "#ff6175";
}

export default function Gauge({
  score = 0,
  title = "SCORE",
}) {
  const value = Math.max(
    0,
    Math.min(100, Number(score) || 0)
  );

  const color = scoreColor(value);

  const radius = 48;
  const circumference = 2 * Math.PI * radius;

  const offset =
    circumference -
    (value / 100) * circumference;

  return (
    <div className="gauge">
      <svg
        viewBox="0 0 120 120"
        className="gauge-svg"
      >
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="#111b24"
          strokeWidth="9"
        />

        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
        />

        <text
          x="60"
          y="64"
          textAnchor="middle"
          fill="#edf6fa"
          fontSize="22"
          fontWeight="800"
        >
          {Math.round(value)}
        </text>
      </svg>

      <div className="gauge-title">
        {title}
      </div>
    </div>
  );
}