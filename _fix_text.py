# -*- coding: utf-8 -*-
"""Fix remaining manuscript text references."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

path = 'D:/桌面/科研训练/export_manuscript_docx.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix: R19 data estimation limitation
old = "本研究中有四项数据涉及估算或近似：（a）R19 Michailidis（2018）的SD从CI反推估算（≈0.80cm）；\n" \
     "         '（b）R23 Rensing（2015）的对照组SD以干预组SD近似（5.35cm）；（c）R29 Vescovi（2008）的后测均值"
new = "本研究中有三项数据涉及估算或近似，另有一项因数据来源问题被排除：\n" \
      "         '（a）R19 Michailidis（2018, k=1）因CI反推存在SE/SD歧义（效应量被高估约4.0倍），已从严格池排除，排除后合并效应量变化Δg=−0.016；\n" \
      "         '（b）R23 Rensing（2015）的对照组SD以干预组SD近似（5.35cm）；（c）R29 Vescovi（2008）的后测均值"

if old in content:
    content = content.replace(old, new)
    print('FIXED: R19 data estimation limitation text')
else:
    print('NOT FOUND in content')

# Also fix the old g values still lingering in limitation text
old_lim_g = '四项均通过敏感性分析验证——分别剔除对应研究后，合并效应量的变化范围为Δg=−0.016至+0.049'
new_lim_g = '三项估算均通过敏感性分析验证——分别剔除R23/R29/R16后，合并效应量的变化范围为Δg=−0.016至+0.049'
if old_lim_g in content:
    content = content.replace(old_lim_g, new_lim_g)
    print('FIXED: old g sensitivity range text')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Saved')
