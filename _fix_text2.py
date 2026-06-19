# -*- coding: utf-8 -*-
"""Fix the R19 limitation text by direct line replacement."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = 'D:/桌面/科研训练/export_manuscript_docx.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the data estimation limitation
# Old pattern
old_pattern = (
    "本研究中有四项数据涉及估算或近似：（a）R19 Michailidis（2018）的SD从CI反推估算（≈0.80cm）；"
)
new_text = (
    "本研究中有三项数据涉及估算或近似，另有一项因数据来源问题被排除："
    "（a）R19 Michailidis（2018, k=1）因CI反推存在SE/SD歧义"
    "（效应量被高估约4.0倍），已从严格池排除，排除后合并效应量变化Δg=−0.016；"
)

if old_pattern in content:
    content = content.replace(old_pattern, new_text)
    print('FIXED: R19 limitation text')
else:
    print('Pattern not found - checking fragments')

old_pattern2 = "四项均通过敏感性分析验证——分别剔除对应研究后，合并效应量的变化范围为Δg=−0.016至+0.049"
new_text2 = "三项估算均通过敏感性分析验证——分别剔除R23/R29/R16后，合并效应量的变化范围为Δg=−0.016至+0.049"
if old_pattern2 in content:
    content = content.replace(old_pattern2, new_text2)
    print('FIXED: old g sensitivity range')

# Also add the R06 note explicitly - search for the PEDro correction
old_pedro = "分配隐藏仅7%，评估者盲法仅15%"
if old_pedro in content:
    print(f'PEDro note already present: {old_pedro}')

# Also fix the Cohen's d note in limitations
# Fix "四项" -> "三项" in the general text
content = content.replace(
    "四项均通过敏感性分析验证",
    "三项均通过敏感性分析验证"
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
