# run_meta.R - Meta analysis worker script
# Called by Python r_bridge.py via subprocess
# Reads JSON input, runs metafor, writes JSON output + plots

library(metafor)

# ---- Parse command line args ----
args <- commandArgs(trailingOnly = TRUE)
input_file <- NULL
output_file <- NULL
plot_file <- NULL

for (i in seq_along(args)) {
  if (args[i] == "--input" && i < length(args)) {
    input_file <- args[i + 1]
  } else if (args[i] == "--output" && i < length(args)) {
    output_file <- args[i + 1]
  } else if (args[i] == "--plot" && i < length(args)) {
    plot_file <- args[i + 1]
  }
}

if (is.null(input_file) || is.null(output_file)) {
  stop("Usage: Rscript run_meta.R --input <in.json> --output <out.json> [--plot <file.png>]")
}

# ---- Read input JSON ----
in_data <- jsonlite::fromJSON(input_file)

yi <- in_data$yi
vi <- in_data$vi
method <- in_data$method
if (is.null(method)) method <- "REML"
labels <- in_data$labels
if (is.null(labels)) labels <- paste("Study", seq_along(yi))

# ---- Run rma ----
res <- rma(yi = yi, vi = vi, method = method)

# ---- Build output list ----
out <- list(
  beta = as.numeric(res$beta),
  se = as.numeric(res$se),
  ci_low = as.numeric(res$ci.lb),
  ci_upp = as.numeric(res$ci.ub),
  z = as.numeric(res$zval),
  pval = as.numeric(res$pval),
  tau2 = as.numeric(res$tau2),
  I2 = as.numeric(res$I2),
  H2 = as.numeric(res$H2),
  Q = as.numeric(res$QE),
  Q_pval = as.numeric(res$QEp),
  k = as.numeric(res$k),
  method = method,
  model = paste("Random-effects (", method, ")", sep = "")
)

# Prediction interval
if (res$k > 2) {
  pred <- tryCatch(predict(res), error = function(e) NULL)
  if (!is.null(pred)) {
    out$pred_low <- as.numeric(pred$cr.lb)
    out$pred_upp <- as.numeric(pred$cr.ub)
  }
}

# I² and tau² confidence intervals via profile likelihood (Q-profile method)
if (res$k >= 3) {
  ci_res <- tryCatch(confint(res), error = function(e) NULL)
  if (!is.null(ci_res)) {
    # tau2 CI
    out$tau2_ci_low <- as.numeric(ci_res$random[1, 2])
    out$tau2_ci_upp <- as.numeric(ci_res$random[1, 3])
    # I2 CI
    out$I2_ci_low <- as.numeric(ci_res$random[3, 2])
    out$I2_ci_upp <- as.numeric(ci_res$random[3, 3])
  }
}

# Egger test
if (res$k >= 3) {
  egger <- tryCatch(regtest(res), error = function(e) NULL)
  if (!is.null(egger)) {
    out$egger_intercept <- as.numeric(egger$est[1])
    out$egger_pval <- as.numeric(egger$pval)
  }
}

# Study-level results
out$study_effects <- yi
out$study_se <- sqrt(vi)
out$study_ci_low <- yi - 1.96 * sqrt(vi)
out$study_ci_upp <- yi + 1.96 * sqrt(vi)
out$study_weights <- as.numeric(weights(res))
out$study_labels <- labels

# ---- Write output JSON ----
jsonlite::write_json(out, output_file, auto_unbox = TRUE, pretty = TRUE)

# ---- Generate forest plot if requested ----
if (!is.null(plot_file)) {
  png(plot_file, width = 10, height = max(3, res$k * 0.4 + 1.5),
      units = "in", res = 300, bg = "white")
  forest(res, slab = labels, header = TRUE,
         main = "Forest Plot (metafor)")
  dev.off()
  cat(paste("Forest plot saved to:", plot_file, "\n"))
}

cat(paste("Results saved to:", output_file, "\n"))
cat(paste("Pooled ES:", round(out$beta, 4),
          "95% CI: [", round(out$ci_low, 4), ",", round(out$ci_upp, 4), "]",
          "I2:", round(out$I2, 1), "%\n"))
