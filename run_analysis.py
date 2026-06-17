#!/usr/bin/env python
"""
体育科学 Meta 分析 — 标准分析流水线

用法:
  python run_analysis.py                          # 默认模板 + 自动引擎
  python run_analysis.py --template mydata.xlsx   # 指定模板
  python run_analysis.py --engine python          # 强制纯 Python
  python run_analysis.py --engine r --method ML   # R/metafor + ML 估计
  python run_analysis.py --no-plots               # 不生成图片
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from meta_toolkit.reader import read_template, merge_study_info
from meta_toolkit.effects import compute_effects_continuous, compute_effects_dichotomous
from meta_toolkit.pooling import meta_pool
from meta_toolkit.output import print_results, format_effect_original
from meta_toolkit.viz import draw_forest, draw_funnel
from meta_toolkit.r_bridge import is_r_available


def main():
    parser = argparse.ArgumentParser(
        description='Sport Science Meta-Analysis Pipeline')
    parser.add_argument('--template', type=str,
                        default='体育科学Meta分析_数据模板.xlsx',
                        help='Path to Excel template')
    parser.add_argument('--engine', type=str, default='auto',
                        choices=['auto', 'python', 'r'],
                        help='Analysis engine (auto = detect R if available)')
    parser.add_argument('--method', type=str, default='REML',
                        choices=['REML', 'DL', 'ML', 'FE', 'fixed', 'random'],
                        help='Pooling method')
    parser.add_argument('--no-plots', action='store_true',
                        help='Skip generating plots')
    parser.add_argument('--output-dir', type=str, default='.',
                        help='Output directory for plots')
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.exists():
        print(f'Error: Template not found: {template_path}')
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Engine detection
    if args.engine == 'auto':
        active_engine = 'R/metafor (REML)' if is_r_available() else 'Python (DL)'
    elif args.engine == 'r':
        if not is_r_available():
            print('Error: R engine requested but R/metafor not available')
            print('Falling back to Python engine')
            active_engine = 'Python (DL)'
        else:
            active_engine = f'R/metafor ({args.method})'
    else:
        active_engine = 'Python (DL)'

    print('=' * 60)
    print('  Sport Science Meta-Analysis Pipeline v1.0')
    print(f'  Engine: {active_engine}')
    print(f'  Template: {template_path.name}')
    print('=' * 60)

    # ---- Read ----
    print(f'\n[Reading] {template_path.name} ...')
    df_info, df_cont, df_dich = read_template(template_path)
    print(f'  StudyInfo: {len(df_info)} records')
    print(f'  Continuous outcomes: {len(df_cont)} records')
    print(f'  Dichotomous outcomes: {len(df_dich)} records')

    # ---- Continuous ----
    if len(df_cont) > 0:
        print('\n' + '-' * 60)
        print('  CONTINUOUS OUTCOMES')
        print('-' * 60)

        df_es = compute_effects_continuous(df_cont)
        df_es = merge_study_info(df_es, df_info)

        yi = df_es['yi'].values
        vi = df_es['vi'].values
        sei = df_es['sei'].values

        labels = [
            f"{row.get('author', row['study_id'])} ({int(row.get('year', 0))})"
            for _, row in df_es.iterrows()
        ]

        result = meta_pool(yi, vi, method=args.method,
                           engine=args.engine, labels=labels)
        print_results(result)

        # Fixed-effect for comparison
        if args.method not in ('FE', 'fixed'):
            result_fe = meta_pool(yi, vi, method='fixed', engine=args.engine)
            print(f'\n(Fixed-effect comparison: beta={result_fe["beta"]:.4f}, '
                  f'95%CI=[{result_fe["ci_low"]:.4f}, {result_fe["ci_upp"]:.4f}], '
                  f'p={result_fe["pval"]:.4f})')

        if not args.no_plots:
            eff_type = df_es['effect_type'].iloc[0]
            fp = str(output_dir / 'output_forest_continuous.png')
            draw_forest(yi, sei, labels, result, filepath=fp,
                        xlabel=f'Effect Size ({eff_type})',
                        title='Forest Plot — Continuous Outcomes')
            print(f'\n[Plot] {fp}')

            fp2 = str(output_dir / 'output_funnel_continuous.png')
            draw_funnel(yi, sei, pooled_effect=result['beta'], labels=labels,
                        filepath=fp2, xlabel=f'Effect Size ({eff_type})',
                        title='Funnel Plot — Continuous Outcomes')
            print(f'[Plot] {fp2}')

    # ---- Dichotomous ----
    if len(df_dich) > 0:
        print('\n' + '-' * 60)
        print('  DICHOTOMOUS OUTCOMES')
        print('-' * 60)

        df_es = compute_effects_dichotomous(df_dich)
        df_es = merge_study_info(df_es, df_info)

        yi = df_es['yi'].values
        vi = df_es['vi'].values
        sei = df_es['sei'].values
        measure = df_es['effect_type'].iloc[0]

        labels = [
            f"{row.get('author', row['study_id'])} ({int(row.get('year', 0))})"
            for _, row in df_es.iterrows()
        ]

        result = meta_pool(yi, vi, method=args.method,
                           engine=args.engine, labels=labels)
        print_results(result)

        if measure in ('logOR', 'logRR'):
            result_orig = format_effect_original(result, measure)
            label = 'OR' if measure == 'logOR' else 'RR'
            print(f'\n(exp-transformed: {label}={result_orig["beta"]:.3f}, '
                  f'95%CI=[{result_orig["ci_low"]:.3f}, {result_orig["ci_upp"]:.3f}])')

        if not args.no_plots:
            fp = str(output_dir / 'output_forest_dichotomous.png')
            draw_forest(yi, sei, labels, result, filepath=fp,
                        xlabel=f'Effect Size ({measure})',
                        title='Forest Plot — Dichotomous Outcomes')
            print(f'\n[Plot] {fp}')

            fp2 = str(output_dir / 'output_funnel_dichotomous.png')
            draw_funnel(yi, sei, pooled_effect=result['beta'], labels=labels,
                        filepath=fp2, xlabel=f'Effect Size ({measure})',
                        title='Funnel Plot — Dichotomous Outcomes')
            print(f'[Plot] {fp2}')

    print('\n' + '=' * 60)
    print('  Analysis complete.')
    print('=' * 60)


if __name__ == '__main__':
    main()
