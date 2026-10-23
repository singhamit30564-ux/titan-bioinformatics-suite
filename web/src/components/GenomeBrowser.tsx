/**
 * Genome Browser panel — igv.js loaded on demand.
 *
 * igv.js is intentionally NOT bundled: it is dynamically imported when the
 * user clicks Load. If the package is unavailable (offline install), the
 * panel degrades to an explanatory message — the app never crashes from a
 * missing optional engine, matching the Python-side philosophy.
 */
import { useRef, useState } from "react";
import { translate, type Language } from "../i18n";
import { Panel } from "./common";

interface IgvBrowser {
  remove(): void;
}

declare global {
  interface Window {
    igv?: {
      createBrowser(element: HTMLElement, options: Record<string, unknown>): Promise<IgvBrowser>;
    };
  }
}

export function GenomeBrowser({ language, referenceUrl }: { language: Language; referenceUrl: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [message, setMessage] = useState("");

  const load = async () => {
    if (!containerRef.current) return;
    setStatus("loading");
    setMessage("");
    try {
      // Dynamic import keeps igv.js out of the main bundle. The specifier is a
      // variable so TypeScript does not require the optional package at
      // build time (see web/optional-igv.txt).
      const igvSpecifier = "igv";
      const igvModule = (await import(/* @vite-ignore */ igvSpecifier)) as unknown as {
        default?: { createBrowser: (el: HTMLElement, opts: Record<string, unknown>) => Promise<IgvBrowser> };
        createBrowser?: (el: HTMLElement, opts: Record<string, unknown>) => Promise<IgvBrowser>;
      };
      const createBrowser = igvModule.default?.createBrowser ?? igvModule.createBrowser;
      if (!createBrowser) throw new Error("igv.js entry point missing");
      await createBrowser(containerRef.current, {
        genome: referenceUrl ? undefined : "hg38",
        reference: referenceUrl ? { fastaURL: referenceUrl, indexed: false } : undefined,
        tracks: [],
      });
      setStatus("ready");
    } catch (error) {
      setStatus("error");
      setMessage(
        `igv.js unavailable (${(error as Error).message}). Install web/optional-igv.txt to enable the embedded browser; every other view works without it.`,
      );
    }
  };

  return (
    <Panel title={translate("nav.genome", language)}>
      <p className="muted">{translate("genome.igv", language)}</p>
      <div className="row">
        <button className="action" onClick={() => void load()} disabled={status === "loading"}>
          {translate("genome.load", language)}
        </button>
        {status === "loading" && <span className="muted">Loading igv.js…</span>}
      </div>
      {message && <p className="error-text">{message}</p>}
      <div ref={containerRef} className="panel" style={{ minHeight: 220 }} aria-live="polite" />
    </Panel>
  );
}
