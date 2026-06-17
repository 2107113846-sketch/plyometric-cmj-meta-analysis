"""
自动筛选脚本 — 用标题+摘要过 7 关
输出：通过的论文列表 + 排除原因统计
"""

import urllib.request, urllib.parse, json, xml.etree.ElementTree as ET
import sys, io, time
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# ============================================================
# Step 1: Search + Fetch
# ============================================================
query = (
    '(plyometric OR plyometrics OR "jump training" OR "ballistic training"'
    ' OR "drop jump" OR "box jump" OR "depth jump")'
    ' AND ("vertical jump" OR "countermovement jump" OR "counter-movement jump"'
    ' OR CMJ OR "jump height" OR "jump performance")'
    ' NOT review[Publication Type] NOT meta-analysis[Publication Type]'
    ' NOT "systematic review"[Publication Type]'
)

print('Searching PubMed...')
params = urllib.parse.urlencode({
    'db': 'pubmed', 'term': query, 'retmax': 200, 'sort': 'relevance', 'retmode': 'json'
})
with urllib.request.urlopen(BASE + 'esearch.fcgi?' + params, timeout=15) as f:
    result = json.loads(f.read())
pmids = result['esearchresult']['idlist']
total = int(result['esearchresult']['count'])
print(f'Total (after excluding reviews): {total}')
print(f'Retrieving top {len(pmids)}...')

# Fetch in batches
all_articles = []
for batch_start in range(0, len(pmids), 50):
    batch = pmids[batch_start:batch_start+50]
    params2 = urllib.parse.urlencode({
        'db': 'pubmed', 'id': ','.join(batch), 'retmode': 'xml', 'rettype': 'abstract'
    })
    with urllib.request.urlopen(BASE + 'efetch.fcgi?' + params2, timeout=30) as f:
        root = ET.fromstring(f.read())
    for article in root.findall('.//PubmedArticle'):
        pmid = article.find('.//PMID').text
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
            t = ae.text or ''
            abs_parts.append(t)
        abstract = ' '.join(abs_parts)
        pub_types = [pt.text for pt in article.findall('.//PublicationType')]
        all_articles.append({
            'pmid': pmid, 'title': title, 'year': year,
            'first_author': first, 'abstract': abstract,
            'pub_types': pub_types
        })
    time.sleep(0.3)

print(f'Fetched {len(all_articles)} articles\n')

# ============================================================
# Step 2: Screen with 7 criteria
# ============================================================
def screen(article):
    t = (article['title'] + ' ' + article['abstract']).lower()
    pt = ' '.join(article['pub_types']).lower()

    # 第1关：原始研究
    review_kw = ['meta-analysis', 'systematic review', 'narrative review',
                 'scoping review', 'umbrella review', 'literature review']
    if any(kw in pt for kw in review_kw):
        if 'randomized controlled trial' not in pt and 'clinical trial' not in pt:
            return False, '1-review/meta'

    # 第6关：健康人群
    disease_kw = ['stroke', 'cerebral palsy', "parkinson's", 'parkinson disease',
                  'acl reconstruction', 'anterior cruciate ligament reconstruction',
                  'osteoarthritis', 'multiple sclerosis', 'knee arthroplasty',
                  'total hip', 'amputation', 'spinal cord injury', 'tendinopathy patient']
    for kw in disease_kw:
        if kw in t:
            return False, f'6-disease: {kw}'

    # 第3关：纯 plyometric
    mixed_kw = [
        ('whole-body vibration', 'mixed: vibration'),
        ('blood flow restriction', 'mixed: BFR'),
        ('electrical stimulation', 'mixed: electrostim'),
        ('plyometric combined with', 'mixed: combined'),
        ('plyometric plus', 'mixed: plus'),
        ('plyometric and strength training', 'mixed: strength+plyo'),
        ('plyometric and resistance training', 'mixed: resist+plyo'),
        ('plyometric and balance training', 'mixed: balance+plyo'),
        ('strength training and plyometric', 'mixed: strength+plyo'),
        ('resistance training and plyometric', 'mixed: resist+plyo'),
        ('combined strength and plyometric', 'mixed: strength+plyo'),
    ]
    for kw, reason in mixed_kw:
        if kw in t:
            return False, f'3-{reason}'

    # 第4关：CMJ 结局
    jump_kw = ['vertical jump', 'countermovement jump', 'counter-movement jump',
               'cmj', 'jump height', 'jumping height', 'jump performance',
               'vertical jumping', 'vertical leap', 'vj height']
    has_cmj = any(kw in t for kw in jump_kw)
    if not has_cmj:
        return False, '4-no CMJ/vertical jump'

    # 第4关补充：排除"结局不对"的研究
    wrong_outcome = {
        'running economy': 'running economy',
        'running performance': 'running performance',
        'sprint performance': 'sprint only',
        'change of direction': 'COD only',
        'vertical stiffness': 'stiffness only',
        'reactive strength index': 'RSI only',
    }
    for kw, reason in wrong_outcome.items():
        if kw in t and not has_cmj:
            return False, f'4-{reason}'

    # 第2关：有对照组
    no_control_kw = ['single group', 'one group', 'within-subject', 'within subject',
                     'same subjects', 'no control group', 'single-arm']
    for kw in no_control_kw:
        if kw in t:
            return False, f'2-{kw}'

    # Check for "crossover" design — can be OK if first period data available
    if 'crossover' in t and 'randomized' not in t:
        return False, '2-crossover unclear'

    # 干预环境
    if 'aquatic' in t or 'water-based' in t or 'underwater' in t:
        return False, '3-aquatic'

    # 特殊排除
    if 'eccentric training' in t and 'plyometric' not in t:
        return False, '3-not plyometric'

    # Check study design keywords - must have indication of controlled trial
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


# Run
passed = []
excluded = []
for a in all_articles:
    ok, reason = screen(a)
    if ok:
        passed.append(a)
    else:
        excluded.append((a, reason))

# ============================================================
# Step 3: Output
# ============================================================
print('=' * 70)
print(f'  SCREENING COMPLETE')
print('=' * 70)
print(f'  Fetched:  {len(all_articles)}')
print(f'  Passed:   {len(passed)}  ({len(passed)/len(all_articles)*100:.1f}%)')
print(f'  Excluded: {len(excluded)}')

print(f'\n{"="*70}')
print(f'  EXCLUSION REASONS')
print(f'{"="*70}')
reasons = Counter(reason.split('-')[0] for _, reason in excluded)
for code, count in reasons.most_common():
    label = {'1': 'Not original research', '2': 'No control group',
             '3': 'Not pure plyometric', '4': 'No CMJ outcome',
             '6': 'Wrong population'}.get(code, code)
    print(f'  [{code}] {label}: {count}')

print(f'\n{"="*70}')
print(f'  PASSED ARTICLES ({len(passed)} total)')
print(f'{"="*70}')

for i, a in enumerate(passed, 1):
    print(f'\n{i}. PMID {a["pmid"]} [{a["year"]}]  |  {a["first_author"]}')
    print(f'   {a["title"][:150]}')
    abs_preview = a['abstract'][:250].replace('\n', ' ')
    print(f'   {abs_preview}...')

# Save passed to JSON for later use
import json as j
with open('screening_passed.json', 'w', encoding='utf-8') as f:
    j.dump(passed, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(passed)} passed articles to screening_passed.json')
