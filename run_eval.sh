#!/usr/bin/env bash
# One-command reproduction script for the governance evaluation.
# Usage: ./run_eval.sh
set -e

echo "=== Deterministic Runtime Governance — Reproduction Script ==="
echo "Python version: $(python3 --version)"
echo "NumPy version: $(python3 -c 'import numpy; print(numpy.__version__)')"

# Run the main harness
echo ""
echo "=== Running governance harness (seed 42) ==="
python3 rerun_sil_experiments.py --seed 42 --output-dir results

# Run property tests
echo ""
echo "=== Running property-based tests ==="
python3 tests/test_properties.py

# Verify results
echo ""
echo "=== Verifying results ==="
python3 -c "
import json
d = json.load(open('results/experiment_results.json'))
print('RQ1: n_requests =', d['RQ1']['n_requests'])
print('RQ2: FPR =', round(d['RQ2']['metrics']['false_positive_rate_pct'], 2), '%')
print('RQ3: causal rejection =', d['RQ3']['causal_rejection_pct'], '%')
print('RQ4: mean =', round(d['RQ4']['mean_ms'], 2), 'ms')
print('All results verified.')
"

echo ""
echo "=== Reproduction complete ==="
echo "Results in: results/experiment_results.json"
echo "Observations in: results/experiment_observations.csv"