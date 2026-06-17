"""
从 analysis_ready_effects.csv 生成森林图
分两个池: 严格手叉腰 vs 宽版含臂位不明
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from meta_toolkit.r_bridge import meta_pool_r


def load_effects(csv_path):
    """Load effect sizes from analysis-ready CSV."""
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            studies.append({
                'study_id': row['study_id'],
                'author': row['author'],
                'year': row['year'],
                'exp_n': int(float(row['exp_n'])),
                'ctrl_n': int(float(row['ctrl_n'])),
                'yi': float(row['yi_change']),  # pre-post change SMD (more precise)
                'vi': float(row['vi_change']),
                'sei': float(row['sei_change']),
                'data_note': row.get('data_note', ''),
                'cmj_arm': row.get('cmj_arm', ''),
            })
    return studies


def classify_study(s):
    """Classify study into strict hand-on-hip vs arm-unclear."""
    note = s.get('data_note', '')
    if '✅' in note:
        return 'strict'       # 严格手叉腰无臂
    elif 'VJ带臂' in note or 'VJ敏感性' in note:
        return 'vj_subgroup'  # VJ敏感性亚组
    else:
        return 'arm_unclear'  # 臂位未明/CMJA


def run_forest(strict_studies, arm_unclear_studies, output_dir):
    """Run forest plot for each pool."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # === Pool 1: Strict hand-on-hip ===
    if strict_studies:
        yi = [s['yi'] for s in strict_studies]
        vi = [s['vi'] for s in strict_studies]
        labels = [f"{s['author']} {s['year']} (n={s['exp_n']+s['ctrl_n']})"
                  for s in strict_studies]

        print(f"\n{'='*60}")
        print(f"  [Pool 1] 严格手叉腰无臂 CMJ ({len(strict_studies)} studies)")
        print(f"{'='*60}")

        try:
            result_strict = meta_pool_r(
                yi, vi, labels=labels, method='REML',
                forest_plot=str(output_dir / 'forest_strict_hand_on_hip.png')
            )
            print(f"  Pooled SMD (Hedges' g): {result_strict['beta']:.3f}")
            print(f"  95% CI: [{result_strict['ci_low']:.3f}, {result_strict['ci_upp']:.3f}]")
            print(f"  p = {result_strict['pval']:.4f}")
            print(f"  tau^2 = {result_strict['tau2']:.4f}")
            print(f"  I^2 = {result_strict['I2']:.1f}%")
            print(f"  Q (df={result_strict['k']-1}) = {result_strict['Q']:.2f}, p = {result_strict['Q_pval']:.4f}")
            print(f"  森林图 -> {output_dir / 'forest_strict_hand_on_hip.png'}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    # === Pool 2: Wide pool (strict + arm_unclear) ===
    all_studies = strict_studies + arm_unclear_studies
    if all_studies:
        yi = [s['yi'] for s in all_studies]
        vi = [s['vi'] for s in all_studies]
        labels = [f"{s['author']} {s['year']}" for s in all_studies]

        print(f"\n{'='*60}")
        print(f"  [Pool 2] 宽版含臂位不明 CMJ ({len(all_studies)} studies)")
        print(f"{'='*60}")

        try:
            result_wide = meta_pool_r(
                yi, vi, labels=labels, method='REML',
                forest_plot=str(output_dir / 'forest_wide_all_cmj.png')
            )
            print(f"  Pooled SMD (Hedges' g): {result_wide['beta']:.3f}")
            print(f"  95% CI: [{result_wide['ci_low']:.3f}, {result_wide['ci_upp']:.3f}]")
            print(f"  p = {result_wide['pval']:.4f}")
            print(f"  tau^2 = {result_wide['tau2']:.4f}")
            print(f"  I^2 = {result_wide['I2']:.1f}%")
            print(f"  Q (df={result_wide['k']-1}) = {result_wide['Q']:.2f}, p = {result_wide['Q_pval']:.4f}")
            print(f"  森林图 -> {output_dir / 'forest_wide_all_cmj.png'}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    return result_strict if strict_studies else None, result_wide if all_studies else None


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    studies = load_effects(csv_path)
    print(f"加载: {len(studies)} 篇有效应量")

    # Classify
    strict = [s for s in studies if classify_study(s) == 'strict']
    arm_unclear = [s for s in studies if classify_study(s) == 'arm_unclear']
    vj = [s for s in studies if classify_study(s) == 'vj_subgroup']

    print(f"  严格手叉腰: {len(strict)} 篇")
    print(f"  臂位未明/CMJA: {len(arm_unclear)} 篇")
    print(f"  VJ敏感性亚组: {len(vj)} 篇")

    # Show study list
    print("\n严格手叉腰列表:")
    for s in strict:
        print(f"  {s['study_id']} {s['author']} ({s['year']}) g={s['yi']:.3f} CI=[{s['yi']-1.96*s['sei']:.3f},{s['yi']+1.96*s['sei']:.3f}]")

    output_dir = "D:/桌面/科研训练/output"
    run_forest(strict, arm_unclear, output_dir)


if __name__ == "__main__":
    main()
