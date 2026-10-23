/** WebGL-free canvas heatmap with zoom, hover crosshair and PNG export. */
import { useEffect, useRef, useState } from "react";
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

  const flat = data.values.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cell = 18 * zoom;
    const width = Math.max(1, Math.ceil(data.columns.length * cell));
    const height = Math.max(1, Math.ceil(data.rows.length * cell));
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = "#0d1320";
    ctx.fillRect(0, 0, width, height);
    data.values.forEach((row, rowIndex) => {
      row.forEach((value, columnIndex) => {
        ctx.fillStyle = colorFor(value, min, max);
        ctx.fillRect(columnIndex * cell, rowIndex * cell, cell - 1, cell - 1);
      });
    });
  }, [data, zoom, min, max]);

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
        {hover && data.rows[hover.row] && data.columns[hover.col]
          ? `${data.rows[hover.row]} × ${data.columns[hover.col]} = ${data.values[hover.row]?.[hover.col]?.toFixed(3)}`
          : `${data.rows.length} rows × ${data.columns.length} columns`}
      </p>
    </div>
  );
}
