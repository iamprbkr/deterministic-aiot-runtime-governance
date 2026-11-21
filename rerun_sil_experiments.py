#!/usr/bin/env python3
"""Reproducible synthetic-input SIL harness for the AIoT governance prototype.

PURPOSE: Main harness for M1-M4 governance mechanisms (synthetic data)
INPUTS: CLI args (--seed, --requests, --models, --replays, --transitions, --output-dir)
OUTPUTS: experiment_results.json, experiment_observations.csv
DATA TYPE: SIMULATED (synthetic workloads, not real datasets or hardware)
PAPER ALIGNMENT: RQ1 (M1 policy), RQ2 (M2 attestation), RQ3 (M3/M4 replay), RQ4 (governance)

IMPORTANT SCOPE:
- This script generates synthetic workloads. It does not load Edge-IIoTset,
  CIC-IoT2023, or HAI v23.05, and it does not execute a real WebAssembly runtime.
- RQ1 and RQ4 latency values are simulated values, not hardware measurements.
- RQ2 is a controlled synthetic classification experiment; it is not evidence
  of generalization to real quantized model binaries.
- RQ3 evaluates explicitly constructed stale/replay cases. Its rates apply only
  to the generated test corpus and configured wall-clock policy.

Outputs:
  experiment_results.json  Summary, provenance, and per-RQ definitions
  experiment_observations.csv  Per-observation synthetic records

Dependencies: Python 3.10+, numpy. No metric is hard-coded; metrics are computed
from generated observations and decisions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_VERSION = "2.0.0"
DEFAULT_SEED = 42


class DeterministicWasmGovernor:
    """Python reference model of selected governance decisions; not Wasm itself."""

    def __init__(self, tau_crit_ms: float = 1.875, tau_budget_ms: float = 2.50,
                 delta_bound: float = 0.008, rotation_ceiling_ms: float = 150.0):
        self.tau_crit_ms = tau_crit_ms
        self.tau_budget_ms = tau_budget_ms
        self.delta_bound = delta_bound
        self.rotation_ceiling_ms = rotation_ceiling_ms
        self.consumed_ids: set[str] = set()
        self.sender_sequence: dict[int, int] = {}

    def evaluate_layer3_shedding(self, raw_latency_ms: float, dos_flag: bool = False):
        """Simulated policy decision. Returned latency is a modelled cost, not measured time."""
        if raw_latency_ms > self.tau_crit_ms or dos_flag:
            latency_ms = 0.060  # configured LUT fallback cost assumption
            mode = "LUT_FALLBACK"
            verdict = "ALLOW" if raw_latency_ms <= self.tau_budget_ms else "DENY"
        else:
            latency_ms = raw_latency_ms
            mode = "WASM_FULL_SIMULATED"
            verdict = "ALLOW"
        return verdict, latency_ms, mode, latency_ms > self.tau_budget_ms

    def evaluate_layer5_attestation(self, fp32_probs: np.ndarray, int4_probs: np.ndarray):
        """Compare probability vectors; this does not attest binary integrity."""
        delta = float(np.max(np.abs(fp32_probs - int4_probs)))
        return ("ALLOW" if delta <= self.delta_bound else "QUARANTINE"), delta

    def evaluate_layer7_policy_selection(self, jurisdiction: str,
                                         available_policies: list[str]) -> tuple[str, bool]:
        """M1: Sovereignty Policy Matrix Selector (reference implementation).

        Selects the applicable policy for a given jurisdiction from the
        available policy set. Returns (selected_policy, permitted).
        """
        # Simple reference: jurisdiction maps to a policy prefix.
        # In production this would consult a sovereignty matrix.
        selected = None
        for p in available_policies:
            if p.startswith(jurisdiction.split('_')[0].lower()):
                selected = p
                break
        if selected is None and available_policies:
            selected = available_policies[0]
        permitted = selected is not None
        return selected or "NONE", permitted

    def evaluate_layer4_epoch_gate(self, sender_id: int, cmd_id: str,
                                   v_msg: list[int], v_local: list[int]):
        """Reference causal gate: exact next sender sequence, no unseen dependencies.

        This reference model is intentionally not represented as production-grade
        cryptographic replay protection: it has no authenticated epoch, durable
        storage, or atomic distributed commit.
        """
        if cmd_id in self.consumed_ids:
            return "DENY", "REPLAY_DUPLICATE"
        if not (0 <= sender_id < len(v_msg) == len(v_local)):
            return "DENY", "INVALID_CLOCK"
        if v_msg[sender_id] != v_local[sender_id] + 1:
            return "DENY", "SEQUENCE_NOT_NEXT"
        for j in range(len(v_msg)):
            if j != sender_id and v_msg[j] > v_local[j]:
                return "DENY", "UNMET_CAUSAL_DEPENDENCY"
        self.consumed_ids.add(cmd_id)
        return "ALLOW", "FRESH_COMMAND"


def auc_rank(y_true: np.ndarray, scores: np.ndarray) -> float:
    """ROC AUC using average ranks; returns NaN if either class is absent."""
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    ranks = np.empty(len(scores), dtype=float)
    i = 0
    while i < len(scores):
        j = i + 1
        while j < len(scores) and sorted_scores[j] == sorted_scores[i]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2.0  # average of 1-based ranks i+1..j
        i = j
    rank_sum_pos = float(np.sum(ranks[y_true == 1]))
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    div = lambda a, b: (a / b) if b else None
    return {
        "n": int(len(y_true)), "positive_count": int(np.sum(y_true == 1)),
        "negative_count": int(np.sum(y_true == 0)),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "detection_rate_recall_pct": 100.0 * div(tp, tp + fn) if tp + fn else None,
        "false_positive_rate_pct": 100.0 * div(fp, fp + tn) if fp + tn else None,
        "precision_pct": 100.0 * div(tp, tp + fp) if tp + fp else None,
        "accuracy_pct": 100.0 * div(tp + tn, len(y_true)),
        "roc_auc": auc_rank(y_true, scores),
    }


def run(seed: int, output_dir: Path, n_requests: int, n_models: int,
        n_replays: int, n_transitions: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    observations: list[dict[str, Any]] = []
    governor = DeterministicWasmGovernor()

    # RQ1: explicitly synthetic request-latency workload.
    tau_crit, tau_budget = governor.tau_crit_ms, governor.tau_budget_ms
    opa = rng.gamma(shape=2.5, scale=1.934, size=n_requests)
    governed, modes = [], []
    for i, raw in enumerate(opa):
        # Attack flag is an explicit synthetic workload rule, not a dataset label.
        is_dos = bool(raw > tau_crit)
        verdict, latency, mode, violation = governor.evaluate_layer3_shedding(float(raw), is_dos)
        governed.append(latency)
        modes.append(mode)
        observations.append({"rq": "RQ1", "observation_id": i, "input_type": "synthetic_latency",
                             "baseline_latency_ms": float(raw), "governed_latency_ms": float(latency),
                             "mode": mode, "verdict": verdict,
                             "baseline_budget_violation": bool(raw > tau_budget),
                             "governed_budget_violation": bool(violation)})
    governed = np.asarray(governed)
    rq1 = {
        "input_provenance": "synthetic gamma-distributed latency; no public dataset loaded",
        "n_requests": n_requests,
        "baseline_mean_ms": float(np.mean(opa)), "baseline_median_ms": float(np.median(opa)),
        "baseline_p95_ms": float(np.quantile(opa, .95)), "baseline_max_ms": float(np.max(opa)),
        "baseline_budget_violations": int(np.sum(opa > tau_budget)),
        "baseline_budget_violation_pct": float(100 * np.mean(opa > tau_budget)),
        "governed_mean_ms": float(np.mean(governed)), "governed_median_ms": float(np.median(governed)),
        "governed_p95_ms": float(np.quantile(governed, .95)), "governed_max_ms": float(np.max(governed)),
        "governed_budget_violations": int(np.sum(governed > tau_budget)),
        "governed_budget_violation_pct": float(100 * np.mean(governed > tau_budget)),
        "governed_latency_std_ms": float(np.std(governed, ddof=1)) if n_requests > 1 else 0.0,
        "mode_counts": {str(k): int(v) for k, v in zip(*np.unique(modes, return_counts=True))},
        "latency_semantics": "simulated policy costs; not measured runtime or hardware latency",
        "assumptions": {"tau_crit_ms": tau_crit, "tau_budget_ms": tau_budget,
                        "lut_fallback_cost_ms": 0.060, "gamma_shape": 2.5, "gamma_scale_ms": 1.934},
    }

    # RQ2: synthetic score distribution. Compute every metric from scores/labels.
    # Exactly 5% positives are generated for transparent sample accounting.
    n_pos = max(1, int(round(n_models * 0.05)))
    y_true = np.zeros(n_models, dtype=int)
    pos_idx = rng.choice(n_models, size=n_pos, replace=False)
    y_true[pos_idx] = 1
    benign_scores = rng.beta(a=1.5, b=250.0, size=n_models)
    corrupt_scores = rng.beta(a=8.0, b=12.0, size=n_models)
    delta_scores = np.where(y_true == 1, corrupt_scores, benign_scores)
    threshold = governor.delta_bound
    y_pred = (delta_scores > threshold).astype(int)
    rq2_metrics = classification_metrics(y_true, y_pred, delta_scores)
    for i in range(n_models):
        observations.append({"rq": "RQ2", "observation_id": i, "input_type": "synthetic_divergence_score",
                             "label_corrupted": int(y_true[i]), "delta_infinity_norm": float(delta_scores[i]),
                             "threshold": threshold, "predicted_corrupted": int(y_pred[i])})
    rq2 = {
        "input_provenance": "synthetic beta-distributed divergence scores; no HAI records or model binaries loaded",
        "metrics": rq2_metrics,
        "decision_threshold": threshold,
        "score_generation": {"benign_beta": [1.5, 250.0], "corrupted_beta": [8.0, 12.0],
                             "positive_fraction_target": 0.05},
        "sha256_baseline": {
            "status": "not_computed_as_a_behavioral_detection_metric",
            "reason": "A digest tests byte identity against a trusted reference; it is not a calibrated behavioral score. A valid comparison requires actual reference and candidate binary artifacts and a prespecified corruption model."
        },
        "interpretation_limit": "Synthetic proof-of-pipeline only; not evidence of generalization to real quantized models.",
    }

    # RQ3: synthetic stale replay corpus with an explicit wall-clock policy.
    # Replays are stale by sequence state; timestamps and drift are independently generated.
    # Wall-clock rejects when absolute apparent age exceeds the configured freshness window.
    freshness_window_s = 300.0
    true_age_s = rng.uniform(1.0, 7200.0, size=n_replays)
    clock_offset_s = rng.uniform(-1800.0, 1800.0, size=n_replays)
    apparent_age_s = true_age_s + clock_offset_s
    wall_reject = np.abs(apparent_age_s) > freshness_window_s
    causal_governor = DeterministicWasmGovernor()
    causal_reject = np.zeros(n_replays, dtype=bool)
    v_local_replay = [100, 150, 200]
    for i in range(n_replays):
        # Each message has a unique ID but a sender sequence at or below the
        # receiver's accepted sequence: a stale-command replay by construction.
        v_msg_stale = [int(rng.integers(0, 101)), 120, 180]
        verdict, reason = causal_governor.evaluate_layer4_epoch_gate(
            sender_id=0, cmd_id=f"stale-replay-{i}", v_msg=v_msg_stale,
            v_local=v_local_replay)
        causal_reject[i] = verdict == "DENY"
        observations.append({"rq": "RQ3", "observation_id": i, "input_type": "synthetic_stale_replay",
                             "true_message_age_s": float(true_age_s[i]), "clock_offset_s": float(clock_offset_s[i]),
                             "apparent_age_s": float(apparent_age_s[i]), "wallclock_rejected": bool(wall_reject[i]),
                             "causal_rejected": bool(causal_reject[i]), "causal_reason": reason, "replay_label": 1})
    # Separate legitimate-command acceptance test, so false rejection is not hidden.
    n_legit = n_replays
    legit_accepted = 0
    for i in range(n_legit):
        local = [100 + i, 150, 200]
        msg = [101 + i, 150, 200]
        g = DeterministicWasmGovernor()
        verdict, _ = g.evaluate_layer4_epoch_gate(0, f"legit-{i}", msg, local)
        legit_accepted += verdict == "ALLOW"
    rq3 = {
        "input_provenance": "synthetically generated stale vector-clock cases; no HAI or agent dataset loaded",
        "n_replay_cases": n_replays,
        "wallclock_freshness_window_s": freshness_window_s,
        "wallclock_rejected": int(np.sum(wall_reject)),
        "wallclock_rejection_pct": float(100 * np.mean(wall_reject)),
        "causal_rejected": int(np.sum(causal_reject)),
        "causal_rejection_pct": float(100 * np.mean(causal_reject)),
        "n_legitimate_control_cases": n_legit,
        "legitimate_causal_accepted": int(legit_accepted),
        "legitimate_causal_acceptance_pct": float(100 * legit_accepted / n_legit) if n_legit else None,
        "assumptions": {"true_age_distribution": "Uniform(1, 7200) seconds",
                        "clock_offset_distribution": "Uniform(-1800, 1800) seconds",
                        "wallclock_rule": "reject if absolute apparent age exceeds 300 seconds"},
        "interpretation_limit": "Rates apply only to this generated corpus and rule; no universal replay guarantee is established.",
    }

    # RQ4: synthetic latency samples; not actual WebAssembly page-swap timing.
    rot_mean_parameter, rot_sd_parameter = 118.23, 5.12
    rot = np.clip(rng.normal(rot_mean_parameter, rot_sd_parameter, size=n_transitions), 100.0, 145.0)
    breaches = rot >= governor.rotation_ceiling_ms
    for i, value in enumerate(rot):
        observations.append({"rq": "RQ4", "observation_id": i, "input_type": "synthetic_rotation_latency",
                             "rotation_latency_ms": float(value), "ceiling_ms": governor.rotation_ceiling_ms,
                             "ceiling_breach": bool(breaches[i])})
    rq4 = {
        "input_provenance": "synthetic normal-distribution latency samples with clipping; no Wasm runtime measured",
        "n_transitions": n_transitions,
        "mean_ms": float(np.mean(rot)), "median_ms": float(np.median(rot)),
        "sd_ms_sample": float(np.std(rot, ddof=1)) if n_transitions > 1 else 0.0,
        "p95_ms": float(np.quantile(rot, .95)), "max_ms": float(np.max(rot)),
        "ceiling_ms": governor.rotation_ceiling_ms,
        "ceiling_breaches": int(np.sum(breaches)),
        "ceiling_breach_pct": float(100 * np.mean(breaches)),
        "generation_parameters": {"normal_mean_ms": rot_mean_parameter, "normal_sd_ms": rot_sd_parameter,
                                  "clip_min_ms": 100.0, "clip_max_ms": 145.0},
    }

    results: dict[str, Any] = {
        "metadata": {
            "script_version": SCRIPT_VERSION, "seed": seed,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version, "platform": platform.platform(),
            "numpy_version": np.__version__,
            "scope": "synthetic-input reference-model simulation; not public-dataset evaluation or measured Wasm hardware performance",
            "reproducibility_note": "Same seed and software versions should reproduce generated observations and metrics; created_utc is expected to differ.",
        },
        "RQ1": rq1, "RQ2": rq2, "RQ3": rq3, "RQ4": rq4,
    }
    result_path = output_dir / "experiment_results.json"
    with result_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, allow_nan=False)

    obs_path = output_dir / "experiment_observations.csv"
    fieldnames = sorted({k for row in observations for k in row})
    with obs_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(observations)

    # Console output mirrors the machine-readable computed metrics.
    print("=" * 78)
    print("SYNTHETIC-INPUT SIL REFERENCE-MODEL EVALUATION")
    print("This script does not load public datasets or measure real Wasm hardware.")
    print(f"Seed: {seed} | Outputs: {output_dir.resolve()}")
    print("=" * 78)
    print("RQ1 | Layer 3 synthetic latency workload")
    print(f"  Baseline mean: {rq1['baseline_mean_ms']:.3f} ms | budget violations: {rq1['baseline_budget_violation_pct']:.2f}%")
    print(f"  Governed max: {rq1['governed_max_ms']:.3f} ms | budget violations: {rq1['governed_budget_violation_pct']:.2f}% | sample SD: {rq1['governed_latency_std_ms']:.3f} ms")
    print("RQ2 | Layer 5 synthetic divergence classification")
    print(f"  Detection: {rq2_metrics['detection_rate_recall_pct']:.2f}% | AUC: {rq2_metrics['roc_auc']:.4f} | FPR: {rq2_metrics['false_positive_rate_pct']:.2f}% | precision: {rq2_metrics['precision_pct']:.2f}%")
    print("  SHA-256 behavioral comparison: NOT COMPUTED (not a comparable behavioral score)")
    print("RQ3 | Layer 4 synthetic stale replay corpus")
    print(f"  Wall-clock rejection: {rq3['wallclock_rejection_pct']:.2f}% | causal-gate stale rejection: {rq3['causal_rejection_pct']:.2f}%")
    print(f"  Legitimate causal command acceptance: {rq3['legitimate_causal_acceptance_pct']:.2f}%")
    print("RQ4 | Layer 7 synthetic rotation-latency samples")
    print(f"  Mean: {rq4['mean_ms']:.2f} ms | max: {rq4['max_ms']:.2f} ms | ceiling breaches: {rq4['ceiling_breach_pct']:.2f}%")
    print("=" * 78)
    print(f"Wrote {result_path} and {obs_path}")
    print("Use these outputs as synthetic simulation results only; do not label them dataset-driven or measured runtime results.")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--requests", type=int, default=24862)
    parser.add_argument("--models", type=int, default=10000)
    parser.add_argument("--replays", type=int, default=5000)
    parser.add_argument("--transitions", type=int, default=1000)
    args = parser.parse_args()
    for name in ("requests", "models", "replays", "transitions"):
        if getattr(args, name) < 1:
            parser.error(f"--{name} must be >= 1")
    run(args.seed, args.output_dir, args.requests, args.models, args.replays, args.transitions)


if __name__ == "__main__":
    main()
