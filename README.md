# Plyometric Training Effects on CMJ Height: Meta-Analysis

Systematic review and meta-analysis of the effects of plyometric training on countermovement jump (CMJ) height, with effect size estimation and dose-response relationship stratified by arm position.

## PROSPERO Registration

CRD420261422906

## Repository Structure

```
├── meta_toolkit/              # Core analysis tools
│   ├── effects.py             # Effect size calculation
│   ├── pooling.py             # Meta-analysis pooling
│   ├── r_bridge.py            # R/metafor bridge
│   ├── run_meta.R             # R script for meta-analysis
│   ├── run_trimfill.R         # Trim-and-fill analysis
│   ├── viz.py                 # Visualization (forest/funnel plots)
│   └── ...
├── output/                    # Analysis results
│   ├── Manuscript_Draft_Methods_Results.md
│   ├── Table1_Study_Characteristics.csv
│   ├── PEDro_Score_Final.csv
│   ├── analysis_ready_effects.csv
│   ├── trimfill_results.json
│   ├── forest_*.png           # Forest plots
│   ├── funnel_*.png           # Funnel plots
│   └── PRISMA_flow_diagram.png
├── analysis_ready_effects.csv # Complete effect size dataset
├── screening_merged_30studies.csv
├── publication_bias.py        # Publication bias analysis
├── trimfill_analysis.py       # Trim-and-fill analysis
├── meta_regression.py         # Meta-regression
├── sensitivity_analysis.py    # Sensitivity analyses
└── export_manuscript_docx.py  # Export to Word
```

## Requirements

### Python

```bash
pip install -r requirements.txt
```

### R

- R >= 4.0
- packages: `metafor`, `jsonlite`

## Usage

1. Effect size calculation:
```bash
python clean_and_compute_effects.py
```

2. Meta-analysis:
```bash
python run_analysis.py
```

3. Publication bias & trim-and-fill:
```bash
python publication_bias.py
python trimfill_analysis.py
```

4. Generate figures:
```bash
python generate_forest.py
```

## Data

- `analysis_ready_effects.csv`: 29 RCTs with pre-computed effect sizes (Hedges' g)
- `screening_merged_30studies.csv`: Study characteristics extracted from included studies

## Citation

If you use this code, please cite:

```
Mo Y. (2026). Plyometric Training Effects on CMJ Height: Meta-Analysis Code.
GitHub. https://github.com/[username]/plyometric-cmj-meta-analysis
```

## License

MIT
