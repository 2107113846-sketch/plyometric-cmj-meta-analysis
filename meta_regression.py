"""
Meta回归分析: 检验连续/分类调节变量对异质性的解释力
通过临时R脚本调用metafor::rma(mods=~x)
"""
import csv, sys, json, tempfile, subprocess, os
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from meta_toolkit.r_bridge import _find_rscript


def load_effects(csv_path):
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            studies.append({
                'study_id': row['study_id'],
                'author': row['author'], 'year': int(float(row['year'])) if row['year'] else 2015,
                'exp_n': int(float(row['exp_n'])),
                'ctrl_n': int(float(row['ctrl_n'])),
                'yi': float(row['yi_change']),
                'vi': float(row['vi_change']),
                'sei': float(row['sei_change']),
                'data_note': row.get('data_note', ''),
            })
    return studies


def is_strict(s):
    return '✅' in s.get('data_note', '')


# Manual coding of moderators based on extraction tables
# Duration in weeks
DURATION_WEEKS = {
    'R01': 6, 'R02': 6, 'R03': 6, 'R04': 6, 'R05': 6, 'R06': 12,
    'R07': 4, 'R08': 8, 'R09': 5, 'R10': 8, 'R11': 12, 'R12': 8,
    'R13': 12, 'R14': 8, 'R15': 6, 'R16': 10, 'R17': 4, 'R18': 10,
    'R19': 6, 'R20': 12, 'R21': 6, 'R22': 7, 'R23': 6, 'R24': 14,
    'R26': 10, 'R27': 8, 'R29': 6, 'R30': 6, 'R31': 8,
}

# Mean age (approximate)
MEAN_AGE = {
    'R01': 14.1, 'R02': 11.3, 'R03': 12.9, 'R04': 14.2, 'R05': 22.1,
    'R06': 69.6, 'R07': 18.7, 'R08': 18.5, 'R09': 22.1, 'R10': 21.0,
    'R11': 22.9, 'R12': 19.1, 'R13': 16.6, 'R14': 11.8, 'R15': 19.0,
    'R16': 23.6, 'R17': 21.9, 'R18': 22.0, 'R19': 12.0, 'R20': 12.7,
    'R21': 14.2, 'R22': 17.0, 'R23': 24.8, 'R24': 13.4, 'R26': 14.8,
    'R27': 20.5, 'R29': 20.0, 'R30': 20.5, 'R31': 22.4,
}

# Sessions per week
SESSIONS_PER_WK = {
    'R01': 2, 'R02': 2, 'R03': 2, 'R04': 2, 'R05': 2, 'R06': 3,
    'R07': 3, 'R08': 3, 'R09': 3, 'R10': 2, 'R11': 3, 'R12': 2,
    'R13': 2, 'R14': 2, 'R15': 2, 'R16': 2.5, 'R17': 2, 'R18': 2,
    'R19': 3, 'R20': 2, 'R21': 2, 'R22': 2, 'R23': 1, 'R24': 1,
    'R26': 2, 'R27': 4, 'R29': 3, 'R30': 1, 'R31': 3,
}


def run_meta_regression_r(yi, vi, moderators, mod_names, method='REML'):
    """
    Run meta-regression via R/metafor: rma(yi, vi, mods=~x1+x2, method=method)
    Returns a dict with results for each moderator.
    """
    rscript = _find_rscript()
    if rscript is None:
        raise RuntimeError('Rscript not found')

    yi_arr = np.asarray(yi, dtype=float)
    vi_arr = np.asarray(vi, dtype=float)

    results = {}

    for mod_name, mod_values in zip(mod_names, moderators):
        mod_arr = np.asarray(mod_values, dtype=float)

        # Build R script for this moderator
        r_code = f'''
library(metafor)

yi <- c({','.join(str(x) for x in yi_arr)})
vi <- c({','.join(str(x) for x in vi_arr)})
x <- c({','.join(str(x) for x in mod_arr)})

# Meta-regression
res <- rma(yi, vi, mods = ~ x, method = "{method}")

# Output as JSON
out <- list(
  beta = as.numeric(res$b[1]),
  se_beta = as.numeric(res$se[1]),
  moderator_coef = as.numeric(res$b[2]),
  moderator_se = as.numeric(res$se[2]),
  moderator_z = as.numeric(res$zval[2]),
  moderator_p = as.numeric(res$pval[2]),
  tau2 = as.numeric(res$tau2),
  I2 = as.numeric(res$I2),
  R2 = as.numeric(res$R2),
  QE = as.numeric(res$QE),
  QE_df = as.numeric(res$QEdf),
  QE_p = as.numeric(res$QEp),
  QM = as.numeric(res$QM),
  QM_df = 1,
  QM_p = as.numeric(res$QMp),
  k = as.numeric(res$k),
  intrcpt = as.numeric(res$b[1,1]),
  slope = as.numeric(res$b[2,1])
)
cat(jsonlite::toJSON(out, auto_unbox = TRUE))
'''

        # Write temp R script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R',
                                         delete=False, encoding='utf-8') as f:
            f.write(r_code)
            r_script_path = f.name

        try:
            result = subprocess.run(
                [rscript, '--no-save', '--no-restore', r_script_path],
                capture_output=True, text=True, timeout=120,
                encoding='utf-8', errors='replace',
                env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'}
            )

            if result.returncode == 0 and result.stdout.strip():
                # Parse JSON output
                out = json.loads(result.stdout.strip())
                out['moderator'] = mod_name
                results[mod_name] = out
            else:
                err = result.stderr or result.stdout or 'Unknown error'
                print(f"  [ERROR] {mod_name}: {err[:200]}")
                results[mod_name] = None
        finally:
            try:
                os.unlink(r_script_path)
            except OSError:
                pass

    return results


def run_baseline_no_mod(yi, vi, method='REML'):
    """Run intercept-only model for R² reference."""
    rscript = _find_rscript()
    yi_arr = np.asarray(yi, dtype=float)
    vi_arr = np.asarray(vi, dtype=float)

    r_code = f'''
library(metafor)
yi <- c({','.join(str(x) for x in yi_arr)})
vi <- c({','.join(str(x) for x in vi_arr)})
res <- rma(yi, vi, method = "{method}")
out <- list(tau2 = as.numeric(res$tau2), I2 = as.numeric(res$I2), k = as.numeric(res$k))
cat(jsonlite::toJSON(out, auto_unbox = TRUE))
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.R',
                                     delete=False, encoding='utf-8') as f:
        f.write(r_code)
        r_script_path = f.name
    try:
        result = subprocess.run(
            [rscript, '--no-save', '--no-restore', r_script_path],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
            env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'})
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
    finally:
        try: os.unlink(r_script_path)
        except OSError: pass
    return None


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    all_studies = load_effects(csv_path)
    # Use wide pool (all CMJ) for meta-regression (more power)
    pool = [s for s in all_studies if 'VJ' not in s.get('data_note', '')]

    yi = [s['yi'] for s in pool]
    vi = [s['vi'] for s in pool]
    sei = [s['sei'] for s in pool]
    n_total = [s['exp_n'] + s['ctrl_n'] for s in pool]
    years = [s['year'] for s in pool]

    print(f"\n{'='*65}")
    print(f"  Meta-Regression Analysis ({len(pool)} CMJ studies)")
    print(f"{'='*65}")

    # Baseline model
    bl = run_baseline_no_mod(yi, vi)
    if bl:
        print(f"\n  Baseline (intercept-only): tau2={bl['tau2']:.4f}, I2={bl['I2']:.1f}%")

    # Build moderator vectors
    mod_duration = [DURATION_WEEKS.get(s['study_id'], 8) for s in pool]
    mod_age = [MEAN_AGE.get(s['study_id'], 20) for s in pool]
    mod_n = n_total
    mod_year = years
    mod_sessions = [SESSIONS_PER_WK.get(s['study_id'], 2) for s in pool]

    # Categorical: arm position
    arm_map = {'Strict hands-on-hips': 1, 'Arm-unclear': 2, 'CMJA-arm-swing': 3}
    mod_arm = []
    for s in pool:
        note = s['data_note']
        if '✅' in note:
            mod_arm.append(1)
        elif 'CMJA' in note or '带臂' in note:
            mod_arm.append(3)
        else:
            mod_arm.append(2)

    # Run all meta-regressions
    moderator_list = [mod_duration, mod_age, mod_n, mod_sessions, mod_year, mod_arm]
    mod_names = [
        'Duration (weeks)',
        'Mean Age (years)',
        'Total Sample Size (n)',
        'Sessions per Week',
        'Publication Year',
        'Arm Position (1=strict,2=unclear,3=CMJA)',
    ]

    results = run_meta_regression_r(yi, vi, moderator_list, mod_names)

    # Print results
    print(f"\n  {'Moderator':<30} {'Slope':>8} {'SE':>6} {'z':>7} {'p':>7} {'R2':>7} {'tau2':>8} {'I2':>5}")
    print(f"  {'-'*75}")

    for mod_name, r in results.items():
        if r is None:
            print(f"  {mod_name:<30} {'-- FAILED --':>30}")
            continue
        slope = r['moderator_coef']
        se_slope = r['moderator_se']
        z = r['moderator_z']
        p = r['moderator_p']
        r2 = r.get('R2', 0) or 0
        tau2 = r['tau2']
        i2 = r['I2']
        sig = ' **' if p < 0.01 else (' *' if p < 0.05 else (' .' if p < 0.10 else ''))
        print(f"  {mod_name:<30} {slope:+.4f}  {se_slope:.4f}  {z:+.2f}  {p:.4f}{sig}  {r2:.1%}  {tau2:.4f}  {i2:.0f}%")

    # Focus: Duration x I2 relationship
    print(f"\n{'='*65}")
    print(f"  Key Finding: Duration as Moderator")
    print(f"{'='*65}")
    dur_result = results.get('Duration (weeks)')
    if dur_result:
        print(f"\n  Each additional week of intervention:")
        print(f"    Slope = {dur_result['moderator_coef']:+.4f} (SE={dur_result['moderator_se']:.4f})")
        print(f"    z = {dur_result['moderator_z']:.2f}, p = {dur_result['moderator_p']:.4f}")
        print(f"    R2 = {dur_result['R2']:.1%} (variance explained by duration)")
        print(f"    Residual I2 = {dur_result['I2']:.0f}%")
        if dur_result['moderator_p'] < 0.05:
            print(f"    >> Duration is a SIGNIFICANT moderator <<")
        else:
            print(f"    >> Duration is NOT a significant moderator <<")

        # Predicted effect by duration
        intrcpt = dur_result['intrcpt']
        slope = dur_result['slope']
        print(f"\n  Predicted SMD by duration:")
        for wks in [4, 6, 8, 10, 12]:
            pred_g = intrcpt + slope * wks
            print(f"    {wks} weeks: g = {pred_g:+.3f}")

    # Multi-variable model: duration + arm position
    print(f"\n{'='*65}")
    print(f"  Multi-Variable Model: Duration + Arm Position")
    print(f"{'='*65}")

    yi_arr = np.asarray(yi, dtype=float)
    vi_arr = np.asarray(vi, dtype=float)
    dur_arr = np.asarray(mod_duration, dtype=float)
    arm_arr = np.asarray(mod_arm, dtype=float)

    rscript = _find_rscript()
    r_code = f'''
library(metafor)
yi <- c({','.join(str(x) for x in yi_arr)})
vi <- c({','.join(str(x) for x in vi_arr)})
dur <- c({','.join(str(x) for x in dur_arr)})
arm <- c({','.join(str(x) for x in arm_arr)})

res <- rma(yi, vi, mods = ~ dur + arm, method = "REML")
out <- list(
  k = as.numeric(res$k),
  R2 = as.numeric(res$R2),
  tau2 = as.numeric(res$tau2),
  I2 = as.numeric(res$I2),
  QM = as.numeric(res$QM),
  QM_p = as.numeric(res$QMp),
  b_dur = as.numeric(res$b[2,1]),
  se_dur = as.numeric(res$se[2]),
  p_dur = as.numeric(res$pval[2]),
  b_arm = as.numeric(res$b[3,1]),
  se_arm = as.numeric(res$se[3]),
  p_arm = as.numeric(res$pval[3])
)
cat(jsonlite::toJSON(out, auto_unbox = TRUE))
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.R',
                                     delete=False, encoding='utf-8') as f:
        f.write(r_code)
        r_mv_path = f.name

    try:
        result = subprocess.run(
            [rscript, '--no-save', '--no-restore', r_mv_path],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
            env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'})
        if result.returncode == 0 and result.stdout.strip():
            mv = json.loads(result.stdout.strip())
            print(f"\n  Multi-variable model (Duration + Arm):")
            print(f"    R2 = {mv['R2']:.1%}, Residual I2 = {mv['I2']:.0f}%")
            print(f"    QM(df=2) = {mv['QM']:.2f}, p = {mv['QM_p']:.4f}")
            print(f"    Duration: b = {mv['b_dur']:+.4f}, p = {mv['p_dur']:.4f}")
            print(f"    Arm Pos:  b = {mv['b_arm']:+.4f}, p = {mv['p_arm']:.4f}")
            if mv['p_dur'] < 0.05:
                print(f"    >> Duration remains significant after controlling for arm <<")
    finally:
        try: os.unlink(r_mv_path)
        except OSError: pass


if __name__ == "__main__":
    main()
