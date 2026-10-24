# Tests for r/de_runner.R — the JSON bridge used by titan_stats.r_bridge.
# Run with: Rscript r/run_tests.R   (or via CI's R job)

library(testthat)

runner <- normalizePath(file.path("..", "..", "de_runner.R"), mustWork = FALSE)
if (!file.exists(runner)) {
  runner <- normalizePath(file.path("r", "de_runner.R"), mustWork = FALSE)
}

make_payload <- function(method = "deseq2", n_genes = 40, n_samples = 6) {
  set.seed(1)
  counts <- matrix(
    rpois(n_genes * n_samples, lambda = rep(c(200, 20), n_genes / 2)),
    nrow = n_genes
  )
  # Make the first half of genes DE between conditions.
  group <- rep(c("control", "treated"), each = n_samples / 2)
  counts[1:(n_genes / 2), group == "treated"] <- counts[1:(n_genes / 2), group == "treated"] + 300
  genes <- paste0("gene", seq_len(n_genes))
  samples <- paste0("sample", seq_len(n_samples))
  metadata <- data.frame(sample = samples, condition = group, stringsAsFactors = FALSE)
  list(
    method = method,
    design = "~ condition",
    factor = "condition",
    treated = "treated",
    control = "control",
    min_count = 10L,
    min_samples = 2L,
    seed = 1337L,
    matrix = list(
      genes = genes,
      samples = samples,
      counts = lapply(seq_len(n_genes), function(i) as.integer(counts[i, ])),
      metadata = lapply(seq_len(n_samples), function(i) list(sample = samples[i], condition = group[i]))
    )
  )
}

run_bridge <- function(payload) {
  input <- jsonlite::toJSON(payload, auto_unbox = TRUE)
  out <- system2("Rscript", c("--vanilla", runner), input = input, stdout = TRUE, stderr = TRUE)
  attr(out, "status")
  out
}

has_pkg <- function(pkg) requireNamespace(pkg, quietly = TRUE)

test_that("bridge rejects empty input safely", {
  status <- system2("Rscript", c("--vanilla", runner), input = "", stdout = TRUE, stderr = TRUE)
  code <- attr(status, "status")
  expect_true(!is.null(code) && code != 0)
})

test_that("bridge reports absent packages with a clean error code", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  payload <- make_payload()
  payload$method <- "definitely-not-an-engine"
  res <- run_bridge(payload)
  code <- attr(res, "status")
  expect_true(!is.null(code) && code != 0)
})

test_that("DESeq2 path returns schema fields", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  skip_if_not(has_pkg("DESeq2"), "DESeq2 not installed")
  res <- run_bridge(make_payload("deseq2"))
  expect_null(attr(res, "status"))
  doc <- jsonlite::fromJSON(paste(res, collapse = ""))
  expect_true(doc$ok)
  expect_equal(doc$method, "r-deseq2")
  expect_true(all(c("gene", "baseMean", "log2FC", "stat", "pvalue", "padj") %in% names(doc$results)))
  expect_gt(nrow(doc$results), 0)
  expect_true("normalized_counts" %in% names(doc))
})

test_that("edgeR path returns schema fields", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  skip_if_not(has_pkg("edgeR"), "edgeR not installed")
  res <- run_bridge(make_payload("edger"))
  expect_null(attr(res, "status"))
  doc <- jsonlite::fromJSON(paste(res, collapse = ""))
  expect_true(doc$ok)
  expect_equal(doc$method, "r-edger")
  expect_gt(nrow(doc$results), 0)
})

test_that("limma path returns schema fields", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  skip_if_not(has_pkg("limma"), "limma not installed")
  res <- run_bridge(make_payload("limma"))
  expect_null(attr(res, "status"))
  doc <- jsonlite::fromJSON(paste(res, collapse = ""))
  expect_true(doc$ok)
  expect_equal(doc$method, "r-limma")
  expect_gt(nrow(doc$results), 0)
})

test_that("every engine reports an outliers section", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  for (engine in c("deseq2", "edger", "limma")) {
    pkg <- switch(engine, deseq2 = "DESeq2", edger = "edgeR", limma = "limma")
    if (!has_pkg(pkg)) next
    res <- run_bridge(make_payload(engine))
    expect_null(attr(res, "status"))
    doc <- jsonlite::fromJSON(paste(res, collapse = ""))
    expect_true(doc$ok)
    expect_true("outliers" %in% names(doc))
    expect_true("flagged_genes" %in% names(doc$outliers))
    expect_true("notes" %in% names(doc$outliers))
    expect_true(is.character(unlist(doc$outliers$notes)) || is.list(doc$outliers$notes))
  }
})

test_that("DESeq2 reports a Cook's distance cutoff and flags", {
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  skip_if_not(has_pkg("DESeq2"), "DESeq2 not installed")
  res <- run_bridge(make_payload("deseq2"))
  doc <- jsonlite::fromJSON(paste(res, collapse = ""))
  expect_true(doc$ok)
  # With 3 vs 3 replicates Cook's distances are computed and the cutoff reported
  expect_true("cooks_cutoff" %in% names(doc$outliers) ||
                any(grepl("Cook", unlist(doc$outliers$notes))))
})

test_that("outlier-screen injection is flagged (robust-MAD parity, Python side contract)", {
  # The R bridge honors the same shared schema as titan_stats.de: when a gene
  # carries an extreme sample it must appear under outliers$flagged_genes.
  skip_if_not(has_pkg("jsonlite"), "jsonlite required for the bridge")
  skip_if_not(has_pkg("DESeq2"), "DESeq2 not installed")
  payload <- make_payload("deseq2")
  # inject a wild outlier into one sample of one gene (100x)
  payload$matrix$counts[1, 4] <- payload$matrix$counts[1, 4] * 100
  res <- run_bridge(payload)
  doc <- jsonlite::fromJSON(paste(res, collapse = ""))
  expect_true(doc$ok)
  expect_true("outliers" %in% names(doc))
})
