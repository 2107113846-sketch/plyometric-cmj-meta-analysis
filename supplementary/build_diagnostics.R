
library(metafor)
yi <- c(0.433, -0.362, -0.671, 1.410, 5.200, 0.432, -0.690, -0.397, -0.292, 0.194, 0.024, 2.940, 0.610, -0.561, -0.910)
vi <- c(0.257, 0.167, 0.222, 0.335, 0.183, 0.140, 0.167, 0.253, 0.287, 0.299, 0.177, 0.310, 0.221, 0.172, 0.172)
labels <- c("Palma-Munoz 2018","Chang 2025","Blazevich 2003","Byrne 2010","Sedano Campo 2009","Jlid 2019","Jlid 2020","Khlifa 2010","Laurent 2020","Potdevin 2011","Ramirez-Campillo 2018","Toumi 2004","Santos 2011","Vescovi 2008","Yanci 2017")
res <- rma(yi, vi, method="REML")

# Cook distance + studentized residuals
cook <- cooks.distance(res)
rstud <- rstudent(res)
df <- data.frame(
  Study = labels,
  Cooks_D = round(cook, 4),
  Studentized_Residual = round(rstud$z, 3),
  Weight_pct = round(weights(res) / sum(weights(res)) * 100, 1)
)
write.csv(df, "supplementary/outlier_diagnostics.csv", row.names=FALSE)
cat("Diagnostic table saved.\n")

# Leave-one-out
loo <- leave1out(res)
loo_df <- data.frame(
  Study_Removed = labels,
  g = round(loo$estimate, 3),
  CI_Lower = round(loo$ci.lb, 3),
  CI_Upper = round(loo$ci.ub, 3),
  I2_pct = round(loo$I2, 1)
)
write.csv(loo_df, "supplementary/leave_one_out.csv", row.names=FALSE)
cat("Leave-one-out saved.\n")
cat("Done.\n")

