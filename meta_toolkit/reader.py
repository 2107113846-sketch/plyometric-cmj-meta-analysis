"""
读取 Excel 模板模块

解析「体育科学Meta分析_数据模板.xlsx」的数据 Sheet。
模板格式:
  Row 1: English column names (used by code)
  Row 2: Chinese descriptions (for human readers)
  Row 3+: data

Sheet names: Instructions, Continuous, Dichotomous, StudyInfo
"""

import pandas as pd
from pathlib import Path


# ---- 列名常量 (对应 Excel Row 1) ----

CONT_COLS = ['study_id', 'outcome', 'measure_tool', 'exp_n', 'exp_mean',
             'exp_sd', 'ctrl_n', 'ctrl_mean', 'ctrl_sd', 'direction', 'comments']

DICH_COLS = ['study_id', 'outcome', 'exp_events', 'exp_nonevents',
             'ctrl_events', 'ctrl_nonevents', 'effect_measure', 'comments']

INFO_COLS = ['study_id', 'author', 'year', 'title', 'design',
             'population', 'intervention', 'control', 'duration_weeks',
             'pedro_score', 'pmid_doi']


def read_template(filepath):
    """
    读取 Excel 模板，返回三个 DataFrame。

    参数:
        filepath: Excel 模板路径

    返回:
        (df_info, df_cont, df_dich)
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Template not found: {filepath}")

    # 从第 3 行开始读取 (跳过英文表头 Row1 + 中文说明 Row2)
    df_info = _read_sheet(filepath, 'StudyInfo', INFO_COLS)
    df_cont = _read_sheet(filepath, 'Continuous', CONT_COLS)
    df_dich = _read_sheet(filepath, 'Dichotomous', DICH_COLS)

    df_info = _clean_info(df_info)
    df_cont = _clean_continuous(df_cont)
    df_dich = _clean_dichotomous(df_dich)

    return df_info, df_cont, df_dich


def _read_sheet(filepath, sheet_name, columns):
    """读取单个 Sheet，跳过前 2 行 (Row1=英文, Row2=中文)"""
    raw = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
    # Set Row 1 (index 0) as column names, then drop rows 0-1
    raw.columns = raw.iloc[0]
    raw = raw.drop([0, 1]).reset_index(drop=True)
    # Keep only expected columns that exist
    available = [c for c in columns if c in raw.columns]
    return raw[available].copy()


def _is_valid_id(val):
    """Filter out separator rows like '>>> Example above...'."""
    s = str(val).strip()
    return len(s) > 0 and '>>>' not in s and 'Example' not in s and s.lower() != 'nan'


def _clean_continuous(df):
    """清洗连续型数据"""
    df = df.dropna(subset=['study_id']).copy()
    df = df[df['study_id'].apply(_is_valid_id)].copy()
    num_cols = ['exp_n', 'exp_mean', 'exp_sd', 'ctrl_n', 'ctrl_mean', 'ctrl_sd']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['exp_mean', 'exp_sd', 'ctrl_mean', 'ctrl_sd'])
    df = df.reset_index(drop=True)
    return df


def _clean_dichotomous(df):
    """清洗二分类数据"""
    df = df.dropna(subset=['study_id']).copy()
    df = df[df['study_id'].apply(_is_valid_id)].copy()
    event_cols = ['exp_events', 'exp_nonevents', 'ctrl_events', 'ctrl_nonevents']
    for col in event_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    df = df.dropna(subset=event_cols)
    df = df.reset_index(drop=True)
    return df


def _clean_info(df):
    """清洗研究信息"""
    df = df.dropna(subset=['study_id']).copy()
    df = df[df['study_id'].apply(_is_valid_id)].copy()
    df = df.reset_index(drop=True)
    return df


def merge_study_info(df_data, df_info):
    """将研究信息合并到效应量数据，丰富分析"""
    cols = ['study_id', 'author', 'year', 'design',
            'population', 'intervention', 'control', 'pedro_score']
    available = [c for c in cols if c in df_info.columns]
    return df_data.merge(df_info[available], on='study_id', how='left')
