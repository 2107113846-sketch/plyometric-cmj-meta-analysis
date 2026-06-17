"""
Full PubMed screening — fetches ALL matching articles in batches,
applies 7-criteria screening + stricter round-2 filters.
Saves final eligible list.
"""
import urllib.request, urllib.parse, json, xml.etree.ElementTree as ET
import sys, io, time
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# ============================================================
# Step 1: Search — get ALL PMIDs
# ============================================================
query = (
    '(plyometric OR plyometrics OR "jump training" OR "ballistic training"'
    ' OR "drop jump" OR "box jump" OR "depth jump")'
    ' AND ("vertical jump" OR "countermovement jump" OR "counter-movement jump"'
    ' OR CMJ OR "jump height" OR "jump performance")'
    ' NOT review[Publication Type] NOT meta-analysis[Publication Type]'
    ' NOT "systematic review"[Publication Type]'
)

print('Step 1: Searching PubMed for all matching articles...')
params = urllib.parse.urlencode({
    'db': 'pubmed', 'term': query, 'retmax': 2000, 'sort': 'relevance', 'retmode': 'json'
})
with urllib.request.urlopen(BASE + 'esearch.fcgi?' + params, timeout=30) as f:
    result = json.loads(f.read())
pmids = result['esearchresult']['idlist']
total = int(result['esearchresult']['count'])
print(f'Total matches: {total}')
print(f'Retrieved PMIDs: {len(pmids)}')

# ============================================================
# Step 2: Fetch in batches
# ============================================================
all_articles = []
batch_size = 100
total_batches = (len(pmids) + batch_size - 1) // batch_size

for batch_num, batch_start in enumerate(range(0, len(pmids), batch_size), 1):
    batch = pmids[batch_start:batch_start + batch_size]
    print(f'  Fetching batch {batch_num}/{total_batches} ({len(batch)} articles)...', end=' ')
    try:
        params2 = urllib.parse.urlencode({
            'db': 'pubmed', 'id': ','.join(batch), 'retmode': 'xml', 'rettype': 'abstract'
        })
        with urllib.request.urlopen(BASE + 'efetch.fcgi?' + params2, timeout=60) as f:
            root = ET.fromstring(f.read())

        for article in root.findall('.//PubmedArticle'):
            pmid_el = article.find('.//PMID')
            if pmid_el is None:
                continue
            pmid = pmid_el.text
            title_el = article.find('.//ArticleTitle')
            title = (title_el.text or '') if title_el is not None else ''
            year_el = article.find('.//PubDate/Year')
            year = year_el.text if year_el is not None else 'N/A'
            authors = []
            for a in article.findall('.//Author'):
                l = a.find('./LastName')
                i = a.find('./Initials')
                if l is not None:
                    authors.append(l.text + ((' ' + i.text) if i is not None else ''))
            first = authors[0] if authors else 'N/A'
            abs_parts = []
            for ae in article.findall('.//AbstractText'):
                txt = ae.text or ''
                abs_parts.append(txt)
            abstract = ' '.join(abs_parts)
            pub_types = [pt.text for pt in article.findall('.//PublicationType')]
            all_articles.append({
                'pmid': pmid, 'title': title, 'year': year,
                'first_author': first, 'abstract': abstract,
                'pub_types': pub_types
            })
        print(f'OK ({len(all_articles)} total)')
    except Exception as e:
        print(f'ERROR: {e}')
    time.sleep(0.35)

print(f'\nFetched {len(all_articles)} articles total\n')

# ============================================================
# Step 3: Screening (combined R1 + R2 criteria)
# ============================================================
def screen_combined(article):
    t = (article['title'] + ' ' + article['abstract']).lower()
    pt = ' '.join(article['pub_types']).lower()

    # --- R1: Review check ---
    review_kw = ['meta-analysis', 'systematic review', 'narrative review',
                 'scoping review', 'umbrella review', 'literature review']
    if any(kw in pt for kw in review_kw):
        if 'randomized controlled trial' not in pt and 'clinical trial' not in pt:
            return False, '1-review/meta'

    # --- R1: Disease ---
    disease_kw = ['stroke', 'cerebral palsy', "parkinson's", 'parkinson disease',
                  'acl reconstruction', 'anterior cruciate ligament reconstruction',
                  'osteoarthritis', 'multiple sclerosis', 'knee arthroplasty',
                  'total hip', 'amputation', 'spinal cord injury', 'tendinopathy patient']
    for kw in disease_kw:
        if kw in t:
            return False, f'6-disease: {kw}'

    # --- R2: Acute / non-intervention studies ---
    acute_kw = [
        'acute effects', 'post-activation performance enhancement',
        'post activation performance enhancement', 'postactivation potentiation',
        'post-activation potentiation', 'single session', 'warm-up protocol',
        'warm up protocol', 'external cueing', 'conditioning activity',
        'effects of caffeine', 'hot-water immersion', 'creatine monohydrate',
        'loading strategies for countermovement',
        'assessment of countermovement jump with and without',
        'using a single inertial measurement', 'can classify individuals',
        'kinetic time-curves can classify', 'performance of artificial neural network',
        'comparison of methods for analyzing', 'maximal and submaximal vertical jump',
        'exploring peak concentric force', 'variability of plyometric',
        'loaded and unloaded jump performance of top-level',
        'countermovement jump performance with increased training loads',
        'effects of drop-height and surface instability',
        'is altered by visual and auditory',
    ]
    for kw in acute_kw:
        if kw in t:
            return False, f'R2-acute/non-intervention'

    # --- R1: Mixed interventions (not pure plyometric) ---
    mixed_r1 = [
        ('whole-body vibration', 'mixed: vibration'),
        ('blood flow restriction', 'mixed: BFR'),
        ('electrical stimulation', 'mixed: electrostim'),
        ('electromyostimulation', 'mixed: EMS'),
        ('electrostimulation', 'mixed: EMS'),
        ('combined electrostimulation', 'mixed: EMS'),
        ('plyometric combined with', 'mixed: combined'),
        ('plyometric plus', 'mixed: plus'),
        ('plyometric and strength training', 'mixed: strength+plyo'),
        ('plyometric and resistance training', 'mixed: resist+plyo'),
        ('plyometric and balance training', 'mixed: balance+plyo'),
        ('strength training and plyometric', 'mixed: strength+plyo'),
        ('resistance training and plyometric', 'mixed: resist+plyo'),
        ('combined strength and plyometric', 'mixed: strength+plyo'),
        ('combined balance and plyometric', 'mixed: balance+plyo'),
        ('combined plyometric, strength', 'mixed: multi'),
        ('plyometric, strength and change', 'mixed: multi'),
        ('compound training', 'mixed: compound'),
        ('complex training', 'mixed: complex'),
        ('plyometrics along with pilates', 'mixed: pilates'),
        ('squat training combined with plyometrics', 'mixed: squat+plyo'),
        ('weight training combined with plyometrics', 'mixed: weight+plyo'),
        ('combined weight training and plyometrics', 'mixed: weight+plyo'),
        ('loaded jump squat', 'not plyometric'),
        ('light load jump squat and plyometric', 'mixed: jump squat+plyo'),
        ('olympic-style weightlifting', 'not plyometric'),
        ('flywheel resistance training', 'not plyometric'),
        ('velocity-based resistance training', 'not plyometric'),
        ('autoregulatory progressive resistance', 'not plyometric'),
        ('weighted-jump-squat', 'not plyometric'),
        ('eccentric load reduction', 'not plyometric'),
        ('muscle plasticity after weight', 'mixed: weight+plyo'),
        ('upper limb', 'upper limb study'),
        ('aquatic', 'aquatic'),
        ('aqua plyometric', 'aquatic'),
        ('knee-to-feet jump', 'non-standard'),
        ('plyometric and sprint training', 'mixed: sprint+plyo'),
        ('sprint and plyometric training', 'mixed: sprint+plyo'),
        ('light-load maximal lifting velocity', 'not plyometric'),
        ('plyometrics combined with dynamic stretching', 'mixed: stretching'),
    ]
    for kw, reason in mixed_r1:
        if kw in t:
            return False, f'3-{reason}'

    # --- R1: CMJ check ---
    jump_kw = ['vertical jump', 'countermovement jump', 'counter-movement jump',
               'cmj', 'jump height', 'jumping height', 'jump performance',
               'vertical jumping', 'vertical leap', 'vj height']
    has_cmj = any(kw in t for kw in jump_kw)
    if not has_cmj:
        return False, '4-no CMJ/vertical jump'

    # --- R2: No proper control (all groups plyometric) ---
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
            return False, 'R2-no proper control'

    # Check for meta-analysis in pub type
    if 'meta-analysis' in pt and 'randomized controlled trial' not in pt:
        return False, '1-meta-analysis'

    # --- R2: No control check ---
    no_control_kw = ['single group', 'one group', 'within-subject', 'within subject',
                     'same subjects', 'no control group', 'single-arm']
    for kw in no_control_kw:
        if kw in t:
            return False, f'2-{kw}'

    # Check for study design keywords
    design_ok = any(kw in t for kw in [
        'randomized', 'randomised', 'controlled trial', 'control group',
        'compared', 'comparison group', 'assigned', 'allocated',
        'experimental group', 'intervention group', 'quasi-experimental',
        'two groups', 'three groups', 'parallel group', 'between-group',
        'between group', 'pre-post', 'pretest', 'posttest'
    ])
    if not design_ok:
        return False, '2-no design indication'

    return True, 'OK'


# Run screening
passed = []
excluded = []
for a in all_articles:
    ok, reason = screen_combined(a)
    if ok:
        passed.append(a)
    else:
        excluded.append((a, reason))

# Output
print('=' * 70)
print(f'  SCREENING COMPLETE')
print('=' * 70)
print(f'  Fetched:  {len(all_articles)}')
print(f'  Passed:   {len(passed)}  ({len(passed)/len(all_articles)*100:.1f}%)')
print(f'  Excluded: {len(excluded)}')

print(f'\n{"="*70}')
print(f'  EXCLUSION BREAKDOWN')
print(f'{"="*70}')
reasons = Counter(reason.split('-')[0] if '-' in reason else reason for _, reason in excluded)
for code, count in reasons.most_common():
    print(f'  [{code}] {count}')

# Save
with open('screening_all_passed.json', 'w', encoding='utf-8') as f:
    json.dump(passed, f, ensure_ascii=False, indent=2)

excluded_out = [{'pmid': a['pmid'], 'title': a['title'][:150], 'reason': r}
                for a, r in excluded]
with open('screening_all_excluded.json', 'w', encoding='utf-8') as f:
    json.dump(excluded_out, f, ensure_ascii=False, indent=2)

print(f'\nSaved:')
print(f'  {len(passed)} passed → screening_all_passed.json')
print(f'  {len(excluded)} excluded → screening_all_excluded.json')
