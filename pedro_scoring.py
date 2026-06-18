# -*- coding: utf-8 -*-
"""
PEDro scoring for 29 included studies.
Items 2-11 are scored (0-10 total). Item 1 (eligibility) is not scored.
We fill what we can from study-level data; items needing PDF review are flagged.
"""

import csv, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

# Load study data
with open('output/Table1_Study_Characteristics.csv', 'r', encoding='utf-8-sig') as f:
    studies = list(csv.DictReader(f))

# Load screening data for flags/notes
with open('screening_final.json', 'r', encoding='utf-8') as f:
    screen_data = json.load(f)

# Build pmid -> flag lookup
pmid_flags = {}
for item in screen_data:
    pmid = item.get('pmid', '')
    flag = item.get('flag', '')
    pmid_flags[pmid] = flag

# Load extraction master for notes
with open('data_extraction_FINAL.csv', 'r', encoding='utf-8-sig') as f:
    ext_data = list(csv.DictReader(f))

pmid_notes = {}
for row in ext_data:
    pmid_notes[row['pmid']] = row.get('extraction_notes', '')

# ── PEDro items ────────────────────────────────────────
# Item 1: eligibility criteria specified (NOT SCORED)
# Item 2: random allocation
# Item 3: concealed allocation
# Item 4: groups similar at baseline (prognostic indicators)
# Item 5: blinding of all subjects
# Item 6: blinding of all therapists
# Item 7: blinding of all assessors
# Item 8: >85% follow-up for at least one key outcome
# Item 9: intention-to-treat analysis (or all received allocated condition)
# Item 10: between-group statistical comparisons reported
# Item 11: point measures + measures of variability

PEDRO_ITEMS = [
    "1. Eligibility criteria specified (not scored)",
    "2. Random allocation",
    "3. Concealed allocation",
    "4. Groups similar at baseline",
    "5. Blinding of subjects",
    "6. Blinding of therapists",
    "7. Blinding of assessors",
    "8. >85% follow-up (key outcome)",
    "9. Intention-to-treat analysis",
    "10. Between-group comparisons reported",
    "11. Point measure + variability",
]

# ── Scoring logic ──────────────────────────────────────
def score_item2(study_name):
    """All 29 are described as RCTs -> YES (1)."""
    return 'Y', 'RCT design'

def score_item3(study_name):
    """Concealed allocation rarely reported in sports science. Default UNCLEAR."""
    return '?', 'Need PDF: check Methods for allocation concealment'

def parse_mean(val):
    """Parse mean from format like '32.6+-6.1' or '32.6±6.1' or '32.6'."""
    import re
    if not val:
        return None
    # Split on +-, ±, or space
    parts = re.split(r'[±\+\-\s]', str(val).strip())
    try:
        return float(parts[0])
    except (ValueError, IndexError):
        return None

def score_item4(pre_ig, post_ig, pre_cg, post_cg, n_ig, n_cg):
    """Baseline comparability: check if pre-test means are similar."""
    pig = parse_mean(pre_ig)
    pcg = parse_mean(pre_cg)
    if pig is None or pcg is None:
        return '?', 'Pre-test data missing or unparseable'
    if pig == 0 or pcg == 0:
        return '?', 'Pre-test mean is zero (likely missing)'
    diff_pct = abs(pig - pcg) / max(pig, pcg) * 100
    if diff_pct < 10:
        return 'Y', f'Pre diff {diff_pct:.1f}% (<10%)'
    else:
        return 'N', f'Pre diff {diff_pct:.1f}% (>=10%)'

def score_item5():
    """Exercise intervention: subjects know they are exercising. Always NO."""
    return 'N', 'Exercise study: subjects cannot be blinded'

def score_item6():
    """Exercise intervention: trainers know the protocol. Always NO."""
    return 'N', 'Exercise study: trainer cannot be blinded'

def score_item7(study_name):
    """CMJ assessor blinding depends on study. Need to check."""
    return '?', 'Need PDF: check if CMJ assessor was blinded'

def score_item8(n_total):
    """>85% follow-up. Check dropout from available data."""
    # Most studies don't report dropout in our extraction
    return '?', 'Need PDF: check dropout rate'

def score_item9(study_name):
    """ITT analysis. Rarely done in sports science."""
    return '?', 'Need PDF: check if ITT or per-protocol'

def score_item10():
    """Between-group comparisons: all report pre/post CMJ -> YES."""
    return 'Y', 'CMJ between-group data reported'

def score_item11():
    """Point + variability: all report Mean +- SD -> YES."""
    return 'Y', 'Mean +- SD reported'

# ── Score all studies ──────────────────────────────────
results = []
for s in studies:
    name = s['Study']
    n_total = s.get('n_Total', '?')
    n_ig = s.get('n_IG', '?')
    n_cg = s.get('n_CG', '?')
    pre_ig = s.get('CMJ_Pre_IG', '0')
    pre_cg = s.get('CMJ_Pre_CG', '0')
    arm = s.get('CMJ_Arm', '')
    device = s.get('CMJ_Device', '')

    row = {'Study': name, 'n': n_total, 'Arm': arm, 'Device': device}

    # Item 1 (not scored)
    row['I1'] = 'Y'
    row['I1_note'] = 'Eligibility stated in Methods'

    # Item 2
    v, note = score_item2(name); row['I2'] = v; row['I2_note'] = note

    # Item 3
    v, note = score_item3(name); row['I3'] = v; row['I3_note'] = note

    # Item 4
    v, note = score_item4(pre_ig, s.get('CMJ_Post_IG','0'), pre_cg, s.get('CMJ_Post_CG','0'), n_ig, n_cg)
    row['I4'] = v; row['I4_note'] = note

    # Item 5
    v, note = score_item5(); row['I5'] = v; row['I5_note'] = note

    # Item 6
    v, note = score_item6(); row['I6'] = v; row['I6_note'] = note

    # Item 7
    v, note = score_item7(name); row['I7'] = v; row['I7_note'] = note

    # Item 8
    v, note = score_item8(n_total); row['I8'] = v; row['I8_note'] = note

    # Item 9
    v, note = score_item9(name); row['I9'] = v; row['I9_note'] = note

    # Item 10
    v, note = score_item10(); row['I10'] = v; row['I10_note'] = note

    # Item 11
    v, note = score_item11(); row['I11'] = v; row['I11_note'] = note

    # Compute confirmed score (items 2-11, only Y counts)
    confirmed = sum(1 for k in ['I2','I3','I4','I5','I6','I7','I8','I9','I10','I11'] if row[k] == 'Y')
    uncertain = sum(1 for k in ['I2','I3','I4','I5','I6','I7','I8','I9','I10','I11'] if row[k] == '?')
    row['Confirmed'] = confirmed
    row['Uncertain'] = uncertain
    row['Potential_max'] = confirmed + uncertain

    results.append(row)

# ── Summary statistics ─────────────────────────────────
confirmed_scores = [r['Confirmed'] for r in results]
potential_maxes = [r['Potential_max'] for r in results]

print(f"PEDro Scoring Summary (n={len(results)} studies)")
print(f"  Confirmed score range:  {min(confirmed_scores)} - {max(confirmed_scores)}")
print(f"  Mean confirmed:         {np.mean(confirmed_scores):.1f}")
print(f"  Mean potential max:     {np.mean(potential_maxes):.1f}")
print(f"  Uncertain items range:  {min(r['Uncertain'] for r in results)} - {max(r['Uncertain'] for r in results)}")

# ── Save CSV ──────────────────────────────────────────
output_path = 'output/PEDro_Scores.csv'
with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
    fieldnames = ['Study','n','Arm','Device',
                  'I1','I1_note','I2','I2_note','I3','I3_note',
                  'I4','I4_note','I5','I5_note','I6','I6_note',
                  'I7','I7_note','I8','I8_note','I9','I9_note',
                  'I10','I10_note','I11','I11_note',
                  'Confirmed','Uncertain','Potential_max']
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for r in results:
        writer.writerow(r)

print(f"\nSaved: {output_path}")

# ── Print detailed table ───────────────────────────────
print(f"\n{'Study':<30s} {'Arm':<15s} {'I2':'>3s} {'I3':'>3s} {'I4':'>3s} {'I5':'>3s} {'I6':'>3s} {'I7':'>3s} {'I8':'>3s} {'I9':'>3s} {'I10':'>4s} {'I11':'>4s} {'Conf':'>5s} {'Max':'>4s}")
print("-" * 115)
for r in results:
    name = r['Study'][:28]
    arm_short = r['Arm'][:13]
    items = ''
    for k in ['I2','I3','I4','I5','I6','I7','I8','I9','I10','I11']:
        items += f' {r[k]:>3s}'
    print(f'{name:<30s} {arm_short:<15s}{items} {r["Confirmed"]:>5d} {r["Potential_max"]:>4d}')

# ── Save JSON for manuscript ───────────────────────────
with open('output/PEDro_Scores.json', 'w', encoding='utf-8') as f:
    json.dump({
        'items': PEDRO_ITEMS,
        'scoring_notes': {
            'I2': 'All 29 RCTs -> YES',
            'I3': 'Concealed allocation rarely reported in sports science',
            'I4': 'Baseline CMJ pre-test difference <10% -> YES',
            'I5': 'Exercise intervention -> impossible to blind subjects',
            'I6': 'Exercise intervention -> impossible to blind trainers',
            'I7': 'Assessor blinding varies -> NEED PDF REVIEW',
            'I8': 'Dropout/follow-up -> NEED PDF REVIEW',
            'I9': 'ITT analysis -> NEED PDF REVIEW',
            'I10': 'All report between-group CMJ -> YES',
            'I11': 'All report Mean +/- SD -> YES',
        },
        'summary': {
            'n_studies': len(results),
            'mean_confirmed': float(np.mean(confirmed_scores)),
            'mean_potential_max': float(np.mean(potential_maxes)),
            'confirmed_range': [int(min(confirmed_scores)), int(max(confirmed_scores))],
            'uncertain_items_per_study': int(np.mean([r['Uncertain'] for r in results])),
        },
        'studies': [{k: r[k] for k in ['Study','n','Arm','Device','I2','I3','I4','I5','I6','I7','I8','I9','I10','I11','Confirmed','Potential_max']} for r in results]
    }, f, ensure_ascii=False, indent=2)

print(f"Saved: output/PEDro_Scores.json")
