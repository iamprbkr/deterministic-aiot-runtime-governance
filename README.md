# Deterministic Runtime Governance for Defensive AI in Web and IoT Systems

## Overview

This repository contains a Python reference model and reproducible experiment harness for **deterministic runtime governance** of AI-generated operations in web and IoT systems. The governance rule is:

$$G_k = A_k \land P_k \land F_k \land C_k \land B_k \land I_k \land D_k$$

Where each predicate evaluates a distinct security dimension:

| Predicate | Name | Description |
|-----------|------|-------------|
| $A_k$ | Authority | Is the requesting entity authenticated and authorized? |
| $P_k$ | Policy | Does the operation comply with the active policy? |
| $F_k$ | Freshness | Is the request within the temporal validity window? |
| $C_k$ | Context | Is the operational context valid and consistent? |
| $B_k$ | Behavioural | Does the operation match expected behavioural patterns? |
| $I_k$ | Integrity | Is the artefact (model, config) integrity verified? |
| $D_k$ | Budget | Is the execution within resource/time budget? |

**Verdict function:** QUARANTINE > DENY > DEFER > ALLOW (fail-closed)

## Repository Structure

```
├── rerun_sil_experiments.py    # Main harness (M1-M4 reference model)
├── run_experiments.py          # Compatibility entry point
├── tests/
│   └── test_properties.py      # 110,000 property-based test cases (9 properties)
├── scripts/                    # 50+ experiment scripts
├── results/                    # 55+ result JSON files
├── figures/                    # 9 regenerated figures (300 dpi)
├── Dockerfile                  # Container definition
├── docker-compose.yml          # 3-service testbed
├── .gitignore                  # Ignore rules
└── LICENSE                     # MIT
```

## Quick Start

### Prerequisites
- Python 3.10+
- NumPy, pandas, scikit-learn
- Optional: pymodbus (for OpenPLC experiment), matplotlib (for figures)

### One-Command Reproduction
```bash
bash run_eval.sh
```

### Manual Reproduction
```bash
# Main harness (seed 42)
python3 rerun_sil_experiments.py --seed 42 --output-dir results

# Property-based tests (110,000 cases)
python3 tests/test_properties.py

# Real dataset experiments
python3 scripts/run_edgeiiot_experiment.py       # Edge-IIoTset (50k flows)
python3 scripts/defensive_ai_scenario.py        # Defensive AI (1k rules)
python3 scripts/run_web_traffic_experiment.py    # Web traffic (10k requests)
python3 scripts/run_ciciot_full_experiment.py   # CIC-IoT2023 (7k flows)
python3 scripts/run_cicids2018_experiment.py    # CIC-IDS-2018 (19k flows)

# Real artifact demos
python3 scripts/m3_real_artifact_demo.py        # M3 logistic regression
python3 scripts/m3_neural_quantization_demo.py  # M3 neural network (int8)

# Measured overhead
python3 scripts/measure_overhead.py

# Real ablation
python3 scripts/run_ablation_real.py

# Adversarial resilience
python3 scripts/adversarial_resilience_test.py

# Concurrency stress
python3 scripts/test_concurrency_stress.py

# Cross-dataset generalization
python3 scripts/exp20_cross_dataset.py

# External validation
python3 scripts/exp28_fuzzing.py                 # 100k fuzzed cases
python3 scripts/openplc_modbus_real.py           # OpenPLC Modbus/TCP (500 transactions)
python3 scripts/thermal_dvfs_real.py            # Thermal/DVFS analysis
python3 scripts/gen_validation_figures_v2.py     # Regenerate figures
```

## Experiment Inventory (50+ scripts, 55+ result JSONs)

### Security Enforcement (13 experiments)
| Script | Result | Key Metric |
|--------|--------|------------|
| `run_edgeiiot_experiment.py` | Edge-IIoTset governance | 0.03% false-allow (11/42,500) |
| `defensive_ai_scenario.py` | AI-generated firewall rules | 6% FA, 5% FD, 94.5% accuracy |
| `run_web_traffic_experiment.py` | Web traffic governance | 19.86% FA, 23.34% FD, 78.4% accuracy |
| `adversarial_resilience_test.py` | 6 attack types | 100% block, 0% FP |
| `test_concurrency_stress.py` | Thread safety | 0 leakage, 227k-321k ops/s |
| `exp09_resource_exhaustion_dos.py` | DoS resilience | O(1) governance, no blowup |
| `exp12_toctou_race.py` | TOCTOU race | 0 races, atomic handling |
| `exp14_cross_layer_smuggling.py` | Cross-layer smuggling | 0 smuggled |
| `exp15_split_brain.py` | Split-brain | 0 split-brain events |
| `exp16_policy_hotreload.py` | Policy hot-reload | 0 downtime |
| `exp17_low_slow_stealth.py` | Low-and-slow stealth | 83.3% detected |
| `exp19_audit_logging.py` | Tamper-evident audit | 10k entries, hash chain verified |
| `exp31_cross_tenant.py` | Cross-tenant isolation | 0 cross-tenant leaks |

### Edge Constraints (7 experiments)
| Script | Result | Key Metric |
|--------|--------|------------|
| `measure_overhead.py` | Measured overhead | 0.47 μs/decision |
| `exp10_concept_drift.py` | Concept drift | Adaptation verified |
| `exp11_timing_sidechannel.py` | Timing side-channel | No leakage |
| `exp13_cold_start.py` | Cold start | <1ms startup |
| `exp23_thermal_dvfs.py` | Thermal/DVFS | 0% deadline misses |
| `thermal_dvfs_real.py` | Real DVFS analysis | 0.335-1.674 μs |
| `exp22` (Renode) | Firmware emulation | 70 cycles, 0.875 μs, 256 bytes SRAM |

### Real Data (6 experiments)
| Script | Dataset | Result |
|--------|---------|--------|
| `run_edgeiiot_experiment.py` | Edge-IIoTset (50k) | 0.03% false-allow |
| `run_ciciot_full_experiment.py` | CIC-IoT2023 (7k) | 74.13% FA, 8.15% FD |
| `run_cicids2018_experiment.py` | CIC-IDS-2018 (19k) | 0% FA, 96.31% FD |
| `run_new_datasets_experiment.py` | TON_IoT (20k) | 13.99% FA, 0% FD |
| `run_new_datasets_experiment.py` | CSIC 2010 (20k) | 98.31% FA, 0% FD |
| `run_new_datasets_experiment.py` | IDS2025 (20k) | 0.34% FA, 77.57% FD |

### Real Artifacts (2 experiments)
| Script | Artifact | Result |
|--------|----------|--------|
| `m3_real_artifact_demo.py` | Logistic regression (int8) | Δ∞=0.0047, ALLOW |
| `m3_neural_quantization_demo.py` | MLP (int8) | Δ∞=1.0, QUARANTINE |

### Formal Verification (5 experiments)
| Script | Method | Result |
|--------|--------|--------|
| `test_properties.py` | Property-based (9 properties) | 110,000 cases, 0 failures |
| `exp18` (formal bound) | ε^k bound | Proven |
| `exp20_cross_dataset.py` | Cross-dataset | 34.67% FA on CIC-IoT2023 |
| `exp24_mia.py` | Membership inference | AUC ~0.5 (no leakage) |
| `exp28_fuzzing.py` | Fuzzing | 100k cases, 0 violations |

### Privacy/Governance (6 experiments)
| Script | Focus | Result |
|--------|-------|--------|
| `exp25_pii_redaction.py` | PII redaction | 9 types detected |
| `exp26_zero_egress.py` | Zero egress | 93.75% reduction |
| `exp27_risk_adaptive.py` | Risk-adaptive policy | Verified |
| `exp29_swarm.py` | Swarm governance | Verified |
| `exp30_supply_chain.py` | Supply chain | Verified |
| `exp32_self_healing.py` | Self-healing | Verified |

### External Validation (4 experiments)
| Script/Tool | Method | Result |
|-------------|--------|--------|
| Renode v1.16.0 | ARM Cortex-M4 emulation | 373 instructions, all 7 verdicts correct |
| QEMU v11.1.0 | Cross-ISA verification | 7/7 parity (Python x86 = ARM) |
| `openplc_modbus_real.py` | Modbus/TCP (pymodbus) | 500 transactions, 0% FA, 0% FD |
| `thermal_dvfs_real.py` | DVFS analysis | 0.335-1.674 μs, 0% misses |

## Reproducibility

### One-Command Reproduction
```bash
bash run_eval.sh
```

### Seed
All experiments use seed 42 for reproducibility.

### Results
All numerical results are stored in `results/*.json`. Each JSON file contains:
- Experiment parameters
- Raw measurements
- Computed metrics
- Conclusion

### Figures
All figures are regenerated at 300 dpi in `figures/`. Regenerate with:
```bash
python3 scripts/gen_validation_figures_v2.py
python3 scripts/gen_thermal_figure_real.py
python3 scripts/gen_openplc_figure_real.py
```

## Key Results Summary

| Metric | Value |
|--------|-------|
| False-allow rate (Edge-IIoTset) | 0.03% (11/42,500) |
| Governance overhead | 0.47 μs/decision |
| M3 attestation overhead | 13.24 μs/model |
| M4 causal gate overhead | 2.15 μs/command |
| Property tests | 110,000 cases, 0 failures |
| Concurrency stress | 0 leakage, 227k-321k ops/s |
| Renode instructions | 373 (measured) |
| Cross-ISA parity | 7/7 (100%) |
| OpenPLC false-allow | 0% (20/20 denied) |
| OpenPLC mean response | 539.54 μs |

## FAQ

**Q: Are the results real or simulated?**
A: All dataset experiments use real published datasets (Edge-IIoTset, CIC-IoT2023, CIC-IDS-2018, TON_IoT, CSIC 2010, IDS2025). Renode results: binary executed, 373 instructions measured, 7/7 verdicts correct (cycle counts are estimates). QEMU: functional verification + cross-ISA parity (Python x86 = ARM, 7/7). Thermal/DVFS: simulated (base from Renode, frequency scaling modeled). OpenPLC: real Modbus/TCP communication (pymodbus), but not real OpenPLC runtime (requires Docker).

**Q: What about Docker/WSL?**
A: Docker Desktop is installed but the daemon is not running. OpenPLC runtime requires Docker (not available). Multi-container testbed (docker-compose.yml) is defined but not executed. WSL2 is available but not used for experiments. See DOCKER_WSL_STATUS.md for details.

**Q: What requires real hardware?**
A: (1) Renode cycle-accurate profiling (needs Renode profiler API), (2) QEMU true cross-ISA (needs x86 C compiler), (3) Thermal/DVFS (needs real CPU with cpufreq + thermal sensors), (4) OpenPLC runtime (needs Docker or native build), (5) Multi-container testbed (needs Docker daemon).

**Q: Can I reproduce the results?**
A: Yes. Run `bash run_eval.sh` with seed 42. All scripts are in `scripts/`. All results are in `results/*.json`.

**Q: What's the governance rule?**
A: $G_k = A_k \land P_k \land F_k \land C_k \land B_k \land I_k \land D_k$ (7-predicate conjunction). Verdict: QUARANTINE > DENY > DEFER > ALLOW (fail-closed).

**Q: What datasets are used?**
A: Edge-IIoTset (50k), CIC-IoT2023 (7k), CIC-IDS-2018 (19k), TON_IoT (20k sampled), CSIC 2010 (20k sampled), IDS2025 (20k sampled), USGS live telemetry (24 readings).

**Q: How do I cite this work?**
A: [Paper citation to be added upon publication]

## License

MIT License. See [LICENSE](LICENSE).

## Contact

For questions about the experiments or code, please open an issue.