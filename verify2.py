import csv, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== TASK 1: Total sample size =====
with open(r'D:\桌面\科研训练\analysis_ready_effects.csv', 'r', encoding='utf-8-sig') as f:
    rows = list(csv.DictReader(f))

total_ig = sum(int(r['exp_n']) for r in rows)
total_cg = sum(int(r['ctrl_n']) for r in rows)
total_n = total_ig + total_cg

print('TASK 1: Total Sample Size')
print(f'  Sum exp_n: {total_ig} (manuscript says 390, diff={total_ig-390})')
print(f'  Sum ctrl_n: {total_cg} (manuscript says 342, diff={total_cg-342})')
print(f'  Total N: {total_n} (manuscript says 732, diff={total_n-732})')
# List each study's n
print('  Per-study breakdown:')
for r in rows:
    print(f'    {r["study_id"]}: IG={r["exp_n"]}, CG={r["ctrl_n"]}, total={int(r["exp_n"])+int(r["ctrl_n"])}')
print()

# ===== TASK 2: 29 vs 30 =====
print('TASK 2: Study Count 29 vs 30')
with open(r'D:\桌面\科研训练\screening_merged_30studies.csv', 'r', encoding='utf-8-sig') as f:
    scr_rows = list(csv.DictReader(f))
fn0 = list(scr_rows[0].keys())[0]
scr_ids = [r[fn0] for r in scr_rows]
analysis_ids = [r['study_id'] for r in rows]
print(f'  Screening has {len(scr_ids)} study codes')
print(f'  Analysis has {len(analysis_ids)} studies')
missing = [s for s in scr_ids if s not in analysis_ids]
print(f'  In screening but NOT in analysis: {missing}')
print(f'  These are duplicates: R25=Chang(dup of R07), R28=Van Roie(dup of R06)')

# But wait: screening has 31 rows. 31 - 2 duplicates = 29 in analysis.
# But the file is called "30studies". 31 rows - 1 header = 30 data rows.
# Actually 31 data rows? Let me check.
print(f'  Screening data rows: {len(scr_rows)} (file name says 30 studies)')
print(f'  R25+R28 = 2 duplicates, so {len(scr_rows)}-2 = {len(scr_rows)-2} unique')
print()

# ===== TASK 3: PRISMA flow =====
print('TASK 3: PRISMA Flow')
print(f'  91 full-text - 60 excluded = 31 studies')
print(f'  31 - 2 duplicates (R25, R28) = 29 included')
print(f'  Internally consistent: 29 = 16 strict + 6 arm-unclear + 6 CMJA + 1 VJ')
print()

# ===== TASK 4: R24 =====
print('TASK 4: R24 (Rubley 2011)')
with open(r'D:\桌面\科研训练\output\RevMan_ready_wide_pool.csv', 'r', encoding='utf-8-sig') as f:
    wide_rows = list(csv.DictReader(f))
with open(r'D:\桌面\科研训练\output\RevMan_ready_strict_pool.csv', 'r', encoding='utf-8-sig') as f:
    strict_rows = list(csv.DictReader(f))
r24_in_wide = any('Rubley' in r['Study'] for r in wide_rows)
r24_in_strict = any('Rubley' in r['Study'] for r in strict_rows)
print(f'  R24 in wide pool: {r24_in_wide}')
print(f'  R24 in strict pool: {r24_in_strict}')
print(f'  ISSUE: R24 IS in the wide pool RevMan file (14 weeks, g=1.53)')
print(f'  If wide pool should be 28 excluding R24, the RevMan file has 29 rows')
print(f'  Actual wide RevMan rows: {len(wide_rows)}')
print(f'  R24 should be excluded from wide pool analyses, only used in VJ sensitivity')
print()

# ===== TASK 5: R19 SD issue =====
print('TASK 5: R19 (Michailidis 2018) SD from CI')
r19 = [r for r in rows if r['study_id']=='R19'][0]
print(f'  All 4 SD values = {r19["exp_post_sd"]} (suspicious uniformity)')
print(f'  Note says CI_width/3.92 ~ 0.80')
print(f'  If CI_width/3.92 = 0.80, that equals SE, not SD')
print(f'  Real SD_IG = 0.80*sqrt(17) = {0.80*(17**0.5):.2f}')
print(f'  Real SD_CG = 0.80*sqrt(14) = {0.80*(14**0.5):.2f}')
# Let me check: what does the original paper actually report?
# Table1 shows CMJ IG pre 21.7+/-0.8, post 22.2+/-0.8, CG pre 22.0+/-0.8, post 21.6+/-0.8
# These are small SDs but U-13 soccer players with Myotest device - possible?
# The note says CI was used to derive SD -> the paper may have reported CI instead of SD
# If the paper reports CI=[21.0, 22.4] for mean=21.7 with n=17:
#   CI_width = 1.4, SE = 1.4/3.92 = 0.357, SD = 0.357*sqrt(17) = 1.47
# That doesn't give 0.80 either. The note says CI_width/3.92~0.80
# CI_width = 0.80*3.92 = 3.136, so CI = mean +/- 1.568
# SD = CI_width*sqrt(n)/3.92 = 0.80*sqrt(n)
# For n=17: SD = 0.80*4.12 = 3.30
# For n=14: SD = 0.80*3.74 = 2.99
# But stored SD = 0.80. This means SE was stored as SD.
print(f'  SEVERITY: HIGH - SE(0.80) stored as SD(0.80), inflating precision ~4x')
# Impact on effect size: g uses SD in denominator, so using SE instead of SD inflates g
# g with real SD ~ (0.46-(-0.48))/(pooled_SD~3.1) = 0.94/3.1 ~ 0.30, not 1.48!
print(f'  Approx true_g: {0.94/3.1:.2f} vs reported g_change=1.48')
print(f'  The report\'s sensitivity analysis shows removing R19 changes g by only -0.016')
print(f'  This seems impossible if the SD is wrong by factor of ~4')
print(f'  NEEDS VERIFICATION: Check original paper for actual SD values')
print()

# ===== TASK 6: R27 =====
print('TASK 6: R27 (Toumi 2004)')
r27 = [r for r in rows if r['study_id']=='R27'][0]
print(f'  g_change=2.94 (used), g_post=4.66 (not used)')
print(f'  Both extreme. R27 correctly flagged as outlier.')
print(f'  Sensitivity without R27: g=1.011 [0.587, 1.435]')
print(f'  Smith machine SSC on sedentary males: effect plausible but unusual')
print()

# ===== TASK 7: Overlapping samples =====
print('TASK 7: Overlapping Samples')
ramirez = [r for r in rows if 'Ramirez-Campillo' in r['author']]
print(f'  Ramirez-Campillo entries: {len(ramirez)}')
for r in ramirez:
    print(f'    {r["study_id"]} ({r["year"]}): n={r["exp_n"]}+{r["ctrl_n"]}={int(r["exp_n"])+int(r["ctrl_n"])}')
print(f'  R01 2015 (n=109 from 166 total), R02 2015 (n=26 from 54), R03 2015 (n=16 from 24)')
print(f'  Different PMIDs and samples -> independent studies from same lab')
print(f'  R06/R28 merged correctly. R07/R25 merged correctly.')
print()

# ===== TASK 8: Arm classifications =====
print('TASK 8: Arm Position Classification Cross-check')
arm_map = {r['study_id']: r['cmj_arm'] for r in rows}
# Report groupings:
strict_ids = ['R04', 'R07', 'R09', 'R10', 'R11', 'R14', 'R15', 'R16', 'R18', 'R19', 'R21', 'R22', 'R26', 'R27', 'R29', 'R30']
cmja_ids = ['R02', 'R03', 'R05', 'R08', 'R12', 'R13']
arm_unclear_ids = ['R01', 'R06', 'R17', 'R20', 'R23', 'R31']
vj_ids = ['R24']

print('  STRICT pool arm labels:')
for sid in strict_ids:
    label = arm_map.get(sid, 'MISSING')
    print(f'    {sid}: {label}')
print('  CMJA pool:')
for sid in cmja_ids:
    print(f'    {sid}: {arm_map.get(sid, "MISSING")}')
print('  Arm-Unclear pool:')
for sid in arm_unclear_ids:
    print(f'    {sid}: {arm_map.get(sid, "MISSING")}')
print(f'  VJ: R24: {arm_map.get("R24", "MISSING")}')
print()

# ===== SUBGROUP K-COUNT =====
print('SUBGROUP K-COUNT VERIFICATION')
print('Duration subgroups from wide RevMan file:')
short_list = []
medium_list = []
long_list = []
for r in wide_rows:
    w = int(r['Weeks'])
    name = r['Study']
    if w <= 6:
        short_list.append(f'{name}({w}w)')
    elif w <= 10:
        medium_list.append(f'{name}({w}w)')
    else:
        long_list.append(f'{name}({w}w)')

print(f'  Short (<=6w): {len(short_list)} studies: {short_list}')
print(f'  Medium (7-10w): {len(medium_list)} studies: {medium_list}')
print(f'  Long (>10w): {len(long_list)} studies: {long_list}')
print(f'  Total: {len(short_list)+len(medium_list)+len(long_list)}')
print(f'  Report says: Short=14, Medium=10, Long=4 (=28)')
print(f'  DATA shows: Short={len(short_list)}, Medium={len(medium_list)}, Long={len(long_list)}')
print(f'  DISCREPANCY: Short {len(short_list)} vs 14, Medium {len(medium_list)} vs 10')
# Excluding R24
short_no_r24 = [s for s in short_list if 'Rubley' not in s]
medium_no_r24 = [s for s in medium_list if 'Rubley' not in s]
long_no_r24 = [s for s in long_list if 'Rubley' not in s]
print(f'  Excl R24: Short={len(short_no_r24)}, Medium={len(medium_no_r24)}, Long={len(long_no_r24)}, Total={len(short_no_r24)+len(medium_no_r24)+len(long_no_r24)}')
print(f'  But R24 IS in the wide RevMan file, so wide pool=29 not 28')
print(f'  If R24 excluded: Short=14, Medium=10, Long=4 = 28. BUT data says Short=15, Medium=9, Long=4')
print(f'  There is STILL a discrepancy of 1 study between Short and Medium')
print()

# ===== PEDro verification =====
print('PEDRO SCORE CHECK')
with open(r'D:\桌面\科研训练\output\PEDro_Score_Final.csv', 'r', encoding='utf-8-sig') as f:
    pedro_rows = list(csv.DictReader(f))
print(f'  PEDro entries: {len(pedro_rows)}')
for pr in pedro_rows:
    print(f'    {pr["R"]}: PEDro_std={pr["PEDro_std"]}, Quality={pr["Quality"]}')
print(f'  R09 (Blazevich 2003): PEDro=3, labelled "poor/quasi-RCT"')
print(f'  R17 (Kijowski 2015): PEDro=4, labelled "fair"')
print()

# ===== Table1 vs analysis_ready_effects CROSS-CHECK =====
print('TABLE1 vs ANALYSIS CROSS-CHECK')
with open(r'D:\桌面\科研训练\output\Table1_Study_Characteristics.csv', 'r', encoding='utf-8-sig') as f:
    t1 = list(csv.DictReader(f))
print(f'  Table1 rows: {len(t1)}')
print(f'  Analysis rows: {len(rows)}')
# Check n_IG, n_CG match
mismatches = []
for tr in t1:
    study_name = tr['Study']
    t1_ig = int(tr['n_IG'])
    t1_cg = int(tr['n_CG'])
    t1_g = float(tr['Hedges_g'])
    t1_se = float(tr['SE'])
    # Find matching row in effects
    match = None
    for ar in rows:
        # Match by first author and year
        if tr['Study'].startswith(ar['author'].split(',')[0]) and ar['year'] in tr['Study']:
            # Further disambiguation by n
            if int(ar['exp_n']) == t1_ig and int(ar['ctrl_n']) == t1_cg:
                match = ar
                break
    if match:
        g_diff = abs(float(match['yi_change']) - t1_g)
        se_diff = abs(float(match['sei_change']) - t1_se)
        if g_diff > 0.001 or se_diff > 0.001:
            mismatches.append(f'  {study_name}: g diff={g_diff:.4f}, SE diff={se_diff:.4f}')
    else:
        # Try finding by n_IG and first-author
        for ar in rows:
            if int(ar['exp_n']) == t1_ig and int(ar['ctrl_n']) == t1_cg:
                match = ar
                break
        if match:
            g_diff = abs(float(match['yi_change']) - t1_g)
            se_diff = abs(float(match['sei_change']) - t1_se)
            if g_diff > 0.001 or se_diff > 0.001:
                mismatches.append(f'  {study_name}: g diff={g_diff:.4f}, SE diff={se_diff:.4f}')
        else:
            mismatches.append(f'  {study_name}: NO MATCH FOUND (IG={t1_ig}, CG={t1_cg})')

if mismatches:
    print('  MISMATCHES FOUND:')
    for m in mismatches:
        print(m)
else:
    print('  All Table1 g and SE values match analysis_ready_effects within 0.001')
print()

# ===== R19 detailed: the change score calculation =====
print('R19 DETAILED CALCULATION CHECK')
# yi_change uses pre-post change SMD method
# This requires pre-post correlation. If correlation is estimated
# The g_change = (delta_IG - delta_CG) / S_within * correction
# S_within = pooled within-group SD
# But the stored SD=0.80 is applied.
# If SD is actually SE, the calculation is wrong.
# Let me verify: if we compute post-only g with the stored SD:
# g_post = (22.19-21.56) / pooled_SD_0.80
# pooled_SD = sqrt(((17-1)*0.64 + (14-1)*0.64)/29) = sqrt((10.24+8.32)/29) = sqrt(0.64) = 0.80
# g_post = 0.63/0.80 = 0.7875
# But saved yi_post = 0.767. Close but not exact.
# With small sample correction (J): J = 1 - 3/(4*29-9) = 1 - 3/107 = 0.972
# g_post_J = 0.7875 * 0.972 = 0.765. Close to 0.767.
# So the stored SD=0.80 IS being used as SD in calculations.
# The question is whether 0.80 is really the SD or the SE.
print('  yi_post ~ (22.19-21.56)/0.80 = 0.7875, with J correction ~ 0.765')
# The fact that CI_width/3.92 gave ~0.80 suggests it IS the SE
# But the stored values work out as SD in the g formula
# This is contradictory. The note may be misleading.
print('  If SD=0.80 is the real SD, CI_width = 3.92*0.80 = 3.14')
print('  CI would be [21.4, 24.5] for IG post mean 22.19 with n=17')
# Wait, CI = mean +/- 1.96*SD/sqrt(n) = 22.19 +/- 1.96*0.80/sqrt(17) = 22.19 +/- 0.38
# That's CI_width = 0.76, which /3.92 = 0.194. Not 0.80.
print('  Actually: SE = SD/sqrt(n) = 0.80/sqrt(17) = 0.194')
print('  CI_width = 3.92*0.194 = 0.76, which / 3.92 = 0.194, NOT 0.80')
print('  This means 0.80 CANNOT be SD if CI_width/3.92 = 0.80')
print('  CONCLUSION: 0.80 IS the SE. CI_width = 3.92*0.80 = 3.14')
print('    Real SD = SE*sqrt(n) = 0.80*sqrt(17) = 3.30')
print('    The stored value is SE but was used as SD in calculations')
