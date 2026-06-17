"""
Final manual curation — combines round 2 results with manual false positive/negative corrections.
Produces the definitive list of eligible studies.
"""
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('screening_passed.json', 'r', encoding='utf-8') as f:
    all_105 = json.load(f)

# Index by PMID
by_pmid = {a['pmid']: a for a in all_105}

# False positives to EXCLUDE from round 2 (passed but shouldn't have):
false_positives = {
    '33105376': 'No CMJ outcome — only DJ and 3-hop test, no countermovement jump measured',
    '36157958': 'Acute biomechanics study — single-session landing style comparison, not training intervention',
    '32879545': 'Both groups do mixed training — explosive strength + plyometric in different orders, no pure plyometric arm',
    '21654341': 'No non-training control — all 3 groups do CMJ training (assisted/resisted/free), no true control',
    '40294009': 'No control group — compares 2x vs 4x per week plyometric, both groups do plyometric',
    '26987499': 'No control group — cluster vs traditional plyometric sets, no non-training control',
    '8947398': 'Single-group pre-post design — no female control group, compared to males only',
}

# False negatives to RE-INCLUDE (wrongly excluded in round 2):
false_negatives = {
    '29351161': 'Has plyometric-only group (PG) vs control group (CG) — PG does pure plyometric',
    '16802248': 'Has plyometric-only group (PG) vs control group (CG) — 4-group design with pure plyometric arm',
    '31268999': 'Has 3 PT groups (Mix/LowHi/Low) + control group (Control) — all PT groups are pure plyometric',
    '35894994': 'Has plyometric training group + combined group + control group — PT group is pure plyometric',
    '34025875': 'Has separate PG (plyometric), SG (strength), CODG, and CG — PG vs CG valid comparison',
    '17530960': 'Has separate PG (plyometric), SG (sprint), and CG — PG vs CG valid comparison',
    '42172307': 'Has LP (land plyometric), AQP (aqua), CON (control) — LP vs CON valid (exclude AQP)',
    '39870072': 'Has BG (bilateral), UG (unilateral), CG (control) — both PT groups vs CG valid',
    '22076090': 'Has unilateral, bilateral PT groups + control group — combine PT groups vs control',
    '24150085': 'Has PT-only group (control group) vs EMS+PT combination groups — PT vs true control valid',
}

# Uncertain — keep in list but mark for manual verification
uncertain = {
    '41487940': 'UNCERTAIN: Abstract mentions 4 groups but cut off — verify control group exists',
    '38074324': 'UNCERTAIN: Abstract incomplete — verify control group exists (likely EG1, EG2, CG)',
    '26258856': 'UNCERTAIN: Primary outcome running economy, CMJ measured but as secondary — verify CMJ Mean±SD reported',
    '11880813': 'UNCERTAIN: "Power training" group — verify it is plyometric/ballistic not weight training',
}

# Build final list
final = []

# Start with round 2 passed, remove false positives
with open('screening_eligible.json', 'r', encoding='utf-8') as f:
    r2_passed = json.load(f)

for a in r2_passed:
    if a['pmid'] in false_positives:
        continue
    entry = dict(a)
    if a['pmid'] in uncertain:
        entry['flag'] = uncertain[a['pmid']]
    else:
        entry['flag'] = ''
    final.append(entry)

# Add false negatives
for pmid, note in false_negatives.items():
    if pmid in by_pmid:
        entry = dict(by_pmid[pmid])
        entry['flag'] = f'Re-included: {note}'
        final.append(entry)

# Sort by year desc
final.sort(key=lambda a: a['year'], reverse=True)

# Output
print('=' * 70)
print(f'  FINAL ELIGIBLE STUDIES: {len(final)}')
print('=' * 70)

flagged = [a for a in final if a['flag']]
clean = [a for a in final if not a['flag']]
print(f'  Clean:    {len(clean)}')
print(f'  Flagged:  {len(flagged)} (need manual verification)')
print(f'  Total:    {len(final)}')

print(f'\n{"="*70}')
print(f'  CLEAN STUDIES ({len(clean)} total)')
print(f'{"="*70}')
for i, a in enumerate(clean, 1):
    print(f'\n{i}. PMID {a["pmid"]} [{a["year"]}]  |  {a["first_author"]}')
    print(f'   {a["title"][:160]}')

if flagged:
    print(f'\n{"="*70}')
    print(f'  FLAGGED — NEED MANUAL VERIFICATION ({len(flagged)} total)')
    print(f'{"="*70}')
    for i, a in enumerate(flagged, 1):
        print(f'\n{i}. PMID {a["pmid"]} [{a["year"]}]  |  {a["first_author"]}')
        print(f'   {a["title"][:160]}')
        print(f'   ⚠ {a["flag"]}')

# Save
with open('screening_final.json', 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(final)} articles to screening_final.json')

# Summary for Excel
print(f'\n{"="*70}')
print(f'  QUICK SUMMARY')
print(f'{"="*70}')
print(f'  Automated first pass:  105 / 200 (52.5%)')
print(f'  After R2 strict filter: 40 / 105 (38.1%)')
print(f'  After manual curation:  {len(final)} / 105 ({len(final)/105*100:.1f}%)')
print(f'  Clean (ready to use):   {len(clean)}')
print(f'  Need verification:     {len(flagged)}')
