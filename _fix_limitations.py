# -*- coding: utf-8 -*-
"""Apply remaining P2 fixes to limitations and practice recommendations sections."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = 'D:/桌面/科研训练/export_manuscript_docx.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the limitation '训练安全性数据缺失' block and extend it
new_limitations = """	    ('训练安全性数据缺失。',
	     '本研究纳入的29篇RCT中，仅3篇简要提及无严重不良事件，均未提供损伤发生率的定量数据。'
	     '因此，本研究无法评估Plyometric训练的效益-风险比，效应量估计应与安全性评估结合解读。'
	     '未来研究应系统报告不良事件和损伤发生率。'),
	    ('足球研究过度代表。',
	     '纳入29篇RCT中足球运动员占11篇（37.9%），且部分足球人群（U-13、U-21学员）高度特异，'
	     '将效应量推广至其他运动项目时需考虑运动专项差异的潜在影响。'),
	    ('CMJ测试设备的潜在调节效应。',
	     '纳入研究使用了力台、接触垫、OptoJump和Myotest等多种设备，不同设备的系统误差'
	     '（飞行时间法vs.力量积分法）可能引入间接性偏倚，但因多数亚组k过小，设备类型未作为正式调节变量分析。'),
	    ('多臂研究选择策略的主观性。',
	     '具有多个干预组的研究（如R01含PT24/PT48两组，R16含PG/LPG两组）中，'
	     '选择哪个研究组纳入分析存在主观成分——本研究优先选择训练方案更"标准"的组，但这一选择可能偏向较高效应量。'),
	    ('训练依从性信息不充分。',
	     '大多数纳入研究未系统报告训练出勤率、退出原因和不良反应，无法评估实际训练量对效应量'
	     '的影响及干预中的潜在偏倚。'),
	    ('对照类型的异质性。',
	     '纳入研究包括无训练对照和维持常规训练对照两类，两者的效应量基准不同（常规训练对照的效应量预期较小），'
	     '但因各组k数不等，未单独检验对照类型对合并效应量的调节作用。'),
"""

# Replace:
# 	    ('训练安全性数据缺失。',
# 	     ...
# 	     '未来研究应系统报告不良事件和损伤发生率。'),
# ]
# WITH
# new_limitations + ]

out = []
i = 0
found = False
while i < len(lines):
    line = lines[i]
    if not found and '训练安全性数据缺失' in line:
        # Find the closing '],' for the limitations list
        j = i
        while j < len(lines):
            if lines[j].strip() == ']' or lines[j].strip() == ']' or (lines[j].strip() == ']' and j < i + 30):
                # Insert new limitations before the closing ]
                out.append(new_limitations)
                found = True
                # Add a new ] line
                out.append(']\n')
                # Skip to after the original ]
                i = j + 1
                break
            j += 1
        if not found:
            out.append(line)
            i += 1
    else:
        out.append(line)
        i += 1

if found:
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print('SUCCESS: Added 5 new limitations')
else:
    # Alternative: just append after line containing '训练安全性数据缺失'
    out2 = []
    for i, line in enumerate(lines):
        out2.append(line)
        if '未来研究应系统报告不良事件和损伤发生率' in line:
            # Next line should be '	    ),'
            # After that comes ']'
            # We need to insert after the '	    ),' line
            if i+2 < len(lines) and lines[i+2].strip() == ']':
                out2.append('	    ),\n')
                out2.append(new_limitations)
                # Skip the original ), and ]
                del out2[-2]  # Remove the ), we just added
                # Actually this is getting complicated. Let me do it simpler.
    print('Alternative approach needed')

# Simpler approach: find line numbers
for idx, line in enumerate(lines):
    if '训练安全性数据缺失' in line:
        print(f'Line {idx}: {line.strip()}')
    if idx > 820 and idx < 840:
        print(f'{idx}: {line.rstrip()}')
