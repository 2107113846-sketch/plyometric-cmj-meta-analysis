"""
亚组分析: 按 CMJ臂位 / 训练类型 / 年龄组 / 训练水平 / 对照类型 / 干预时长
"""
import csv, sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from meta_toolkit.r_bridge import meta_pool_r


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
                'cmj_arm': row.get('cmj_arm', ''),
                'population': row.get('population', ''),
                'sport': row.get('sport', ''),
            })
    return studies


def classify_arm(note, arm_field):
    """CMJ arm position."""
    if 'VJ带臂' in note or 'VJ敏感性' in note:
        return 'VJ-with-arm-swing'
    if '✅' in note:
        return 'Strict hands-on-hips'
    if 'CMJA' in note or '带臂' in note:
        return 'CMJA-arm-swing'
    return 'Arm-unclear'


def classify_population(note, pop):
    """Age/development group."""
    n = note.lower() + pop.lower()
    if '老年' in n or 'elder' in n or 'older' in n:
        return 'Older adults'
    if '青春期前' in n or 'prepubertal' in n or '青春期前期' in n or '青春期早' in n:
        return 'Pre/Early Pubertal'
    if '青春期' in n or 'pubertal' in n or 'tanner' in n:
        return 'Pubertal'
    if '青年' in n or 'young' in n or 'u-' in n or 'college' in n or '大学' in n:
        return 'Young adult'
    if '成年' in n or 'adult' in n or 'senior' in n or '职业' in n:
        return 'Adult/Pro'
    return 'Adult/Pro'  # default


def classify_training_type(note):
    """Pure plyo vs mixed."""
    n = note.lower()
    # "混合" can appear in "混合性别" (mixed sex) — only match when about training
    if 'smith' in n or '混合训' in n or '混合干预' in n or '重训' in n or 'resistance' in n or 'plyo+' in n:
        return 'Mixed (Plyo+Strength)'
    if 'cod' in n or 'mb throw' in n or '药球' in n:
        return 'Plyo+minor other'
    return 'Pure plyometric'


def classify_duration(note):
    """Intervention duration from data_note or context."""
    # We infer from known study characteristics
    return 'Unknown'


def classify_control(note):
    """Control group type."""
    n = note.lower()
    if '无训练' in n or 'no training' in n or '维持正常' in n or '维持日常' in n or '日常活动' in n:
        return 'No-training control'
    return 'Active control (sport training)'


def run_subgroup(name, subgroups):
    """Run meta-analysis for each subgroup and print results."""
    print(f"\n{'='*65}")
    print(f"  {name}")
    print(f"{'='*65}")
    print(f"  {'Subgroup':<35} {'k':>3}  {'SMD':>7}  {'95% CI':>22}  {'I2':>5}  {'tau2':>6}")
    print(f"  {'-'*60}")

    results = {}
    for label, studies in subgroups.items():
        if len(studies) < 2:
            print(f"  {label:<35} {len(studies):>3}  (too few studies)")
            continue
        yi = [s['yi'] for s in studies]
        vi = [s['vi'] for s in studies]
        labels_l = [f"{s['author']} {s['year']}" for s in studies]
        try:
            r = meta_pool_r(yi, vi, labels=labels_l, method='REML')
            results[label] = r
            # Flag k=2 subgroups as insufficient evidence
            k_flag = " [! k=2, insufficient]" if r['k'] == 2 else ""
            print(f"  {label:<35} {r['k']:>3}  {r['beta']:+.3f}   [{r['ci_low']:+.3f}, {r['ci_upp']:+.3f}]  {r['I2']:.0f}%  {r['tau2']:.3f}{k_flag}")
            # List studies
            for s in studies:
                print(f"    {s['study_id']} {s['author']} ({s['year']}) g={s['yi']:+.2f}")
        except Exception as e:
            print(f"  {label:<35} {len(studies):>3}  [ERROR: {e}]")

    return results


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    studies = load_effects(csv_path)
    # Exclude VJ-only study for CMJ analysis
    studies = [s for s in studies if 'VJ带臂' not in s.get('data_note', '')]
    print(f"Loaded {len(studies)} CMJ studies for subgroup analysis")

    # ============================================================
    # Subgroup 1: CMJ Arm Position
    # ============================================================
    arm_groups = {}
    for s in studies:
        key = classify_arm(s['data_note'], s['cmj_arm'])
        arm_groups.setdefault(key, []).append(s)

    # Order: Strict > Arm-unclear > CMJA
    order = ['Strict hands-on-hips', 'Arm-unclear', 'CMJA-arm-swing']
    arm_ordered = {k: arm_groups[k] for k in order if k in arm_groups}
    run_subgroup("Subgroup 1: CMJ Arm Position", arm_ordered)

    # ============================================================
    # Subgroup 2: Age/Development Stage
    # ============================================================
    age_groups = {}
    for s in studies:
        key = classify_population(s['data_note'], s['population'])
        age_groups.setdefault(key, []).append(s)

    age_order = ['Pre/Early Pubertal', 'Pubertal', 'Young adult', 'Adult/Pro', 'Older adults']
    age_ordered = {k: age_groups[k] for k in age_order if k in age_groups}
    run_subgroup("Subgroup 2: Age / Development Stage", age_ordered)

    # ============================================================
    # Subgroup 3: Training Type (Pure Plyo vs Mixed)
    # ============================================================
    type_groups = {}
    for s in studies:
        key = classify_training_type(s['data_note'])
        type_groups.setdefault(key, []).append(s)
    run_subgroup("Subgroup 3: Training Type", type_groups)

    # ============================================================
    # Subgroup 4: Control Type
    # ============================================================
    ctrl_groups = {}
    for s in studies:
        key = classify_control(s['data_note'])
        ctrl_groups.setdefault(key, []).append(s)
    run_subgroup("Subgroup 4: Control Type", ctrl_groups)

    # ============================================================
    # Subgroup 5: Intervention Duration (from data_note or manual)
    # ============================================================
    # Manual coding based on the data extraction tables
    DURATION_MAP = {
        'R01': 'Short (<=6wk)', 'R02': 'Short (<=6wk)',
        'R03': 'Short (<=6wk)', 'R04': 'Short (<=6wk)',
        'R05': 'Short (<=6wk)', 'R06': 'Long (>10wk)',
        'R07': 'Short (<=6wk)', 'R08': 'Medium (7-10wk)',
        'R09': 'Short (<=6wk)', 'R10': 'Medium (7-10wk)',
        'R11': 'Long (>10wk)', 'R12': 'Medium (7-10wk)',
        'R13': 'Long (>10wk)', 'R14': 'Medium (7-10wk)',
        'R15': 'Short (<=6wk)', 'R16': 'Medium (7-10wk)',
        'R17': 'Short (<=6wk)', 'R18': 'Medium (7-10wk)',
        'R19': 'Short (<=6wk)', 'R20': 'Long (>10wk)',
        'R21': 'Short (<=6wk)', 'R22': 'Medium (7-10wk)',
        'R23': 'Short (<=6wk)', 'R24': 'Long (>10wk)',
        'R26': 'Medium (7-10wk)', 'R27': 'Medium (7-10wk)',
        'R29': 'Short (<=6wk)', 'R30': 'Short (<=6wk)',
        'R31': 'Medium (7-10wk)',
    }
    dur_groups = {}
    for s in studies:
        rid = s['study_id']
        key = DURATION_MAP.get(rid, 'Unknown')
        dur_groups.setdefault(key, []).append(s)
    dur_order = ['Short (<=6wk)', 'Medium (7-10wk)', 'Long (>10wk)']
    dur_ordered = {k: dur_groups[k] for k in dur_order if k in dur_groups}
    run_subgroup("Subgroup 5: Intervention Duration", dur_ordered)

    # ============================================================
    # Subgroup 6: Participant Sex
    # ============================================================
    # From data_note
    sex_groups = {'Male': [], 'Female': [], 'Mixed': []}
    MALE_STUDIES = {'R01','R02','R03','R04','R06','R07','R08','R10','R12','R14','R15','R16','R17','R18','R20','R22','R23','R26','R27','R30'}
    FEMALE_STUDIES = {'R11','R13','R29'}
    MIXED_STUDIES = {'R05','R09','R19','R21','R31'}
    for s in studies:
        rid = s['study_id']
        if rid in MALE_STUDIES:
            sex_groups['Male'].append(s)
        elif rid in FEMALE_STUDIES:
            sex_groups['Female'].append(s)
        elif rid in MIXED_STUDIES:
            sex_groups['Mixed'].append(s)
    sex_ordered = {k: sex_groups[k] for k in ['Male', 'Female', 'Mixed'] if sex_groups[k]}
    run_subgroup("Subgroup 6: Participant Sex", sex_ordered)

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'='*65}")
    print(f"  Summary: All significant moderators")
    print(f"{'='*65}")
    print(f"  CMJ arm position is the primary pre-planned moderator.")
    print(f"  Consider meta-regression for continuous moderators (duration, age).")


if __name__ == "__main__":
    main()
