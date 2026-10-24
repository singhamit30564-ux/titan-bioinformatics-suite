/**
 * Web Worker entry: wires vcfCore parsing/filtering to postMessage so 1M-row
 * tables never jank the main thread.
 */
import { filterVcfRows, parseVcfRows, type VcfFilters } from "./vcfCore";

self.onmessage = (event: MessageEvent) => {
  const { vcfText, filters } = event.data as { vcfText: string; filters: VcfFilters };
  const all = parseVcfRows(vcfText);
  const filtered = filterVcfRows(all, filters ?? {});
  self.postMessage({ rows: filtered.slice(0, 5000), total: all.length, filtered: filtered.length });
};
