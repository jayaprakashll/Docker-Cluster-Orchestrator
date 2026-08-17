export default function EcgChart({
  active = true,
}) {
  const points = [];

  for (let i = 0; i < 500; i++) {
    const t = i / 50;
    const phase = t % 1;

    let value =
      0.018 * Math.sin(t * 7);

    if (active) {
      if (phase > 0.18 && phase < 0.205) {
        value +=
          ((phase - 0.18) / 0.025) * 0.75;
      } else if (
        phase >= 0.205 &&
        phase < 0.235
      ) {
        value =
          0.75 -
          ((phase - 0.205) / 0.03) * 1.5;
      } else if (
        phase >= 0.235 &&
        phase < 0.29
      ) {
        value =
          -0.75 +
          ((phase - 0.235) / 0.055) *
            0.75;
      }
    }

    const x = (i / 499) * 500;
    const y = 48 - value * 35;

    points.push(`${x},${y}`);
  }

  return (
    <div className="ecg-shell">
      <svg
        viewBox="0 0 500 96"
        preserveAspectRatio="none"
        className="ecg-svg"
      >
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke={
            active
              ? "#39d8ff"
              : "#384651"
          }
          strokeWidth="2"
        />
      </svg>
    </div>
  );
}