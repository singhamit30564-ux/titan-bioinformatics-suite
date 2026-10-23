/** WebGL-free canvas heatmap with zoom, hover crosshair and PNG export. */
import { useEffect, useMemo, useRef, useState } from "react";
import { downloadBlob } from "../api/client";
import { translate, type Language } from "../i18n";

export interface HeatmapInput {
  rows: string[];
  columns: string[];
  values: number[][]; // values[rowIndex][columnIndex]
}

function colorFor(value: number, min: number, max: number): string {
  const t = max === min ? 0.5 : (value - min) / (max - min);
  // Titan ramp: deep navy -> gold -> teal
  const stops = [
    [13, 19, 32],
    [212, 175, 55],
    [102, 252, 241],
  ];
  const scaled = t * (stops.length - 1);
  const index = Math.min(stops.length - 2, Math.floor(scaled));
  const frac = scaled - index;
  const rgb = stops[index].map((channel, i) => Math.round(channel + (stops[index + 1][i] - channel) * frac));
  return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
}

/** Average-linkage agglomerative clustering order (Euclidean distance). */
export function hierarchicalOrder(matrix: number[][]): number[] {
  const n = matrix.length;
  if (n <= 2) return matrix.map((_, i) => i);
  const dist = (a: number[], b: number[]): number => {
    let sum = 0;
    for (let i = 0; i < a.length; i += 1) {
      const delta = (a[i] ?? 0) - (b[i] ?? 0);
      sum += delta * delta;
    }
    return Math.sqrt(sum);
  };
  let clusters: number[][] = matrix.map((_, i) => [i]);
  const distances = new Map<string, number>();
  const key = (x: number, y: number) => `${Math.min(x, y)}:${Math.max(x, y)}`;
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 1; j < n; j += 1) {
      distances.set(key(i, j), dist(matrix[i], matrix[j]));
    }
  }
  const clusterDistance = (c1: number[], c2: number[]): number => {
    let total = 0;
    let count = 0;
    for (const i of c1) {
      for (const j of c2) {
        total += distances.get(key(i, j)) ?? dist(matrix[i], matrix[j]);
        count += 1;
      }
    }
    return count ? total / count : 0;
  };
  while (clusters.length > 1) {
    let best = [0, 1];
    let bestDist = Infinity;
    for (let a = 0; a < clusters.length; a += 1) {
      for (let b = a + 1; b < clusters.length; b += 1) {
        const d = clusterDistance(clusters[a], clusters[b]);
        if (d < bestDist) {
          bestDist = d;
          best = [a, b];
        }
      }
    }
    const [a, b] = best;
    const merged = [...clusters[a], ...clusters[b]];
    clusters = clusters.filter((_, index) => index !== a && index !== b);
    clusters.push(merged);
  }
  return clusters[0] ?? matrix.map((_, i) => i);
}

export function Heatmap({
  data,
  language,
  title = "Clustered heatmap",
}: {
  data: HeatmapInput;
  language: Language;
  title?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [zoom, setZoom] = useState(1);
  const [hover, setHover] = useState<{ row: number; col: number } | null>(null);
  const [clustered, setClustered] = useState(false);

  const ordered = useMemo(() => {
    if (!clustered) return data;
    const rowOrder = hierarchicalOrder(data.values);
    const transposed = data.values[0]?.map((_, columnIndex) => data.values.map((row) => row[columnIndex])) ?? [];
    const colOrder = hierarchicalOrder(transposed);
    return {
      rows: rowOrder.map((i) => data.rows[i]),
      columns: colOrder.map((j) => data.columns[j]),
      values: rowOrder.map((i) => colOrder.map((j) => data.values[i][j])),
    };
  }, [data, clustered]);

  const flat = ordered.values.flat();
  const min = flat.length ? Math.min(...flat) : 0;
  const max = flat.length ? Math.max(...flat) : 1;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cell = 18 * zoom;
    const width = Math.max(1, Math.ceil(ordered.columns.length * cell));
    const height = Math.max(1, Math.ceil(ordered.rows.length * cell));
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#0d1320";
    ctx.fillRect(0, 0, width, height);
    ordered.values.forEach((row, rowIndex) => {
      row.forEach((value, columnIndex) => {
        ctx.fillStyle = colorFor(value, min, max);
        ctx.fillRect(columnIndex * cell, rowIndex * cell, cell - 1, cell - 1);
      });
    });
  }, [ordered, zoom, min, max]);

  const exportPng = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob((blob) => blob && downloadBlob(`${title}.png`, blob), "image/png");
  };

  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>{title}</h3>
        <div className="row">
          <button
            className={`action ${clustered ? "" : "secondary"}`}
            aria-pressed={clustered}
            onClick={() => setClustered((value) => !value)}
          >
            {clustered ? "Clustered ✓" : "Cluster rows & columns"}
          </button>
          <button className="action secondary" onClick={() => setZoom((z) => Math.min(4, z + 0.5))}>
            Zoom in
          </button>
          <button className="action secondary" onClick={() => setZoom((z) => Math.max(0.5, z - 0.5))}>
            Zoom out
          </button>
          <button className="action secondary" onClick={exportPng}>
            {translate("export.png", language)}
          </button>
        </div>
      </div>
      <div className="virtual-wrap" style={{ height: 360 }}>
        <canvas
          ref={canvasRef}
          aria-label={title}
          role="img"
          onMouseMove={(event) => {
            const rect = event.currentTarget.getBoundingClientRect();
            const cell = 18 * zoom;
            const col = Math.floor(((event.clientX - rect.left) / rect.width) * (event.currentTarget.width / cell));
            const row = Math.floor(((event.clientY - rect.top) / rect.height) * (event.currentTarget.height / cell));
            setHover({ row, col });
          }}
          onMouseLeave={() => setHover(null)}
        />
      </div>
      <p className="muted">
        {hover && ordered.rows[hover.row] && ordered.columns[hover.col]
          ? `${ordered.rows[hover.row]} × ${ordered.columns[hover.col]} = ${ordered.values[hover.row]?.[hover.col]?.toFixed(3)}`
          : `${ordered.rows.length} rows × ${ordered.columns.length} columns`}
      </p>
    </div>
  );
}
