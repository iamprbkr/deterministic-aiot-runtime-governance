# Deterministic Runtime Governance for Defensive AI in Web and IoT Systems

This repository contains a Python reference model and a reproducible **synthetic-input simulation harness** for four runtime-governance research questions. The current harness is useful for checking policy logic and metric computation, but it is not a public-dataset evaluation and does not measure a deployed WebAssembly runtime or physical IoT system.

## Current status and scope

The experiment harness deliberately labels the provenance and limitations of every research question. Do not describe its outputs as measurements of Edge-IIoTset, CIC-IoT2023, HAI v23.05, AgentDojo, InjecAgent, or a real WebAssembly deployment: the current script does not load those datasets or execute that runtime.

| Research question | Current implementation | What results mean |
|---|---|---|
| RQ1 — Layer 3 latency shedding | Generates gamma-distributed synthetic request latencies and applies a Python reference policy model | Simulated policy costs and budget violations under the specified synthetic workload; not measured OPA/Wasm latency |
| RQ2 — Layer 5 attestation | Generates synthetic benign/corrupted divergence scores and computes metrics from labels and scores | Classification behavior on the generated score distributions; not generalization to actual quantized models |
| RQ3 — Layer 4 replay gate | Generates stale-message cases and evaluates a configured wall-clock rule and causal sequence reference gate | Rejection rates for the generated corpus; not a universal replay-security proof |
| RQ4 — Layer 7 policy rotation | Generates latency samples from a configured distribution | Simulated latency distribution; not measured WebAssembly page-swap performance |

The previous harnesses included hard-coded metric overrides and generated synthetic CSVs in folders named after public datasets. Those practices have been removed from the supported path. `download_datasets.py.py` is retained as a deprecated compatibility stub and no longer fabricates dataset-like files.

## Requirements

- Python 3.10+
- NumPy

## Run the current harness

From the repository root:

```bash
python3 rerun_sil_experiments.py --seed 42 --output-dir results
```

Optional sample-size arguments:

```bash
python3 rerun_sil_experiments.py \
  --seed 42 \
  --requests 24862 \
  --models 10000 \
  --replays 5000 \
  --transitions 1000 \
  --output-dir results
```

The run creates:

- `results/experiment_results.json` — metadata, assumptions, computed metrics, and scope statements.
- `results/experiment_observations.csv` — per-observation inputs, decisions, and outputs.

Metrics are computed from generated observations; AUC, precision, false-positive rate, detection rate, latency summaries, and rejection rates are not overwritten with target values. A fixed seed and software environment should reproduce the observations and metrics; the JSON creation timestamp will differ between runs.

`run_experiments.py` is a compatibility entry point to the same supported harness, so there is only one authoritative simulation implementation.

## Metric interpretation notes

### RQ1 — Latency shedding

The generated baseline latency follows a gamma distribution. The policy model uses a configured threshold and fallback cost. The reported jitter field is the sample standard deviation of generated governed latencies; it is not a direct measurement of timer jitter or a physical control loop.

### RQ2 — Post-quantization attestation

The harness computes the infinity-norm divergence and derives threshold predictions, confusion-matrix metrics, and ROC AUC from generated labels and scores. A SHA-256 digest checks byte identity against a trusted reference; it is not a calibrated behavioral score. A meaningful binary-integrity baseline requires actual reference/candidate binary artifacts and a prespecified corruption model, so no SHA-256 behavioral detection rate is reported here.

### RQ3 — Causal replay gate

The synthetic replay cases are stale by construction. The wall-clock baseline uses the configured apparent-age window, while the causal reference gate checks duplicate identifiers, exact next sender sequence, and causal dependencies. The implementation is a reference model: it does not provide authenticated epochs, durable non-rollbackable state, or atomic distributed commits. The rates therefore do not establish production-grade replay protection.

### RQ4 — Policy rotation

Latency samples are generated from a clipped normal distribution. These samples test summary-statistic and ceiling calculations only. A runtime performance claim requires instrumenting the actual policy-rotation implementation and preserving raw timings on a specified platform.

## Requirements for a dataset-backed evaluation

Before calling any experiment dataset-driven, document and implement:

1. Official dataset source, version, license, and download date.
2. SHA-256 hashes of the source files and the exact files used.
3. The selected records, columns, labels, exclusions, and preprocessing steps.
4. The mapping from dataset observations to the governance experiment's inputs and outcomes.
5. Train/calibration/test separation where relevant, plus sample counts and class balance.
6. A script that loads the real files and emits the exact observations consumed by the metric calculation.

A dataset's presence in a folder, its name in a comment, or a generated synthetic CSV is not evidence that the dataset was used.

## Requirements for implementation-level performance claims

To claim measured WebAssembly or hardware latency, instrument the actual runtime path, identify the hardware and software versions, report warm-up and repetition procedures, preserve raw observations, and report distributions and uncertainty—not just a mean. Simulated latency parameters must not be presented as measured execution times.

## Reproducibility checklist

- [ ] Run the harness twice with the same seed and compare the observation CSVs and metrics.
- [ ] Record Python and NumPy versions.
- [ ] Preserve the JSON summary and raw observations with each manuscript revision.
- [ ] Update the manuscript only from the generated results and clearly identify the results as synthetic simulation unless dataset or runtime instrumentation has been added.
- [ ] Do not claim formal guarantees from simulation alone; state assumptions and provide proofs or implementation-level tests separately.

## License

See [LICENSE](LICENSE).
