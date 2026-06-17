"""
效应量计算模块

支持的效应量:
  连续型: MD (均数差), SMD (Hedges' g)
  二分类: OR (比值比), RR (风险比), RD (风险差)

每个效应量输出: yi, vi, sei
"""

import numpy as np


# ============================================================
# 连续型: MD & SMD
# ============================================================

def _pooled_sd(sd_e, n_e, sd_c, n_c):
    return np.sqrt(
        ((n_e - 1) * sd_e**2 + (n_c - 1) * sd_c**2) / (n_e + n_c - 2)
    )


def compute_md(mean_e, sd_e, n_e, mean_c, sd_c, n_c):
    """MD = 均数差"""
    yi = mean_e - mean_c
    sd_p = _pooled_sd(sd_e, n_e, sd_c, n_c)
    vi = sd_p**2 * (1.0 / n_e + 1.0 / n_c)
    sei = np.sqrt(vi)
    return yi, vi, sei


def compute_smd(mean_e, sd_e, n_e, mean_c, sd_c, n_c):
    """SMD = Hedges' g (小样本修正的标准化均数差)"""
    sd_p = _pooled_sd(sd_e, n_e, sd_c, n_c)
    d = (mean_e - mean_c) / sd_p
    df = n_e + n_c - 2
    J = 1.0 - 3.0 / (4.0 * df - 1.0)  # Hedges 修正因子
    yi = J * d
    vi = (n_e + n_c) / (n_e * n_c) + yi**2 / (2.0 * (n_e + n_c))
    sei = np.sqrt(vi)
    return yi, vi, sei


def compute_effects_continuous(df):
    """
    批量计算连续型结局的效应量。

    输入列: exp_mean, exp_sd, exp_n, ctrl_mean, ctrl_sd, ctrl_n, measure_tool (可选)
    输出列: yi, vi, sei, effect_type

    规则: 如果 measure_tool 有值 → SMD; 否则 → MD
    """
    n = len(df)
    yi_arr = np.zeros(n)
    vi_arr = np.zeros(n)
    sei_arr = np.zeros(n)
    type_arr = [''] * n

    for i, (_, row) in enumerate(df.iterrows()):
        me, se, ne = row['exp_mean'], row['exp_sd'], row['exp_n']
        mc, sc, nc = row['ctrl_mean'], row['ctrl_sd'], row['ctrl_n']
        tool = row.get('measure_tool', None)
        use_smd = (tool is not None
                   and isinstance(tool, str)
                   and len(tool.strip()) > 0
                   and str(tool).lower() != 'nan')

        if use_smd:
            yi, vi, sei = compute_smd(me, se, ne, mc, sc, nc)
            type_arr[i] = 'SMD'
        else:
            yi, vi, sei = compute_md(me, se, ne, mc, sc, nc)
            type_arr[i] = 'MD'

        yi_arr[i] = yi
        vi_arr[i] = vi
        sei_arr[i] = sei

    df = df.copy()
    df['yi'] = yi_arr
    df['vi'] = vi_arr
    df['sei'] = sei_arr
    df['effect_type'] = type_arr
    return df


# ============================================================
# 二分类: OR, RR, RD
# ============================================================

def _add_zero_cell_correction(a, b, c, d):
    """Haldane 修正: 每个格子 +0.5"""
    return a + 0.5, b + 0.5, c + 0.5, d + 0.5


def compute_or(a, b, c, d, correct_zero=True):
    """OR (log scale): log(OR) = log(a) - log(b) - log(c) + log(d)"""
    if correct_zero and (a == 0 or b == 0 or c == 0 or d == 0):
        a, b, c, d = _add_zero_cell_correction(a, b, c, d)
    yi = np.log(a) - np.log(b) - np.log(c) + np.log(d)
    vi = 1.0 / a + 1.0 / b + 1.0 / c + 1.0 / d
    sei = np.sqrt(vi)
    return yi, vi, sei


def compute_rr(a, b, c, d, correct_zero=True):
    """RR (log scale): log(RR) = log(a/(a+b)) - log(c/(c+d))"""
    if correct_zero and (a == 0 or b == 0 or c == 0 or d == 0):
        a, b, c, d = _add_zero_cell_correction(a, b, c, d)
    n_e, n_c = a + b, c + d
    yi = np.log(a) - np.log(n_e) - np.log(c) + np.log(n_c)
    vi = b / (a * n_e) + d / (c * n_c)
    sei = np.sqrt(vi)
    return yi, vi, sei


def compute_rd(a, b, c, d):
    """RD (原始尺度): RD = p_e - p_c"""
    n_e, n_c = a + b, c + d
    p_e, p_c = a / n_e, c / n_c
    yi = p_e - p_c
    vi = p_e * (1.0 - p_e) / n_e + p_c * (1.0 - p_c) / n_c
    sei = np.sqrt(vi)
    return yi, vi, sei


def compute_effects_dichotomous(df):
    """
    批量计算二分类结局的效应量。

    输入列: exp_events, exp_nonevents, ctrl_events, ctrl_nonevents, effect_measure
    输出列: yi, vi, sei, effect_type
    """
    n = len(df)
    yi_arr = np.zeros(n)
    vi_arr = np.zeros(n)
    sei_arr = np.zeros(n)
    type_arr = [''] * n

    for i, (_, row) in enumerate(df.iterrows()):
        a = int(row['exp_events'])
        b = int(row['exp_nonevents'])
        c_val = int(row['ctrl_events'])
        d_val = int(row['ctrl_nonevents'])
        preferred = str(row.get('effect_measure', 'OR')).strip().upper()

        has_zero = (a == 0 or b == 0 or c_val == 0 or d_val == 0)

        if preferred == 'RR':
            yi, vi, sei = compute_rr(a, b, c_val, d_val, correct_zero=has_zero)
            type_arr[i] = 'logRR'
        elif preferred == 'RD':
            yi, vi, sei = compute_rd(a, b, c_val, d_val)
            type_arr[i] = 'RD'
        else:
            yi, vi, sei = compute_or(a, b, c_val, d_val, correct_zero=has_zero)
            type_arr[i] = 'logOR'

        yi_arr[i] = yi
        vi_arr[i] = vi
        sei_arr[i] = sei

    df = df.copy()
    df['yi'] = yi_arr
    df['vi'] = vi_arr
    df['sei'] = sei_arr
    df['effect_type'] = type_arr
    return df
