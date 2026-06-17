"""
Reorganize all Plyometric CMJ Meta-analysis project files.
- Create categorized folders on Desktop
- Rename files to Chinese
- Move everything in one shot
"""

import os
import shutil

# ── Paths ───────────────────────────────────────────────
SRC = r"D:\桌面\科研训练"
DST = r"D:\桌面\Plyometric训练对CMJ影响的Meta分析"

# ── Category definitions ────────────────────────────────
# Each entry: (source_relative_path, dest_filename, category_folder)
# source_relative_path is relative to SRC

PLAN = [
    # ===== 01_原始数据 =====
    ("data_extraction_FINAL.csv",       "数据提取终表.csv",           "01_原始数据"),
    ("CLEANED_data.csv",                "清洗后数据.csv",             "01_原始数据"),
    ("analysis_ready_effects.csv",      "分析就绪效应量.csv",         "01_原始数据"),
    ("DATA_DICTIONARY.md",              "数据字段说明.md",            "01_原始数据"),
    ("论文代号对照表.csv",              "论文代号对照表.csv",         "01_原始数据"),
    ("数据提取教程.md",                 "数据提取教程.md",            "01_原始数据"),
    ("FINAL_EXTRACTION.csv",            "最终提取备份.csv",           "01_原始数据"),

    # ===== 02_分析代码 =====
    ("run_analysis.py",                 "主分析脚本.py",              "02_分析代码"),
    ("generate_forest.py",              "绘制森林图.py",              "02_分析代码"),
    ("subgroup_analysis.py",            "亚组分析.py",                "02_分析代码"),
    ("meta_regression.py",              "Meta回归.py",                "02_分析代码"),
    ("sensitivity_analysis.py",         "敏感性分析.py",              "02_分析代码"),
    ("publication_bias.py",             "发表偏倚检验.py",            "02_分析代码"),
    ("clean_and_compute_effects.py",    "效应量计算.py",              "02_分析代码"),
    ("export_paper_outputs.py",         "导出论文输出.py",            "02_分析代码"),
    ("main.py",                         "主入口.py",                  "02_分析代码"),

    # ===== 03_筛选记录 =====
    ("screening_final.json",            "筛选结果最终.json",          "03_筛选记录"),
    ("screening_merged_30studies.csv",  "筛选合并30篇.csv",           "03_筛选记录"),
    ("screening_merged_summary.json",   "筛选汇总统计.json",          "03_筛选记录"),
    ("screening_result.csv",            "筛选结果表.csv",             "03_筛选记录"),
    ("output/不确定清单_复核链接.csv",   "不确定清单_复核链接.csv",    "03_筛选记录"),
    ("output/不确定清单_复核链接.txt",   "不确定清单_复核链接.txt",    "03_筛选记录"),

    # ===== 04_论文输出 =====
    ("output/Manuscript_Draft_Methods_Results.md", "论文稿件_Methods_Results.md", "04_论文输出"),
    ("output/forest_strict_hand_on_hip.png",       "森林图_严格手叉腰池.png",     "04_论文输出"),
    ("output/forest_wide_all_cmj.png",             "森林图_宽版全池.png",         "04_论文输出"),
    ("output/funnel_strict_hand_on_hip.png",       "漏斗图_严格手叉腰池.png",     "04_论文输出"),
    ("output/funnel_wide_all_cmj.png",             "漏斗图_宽版全池.png",         "04_论文输出"),
    ("output/PRISMA_flow_diagram.png",             "PRISMA流程图.png",            "04_论文输出"),
    ("output/PRISMA_flow_diagram.svg",             "PRISMA流程图.svg",            "04_论文输出"),
    ("output/PRISMA_flow.json",                    "PRISMA数据.json",             "04_论文输出"),
    ("output/Analysis_Report.txt",                 "完整分析报告.txt",            "04_论文输出"),
    ("output/Table1_Study_Characteristics.csv",    "表1_研究特征.csv",            "04_论文输出"),
    ("output/RevMan_ready_strict_pool.csv",        "RevMan导入_严格池.csv",       "04_论文输出"),
    ("output/RevMan_ready_wide_pool.csv",          "RevMan导入_宽版池.csv",       "04_论文输出"),
    ("output/prisma_flow_diagram.py",              "绘制PRISMA流程图.py",         "04_论文输出"),

    # ===== 05_工具库 =====
]

# ── Create destination folders ──────────────────────────
folders = [
    "01_原始数据",
    "02_分析代码",
    "03_筛选记录",
    "04_论文输出",
    "05_工具库",
]

print(f"Creating: {DST}")
os.makedirs(DST, exist_ok=True)

for f in folders:
    p = os.path.join(DST, f)
    os.makedirs(p, exist_ok=True)
    print(f"  + {f}/")

# ── Move and rename files ───────────────────────────────
moved = 0
errors = []

for src_rel, dst_name, folder in PLAN:
    src_path = os.path.join(SRC, src_rel)
    dst_path = os.path.join(DST, folder, dst_name)

    if not os.path.exists(src_path):
        errors.append(f"  MISSING: {src_rel}")
        continue

    try:
        shutil.move(src_path, dst_path)
        print(f"  OK  {src_rel}  -->  {folder}/{dst_name}")
        moved += 1
    except Exception as e:
        errors.append(f"  FAIL: {src_rel} -> {dst_name}: {e}")

# ── Copy meta_toolkit as whole folder ───────────────────
toolkit_src = os.path.join(SRC, "meta_toolkit")
toolkit_dst = os.path.join(DST, "05_工具库", "meta_toolkit")
if os.path.isdir(toolkit_src):
    if os.path.exists(toolkit_dst):
        shutil.rmtree(toolkit_dst)
    shutil.copytree(toolkit_src, toolkit_dst)
    print(f"  OK  meta_toolkit/  -->  05_工具库/meta_toolkit/ (copied)")
else:
    print("  WARN: meta_toolkit/ not found, skipping")

# ── Report ──────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"Moved: {moved} files")
print(f"Toolkit: copied")
if errors:
    print(f"\nWarnings ({len(errors)}):")
    for e in errors:
        print(e)
else:
    print("No errors!")

print(f"\nAll files in: {DST}")
