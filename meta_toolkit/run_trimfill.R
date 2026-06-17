# run_trimfill.R - Trim-and-Fill analysis script
# Called by Python via subprocess
# Reads JSON input, runs metafor trimfill, writes JSON output

library(metafor)

# ---- Parse command line args ----
args <- commandArgs(trailingOnly = TRUE)
input_file <- NULL
output_file <- NULL

for (i in seq_along(args)) {
  if (args[i] == "--input" && i < length(args)) {
    input_file <- args[i + 1]
  } else if (args[i] == "--output" && i < length(args)) {
    output_file <- args[i + 1]
  }
}

if (is.null(input_file) || is.null(output_file)) {
  stop("Usage: Rscript run_trimfill.R --input <in.json> --output <out.json>")
}

# ---- Read input JSON ----
in_data <- jsonlite::fromJSON(input_file)

yi <- in_data$yi
vi <- in_data$vi
method <- in_data$method
if (is.null(method)) method <- "REML"
side <- in_data$side
if (is.null(side)) side <- "right"

# ---- Run rma first ----
res <- rma(yi = yi, vi = vi, method = method)

# ---- Run trimfill ----
tf <- tryCatch(trimfill(res, side = side), error = function(e) NULL)

if (is.null(tf)) {
  # Fallback: try opposite side
  tf <- tryCatch(trimfill(res, side = "left"), error = function(e) NULL)
}

# ---- Build output list ----
out <- list(
  # Original model
  beta_original = as.numeric(res$beta),
  se_original = as.numeric(res$se),
  ci_low_original = as.numeric(res$ci.lb),
  ci_upp_original = as.numeric(res$ci.ub),
  k_original = as.numeric(res$k),
  tau2_original = as.numeric(res$tau2),
  I2_original = as.numeric(res$I2),
  pval_original = as.numeric(res$pval)
)

if (!is.null(tf)) {
  out$beta_trimfill <- as.numeric(tf$beta)
  out$se_trimfill <- as.numeric(tf$se)
  out$ci_low_trimfill <- as.numeric(tf$ci.lb)
  out$ci_upp_trimfill <- as.numeric(tf$ci.ub)
  out$k_trimfill <- as.numeric(tf$k)
  out$k_missing <- as.numeric(tf$k0)
  out$tau2_trimfill <- as.numeric(tf$tau2)
  out$I2_trimfill <- as.numeric(tf$I2)
  out$pval_trimfill <- as.numeric(tf$pval)
  out$side <- tf$side
  
  # Imputed study effects
  if (!is.null(tf$inf$yi)) {
    out$imputed_yi <- as.numeric(tf$inf$yi)
    out$imputed_vi <- as.numeric(tf$inf$vi)
  }
}

# ---- Write output JSON ----
jsonlite::write_json(out, output_file, auto_unbox = TRUE, pretty = TRUE)

cat(paste("Original: k =", out$k_original, 
          "g =", round(out$beta_original, 4),
          "95% CI: [", round(out$ci_low_original, 4), ",", round(out$ci_upp_original, 4), "]\n"))

if (!is.null(tf)) {
  cat(paste("Trim-fill: k =", out$k_trimfill, 
            "(imputed", out$k_missing, "studies)",
            "g =", round(out$beta_trimfill, 4),
            "95% CI: [", round(out$ci_low_trimfill, 4), ",", round(out$ci_upp_trimfill, 4), "]\n"))
}
