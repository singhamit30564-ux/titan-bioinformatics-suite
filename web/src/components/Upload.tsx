/** Chunked in-RAM upload with drag/drop, progress, and accessible fallback. */
import { useRef, useState } from "react";
import { api } from "../api/client";
import { translate, type Language } from "../i18n";
import { Panel, Progress } from "./common";

export interface UploadResult {
  uploadId: string;
  name: string;
  size: number;
  kind: "fastq" | "vcf" | "bam" | "text";
}

function classify(file: File): UploadResult["kind"] {
  const name = file.name.toLowerCase();
  if (name.endsWith(".vcf") || name.endsWith(".vcf.gz")) return "vcf";
  if (name.endsWith(".bam") || name.endsWith(".sam")) return "bam";
  if (name.endsWith(".fastq") || name.endsWith(".fq") || name.endsWith(".fastq.gz")) return "fastq";
  return "text";
}

export function Upload({
  language,
  onUploaded,
}: {
  language: Language;
  onUploaded: (result: UploadResult) => void;
}) {
  const [fraction, setFraction] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File | undefined | null) => {
    if (!file) return;
    setError(null);
    setBusy(true);
    setFraction(0);
    try {
      const uploadId = await api.uploadFile(file, { onProgress: setFraction });
      onUploaded({ uploadId, name: file.name, size: file.size, kind: classify(file) });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel title={translate("nav.upload", language)}>
      <div
        className="panel"
        style={{ textAlign: "center", borderStyle: "dashed" }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          void handleFile(event.dataTransfer.files.item(0));
        }}
      >
        <p className="hl">{translate("upload.drop", language)}</p>
        <p className="muted">{translate("upload.chunked", language)}</p>
        <input
          ref={inputRef}
          type="file"
          aria-label={translate("nav.upload", language)}
          onChange={(event) => void handleFile(event.target.files?.item(0))}
        />
        <div className="row" style={{ justifyContent: "center", marginTop: 10 }}>
          <button
            className="action"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
          >
            {translate("upload.start", language)}
          </button>
        </div>
        {busy && <Progress fraction={fraction} />}
        {error && <p className="error-text">{error}</p>}
      </div>
      <p className="muted">{translate("zdr.notice", language)}</p>
    </Panel>
  );
}
