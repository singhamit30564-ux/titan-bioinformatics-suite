/** SVG charts with brush selection, linked highlight and SVG/PNG export. */
import { useMemo, useRef, useState } from "react";
import { downloadBlob, downloadJson } from "../api/client";
import { translate, type Language } from "../i18n";

export interface ScatterPoint {
  id: string;
  x: number;
  y: number;
  group?: string;
  significant?: boolean;
}

const PALETTE = ["#d4af37", "#66fcf1", "#ff0055", "#88ff88", "#c792ea"];

export function ScatterChart({
  title,
  xLabel,
  yLabel,
  points,
  language,
  selection,
  onSelectionChange,
}: {
  title: string;
  xLabel: string;
  yLabel: string;
  points: ScatterPoint[];
  language: Language;
  selection: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [brush, setBrush] = useState<{ x0: number; y0: number; x1: number; y1: number } | null>(null);
  const width = 720;
  const height = 380;
  const pad = 44;

  const bounds = useMemo(() => {
    const xs = points.map((p) => p.x);
    const ys = points.map((p) => p.y);
    return {
      xMin: Math.min(...xs, 0),
      xMax: Math.max(...xs, 1),
      yMin: Math.min(...ys, 0),
      yMax: Math.max(...ys, 1),
    };
  }, [points]);

  const scaleX = (value: number) =>
    pad + ((value - bounds.xMin) / (bounds.xMax - bounds.xMin || 1)) * (width - 2 * pad);
  const scaleY = (value: number) =>
    height - pad - ((value - bounds.yMin) / (bounds.yMax - bounds.yMin || 1)) * (height - 2 * pad);

  const groups = useMemo(() => [...new Set(points.map((p) => p.group ?? "all"))], [points]);

  const toSvgCoords = (event: React.PointerEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: ((event.clientX - rect.left) / rect.width) * width,
      y: ((event.clientY - rect.top) / rect.height) * height,
    };
  };

  const commitBrush = () => {
    if (!brush) return;
    const selected = new Set<string>();
    for (const point of points) {
      const px = scaleX(point.x);
      const py = scaleY(point.y);
      const inX = px >= Math.min(brush.x0, brush.x1) && px <= Math.max(brush.x0, brush.x1);
      const inY = py >= Math.min(brush.y0, brush.y1) && py <= Math.max(brush.y0, brush.y1);
      if (inX && inY) selected.add(point.id);
    }
    onSelectionChange(selected);
    setBrush(null);
  };

  const exportSvg = () => {
    const svg = svgRef.current;
    if (!svg) return;
    downloadBlob(`${title}.svg`, new Blob([svg.outerHTML], { type: "image/svg+xml" }));
  };

  const exportPng = () => {
    const svg = svgRef.current;
    if (!svg) return;
    const canvas = document.createElement("canvas");
    canvas.width = width * 2;
    canvas.height = height * 2;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const image = new Image();
    image.onload = () => {
      ctx.fillStyle = "#0d1320";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      canvas.toBlob((blob) => blob && downloadBlob(`${title}.png`, blob), "image/png");
    };
    image.src = `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg.outerHTML)))}`;
  };

  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h3>{title}</h3>
        <div className="row">
          <button className="action secondary" onClick={exportSvg}>
            {translate("export.svg", language)}
          </button>
          <button className="action secondary" onClick={exportPng}>
            {translate("export.png", language)}
          </button>
          <button className="action secondary" onClick={() => downloadJson(`${title}.json`, points)}>
            {translate("export.json", language)}
          </button>
          {selection.size > 0 && (
            <button className="action secondary" onClick={() => onSelectionChange(new Set())}>
              Clear ({selection.size})
            </button>
          )}
        </div>
      </div>
      <svg
        ref={svgRef}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={title}
        tabIndex={0}
        style={{ width: "100%", background: "#0d1320", borderRadius: 8, touchAction: "none" }}
        onPointerDown={(event) => {
          const coords = toSvgCoords(event);
          setBrush({ x0: coords.x, y0: coords.y, x1: coords.x, y1: coords.y });
          (event.target as Element).setPointerCapture?.(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (!brush) return;
          const coords = toSvgCoords(event);
          setBrush({ ...brush, x1: coords.x, y1: coords.y });
        }}
        onPointerUp={commitBrush}
      >
        <line x1={pad} x2={width - pad} y1={height - pad} y2={height - pad} stroke="#2a3142" />
        <line x1={pad} x2={pad} y1={pad} y2={height - pad} stroke="#2a3142" />
        <text x={width / 2} y={height - 8} fill="#9aa4b2" fontSize="12" textAnchor="middle">
          {xLabel}
        </text>
        <text x={12} y={height / 2} fill="#9aa4b2" fontSize="12" transform={`rotate(-90 12 ${height / 2})`}>
          {yLabel}
        </text>
        {points.map((point) => {
          const selected = selection.has(point.id);
          const groupIndex = Math.max(0, groups.indexOf(point.group ?? "all"));
          const fill = point.significant ? PALETTE[groupIndex % PALETTE.length] : "#3a4662";
          return (
            <circle
              key={point.id}
              cx={scaleX(point.x)}
              cy={scaleY(point.y)}
              r={selected ? 6 : 3.5}
              fill={fill}
              stroke={selected ? "#ffd75e" : "none"}
              strokeWidth={selected ? 2 : 0}
              opacity={selection.size > 0 && !selected ? 0.35 : 0.9}
            >
              <title>{`${point.id} (${point.x.toFixed(2)}, ${point.y.toFixed(2)})`}</title>
            </circle>
          );
        })}
        {brush && (
          <rect
            x={Math.min(brush.x0, brush.x1)}
            y={Math.min(brush.y0, brush.y1)}
            width={Math.abs(brush.x1 - brush.x0)}
            height={Math.abs(brush.y1 - brush.y0)}
            fill="rgba(212,175,55,0.15)"
            stroke="#d4af37"
            strokeDasharray="5 4"
          />
        )}
      </svg>
    </div>
  );
}

export function VolcanoChart({
  rows,
  language,
  selection,
  onSelectionChange,
}: {
  rows: { gene: string; log2FC: number; padj: number }[];
  language: Language;
  selection: Set<string>;
  onSelectionChange: (ids: Set<string>) => void;
}) {
  const points: ScatterPoint[] = rows
    .filter((row) => Number.isFinite(row.log2FC) && Number.isFinite(row.padj))
    .map((row) => ({
      id: row.gene,
      x: row.log2FC,
      y: -Math.log10(Math.max(row.padj, 1e-300)),
      significant: row.padj < 0.05 && Math.abs(row.log2FC) >= 1,
    }));
  return (
    <ScatterChart
      title="Volcano (log2FC vs -log10 FDR)"
      xLabel="log2 fold change"
      yLabel="-log10(FDR)"
      points={points}
      language={language}
      selection={selection}
      onSelectionChange={onSelectionChange}
    />
  );
}
