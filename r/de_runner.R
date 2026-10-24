#!/usr/bin/env Rscript
# Titan Bioinformatics Suite — differential expression R bridge.
#
# Reads one JSON payload on stdin (see titan_stats/r_bridge.py) and writes one
# JSON document on stdout. No file I/O, no network, no shell — the Python side
# invokes this with an argv list only. Failures exit non-zero with a short
# stderr tag; user data is never echoed into stderr.
#
# Engines: DESeq2 (default), edgeR, limma-voom. Each is optional; the script
# reports which one ran in the output ("method" field).

suppressPackageStartupMessages({
  ok_json <- requireNamespace("jsonlite", quietly = TRUE)
})
if (!ok_json) {
  cat("ERROR:jsonlite_missing\n", file = stderr())
  quit(status = 3)
}

payload_raw <- paste(readLines(file("stdin"), warn = FALSE, encoding = "UTF-8"), collapse = "")
if (nchar(payload_raw) == 0) {
  cat("ERROR:empty_input\n", file = stderr())
  quit(status = 2)
}
payload <- jsonlite::fromJSON(payload_raw, simplifyVector = TRUE)

mat <- payload$matrix
counts <- as.data.frame(mat$counts, stringsAsFactors = FALSE)
rownames(counts) <- as.character(mat$genes)
colnames(counts) <- as.character(mat$samples)
meta <- as.data.frame(mat$metadata, stringsAsFactors = FALSE)
rownames(meta) <- as.character(meta$sample)

method <- if (is.null(payload$method) || (length(payload$method) == 1 && is.na(payload$method))) {
  "deseq2"
} else {
  as.character(payload$method)
}
design <- if (is.null(payload$design)) "~ condition" else as.character(payload$design)
factor_col <- if (is.null(payload$factor) || payload$factor == "NULL") {
  sub("^~\\s*", "", strsplit(design, "\\+")[[1]][1])
} else {
  as.character(payload$factor)
}
treated <- if (is.null(payload$treated) || payload$treated == "NULL") NULL else as.character(payload$treated)
control <- if (is.null(payload$control) || payload$control == "NULL") NULL else as.character(payload$control)
min_count <- if (is.null(payload$min_count)) 10 else as.integer(payload$min_count)
min_samples <- if (is.null(payload$min_samples) || payload$min_samples == "NULL") {
  max(2L, floor(ncol(counts) / 2))
} else {
  as.integer(payload$min_samples)
}
seed <- if (is.null(payload$seed)) 1337L else as.integer(payload$seed)
set.seed(seed)

warnings_out <- character(0)

# ── Low-count filter ────────────────────────────────────────────────────────
keep <- rowSums(counts >= min_count, na.rm = TRUE) >= min_samples
n_filtered <- sum(!keep)
counts <- counts[keep, , drop = FALSE]
if (nrow(counts) == 0) {
  cat("ERROR:all_genes_filtered\n", file = stderr())
  quit(status = 4)
}

if (!(factor_col %in% colnames(meta))) {
  cat("ERROR:factor_missing\n", file = stderr())
  quit(status = 5)
}
meta[[factor_col]] <- as.character(meta[[factor_col]])
levels_present <- sort(unique(meta[[factor_col]]))
if (is.null(treated) || is.null(control)) {
  if (length(levels_present) != 2) {
    cat("ERROR:contrast_required\n", file = stderr())
    quit(status = 6)
  }
  control <- levels_present[1]
  treated <- levels_present[2]
}
if (!(treated %in% levels_present) || !(control %in% levels_present)) {
  cat("ERROR:contrast_levels_missing\n", file = stderr())
  quit(status = 6)
}

sample_order <- colnames(counts)
meta <- meta[sample_order, , drop = FALSE]
group <- factor(meta[[factor_col]], levels = c(control, treated))

# ── Outlier detection (per engine) ─────────────────────────────────────────
# DESeq2: Cook's distance gene flags (standard DESeq2 semantics: F-distribution
# cutoff at 99%). edgeR: robust QL estimation (statmod) down-weights outlier
# samples. limma: eBayes robust = TRUE (M-estimation outlier resistance).
cooks_matrix <- NULL
outlier_info <- list(engine = method, flagged_genes = list(), notes = character(0))

results <- NULL
normalized <- NULL
dispersion <- NULL
size_factors <- list()
method_label <- paste0("r-", method)

if (method == "deseq2" && requireNamespace("DESeq2", quietly = TRUE)) {
  suppressPackageStartupMessages(library(DESeq2))
  coldata <- data.frame(row.names = sample_order, condition = group)
  dds <- DESeqDataSetFromMatrix(countData = round(as.matrix(counts)), colData = coldata, design = ~ condition)
  dds <- DESeq(dds, quiet = TRUE)
  res <- as.data.frame(results(dds, contrast = c("condition", treated, control)))
  res$gene <- rownames(res)
  results <- res[, c("gene", "baseMean", "log2FoldChange", "stat", "pvalue", "padj")]
  colnames(results) <- c("gene", "baseMean", "log2FC", "stat", "pvalue", "padj")
  normalized <- as.data.frame(counts(dds, normalized = TRUE))
  normalized$gene <- rownames(normalized)
  dispersion <- as.list(mcols(dds)$dispGeneEst)
  names(dispersion) <- rownames(dds)
  size_factors <- as.list(sizeFactors(dds))
  # Cook's-distance outlier flags (DESeq2 standard: F(p, m-p) 99% cutoff).
  cooks_matrix <- assays(dds)[["cooks"]]
  if (!is.null(cooks_matrix)) {
    p_params <- ncol(model.matrix(design(dds), colData(dds)))
    m_samples <- ncol(dds)
    cooks_cutoff <- qf(0.99, p_params, m_samples - p_params)
    flagged <- apply(cooks_matrix, 1, function(row) any(row > cooks_cutoff, na.rm = TRUE))
    outlier_info$cooks_cutoff <- cooks_cutoff
    outlier_info$flagged_genes <- as.list(rownames(dds)[flagged])
    outlier_info$notes <- c(
      outlier_info$notes,
      sprintf("DESeq2 Cook's distance cutoff %.3f (F(%d,%d), 99%%); %d gene(s) flagged.", cooks_cutoff, p_params, m_samples - p_params, sum(flagged))
    )
  } else {
    outlier_info$notes <- c(outlier_info$notes, "Cook's distances unavailable (replicates too few); no outlier flags computed.")
  }
} else if (method == "edger" && requireNamespace("edgeR", quietly = TRUE)) {
  suppressPackageStartupMessages(library(edgeR))
  y <- DGEList(counts = round(as.matrix(counts)), group = group)
  y <- calcNormFactors(y)
  design_matrix <- model.matrix(~ group)
  robust_ok <- TRUE
  y <- tryCatch(estimateDisp(y, design_matrix, robust = TRUE), error = function(e) { robust_ok <<- FALSE; estimateDisp(y, design_matrix) })
  fit <- tryCatch(glmQLFit(y, design_matrix, robust = TRUE), error = function(e) { robust_ok <<- FALSE; glmQLFit(y, design_matrix) })
  qlf <- glmQLFTest(fit, coef = 2)
  tab <- as.data.frame(topTags(qlf, n = nrow(counts), sort.by = "none")$table)
  tab$gene <- rownames(tab)
  results <- data.frame(
    gene = tab$gene,
    baseMean = rowMeans(cpm(y, log = FALSE)),
    log2FC = tab$logFC,
    stat = tab$F,
    pvalue = tab$PValue,
    padj = tab$FDR,
    stringsAsFactors = FALSE
  )
  normalized <- as.data.frame(cpm(y, log = FALSE))
  normalized$gene <- rownames(normalized)
  size_factors <- as.list(y$samples$norm.factors)
  method_label <- "r-edger"
  outlier_info$notes <- c(
    outlier_info$notes,
    if (robust_ok) "edgeR robust QL estimation active (statmod) — outlier samples down-weighted."
    else "edgeR robust QL unavailable (statmod missing); standard estimation used — no outlier down-weighting."
  )
} else if (method == "limma" && requireNamespace("limma", quietly = TRUE)) {
  suppressPackageStartupMessages(library(limma))
  logcpm <- cpm(as.matrix(counts), log = TRUE, prior.count = 3)
  design_matrix <- model.matrix(~ group)
  fit <- eBayes(lmFit(logcpm, design_matrix), robust = TRUE)
  tab <- topTable(fit, coef = 2, number = nrow(counts), sort.by = "none")
  tab$gene <- rownames(tab)
  results <- data.frame(
    gene = tab$gene,
    baseMean = 2^tab$AveExpr,
    log2FC = tab$logFC,
    stat = tab$t,
    pvalue = tab$P.Value,
    padj = tab$adj.P.Val,
    stringsAsFactors = FALSE
  )
  normalized <- as.data.frame(2^logcpm)
  normalized$gene <- rownames(normalized)
  method_label <- "r-limma"
  outlier_info$notes <- c(outlier_info$notes, "limma eBayes(robust = TRUE) — outlier variance observations down-weighted.")
} else {
  cat("ERROR:requested_package_absent\n", file = stderr())
  quit(status = 7)
}

if (method == "deseq2") method_label <- "r-deseq2"
outlier_info$engine <- method_label

results <- results[order(results$padj, na.last = TRUE), , drop = FALSE]
contrast_out <- list(factor = factor_col, treated = treated, control = control)
versions <- list(
  R = R.version.string,
  DESeq2 = if (requireNamespace("DESeq2", quietly = TRUE)) as.character(packageVersion("DESeq2")) else "absent",
  edgeR = if (requireNamespace("edgeR", quietly = TRUE)) as.character(packageVersion("edgeR")) else "absent",
  limma = if (requireNamespace("limma", quietly = TRUE)) as.character(packageVersion("limma")) else "absent"
)

out <- list(
  ok = TRUE,
  method = method_label,
  results = results,
  normalized_counts = normalized,
  dispersion = dispersion,
  size_factors = size_factors,
  n_genes_filtered = n_filtered,
  contrast = contrast_out,
  outliers = outlier_info,
  warnings = warnings_out,
  versions = versions
)
cat(jsonlite::toJSON(out, auto_unbox = TRUE, digits = 8, na = "null"))
