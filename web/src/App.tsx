import { useState } from "react";
import { translate, type Language } from "./i18n";
import { useEngineStatus } from "./hooks/useJobs";
import { Upload, type UploadResult } from "./components/Upload";
import { QCReport } from "./components/QCReport";
import { DEPanel } from "./components/DEPanel";
import { VariantExplorer } from "./components/VariantExplorer";
import { GenomeBrowser } from "./components/GenomeBrowser";
import { JobHistory } from "./components/JobHistory";
import { Settings } from "./components/Settings";

type View = "upload" | "qc" | "de" | "variants" | "genome" | "jobs" | "settings";

const VIEWS: { id: View; key: string }[] = [
  { id: "upload", key: "nav.upload" },
  { id: "qc", key: "nav.qc" },
  { id: "de", key: "nav.de" },
  { id: "variants", key: "nav.variants" },
  { id: "genome", key: "nav.genome" },
  { id: "jobs", key: "nav.jobs" },
  { id: "settings", key: "nav.settings" },
];

const DEMO_VCF = `##fileformat=VCFv4.2
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
chr1\t100\trs123\tA\tG\t50\tPASS\tAF=0.001;Consequence=missense_variant;CLNSIG=Pathogenic
chr1\t150\trs124\tC\tT\t45\tPASS\tAF=0.42;Consequence=synonymous_variant;CLNSIG=Benign
chr2\t50\trs125\tG\tGAT\t60\tPASS\tAF=0.02;Consequence=frameshift_variant;CLNSIG=Likely_pathogenic
chr2\t100\trs126\tA\tA\t30\tLowQual\tAF=0.5;Consequence=intron_variant`;

export default function App() {
  const [language, setLanguage] = useState<Language>("en");
  const [view, setView] = useState<View>("upload");
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [vcfText, setVcfText] = useState<string>(DEMO_VCF);
  const [referenceUrl, setReferenceUrl] = useState("");
  const engineStatus = useEngineStatus();
  const t = (key: string) => translate(key, language);

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1 className="brand">
          <span aria-hidden="true">🧬</span>
          <span>{t("app.title")}</span>
        </h1>
        <span className="badge gold">{t("app.tagline")}</span>
        <div className="spacer" />
        <span className="badge">
          {t("engine.status")}: {String(engineStatus?.active ?? "…")}
        </span>
        <button
          className="action secondary"
          aria-label="Switch language"
          onClick={() => setLanguage((lang) => (lang === "en" ? "hi" : "en"))}
        >
          {t("lang.toggle")}
        </button>
      </header>

      <nav className="nav" aria-label="Primary">
        {VIEWS.map((entry) => (
          <button
            key={entry.id}
            aria-current={view === entry.id ? "page" : undefined}
            onClick={() => setView(entry.id)}
          >
            {t(entry.key)}
          </button>
        ))}
      </nav>

      <main>
        {view === "upload" && (
          <>
            <Upload language={language} onUploaded={setUpload} />
            {upload && (
              <p className="ok-text">
                Uploaded <span className="hl">{upload.name}</span> ({(upload.size / 1e6).toFixed(2)} MB, {upload.kind})
                — upload_id <code>{upload.uploadId}</code>
              </p>
            )}
          </>
        )}
        {view === "qc" && <QCReport language={language} upload={upload} />}
        {view === "de" && <DEPanel language={language} />}
        {view === "variants" && (
          <VariantExplorer
            language={language}
            vcfText={vcfText}
            onVcfTextChange={setVcfText}
            demoVcf={DEMO_VCF}
            uploadId={upload?.uploadId ?? null}
          />
        )}
        {view === "genome" && <GenomeBrowser language={language} referenceUrl={referenceUrl} />}
        {view === "jobs" && <JobHistory language={language} />}
        {view === "settings" && (
          <Settings
            language={language}
            onLanguageChange={setLanguage}
            referenceUrl={referenceUrl}
            onReferenceUrlChange={setReferenceUrl}
            engineStatus={engineStatus}
          />
        )}
      </main>

      <footer className="titan">
        Titan Bioinformatics Suite · Zero Data Retention (RAM only, SHA-256 provenance) · Free CSV/JSON/SVG/PNG
        exports · EN/हिंदी
      </footer>
    </div>
  );
}
