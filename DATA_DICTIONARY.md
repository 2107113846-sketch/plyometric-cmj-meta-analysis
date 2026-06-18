# 数据提取表字段说明 (Data Dictionary)

## 文件: `data_extraction_master.csv`
- **91 行** = 91 篇纳入论文
- **88 列** = 研究元数据 + 参与者特征 + 干预参数 + 多结局指标 + 质量评价
- **编码**: UTF-8 BOM (Excel 可直接打开)

---

## 一、研究标识 (Study Identification)

| 字段 | 说明 | 示例 |
|------|------|------|
| `seq` | 序号 1-91 | `1` |
| `pmid` | PubMed ID (唯一标识) | `34027922` |
| `first_author` | 第一作者姓氏 | `Ramirez-Campillo R` |
| `year` | 发表年份 | `2021` |
| `title` | 论文标题 | `Effects of...` |
| `doi` | DOI 号 | `10.1519/JSC...` |
| `filename` | 本地 PDF 文件名 | `chaabene2017.pdf` |
| `table_source` | 工作簿来源表 | `0-第4关推测` |
| `extraction_status` | 提取状态: `pending` / `partial` / `complete` / `flagged` | `pending` |

## 二、研究特征 (Study Characteristics)

| 字段 | 说明 | 选项/示例 |
|------|------|-----------|
| `study_design` | 研究设计 | `RCT` / `quasi-experimental` / `crossover` |
| `country` | 国家 | `Tunisia` / `Brazil` |
| `population` | 人群类型 | `athletes` / `students` / `general` |
| `sport` | 运动项目 | `soccer` / `basketball` / `volleyball` |
| `sex` | 性别 | `male` / `female` / `mixed` |
| `age_mean` | 平均年龄 | `14.5` |
| `age_sd` | 年龄标准差 | `1.2` |
| `age_unit` | 年龄单位 | `years` |
| `training_level` | 训练水平 | `trained` / `recreational` / `elite` |
| `maturity_group` | 成熟度 | `pre-pubertal` / `circa-pubertal` / `post-pubertal` / `adult` |

## 三、样本量 (Sample Size)

| 字段 | 说明 |
|------|------|
| `n_total` | 总样本量 |
| `n_int` | 干预组样本量 |
| `n_ctrl` | 对照组样本量 |
| `group_int_name` | 干预组名称 (默认: `Plyometric`) |
| `group_ctrl_name` | 对照组名称 (默认: `Control`) |

## 四、干预参数 (Intervention Details)

| 字段 | 说明 | 选项/示例 |
|------|------|-----------|
| `int_category` | 干预大类 | `plyometric` / `combined` / `resistance` |
| `plyo_type` | 跳跃类型 | `CMJ` / `DJ` / `SJ` / `mixed` / `horizontal` / `vertical` |
| `int_duration_wk` | 干预周期 (周) | `8` |
| `int_freq_pw` | 每周频率 | `2` (次/周) |
| `int_session_min` | 每节课时长 (分钟) | `45` |
| `int_total_contacts` | 总跳跃触地次数 | `960` |
| `int_intensity` | 训练强度 | `low` / `moderate` / `high` / `maximal` |
| `int_surface` | 训练地面 | `grass` / `indoor` / `force plate` |
| `ctrl_activity` | 对照组活动 | `regular training` / `no training` |

## 五、CMJ 结局指标 (Countermovement Jump — 主要结局)

| 字段 | 说明 |
|------|------|
| `cmj_reported` | 是否报告 CMJ: `yes` / `no` |
| `cmj_equipment` | 测量设备: `force plate` / `contact mat` / `Optojump` / `Vertec` |
| `cmj_pre_mean_int` | 干预组前测均值 |
| `cmj_pre_sd_int` | 干预组前测标准差 |
| `cmj_post_mean_int` | 干预组后测均值 |
| `cmj_post_sd_int` | 干预组后测标准差 |
| `cmj_pre_mean_ctrl` | 对照组前测均值 |
| `cmj_pre_sd_ctrl` | 对照组前测标准差 |
| `cmj_post_mean_ctrl` | 对照组后测均值 |
| `cmj_post_sd_ctrl` | 对照组后测标准差 |
| `cmj_unit` | 单位: `cm` / `m` / `inches` |
| `cmj_timepoint_post_wk` | 后测时间点 (第几周) |

## 六、SJ 结局指标 (Squat Jump)

列名同 CMJ 结构: `sj_reported`, `sj_pre_mean_int`, `sj_pre_sd_int`, ...

## 七、DJ 结局指标 (Drop Jump)

列名同 CMJ 结构: `dj_reported`, `dj_pre_mean_int`, `dj_pre_sd_int`, ...

## 八、短跑 (Sprint)

| 字段 | 说明 |
|------|------|
| `sprint_distance_m` | 距离 (米): `10` / `20` / `30` |
| `sprint_unit` | 单位: `s` |

其余列名同 CMJ 结构。

## 九、灵敏性 (Agility)

| 字段 | 说明 |
|------|------|
| `agility_test` | 测试名称: `T-test` / `505` / `Illinois` |

## 十、其他 (Other & Quality)

| 字段 | 说明 |
|------|------|
| `other_outcomes` | 其他结局指标 (自由文本) |
| `randomization` | 随机化方法: `yes` / `no` / `unclear` |
| `blinding` | 盲法: `single` / `double` / `none` |
| `dropout_pct` | 脱落率 (%) |
| `itt_analysis` | 意向性分析: `yes` / `no` |
| `data_source` | 数据来源: `text` / `table` / `figure` / `calculated` |
| `needs_calculation` | 需要计算: 如 `SD from SE` / `change SD` |
| `extraction_notes` | 提取备注 |

---

## 填写优先级

1. **必须先填**: `pmid`, `first_author`, `year` ✅ (已自动填充)
2. **核心数据**: `n_int`, `n_ctrl`, CMJ 的 pre/post mean±SD
3. **干预参数**: `int_duration_wk`, `int_freq_pw`, `plyo_type`
4. **次要结局**: SJ, DJ, Sprint (如有)
5. **质量评估**: `randomization`, `dropout_pct`
