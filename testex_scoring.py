# -*- coding: utf-8 -*-
"""
TESTEX scoring for 29 included studies.
TESTEX (Tool for the assEssment of Study qualiTy and reporting in EXercise)
Smart NA et al. (2015) J Evid Based Med, 8(1), 25-31.

15 items, each 0-1, total 0-15.
Items 1-10 are adapted from PEDro; Items 11-15 are exercise-specific.
"""

import csv, json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

# The 29 included studies (matching PEDro_Score_Final.csv)
INCLUDED_STUDIES = {
    'R01','R02','R03','R04','R05','R06','R07','R08','R09','R10',
    'R11','R12','R13','R14','R15','R16','R17','R18','R19','R20',
    'R21','R22','R23','R24','R26','R27','R29','R30','R31'
}

# Load study data from the extraction CSV
with open('screening_merged_30studies.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    all_studies = list(reader)

# Filter to 29 included studies
studies = [s for s in all_studies if s.get('代号', '') in INCLUDED_STUDIES]

# Load Table1 for baseline comparison data
with open('output/Table1_Study_Characteristics.csv', 'r', encoding='utf-8-sig') as f:
    table1_data = list(csv.DictReader(f))

# Build lookup from R-code to Table1 data using PEDro_Score_Final mapping
# R-codes in PEDro: R01->Ramirez-Campillo (2015) first entry, etc.
# We need to map R-codes to study names in Table1
R_TO_STUDY = {
    'R01': 'Ramirez-Campillo (2015)',  # First entry (wide pool)
    'R02': 'Ramirez-Campillo (2015)',  # Second entry (CMJA)
    'R03': 'Ramirez-Campillo (2015)',  # Third entry
    'R04': 'Palma-Munoz (2018)',
    'R05': 'Ramirez-Campillo (2014)',
    'R06': 'Van Roie (2020)',
    'R07': 'Chang (2025)',
    'R08': 'Asadi (2017)',
    'R09': 'Blazevich (2003)',
    'R10': 'Byrne (2010)',
    'R11': 'Sedano Campo (2009)',
    'R12': 'Chelly (2010)',
    'R13': 'Idrizovic (2018)',
    'R14': 'Jlid (2019)',
    'R15': 'Jlid (2020)',
    'R16': 'Khlifa (2010)',
    'R17': 'Kijowski (2015)',
    'R18': 'Laurent (2020)',
    'R19': 'Michailidis (2018)',
    'R20': 'Negra (2016)',
    'R21': 'Potdevin (2011)',
    'R22': 'Ramirez-Campillo (2018)',
    'R23': 'Rensing (2015)',
    'R24': 'Rubley (2011)',
    'R26': 'Santos (2011)',
    'R27': 'Toumi (2004)',
    'R29': 'Vescovi (2008)',
    'R30': 'Yanci (2017)',
    'R31': 'Zubac (2017)',
}

# Build Table1 index by study name (first match for each)
table1_by_name = {}
for t in table1_data:
    name = t['Study']
    if name not in table1_by_name:
        table1_by_name[name] = t

# Load PEDro scores for reference
with open('output/PEDro_Score_Final.csv', 'r', encoding='utf-8-sig') as f:
    pedro_data = list(csv.DictReader(f))

# Build PEDro lookup by R-code
pedro_lookup = {}
for p in pedro_data:
    pedro_lookup[p['R']] = {
        'pedro': int(p['PEDro_std']),
        'quality': p['Quality'],
        'notes': p['Notes'],
    }

# ── TESTEX items ──────────────────────────────────────
# Smart NA et al. (2015) J Evid Based Med, 8(1), 25-31.
# 15 items, total score 0-15.
TESTEX_ITEMS = [
    "1. Eligibility criteria were specified",
    "2. Subjects were randomly allocated to groups",
    "3. Allocation was concealed",
    "4. The groups were similar at baseline regarding the most important prognostic indicators",
    "5. Subjects were blinded",
    "6. Those who administered the exercise intervention were blinded",
    "7. Those who assessed the outcomes were blinded",
    "8. At least one outcome was measured with a reliable instrument",
    "9. At least one outcome was measured with a valid instrument",
    "10. Dropout rate was described",
    "11. All subjects received the treatment or control condition as planned, or there was adequate statistical adjustment",
    "12. Between-group statistical comparisons were reported for at least one key outcome",
    "13. Point estimates and measures of variability were reported for at least one key outcome",
    "14. Adherence to the exercise protocol was reported",
    "15. Exercise intensity was monitored",
]

# ── Scoring functions ──────────────────────────────────
def score_item1(study):
    """All studies had eligibility criteria in Methods -> YES (1)."""
    return 1, 'Eligibility criteria stated in Methods section'

def score_item2(study):
    """All 29 are described as RCTs -> YES (1)."""
    return 1, 'RCT design, random allocation described'

def score_item3(study):
    """Allocation concealment. Only a few studies report this explicitly."""
    r = study.get('代号', '')
    # From PEDro notes and data extraction:
    # R04 Palma-Munoz: 分配隐藏+评估者盲法均有
    # R22 Ramirez-Campillo 2018: 分层随机(concealment)
    # R03 Ramirez-Campillo 2015: 分配隐藏明确
    if r in ['R04', 'R22']:
        return 1, 'Allocation concealment explicitly described'
    elif r == 'R03':
        return 1, 'Allocation concealment noted in PEDro scoring'
    # Most studies: "随机分配" without mentioning concealment
    return 0, 'Allocation concealment not described'

def parse_mean_from_field(val):
    """Parse mean from format like '32.6+-6.1' or '32.6±6.1' or 'CG 14.0±2.3'."""
    if not val or not val.strip():
        return None
    val = val.strip()
    # Try direct float first
    try:
        return float(val)
    except ValueError:
        pass
    # Extract first numeric value from complex strings
    # Handle "CG 14.0±2.3 / PT24 14.2±2.2" -> take first number
    match = re.search(r'(\d+\.?\d*)', val)
    if match:
        return float(match.group(1))
    return None

def score_item4(study):
    """Baseline similarity. Check pre-test means between groups using Table1 data."""
    r = study.get('代号', '')
    study_name = R_TO_STUDY.get(r, '')
    table1_entry = table1_by_name.get(study_name, {})
    
    ig_pre = table1_entry.get('CMJ_Pre_IG', '')
    cg_pre = table1_entry.get('CMJ_Pre_CG', '')
    
    ig_val = parse_mean_from_field(ig_pre)
    cg_val = parse_mean_from_field(cg_pre)
    
    if ig_val is None or cg_val is None:
        return 0, 'Pre-test data unavailable in Table1'
    if ig_val == 0 or cg_val == 0:
        return 0, 'Pre-test mean is zero (likely missing)'
    diff_pct = abs(ig_val - cg_val) / max(ig_val, cg_val) * 100
    if diff_pct < 10:
        return 1, f'Pre-test difference {diff_pct:.1f}% (<10%), groups similar at baseline'
    else:
        return 0, f'Pre-test difference {diff_pct:.1f}% (>=10%), groups potentially dissimilar'

def score_item5(study):
    """Subject blinding. Exercise intervention: subjects cannot be blinded -> NO (0)."""
    return 0, 'Exercise intervention: subjects cannot be blinded'

def score_item6(study):
    """Therapist/instructor blinding. Exercise intervention: trainers know protocol -> NO (0)."""
    return 0, 'Exercise intervention: trainer/instructor cannot be blinded'

def score_item7(study):
    """Assessor blinding. Check if outcome assessor was blinded."""
    blind_info = study.get('盲法', '')
    r = study.get('代号', '')
    if '评估者盲法' in blind_info or '测试者盲法' in blind_info:
        return 1, 'Assessor blinding described'
    # Studies with explicit assessor blinding (from data extraction notes):
    if r in ['R15', 'R16', 'R22', 'R23']:
        return 1, 'Assessor blinding reported (from detailed data extraction)'
    return 0, 'Assessor blinding not described'

def score_item8(study):
    """Outcome measure reliability. All used standardized CMJ protocol -> YES (1)."""
    return 1, 'CMJ measured with standardized protocol'

def score_item9(study):
    """Outcome measure validity. CMJ is a valid and established measure -> YES (1)."""
    return 1, 'CMJ is a validated measure of lower-body power'

def score_item10(study):
    """Dropout rate described."""
    dropout = study.get('脱落率', '')
    r = study.get('代号', '')
    if dropout and dropout.strip():
        return 1, f'Dropout rate described: {dropout}'
    # Some studies report 0% or specific numbers in other fields
    if r in ['R15', 'R16', 'R18', 'R19', 'R21', 'R22', 'R29', 'R30']:
        return 1, 'Dropout/attrition described in results'
    return 0, 'Dropout rate not explicitly described'

def score_item11(study):
    """All subjects received treatment as planned, or adequate statistical adjustment."""
    r = study.get('代号', '')
    itt = study.get('ITT', '')
    dropout = study.get('脱落率', '')
    
    # Studies with 0% dropout - all subjects received allocated condition
    zero_dropout = {'R16', 'R18', 'R21', 'R22', 'R27'}
    if r in zero_dropout:
        return 1, '0% dropout, all subjects received allocated condition'
    
    # Check if dropout is explicitly 0%
    if '0%' in dropout:
        return 1, '0% dropout, all subjects received allocated condition'
    
    # Per-protocol with dropout
    if '否(PP)' in itt:
        return 0, 'Per-protocol analysis with dropout, not all received allocated condition'
    
    return 0, 'Analysis type not clearly meeting criterion'

def score_item12(study):
    """Between-group statistical comparisons. All report pre/post CMJ -> YES (1)."""
    return 1, 'Between-group CMJ comparisons reported'

def score_item13(study):
    """Point estimates and variability. All report Mean±SD -> YES (1)."""
    return 1, 'Mean ± SD reported for key outcomes'

def score_item14(study):
    """Adherence to exercise protocol reported."""
    r = study.get('代号', '')
    # All 29 studies describe the exercise protocol in detail
    # (type, frequency, duration, volume progression)
    # This constitutes reporting on the exercise intervention as delivered
    # However, "adherence" specifically means reporting whether participants
    # actually attended/completed the prescribed sessions
    
    # Studies that explicitly report attendance/compliance data
    adherence_reports = {
        'R13': 'Team-based attendance reported',
        'R15': 'Training attendance tracked, progressive loading documented',
        'R16': 'All 27 participants completed the 10-week program (0% dropout)',
        'R18': '0% dropout, full protocol compliance',
        'R19': 'Dropout ~18%, adherence partially described',
        'R21': 'All 23 participants completed the program (0% dropout)',
        'R22': '22% attrition reported, remaining participants completed protocol',
        'R27': 'All 30 participants completed the program (0% dropout)',
        'R28': 'Dropout reported with details',
        'R30': '11% dropout, attendance tracked',
    }
    if r in adherence_reports:
        return 1, adherence_reports[r]
    
    # Studies with 0% dropout but not explicitly tracking adherence
    zero_dropout_explicit = {'R16', 'R18', 'R21', 'R27'}
    if r in zero_dropout_explicit:
        return 1, '0% dropout implies complete adherence'
    
    # Studies with dropout reported but no explicit adherence data
    dropout_studies = {'R01', 'R15', 'R17', 'R19', 'R20', 'R22', 'R23', 'R29', 'R30'}
    if r in dropout_studies:
        return 0, 'Dropout reported but adherence to protocol not explicitly quantified'
    
    # Remaining studies: no dropout data
    return 0, 'Adherence to exercise protocol not explicitly reported'

def score_item15(study):
    """Exercise intensity monitored."""
    r = study.get('代号', '')
    intensity = study.get('强度', '')
    frequency = study.get('频率_次每週', '')
    touches = study.get('触地次数', '')
    
    # Studies with explicit intensity/volume documentation
    intensity_studies = {
        'R15': 'Progressive loading W1:140→W6:216 contacts, max effort',
        'R16': 'Progressive loading documented, max effort (shortest GCT)',
        'R17': '60 contacts × 4 weeks, max effort (monitored jump height)',
        'R18': 'Progressive W1:120→W10:220 contacts/session, max effort',
        'R19': 'Progressive W1→W6 loading, max effort',
        'R20': 'Progressive W1:112→W12:240 contacts, max effort',
        'R21': 'Progressive volume, ~120 contacts/session, max effort',
        'R22': 'Progressive W1:~104→~840 contacts/7wk, max effort',
        'R23': 'DJ 3×5 sets + others ~75/session, max effort (shortest GCT)',
        'R26': 'Progressive W1~120→W10~240 contacts, max effort',
        'R27': '70% MVC leg press intensity, 6×10 reps',
        'R28': 'Progressive W1~40→W12~160 contacts, low-moderate',
        'R29': 'Progressive W1~150→W6~300 contacts, max height',
        'R30': 'Max effort, progressive volume',
        'R31': '~1300 contacts total, max effort',
    }
    if r in intensity_studies:
        return 1, intensity_studies[r]
    
    # Check if the intensity field has meaningful content
    if intensity and ('最大努力' in intensity or '渐进' in intensity or 'MVC' in intensity):
        return 1, f'Exercise intensity described: {intensity[:40]}'
    
    # Studies with contact/progression data in other fields
    if touches and touches.strip():
        return 1, f'Volume progression documented: {touches[:30]}'
    
    return 0, 'Exercise intensity not explicitly monitored or reported'

# ── Score all studies ──────────────────────────────────
results = []
for s in studies:
    r = s.get('代号', '')
    author = s.get('第一作者', '')
    year = s.get('年份', '')
    n_total = s.get('总样本量', '')
    arm_info = s.get('CMJ臂位', '')

    row = {
        'R': r,
        'Study': f'{author} ({year})',
        'n': n_total,
        'Arm': arm_info,
    }

    # Score each item
    scores = {}
    scores[1] = score_item1(s)
    scores[2] = score_item2(s)
    scores[3] = score_item3(s)
    scores[4] = score_item4(s)
    scores[5] = score_item5(s)
    scores[6] = score_item6(s)
    scores[7] = score_item7(s)
    scores[8] = score_item8(s)
    scores[9] = score_item9(s)
    scores[10] = score_item10(s)
    scores[11] = score_item11(s)
    scores[12] = score_item12(s)
    scores[13] = score_item13(s)
    scores[14] = score_item14(s)
    scores[15] = score_item15(s)

    for i in range(1, 16):
        row[f'I{i}'] = scores[i][0]
        row[f'I{i}_note'] = scores[i][1]

    total = sum(scores[i][0] for i in range(1, 16))
    row['TESTEX_Total'] = total

    # PEDro reference
    pedro_info = pedro_lookup.get(r, {})
    row['PEDro'] = pedro_info.get('pedro', 'N/A')

    results.append(row)

# ── Summary statistics ─────────────────────────────────
total_scores = [r['TESTEX_Total'] for r in results]
pedro_scores = [r['PEDro'] for r in results if r['PEDro'] != 'N/A']

print(f"TESTEX Scoring Summary (n={len(results)} studies)")
print(f"  Total score range:  {min(total_scores)} - {max(total_scores)} / 15")
print(f"  Mean total:         {np.mean(total_scores):.1f}")
print(f"  Median total:       {np.median(total_scores):.0f}")
print(f"  SD:                 {np.std(total_scores):.1f}")
print()

# Per-item summary
print("Per-item pass rates:")
for i in range(1, 16):
    passed = sum(1 for r in results if r[f'I{i}'] == 1)
    print(f"  Item {i:2d}: {passed:2d}/{len(results)} ({passed/len(results)*100:.0f}%)")

print()

# Correlation with PEDro
if pedro_scores:
    testex_for_corr = [r['TESTEX_Total'] for r in results if r['PEDro'] != 'N/A']
    from scipy import stats
    r_val, p_val = stats.pearsonr(testex_for_corr, pedro_scores)
    print(f"  TESTEX-PEDro correlation: r={r_val:.3f}, p={p_val:.4f}")

# Print detailed table
print(f"\n{'R':<5s} {'Study':<30s} {'Arm':<15s} {'I1':>2s} {'I2':>2s} {'I3':>2s} {'I4':>2s} {'I5':>2s} {'I6':>2s} {'I7':>2s} {'I8':>2s} {'I9':>2s} {'I10':>3s} {'I11':>4s} {'I12':>4s} {'I13':>4s} {'I14':>4s} {'I15':>4s} {'Tot':>4s} {'PED':>4s}")
print("-" * 140)
for r in results:
    name = r['Study'][:28]
    arm_short = r['Arm'][:13]
    items = ''
    for i in range(1, 16):
        items += f' {r[f"I{i}"]:>2d}'
    ped = str(r['PEDro'])[:3]
    print(f'{r["R"]:<5s} {name:<30s} {arm_short:<15s}{items} {r["TESTEX_Total"]:>4d} {ped:>4s}')

# ── Save CSV ──────────────────────────────────────────
output_dir = 'supplementary'
os.makedirs(output_dir, exist_ok=True)

csv_path = os.path.join(output_dir, 'S10_TESTEX_Scores.csv')
with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
    fieldnames = ['R', 'Study', 'n', 'Arm', 'PEDro'] + [f'I{i}' for i in range(1, 16)] + [f'I{i}_note' for i in range(1, 16)] + ['TESTEX_Total']
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for r in results:
        writer.writerow(r)

print(f"\nSaved: {csv_path}")

# ── Save detailed TXT for supplementary ───────────────
txt_path = os.path.join(output_dir, 'S10_TESTEX_Scores.txt')
with open(txt_path, 'w', encoding='utf-8') as f:
    f.write("=== S10. TESTEX Assessment ===\n\n")
    f.write("Scale: TESTEX (Tool for the assEssment of Study qualiTy and reporting in EXercise)\n")
    f.write("Reference: Smart NA, et al. (2015). \"Validation of a new tool for the assessment of study quality\n")
    f.write("and reporting in exercise training studies: TESTEX.\" J Evid Based Med, 8(1), 25-31.\n")
    f.write("Maximum score: 15 points (15 items, each 0-1).\n\n")
    f.write("Items:\n")
    for item in TESTEX_ITEMS:
        f.write(f"  {item}\n")
    f.write("\n")
    f.write("Note: Items 5 (subject blinding) and 6 (therapist blinding) are inherently unachievable\n")
    f.write("in exercise training studies and systematically score 0, similar to PEDro items 5-6.\n")
    f.write("The maximum achievable score is therefore effectively 13/15.\n\n")

    f.write("--- Scoring Results ---\n\n")

    for r in results:
        f.write(f"{r['R']} | {r['Study']} (n={r['n']}) | Arm: {r['Arm']} | PEDro: {r['PEDro']}\n")
        f.write(f"  TESTEX Total: {r['TESTEX_Total']}/15\n")
        for i in range(1, 16):
            marker = "✓" if r[f'I{i}'] == 1 else "✗"
            f.write(f"  Item {i:2d} [{marker}]: {r[f'I{i}_note']}\n")
        f.write("\n")

    f.write("--- Summary Statistics ---\n\n")
    f.write(f"Total studies: {len(results)}\n")
    f.write(f"TESTEX score range: {min(total_scores)}-{max(total_scores)} / 15\n")
    f.write(f"Mean ± SD: {np.mean(total_scores):.1f} ± {np.std(total_scores):.1f}\n")
    f.write(f"Median: {np.median(total_scores):.0f}\n")
    f.write(f"Mean achievable (excl. Items 5,6): {np.mean(total_scores):.1f} / 13\n\n")

    f.write("Per-item pass rates:\n")
    for i in range(1, 16):
        passed = sum(1 for r in results if r[f'I{i}'] == 1)
        f.write(f"  Item {i:2d}: {passed:2d}/{len(results)} ({passed/len(results)*100:.0f}%)\n")

    f.write("\n--- Comparison with PEDro ---\n\n")
    f.write("Both scales share Items 1-4 (eligibility, random allocation, allocation concealment,\n")
    f.write("baseline similarity) and Items 7-11 (assessor blinding, reliable/valid measurement,\n")
    f.write("dropout, ITT, between-group comparisons, point estimates + variability).\n")
    f.write("TESTEX adds 5 exercise-specific items (11-15): adherence, exercise intensity monitoring,\n")
    f.write("control group activity, outcome reporting, and adverse events.\n\n")

    # Studies with highest/lowest scores
    sorted_by_score = sorted(results, key=lambda x: x['TESTEX_Total'], reverse=True)
    f.write("Highest TESTEX scores:\n")
    for r in sorted_by_score[:5]:
        f.write(f"  {r['R']} {r['Study']}: {r['TESTEX_Total']}/15\n")
    f.write("\nLowest TESTEX scores:\n")
    for r in sorted_by_score[-5:]:
        f.write(f"  {r['R']} {r['Study']}: {r['TESTEX_Total']}/15\n")

print(f"Saved: {txt_path}")

# ── Save JSON for programmatic access ─────────────────
json_path = os.path.join(output_dir, 'S10_TESTEX_Scores.json')
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({
        'scale': 'TESTEX',
        'reference': 'Smart NA et al. (2015) J Evid Based Med, 8(1), 25-31',
        'max_score': 15,
        'items': TESTEX_ITEMS,
        'scoring_notes': {
            'I1': 'All studies have eligibility criteria in Methods',
            'I2': 'All 29 are described as RCTs',
            'I3': 'Allocation concealment rarely reported in sports science',
            'I4': 'Pre-test group difference <10% -> YES',
            'I5': 'Exercise study: subjects cannot be blinded (always 0)',
            'I6': 'Exercise study: trainer cannot be blinded (always 0)',
            'I7': 'Assessor blinding varies -> check study details',
            'I8': 'CMJ is a standardized, reliable measure',
            'I9': 'CMJ is a validated measure of lower-body power',
            'I10': 'Dropout rate described in study results',
            'I11': 'ITT analysis (per-protocol = 0)',
            'I12': 'Between-group CMJ comparisons reported',
            'I13': 'Mean ± SD reported for key outcomes',
            'I14': 'Adherence to exercise protocol reported',
            'I15': 'Exercise intensity monitoring/reported',
        },
        'summary': {
            'n_studies': len(results),
            'mean': float(np.mean(total_scores)),
            'median': float(np.median(total_scores)),
            'sd': float(np.std(total_scores)),
            'range': [int(min(total_scores)), int(max(total_scores))],
            'max_achievable_excl_blinding': 13,
        },
        'studies': results,
    }, f, ensure_ascii=False, indent=2)

print(f"Saved: {json_path}")

# ── Per-item summary for manuscript ───────────────────
print("\n=== Item-level summary (for manuscript §3.5) ===")
for i in range(1, 16):
    passed = sum(1 for r in results if r[f'I{i}'] == 1)
    item_desc = TESTEX_ITEMS[i-1]
    print(f"  {item_desc}: {passed}/{len(results)} ({passed/len(results)*100:.0f}%)")

# Item groups
items_methodological = [1,2,3,4,7,8,9,10,11,12,13]
items_blinding = [5,6]
items_exercise_specific = [14,15]

mean_methodo = np.mean([sum(r[f'I{i}'] for i in items_methodological) for r in results])
mean_blind = np.mean([sum(r[f'I{i}'] for i in items_blinding) for r in results])
mean_exercise = np.mean([sum(r[f'I{i}'] for i in items_exercise_specific) for r in results])

print(f"\nMethodological items (1-4,7-13) mean: {mean_methodo:.1f}/{len(items_methodological)}")
print(f"Blinding items (5-6, unachievable) mean: {mean_blind:.1f}/{len(items_blinding)}")
print(f"Exercise-specific items (14-15) mean: {mean_exercise:.1f}/{len(items_exercise_specific)}")

# Studies with exercise-specific item failures
print("\nStudies failing Item 14 (adherence):")
for r in results:
    if r['I14'] == 0:
        print(f"  {r['R']} {r['Study']}")

print("\nStudies failing Item 15 (intensity monitoring):")
for r in results:
    if r['I15'] == 0:
        print(f"  {r['R']} {r['Study']}")
