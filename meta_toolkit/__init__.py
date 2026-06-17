# meta_toolkit - 体育科学 Meta 分析工具链
# Python + R 混合架构，当前先实现纯 Python 层
from meta_toolkit.reader import read_template, merge_study_info
from meta_toolkit.effects import compute_effects_continuous, compute_effects_dichotomous
from meta_toolkit.pooling import meta_pool
from meta_toolkit.output import summary_table, print_results, format_effect_original
from meta_toolkit.viz import draw_forest, draw_funnel, egger_test
from meta_toolkit.r_bridge import meta_pool_r, is_r_available
