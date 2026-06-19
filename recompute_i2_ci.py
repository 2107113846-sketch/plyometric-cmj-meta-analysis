"""
Recalculate I² confidence intervals using R/metafor confint() (Q-profile method).
"""
import sys, io, json, csv, numpy as np
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
PROJ = Path(__file__).parent
sys.path.insert(0, str(PROJ))
from meta_toolkit.r_bridge import meta_pool_r, is_r_available

EFFECTS_CSV = PROJ / 'analysis_ready_effects.csv'
OUTPUT_DIR = PROJ / 'output'

def get_key(d, *candidates):
    for c in candidates:
        for k in d.keys():
            if c in k:
                return k
    return None

def main():
    if not is_r_available():
        print("R not available")
        return

    with open(EFFECTS_CSV, 'r', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    sid_key = get_key(rows[0], 'study_id')

    # Helper
    def pool_rows(rlist, label):
        yi = [float(r['yi_change']) for r in rlist]
        vi = [float(r['vi_change']) for r in rlist]
        labs = [f"{r['author']} {r['year']}" for r in rlist]
        print(f"\n=== {label} (k={len(yi)}) ===")
        res = meta_pool_r(yi, vi, labs, method='REML')
        g = res['beta']; cl = res['ci_low']; cu = res['ci_upp']
        I2 = res['I2']; il = res['I2_ci_low']; iu = res['I2_ci_upp']
        t2 = res['tau2']; tl = res['tau2_ci_low']; tu = res['tau2_ci_upp']
        ok = "OK" if il <= I2 <= iu else f"FAIL (I2={I2} not in [{il},{iu}])"
        print(f"  g={g:.3f}[{cl:.3f},{cu:.3f}]")
        print(f"  I2={I2:.1f}% [95%CI: {il:.1f}%, {iu:.1f}%]  {ok}")
        print(f"  tau2={t2:.3f} [95%CI: {tl:.3f}, {tu:.3f}]")
        return {'label': label, 'k': res['k'], 'g': g, 'ci_low': cl, 'ci_upp': cu,
                'I2': I2, 'I2_ci_low': il, 'I2_ci_upp': iu,
                'tau2': t2, 'tau2_ci_low': tl, 'tau2_ci_upp': tu,
                'pred_low': res.get('pred_low'), 'pred_upp': res.get('pred_upp')}

    results = {}

    # === Strict pool: "手叉腰" in cmj_arm, exclude VJ ===
    strict = [r for r in rows if '手叉腰' in r['cmj_arm'] and 'VJ' not in r['cmj_arm'] and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    results['strict'] = pool_rows(strict, 'Strict hand-on-hip')

    # === Wide pool: all change-score studies (exclude VJ-only) ===
    wide = [r for r in rows if 'VJ' not in r['cmj_arm'] and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    results['wide'] = pool_rows(wide, 'Wide all CMJ')

    # === Short-term (≤6 weeks): known R-IDs from manuscript (R19 excluded due to SE/SD confusion) ===
    short_ids = {'R01','R02','R04','R05','R06','R12','R13','R14','R15','R16','R20','R22'}
    short = [r for r in rows if r[sid_key] in short_ids and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    results['short'] = pool_rows(short, 'Short-term <=6wk')

    # === Mid-term (7-10 weeks) ===
    mid_ids = {'R03','R07','R08','R09','R10','R17','R18','R21','R23','R26','R29','R30','R31'}
    mid = [r for r in rows if r[sid_key] in mid_ids and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    results['mid'] = pool_rows(mid, 'Mid-term 7-10wk')

    # === k=2 sub-groups: confint() needs k>=3, so these will fail gracefully ===
    pre_ids = {'R14', 'R20'}
    pre = [r for r in rows if r[sid_key] in pre_ids and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    print(f"\n=== Pre-pubertal (k={len(pre)}) ===")
    if len(pre) >= 3:
        results['pre'] = pool_rows(pre, 'Pre-pubertal')
    else:
        print(f"  k={len(pre)} < 3; confint() not applicable. I2 CI not computable.")
        # Do simple rma without CI
        yi = [float(r['yi_change']) for r in pre]
        vi = [float(r['vi_change']) for r in pre]
        try:
            res = meta_pool_r(yi, vi, [f"{r['author']} {r['year']}" for r in pre], method='REML')
            print(f"  g={res['beta']:.3f}, I2={res['I2']:.1f}% (note: k=2, CI not computable via confint)")
        except:
            print(f"  meta_pool_r failed for k=2")

    pub_ids = {'R21', 'R26'}
    pub = [r for r in rows if r[sid_key] in pub_ids and r['effect_method'] == 'pre-post change SMD (Hedges g)']
    print(f"\n=== Pubertal (k={len(pub)}) ===")
    if len(pub) >= 3:
        results['pub'] = pool_rows(pub, 'Pubertal')
    else:
        print(f"  k={len(pub)} < 3; confint() not applicable. I2 CI not computable.")

    # === Save ===
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / 'i2_ci_corrected.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved to {out_path}")

    # === Summary ===
    print("\n" + "="*60)
    print("MANUSCRIPT CORRECTED VALUES")
    print("="*60)
    for key in ['strict', 'wide', 'short', 'mid']:
        r = results[key]
        print(f"\n{r['label']} (k={r['k']}):")
        print(f"  g = {r['g']:.3f} [{r['ci_low']:.3f}, {r['ci_upp']:.3f}]")
        print(f"  I² = {r['I2']:.1f}% [95%CI: {r['I2_ci_low']:.1f}%, {r['I2_ci_upp']:.1f}%]")

if __name__ == '__main__':
    main()
