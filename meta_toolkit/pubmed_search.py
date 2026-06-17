"""
PubMed 自动检索工具

用法:
  python pubmed_search.py                          # 用预设 query 搜索
  python pubmed_search.py --query "your terms"     # 自定义检索
  python pubmed_search.py --max 50                 # 返回前 50 篇
  python pubmed_search.py --save results.xlsx      # 保存到 Excel
  python pubmed_search.py --check-meta             # 检查是否已有类似 Meta 分析
"""

import argparse
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
import sys
import io
import time

# Fix Windows GBK encoding issues with special characters
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


BASE_URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

# 预设检索式：plyometric + CMJ
DEFAULT_QUERY = (
    '(plyometric OR plyometrics OR "jump training" OR "ballistic training"'
    ' OR "drop jump" OR "box jump" OR "depth jump" OR "rebound jump")'
    ' AND'
    ' ("vertical jump" OR "countermovement jump" OR "counter-movement jump"'
    ' OR CMJ OR "jump height" OR "jump performance")'
)

META_FILTER = ' AND (meta-analysis[Publication Type] OR systematic review[Publication Type])'


def search(query, max_results=20, sort='relevance'):
    """搜索 PubMed 并返回 PMID 列表"""
    params = urllib.parse.urlencode({
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'sort': sort,
        'retmode': 'json'
    })
    url = BASE_URL + 'esearch.fcgi?' + params
    with urllib.request.urlopen(url, timeout=15) as f:
        result = json.loads(f.read())
    pmids = result['esearchresult']['idlist']
    total = int(result['esearchresult']['count'])
    return pmids, total


def fetch_details(pmids):
    """根据 PMID 列表获取文章详情"""
    if not pmids:
        return []
    params = urllib.parse.urlencode({
        'db': 'pubmed',
        'id': ','.join(pmids),
        'retmode': 'xml',
        'rettype': 'abstract'
    })
    url = BASE_URL + 'efetch.fcgi?' + params
    with urllib.request.urlopen(url, timeout=30) as f:
        root = ET.fromstring(f.read())

    articles = []
    for article in root.findall('.//PubmedArticle'):
        pmid = article.find('.//PMID').text
        title_el = article.find('.//ArticleTitle')
        title = title_el.text if title_el is not None else 'N/A'

        # Year
        year_el = article.find('.//PubDate/Year')
        year = year_el.text if year_el is not None else (
            article.find('.//PubDate/MedlineDate').text[:4]
            if article.find('.//PubDate/MedlineDate') is not None else 'N/A'
        )

        # Authors
        authors = []
        for author in article.findall('.//Author'):
            last = author.find('./LastName')
            init = author.find('./Initials')
            if last is not None:
                name = last.text
                if init is not None:
                    name += ' ' + init.text
                authors.append(name)
        first_author = authors[0] if authors else 'N/A'

        # Abstract
        abs_parts = []
        for abs_el in article.findall('.//AbstractText'):
            label = abs_el.get('Label', '')
            text = abs_el.text or ''
            prefix = f'{label}: ' if label else ''
            abs_parts.append(prefix + text)
        abstract = ' '.join(abs_parts)[:500]

        # Publication types
        pub_types = [pt.text for pt in article.findall('.//PublicationType')]

        # DOI
        doi_el = article.find('.//ArticleId[@IdType="doi"]')
        doi = doi_el.text if doi_el is not None else 'N/A'

        articles.append({
            'pmid': pmid,
            'title': title,
            'year': year,
            'first_author': first_author,
            'abstract': abstract,
            'pub_types': pub_types,
            'doi': doi,
        })

    return articles


def check_existing_meta(query):
    """检查是否有相同主题的 Meta 分析"""
    meta_query = f'({query}){META_FILTER}'
    pmids, total = search(meta_query, max_results=10)
    if total == 0:
        print('No existing meta-analyses found. Topic is novel!')
        return []

    print(f'Found {total} existing meta-analyses/reviews:')
    articles = fetch_details(pmids)
    for i, a in enumerate(articles, 1):
        print(f"\n  {i}. [{a['year']}] {a['title'][:120]}")
        print(f"     Authors: {a['first_author']} et al.")
        print(f"     PMID: {a['pmid']}")
    return articles


def save_to_excel(articles, filepath):
    """保存到 Excel"""
    import pandas as pd
    df = pd.DataFrame(articles)
    # Simplify for Excel
    df['pub_types'] = df['pub_types'].apply(lambda x: ', '.join(x))
    cols = ['pmid', 'title', 'year', 'first_author', 'pub_types', 'doi']
    df[cols].to_excel(filepath, index=False)
    return filepath


def main():
    parser = argparse.ArgumentParser(description='PubMed Search for Meta-Analysis')
    parser.add_argument('--query', type=str, default=DEFAULT_QUERY,
                        help='Search query')
    parser.add_argument('--max', type=int, default=20,
                        help='Max results to return')
    parser.add_argument('--sort', type=str, default='relevance',
                        choices=['relevance', 'pub_date', 'first_author'])
    parser.add_argument('--save', type=str, default=None,
                        help='Save results to Excel file')
    parser.add_argument('--check-meta', action='store_true',
                        help='Check for existing meta-analyses on topic')
    parser.add_argument('--full', action='store_true',
                        help='Show full abstracts')
    args = parser.parse_args()

    print('=' * 70)
    print('  PubMed Search Tool for Meta-Analysis')
    print('=' * 70)

    # Check existing meta if requested
    if args.check_meta:
        print('\n--- Checking for Existing Meta-Analyses ---')
        check_existing_meta(args.query)
        print()

    # Main search
    print(f'\nSearching PubMed...')
    print(f'Query: {args.query[:100]}...')
    pmids, total = search(args.query, max_results=args.max, sort=args.sort)
    print(f'Total matches: {total}')
    print(f'Retrieved: {len(pmids)}')

    if not pmids:
        print('No results found.')
        return

    # Fetch details
    print('\nFetching article details...')
    articles = fetch_details(pmids)

    # Display
    print(f'\n{"="*70}')
    for i, a in enumerate(articles, 1):
        pub_label = ', '.join([t for t in a['pub_types']
                               if t in ('Meta-Analysis', 'Systematic Review',
                                        'Randomized Controlled Trial',
                                        'Clinical Trial', 'Review')])[:50]
        print(f"\n{i}. PMID {a['pmid']} [{a['year']}]")
        print(f"   {a['title'][:130]}")
        print(f"   First author: {a['first_author']}")
        if pub_label:
            print(f"   Type: {pub_label}")
        if a['doi'] != 'N/A':
            print(f"   DOI: {a['doi']}")
        if args.full and a['abstract']:
            print(f"   Abstract: {a['abstract'][:300]}...")

    # Save to Excel
    if args.save:
        path = save_to_excel(articles, args.save)
        print(f'\nSaved {len(articles)} articles to {path}')

    print(f'\nDone. ({len(articles)} articles retrieved)')


if __name__ == '__main__':
    main()
