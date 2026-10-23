/** Settings — API base (display only; same-origin), reference genome, language. */
import { translate, type Language, LANGUAGES } from "../i18n";
import { Metric, Panel } from "./common";

export function Settings({
  language,
  onLanguageChange,
  referenceUrl,
  onReferenceUrlChange,
  engineStatus,
}: {
  language: Language;
  onLanguageChange: (language: Language) => void;
  referenceUrl: string;
  onReferenceUrlChange: (url: string) => void;
  engineStatus: Record<string, unknown> | null;
}) {
  return (
    <Panel title={translate("settings.title", language)}>
      <div className="grid">
        <div className="field">
          <label htmlFor="st-api">{translate("settings.api", language)}</label>
          <input id="st-api" type="text" value="/api/v2" readOnly />
        </div>
        <div className="field">
          <label htmlFor="st-ref">{translate("settings.ref", language)}</label>
          <input
            id="st-ref"
            type="text"
            value={referenceUrl}
            placeholder="https://…/hg38.fa"
            onChange={(event) => onReferenceUrlChange(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="st-lang">{translate("settings.language", language)}</label>
          <select
            id="st-lang"
            value={language}
            onChange={(event) => onLanguageChange(event.target.value as Language)}
          >
            {LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>
                {lang === "en" ? "English" : "हिंदी"}
              </option>
            ))}
          </select>
        </div>
      </div>
      <h3>{translate("engine.status", language)}</h3>
      <div className="grid">
        <Metric label="Active engine" value={String(engineStatus?.active ?? "unknown")} />
        <Metric label="Rust" value={String(engineStatus?.rust_version ?? "not installed")} />
        <Metric label="Python fallback" value={String(engineStatus?.python_fallback ?? false)} />
        <Metric label="R bridge" value={String(engineStatus?.r_available ?? false)} />
      </div>
      <p className="muted">{translate("zdr.notice", language)}</p>
    </Panel>
  );
}
