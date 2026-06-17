import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('screening_remaining_passed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

year = sys.argv[1] if len(sys.argv) > 1 else None
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
count = int(sys.argv[3]) if len(sys.argv) > 3 else 20

if year:
    articles = [a for a in data if a.get('year') == year]
else:
    articles = data

articles = articles[start:start + count]

for i, a in enumerate(articles, start + 1):
    ab = (a.get('abstract', '') or '').lower()
    has_cmj = 'countermovement' in ab or 'cmj' in ab
    has_rct = 'random' in ab or 'assigned' in ab or 'allocated' in ab
    has_control = 'control group' in ab
    has_plyo = 'plyometric' in ab or 'jump training' in ab or 'drop jump' in ab

    # Find CMJ context
    cmj_context = ''
    for kw in ['countermovement jump', 'cmj', 'vertical jump height', 'vertical jump performance']:
        idx = ab.find(kw)
        if idx >= 0:
            cmj_context = ab[max(0,idx-20):idx+len(kw)+80]
            break

    pub_str = ', '.join(a.get('pub_types', []))
    title = a.get('title', 'N/A')
    abstract = (a.get('abstract', '') or 'N/A')[:500]

    print('=== [{}] PMID:{} | {} | {} ==='.format(i, a['pmid'], a.get('year','?'), a.get('first_author','?')))
    print('TITLE: {}'.format(title))
    print('TYPE: {}'.format(pub_str))
    print('FLAGS: CMJ={} | RCT={} | ControlGrp={} | Plyo={}'.format(has_cmj, has_rct, has_control, has_plyo))
    if cmj_context:
        print('CMJ context: ...{}...'.format(cmj_context))
    print('ABSTRACT: {}'.format(abstract))
    print()
    print('---')
    print()
