# -*- coding: utf-8 -*-
"""Compute PET-PEESE using pandas to handle quoted CSV fields correctly."""
import json, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pandas as pd

df = pd.read_csv('D:/桌面/科研训练/analysis_ready_effects.csv', encoding='utf-8-sig')
print("Columns:", list(df.columns))
print(f"Shape: {df.shape}")

# Verify column existence
assert 'study_id' in df.columns
assert 'yi_change' in df.columns
assert 'sei_change' in df.columns
assert 'cmj_arm' in df.columns

print("\nUnique cmj_arm values:", df['cmj_arm'].unique())

def ols(x, y):
    n = len(x)
    mean_x = sum(x)/n
    mean_y = sum(y)/n
    num = sum((xi-mean_x)*(yi-mean_y) for xi, yi in zip(x, y))
    den = sum((xi-mean_x)**2 for xi in x)
    if den == 0:
        return {'intercept': mean_y, 'slope': 0, 'se_slope': float('inf'), 't_slope': 0, 'r2': 0, 'n': n}
    beta1 = num/den
    beta0 = mean_y - beta1*mean_x
    yhat = [beta0 + beta1*xi for xi in x]
    ss_res = sum((yi-yhi)**2 for yi, yhi in zip(y, yhat))
    ss_tot = sum((yi-mean_y)**2 for yi in y)
    r2 = 1 - ss_res/ss_tot if ss_tot != 0 else 0
    se_beta1 = math.sqrt(ss_res/(n-2) / den) if n > 2 else float('inf')
    t_beta1 = beta1/se_beta1 if se_beta1 > 0 else 0
    return {'intercept': beta0, 'slope': beta1, 'se_slope': se_beta1, 't_slope': t_beta1, 'r2': r2, 'n': n}

# === STRICT POOL ===
strict_df = df[(df['cmj_arm'] == '手叉腰无臂') & (df['study_id'] != 'R19')]
print(f"\nStrict pool studies (k={len(strict_df)}):")
for _, r in strict_df.iterrows():
    print(f"  {r['study_id']} {r['author']}: g={r['yi_change']:+.4f}, SE={r['sei_change']:.4f}")

strict_yi = strict_df['yi_change'].tolist()
strict_sei = strict_df['sei_change'].tolist()
strict_sei_sq = [s**2 for s in strict_sei]

pet_s = ols(strict_sei, strict_yi)
peese_s = ols(strict_sei_sq, strict_yi)

# === WIDE POOL ===
wide_df = df[~df['study_id'].isin(['R19', 'R24'])]
print(f"\nWide pool studies (k={len(wide_df)}):")
for _, r in wide_df.iterrows():
    print(f"  {r['study_id']} {r['author']}: g={r['yi_change']:+.4f}, SE={r['sei_change']:.4f}")

wide_yi = wide_df['yi_change'].tolist()
wide_sei = wide_df['sei_change'].tolist()
wide_sei_sq = [s**2 for s in wide_sei]

pet_w = ols(wide_sei, wide_yi)
peese_w = ols(wide_sei_sq, wide_yi)

# === Output ===
pet_peese = {
    'strict': {
        'pet_intercept': round(pet_s['intercept'], 4),
        'pet_slope': round(pet_s['slope'], 4),
        'pet_se_slope': round(pet_s['se_slope'], 4),
        'pet_t_slope': round(pet_s['t_slope'], 3),
        'pet_r2': round(pet_s['r2'], 3),
        'peese_intercept': round(peese_s['intercept'], 4),
        'peese_slope': round(peese_s['slope'], 4),
        'peese_se_slope': round(peese_s['se_slope'], 4),
        'peese_t_slope': round(peese_s['t_slope'], 3),
        'peese_r2': round(peese_s['r2'], 3),
        'k': len(strict_df),
        'note': 'PET-PEESE: g ~ SE (PET) or g ~ SE^2 (PEESE). When PET intercept > 0, PEESE is recommended.'
    },
    'wide': {
        'pet_intercept': round(pet_w['intercept'], 4),
        'pet_slope': round(pet_w['slope'], 4),
        'pet_se_slope': round(pet_w['se_slope'], 4),
        'pet_r2': round(pet_w['r2'], 3),
        'peese_intercept': round(peese_w['intercept'], 4),
        'peese_slope': round(peese_w['slope'], 4),
        'peese_se_slope': round(peese_w['se_slope'], 4),
        'peese_r2': round(peese_w['r2'], 3),
        'k': len(wide_df),
        'note': 'PET-PEESE: g ~ SE (PET) or g ~ SE^2 (PEESE). When PET intercept > 0, PEESE is recommended.'
    }
}

out_path = 'D:/桌面/科研训练/output/pet_peese_results.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(pet_peese, f, indent=2, ensure_ascii=False)

print(f"\n===== RESULTS =====")
print(f"STRICT POOL (k={len(strict_df)}):")
print(f"  PET: intercept={pet_s['intercept']:+.4f}, slope={pet_s['slope']:+.4f}, R2={pet_s['r2']:.3f}")
print(f"  PEESE: intercept={peese_s['intercept']:+.4f}, slope={peese_s['slope']:+.4f}, R2={peese_s['r2']:.3f}")
print(f"  Original RE g=+1.112, PEESE-corrected g={peese_s['intercept']:+.4f}")

print(f"\nWIDE POOL (k={len(wide_df)}):")
print(f"  PET: intercept={pet_w['intercept']:+.4f}, slope={pet_w['slope']:+.4f}, R2={pet_w['r2']:.3f}")
print(f"  PEESE: intercept={peese_w['intercept']:+.4f}, slope={peese_w['slope']:+.4f}, R2={peese_w['r2']:.3f}")
print(f"  Original RE g=+0.986, PEESE-corrected g={peese_w['intercept']:+.4f}")

print(f"\nSaved to: {out_path}")
