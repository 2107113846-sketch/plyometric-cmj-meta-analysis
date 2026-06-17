# -*- coding: utf-8 -*-
"""Map user's verified PEDro scores (P-numbers) to our R-numbered studies."""

import csv, sys, json
sys.stdout.reconfigure(encoding='utf-8')

# Verified PEDro scores from user's manual review
# Columns: P_num, first_author, I1-I11, total
# Items: 1.纳入条件 2.随机分配 3.分配隐藏 4.基线可比 5.受试者施盲 6.治疗师施盲
#        7.评估者施盲 8.随访≥85% 9.组间统计比较 10.点估计与变异指标 11.效应量与精确度量
# PEDro standard: items 2-11 count (10 total). User's "总分" counts items 1-11 (11 total).
# We will compute PEDro_standard = sum(I2:I11) for comparability with standard PEDro.

VERIFIED = [
    # P_num, author, I1,I2,I3,I4,I5,I6,I7,I8,I9,I10,I11, total_11
    ["P02", "Ramirez-Campillo",    1,1,0,1,0,0,0,1,1,1,0, 6],
    ["P03", "Ramirez-Campillo, Burgos", 1,1,0,1,0,0,0,1,1,1,1, 8],
    ["P04", "Ramirez-Campillo",    1,1,1,1,0,0,1,1,1,1,1, 9],
    ["P05", "Palma-Munoz",         1,1,1,1,0,0,1,1,1,1,1, 9],
    ["P06", "Ramirez-Campillo",    1,1,0,1,0,0,0,1,1,1,1, 8],
    ["P09", "Van Roie",            1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P12", "Chun-Hao Chang",      1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P18", "Asadi",               1,1,0,1,0,0,1,0,1,1,1, 7],
    ["P20", "Blazevich",           1,0,0,0,0,0,0,0,1,1,1, 3],
    ["P21", "Byrne",               1,1,0,1,0,0,0,1,1,1,1, 8],
    ["P22", "Silvia Sedano Campo", 1,1,0,1,0,0,0,1,1,1,0, 6],
    ["P39", "Idrizovic",           1,1,0,1,0,0,0,1,1,1,0, 7],
    ["P42", "Mohamed C. Jlid",     1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P43", "Jlid, Mohamed Chedly",1,1,0,1,0,0,0,1,1,1,1, 9],
    ["P45", "Khlifa",              1,1,0,1,0,0,1,1,1,1,1, 8],
    ["P47", "Kijowski",            1,1,0,1,0,0,0,1,1,1,0, 5],
    ["P51", "Cedric Laurent",      1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P55", "Michailidis",         1,1,0,1,0,0,0,1,1,1,0, 6],
    ["P58", "Negra",               1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P66", "Potdevin",            1,1,0,1,0,0,0,1,1,1,1, 7],
    ["P77", "Chun-Hao Chang",      1,1,0,1,0,0,0,1,1,1,1, 6],
    ["P78", "Eduardo J.A.M. Santos",1,1,0,1,0,0,0,1,1,1,0, 6],
    ["P82", "Van Roie",            1,1,0,1,0,0,0,1,1,1,1, 7],
    ["P83", "Vescovi",             1,1,0,1,0,0,0,1,1,1,0, 7],
    ["P89", "Yanci",               1,1,0,0,0,0,0,1,1,1,1, 7],
]

# Load our 29-study Table1
with open('output/Table1_Study_Characteristics.csv', 'r', encoding='utf-8-sig') as f:
    our_studies = list(csv.DictReader(f))

# Build name+year matching
def normalize_name(name):
    """Normalize for fuzzy matching."""
    name = name.lower().strip()
    # Remove periods, extra spaces
    import re
    name = re.sub(r'[.,]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name

def match_study(our_row):
    """Try to match our study to a verified PEDro entry."""
    our_author = normalize_name(our_row['Study'])
    our_year = our_row.get('Year', '')
    our_n = our_row.get('n_Total', '')

    for v in VERIFIED:
        v_auth = normalize_name(v[1])
        # Check if one name contains the other
        if v_auth in our_author or our_author in v_auth:
            return v
        # Also check first name parts
        our_parts = our_author.split()
        v_parts = v_auth.split()
        if our_parts and v_parts:
            if our_parts[0] == v_parts[0]:  # Same last name
                # Check year proximity (we don't have years in VERIFIED, skip)
                return v
    return None

# Map and report
mapped = []
unmapped = []

for i, s in enumerate(our_studies):
    v = match_study(s)
    if v:
        pedro_std = sum(v[3:13])  # I2 through I11 = 10 items
        mapped.append({
            'R': f'R{i+1:02d}',
            'Study': s['Study'],
            'Year': s.get('Year', '?'),
            'Arm': s.get('CMJ_Arm', ''),
            'n': s.get('n_Total', '?'),
            'P_num': v[0],
            'I1': v[2], 'I2': v[3], 'I3': v[4], 'I4': v[5],
            'I5': v[6], 'I6': v[7], 'I7': v[8], 'I8': v[9],
            'I9': v[10], 'I10': v[11], 'I11': v[12],
            'PEDro_std': pedro_std,
        })
    else:
        unmapped.append({
            'R': f'R{i+1:02d}',
            'Study': s['Study'],
            'Year': s.get('Year', '?'),
            'Arm': s.get('CMJ_Arm', ''),
            'n': s.get('n_Total', '?'),
        })

print(f"Mapped: {len(mapped)}/{len(our_studies)}")
print(f"Unmapped: {len(unmapped)}")

if unmapped:
    print("\n=== NEED MANUAL SCORING ===")
    for u in unmapped:
        print(f"  {u['R']}  {u['Study']:<30s}  Year={u['Year']}  n={u['n']}  Arm={u['Arm']}")

# Compute stats for mapped studies
scores = [m['PEDro_std'] for m in mapped]
print(f"\n=== PEDro Score Distribution (standard, out of 10) ===")
print(f"  Mean:   {sum(scores)/len(scores):.1f}")
print(f"  Median: {sorted(scores)[len(scores)//2]}")
print(f"  Range:  {min(scores)} - {max(scores)}")
print(f"  >=6 (good):     {sum(1 for s in scores if s >= 6)}/{len(scores)} ({100*sum(1 for s in scores if s>=6)/len(scores):.0f}%)")
print(f"  >=8 (excellent):{sum(1 for s in scores if s >= 8)}/{len(scores)} ({100*sum(1 for s in scores if s>=8)/len(scores):.0f}%)")
print(f"  <5 (poor):      {sum(1 for s in scores if s < 5)}/{len(scores)}")

# Item-level passing rates (standard PEDro items 2-11)
item_labels = ['I2:Random','I3:Conceal','I4:Baseline','I5:SubjBlind','I6:TherBlind',
               'I7:AssessBlind','I8:FollowUp','I9:ITT/Compl','I10:BetweenGrp','I11:PointVar']
for idx, label in enumerate(item_labels):
    item_key = f'I{idx+2}'
    passed = sum(1 for m in mapped if m[item_key] == 1)
    rate = passed / len(mapped) * 100
    bar = '█' * int(rate / 5) + '░' * (20 - int(rate / 5))
    print(f"  {label:<20s}: {passed:>2d}/{len(mapped)} ({rate:5.1f}%)  {bar}")

# Save mapped scores
with open('output/PEDro_Scores_Verified.csv', 'w', encoding='utf-8-sig', newline='') as f:
    fieldnames = ['R','Study','Year','Arm','n','P_num',
                  'I1','I2','I3','I4','I5','I6','I7','I8','I9','I10','I11','PEDro_std']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for m in mapped:
        writer.writerow(m)
print(f"\nSaved: output/PEDro_Scores_Verified.csv")

# Save unmapped list
with open('output/PEDro_Unmapped_Need_Manual.csv', 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['R','Study','Year','Arm','n'])
    writer.writeheader()
    for u in unmapped:
        writer.writerow(u)
print(f"Saved: output/PEDro_Unmapped_Need_Manual.csv")
