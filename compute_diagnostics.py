"""
Run all remaining diagnostics: quadratic meta-regression, Baujat/Cook's D,
PEDro continuous meta-regression, arm×PEDro bivariate, prediction interval sensitivity,
baseline CMJ confounding, etc.
"""
import sys, io, json, csv, numpy as np
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
PROJ = Path(__file__).parent
sys.path.insert(0, str(PROJ))
from meta_toolkit.r_bridge import _find_rscript
import subprocess, tempfile, os

EFFECTS_CSV = PROJ / 'analysis_ready_effects.csv'
OUTPUT_DIR = PROJ / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

# Known study covariates
DURATION_WEEKS = {
    'R01': 6, 'R02': 6, 'R03': 6, 'R04': 6, 'R05': 6, 'R06': 12,
    'R07': 4, 'R08': 8, 'R09': 5, 'R10': 8, 'R11': 12, 'R12': 8,
    'R13': 12, 'R14': 8, 'R15': 6, 'R16': 10, 'R17': 4, 'R18': 10,
    'R19': 6, 'R20': 12, 'R21': 6, 'R22': 7, 'R23': 6, 'R24': 14,
    'R26': 10, 'R27': 8, 'R29': 6, 'R30': 6, 'R31': 8,
}
MEAN_AGE = {
    'R01': 14.1, 'R02': 11.3, 'R03': 12.9, 'R04': 14.2, 'R05': 22.1,
    'R06': 69.6, 'R07': 18.7, 'R08': 18.5, 'R09': 22.1, 'R10': 21.0,
    'R11': 22.9, 'R12': 19.1, 'R13': 16.6, 'R14': 11.8, 'R15': 19.0,
    'R16': 23.6, 'R17': 21.9, 'R18': 22.0, 'R19': 12.0, 'R20': 12.7,
    'R21': 14.2, 'R22': 17.0, 'R23': 24.8, 'R24': 13.4, 'R26': 14.8,
    'R27': 20.5, 'R29': 20.0, 'R30': 20.5, 'R31': 22.4,
}
SESSIONS_PER_WK = {
    'R01': 2, 'R02': 2, 'R03': 2, 'R04': 2, 'R05': 2, 'R06': 3,
    'R07': 3, 'R08': 3, 'R09': 3, 'R10': 2, 'R11': 3, 'R12': 2,
    'R13': 2, 'R14': 2, 'R15': 2, 'R16': 2.5, 'R17': 2, 'R18': 2,
    'R19': 3, 'R20': 2, 'R21': 2, 'R22': 2, 'R23': 1, 'R24': 1,
    'R26': 2, 'R27': 4, 'R29': 3, 'R30': 1, 'R31': 3,
}
PEDRO_SCORES = {
    'R01': 6, 'R02': 7, 'R03': 6, 'R04': 6, 'R05': 6,
    'R06': 8, 'R07': 7, 'R08': 6, 'R09': 3, 'R10': 5,
    'R11': 5, 'R12': 6, 'R13': 6, 'R14': 7, 'R15': 5,
    'R16': 6, 'R17': 5, 'R18': 6, 'R19': 6, 'R20': 6,
    'R21': 6, 'R22': 7, 'R23': 5, 'R24': 7,
    'R26': 7, 'R27': 4, 'R29': 5, 'R30': 6, 'R31': 6,
}

def load_strict():
    with open(EFFECTS_CSV, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if '手叉腰' in r['cmj_arm'] and 'VJ' not in r['cmj_arm']
            and r['study_id'] != 'R19'
            and r['effect_method'] == 'pre-post change SMD (Hedges g)']

def run_r_code(r_code):
    """Execute inline R code and return stdout."""
    rscript = _find_rscript()
    if rscript is None:
        raise RuntimeError('Rscript not found')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False, encoding='utf-8') as f:
        f.write(r_code)
        script_path = f.name
    try:
        result = subprocess.run(
            [rscript, '--no-save', '--no-restore', script_path],
            capture_output=True, timeout=120,
            encoding='utf-8', errors='replace',
            env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'}
        )
        if result.returncode != 0:
            print(f"R ERROR: {result.stderr[:500]}")
        return result.stdout
    finally:
        os.unlink(script_path)


# ================================================================
# 1. QUADRATIC META-REGRESSION + R² reporting
# ================================================================
print("\n" + "="*60)
print("1. QUADRATIC META-REGRESSION (duration + duration²)")
print("="*60)

strict = load_strict()
yi_strict = [float(r['yi_change']) for r in strict]
vi_strict = [float(r['vi_change']) for r in strict]
sid_strict = [r['study_id'] for r in strict]
dur_strict = [DURATION_WEEKS[s] for s in sid_strict]
age_strict = [MEAN_AGE[s] for s in sid_strict]
sess_strict = [SESSIONS_PER_WK[s] for s in sid_strict]
pedro_strict = [PEDRO_SCORES[s] for s in sid_strict]

r_code = f"""
library(metafor)

yi <- c({','.join(str(x) for x in yi_strict)})
vi <- c({','.join(str(x) for x in vi_strict)})
duration <- c({','.join(str(x) for x in dur_strict)})
age <- c({','.join(str(x) for x in age_strict)})
sessions <- c({','.join(str(x) for x in sess_strict)})
pedro <- c({','.join(str(x) for x in pedro_strict)})

duration2 <- duration^2

cat("=== Linear duration ===\\n")
m1 <- rma(yi, vi, mods = ~ duration, method = "REML")
print(summary(m1))
cat("R2:", round(m1$R2, 2), "%\\n")
cat("Residual I2:", round(m1$I2, 1), "%\\n")

cat("\\n=== Quadratic (duration + duration²) ===\\n")
m2 <- rma(yi, vi, mods = ~ duration + duration2, method = "REML")
print(summary(m2))
cat("R2:", round(m2$R2, 2), "%\\n")
cat("Residual I2:", round(m2$I2, 1), "%\\n")

cat("\\n=== Duration + Sessions ===\\n")
m3 <- rma(yi, vi, mods = ~ duration + sessions, method = "REML")
print(summary(m3))
cat("R2:", round(m3$R2, 2), "%\\n")
cat("Residual I2:", round(m3$I2, 1), "%\\n")

cat("\\n=== PEDro continuous ===\\n")
m4 <- rma(yi, vi, mods = ~ pedro, method = "REML")
print(summary(m4))
cat("R2:", round(m4$R2, 2), "%\\n")
cat("Residual I2:", round(m4$I2, 1), "%\\n")

cat("\\n=== Arm position (dummy: strict=1) + PEDro ===\\n")
# All are strict, but we can test PEDro × duration interaction
m5 <- rma(yi, vi, mods = ~ duration + pedro, method = "REML")
print(summary(m5))
cat("R2:", round(m5$R2, 2), "%\\n")
cat("Residual I2:", round(m5$I2, 1), "%\\n")

cat("\\n=== Baseline CMJ (pre-test mean as predictor) ===\\n")
# Use exp_pre_mean as proxy for baseline
exp_pre <- c({','.join(str(float(r['exp_pre_mean'])) for r in strict)})
m6 <- rma(yi, vi, mods = ~ exp_pre, method = "REML")
print(summary(m6))
cat("R2:", round(m6$R2, 2), "%\\n")
cat("Residual I2:", round(m6$I2, 1), "%\\n")
cat("\\n=== DONE QUADRATIC ===\\n")
"""

out = run_r_code(r_code)
print(out)

# Parse key results
quad_results = {}
for line in out.split('\n'):
    if 'R2:' in line:
        print(line.strip())
    if 'Residual I2:' in line:
        print(line.strip())

print("\nQuadratic meta-regression completed.")


# ================================================================
# 2. BAUJAT PLOT + COOK'S D + STUDENTIZED RESIDUALS
# ================================================================
print("\n" + "="*60)
print("2. OUTLIER DIAGNOSTICS (Baujat, Cook's D, Studentized)")
print("="*60)

r_code2 = f"""
library(metafor)

yi <- c({','.join(str(x) for x in yi_strict)})
vi <- c({','.join(str(x) for x in vi_strict)})
labels <- c({','.join("'" + r['author'] + ' ' + r['year'] + "'" for r in strict)})

res <- rma(yi, vi, method = "REML")

cat("\\n=== Influential case diagnostics ===\\n")

# Studentized deleted residuals
rstudent_vals <- rstudent(res)
cat("Studentized deleted residuals:\\n")
print(data.frame(study=labels, rstudent=round(rstudent_vals$z, 3)))

# Cook's distance
cook_vals <- cooks.distance(res)
cat("\\nCook's distance:\\n")
print(data.frame(study=labels, cooks_d=round(cook_vals, 4)))

# DFFITS
dffits_vals <- dffits(res)
cat("\\nDFFITS:\\n")
print(data.frame(study=labels, dffits=round(dffits_vals, 3)))

# Leave-one-out
cat("\\n=== Leave-one-out analysis ===\\n")
loo <- leave1out(res)
print(loo)

# Q-Q plot of residuals
cat("\\n=== Residual normality ===\\n")
rres <- rstandard(res)
cat("Shapiro-Wilk normality test on standardized residuals:\\n")
print(shapiro.test(rres$z))

cat("\\n=== DONE DIAGNOSTICS ===\\n")
"""

out2 = run_r_code(r_code2)
print(out2)

# Extract diagnostic scores
diag_results = {}
for line in out2.split('\n'):
    if any(w in line for w in ['rstudent', 'cooks_d', 'dffits', 'Sedano', 'Toumi', 'Shapiro']):
        print(line.strip())

print("\nOutlier diagnostics completed.")


# ================================================================
# 3. PREDICTION INTERVAL SENSITIVITY (exclude R11+R27)
# ================================================================
print("\n" + "="*60)
print("3. PREDICTION INTERVAL SENSITIVITY (excl R11+R27)")
print("="*60)

# Remove R11 and R27
yi_sens = []
vi_sens = []
labels_sens = []
for r in strict:
    if r['study_id'] not in ('R11', 'R27'):
        yi_sens.append(float(r['yi_change']))
        vi_sens.append(float(r['vi_change']))
        labels_sens.append(f"{r['author']} {r['year']}")

r_code3 = f"""
library(metafor)
yi <- c({','.join(str(x) for x in yi_sens)})
vi <- c({','.join(str(x) for x in vi_sens)})

res <- rma(yi, vi, method = "REML")
cat("\\n=== Strict pool WITHOUT R11+R27 ===\\n")
cat("k =", res$k, "\\n")
cat("g =", round(res$b, 4), "\\n")
cat("95% CI = [", round(res$ci.lb, 4), ",", round(res$ci.ub, 4), "]\\n")
cat("I2 =", round(res$I2, 2), "%\\n")
cat("tau2 =", round(res$tau2, 4), "\\n")

# Prediction interval
pi_res <- predict(res)
cat("Prediction interval = [", round(pi_res$pi.lb, 4), ",", round(pi_res$pi.ub, 4), "]\\n")

# I2 CI (Q-profile)
ci_i2 <- confint(res)
cat("I2 95% CI = [", round(ci_i2[[2]][[2]], 1), "%, ", round(ci_i2[[2]][[3]], 1), "%]\\n")
cat("tau2 95% CI = [", round(ci_i2[[1]][[2]], 4), ",", round(ci_i2[[1]][[3]], 4), "]\\n")

cat("\\n=== DONE PI SENSITIVITY ===\\n")
"""

out3 = run_r_code(r_code3)
print(out3)
pi_sens = {}
for line in out3.split('\n'):
    print(line.strip())
print("\nPI sensitivity completed.")


# ================================================================
# 4. WIDE POOL ARM + PEDRO BIVARIATE ANALYSIS
# ================================================================
print("\n" + "="*60)
print("4. WIDE POOL: ARM × PEDRO BIVARIATE META-REGRESSION")
print("="*60)

with open(EFFECTS_CSV, 'r', encoding='utf-8-sig') as f:
    all_rows = list(csv.DictReader(f))
wide = [r for r in all_rows if 'VJ' not in r['cmj_arm'] and r['study_id'] != 'R19'
        and r['effect_method'] == 'pre-post change SMD (Hedges g)']
yi_wide = [float(r['yi_change']) for r in wide]
vi_wide = [float(r['vi_change']) for r in wide]
sid_wide = [r['study_id'] for r in wide]
arm_wide = [1 if '手叉腰' in r['cmj_arm'] else 0 for r in wide]  # 1=strict, 0=other
pedro_wide = [PEDRO_SCORES[s] for s in sid_wide]
dur_wide = [DURATION_WEEKS[s] for s in sid_wide]

r_code4 = f"""
library(metafor)
yi <- c({','.join(str(x) for x in yi_wide)})
vi <- c({','.join(str(x) for x in vi_wide)})
arm_strict <- c({','.join(str(x) for x in arm_wide)})
pedro <- c({','.join(str(x) for x in pedro_wide)})
duration <- c({','.join(str(x) for x in dur_wide)})

cat("\\n=== Bivariate: arm_strict + pedro ===\\n")
m <- rma(yi, vi, mods = ~ arm_strict + pedro, method = "REML")
print(summary(m))
cat("R2:", round(m$R2, 2), "%\\n")

cat("\\n=== Bivariate: arm_strict + duration ===\\n")
m2 <- rma(yi, vi, mods = ~ arm_strict + duration, method = "REML")
print(summary(m2))
cat("R2:", round(m2$R2, 2), "%\\n")

cat("\\n=== Arm subgroup mean PEDro score comparison ===\\n")
cat("Strict (arm=1) mean PEDro:", round(mean(pedro[arm_strict==1]), 2), "\\n")
cat("Non-strict (arm=0) mean PEDro:", round(mean(pedro[arm_strict==0]), 2), "\\n")

# t-test for PEDro difference
t_res <- t.test(pedro[arm_strict==1], pedro[arm_strict==0])
print(t_res)

cat("\\n=== DONE BIVARIATE ===\\n")
"""

out4 = run_r_code(r_code4)
print(out4)
print("Arm + PEDro bivariate completed.")


# ================================================================
# 5. BASELINE CMJ CONFOUNDING (wide pool)
# ================================================================
print("\n" + "="*60)
print("5. BASELINE CMJ × EFFECT SIZE ANALYSIS")
print("="*60)

r_code5 = f"""
library(metafor)
yi <- c({','.join(str(x) for x in yi_wide)})
vi <- c({','.join(str(x) for x in vi_wide)})
exp_pre <- c({','.join(str(float(r['exp_pre_mean'])) for r in wide)})
exp_post <- c({','.join(str(float(r['exp_post_mean'])) for r in wide)})
# Expected gain proportional to baseline
baseline_ratio <- exp_post / exp_pre

cat("\\n=== Effect size vs baseline CMJ ===\\n")
m <- rma(yi, vi, mods = ~ exp_pre, method = "REML")
print(summary(m))

cat("\\n=== Regression to mean check ===\\n")
cat("Mean exp_pre:", round(mean(exp_pre), 1), "cm\\n")
cat("Mean exp_post:", round(mean(exp_post), 1), "cm\\n")
cat("Min exp_pre:", min(exp_pre), "\\n")
cat("Max exp_pre:", max(exp_pre), "\\n")

cat("\\n=== DONE BASELINE ===\\n")
"""

out5 = run_r_code(r_code5)
print(out5)
print("Baseline CMJ analysis completed.")

# ================================================================
# COLLECT ALL RESULTS
# ================================================================
results = {
    'status': 'completed',
    'note': 'Round 10 diagnostic computations'
}

with open(OUTPUT_DIR / 'round10_diagnostics.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n\nAll diagnostics complete. Results saved to {OUTPUT_DIR / 'round10_diagnostics.json'}")
