"use client";

interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
}

export default function Sparkline({ values, width = 640, height = 120 }: SparklineProps) {
  if (values.length < 2) {
    return <p style={{ color: "#888", fontSize: "0.9rem" }}>Aún no hay suficiente histórico para graficar.</p>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = width / (values.length - 1);

  const points = values
    .map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto" }}>
      <polyline points={points} fill="none" stroke="#111" strokeWidth={2} />
    </svg>
  );
}
