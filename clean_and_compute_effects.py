"""
数据清洗脚本: 从元宝对话提取的30篇文献 → 分析就绪数据集
步骤:
  1. 加载CSV + 补全已知CMJ数值
  2. 统一单位换算 (SEM→SD, CI→SD, m→cm)
  3. 计算效应量 (SMD / Hedges' g)
  4. 导出分析就绪数据集
  5. 调用R/metafor生成森林图
"""

import csv
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================
# 阶段1: 加载并补全CMJ数值
# ============================================================

# 从元宝对话HTML中提取的已知CMJ数值 (Pre/Post Mean±SD, cm)
# 格式: study_id -> {exp_n, exp_pre_mean, exp_pre_sd, exp_post_mean, exp_post_sd,
#                   ctrl_n, ctrl_pre_mean, ctrl_pre_sd, ctrl_post_mean, ctrl_post_sd}
KNOWN_CMJ_DATA = {
    # ====================================================================
    # 元宝全量提取 2026-06-07 — R01~R31 (去重后30篇 unique)
    # 重复: R07=R25(Chang2025), R06=R28(Van Roie2020) — 已合并
    # ====================================================================

    # ========== 严格手叉腰无臂 CMJ ✅ ==========
    "R04": {  # Palma-Munoz 2018 — ✅ 取PPT+CMJ无臂列
        "exp_n": 7, "ctrl_n": 7,
        "exp_pre_mean": 28.4, "exp_pre_sd": 9.1,
        "exp_post_mean": 32.4, "exp_post_sd": 9.1,
        "ctrl_pre_mean": 27.8, "ctrl_pre_sd": 9.1,
        "ctrl_post_mean": 28.5, "ctrl_post_sd": 9.1,
        "data_note": "✅ 取PPT组+CMJ无臂列; Table2; 后测推算; 篮球青少年"
    },
    "R07": {  # Chang 2025 — ✅ (R25=重复已去重)
        "exp_n": 11, "ctrl_n": 12,
        "exp_pre_mean": 28.0, "exp_pre_sd": 4.0,
        "exp_post_mean": 30.0, "exp_post_sd": 5.0,
        "ctrl_pre_mean": 27.0, "ctrl_pre_sd": 5.0,
        "ctrl_post_mean": 28.0, "ctrl_post_sd": 4.0,
        "data_note": "✅ hands on hips + no arm swing; 赛艇; Kistler测力台; Table2,3; R25=同篇已去重"
    },
    "R09": {  # Blazevich 2003 — ✅ 双臂交叉胸前
        "exp_n": 7, "ctrl_n": 8,  # FHS vs SJ(ctrl)
        "exp_pre_mean": 38.0, "exp_pre_sd": 16.0,
        "exp_post_mean": 41.0, "exp_post_sd": 11.0,
        "ctrl_pre_mean": 39.0, "ctrl_pre_sd": 11.0,
        "ctrl_post_mean": 41.0, "ctrl_post_sd": 11.0,
        "data_note": "✅ 双臂交叉胸前; 取FHS组; SQ组异常(45→41下降)已排除; SD大→异质性高"
    },
    "R10": {  # Byrne 2010 — ✅ 双手置于髋部
        "exp_n": 6, "ctrl_n": 7,  # MJH vs CG
        "exp_pre_mean": 35.0, "exp_pre_sd": 5.0,
        "exp_post_mean": 39.0, "exp_post_sd": 2.0,
        "ctrl_pre_mean": 34.0, "ctrl_pre_sd": 2.0,
        "ctrl_post_mean": 33.0, "ctrl_post_sd": 3.0,
        "data_note": "✅ hands placed on hips; 取MJH组; 大学多项运动; Table1,3"
    },
    "R11": {  # Sedano Campo 2009 — ✅ 双手置于髋部
        "exp_n": 10, "ctrl_n": 10,
        "exp_pre_mean": 25.6, "exp_pre_sd": 1.0,
        "exp_post_mean": 29.3, "exp_post_sd": 1.0,
        "ctrl_pre_mean": 26.2, "ctrl_pre_sd": 0.9,
        "ctrl_post_mean": 25.9, "ctrl_post_sd": 0.9,
        "data_note": "✅ 双手置于髋部; 西甲女足; SD极小(精英运动员同质性好); Table2,3"
    },
    "R14": {  # Jlid 2019 — ✅ hands on hips
        "exp_n": 14, "ctrl_n": 14,
        "exp_pre_mean": 30.3, "exp_pre_sd": 2.1,
        "exp_post_mean": 33.3, "exp_post_sd": 2.4,
        "ctrl_pre_mean": 30.5, "ctrl_pre_sd": 2.3,
        "ctrl_post_mean": 30.6, "ctrl_post_sd": 2.5,
        "data_note": "✅ hands on the hips; 青少男足; OptoJump; Table4; 青春期前-中期"
    },
    "R15": {  # Jlid 2020 — ✅ hands on hips
        "exp_n": 14, "ctrl_n": 13,
        "exp_pre_mean": 30.45, "exp_pre_sd": 4.49,
        "exp_post_mean": 32.19, "exp_post_sd": 4.69,
        "ctrl_pre_mean": 29.82, "ctrl_pre_sd": 3.45,
        "ctrl_post_mean": 30.64, "ctrl_post_sd": 3.34,
        "data_note": "✅ SJ hands on hips→CMJ同; U-21男足; OptoJump; Table3"
    },
    "R16": {  # Khlifa 2010 — ✅ SEM→SD已换算 (×3)
        "exp_n": 9, "ctrl_n": 9,  # PG(无负重) vs CG
        "exp_pre_mean": 44.10, "exp_pre_sd": 3.66,   # SEM 1.22×3
        "exp_post_mean": 47.20, "exp_post_sd": 3.21,  # SEM 1.07×3
        "ctrl_pre_mean": 45.20, "ctrl_pre_sd": 3.75,  # SEM 1.25×3
        "ctrl_post_mean": 46.02, "ctrl_post_sd": 4.59, # SEM 1.53×3
        "data_note": "✅ hands held on hips; SEM→SD(×√9=×3); 取PG无负重; LPG可做负重亚组; Table3"
    },
    "R18": {  # Laurent 2020 — ✅ hands on hips
        "exp_n": 11, "ctrl_n": 10,  # KF(屈膝Plyo) vs CON
        "exp_pre_mean": 32.9, "exp_pre_sd": 7.6,
        "exp_post_mean": 38.4, "exp_post_sd": 7.9,
        "ctrl_pre_mean": 27.8, "ctrl_pre_sd": 7.5,
        "ctrl_post_mean": 28.2, "ctrl_post_sd": 7.5,
        "data_note": "✅ keep hands on hips during entire CMJ; 取KF组; KE可做敏感性; Table2"
    },
    "R19": {  # Michailidis 2018 — ✅ arms akimbo (CI反推均值/SD⚠️)
        "exp_n": 17, "ctrl_n": 14,
        "exp_pre_mean": 21.73, "exp_pre_sd": 0.80,   # CI 20.16-23.30→中点21.73, SD≈0.80
        "exp_post_mean": 22.19, "exp_post_sd": 0.80,  # CI反推SD≈0.80(假设前后同SD)
        "ctrl_pre_mean": 22.04, "ctrl_pre_sd": 0.80,  # 同方法估算
        "ctrl_post_mean": 21.56, "ctrl_post_sd": 0.80,
        "data_note": "✅ arms akimbo; CI→均值/SD反推(CI width/3.92≈0.80); ⚠️估算值需联系作者; U-13男足; Myotest"
    },
    "R21": {  # Potdevin 2011 — ✅ hands on hips
        "exp_n": 12, "ctrl_n": 11,
        "exp_pre_mean": 28.92, "exp_pre_sd": 4.82,
        "exp_post_mean": 32.45, "exp_post_sd": 4.20,
        "ctrl_pre_mean": 27.04, "ctrl_pre_sd": 4.51,
        "ctrl_post_mean": 25.88, "ctrl_post_sd": 3.82,
        "data_note": "✅ hold their hands on their hips; 青春期泳将; Ergojump; Table3"
    },
    "R22": {  # Ramirez-Campillo 2018 — ✅ arms akimbo
        "exp_n": 12, "ctrl_n": 12,  # PJT-B vs CON
        "exp_pre_mean": 37.9, "exp_pre_sd": 5.1,
        "exp_post_mean": 42.0, "exp_post_sd": 4.9,
        "ctrl_pre_mean": 40.2, "ctrl_pre_sd": 4.3,
        "ctrl_post_mean": 40.0, "ctrl_post_sd": 4.3,
        "data_note": "✅ arms akimbo; 取PJT-B(训练前置,效应更大); 青年男足; ErgoJump; Table3"
    },
    "R26": {  # Santos & Janeira 2011 — ✅ CMJ(无臂)与ABA(带臂)分列
        "exp_n": 14, "ctrl_n": 10,
        "exp_pre_mean": 30.33, "exp_pre_sd": 4.3,
        "exp_post_mean": 34.52, "exp_post_sd": 5.0,
        "ctrl_pre_mean": 30.76, "ctrl_pre_sd": 5.1,
        "ctrl_post_mean": 28.40, "ctrl_post_sd": 4.0,
        "data_note": "✅ CMJ(无臂)与ABA(带臂CMJ)分别报告→取CMJ行; 男篮; Globus Ergo Tester; Table3"
    },
    "R27": {  # Toumi 2004 — ✅ hands rested on hips
        "exp_n": 12, "ctrl_n": 6,  # TG1(快ECC) vs CG
        "exp_pre_mean": 37.3, "exp_pre_sd": 1.9,
        "exp_post_mean": 42.5, "exp_post_sd": 1.3,
        "ctrl_pre_mean": 33.9, "ctrl_pre_sd": 1.9,
        "ctrl_post_mean": 34.7, "ctrl_post_sd": 2.1,
        "data_note": "✅ Hands rested on hips; Smith机SSC训练(非经典跳箱,作者称plyometric); 取TG1; Table3"
    },
    "R29": {  # Vescovi 2008 — ✅ hands on hips (Post=Pre+Δ⚠️)
        "exp_n": 10, "ctrl_n": 8,
        "exp_pre_mean": 32.4, "exp_pre_sd": 3.5,
        "exp_post_mean": 33.4, "exp_post_sd": 3.5,   # Post=Pre+1.0, SD用Pre SD近似
        "ctrl_pre_mean": 31.2, "ctrl_pre_sd": 1.0,
        "ctrl_post_mean": 31.0, "ctrl_post_sd": 1.0,   # Post=31.2-0.2, SD用Pre SD近似
        "data_note": "✅ Hands remained on hips; Post=Pre+Δ(SD用Pre SD近似⚠️); G×T ns; 女篮; Kistler; Table3"
    },
    "R30": {  # Yanci 2017 — ✅ hands on waist (m→cm)
        "exp_n": 12, "ctrl_n": 12,  # PT1D vs CG
        "exp_pre_mean": 36.0, "exp_pre_sd": 4.8,
        "exp_post_mean": 35.7, "exp_post_sd": 5.3,
        "ctrl_pre_mean": 35.2, "ctrl_pre_sd": 4.6,
        "ctrl_post_mean": 34.0, "ctrl_post_sd": 4.5,
        "data_note": "✅ hands on the waist(CMJ); 取PT1D(1次/周); 赛季疲劳→CMJ略降; Optojump; Table4"
    },

    # ========== 臂位未明/CMJA推断带臂 ⚠️ ==========
    "R01": {  # Ramirez-Campillo 2015 PMID:25632706 — ⚠️后测推算
        "exp_n": 54, "ctrl_n": 55,  # PT24
        "exp_pre_mean": 32.6, "exp_pre_sd": 6.1,
        "exp_post_mean": 35.01, "exp_post_sd": 6.1,
        "ctrl_pre_mean": 33.1, "ctrl_pre_sd": 6.4,
        "ctrl_post_mean": 32.97, "ctrl_post_sd": 6.4,
        "data_note": "含两Plyo组(PT24/PT48)取PT24; 后测推算; 足球青少年; Globus接触垫; Table1&3"
    },
    "R02": {  # Ramirez-Campillo 2015 PMID:25789497 — CMJA⚠️
        "exp_n": 12, "ctrl_n": 14,  # BG
        "exp_pre_mean": 31.1, "exp_pre_sd": 2.0,
        "exp_post_mean": 36.91, "exp_post_sd": 2.0,
        "ctrl_pre_mean": 28.9, "ctrl_pre_sd": 7.6,
        "ctrl_post_mean": 29.36, "ctrl_post_sd": 7.6,
        "data_note": "⚠️ CMJA带臂; 3Plyo组取BG双侧; 后测推算; Globus Tester; Table1&3"
    },
    "R03": {  # Ramirez-Campillo 2015 PMID:26010692 — CMJA⚠️
        "exp_n": 8, "ctrl_n": 8,  # PPT
        "exp_pre_mean": 27.9, "exp_pre_sd": 8.7,
        "exp_post_mean": 32.53, "exp_post_sd": 8.7,
        "ctrl_pre_mean": 29.2, "ctrl_pre_sd": 9.4,
        "ctrl_post_mean": 29.96, "ctrl_post_sd": 9.4,
        "data_note": "⚠️ CMJA带臂; 2Plyo组取PPT渐进; 后测推算; Ergojump; Table1,3,4"
    },
    "R05": {  # Ramirez-Campillo 2014 — CMJA⚠️
        "exp_n": 17, "ctrl_n": 15,
        "exp_pre_mean": 36.1, "exp_pre_sd": 5.6,
        "exp_post_mean": 39.3, "exp_post_sd": 7.0,
        "ctrl_pre_mean": 34.1, "ctrl_pre_sd": 7.1,
        "ctrl_post_mean": 36.3, "ctrl_post_sd": 8.1,
        "data_note": "⚠️ CMJA带臂; 中长跑运动员; Globus Tester; Table1,3"
    },
    "R08": {  # Asadi 2017 — CMJA⚠️
        "exp_n": 8, "ctrl_n": 8,
        "exp_pre_mean": 44.2, "exp_pre_sd": 2.1,
        "exp_post_mean": 50.5, "exp_post_sd": 2.2,
        "ctrl_pre_mean": 47.1, "ctrl_pre_sd": 2.1,
        "ctrl_post_mean": 47.2, "ctrl_post_sd": 2.1,
        "data_note": "⚠️ CMJA推断带臂; 篮球国家级; Vertec; Table III"
    },
    "R12": {  # Chelly 2010 — 臂位未明示⚠️
        "exp_n": 12, "ctrl_n": 11,
        "exp_pre_mean": 40.0, "exp_pre_sd": 3.0,
        "exp_post_mean": 41.0, "exp_post_sd": 3.0,
        "ctrl_pre_mean": 39.0, "ctrl_pre_sd": 2.0,
        "ctrl_post_mean": 39.0, "ctrl_post_sd": 2.0,
        "data_note": "⚠️ CMJ臂位未明示(SJ限腿CMJ未提臂→推断CMJA); Kistler Quattro Jump; Table5"
    },
    "R13": {  # Idrizovic 2018 — CMJA带臂⚠️
        "exp_n": 13, "ctrl_n": 17,  # Plyo vs CON
        "exp_pre_mean": 42.2, "exp_pre_sd": 6.0,
        "exp_post_mean": 49.5, "exp_post_sd": 7.0,
        "ctrl_pre_mean": 41.7, "ctrl_pre_sd": 4.3,
        "ctrl_post_mean": 45.1, "ctrl_post_sd": 5.1,
        "data_note": "⚠️ 明确带臂CMJA(to mimic volleyball); 女排; OptoJump; Table3; 团队随机"
    },
    "R17": {  # Kijowski/McBride 2015 — 臂位未明示⚠️ (m→cm)
        "exp_n": 9, "ctrl_n": 10,
        "exp_pre_mean": 46.0, "exp_pre_sd": 8.0,
        "exp_post_mean": 49.0, "exp_post_sd": 6.0,
        "ctrl_pre_mean": 47.0, "ctrl_pre_sd": 6.0,
        "ctrl_post_mean": 44.0, "ctrl_post_sd": 5.0,
        "data_note": "⚠️ 臂位未明示; 混合干预(Plyo+重训); m→cm×100; AMTI测力台; Table2"
    },
    "R20": {  # Negra 2016 — 臂位未明示⚠️
        "exp_n": 11, "ctrl_n": 11,  # PTG vs CG
        "exp_pre_mean": 22.89, "exp_pre_sd": 6.06,
        "exp_post_mean": 28.17, "exp_post_sd": 5.93,
        "ctrl_pre_mean": 21.13, "ctrl_pre_sd": 2.96,
        "ctrl_post_mean": 21.99, "ctrl_post_sd": 1.88,
        "data_note": "⚠️ CMJ臂位未明示(SJ写限腿CMJ未提臂); 青春期前男足; OptoJump; Table2"
    },
    "R23": {  # Rensing 2015 — 臂位未明+KG SD缺失⚠️
        "exp_n": 12, "ctrl_n": 9,
        "exp_pre_mean": 37.6, "exp_pre_sd": 5.35,    # IG Pre SD用Post SD近似
        "exp_post_mean": 40.2, "exp_post_sd": 5.35,
        "ctrl_pre_mean": 37.22, "ctrl_pre_sd": 5.35,  # KG SD未报告,用IG SD近似⚠️
        "ctrl_post_mean": 37.58, "ctrl_post_sd": 5.35, # KG SD未报告,用IG SD近似⚠️
        "data_note": "⚠️ 臂位未明示; IG ΔSD=5.35(Results); KG SD未报告→用IG SD近似; 手球; Myotest; Table4"
    },

    # ========== 特殊人群/需换算 ==========
    "R06": {  # Van Roie 2020 — 老年+斜台+SE→SD (R28=同篇已合并)
        "exp_n": 13, "ctrl_n": 14,
        "exp_pre_mean": 14.1, "exp_pre_sd": 2.5,   # SE 0.007×√13≈0.025m=2.5cm
        "exp_post_mean": 15.6, "exp_post_sd": 2.5,  # 同假设
        "ctrl_pre_mean": 13.9, "ctrl_pre_sd": 2.2,  # SE 0.006×√14≈0.022m=2.2cm
        "ctrl_post_mean": 14.1, "ctrl_post_sd": 2.2, # 同假设
        "data_note": "⚠️ 老年(69-70y); 20°斜台sledge CMJ; SE→SD(×√n); 臂位未明示; m→cm×100; R28=同篇已合并; Table S4"
    },

    # ========== VJ带臂敏感性亚组 (非CMJ主分析) ==========
    "R24": {  # Rubley 2011 — VJ带臂(非CMJ❗)
        "exp_n": 10, "ctrl_n": 6,
        "exp_pre_mean": 39.6, "exp_pre_sd": 8.2,
        "exp_post_mean": 47.0, "exp_post_sd": 8.1,
        "ctrl_pre_mean": 39.4, "ctrl_pre_sd": 8.3,
        "ctrl_post_mean": 36.8, "ctrl_post_sd": 6.2,
        "data_note": "❗ VJ带臂(1-step approach+arm swing)非CMJ; 仅VJ敏感性亚组用; Vertec; Table3"
    },

    # ========== 臂位未明 (续) ==========
    "R31": {  # Zubac 2017 — 臂位未明⚠️ (原文已给出Mean±SD,无需换算)
        "exp_n": 10, "ctrl_n": 10,
        "exp_pre_mean": 31.2, "exp_pre_sd": 3.0,
        "exp_post_mean": 35.0, "exp_post_sd": 3.2,    # PL/YO ↑12.2% (p=0.015)
        "ctrl_pre_mean": 31.5, "ctrl_pre_sd": 3.1,
        "ctrl_post_mean": 31.5, "ctrl_post_sd": 3.0,   # CTRL无变化(ns)
        "data_note": "⚠️ 臂位未明示(颈后杆固定但未提hands on hips); AMTI测力台HE600X600; 8周3次/周; 健康活跃大学生混合性别; Figure1+Abstract"
    },
}

# ====================================================================
# COMPLETE_STUDIES — 可直接计算效应量的研究
# ====================================================================
COMPLETE_STUDIES = [
    # 严格手叉腰无臂 ✅ (主分析池)
    "R04", "R07", "R09", "R10", "R11",    # 第1批
    "R14", "R15", "R16", "R18", "R19",    # 第2批 (R19 CI估算⚠️)
    "R21", "R22", "R26", "R27", "R29", "R30",  # 第3批 (R29 Post=Pre+Δ⚠️)
    # 臂位未明/CMJA ⚠️ (宽版池/敏感性)
    "R01", "R02", "R03", "R05", "R08", "R12", "R13",
    "R17", "R20", "R23", "R31",              # R23 KG SD用IG SD近似⚠️; R31 Zubac2017臂位未明
    # 特殊人群
    "R06",                                   # 老年+斜台, SE→SD
    # VJ敏感性亚组
    "R24",                                   # VJ带臂,非CMJ主分析
]
# 待补全: R31(Zubac 2016, Figure提取)
# 排除于CMJ主分析: Stien(无CMJ高度), Vissing(无不做Plyo对照)

# ============================================================
# 阶段2: 效应量计算
# ============================================================

def compute_smd_post_only(exp_n, exp_mean, exp_sd, ctrl_n, ctrl_mean, ctrl_sd):
    """
    Compute standardized mean difference (Cohen's d) from post-test only.
    Uses pooled pre-test SD or post-test SD as the standardizer.
    For Hedges' g, apply small-sample correction: g = d × J(df)
    """
    # Pooled SD
    pooled_sd = np.sqrt(
        ((exp_n - 1) * exp_sd**2 + (ctrl_n - 1) * ctrl_sd**2) /
        (exp_n + ctrl_n - 2)
    )

    # Cohen's d
    d = (exp_mean - ctrl_mean) / pooled_sd

    # Variance of d
    n_total = exp_n + ctrl_n
    v_d = (n_total) / (exp_n * ctrl_n) + d**2 / (2 * n_total)

    # Hedges' g correction factor
    df = exp_n + ctrl_n - 2
    J = 1 - 3 / (4 * df - 1)
    g = d * J
    v_g = J**2 * v_d
    se_g = np.sqrt(v_g)

    # 95% CI
    ci_low = g - 1.96 * se_g
    ci_upp = g + 1.96 * se_g

    return {
        'd': d, 'g': g,
        'v_d': v_d, 'v_g': v_g, 'se_g': se_g,
        'ci_low': ci_low, 'ci_upp': ci_upp,
        'pooled_sd': pooled_sd,
        'method': 'post-only SMD (Hedges g)'
    }


def compute_smd_pre_post_change(exp_n, exp_pre_mean, exp_pre_sd, exp_post_mean, exp_post_sd,
                                  ctrl_n, ctrl_pre_mean, ctrl_pre_sd, ctrl_post_mean, ctrl_post_sd,
                                  pre_post_corr=0.7):
    """
    Compute SMD from pre-post change scores.
    This is more precise than post-only when pre-test differences exist.

    pre_post_corr: assumed correlation between pre and post (default 0.7 for CMJ)
    """
    # Change scores
    exp_change = exp_post_mean - exp_pre_mean
    ctrl_change = ctrl_post_mean - ctrl_pre_mean

    # SD of change scores
    exp_change_sd = np.sqrt(exp_pre_sd**2 + exp_post_sd**2 - 2 * pre_post_corr * exp_pre_sd * exp_post_sd)
    ctrl_change_sd = np.sqrt(ctrl_pre_sd**2 + ctrl_post_sd**2 - 2 * pre_post_corr * ctrl_pre_sd * ctrl_post_sd)

    # Pooled SD of change
    pooled_sd_change = np.sqrt(
        ((exp_n - 1) * exp_change_sd**2 + (ctrl_n - 1) * ctrl_change_sd**2) /
        (exp_n + ctrl_n - 2)
    )

    # Cohen's d on change
    d_change = (exp_change - ctrl_change) / pooled_sd_change

    # Variance
    n_total = exp_n + ctrl_n
    v_d_change = (n_total) / (exp_n * ctrl_n) + d_change**2 / (2 * n_total)

    # Hedges' g
    df = exp_n + ctrl_n - 2
    J = 1 - 3 / (4 * df - 1)
    g_change = d_change * J
    v_g_change = J**2 * v_d_change
    se_g_change = np.sqrt(v_g_change)

    ci_low = g_change - 1.96 * se_g_change
    ci_upp = g_change + 1.96 * se_g_change

    return {
        'd_change': d_change, 'g_change': g_change,
        'v_g_change': v_g_change, 'se_g_change': se_g_change,
        'ci_low': ci_low, 'ci_upp': ci_upp,
        'exp_change': exp_change, 'ctrl_change': ctrl_change,
        'method': 'pre-post change SMD (Hedges g)',
        'pre_post_corr': pre_post_corr
    }


# ============================================================
# 阶段3: 主流程
# ============================================================

def main():
    print("=" * 70)
    print("  Plyometric训练Meta分析 — 数据清洗 + 效应量计算")
    print("=" * 70)

    # Load existing CSV
    csv_path = "D:/桌面/科研训练/screening_merged_30studies.csv"
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        studies = list(reader)

    print(f"\n加载: {len(studies)} 篇文献")

    # Merge known CMJ data
    for s in studies:
        rid = s["代号"]
        if rid in KNOWN_CMJ_DATA:
            kd = KNOWN_CMJ_DATA[rid]
            for key, val in kd.items():
                if val is not None:
                    s[key] = val

    # Count data completeness
    has_cmj = sum(1 for s in studies if s.get("IG前测_cm") or s.get("IG后测_cm"))
    print(f"有CMJ数值: {has_cmj} 篇")

    # ---- Compute effect sizes for COMPLETE studies ----
    print("\n" + "-" * 70)
    print("  效应量计算 (Hedges' g)")
    print("-" * 70)

    effect_sizes = []

    for s in studies:
        rid = s["代号"]
        if rid not in COMPLETE_STUDIES:
            continue

        # Try to get values
        try:
            exp_n_str = s.get("干预组_n", "")
            ctrl_n_str = s.get("对照组_n", "")

            # Parse n values (handle multi-arm like "PG(9)/LPG(9)")
            exp_n = None
            if exp_n_str:
                import re
                nums = re.findall(r'\((\d+)\)', str(exp_n_str))
                if nums:
                    exp_n = int(nums[0])  # Take first group
                else:
                    try:
                        exp_n = int(float(exp_n_str))
                    except:
                        pass

            ctrl_n = None
            if ctrl_n_str:
                try:
                    ctrl_n = int(float(ctrl_n_str))
                except:
                    pass

            exp_pre_mean = float(s.get("IG前测_cm", 0) or 0)
            exp_post_mean = float(s.get("IG后测_cm", 0) or 0)
            ctrl_pre_mean = float(s.get("CG前测_cm", 0) or 0)
            ctrl_post_mean = float(s.get("CG后测_cm", 0) or 0)

            # For now, use KNOWN_CMJ_DATA directly
            if rid in KNOWN_CMJ_DATA:
                kd = KNOWN_CMJ_DATA[rid]
                exp_n = kd.get("exp_n", exp_n)
                ctrl_n = kd.get("ctrl_n", ctrl_n)
                exp_pre_mean = kd.get("exp_pre_mean") or exp_pre_mean
                exp_pre_sd = kd.get("exp_pre_sd") or 0
                exp_post_mean = kd.get("exp_post_mean") or exp_post_mean
                exp_post_sd = kd.get("exp_post_sd") or 0
                ctrl_pre_mean = kd.get("ctrl_pre_mean") or ctrl_pre_mean
                ctrl_pre_sd = kd.get("ctrl_pre_sd") or 0
                ctrl_post_mean = kd.get("ctrl_post_mean") or ctrl_post_mean
                ctrl_post_sd = kd.get("ctrl_post_sd") or 0
            else:
                continue

            if not all([exp_n, ctrl_n, exp_post_mean, exp_post_sd, ctrl_post_mean, ctrl_post_sd]):
                continue

            # Post-only SMD
            result_post = compute_smd_post_only(
                exp_n, exp_post_mean, exp_post_sd,
                ctrl_n, ctrl_post_mean, ctrl_post_sd
            )

            # Pre-post change SMD (more precise)
            result_change = compute_smd_pre_post_change(
                exp_n, exp_pre_mean, exp_pre_sd, exp_post_mean, exp_post_sd,
                ctrl_n, ctrl_pre_mean, ctrl_pre_sd, ctrl_post_mean, ctrl_post_sd
            )

            author = s.get("第一作者", rid)
            year = s.get("年份", "")

            es = {
                "study_id": rid,
                "author": author,
                "year": year,
                "exp_n": exp_n,
                "ctrl_n": ctrl_n,
                "exp_post_mean": exp_post_mean,
                "exp_post_sd": exp_post_sd,
                "ctrl_post_mean": ctrl_post_mean,
                "ctrl_post_sd": ctrl_post_sd,
                "exp_pre_mean": exp_pre_mean,
                "exp_pre_sd": exp_pre_sd,
                "ctrl_pre_mean": ctrl_pre_mean,
                "ctrl_pre_sd": ctrl_pre_sd,
                # Post-only
                "yi_post": result_post['g'],  # Hedges' g
                "vi_post": result_post['v_g'],
                "sei_post": result_post['se_g'],
                "ci_low_post": result_post['ci_low'],
                "ci_upp_post": result_post['ci_upp'],
                # Pre-post change
                "yi_change": result_change['g_change'],
                "vi_change": result_change['v_g_change'],
                "sei_change": result_change['se_g_change'],
                "ci_low_change": result_change['ci_low'],
                "ci_upp_change": result_change['ci_upp'],
                # Metadata
                "cmj_arm": s.get("CMJ臂位", ""),
                "population": s.get("受试者人群", ""),
                "sport": s.get("训练水平", ""),
                "data_note": KNOWN_CMJ_DATA.get(rid, {}).get("data_note", ""),
                "effect_method": result_change['method']
            }

            effect_sizes.append(es)

            print(f"\n  {rid} {author} ({year})")
            print(f"    exp (n={exp_n}): {exp_pre_mean}±{exp_pre_sd} → {exp_post_mean}±{exp_post_sd}")
            print(f"    ctrl (n={ctrl_n}): {ctrl_pre_mean}±{ctrl_pre_sd} → {ctrl_post_mean}±{ctrl_post_sd}")
            print(f"    Post-only SMD: g={result_post['g']:.3f}, 95%CI=[{result_post['ci_low']:.3f}, {result_post['ci_upp']:.3f}]")
            print(f"    Change SMD:   g={result_change['g_change']:.3f}, 95%CI=[{result_change['ci_low']:.3f}, {result_change['ci_upp']:.3f}]")
            print(f"    Δ exp={result_change['exp_change']:.1f}cm, Δ ctrl={result_change['ctrl_change']:.1f}cm")

        except Exception as e:
            print(f"  {rid}: 计算失败 - {e}")

    # ---- Export analysis-ready dataset ----
    if effect_sizes:
        csv_out = "D:/桌面/科研训练/analysis_ready_effects.csv"
        with open(csv_out, 'w', newline='', encoding='utf-8-sig') as f:
            fields = list(effect_sizes[0].keys())
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(effect_sizes)
        print(f"\n[导出] {csv_out} ({len(effect_sizes)} studies)")

    # ---- Data gap report ----
    print("\n" + "=" * 70)
    print("  数据缺口报告")
    print("=" * 70)

    missing_cmj = []
    for s in studies:
        rid = s["代号"]
        if rid not in COMPLETE_STUDIES:
            author = s.get("第一作者", "?")
            year = s.get("年份", "?")
            arm = s.get("CMJ臂位", "?")
            missing_cmj.append(f"  {rid} {author} ({year}) | CMJ臂位: {arm}")

    n_strict = sum(1 for e in effect_sizes if "✅" in str(e.get("data_note", "")))
    n_arm_unclear = sum(1 for e in effect_sizes if "⚠️" in str(e.get("data_note", "")) and "CMJA" in str(e.get("data_note", "")) or "臂位未明" in str(e.get("data_note", "")))
    n_other = len(effect_sizes) - n_strict - n_arm_unclear

    print(f"\n待补全CMJ数值: {len(missing_cmj)} 篇")
    print(f"\n[OK] 可分析: {len(effect_sizes)} 篇")
    print(f"   严格手叉腰: ~{n_strict}篇 | 臂位未明: ~{n_arm_unclear}篇 | 其他: ~{n_other}篇")

    return effect_sizes


if __name__ == "__main__":
    main()
