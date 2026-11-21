# Reproducibility Guide

## Environment

- **OS:** Windows 10/11 (Linux/macOS also supported)
- **Python:** 3.10+ (tested on 3.11)
- **Dependencies:** numpy, pandas, scikit-learn, matplotlib, pymodbus (optional)

## Installation

```bash
# Clone repository
git clone https://github.com/iamprbkr/deterministic-aiot-runtime-governance.git
cd deterministic-aiot-runtime-governance

# Install Python dependencies
pip install numpy pandas scikit-learn matplotlib pymodbus

# Verify installation
python3 -c "import numpy, pandas, sklearn; print('OK')"
```

## One-Command Reproduction

```bash
bash run_eval.sh
```

This runs the main harness with seed 42 and generates all result JSONs.

## Step-by-Step Reproduction

### 1. Main Harness (M1-M4)
```bash
python3 rerun_sil_experiments.py --seed 42 --output-dir results
```
Expected output: 4 result JSONs in `results/` directory.

### 2. Property-Based Tests
```bash
python3 tests/test_properties.py
```
Expected: 110,000 cases, 9 properties, 0 failures.

### 3. Real Dataset Experiments
```bash
python3 scripts/run_edgeiiot_experiment.py       # Edge-IIoTset (50k flows)
python3 scripts/defensive_ai_scenario.py        # Defensive AI (1k rules)
python3 scripts/run_web_traffic_experiment.py   # Web traffic (10k requests)
python3 scripts/run_ciciot_full_experiment.py  # CIC-IoT2023 (7k flows)
python3 scripts/run_cicids2018_experiment.py   # CIC-IDS-2018 (19k flows)
python3 scripts/run_new_datasets_experiment.py  # TON_IoT, CSIC 2010, IDS2025
```

### 4. Real Artifact Demos
```bash
python3 scripts/m3_real_artifact_demo.py        # M3 logistic regression
python3 scripts/m3_neural_quantization_demo.py # M3 neural network (int8)
```

### 5. Measured Overhead
```bash
python3 scripts/measure_overhead.py
```

### 6. Real Ablation
```bash
python3 scripts/run_ablation_real.py
```

### 7. Adversarial Resilience
```bash
python3 scripts/adversarial_resilience_test.py
```

### 8. Concurrency Stress
```bash
python3 scripts/test_concurrency_stress.py
```

### 9. Cross-Dataset Generalization
```bash
python3 scripts/exp20_cross_dataset.py
```

### 10. External Validation
```bash
python3 scripts/exp28_fuzzing.py                 # 100k fuzzed cases
python3 scripts/openplc_modbus_real.py           # OpenPLC Modbus/TCP
python3 scripts/thermal_dvfs_real.py             # Thermal/DVFS analysis
```

### 11. Regenerate Figures
```bash
python3 scripts/gen_validation_figures_v2.py
python3 scripts/gen_thermal_figure_real.py
python3 scripts/gen_openplc_figure_real.py
```

## Renode Emulation (optional)

Requires Renode v1.16.0+:
```bash
# Compile governance stub for ARM
arm-none-eabi-gcc -O0 -mcpu=cortex-m4 -mthumb --specs=nosys.specs governance_stub.c -o governance_stub.elf

# Run in Renode
"C:\Program Files\Renode\bin\Renode.exe" --console --disable-xwt renode_real.resc
```

## QEMU Cross-ISA (optional)

Requires QEMU v11.1.0+ and arm-none-eabi-gcc:
```bash
# Compile for ARM
arm-none-eabi-gcc -O0 -mcpu=cortex-m4 -mthumb --specs=nosys.specs governance_stub.c -o governance_stub.elf

# Run in QEMU
qemu-system-arm -M b-l475e-iot01a -nographic -kernel governance_stub.elf

# Read memory via GDB
arm-none-eabi-gdb governance_stub.elf -ex "target remote localhost:1234" -ex "x /8wx 0x200008c4"
```

## Data Reproducibility

All numerical results are stored in `results/*.json`. Each file contains:
- Experiment parameters (seed, sample size, etc.)
- Raw measurements
- Computed metrics (false-allow, false-deny, accuracy, etc.)
- Conclusion

To verify reproducibility:
1. Run any experiment script
2. Compare output JSON with committed version
3. Results should be identical (deterministic, seed 42)

## File Inventory

| Directory | Contents | Count |
|-----------|----------|-------|
| `scripts/` | Experiment scripts | 50+ |
| `results/` | Result JSON files | 55+ |
| `figures/` | Regenerated figures (300 dpi) | 9 |
| `tests/` | Property-based tests | 1 |

## Troubleshooting

- **Missing datasets**: Some experiments require datasets in `datasets/`. Download from Kaggle or use provided samples.
- **Docker required**: OpenPLC runtime requires Docker. Modbus simulation works without Docker.
- **Renode/QEMU**: Optional. Core experiments run without them.