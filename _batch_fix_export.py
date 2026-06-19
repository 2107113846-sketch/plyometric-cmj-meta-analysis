# -*- coding: utf-8 -*-
"""Batch apply all 4th round review P0-P2 fixes to export_manuscript_docx.py."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = 'D:/桌面/科研训练/export_manuscript_docx.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # P1-3: Fix M7 - all remaining p=0.026 references to p=0.023
    ('p=0.026', 'p=0.023'),

    # P2-2: Fix M12/P2-2 - PEDro percentage
    ('分配隐藏仅5%', '分配隐藏仅7%（2篇明确描述）'),
    ('评估者盲法仅17%', '评估者盲法仅15%（仅3篇）'),

    # P2-5: Face arm position paradoxical data
    ('臂位未明组I²最低（20%），效应量中等偏大。',
     '臂位未明组I²最低（20%），效应量中等偏大——这是一个值得关注的模式：严格手叉腰组异质性（I²=78%）反而高于臂位未明组（I²=20%），与"手臂位置分层排除噪声"的预期方向相反。'),

    # P2-6: Document MCID calculation
    ('加权合并基线SD≈4.5 cm',
     '从纳入研究的基线CMJ SD计算得到的加权合并基线SD≈4.5 cm（基于16篇研究报告基线标准差，I²=98.7%，反映跨研究SD的巨大异质性——纳入研究SD范围为0.8-16cm——该值仅为示意性近似）'),

    # P2-7: Add missing limitations
    ('10. 训练安全性数据缺失。\n'
     '     \'本研究纳入的29篇RCT中，仅3篇简要提及无严重不良事件，均未提供损伤发生率的定量数据。\n\''
     '     \'因此，本研究无法评估Plyometric训练的效益-风险比，效应量估计应与安全性评估结合解读。\n\''
     '     \'未来研究应系统报告不良事件和损伤发生率。\')',
     '10. 训练安全性数据缺失。\n'
     '     \'本研究纳入的29篇RCT中，仅3篇简要提及无严重不良事件，均未提供损伤发生率的定量数据。\n\''
     '     \'因此，本研究无法评估Plyometric训练的效益-风险比，效应量估计应与安全性评估结合解读。\n\''
     '     \'未来研究应系统报告不良事件和损伤发生率。\n\''
     '11. 足球研究过度代表。纳入29篇RCT中足球运动员占11篇（37.9%），部分足球人群（如U-13、U-21学员）高度特异，\n'
     '     \'将效应量推广至其他运动项目（如游泳、赛艇、手球）时需考虑运动专项差异的潜在影响。\n\''
     '12. CMJ测试设备的潜在调节效应。纳入研究使用了力台、接触垫、OptoJump和Myotest等多种设备，\n'
     '     \'不同设备的系统误差（飞行时间法vs.力量积分法）可能引入间接性偏倚，但因多数亚组k过小，\n\''
     '     \'设备类型未作为正式调节变量分析。\n\''
     '13. 多臂研究选择策略的主观性。具有多个干预组的研究（如R01含PT24和PT48两组，R16含PG和LPG两组）中，\n'
     '     \'选择哪个组纳入分析存在主观成分——本研究优先选择训练方案更"标准化"的组，但这一选择可能偏向较高效应量。\n\''
     '14. 训练依从性信息不充分。大多数纳入研究未系统报告训练出勤率、退出原因和不良反应，\n'
     '     \'无法评估实际训练量对效应量的影响。\n\''
     '15. 对照类型的异质性。纳入研究包括无训练对照和维持常规训练对照两类，\n'
     '     \'两者的效应量基准不同（常规训练对照的效应量预期较小），但因各组k数不等，\n\''
     '     \'未单独检验对照类型对合并效应量的调节作用。\')'),
]

# Actually the limitations block is complex, let me just check what entries we have
# and handle them differently

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f'REPLACED: {repr(old[:60])}...')
    else:
        print(f'NOT FOUND: {repr(old[:60])}...')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('\nDone!')
