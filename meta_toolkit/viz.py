"""
可视化模块 — 森林图 + 漏斗图 + Egger's 检验

纯 matplotlib 实现，不需要 R 环境。
输出 PNG/SVG，满足期刊 300 DPI 要求。
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from scipy import stats


# ============================================================
# 森林图
# ============================================================

def draw_forest(yi, sei, labels, result, filepath='forest_plot.png',
                xlabel='Standardized Mean Difference (Hedges\' g)', null=0, title='Forest Plot',
                effect_type='SMD', figsize=None):
    """
    画森林图，保存到 filepath。

    参数:
        yi: 各研究效应量 (1D array)
        sei: 各研究标准误 (1D array)
        labels: 研究标签 (list of str)
        result: meta_pool() 返回的合并结果 dict
        filepath: 输出路径 (PNG 或 SVG)
        xlabel: x轴标签
        null: 无效线位置 (0 for MD/SMD, 1 for OR/RR in original scale)
        title: 图片标题
        effect_type: 'SMD', 'MD', 'logOR', 'logRR', 'RD' 等
        figsize: 图片尺寸 (宽, 高)，None 则自动缩放
    """
    k = len(yi)
    if figsize is None:
        figsize = (10, max(3.5, k * 0.45 + 1.8))

    ci_low = yi - 1.96 * sei
    ci_upp = yi + 1.96 * sei
    weights = result.get('weights', 1.0 / (sei ** 2))
    weights = np.asarray(weights, dtype=float)
    # Normalize weights for visual scaling
    w_scaled = weights / np.max(weights) * 80 + 20  # min marker size = 20, max = 100

    fig, ax = plt.subplots(figsize=figsize)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')

    # Determine x limits with padding
    all_vals = np.concatenate([ci_low, ci_upp, [result['beta']]])
    x_min = np.min(all_vals)
    x_max = np.max(all_vals)
    padding = max((x_max - x_min) * 0.25, 0.5)
    ax.set_xlim(x_min - padding, x_max + padding)

    # y positions: bottom to top
    y_positions = list(range(1, k + 1))
    y_summary = 0.2

    # Vertical dashed line at null
    ax.axvline(x=null, color='gray', linestyle='--', linewidth=0.8, alpha=0.7)

    # Draw each study
    for i in range(k):
        y = y_positions[i]
        ax.plot([ci_low[i], ci_upp[i]], [y, y], color='black', linewidth=1.0)
        ax.scatter(yi[i], y, s=w_scaled[i], c='#2c7bb6', edgecolors='black',
                   linewidth=0.5, zorder=5)

    # Summary diamond at bottom
    diamond_x = [result['ci_low'], result['beta'],
                 result['ci_upp'], result['beta'],
                 result['ci_low']]
    diamond_y = [y_summary, y_summary - 0.25,
                 y_summary, y_summary + 0.25,
                 y_summary]
    ax.fill(diamond_x, diamond_y, color='#d7191c', alpha=0.85,
            edgecolor='black', linewidth=0.8, zorder=6)

    # Set y-axis
    all_y_labels = list(labels) + ['Summary (RE)']
    all_y_pos = y_positions + [y_summary]
    ax.set_yticks(all_y_pos)
    ax.set_yticklabels(all_y_labels, fontsize=8)
    ax.set_ylim(y_summary - 0.6, k + 1.3)

    # Add text annotations on the right side: ES [CI] weight%
    right_x = x_max + padding * 0.1
    for i in range(k):
        yi_str = f'{yi[i]:.2f}'
        ci_str = f'[{ci_low[i]:.2f}, {ci_upp[i]:.2f}]'
        w_pct = weights[i] / np.sum(weights) * 100
        text = f'{yi_str} {ci_str}  ({w_pct:.1f}%)'
        ax.text(right_x, y_positions[i], text, fontsize=7,
                va='center', ha='left', family='monospace')

    # Summary text
    sum_text = (f'{result["beta"]:.3f} '
                f'[{result["ci_low"]:.3f}, {result["ci_upp"]:.3f}]')
    ax.text(right_x, y_summary, sum_text, fontsize=8,
            va='center', ha='left', family='monospace', fontweight='bold')

    # Heterogeneity box at top-left
    if 'I2' in result:
        het_text = (f"I² = {result['I2']:.1f}%   "
                    f"τ² = {result['tau2']:.4f}   "
                    f"Q = {result['Q']:.2f} (p={result.get('Q_pval', 0):.3f})")
        ax.text(0.02, 0.98, het_text, transform=ax.transAxes,
                fontsize=8, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                          edgecolor='gray', alpha=0.8))

    ax.tick_params(axis='y', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(filepath, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    return filepath


# ============================================================
# 漏斗图 + Egger's 检验
# ============================================================

def draw_funnel(yi, sei, pooled_effect=None, labels=None,
                filepath='funnel_plot.png', title='Funnel Plot',
                xlabel='Standardized Mean Difference (Hedges\' g)', show_egger=True):
    """
    画漏斗图 (funnel plot)，保存到 filepath。

    参数:
        yi: 各研究效应量
        sei: 各研究标准误
        pooled_effect: 合并效应量 (画竖参考线用)
        labels: 研究标签 (可选)
        filepath: 输出路径
        title: 图片标题
        xlabel: x轴标签
        show_egger: 是否在图上显示 Egger 检验结果
    """
    k = len(yi)
    fig, ax = plt.subplots(figsize=(7, 6))

    # x limits
    x_pad = max((np.max(yi) - np.min(yi)) * 0.3, 0.5)
    x_min_plot = np.min(yi) - x_pad
    x_max_plot = np.max(yi) + x_pad
    ax.set_xlim(x_min_plot, x_max_plot)

    # Pseudo 95% CI funnel boundaries
    # Under null, yi ~ N(true_effect, sei^2), so 95% limits = pooled_effect +/- 1.96 * sei
    ref_effect = pooled_effect if pooled_effect is not None else np.average(yi, weights=1.0 / sei**2)
    se_range = np.linspace(0, max(sei) * 1.15, 200)
    upper = ref_effect + 1.96 * se_range
    lower = ref_effect - 1.96 * se_range
    ax.plot(upper, se_range, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
    ax.plot(lower, se_range, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
    ax.fill_betweenx(se_range, lower, upper, alpha=0.04, color='gray')

    # Vertical reference line at pooled effect
    ax.axvline(x=ref_effect, color='#d7191c', linestyle='-', linewidth=0.8, alpha=0.8)

    # Scatter points
    ax.scatter(yi, sei, s=45, c='#2c7bb6', edgecolors='black',
               linewidth=0.4, zorder=5)

    # Label a few studies
    if labels is not None:
        for i in range(k):
            ax.annotate(labels[i], (yi[i], sei[i]),
                        textcoords="offset points", xytext=(5, 5),
                        fontsize=6, alpha=0.7)

    # y-axis inverted (top = small SE = precise)
    ax.set_ylim(max(sei) * 1.15, -max(sei) * 0.05)
    ax.set_ylabel('Standard Error', fontsize=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold')

    # Egger test annotation
    if show_egger and k >= 3:
        egger = egger_test(yi, sei)
        egger_str = (f"Egger's test: intercept = {egger['intercept']:.3f}, "
                     f"p = {egger['pval']:.3f}")
        ax.text(0.02, 0.98, egger_str, transform=ax.transAxes,
                fontsize=8, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                          edgecolor='gray', alpha=0.8))

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    fig.tight_layout()
    fig.savefig(filepath, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    return filepath


# ============================================================
# Egger's 回归检验
# ============================================================

def egger_test(yi, sei):
    """
    Egger's 回归检验 — 检测漏斗图不对称。

    做加权线性回归: yi/sei ~ 1/sei
    如果截距显著偏离 0 → 漏斗不对称 → 可能存在发表偏倚

    参数:
        yi: 效应量数组
        sei: 标准误数组

    返回:
        dict: intercept, se_intercept, t_value, pval, ci_low, ci_upp
    """
    k = len(yi)
    if k < 3:
        return {'intercept': np.nan, 'se_intercept': np.nan,
                't_value': np.nan, 'pval': np.nan,
                'ci_low': np.nan, 'ci_upp': np.nan}

    # Standardized effect (z-score) and precision
    z = yi / sei
    precision = 1.0 / sei

    # Weighted least squares: weight = 1/var(z_i) ≈ sei_i^2
    # Actually: z_i ~ N(intercept * 1/sei_i + slope, ...)
    # We regress z on precision
    w = sei ** 2  # inverse-variance weights

    # Weighted linear regression: z = b0 + b1 * precision
    w_sum = np.sum(w)
    x_mean = np.sum(w * precision) / w_sum
    y_mean = np.sum(w * z) / w_sum

    s_xx = np.sum(w * (precision - x_mean) ** 2)
    s_xy = np.sum(w * (precision - x_mean) * (z - y_mean))
    s_yy = np.sum(w * (z - y_mean) ** 2)

    if s_xx < 1e-15:
        return {'intercept': np.nan, 'se_intercept': np.nan,
                't_value': np.nan, 'pval': np.nan,
                'ci_low': np.nan, 'ci_upp': np.nan}

    slope = s_xy / s_xx
    intercept = y_mean - slope * x_mean

    # Residual variance
    residuals = z - (intercept + slope * precision)
    sigma2 = np.sum(w * residuals ** 2) / (k - 2) if k > 2 else 1e-10

    # SE of intercept
    se_intercept = np.sqrt(sigma2 * (1.0 / w_sum + x_mean ** 2 / s_xx))

    t_val = intercept / se_intercept
    p_val = 2.0 * (1.0 - stats.t.cdf(abs(t_val), k - 2))

    ci_half = stats.t.ppf(0.975, k - 2) * se_intercept

    return {
        'intercept': intercept,
        'se_intercept': se_intercept,
        't_value': t_val,
        'pval': p_val,
        'ci_low': intercept - ci_half,
        'ci_upp': intercept + ci_half
    }
