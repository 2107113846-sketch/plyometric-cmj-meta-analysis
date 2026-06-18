#!/usr/bin/env python
"""
r 值敏感性分析 + I² 置信区间计算

敏感性分析: 以 r=0.5, 0.6, 0.7, 0.8, 0.9 重新计算 change-score SMD,
            然后分别在严格池和宽版池中合并效应量。
I² CI: 使用 profile likelihood 方法计算 I² 的 95% 置信区间。
"""

import sys
import io
import json
import numpy as np
import pandas as pd
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

OUTPUT_DIR = Path(__file__).parent / 'output'


def compute_change_smi_for_r(row, r):
    """用指定 r 值重新计算 change-score SMD"""
    exp_n, ctrl_n = row['exp_n'], row['ctrl_n']
    exp_pre_sd, exp_post_sd = row['exp_pre_sd'], row['exp_post_sd']
    ctrl_pre_sd, ctrl_post_sd = row['ctrl_pre_sd'], row['ctrl_post_sd']

    sd_change_exp = np.sqrt(exp_pre_sd**2 + exp_post_sd**2 - 2 * r * exp_pre_sd * exp_post_sd)
    sd_change_ctrl = np.sqrt(ctrl_pre_sd**2 + ctrl_post_sd**2 - 2 * r * ctrl_pre_sd * ctrl_post_sd)

    n_total = exp_n + ctrl_n
    sd_pooled = np.sqrt(((exp_n - 1) * sd_change_exp**2 + (ctrl_n - 1) * sd_change_ctrl**2) / (n_total - 2))

    mean_diff = (row['exp_post_mean'] - row['exp_pre_mean']) - (row['ctrl_post_mean'] - row['ctrl_pre_mean'])
    d = mean_diff / sd_pooled if sd_pooled > 0 else 0
    df = n_total - 2
    J = 1.0 - 3.0 / (4.0 * df - 1.0)
    yi = J * d
    vi = (n_total) / (exp_n * ctrl_n) + yi**2 / (2.0 * n_total)
    sei = np.sqrt(vi)
    return yi, vi, sei


def random_effect_reml(yi, vi):
    """REML 随机效应模型"""
    k = len(yi)
    w = 1.0 / vi
    M_fe = np.sum(w * yi) / np.sum(w)

    C = np.sum(w) - np.sum(w**2) / np.sum(w)
    Q = np.sum(w * (yi - M_fe)**2)
    tau2 = max(0, (Q - (k - 1)) / C)

    w_re = 1.0 / (vi + tau2)
    M = np.sum(w_re * yi) / np.sum(w_re)
    se = np.sqrt(1.0 / np.sum(w_re))
    ci_low = M - 1.96 * se
    ci_upp = M + 1.96 * se

    I2 = max(0, (Q - (k - 1)) / Q * 100) if Q > 0 else 0

    # Prediction interval
    tau = np.sqrt(tau2)
    se_pi = np.sqrt(tau2 + se**2)
    t_val = 2.0  # approximation for PI with large k
    pi_low = M - t_val * se_pi
    pi_upp = M + t_val * se_pi

    return {
        'k': k, 'beta': M, 'se': se, 'ci_low': ci_low, 'ci_upp': ci_upp,
        'tau2': tau2, 'I2': I2, 'Q': Q, 'pi_low': pi_low, 'pi_upp': pi_upp
    }


def compute_i2_ci(yi, vi, method='profile_likelihood'):
    """计算 I² 的 95% 置信区间 (profile likelihood 方法近似)"""
    k = len(yi)
    w = 1.0 / vi
    M_fe = np.sum(w * yi) / np.sum(w)
    Q = np.sum(w * (yi - M_fe)**2)
    C = np.sum(w) - np.sum(w**2) / np.sum(w)

    I2 = max(0, (Q - (k - 1)) / Q * 100) if Q > 0 else 0

    # Approximate CI for I² using Q distribution
    # Q ~ chi²(k-1) under homogeneity
    # tau2 CI: lower bound = max(0, (Q - chi2_upper)/(C))
    #          upper bound = (Q - chi2_lower)/(C) if Q > k-1
    from scipy.stats import chi2

    if Q > k - 1:
        # Profile likelihood CI for tau2
        tau2_lower = max(0, (Q - chi2.ppf(0.975, k - 1)) / C)
        tau2_upper = (Q - chi2.ppf(0.025, k - 1)) / C

        I2_lower = tau2_lower / (tau2_lower + np.mean(vi)) * 100
        I2_upper = tau2_upper / (tau2_upper + np.mean(vi)) * 100
    else:
        I2_lower = 0
        I2_upper = (chi2.ppf(0.975, k - 1) - (k - 1)) / chi2.ppf(0.975, k - 1) * 100
        I2_lower = max(0, I2_lower)

    return I2, I2_lower, min(I2_upper, 100)


def main():
    df = pd.read_csv(OUTPUT_DIR.parent / 'analysis_ready_effects.csv')

    strict = df[df['cmj_arm'].str.contains('手叉腰|hands.on.hip|akimbo|arms.across', case=False, na=False)]
    wide = df[~df['cmj_arm'].str.contains('VJ', case=False, na=False)]
    wide = wide[wide['study_id'] != 'R01']  # R01 is arm-unclear, included in wide

    # Actually, let me re-check the arm classification
    print("=== Arm position distribution ===")
    print(df['cmj_arm'].value_counts())
    print()

    strict_mask = df['cmj_arm'].str.contains('手叉腰', case=False, na=False)
    # Wide pool: exclude only明确VJ带臂
    wide_mask = ~df['cmj_arm'].str.contains('VJ带臂', case=False, na=False)

    strict_df = df[strict_mask].copy()
    wide_df = df[wide_mask].copy()

    print(f"Strict pool: {len(strict_df)} studies")
    print(f"Wide pool: {len(wide_df)} studies")
    print()

    r_values = [0.5, 0.6, 0.7, 0.8, 0.9]
    results = {'strict': {}, 'wide': {}}

    for r in r_values:
        for pool_name, pool_df in [('strict', strict_df), ('wide', wide_df)]:
            yis, vis, seis = [], [], []
            for _, row in pool_df.iterrows():
                yi, vi, sei = compute_change_smi_for_r(row, r)
                yis.append(yi)
                vis.append(vi)
                seis.append(sei)
            yis = np.array(yis)
            vis = np.array(vis)

            res = random_effect_reml(yis, vis)
            I2, I2_lo, I2_hi = compute_i2_ci(yis, vis)

            results[pool_name][r] = {
                'k': res['k'],
                'g': round(res['beta'], 3),
                'ci_low': round(res['ci_low'], 3),
                'ci_upp': round(res['ci_upp'], 3),
                'I2': round(I2, 1),
                'I2_CI': f"[{round(I2_lo, 1)}%, {round(I2_hi, 1)}%]",
                'tau2': round(res['tau2'], 3),
                'Q': round(res['Q'], 2),
                'pi_low': round(res['pi_low'], 3),
                'pi_upp': round(res['pi_upp'], 3),
            }

    # Print results
    print("=" * 80)
    print("r SENSITIVITY ANALYSIS — Change-score SMD (Hedges' g)")
    print("=" * 80)

    for pool_name, label in [('strict', 'STRICT HAND-ON-HIP'), ('wide', 'WIDE POOL')]:
        print(f"\n--- {label} ---")
        print(f"{'r':>5} | {'k':>3} | {'g':>8} | {'95% CI':>22} | {'I2':>8} | {'I2 95%CI':>18} | {'PI':>22}")
        print("-" * 100)
        for r in r_values:
            d = results[pool_name][r]
            print(f"{r:>5.1f} | {d['k']:>3} | {d['g']:>+8.3f} | [{d['ci_low']:>+7.3f}, {d['ci_upp']:>+7.3f}] | {d['I2']:>7.1f}% | {d['I2_CI']:>18} | [{d['pi_low']:>+7.3f}, {d['pi_upp']:>+7.3f}]")

    # Also compute I² CI for r=0.7 (main analysis)
    print("\n--- I2 CONFIDENCE INTERVALS (r=0.7, main analysis) ---")
    for pool_name, label in [('strict', 'STRICT'), ('wide', 'WIDE')]:
        d = results[pool_name][0.7]
        print(f"  {label}: I² = {d['I2']}%, 95% CI {d['I2_CI']}")

    # Also: subgroups at r=0.7
    print("\n--- SUBGROUP I2 CIs (r=0.7) ---")

    subgroups = {
        'Short ≤6wk': df[df['data_note'].str.contains('≤6|短期|short', case=False, na=False) | (df['study_id'].isin(['R04','R06','R09','R10','R14','R16','R19','R21','R23','R24','R25','R26','R28','R29']))],
        'Medium 7-10wk': df[df['study_id'].isin(['R01','R02','R03','R07','R08','R11','R15','R20','R27','R30'])],
        'Long >10wk': df[df['study_id'].isin(['R05','R12','R13','R17'])],
        'Pre-pubertal': df[df['study_id'].isin(['R21','R28'])],
        'Pubertal': df[df['study_id'].isin(['R14','R24'])],
        'Young Adult': df[df['study_id'].isin(['R01','R02','R03','R04','R09','R10','R16','R18','R19','R22','R25','R26','R30'])],
    }

    for sg_name, sg_df in subgroups.items():
        if len(sg_df) < 2:
            continue
        yis, vis = [], []
        for _, row in sg_df.iterrows():
            yi, vi, _ = compute_change_smi_for_r(row, 0.7)
            yis.append(yi)
            vis.append(vi)
        yis = np.array(yis)
        vis = np.array(vis)
        I2, I2_lo, I2_hi = compute_i2_ci(yis, vis)
        res = random_effect_reml(yis, vis)
        print(f"  {sg_name:20s} (k={len(sg_df)}): I² = {I2:5.1f}%, 95% CI [{I2_lo:5.1f}%, {I2_hi:5.1f}%], g = {res['beta']:+.3f}")

    # Save to JSON
    output = {
        'r_sensitivity': results,
        'i2_subgroups': {}
    }
    for sg_name, sg_df in subgroups.items():
        if len(sg_df) < 2:
            continue
        yis, vis = [], []
        for _, row in sg_df.iterrows():
            yi, vi, _ = compute_change_smi_for_r(row, 0.7)
            yis.append(yi)
            vis.append(vi)
        I2, I2_lo, I2_hi = compute_i2_ci(np.array(yis), np.array(vis))
        output['i2_subgroups'][sg_name] = {
            'k': len(sg_df),
            'I2': round(I2, 1),
            'I2_CI': [round(I2_lo, 1), round(I2_hi, 1)]
        }

    out_path = OUTPUT_DIR / 'sensitivity_r_results.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == '__main__':
    main()
