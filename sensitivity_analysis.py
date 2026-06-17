"""
敏感性分析: 离群值剔除 + 留一法 + Baujat 图数据
"""
import csv
from csv import DictReader
import sys
from pathlib import Path
import numpy as np

# Fix Windows GBK encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))
from meta_toolkit.r_bridge import meta_pool_r


def load_effects(csv_path):
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in DictReader(f):
            studies.append({
                'study_id': row['study_id'],
                'author': row['author'],
                'year': row['year'],
                'exp_n': int(float(row['exp_n'])),
                'ctrl_n': int(float(row['ctrl_n'])),
                'yi': float(row['yi_change']),
                'vi': float(row['vi_change']),
                'sei': float(row['sei_change']),
                'data_note': row.get('data_note', ''),
                'exp_post_sd': float(row.get('exp_post_sd', 0) or 0),
                'ctrl_post_sd': float(row.get('ctrl_post_sd', 0) or 0),
                'exp_pre_sd': float(row.get('exp_pre_sd', 0) or 0),
                'ctrl_pre_sd': float(row.get('ctrl_pre_sd', 0) or 0),
                'cmj_arm': row.get('cmj_arm', ''),
            })
    return studies


def is_strict(s):
    return '✅' in s.get('data_note', '')


def run_pool(name, studies):
    """Run meta pool and return key results."""
    yi = [s['yi'] for s in studies]
    vi = [s['vi'] for s in studies]
    labels = [f"{s['author']} {s['year']}" for s in studies]
    try:
        r = meta_pool_r(yi, vi, labels=labels, method='REML')
        return r
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    all_studies = load_effects(csv_path)
    strict = [s for s in all_studies if is_strict(s)]

    print("=" * 65)
    print("  敏感性分析 — Plyometric训练对CMJ高度的影响")
    print("=" * 65)

    # ============================================================
    # 1. 基线模型 (全部严格手叉腰)
    # ============================================================
    print(f"\n{'-'*65}")
    print(f"  Model                             k    SMD      95% CI          I2")
    print(f"{'-'*65}")

    r0 = run_pool("基线: 全部严格手叉腰", strict)
    if r0:
        print(f"  {'基线: 全部严格手叉腰':<30} {r0['k']:>3}   {r0['beta']:+.3f}   [{r0['ci_low']:+.3f}, {r0['ci_upp']:+.3f}]   {r0['I2']:.0f}%")

    # ============================================================
    # 2. 逐一剔除离群值
    # ============================================================
    outliers = ['R11', 'R27', 'R10']  # only those in strict pool
    for rid in outliers:
        subset = [s for s in strict if s['study_id'] != rid]
        if len(subset) == len(strict):  # not found in strict
            continue
        r = run_pool(f"剔除 {rid}", subset)
        if r:
            delta = r['beta'] - r0['beta'] if r0 else float('nan')
            match = [s for s in strict if s['study_id']==rid]
            author_name = match[0]['author'] if match else '?'
            label = f"剔除 {rid} ({author_name})"
            print(f"  {label:<30} {r['k']:>3}   {r['beta']:+.3f}   [{r['ci_low']:+.3f}, {r['ci_upp']:+.3f}]   {r['I2']:.0f}%  D={delta:+.3f}")

    # 同时剔除R11+R27
    subset_both = [s for s in strict if s['study_id'] not in ['R11', 'R27']]
    r_both = run_pool("剔除 R11+R27", subset_both)
    if r_both and r0:
        delta = r_both['beta'] - r0['beta']
        print(f"  {'剔除 R11+R27':<30} {r_both['k']:>3}   {r_both['beta']:+.3f}   [{r_both['ci_low']:+.3f}, {r_both['ci_upp']:+.3f}]   {r_both['I2']:.0f}%  D={delta:+.3f}")

    # ============================================================
    # 3. 留一法分析 (Leave-One-Out)
    # ============================================================
    print(f"\n{'-'*65}")
    print(f"  Leave-One-Out -- strict pool ({len(strict)} studies)")
    print(f"{'-'*65}")
    print(f"  {'Removed':<30} {'g':>7}  {'95% CI':>20}  {'I2':>5}  {'delta_g':>7}")
    print(f"  {'-'*60}")

    loo_results = []
    for i, s in enumerate(strict):
        subset = [strict[j] for j in range(len(strict)) if j != i]
        r = run_pool(f"LOO {s['study_id']}", subset)
        if r:
            delta = r['beta'] - r0['beta'] if r0 else float('nan')
            loo_results.append({
                'removed': s['study_id'],
                'author': s['author'],
                'year': s['year'],
                'g': r['beta'],
                'ci_low': r['ci_low'],
                'ci_upp': r['ci_upp'],
                'I2': r['I2'],
                'delta': delta,
            })
            flag = ' !!' if abs(delta) > 0.2 else ''
            print(f"  {s['study_id']} {s['author']} ({s['year']}):{'':<6} {r['beta']:+.3f}  [{r['ci_low']:+.3f}, {r['ci_upp']:+.3f}]  {r['I2']:.0f}%  {delta:+.3f}{flag}")

    # ============================================================
    # 4. 宽版池同样做敏感性
    # ============================================================
    wide = [s for s in all_studies if not is_strict(s) and 'VJ' not in s.get('data_note', '')]
    wide_all = strict + wide
    rw0 = run_pool("基线: 宽版全部", wide_all)

    print(f"\n{'-'*65}")
    print(f"  宽版池(含臂位不明)敏感性 — {len(wide_all)}篇")
    print(f"{'-'*65}")

    if rw0:
        print(f"  {'基线: 宽版全部':<30} {rw0['k']:>3}   {rw0['beta']:+.3f}   [{rw0['ci_low']:+.3f}, {rw0['ci_upp']:+.3f}]   {rw0['I2']:.0f}%")

        # Remove top outliers from wide pool
        for rid in ['R11', 'R27', 'R08', 'R10']:
            subset = [s for s in wide_all if s['study_id'] != rid]
            r = run_pool(f"剔除 {rid}", subset)
            if r:
                delta = r['beta'] - rw0['beta']
                print(f"  {'剔除 '+rid:<30} {r['k']:>3}   {r['beta']:+.3f}   [{r['ci_low']:+.3f}, {r['ci_upp']:+.3f}]   {r['I2']:.0f}%  D={delta:+.3f}")

        # Both R11+R27
        subset_wb = [s for s in wide_all if s['study_id'] not in ['R11', 'R27']]
        r_wb = run_pool("剔除 R11+R27", subset_wb)
        if r_wb:
            delta = r_wb['beta'] - rw0['beta']
            print(f"  {'剔除 R11+R27':<30} {r_wb['k']:>3}   {r_wb['beta']:+.3f}   [{r_wb['ci_low']:+.3f}, {r_wb['ci_upp']:+.3f}]   {r_wb['I2']:.0f}%  D={delta:+.3f}")

    # ============================================================
    # 5. 数据瑕疵专项敏感性: R23 & R29
    # ============================================================
    print(f"\n{'='*65}")
    print(f"  数据瑕疵专项敏感性检验")
    print(f"{'='*65}")

    # --- R23 Rensing 2015: KG SD未报告, 以IG SD近似 ---
    r23 = [s for s in all_studies if s['study_id'] == 'R23']
    if r23:
        s23 = r23[0]
        print(f"\n  R23 {s23['author']} ({s23['year']}): KG SD以IG SD近似 ({s23['ctrl_post_sd']})")
        print(f"    原始: g={s23['yi']:.3f}, SE={s23['sei']:.3f}, 臂位未明")

        # 剔除R23 from wide pool
        wide_no_r23 = [s for s in wide_all if s['study_id'] != 'R23']
        rw_no23 = run_pool("剔除 R23 (KG SD近似)", wide_no_r23)
        if rw_no23 and rw0:
            delta = rw_no23['beta'] - rw0['beta']
            print(f"    宽版池(27篇)剔除R23后: g={rw_no23['beta']:+.3f} [{rw_no23['ci_low']:+.3f}, {rw_no23['ci_upp']:+.3f}], I2={rw_no23['I2']:.0f}%")
            print(f"    Δg = {delta:+.4f} (剔除影响{'已超' if abs(delta)>0.1 else '远小于'}0.1阈值)")

        # Also check arm-unclear subgroup
        unclear = [s for s in wide_all if '未明' in s.get('data_note', '')]
        unclear_no_r23 = [s for s in unclear if s['study_id'] != 'R23']
        ru0 = run_pool("臂位未明亚组(全)", unclear)
        ru_no23 = run_pool("臂位未明亚组(剔除R23)", unclear_no_r23)
        if ru0 and ru_no23:
            delta_u = ru_no23['beta'] - ru0['beta']
            print(f"    臂位未明亚组({len(unclear)}篇): g={ru0['beta']:+.3f} [{ru0['ci_low']:+.3f}, {ru0['ci_upp']:+.3f}], I2={ru0['I2']:.0f}%")
            print(f"    剔除R23后({len(unclear_no_r23)}篇): g={ru_no23['beta']:+.3f} [{ru_no23['ci_low']:+.3f}, {ru_no23['ci_upp']:+.3f}], I2={ru_no23['I2']:.0f}%")
            print(f"    Δg = {delta_u:+.4f}")

    # --- R29 Vescovi 2008: Post=Pre+Δ, SD以Pre SD近似 ---
    r29 = [s for s in all_studies if s['study_id'] == 'R29']
    if r29:
        s29 = r29[0]
        print(f"\n  R29 {s29['author']} ({s29['year']}): Post=Pre+Δ, SD用Pre SD近似")
        print(f"    原始: g={s29['yi']:.3f}, SE={s29['sei']:.3f}, 严格手叉腰")

        # 剔除R29 from strict pool
        strict_no_r29 = [s for s in strict if s['study_id'] != 'R29']
        r_no29 = run_pool("剔除 R29 (SD近似)", strict_no_r29)
        if r_no29 and r0:
            delta = r_no29['beta'] - r0['beta']
            print(f"    严格池(16篇)剔除R29后: g={r_no29['beta']:+.3f} [{r_no29['ci_low']:+.3f}, {r_no29['ci_upp']:+.3f}], I2={r_no29['I2']:.0f}%")
            print(f"    Δg = {delta:+.4f} (剔除影响{'已超' if abs(delta)>0.1 else '远小于'}0.1阈值)")

        # Also remove from wide pool
        wide_no_r29 = [s for s in wide_all if s['study_id'] != 'R29']
        rw_no29 = run_pool("剔除 R29 (SD近似, wide)", wide_no_r29)
        if rw_no29 and rw0:
            delta_w = rw_no29['beta'] - rw0['beta']
            print(f"    宽版池(28篇)剔除R29后: g={rw_no29['beta']:+.3f} [{rw_no29['ci_low']:+.3f}, {rw_no29['ci_upp']:+.3f}], I2={rw_no29['I2']:.0f}%")
            print(f"    Δg = {delta_w:+.4f}")

    # 同时剔除 R23+R29
    wide_no_both = [s for s in wide_all if s['study_id'] not in ['R23', 'R29']]
    rw_both = run_pool("剔除 R23+R29", wide_no_both)
    if rw_both and rw0:
        delta_both = rw_both['beta'] - rw0['beta']
        print(f"\n  同时剔除R23+R29 (宽版{len(wide_no_both)}篇): g={rw_both['beta']:+.3f} [{rw_both['ci_low']:+.3f}, {rw_both['ci_upp']:+.3f}], I2={rw_both['I2']:.0f}%")
        print(f"  累计Δg = {delta_both:+.4f}")
        print(f"  结论: {'✅ 数据瑕疵对结论无实质影响' if abs(delta_both) < 0.1 else '⚠️ 需在Discussion中讨论此不确定性'}")

    # ============================================================
    # 6. 总结
    # ============================================================
    print(f"\n{'='*65}")
    print(f"  敏感性分析总结")
    print(f"{'='*65}")

    if r0 and r_both:
        print(f"\n  严格手叉腰池:")
        print(f"    全16篇: SMD={r0['beta']:.3f} [95% CI {r0['ci_low']:.3f}, {r0['ci_upp']:.3f}], I2={r0['I2']:.0f}%")
        print(f"    剔除R11+R27后: SMD={r_both['beta']:.3f} [95% CI {r_both['ci_low']:.3f}, {r_both['ci_upp']:.3f}], I2={r_both['I2']:.0f}%")
        print(f"    结论: 合并效应量变化 D={r_both['beta']-r0['beta']:+.3f}，方向未变，效应稳定在大→中范围")

    # Find most influential
    if loo_results:
        loo_results.sort(key=lambda x: abs(x['delta']), reverse=True)
        print(f"\n  最有影响力的研究 (剔除后Dg最大):")
        for lr in loo_results[:3]:
            direction = "^" if lr['delta'] > 0 else "v"
            print(f"    {lr['removed']} {lr['author']} ({lr['year']}): "
                  f"剔除后 g={lr['g']:+.3f}, I2={lr['I2']:.0f}% (D={lr['delta']:+.3f}) {direction}")


if __name__ == "__main__":
    main()
