"""
Second-round manual screening — applies stricter criteria to catch false positives
from the automated first pass (screen_papers.py).
"""
import json, sys, io
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('screening_passed.json', 'r', encoding='utf-8') as f:
    articles = json.load(f)

print(f"Loaded {len(articles)} articles from first-pass screening\n")

def strict_screen(article):
    t = (article['title'] + ' ' + article['abstract']).lower()
    pt = ' '.join(article['pub_types']).lower()

    # ================================================================
    # CATEGORY 1: NOT AN INTERVENTION STUDY (most common false positive)
    # ================================================================

    # Acute / single-session studies
    acute_kw = [
        ('acute effects', 'acute study'),
        ('post-activation performance enhancement', 'PAPE/acute'),
        ('post activation performance enhancement', 'PAPE/acute'),
        ('pape', 'PAPE/acute'),
        ('warm-up protocol', 'acute warm-up'),
        ('warm up protocol', 'acute warm-up'),
        ('single session', 'acute single session'),
        ('postactivation potentiation', 'PAPE/acute'),
        ('post-activation potentiation', 'PAPE/acute'),
        ('conditioning activity', 'PAPE/acute'),
        ('rest interval', 'acute rest interval'),
        ('external cueing', 'acute cueing'),
        ('different warm-up', 'acute warm-up'),
        ('acute effect of', 'acute study'),
        ('after drop jump versus', 'acute PAPE'),
        ('after drop jump vs', 'acute PAPE'),
        ('effects of caffeine', 'acute supplement'),
        ('hot-water immersion', 'not plyometric intervention'),
        ('creatine monohydrate', 'supplement study'),
        ('loading strategies for countermovement jump', 'acute crossover'),
    ]
    for kw, reason in acute_kw:
        if kw in t:
            return False, f'R2-{reason}'

    # Measurement / validation / prediction studies
    measure_kw = [
        ('assessment of countermovement jump with and without', 'measurement validation'),
        ('using a single inertial measurement unit', 'measurement validation'),
        ('can classify individuals', 'classification study'),
        ('kinetic time-curves can classify', 'classification study'),
        ('performance of artificial neural network', 'prediction model'),
        ('comparison of methods for analyzing', 'measurement methods'),
        ('maximal and submaximal vertical jump: implications', 'biomechanical analysis'),
        ('exploring peak concentric force', 'biomechanical analysis'),
        ('kinetic analysis of complex training rest interval', 'acute rest interval'),
        ('is altered by visual and auditory', 'cross-sectional'),
        ('altered by visual and auditory cognitive', 'cross-sectional'),
        ('variability of plyometric and ballistic exercise technique', 'acute technique analysis'),
        ('loaded and unloaded jump performance of top-level', 'cross-sectional comparison'),
        ('countermovement jump performance with increased training loads', 'observational monitoring'),
        ('effects of drop-height and surface instability', 'acute biomechanics'),
    ]
    for kw, reason in measure_kw:
        if kw in t:
            return False, f'R2-{reason}'

    # Meta-analysis / review
    if 'meta-analysis' in pt and 'randomized controlled trial' not in pt:
        return False, 'R2-meta-analysis'

    # ================================================================
    # CATEGORY 2: NO PROPER CONTROL GROUP
    # ================================================================
    no_control_signals = [
        ('both groups do plyometric', False),  # custom check below
    ]

    # Studies where all groups receive plyometric/jump training
    all_groups_plyo = [
        'unilateral, bilateral and combined plyometric',
        'bilateral and unilateral plyometric training on physical performance',
        'effects of unilateral and bilateral plyometric',
        'vertical- vs. horizontal-oriented drop jump',
        'vertical and horizontal plyometric training on jump performances',
        'frontal- and sagittal-plane plyometrics',
        'effects of assisted, resisted, and free countermovement',
        'jump training with different loads: effects on jumping',
        'effects of unilateral and bilateral plyometric training on power',
        'sand vs. land surface',
        'plyometric and ballistic training have similar',
        'effects of drop jump training on physical fitness',
        'effects of different multidirectional plyometric sequences',
        'effects of bilateral and unilateral plyometric training on physical',
        'comparison between warm-up protocols',
        'jump training in youth soccer players: effects of haltere',
        'effects of horizontal plyometric training volume',
        'effects of low-load and low-volume squat training combined with',
        'muscle plasticity after weight and combined',
        'comparing autoregulatory progressive resistance',
        'periodization of plyometrics: is there an optimal',
        'does complex training enhance vertical jump',
        'effects of contrast strength vs. plyometric',
    ]
    for kw in all_groups_plyo:
        if kw in t:
            return False, 'R2-all groups do plyometric/no proper control'

    # Single group or no control
    single_group_kw = [
        ('single group', 'single group'),
        ('no control group', 'no control'),
        ('convenience sample', 'likely no control'),
    ]
    for kw, reason in single_group_kw:
        if kw in t:
            return False, f'R2-{reason}'

    # ================================================================
    # CATEGORY 3: NOT PURE PLYOMETRIC (mixed interventions)
    # ================================================================
    mixed_kw = [
        # Combined with strength/resistance
        ('combined balance and plyometric', 'mixed: balance+plyo'),
        ('plyometric and strength training', 'mixed: strength+plyo'),
        ('plyometric and resistance training', 'mixed: resist+plyo'),
        ('strength and plyometric training', 'mixed: strength+plyo'),
        ('resistance and plyometric training', 'mixed: resist+plyo'),
        ('combined plyometric, strength', 'mixed: multi-component'),
        ('plyometric, strength and change of direction', 'mixed: multi-component'),
        ('compound training', 'mixed: compound'),
        ('complex training', 'mixed: complex'),
        # Combined with EMS
        ('electromyostimulation and plyometric', 'mixed: EMS+plyo'),
        ('electrostimulation and plyometric', 'mixed: EMS+plyo'),
        ('combined electrostimulation and plyometric', 'mixed: EMS+plyo'),
        ('neuromuscular electrostimulation', 'mixed: EMS+plyo'),
        # Combined with other modalities
        ('plyometrics along with pilates', 'mixed: pilates+plyo'),
        ('squat training combined with plyometrics', 'mixed: squat+plyo'),
        ('weight training combined with plyometrics', 'mixed: weight+plyo'),
        ('weight training vs. combined', 'mixed: no pure plyo arm'),
        ('combined weight training and plyometrics', 'mixed: weight+plyo'),
        ('plyometric training combined with', 'mixed: combined'),
        ('combined strength and plyometric', 'mixed: strength+plyo'),
        ('plyometrics combined with dynamic stretching', 'mixed: stretching+plyo'),
        # Not plyometric at all
        ('olympic-style weightlifting', 'not plyometric'),
        ('flywheel resistance training', 'not plyometric'),
        ('velocity-based resistance training', 'not plyometric'),
        ('autoregulatory progressive resistance', 'not plyometric'),
        ('eccentric training', 'not plyometric'),
        ('knee-to-feet jump', 'non-standard exercise'),
        ('eccentric load reduction', 'not plyometric'),
        ('loaded jump squat', 'ballistic not plyometric'),
        ('light load jump squat and plyometric', 'mixed: jump squat+plyo'),
        ('light-load maximal lifting velocity', 'not plyometric'),
        # Upper limb
        ('upper limb', 'upper limb study'),
        # Aquatic
        ('aqua plyometric', 'aquatic'),
        ('aquatic', 'aquatic'),
        # Sprint + plyometric combined in same group
        ('plyometric and sprint training group', 'mixed: sprint+plyo'),
        ('sprint and plyometric training on muscle', 'mixed: sprint+plyo'),
        # Not about plyometric intervention
        ('effects of caffeine on countermovement', 'supplement not training'),
        ('creatine monohydrate and combined', 'supplement not training'),
        ('hot-water immersion enhances', 'not plyometric intervention'),
        ('supplementary physical training on vertical jump', 'UNCERTAIN-combined training'),
    ]
    for kw, reason in mixed_kw:
        if kw in t:
            return False, f'R2-{reason}'

    # ================================================================
    # CATEGORY 4: NO CMJ OUTCOME
    # ================================================================
    # Already filtered in round 1, but double-check for drop-jump-only studies
    cmj_kw = ['countermovement jump', 'counter-movement jump', 'cmj',
              'vertical jump', 'jump height', 'jumping height']
    has_cmj = any(kw in t for kw in cmj_kw)

    # Studies that only measure DJ/SJ, not CMJ
    if 'drop jump' in t and 'squat jump' in t and not has_cmj:
        return False, 'R2-no CMJ (only DJ/SJ)'

    # ================================================================
    # CATEGORY 6: WRONG POPULATION
    # ================================================================
    disease_kw = [
        'stroke', 'cerebral palsy', "parkinson's", 'parkinson disease',
        'acl reconstruction', 'anterior cruciate ligament reconstruction',
        'osteoarthritis', 'multiple sclerosis', 'knee arthroplasty',
        'total hip', 'amputation', 'spinal cord injury', 'tendinopathy patient',
        'medial tibial stress syndrome',
    ]
    for kw in disease_kw:
        if kw in t:
            return False, f'R2-disease: {kw}'

    return True, 'OK'


# Run screening
passed = []
excluded = []
for a in articles:
    ok, reason = strict_screen(a)
    if ok:
        passed.append(a)
    else:
        excluded.append((a, reason))

# Output
print('=' * 70)
print(f'  SECOND-ROUND SCREENING COMPLETE')
print('=' * 70)
print(f'  Input:    {len(articles)}')
print(f'  Passed:   {len(passed)}  ({len(passed)/len(articles)*100:.1f}%)')
print(f'  Excluded: {len(excluded)}')

print(f'\n{"="*70}')
print(f'  EXCLUSION REASONS')
print(f'{"="*70}')
reasons = Counter(reason for _, reason in excluded)
for code, count in reasons.most_common():
    print(f'  {code}: {count}')

print(f'\n{"="*70}')
print(f'  TRULY ELIGIBLE ARTICLES ({len(passed)} total)')
print(f'{"="*70}')

for i, a in enumerate(passed, 1):
    print(f'\n{i}. PMID {a["pmid"]} [{a["year"]}]  |  {a["first_author"]}')
    print(f'   {a["title"][:160]}')
    abs_preview = a['abstract'][:200].replace('\n', ' ')
    print(f'   {abs_preview}...')

# Save
with open('screening_eligible.json', 'w', encoding='utf-8') as f:
    json.dump(passed, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(passed)} eligible articles to screening_eligible.json')

# Save excluded with reasons
excluded_out = [{'pmid': a['pmid'], 'title': a['title'], 'reason': r} for a, r in excluded]
with open('screening_excluded_r2.json', 'w', encoding='utf-8') as f:
    json.dump(excluded_out, f, ensure_ascii=False, indent=2)
print(f'Saved {len(excluded)} excluded articles to screening_excluded_r2.json')
