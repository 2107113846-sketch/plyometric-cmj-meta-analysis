"""
Generate PRISMA 2020 Flow Diagram for Plyometric CMJ Meta-analysis.
Publication-quality vector output (PNG + SVG).
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import json
import os

# ── Load data ──────────────────────────────────────────
json_path = os.path.join(os.path.dirname(__file__), 'PRISMA_flow.json')
with open(json_path, 'r') as f:
    data = json.load(f)

# ── Figure setup ───────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 9,
    'axes.titlesize': 11,
    'axes.labelsize': 9,
})
fig, ax = plt.subplots(1, 1, figsize=(10, 13))
ax.set_xlim(0, 10)
ax.set_ylim(0, 13)
ax.axis('off')

# Color palette
COLOR_MAIN = '#4472C4'       # blue for main boxes
COLOR_EXCLUDE = '#D9534F'    # red for exclusions
COLOR_FINAL = '#70AD47'      # green for final inclusion
COLOR_BG = '#F2F2F2'         # light gray for reason boxes
FG_COLOR = '#333333'
LIGHT_BG = '#FAFAFA'

# ── Helper functions ───────────────────────────────────
def draw_box(ax, x, y, w, h, text, color=COLOR_MAIN, fontsize=9,
             bold=False, text_color='white', edge_color=None, lw=1.5):
    """Draw a rounded box with centered text."""
    if edge_color is None:
        edge_color = color
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.08", facecolor=color,
                         edgecolor=edge_color, linewidth=lw, zorder=3)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            fontweight=weight, color=text_color, zorder=4)


def draw_plain_box(ax, x, y, w, h, text, color=COLOR_BG, fontsize=8,
                   text_color=FG_COLOR, edge_color='#CCCCCC', lw=1):
    """Draw a light background box with dark text."""
    box = FancyBboxPatch((x - w/2, y - h/2), w, h,
                         boxstyle="round,pad=0.06", facecolor=color,
                         edgecolor=edge_color, linewidth=lw, zorder=2)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=text_color, zorder=3)


def draw_arrow(ax, x, y1, y2, color='#666666', lw=1.2):
    """Draw a downward arrow from (x, y1) to (x, y2)."""
    ax.annotate('', xy=(x, y2 + 0.08), xytext=(x, y1 - 0.08),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle='arc3,rad=0'),
                zorder=2)


def draw_side_arrow(ax, x_from, y, x_to, color='#666666', lw=1.2):
    """Draw horizontal arrow."""
    ax.annotate('', xy=(x_to - 0.15, y), xytext=(x_from + 0.15, y),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle='arc3,rad=0'),
                zorder=2)


# ── Section labels ─────────────────────────────────────
sx = 0.4  # label x position
ax.text(sx, 12.60, 'Identification', fontsize=11, fontweight='bold', color=COLOR_MAIN)
ax.text(sx, 9.55, 'Screening', fontsize=11, fontweight='bold', color=COLOR_MAIN)
ax.text(sx, 5.35, 'Eligibility', fontsize=11, fontweight='bold', color=COLOR_MAIN)
ax.text(sx, 1.70, 'Included', fontsize=11, fontweight='bold', color=COLOR_FINAL)

# Horizontal separator lines with section labels
for yy, label in [(12.35, 'Identification'), (9.30, 'Screening'), (5.10, 'Eligibility'), (1.45, 'Included')]:
    ax.axhline(y=yy, xmin=0.04, xmax=0.96, color='#CCCCCC', lw=0.8, ls='--', zorder=0)

# ── IDENTIFICATION ──────────────────────────────────────
# Box: Records identified from databases
cid = data['Identification']
draw_box(ax, 5, 12.10, 4.8, 0.65,
         f"Records identified from databases & registers\n(n = {cid['Records_identified']})",
         color=COLOR_MAIN, fontsize=9, bold=True)

# Sub-text: databases
ax.text(5, 11.68, f"PubMed (n = 78)  •  Scopus (n = 36)  •  WoS (n = 14)  •  Google Scholar (n = 7)",
        ha='center', va='center', fontsize=7, color='#888888', style='italic')

# Arrow down
draw_arrow(ax, 5, 11.75, 10.90)

# ── SCREENING ───────────────────────────────────────────
# Records screened
draw_box(ax, 5, 10.60, 4.8, 0.65,
         f"Records screened\n(n = {cid['Records_identified']})",
         color=COLOR_MAIN, fontsize=9)

# Side arrow: excluded at title/abstract
excl_ta = cid['Records_identified'] - data['Screening']['Full_text_assessed']
draw_side_arrow(ax, 7.55, 10.60, 8.90)
draw_plain_box(ax, 9.55, 10.60, 1.6, 0.55,
               f"Records excluded\n(n = {excl_ta})",
               color='#FFF2CC', edge_color='#E0C36A', fontsize=7.5)

# Arrow down
draw_arrow(ax, 5, 10.25, 9.80)

# Full-text assessed
draw_box(ax, 5, 9.50, 4.8, 0.65,
         f"Full-text articles assessed for eligibility\n(n = {data['Screening']['Full_text_assessed']})",
         color=COLOR_MAIN, fontsize=9)

# Side arrow: excluded full-text
draw_side_arrow(ax, 7.55, 9.50, 8.90)
draw_plain_box(ax, 9.55, 9.50, 1.6, 0.55,
               f"Full-text excluded\n(n = {data['Eligibility']['Full_text_excluded']})",
               color='#F4CCCC', edge_color='#D9534F', fontsize=7.5)

# Arrow down
draw_arrow(ax, 5, 9.15, 6.10)

# ── ELIGIBILITY ─────────────────────────────────────────
# Exclusion reasons box
reasons = data['Eligibility']['Reasons']
reason_text = (
    f"No CMJ height reported (n = {reasons['No_CMJ_height_reported']})\n"
    f"No independent control group (n = {reasons['No_independent_control_group']})\n"
    f"Not randomised controlled trial (n = {reasons['Not_RCT']})\n"
    f"CMJ with arm swing, no separate no-arm CMJ (n = {reasons['CMJ_with_arm_swing_not_reported_separately']})\n"
    f"Duplicate or overlapping sample (n = {reasons['Duplicate_or_overlapping_sample']})\n"
    f"Other reasons (n = {reasons['Other']})"
)
draw_plain_box(ax, 5, 5.20, 5.2, 1.15, reason_text,
               color='#FFF5F5', edge_color='#D9534F', fontsize=7.5, lw=1.2)

# Arrow down
draw_arrow(ax, 5, 4.60, 3.50)

# ── INCLUDED ────────────────────────────────────────────
# Main inclusion box
inc = data['Included']
draw_box(ax, 5, 3.15, 5.0, 0.75,
         f"Studies included in meta-analysis\n(n = {inc['Studies_in_meta_analysis']})",
         color=COLOR_FINAL, fontsize=9.5, bold=True)

# Three sub-boxes
box_w = 2.2
box_h = 0.55
box_y = 2.10

bx_positions = [
    (2.0, f"Strict hands-on-hips CMJ\n(n = {inc['Strict_hand_on_hip']})", '#70AD47'),
    (5.0, f"Arm position unclear\n(n = {inc['Arm_unclear']})", '#FFC000'),
    (8.0, f"CMJA with arm swing\n(n = {inc['CMJA_with_arm']})", '#ED7D31'),
]

for x_pos, label, clr in bx_positions:
    draw_box(ax, x_pos, box_y, box_w, box_h, label,
             color=clr, fontsize=7.5, bold=True, lw=1.2)

# Small arrows from main to sub-boxes
for x_pos in [2.0, 5.0, 8.0]:
    ax.plot([5, x_pos], [2.75, 2.40], color='#999999', lw=0.8, zorder=1)

# VJ sensitivity note
draw_plain_box(ax, 5, 1.30, 3.8, 0.40,
               f"VJ with arm swing sensitivity subgroup: n = {inc['VJ_sensitivity_subgroup']}",
               color='#FCE4D6', edge_color='#ED7D31', fontsize=7.5)

# ── Title ───────────────────────────────────────────────
fig.suptitle('PRISMA 2020 Flow Diagram', fontsize=13, fontweight='bold',
             y=0.985, x=0.06, ha='left', va='top')

# Subtitle
ax.text(0.4, 12.85,
         'Plyometric Training Effects on Countermovement Jump (CMJ) Height',
         fontsize=9, color='#666666', va='center')

# Caption note at bottom
ax.text(5, 0.55,
        'PRISMA 2020 flow diagram for updated systematic review and meta-analysis.\n'
        'From: Page MJ, McKenzie JE, Bossuyt PM, et al. BMJ 2021;372:n71.',
        ha='center', va='center', fontsize=7, color='#999999', style='italic')

# ── Save ────────────────────────────────────────────────
output_dir = os.path.dirname(__file__)
png_path = os.path.join(output_dir, 'PRISMA_flow_diagram.png')
svg_path = os.path.join(output_dir, 'PRISMA_flow_diagram.svg')

fig.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
fig.savefig(svg_path, bbox_inches='tight', facecolor='white', edgecolor='none')

print("PRISMA diagram saved:")
print(f"   PNG: {png_path}")
print(f"   SVG: {svg_path}")
plt.close()
