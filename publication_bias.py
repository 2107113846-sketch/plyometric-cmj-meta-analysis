"""
发表偏倚分析: 漏斗图 + Egger检验 + Trim-and-Fill + 小研究效应
"""
import csv, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from meta_toolkit.r_bridge import meta_pool_r
from meta_toolkit.viz import draw_funnel, egger_test


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


def is_strict(s):
    return '✅' in s.get('data_note', '')


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    all_studies = load_effects(csv_path)
    strict = [s for s in all_studies if is_strict(s)]
    wide = [s for s in all_studies if 'VJ' not in s.get('data_note', '')]

    output_dir = Path("D:/桌面/科研训练/output")
    output_dir.mkdir(exist_ok=True)

    for name, pool in [("strict_hand_on_hip", strict), ("wide_all_cmj", wide)]:
        print(f"\n{'='*65}")
        print(f"  Publication Bias: {name} ({len(pool)} studies)")
        print(f"{'='*65}")

        yi_arr = np.array([s['yi'] for s in pool])
        sei_arr = np.array([s['sei'] for s in pool])
        vi_arr = np.array([s['vi'] for s in pool])
        n_total = np.array([s['exp_n'] + s['ctrl_n'] for s in pool])
        labels = [f"{s['author']} {s['year']}" for s in pool]

        # 1. Egger's regression test via R/metafor
        print(f"\n  [1] Egger's Regression Test (R/metafor regtest)")
        r = meta_pool_r(yi_arr.tolist(), vi_arr.tolist(), labels=labels, method='REML')
        egger_int = r.get('egger_intercept')
        egger_p = r.get('egger_pval')
        if egger_int is not None:
            print(f"      Intercept = {egger_int:.4f}, p = {egger_p:.4f}")
            if egger_p < 0.05:
                print(f"      >> Significant asymmetry detected (p < 0.05) <<")
            elif egger_p < 0.10:
                print(f"      >> Marginal asymmetry (p < 0.10) <<")
            else:
                print(f"      No significant asymmetry (p > 0.10)")

        # 2. Egger's test via Python implementation (sanity check)
        print(f"\n  [2] Egger's Test (Python implementation)")
        e = egger_test(yi_arr, sei_arr)
        print(f"      Intercept = {e['intercept']:.4f}, p = {e['pval']:.4f}")

        # 3. Funnel plot with Egger
        print(f"\n  [3] Funnel Plot -> {output_dir}/funnel_{name}.png")
        draw_funnel(
            yi_arr, sei_arr,
            labels=labels,
            filepath=str(output_dir / f"funnel_{name}.png"),
            title=f"Funnel Plot - {name.replace('_', ' ').title()} ({len(pool)} studies)",
            show_egger=True
        )
        print(f"      Saved.")

        # 4. Trim-and-fill analysis (manual approximation)
        # Count studies on each side of pooled effect
        pooled_g = r['beta']
        right_side = sum(1 for y in yi_arr if y > pooled_g)
        left_side = sum(1 for y in yi_arr if y < pooled_g)
        print(f"\n  [4] Trim-and-Fill Assessment")
        print(f"      Pooled effect: g = {pooled_g:.3f}")
        print(f"      Studies above pooled effect: {right_side}")
        print(f"      Studies below pooled effect: {left_side}")
        asymmetry_ratio = right_side / max(left_side, 1)
        print(f"      Ratio (right/left): {asymmetry_ratio:.2f}")
        if asymmetry_ratio > 1.5:
            print(f"      >> Possible small-study effects (more positive studies) <<")
        elif asymmetry_ratio < 0.67:
            print(f"      >> Possible small-study effects (more negative studies) <<")
        else:
            print(f"      Distribution appears roughly symmetric")

        # 5. Correlation between SE and effect size (small-study effect)
        if len(sei_arr) >= 5:
            corr = np.corrcoef(sei_arr, yi_arr)[0, 1]
            print(f"\n  [5] Small-Study Effect")
            print(f"      Correlation(SE, g) = {corr:.3f}")
            if abs(corr) > 0.3:
                direction = "larger studies show smaller effects" if corr < 0 else "larger studies show larger effects"
                print(f"      >> Moderate correlation: {direction} <<")
            else:
                print(f"      No strong small-study effect detected")

        # 6. Study-level detail for funnel plot interpretation
        print(f"\n  [6] Study Details (sorted by SE, smallest=top)")
        sorted_studies = sorted(zip(labels, yi_arr, sei_arr, n_total), key=lambda x: x[2])
        print(f"      {'Study':<30} {'g':>7} {'SE':>6} {'n_total':>8}")
        print(f"      {'-'*52}")
        for label, g, se, n in sorted_studies:
            print(f"      {label:<30} {g:+.3f}  {se:.3f}  {n:>5}")

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'='*65}")
    print(f"  Publication Bias Summary")
    print(f"{'='*65}")
    print(f"  Funnel plots saved to output/")
    print(f"  Key takeaway: Check Egger's p-value and funnel plot asymmetry.")
    print(f"  If p < 0.10, consider trim-and-fill adjusted estimate.")


if __name__ == "__main__":
    main()
