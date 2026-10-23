#!/usr/bin/env Rscript
# testthat runner for the Titan DE bridge (no package scaffolding required).
# Usage: Rscript r/run_tests.R
library(testthat)

test_dir <- file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(trailingOnly = FALSE), value = TRUE)[1])), "tests", "testthat")
if (!dir.exists(test_dir)) {
  test_dir <- file.path("r", "tests", "testthat")
}
res <- test_dir(test_dir, reporter = "summary")
df <- as.data.frame(res)
if (sum(df$failed) > 0 || any(df$error)) {
  quit(status = 1)
}
quit(status = 0)
