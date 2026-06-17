"""
Screen the remaining ~390 articles from screening_all_passed.json
that haven't been manually reviewed yet.
Applies R2 strict criteria + final_screen corrections.
"""
import json, sys, io, os
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load all 590 passed articles
with open('screening_all_passed.json', 'r', encoding='utf-8') as f:
    all_passed = json.load(f)

# Load already-finalized PMIDs
finalized_pmids = set()
for fname in ['screening_final.json', 'screening_eligible.json',
              'screening_excluded_r2.json', 'screening_passed.json']:
    path = fname
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                finalized_pmids.add(item.get('pmid', ''))

# Filter to remaining articles
remaining = [a for a in all_passed if a['pmid'] not in finalized_pmids]
print(f"All passed: {len(all_passed)}")
print(f"Already screened: {len(all_passed) - len(remaining)}")
print(f"Remaining to screen: {len(remaining)}")
print()

# ================================================================
# R2 Screening Criteria (from screen_round2.py)
# ================================================================
def r2_screen(article):
    t = (article['title'] + ' ' + article['abstract']).lower()
    pt = ' '.join(article['pub_types']).lower()

    # CATEGORY 1: Acute / single-session studies
    acute_kw = [
        'acute effects', 'post-activation performance enhancement',
        'post activation performance enhancement', 'pape',
        'warm-up protocol', 'warm up protocol',
        'postactivation potentiation', 'post-activation potentiation',
        'single session', 'single bout',
        'external cueing', 'conditioning activity',
        'effects of caffeine', 'hot-water immersion', 'creatine monohydrate',
        'loading strategies for countermovement',
        'assessment of countermovement jump with and without',
        'using a single inertial measurement', 'can classify individuals',
        'kinetic time-curves can classify',
        'performance of artificial neural network',
        'comparison of methods for analyzing',
        'maximal and submaximal vertical jump',
        'exploring peak concentric force', 'variability of plyometric',
        'loaded and unloaded jump performance of top-level',
        'countermovement jump performance with increased training loads',
        'effects of drop-height and surface instability',
        'is altered by visual and auditory',
    ]
    for kw in acute_kw:
        if kw in t:
            return False, f'R2-acute/non-intervention: {kw}'

    # CATEGORY 2: No control group (all groups do plyometric)
    no_ctrl_kw = [
        'unilateral, bilateral and combined plyometric',
        'bilateral and unilateral plyometric training on physical',
        'effects of unilateral and bilateral plyometric',
        'vertical- vs. horizontal-oriented drop jump',
        'vertical and horizontal plyometric training on jump',
        'frontal- and sagittal-plane plyometrics',
        'assisted, resisted, and free countermovement',
        'jump training with different loads: effects on jumping',
        'sand vs. land surface',
        'plyometric and ballistic training have similar',
        'effects of drop jump training on physical fitness',
        'cluster vs. traditional plyometric training sets',
        'jump training in youth soccer players: effects of haltere',
        'effects of horizontal plyometric training volume',
        'training order of explosive strength and plyometrics',
        'periodization of plyometrics: is there an optimal',
    ]
    for kw in no_ctrl_kw:
        if kw in t:
            return False, f'R2-no proper control: {kw}'

    # CATEGORY 3: No CMJ outcome
    jump_kw = ['vertical jump', 'countermovement jump', 'counter-movement jump',
               'cmj', 'jump height', 'jumping height', 'jump performance',
               'vertical jumping', 'vertical leap', 'vj height']
    has_cmj = any(kw in t for kw in jump_kw)
    if not has_cmj:
        return False, 'R2-no CMJ outcome'

    # CATEGORY 4: No study design indication
    design_kw = [
        'randomized', 'randomised', 'controlled trial', 'control group',
        'compared', 'comparison group', 'assigned', 'allocated',
        'experimental group', 'intervention group', 'quasi-experimental',
        'two groups', 'three groups', 'parallel group', 'between-group',
        'between group', 'pre-post', 'pretest', 'posttest'
    ]
    if not any(kw in t for kw in design_kw):
        return False, 'R2-no design indication'

    # CATEGORY 5: Review/meta-analysis
    review_kw = ['meta-analysis', 'systematic review', 'narrative review',
                 'scoping review', 'umbrella review', 'literature review']
    if any(kw in pt for kw in review_kw):
        if 'randomized controlled trial' not in pt and 'clinical trial' not in pt:
            return False, 'R2-review/meta'

    # CATEGORY 6: Disease populations
    disease_kw = ['stroke', 'cerebral palsy', "parkinson's", 'parkinson disease',
                  'acl reconstruction', 'anterior cruciate ligament reconstruction',
                  'osteoarthritis', 'multiple sclerosis', 'knee arthroplasty',
                  'total hip', 'amputation', 'spinal cord injury', 'tendinopathy patient']
    for kw in disease_kw:
        if kw in t:
            return False, f'R2-disease: {kw}'

    # CATEGORY 7: Upper limb only
    if 'upper limb' in t and 'lower' not in t:
        return False, 'R2-upper limb only'

    # CATEGORY 8: Older adults / rehabilitation context (keep for now, flag)
    # Not excluding elderly — this is part of the "all ages" contribution

    return True, 'R2-OK'


# Run screening
passed = []
excluded = []
for a in remaining:
    ok, reason = r2_screen(a)
    if ok:
        passed.append(a)
    else:
        excluded.append((a, reason))

# Output
print('=' * 70)
print(f'  R2 SCREENING RESULTS (remaining articles)')
print('=' * 70)
print(f'  Input:     {len(remaining)}')
print(f'  Passed:    {len(passed)}  ({len(passed)/len(remaining)*100:.1f}%)')
print(f'  Excluded:  {len(excluded)}')
print()

print('Exclusion breakdown:')
reasons = Counter(reason for _, reason in excluded)
for code, count in reasons.most_common():
    print(f'  {code}: {count}')

# Save results
out_dir = 'screening_remaining'
os.makedirs(out_dir, exist_ok=True)

with open('screening_remaining_passed.json', 'w', encoding='utf-8') as f:
    json.dump(passed, f, ensure_ascii=False, indent=2)

excluded_out = [{'pmid': a['pmid'], 'title': a['title'][:150], 'year': a['year'],
                  'first_author': a['first_author'], 'reason': r}
                for a, r in excluded]
with open('screening_remaining_excluded.json', 'w', encoding='utf-8') as f:
    json.dump(excluded_out, f, ensure_ascii=False, indent=2)

print(f'\nSaved:')
print(f'  {len(passed)} passed → screening_remaining_passed.json')
print(f'  {len(excluded)} excluded → screening_remaining_excluded.json')

# Print the passed articles for quick review
print(f'\n{"="*70}')
print(f'  PASSED ARTICLES — NEED MANUAL CONFIRMATION ({len(passed)})')
print(f'{"="*70}')
for i, a in enumerate(passed):
    print(f'  [{i+1}] PMID:{a["pmid"]} | {a["year"]} | {a["first_author"]}')
    print(f'      {a["title"][:120]}')
    print()
