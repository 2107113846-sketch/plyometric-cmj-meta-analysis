"""
Run supplementary statistical analyses:
- Begg's rank correlation test
- Peters' regression (multiple predictors)
- Meta-regression R² and residual I²
"""
import csv, json, tempfile, subprocess, os, sys, numpy as np
sys.path.insert(0, '.')
from meta_toolkit.r_bridge import _find_rscript


def load_effects(csv_path):
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            studies.append({
                'study_id': row['study_id'],
                'author': row['author'], 'year': row['year'],
                'exp_n': int(float(row['exp_n'])),
                'ctrl_n': int(float(row['ctrl_n'])),
                'yi': float(row['yi_change']),
                'vi': float(row['vi_change']),
                'sei': float(row['sei_change']),
                'data_note': row.get('data_note', ''),
            })
    return studies


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


def run_r_script(r_code):
    """Execute an R script and return parsed JSON output."""
    rscript = _find_rscript()
    if rscript is None:
        raise RuntimeError('Rscript not found')
    with tempfile.NamedTemporaryFile(mode='w', suffix='.R',
                                     delete=False, encoding='utf-8') as f:
        f.write(r_code)
        r_path = f.name
    try:
        result = subprocess.run(
            [rscript, '--no-save', '--no-restore', r_path],
            capture_output=True, text=True, timeout=120,
            encoding='utf-8', errors='replace',
            env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'})
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            print(f'  ERROR stderr: {result.stderr[:400]}')
            print(f'  ERROR stdout: {result.stdout[:400]}')
            return None
    finally:
        try:
            os.unlink(r_path)
        except OSError:
            pass


def main():
    csv_path = 'analysis_ready_effects.csv'
    all_studies = load_effects(csv_path)
    strict = [s for s in all_studies if '✅' in s.get('data_note', '')]
    wide = [s for s in all_studies if 'VJ' not in s.get('data_note', '')]

    results = {}

    # ============================================================
    # Part 1: Begg & Peters tests for strict and wide pools
    # ============================================================
    for name, pool in [('strict', strict), ('wide', wide)]:
        print(f'\n{"="*60}')
        print(f'  Begg & Peters: {name} ({len(pool)} studies)')
        print(f'{"="*60}')

        yi_arr = np.array([s['yi'] for s in pool])
        vi_arr = np.array([s['vi'] for s in pool])
        sei_arr = np.array([s['sei'] for s in pool])

        yi_str = ','.join(str(float(x)) for x in yi_arr)
        vi_str = ','.join(str(float(x)) for x in vi_arr)
        sei_str = ','.join(str(float(x)) for x in sei_arr)

        r_code = f'''
library(metafor)
yi <- c({yi_str})
vi <- c({vi_str})
sei <- c({sei_str})

res <- rma(yi, vi, method='REML')

# Begg's rank correlation test
bt <- ranktest(res)
begg_tau <- as.numeric(bt$tau)
begg_p <- as.numeric(bt$pval)

# Peters' regression using sei as predictor
pt <- regtest(res, predictor='sei')
pt_int <- as.numeric(pt$est[1])
pt_p <- as.numeric(pt$pval[1])

# Egger test (standard SE predictor, intercept focus)
et <- regtest(res, predictor='sei', model='lm')
et_int <- as.numeric(et$est[1])
et_p <- as.numeric(et$pval[1])

out <- list(
  begg_tau = begg_tau,
  begg_p = begg_p,
  peters_int = pt_int,
  peters_p = pt_p,
  egger_lm_int = et_int,
  egger_lm_p = et_p
)
cat(jsonlite::toJSON(out, auto_unbox = TRUE))
'''

        bp = run_r_script(r_code)
        if bp:
            results[f'{name}_begg_peters'] = bp
            print(f'  Begg rank test:      tau={bp["begg_tau"]:.4f}, p={bp["begg_p"]:.4f}')
            print(f'  Peters test (regtest): int={bp["peters_int"]:.4f}, p={bp["peters_p"]:.4f}')
            print(f'  Egger LM:             int={bp["egger_lm_int"]:.4f}, p={bp["egger_lm_p"]:.4f}')
        else:
            results[f'{name}_begg_peters'] = None

    # ============================================================
    # Part 2: Meta-regression R² and residual I² (wide pool)
    # ============================================================
    yi_w = np.array([s['yi'] for s in wide])
    vi_w = np.array([s['vi'] for s in wide])
    dur_w = np.array([DURATION_WEEKS.get(s['study_id'], 8) for s in wide])
    age_w = np.array([MEAN_AGE.get(s['study_id'], 20) for s in wide])
    sess_w = np.array([SESSIONS_PER_WK.get(s['study_id'], 2) for s in wide])
    # arm: 1=strict, 2=unclear, 3=CMJA
    arm_w = np.array([
        1 if '✅' in s.get('data_note', '') else (3 if 'CMJA' in s.get('data_note', '') or '带臂' in s.get('data_note', '') else 2)
        for s in wide
    ])

    yi_w_str = ','.join(str(float(x)) for x in yi_w)
    vi_w_str = ','.join(str(float(x)) for x in vi_w)
    dur_str = ','.join(str(float(x)) for x in dur_w)
    age_str = ','.join(str(float(x)) for x in age_w)
    sess_str = ','.join(str(float(x)) for x in sess_w)
    arm_str = ','.join(str(int(x)) for x in arm_w)

    r_code = f'''
library(metafor)
yi <- c({yi_w_str})
vi <- c({vi_w_str})
dur <- c({dur_str})
age <- c({age_str})
sess <- c({sess_str})
arm <- c({arm_str})

# Baseline
res0 <- rma(yi, vi, method='REML')
tau2_0 <- res0$tau2
I2_0 <- res0$I2

# Duration only
res_dur <- rma(yi, vi, mods=~dur, method='REML')
# Sessions only
res_sess <- rma(yi, vi, mods=~sess, method='REML')
# Age only
res_age <- rma(yi, vi, mods=~age, method='REML')
# Duration + sessions
res_ds <- rma(yi, vi, mods=~dur+sess, method='REML')
# Duration + arm
res_da <- rma(yi, vi, mods=~dur+arm, method='REML')

out <- list(
  baseline = list(tau2=as.numeric(tau2_0), I2=as.numeric(I2_0), k=as.numeric(res0$k)),
  duration = list(
    b=as.numeric(res_dur$b[2]), se=as.numeric(res_dur$se[2]),
    z=as.numeric(res_dur$zval[2]), p=as.numeric(res_dur$pval[2]),
    R2=as.numeric(res_dur$R2), tau2_resid=as.numeric(res_dur$tau2),
    I2_resid=as.numeric(res_dur$I2), QE=as.numeric(res_dur$QE),
    QE_p=as.numeric(res_dur$QEp), QM=as.numeric(res_dur$QM),
    QM_p=as.numeric(res_dur$QMp)
  ),
  sessions = list(
    b=as.numeric(res_sess$b[2]), se=as.numeric(res_sess$se[2]),
    z=as.numeric(res_sess$zval[2]), p=as.numeric(res_sess$pval[2]),
    R2=as.numeric(res_sess$R2), tau2_resid=as.numeric(res_sess$tau2),
    I2_resid=as.numeric(res_sess$I2)
  ),
  age = list(
    b=as.numeric(res_age$b[2]), se=as.numeric(res_age$se[2]),
    z=as.numeric(res_age$zval[2]), p=as.numeric(res_age$pval[2]),
    R2=as.numeric(res_age$R2), tau2_resid=as.numeric(res_age$tau2),
    I2_resid=as.numeric(res_age$I2)
  ),
  dur_sess = list(
    R2=as.numeric(res_ds$R2), tau2_resid=as.numeric(res_ds$tau2),
    I2_resid=as.numeric(res_ds$I2),
    b_dur=as.numeric(res_ds$b[2]), p_dur=as.numeric(res_ds$pval[2]),
    b_sess=as.numeric(res_ds$b[3]), p_sess=as.numeric(res_ds$pval[3])
  ),
  dur_arm = list(
    R2=as.numeric(res_da$R2), tau2_resid=as.numeric(res_da$tau2),
    I2_resid=as.numeric(res_da$I2),
    b_dur=as.numeric(res_da$b[2]), p_dur=as.numeric(res_da$pval[2]),
    b_arm=as.numeric(res_da$b[3]), p_arm=as.numeric(res_da$pval[3])
  )
)
cat(jsonlite::toJSON(out, auto_unbox = TRUE))
'''
    print(f'\n{"="*60}')
    print(f'  Meta-Regression R2 (wide pool, {len(wide)} studies)')
    print(f'{"="*60}')
    mr = run_r_script(r_code)
    if mr:
        results['meta_reg_r2'] = mr
        bl = mr['baseline']
        print(f'  Baseline: tau2={bl["tau2"]:.4f}, I2={bl["I2"]:.1f}%')
        for mod in ['duration', 'sessions', 'age']:
            d = mr[mod]
            print(f'  {mod.capitalize():<12}: b={d["b"]:+.4f}, p={d["p"]:.4f}, R2={d["R2"]:.1%}, resid I2={d["I2_resid"]:.1f}%')
        for multi in ['dur_sess', 'dur_arm']:
            d = mr[multi]
            print(f'  {multi:<12}: R2={d["R2"]:.1%}, resid I2={d["I2_resid"]:.1f}%')
    else:
        results['meta_reg_r2'] = None

    # Save results
    output_path = 'output/supplementary_tests.json'
    os.makedirs('output', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f'\nResults saved to {output_path}')


if __name__ == '__main__':
    main()
