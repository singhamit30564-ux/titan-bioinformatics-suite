/**
 * Titan web gateway (Node 20 / Express).
 *
 * Serves the built dashboard and proxies to the FastAPI backend:
 *   - HTTP  /api/*  → TITAN_API_ORIGIN (default http://127.0.0.1:8000)
 *   - WS    /api/v2/jobs/:id/stream → same origin (http-proxy-middleware ws)
 *
 * CORS allow-list mirrors titan_utils/api_v2.py via TITAN_CORS_ORIGINS.
 * Security: no shell execution, no secrets in code, no access logging of
 * request BODIES (sequence data must never reach logs).
 */
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT ?? 4173);
const API_ORIGIN = process.env.TITAN_API_ORIGIN ?? "http://127.0.0.1:8000";
const CORS_ORIGINS = (process.env.TITAN_CORS_ORIGINS ?? "http://localhost:4173,http://127.0.0.1:4173")
  .split(",")
  .map((part) => part.trim())
  .filter(Boolean);

const app = express();

// Minimal, allow-list CORS for direct gateway access.
app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (origin && CORS_ORIGINS.includes(origin)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
    res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  }
  if (req.method === "OPTIONS") {
    res.sendStatus(204);
    return;
  }
  next();
});

const apiProxy = createProxyMiddleware({
  target: API_ORIGIN,
  changeOrigin: true,
  ws: true,
  logLevel: "warn",
  // Never log URLs containing potential sequence query params.
  pathRewrite: (pathRewritten) => pathRewritten,
  onProxyReq: (proxyReq) => {
    proxyReq.removeHeader("x-forwarded-email");
    proxyReq.removeHeader("cookie");
  },
});

app.use("/api", apiProxy);

const staticDir = path.join(__dirname, "..", "dist");
app.use(express.static(staticDir, { index: "index.html", maxAge: "1h" }));
app.get("*", (_req, res) => {
  res.setHeader("Cache-Control", "no-store");
  res.sendFile(path.join(staticDir, "index.html"));
});

const server = app.listen(PORT, "0.0.0.0", () => {
  process.stdout.write(`titan-web gateway listening on 0.0.0.0:${PORT} -> ${API_ORIGIN}\n`);
});

server.on("upgrade", apiProxy.upgrade);

process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});
