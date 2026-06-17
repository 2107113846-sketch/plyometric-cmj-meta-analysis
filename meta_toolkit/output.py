"""
Output module - format meta-analysis results for display.
All strings use ASCII to avoid terminal encoding issues.
"""


def summary_table(result):
    """Format pooled results as a readable text table."""
    def pval_str(p):
        if p < 0.001:
            return '< 0.001'
        return f'{p:.4f}'

    lines = []
    lines.append('=' * 55)
    lines.append(f'  Model: {result["model"]}')
    lines.append('=' * 55)
    lines.append(f'  Pooled ES (beta):  {result["beta"]:.4f}')
    lines.append(f'  SE:                {result["se"]:.4f}')
    lines.append(f'  95% CI:            [{result["ci_low"]:.4f}, {result["ci_upp"]:.4f}]')
    lines.append(f'  z-value:           {result["z"]:.4f}')
    lines.append(f'  p-value:           {pval_str(result["pval"])}')
    lines.append('-' * 55)

    if 'tau2' in result:
        lines.append(f'  tau2 (true var):   {result["tau2"]:.4f}')
        lines.append(f'  I2 (inconsistency):{result["I2"]:.1f}%')
        lines.append(f'  Q statistic:       {result["Q"]:.4f} (p={pval_str(result["Q_pval"])})')
        lines.append('-' * 55)
        if result['pred_low'] is not None:
            lines.append(f'  95% Pred Interval: [{result["pred_low"]:.4f}, {result["pred_upp"]:.4f}]')
            lines.append('  (range where a new study likely falls)')
            lines.append('-' * 55)

    return '\n'.join(lines)


def print_results(result):
    """Print the summary table to stdout."""
    print(summary_table(result))


def format_effect_original(results, measure):
    """
    Convert log-scale results back to original scale (for OR, RR).

    measure: 'logOR' or 'logRR'
    """
    import numpy as np
    r = results.copy()
    if measure in ('logOR', 'logRR'):
        for key in ['beta', 'ci_low', 'ci_upp', 'pred_low', 'pred_upp']:
            if key in r and r[key] is not None:
                r[key] = np.exp(r[key])
    r['model'] = r['model'] + ' (exp-transformed)'
    return r
