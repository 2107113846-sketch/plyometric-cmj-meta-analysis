"""
R/metafor 桥接模块

通过 subprocess + Rscript 调用 R 脚本，不依赖 rpy2。
数据通过 JSON 文件在 Python 和 R 之间交换。
"""

import json
import subprocess
import tempfile
import os
from pathlib import Path
import numpy as np


def _find_rscript():
    """Locate Rscript executable."""
    candidates = [
        r'C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe',
        r'C:\Program Files\R\R-4.6.0\bin\Rscript.exe',
    ]
    for c in candidates:
        if os.path.isfile(c):
            # Quick validation: try to run with --version
            try:
                result = subprocess.run(
                    [c, '--version'],
                    capture_output=True, timeout=10,
                    encoding='utf-8', errors='replace',
                    env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'}
                )
                if result.returncode == 0:
                    return c
            except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
                continue
    return None


def _r_available():
    return _find_rscript() is not None


def _convert_numpy(obj):
    """Recursively convert numpy types to native Python for JSON serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float64, np.float32, np.int64, np.int32)):
        return obj.item()
    if isinstance(obj, dict):
        return {k: _convert_numpy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_numpy(v) for v in obj]
    return obj


def meta_pool_r(yi, vi, labels=None, method='REML', forest_plot=None):
    """
    Use R/metafor to pool effect sizes via Rscript subprocess.

    Parameters:
        yi: effect sizes (1D array)
        vi: variances (1D array)
        labels: study labels (list of str, optional)
        method: 'REML' (default), 'DL', 'ML', 'FE', etc.
        forest_plot: output path for forest plot PNG (optional)

    Returns:
        dict with pooled results (same keys as pooling.meta_pool)
    """
    rscript = _find_rscript()
    if rscript is None:
        raise RuntimeError(
            'Rscript not found. Please install R from https://cran.r-project.org/')

    script_path = Path(__file__).parent / 'run_meta.R'
    if not script_path.exists():
        raise FileNotFoundError(f'R script not found: {script_path}')

    # Prepare input data
    yi_list = np.asarray(yi, dtype=float).tolist()
    vi_list = np.asarray(vi, dtype=float).tolist()
    if labels is None:
        labels = [f'Study {i+1}' for i in range(len(yi_list))]

    input_data = {
        'yi': yi_list,
        'vi': vi_list,
        'method': method,
        'labels': labels,
    }

    # Write to temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                     delete=False, encoding='utf-8') as f:
        json.dump(_convert_numpy(input_data), f)
        input_path = f.name

    output_path = input_path.replace('.json', '_out.json')

    # Build command
    cmd = [rscript, str(script_path),
           '--input', input_path,
           '--output', output_path]

    # Run
    env = os.environ.copy()
    env['LANGUAGE'] = 'en'
    env['LC_ALL'] = 'C'

    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace',
                            timeout=120, env=env)

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
        # Clean up temp files
        try:
            os.unlink(input_path)
        except OSError:
            pass
        raise RuntimeError(f'R script failed (exit {result.returncode}):\n{error_msg}')

    # Read output
    with open(output_path, 'r', encoding='utf-8') as f:
        output = json.load(f)

    # Clean up temp files
    try:
        os.unlink(input_path)
        os.unlink(output_path)
    except OSError:
        pass

    # Generate forest plot if requested
    if forest_plot is not None:
        plot_input = dict(input_data)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                         delete=False, encoding='utf-8') as f:
            json.dump(_convert_numpy(plot_input), f)
            plot_in = f.name
        plot_out = plot_in.replace('.json', '_plot_out.json')

        cmd_plot = [rscript, str(script_path),
                    '--input', plot_in,
                    '--output', plot_out,
                    '--plot', str(forest_plot)]
        subprocess.run(cmd_plot, capture_output=True, text=True,
                       encoding='utf-8', errors='replace',
                       timeout=120, env=env)

        try:
            os.unlink(plot_in)
            os.unlink(plot_out)
        except OSError:
            pass

    # Map R output to familiar keys
    mapped = {
        'beta': output.get('beta'),
        'se': output.get('se'),
        'ci_low': output.get('ci_low'),
        'ci_upp': output.get('ci_upp'),
        'z': output.get('z'),
        'pval': output.get('pval'),
        'tau2': output.get('tau2'),
        'tau2_ci_low': output.get('tau2_ci_low'),
        'tau2_ci_upp': output.get('tau2_ci_upp'),
        'I2': output.get('I2'),
        'I2_ci_low': output.get('I2_ci_low'),
        'I2_ci_upp': output.get('I2_ci_upp'),
        'H2': output.get('H2'),
        'Q': output.get('Q'),
        'Q_pval': output.get('Q_pval'),
        'k': output.get('k'),
        'model': output.get('model', f'Random-effects ({method})'),
        'pred_low': output.get('pred_low'),
        'pred_upp': output.get('pred_upp'),
        'egger_intercept': output.get('egger_intercept'),
        'egger_pval': output.get('egger_pval'),
        'study_effects': output.get('study_effects'),
        'study_se': output.get('study_se'),
        'study_ci_low': output.get('study_ci_low'),
        'study_ci_upp': output.get('study_ci_upp'),
        'study_weights': output.get('study_weights'),
        'study_labels': output.get('study_labels'),
    }

    return mapped


def is_r_available():
    """Check if R is installed and metafor is available."""
    rscript = _find_rscript()
    if rscript is None:
        return False
    result = subprocess.run(
        [rscript, '--no-save', '--no-restore', '-e',
         'library(metafor, lib.loc="C:/Users/PC/AppData/Local/R/win-library/4.6"); cat("OK")'],
        capture_output=True, timeout=30,
        encoding='utf-8', errors='replace',
        env={**os.environ, 'LANGUAGE': 'en', 'LC_ALL': 'C'})
    return result.returncode == 0 and 'OK' in result.stdout
