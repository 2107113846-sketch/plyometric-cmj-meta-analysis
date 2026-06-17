"""
Aggressive screening for remaining articles.
Adds many more exclusion patterns beyond the R2 criteria.
"""
import json, sys, io, os
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('screening_all_passed.json', 'r', encoding='utf-8') as f:
    all_passed = json.load(f)

# Already finalized PMIDs
finalized_pmids = set()
for fname in ['screening_final.json', 'screening_eligible.json',
              'screening_excluded_r2.json', 'screening_passed.json']:
    path = fname
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                finalized_pmids.add(item.get('pmid', ''))

remaining = [a for a in all_passed if a['pmid'] not in finalized_pmids]
print(f"Remaining to screen: {len(remaining)}")

def aggressive_screen(article):
    t = (article['title'] + ' ' + article['abstract']).lower()
    pt = ' '.join(article['pub_types']).lower()

    # ================================================================
    # CATEGORY 0: REVIEWS (must exclude first)
    # ================================================================
    review_kw = ['systematic review', 'meta-analysis', 'narrative review',
                 'scoping review', 'literature review', 'umbrella review']
    for kw in review_kw:
        if kw in t or kw in pt:
            return False, f'REVIEW: {kw}'

    # ================================================================
    # CATEGORY 1: NOT A TRAINING INTERVENTION STUDY
    # ================================================================

    # Supplement / nutritional / recovery studies
    supplement_kw = [
        'supplement', 'supplementation', 'β-alanine', 'beta-alanine',
        'creatine', 'caffeine', 'sodium bicarbonate', 'nitrate',
        'protein', 'whey', 'amino acid', 'bicarbonate',
        'enhanced external counterpulsation', 'recovery modality',
        'foam rolling', 'massage', 'cold water', 'ice bath',
        'compression garment', 'nutritional', 'placebo',
        'carbohydrate', 'electrolyte',
    ]
    for kw in supplement_kw:
        if kw in t:
            return False, f'NOT-TRAINING: supplement/recovery ({kw})'

    # ================================================================
    # CATEGORY 2: NO TRAINING INTERVENTION (biomechanics, methods, etc.)
    # ================================================================

    # Pure biomechanics / kinematic analysis (no intervention)
    no_intervention_kw = [
        'biomechanical mechanisms of jumping', 'biomechanical analysis of',
        'kinematic analysis of', 'kinetic analysis of',
        'relationship between reactive strength', 'correlation between',
        'determination of the best pre-jump', 'use of an overhead goal alters',
        'influence of preactivity and eccentric',
        'enhanced jump performance when providing augmented feedback',
        'is altered by visual and auditory',
        'can classify individuals', 'kinetic time-curves can classify',
        'performance of artificial neural network',
        'comparison of methods for analyzing',
        'maximal and submaximal vertical jump',
        'exploring peak concentric force',
        'variability of plyometric', 'reliability of',
        'validity of', 'test-retest', 'intra-rater',
        'inter-rater', 'measurement of',
        'normative data', 'reference values',
        'using a single inertial measurement',
        'loaded and unloaded jump performance of top-level',
        'countermovement jump performance with increased training loads',
        'effects of drop-height and surface instability',
        'assessment of countermovement jump with and without',
        'loading strategies for countermovement',
    ]
    for kw in no_intervention_kw:
        if kw in t:
            return False, f'NOT-INTERVENTION: biomechanics/methods ({kw})'

    # Acute / single-session / PAPE
    acute_kw = [
        'acute effects', 'post-activation performance enhancement',
        'post activation performance enhancement', 'pape',
        'warm-up protocol', 'warm up protocol',
        'postactivation potentiation', 'post-activation potentiation',
        'single session', 'single bout', 'acute effect',
        'external cueing', 'conditioning activity',
        'acute influence', 'immediate effect',
    ]
    for kw in acute_kw:
        if kw in t:
            return False, f'ACUTE: {kw}'

    # Attentional focus / feedback studies (not training)
    focus_kw = [
        'external focus', 'internal focus', 'attentional focus',
        'augmented feedback', 'verbal instruction', 'visual feedback',
        'focus of attention', 'neutral focus',
    ]
    for kw in focus_kw:
        if kw in t:
            return False, f'NOT-TRAINING: attentional focus / feedback'

    # ================================================================
    # CATEGORY 3: MIXED INTERVENTIONS (not pure plyometric)
    # ================================================================
    mixed_patterns = [
        # Combined: strength/resistance + plyometric
        ('combined training with balance, strength, and plyometrics', 'mixed: balance+strength+plyo'),
        ('combined strength and plyometric', 'mixed: strength+plyo'),
        ('combined plyometric and strength', 'mixed: strength+plyo'),
        ('combined resistance and plyometric', 'mixed: resist+plyo'),
        ('plyometric and strength training', 'mixed: strength+plyo'),
        ('plyometric and resistance training', 'mixed: resist+plyo'),
        ('strength training and plyometric', 'mixed: strength+plyo'),
        ('resistance training and plyometric', 'mixed: resist+plyo'),
        ('plyometric plus strength', 'mixed: strength+plyo'),
        ('plyometric, strength and', 'mixed: multi'),
        ('strength, plyometric', 'mixed: multi'),
        # Combined: sprint + plyometric
        ('plyometric and sprint training', 'mixed: sprint+plyo'),
        ('sprint and plyometric training', 'mixed: sprint+plyo'),
        # Combined: HIIT + plyometric
        ('high-intensity interval training and plyometric', 'mixed: HIIT+plyo'),
        ('hiit and plyometric', 'mixed: HIIT+plyo'),
        # Combined: core/stability + plyometric
        ('integrated functional core and plyometric', 'mixed: core+plyo'),
        ('core training and plyometric', 'mixed: core+plyo'),
        ('core stability and plyometric', 'mixed: core+plyo'),
        # Combined: balance + plyometric
        ('plyometric and balance training', 'mixed: balance+plyo'),
        ('balance and plyometric', 'mixed: balance+plyo'),
        # Combined: weight training + plyometric
        ('plyometric, weight lifting, and combined', 'mixed: weight+plyo'),
        ('weight training combined with plyometrics', 'mixed: weight+plyo'),
        ('combined weight training and plyometrics', 'mixed: weight+plyo'),
        # Combined: other
        ('combined vs. maximal power, heavy-resistance, and plyometric', 'mixed: multi'),
        ('plyometrics combined with dynamic stretching', 'mixed: stretching'),
        ('plyometric and ballistic training have similar', 'not pure plyo'),
        ('effects of assisted and resisted plyometric', 'mixed: assisted/resisted'),
        ('complex training', 'mixed: complex'),
        ('compound training', 'mixed: compound'),
        ('contrast training', 'mixed: contrast'),
        ('concurrent training', 'mixed: concurrent'),
    ]
    for kw, reason in mixed_patterns:
        if kw in t:
            return False, f'MIXED: {reason}'

    # ================================================================
    # CATEGORY 4: NOT PLYOMETRIC AT ALL
    # ================================================================
    not_plyo_kw = [
        'hang-power-clean', 'hang power clean', 'weightlifting',
        'olympic-style weightlifting', 'flywheel', 'resistance training program',
        'velocity-based resistance', 'autoregulatory progressive resistance',
        'loaded jump squat', 'weighted-jump-squat',
    ]
    for kw in not_plyo_kw:
        if kw in t:
            return False, f'NOT-PLYO: {kw}'

    # ================================================================
    # CATEGORY 5: NO CONTROL GROUP
    # ================================================================
    no_ctrl_kw = [
        'unilateral, bilateral and combined plyometric',
        'bilateral and unilateral plyometric training on physical',
        'effects of unilateral and bilateral plyometric',
        'vertical- vs. horizontal-oriented drop jump',
        'vertical and horizontal plyometric training on jump',
        'frontal- and sagittal-plane plyometrics',
        'sand vs. land surface',
        'cluster vs. traditional plyometric training sets',
        'jump training in youth soccer players: effects of haltere',
        'effects of horizontal plyometric training volume',
        'training order of explosive strength and plyometrics',
        'periodization of plyometrics: is there an optimal',
        'assisted, resisted, and free countermovement',
        'jump training with different loads: effects on jumping',
    ]
    for kw in no_ctrl_kw:
        if kw in t:
            return False, f'NO-CONTROL: {kw}'

    # ================================================================
    # CATEGORY 6: NO CMJ / VERTICAL JUMP OUTCOME
    # ================================================================
    jump_kw = ['vertical jump', 'countermovement jump', 'counter-movement jump',
               'cmj', 'jump height', 'jumping height', 'jump performance',
               'vertical jumping', 'vertical leap', 'vj height',
               'squat jump', 'drop jump height', 'rebound jump']
    has_jump = any(kw in t for kw in jump_kw)
    if not has_jump:
        return False, 'NO-JUMP-OUTCOME'

    # ================================================================
    # CATEGORY 7: DISEASE / CLINICAL POPULATIONS
    # ================================================================
    disease_kw = ['stroke', 'cerebral palsy', "parkinson's", 'parkinson disease',
                  'acl reconstruction', 'anterior cruciate ligament reconstruction',
                  'osteoarthritis', 'multiple sclerosis', 'knee arthroplasty',
                  'total hip', 'amputation', 'spinal cord injury',
                  'tendinopathy patient', 'copd', 'chronic obstructive',
                  'hemodialysis', 'dialysis', 'cancer patient']
    for kw in disease_kw:
        if kw in t:
            return False, f'DISEASE: {kw}'

    # ================================================================
    # CATEGORY 8: STUDY DESIGN CHECK
    # ================================================================
    design_kw = [
        'randomized', 'randomised', 'controlled trial', 'control group',
        'compared', 'comparison group', 'assigned', 'allocated',
        'experimental group', 'intervention group', 'quasi-experimental',
        'two groups', 'three groups', 'parallel group', 'between-group',
        'between group', 'pre-post', 'pretest', 'posttest',
        'pre- and post-', 'pre-to-post',
    ]
    if not any(kw in t for kw in design_kw):
        return False, 'NO-DESIGN'

    return True, 'OK'


passed = []
excluded = []
for a in remaining:
    ok, reason = aggressive_screen(a)
    if ok:
        passed.append(a)
    else:
        excluded.append((a, reason))

print(f'\n{"="*70}')
print(f'  AGGRESSIVE SCREENING RESULTS')
print(f'{"="*70}')
print(f'  Input:     {len(remaining)}')
print(f'  Passed:    {len(passed)}  ({len(passed)/len(remaining)*100:.1f}%)')
print(f'  Excluded:  {len(excluded)}')
print()

print('Exclusion breakdown:')
reasons = Counter(reason for _, reason in excluded)
for code, count in reasons.most_common():
    print(f'  {code}: {count}')

# Save
with open('screening_remaining_passed.json', 'w', encoding='utf-8') as f:
    json.dump(passed, f, ensure_ascii=False, indent=2)

excluded_out = [{'pmid': a['pmid'], 'title': a['title'][:150], 'year': a['year'],
                  'first_author': a['first_author'], 'reason': r}
                for a, r in excluded]
with open('screening_remaining_excluded.json', 'w', encoding='utf-8') as f:
    json.dump(excluded_out, f, ensure_ascii=False, indent=2)

print(f'\nSaved: {len(passed)} passed, {len(excluded)} excluded')

# Print top 30 passed for quick review
print(f'\n{"="*70}')
print(f'  FIRST 30 PASSED (for spot-check)')
print(f'{"="*70}')
for i, a in enumerate(passed[:30]):
    print(f'  [{i+1}] PMID:{a["pmid"]} | {a["year"]} | {a["first_author"]}')
    print(f'      {a["title"][:130]}')
    print()
