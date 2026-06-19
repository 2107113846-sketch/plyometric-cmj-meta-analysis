import csv

# ===== TASK 1: Total sample size =====
with open(r'D:\桌面\科研训练\analysis_ready_effects.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total_ig = sum(int(r['exp_n']) for r in rows)
total_cg = sum(int(r['ctrl_n']) for r in rows)
total_n = total_ig + total_cg

print('===== TASK 1: Total Sample Size =====')
print(f'Sum exp_n (IG): {total_ig}')
print(f'Sum ctrl_n (CG): {total_cg}')
print(f'Total N: {total_n}')
print(f'Manuscript claims: 390 IG + 342 CG = 732')
print(f'IG match: {total_ig} vs 390 -> {total_ig == 390}')
print(f'CG match: {total_cg} vs 342 -> {total_cg == 342}')
print(f'Sum match: {total_n} vs 732 -> {total_n == 732}')
print()

# ===== TASK 2: 29 vs 30 studies =====
print('===== TASK 2: Study Count 29 vs 30 =====')
study_ids = [r['study_id'] for r in rows]
print(f'Unique study_ids in analysis: {len(study_ids)}')
print(f'IDs: {study_ids}')

with open(r'D:\桌面\科研训练\screening_merged_30studies.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    screening_rows = list(reader)
# Use first fieldname regardless of encoding
fn0 = list(screening_rows[0].keys())[0]
screening_ids = [r[fn0] for r in screening_rows]
print(f'Study codes in screening: {len(screening_ids)}')
print(f'R25 present in screening: {"R25" in screening_ids}')
print(f'R28 present in screening: {"R28" in screening_ids}')

analysis_ids_set = set(study_ids)
print('Studies in screening NOT in analysis:')
for sid in screening_ids:
    if sid not in analysis_ids_set:
        print(f'  {sid}')
print()

# ===== TASK 3: PRISMA flow =====
print('===== TASK 3: PRISMA Flow =====')
print(f'Full text assessed: 91')
print(f'Excluded: 25+15+8+5+3+4 = 60')
print(f'Expected: 91 - 60 = 31, Included: 29')
print(f'Discrepancy: 2 studies (R25 Chang dup + R28 Van Roie dup) merged')
print()

# ===== TASK 4: R24 =====
print('===== TASK 4: R24 (Rubley 2011) =====')
with open(r'D:\桌面\科研训练\output\RevMan_ready_wide_pool.csv', 'r', encoding='utf-8-sig') as f:
    wide_rows = list(csv.DictReader(f))
print(f'Wide file columns: {list(wide_rows[0].keys())}')
r24_in_wide = any('Rubley' in r['Study'] for r in wide_rows)
print(f'R24 in wide pool RevMan: {r24_in_wide}')
with open(r'D:\桌面\科研训练\output\RevMan_ready_strict_pool.csv', 'r', encoding='utf-8-sig') as f:
    strict_rows = list(csv.DictReader(f))
r24_in_strict = any('Rubley' in r['Study'] for r in strict_rows)
print(f'R24 in strict pool RevMan: {r24_in_strict}')
r24_row = [r for r in rows if r['study_id'] == 'R24'][0]
print(f'R24 cmj_arm: {r24_row["cmj_arm"]}')
r24_wide = [r for r in wide_rows if 'Rubley' in r['Study']]
if r24_wide:
    print(f'R24 arm in wide pool: {r24_wide[0]["CMJ_Arm"]}')
    print(f'R24 weeks in wide pool: {r24_wide[0]["Weeks"]}')
    print(f'R24 g in wide pool: {r24_wide[0]["Hedges_g"]}')
print()

# ===== TASK 5: R19 SD estimation =====
print('===== TASK 5: R19 (Michailidis 2018) SD from CI =====')
r19 = [r for r in rows if r['study_id'] == 'R19'][0]
print(f'R19 IG n={r19["exp_n"]}, post_mean={r19["exp_post_mean"]}, post_sd={r19["exp_post_sd"]}')
print(f'R19 CG n={r19["ctrl_n"]}, post_mean={r19["ctrl_post_mean"]}, post_sd={r19["ctrl_post_sd"]}')
print(f'R19 pre IG: mean={r19["exp_pre_mean"]}, sd={r19["exp_pre_sd"]}')
print(f'R19 pre CG: mean={r19["ctrl_pre_mean"]}, sd={r19["ctrl_pre_sd"]}')
print(f'ALL four SD values = 0.80 -- suspicious uniformity')
print(f'note says: CI_width/3.92 approx 0.80')
print(f'If CI_width/3.92 = 0.80, this equals the SE')
print(f'  Actual SD_IG would be: 0.80 * sqrt(17) = {0.80 * (17**0.5):.2f}')
print(f'  Actual SD_CG would be: 0.80 * sqrt(14) = {0.80 * (14**0.5):.2f}')
print(f'WARNING: 0.80 appears to be SE stored as SD. This inflates the effect size.')
# Let me verify what g would be with real SD
# change score: g_change = (delta_IG - delta_CG) / pooled_change_SD * correction
# delta_IG = 22.19-21.73 = 0.46, delta_CG = 21.56-22.04 = -0.48
# If SD is actually SE, the real pooled_change SD would be much larger
# The g of 1.477 might be inflated
print(f'IMPACT: If SD=SE=0.80, real SD~3.0, effect size would be much smaller')
print()

# ===== TASK 6: R27 extreme values =====
print('===== TASK 6: R27 (Toumi 2004) Extreme Effect Sizes =====')
r27 = [r for r in rows if r['study_id'] == 'R27'][0]
print(f'R27 yi_change: {r27["yi_change"]} (used in analysis)')
print(f'R27 yi_post: {r27["yi_post"]} (post-only)')
print(f'R27 sei_change: {r27["sei_change"]}')
print(f'R27 sei_post: {r27["sei_post"]}')
# Verify SE for yi_post approx 0.911
se_post_verify = (1/12 + 1/6 + 4.661**2/(2*18))**0.5
print(f'SE post verify: sqrt(1/12+1/6+4.66^2/36) = {se_post_verify:.4f}')
print(f'Change score g=2.94 used. Post-only g=4.66 is even more extreme')
print(f'Analysis correctly identifies and removes R27 as outlier')
print()

# ===== TASK 7: Overlapping samples =====
print('===== TASK 7: Overlapping Samples =====')
ramirez = [r for r in rows if 'Ramirez-Campillo' in r['author']]
print(f'Ramirez-Campillo entries in analysis: {len(ramirez)}')
for r in ramirez:
    n = int(r['exp_n']) + int(r['ctrl_n'])
    print(f'  {r["study_id"]} ({r["year"]}): n={r["exp_n"]}+{r["ctrl_n"]}={n}, arm={r["cmj_arm"]}')
print(f'R28 (Van Roie dup) in analysis: {any(r["study_id"] == "R28" for r in rows)}')
# Check if any study appears twice under different IDs
ids_from_screening_not_in_analysis = [sid for sid in screening_ids if sid not in analysis_ids_set]
print(f'IDs in screening but not analysis: {ids_from_screening_not_in_analysis}')
print()

# ===== TASK 8: Arm classification cross-check =====
print('===== TASK 8: Arm Position Classification Cross-check =====')
arm_map = {r['study_id']: r['cmj_arm'] for r in rows}

# All studies with their arm classifications
print('Complete arm classification audit:')
for r in rows:
    sid = r['study_id']
    arm = r['cmj_arm']
    note = r['data_note'][:80] if 'data_note' in r else ''
    print(f'  {sid}: arm="{arm}" | {note}')

# Check strict pool members
print()
print('STUDY COUNTS CHECK:')
print(f'  Strict pool files: {len(strict_rows)}')
print(f'  Wide pool files: {len(wide_rows)}')
print(f'  Expected strict: 16, Expected wide: 28 (excl R24)')

# But R24 IS in the wide pool file -- let's check
r24_in_wide_check = any('Rubley' in r['Study'] for r in wide_rows)
print(f'  R24 in wide pool: {r24_in_wide_check}')
print(f'  If R24 in wide pool: wide pool = {len(wide_rows)} (should be 28 without R24)')
# Actually let me recount: 29 in analysis - 1 (R24 VJ) = 28 wide
# But wide file has 29 rows (28 + R24)
# So wide file = 29 rows including R24? Let's check
print(f'  Wide pool rows = {len(wide_rows)}')

# Subgroup k-count verification
print()
print('===== SUBGROUP K-COUNT VERIFICATION =====')
# Report says: Short 14, Medium 10, Long 4 = 28 (wide pool)
# But earlier analysis found: Short 15, Medium 9, Long 4 = 28
# R24 is in wide pool with 14 weeks, so wide pool = 29 rows including R24
# If excluding R24: total = 28

# Let me recount all weeks
print('Week assignments from wide pool:')
short_count = 0
medium_count = 0
long_count = 0
for r in wide_rows:
    w = int(r['Weeks'])
    study_name = r['Study']
    if w <= 6:
        cat = 'SHORT'
        short_count += 1
    elif w <= 10:
        cat = 'MEDIUM'
        medium_count += 1
    else:
        cat = 'LONG'
        long_count += 1
    print(f'  {study_name}: {w} weeks -> {cat}')

print(f'\nShort (<=6): {short_count}')
print(f'Medium (7-10): {medium_count}')
print(f'Long (>10): {long_count}')
print(f'Total: {short_count + medium_count + long_count}')

# Count WITHOUT R24
short_no_r24 = 0
medium_no_r24 = 0
long_no_r24 = 0
for r in wide_rows:
    if 'Rubley' in r['Study']:
        continue
    w = int(r['Weeks'])
    if w <= 6:
        short_no_r24 += 1
    elif w <= 10:
        medium_no_r24 += 1
    else:
        long_no_r24 += 1
print(f'Excluding R24: Short={short_no_r24}, Medium={medium_no_r24}, Long={long_no_r24}')
print(f'Total excl R24: {short_no_r24 + medium_no_r24 + long_no_r24}')
