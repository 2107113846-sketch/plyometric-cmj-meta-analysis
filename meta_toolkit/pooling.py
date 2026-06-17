"""
Meta 分析合并模块

实现:
  - 固定效应模型 (Inverse-Variance Weighting)
  - 随机效应模型 (DerSimonian-Laird 方法)
  - 异质性统计量: Q, I², τ², H²
  - 预测区间 (Prediction Interval)

参考: Borenstein et al. (2009) Introduction to Meta-Analysis
"""

import numpy as np
from scipy.stats import chi2, t as t_dist


# ============================================================
# 固定效应模型
# ============================================================

def fixed_effect(yi, vi):
    """
    固定效应模型 (Inverse-Variance Weighting)

    权重: w_i = 1 / vi
    合并效应量: M = sum(w_i * y_i) / sum(w_i)
    SE: SE_M = 1 / sqrt(sum(w_i))

    返回: (合并效应量, SE, 95%CI下限, 95%CI上限, z值, p值, 权重列表)
    """
    w = 1.0 / vi
    M = np.sum(w * yi) / np.sum(w)
    SE = np.sqrt(1.0 / np.sum(w))
    ci_low = M - 1.96 * SE
    ci_upp = M + 1.96 * SE
    z = M / SE
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))

    return {
        'beta': M, 'se': SE, 'ci_low': ci_low, 'ci_upp': ci_upp,
        'z': z, 'pval': p, 'weights': w, 'model': '固定效应模型'
    }


# ============================================================
# 随机效应模型 — DerSimonian-Laird
# ============================================================

def random_effect_dl(yi, vi):
    """
    随机效应模型 (DerSimonian-Laird 估计器)

    1. 先用固定效应合并
    2. 计算 Q 统计量
    3. 估计 τ² (真实效应方差)
    4. 用新权重 w* = 1 / (vi + τ²) 重新合并

    返回: 同 fixed_effect + tau2, I2, Q, H2, pred_interval
    """
    k = len(yi)

    if k == 1:
        # 只有一个研究，返回简单的固定效应
        result = fixed_effect(yi, vi)
        result['tau2'] = 0.0
        result['I2'] = 0.0
        result['Q'] = 0.0
        result['H2'] = 1.0
        result['Q_pval'] = 1.0
        result['pred_low'] = yi[0] - 1.96 * np.sqrt(vi[0])
        result['pred_upp'] = yi[0] + 1.96 * np.sqrt(vi[0])
        result['model'] = '随机效应模型 (DL)'
        result['weights'] = 1.0 / (vi + 0.0)
        return result

    # Step 1: 固定效应权重
    w_fixed = 1.0 / vi

    # Step 2: Q 统计量
    M_fixed = np.sum(w_fixed * yi) / np.sum(w_fixed)
    Q = np.sum(w_fixed * (yi - M_fixed)**2)
    df = k - 1

    # Step 3: DerSimonian-Laird τ² 估计
    C = np.sum(w_fixed) - np.sum(w_fixed**2) / np.sum(w_fixed)
    tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0

    # Step 4: 用 vi + tau2 作为新权重
    w_random = 1.0 / (vi + tau2)
    M_random = np.sum(w_random * yi) / np.sum(w_random)
    SE_random = np.sqrt(1.0 / np.sum(w_random))

    # CI (用标准正态)
    ci_low = M_random - 1.96 * SE_random
    ci_upp = M_random + 1.96 * SE_random
    z = M_random / SE_random
    p = 2.0 * (1.0 - _norm_cdf(abs(z)))

    # I² = (Q - df) / Q * 100%
    I2 = max(0.0, (Q - df) / Q * 100.0) if Q > 0 else 0.0

    # H² = Q / df
    H2 = Q / df if df > 0 else 1.0

    # Q 的 p 值
    Q_pval = 1.0 - chi2.cdf(Q, df) if df > 0 else 1.0

    # 预测区间 (Prediction Interval)
    # PI = M ± t_{k-2, 0.975} * sqrt(SE² + τ²)
    if k > 2:
        t_crit = t_dist.ppf(0.975, k - 2)
        pred_se = np.sqrt(SE_random**2 + tau2)
        pred_low = M_random - t_crit * pred_se
        pred_upp = M_random + t_crit * pred_se
    else:
        pred_low = None
        pred_upp = None

    return {
        'beta': M_random, 'se': SE_random,
        'ci_low': ci_low, 'ci_upp': ci_upp,
        'z': z, 'pval': p, 'weights': w_random,
        'tau2': tau2, 'I2': I2, 'Q': Q, 'H2': H2,
        'Q_pval': Q_pval,
        'pred_low': pred_low, 'pred_upp': pred_upp,
        'model': '随机效应模型 (DL)'
    }


def meta_pool(yi, vi, method='random', engine='auto', labels=None):
    """
    一站式 Meta 合并函数。

    参数:
        yi: 效应量数组
        vi: 方差数组
        method: 'fixed' | 'random' (engine='r' 时支持 'REML' | 'DL' | 'ML' | 'FE')
        engine: 'auto' (自动检测) | 'python' (纯Python) | 'r' (R/metafor)
        labels: 研究标签 (仅 engine='r' 时使用)

    返回: dict (合并结果)
    """
    # Resolve engine
    if engine == 'auto':
        try:
            from meta_toolkit.r_bridge import is_r_available
            if is_r_available():
                engine = 'r'
            else:
                engine = 'python'
        except ImportError:
            engine = 'python'

    if engine == 'r':
        from meta_toolkit.r_bridge import meta_pool_r
        # Map method names
        r_method = method.upper() if method in ('fixed', 'random') else method
        if method == 'fixed':
            r_method = 'FE'
        elif method == 'random':
            r_method = 'REML'
        return meta_pool_r(yi, vi, labels=labels, method=r_method)
    else:
        if method in ('fixed', 'FE'):
            return fixed_effect(yi, vi)
        else:
            return random_effect_dl(yi, vi)


def _norm_cdf(x):
    """标准正态 CDF (避免 scipy 依赖时使用 math.erfc)"""
    import math
    return 0.5 * math.erfc(-x / math.sqrt(2.0))
