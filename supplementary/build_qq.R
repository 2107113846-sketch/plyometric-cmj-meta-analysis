
library(metafor)
yi <- c(0.433, -0.362, -0.671, 1.410, 5.200, 0.432, -0.690, -0.397, -0.292, 0.194, 0.024, 2.940, 0.610, -0.561, -0.910)
vi <- c(0.257, 0.167, 0.222, 0.335, 0.183, 0.140, 0.167, 0.253, 0.287, 0.299, 0.177, 0.310, 0.221, 0.172, 0.172)
res <- rma(yi, vi, method="REML")
# QQ plot
png("supplementary/qq_plot_residuals.png", width=1600, height=1400, res=200)
rstand <- rstandard(res)
qqnorm(rstand$z, main="Q-Q Plot — Standardized Residuals (Strict Pool, k=15)", xlab="Theoretical Quantiles", ylab="Sample Quantiles")
qqline(rstand$z, col="red", lwd=2)
dev.off()
cat("QQ plot done\n")

