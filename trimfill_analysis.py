"""
Trim-and-Fill Analysis for Meta-Analysis
Computes adjusted effect sizes accounting for publication bias
"""
import json
import subprocess
import tempfile
import os
import csv
from pathlib import Path


def _find_rscript():
    """Locate Rscript executable."""
    candidates = [
        r'C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe',
        r'C:\Program Files\R\R-4.6.0\bin\Rscript.exe',
    ]
    for c in candidates:
        if os.path.isfile(c):
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


def load_effects(csv_path):
    studies = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            studies.append({
                'study_id': row['study_id'],
                'author': row['author'], 'year': row['year'],
                'exp_n': int(float(row['exp_n'])),
                'ctrl_n': int(float(row['ctrl_n'])),
                'yi': float(row['yi_change']),
                'vi': float(row['vi_change']),
                'data_note': row.get('data_note', ''),
            })
    return studies


def is_strict(s):
    return '✅' in s.get('data_note', '')


def run_trimfill(yi, vi, side='right'):
    """Run trim-and-fill analysis via R/metafor."""
    rscript = _find_rscript()
    if rscript is None:
        raise RuntimeError('Rscript not found')
    
    script_path = Path(__file__).parent / 'meta_toolkit' / 'run_trimfill.R'
    if not script_path.exists():
        raise FileNotFoundError(f'R script not found: {script_path}')
    
    input_data = {
        'yi': yi,
        'vi': vi,
        'method': 'REML',
        'side': side,
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json',
                                     delete=False, encoding='utf-8') as f:
        json.dump(input_data, f)
        input_path = f.name
    
    output_path = input_path.replace('.json', '_out.json')
    
    cmd = [rscript, str(script_path),
           '--input', input_path,
           '--output', output_path]
    
    env = os.environ.copy()
    env['LANGUAGE'] = 'en'
    env['LC_ALL'] = 'C'
    
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace',
                            timeout=120, env=env)
    
    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
        try:
            os.unlink(input_path)
        except OSError:
            pass
        raise RuntimeError(f'R script failed (exit {result.returncode}):\n{error_msg}')
    
    with open(output_path, 'r', encoding='utf-8') as f:
        output = json.load(f)
    
    try:
        os.unlink(input_path)
        os.unlink(output_path)
    except OSError:
        pass
    
    return output


def main():
    csv_path = "D:/桌面/科研训练/analysis_ready_effects.csv"
    all_studies = load_effects(csv_path)
    strict = [s for s in all_studies if is_strict(s)]
    wide = [s for s in all_studies if 'VJ' not in s.get('data_note', '')]
    
    output_dir = Path("D:/桌面/科研训练/output")
    output_dir.mkdir(exist_ok=True)
    
    results = {}
    
    for name, pool in [("strict_hand_on_hip", strict), ("wide_all_cmj", wide)]:
        print(f"\n{'='*70}")
        print(f"  Trim-and-Fill Analysis: {name} ({len(pool)} studies)")
        print(f"{'='*70}")
        
        yi = [s['yi'] for s in pool]
        vi = [s['vi'] for s in pool]
        labels = [f"{s['author']} {s['year']}" for s in pool]
        
        # Run trim-and-fill (try both sides)
        for side in ['right', 'left']:
            try:
                tf_result = run_trimfill(yi, vi, side=side)
                
                print(f"\n  Side: {side} (imputing {tf_result.get('k_missing', '?')} studies)")
                print(f"  Original:  k = {tf_result['k_original']}, g = {tf_result['beta_original']:.4f}")
                print(f"             95% CI: [{tf_result['ci_low_original']:.4f}, {tf_result['ci_upp_original']:.4f}]")
                print(f"             I2 = {tf_result['I2_original']:.1f}%")
                print(f"  Adjusted:  k = {tf_result['k_trimfill']}, g = {tf_result['beta_trimfill']:.4f}")
                print(f"             95% CI: [{tf_result['ci_low_trimfill']:.4f}, {tf_result['ci_upp_trimfill']:.4f}]")
                print(f"             I2 = {tf_result['I2_trimfill']:.1f}%")
                
                delta_g = tf_result['beta_trimfill'] - tf_result['beta_original']
                pct_change = (delta_g / tf_result['beta_original']) * 100
                print(f"  Change:    delta_g = {delta_g:+.4f} ({pct_change:+.1f}%)")
                
                # Store results
                results[name] = {
                    'side': side,
                    'k_missing': tf_result['k_missing'],
                    'beta_original': tf_result['beta_original'],
                    'ci_original': [tf_result['ci_low_original'], tf_result['ci_upp_original']],
                    'I2_original': tf_result['I2_original'],
                    'beta_trimfill': tf_result['beta_trimfill'],
                    'ci_trimfill': [tf_result['ci_low_trimfill'], tf_result['ci_upp_trimfill']],
                    'I2_trimfill': tf_result['I2_trimfill'],
                    'delta_g': delta_g,
                    'pct_change': pct_change,
                }
                
                break  # Use first successful side
                
            except Exception as e:
                print(f"  Error with side={side}: {e}")
                continue
    
    # Save results to JSON
    output_file = output_dir / 'trimfill_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"  Summary")
    print(f"{'='*70}")
    for name, r in results.items():
        print(f"\n  {name}:")
        print(f"    Original:  g = {r['beta_original']:.4f} [{r['ci_original'][0]:.4f}, {r['ci_original'][1]:.4f}]")
        print(f"    Adjusted:  g = {r['beta_trimfill']:.4f} [{r['ci_trimfill'][0]:.4f}, {r['ci_trimfill'][1]:.4f}]")
        print(f"    Change:    {r['pct_change']:+.1f}% ({r['k_missing']} studies imputed)")
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
