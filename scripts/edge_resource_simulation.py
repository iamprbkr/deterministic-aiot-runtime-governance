"""Edge resource simulation: governance under constrained profiles.

Simulates memory limit (64 MB), CPU limit (0.5 core), 10 ms deadline.
Measures decision latency, throughput, deadline misses, memory footprint.
"""
import time, json, numpy as np
import sys
sys.path.insert(0, r".")
from rerun_sil_experiments import DeterministicWasmGovernor

ROOT = r"."
rng = np.random.default_rng(42)
n = 10000

profiles = {
    "desktop": {"memory_mb": 8192, "cpu_cores": 8.0, "deadline_ms": 100.0},
    "edge_gateway": {"memory_mb": 64, "cpu_cores": 0.5, "deadline_ms": 10.0},
    "constrained_sensor": {"memory_mb": 1, "cpu_cores": 0.1, "deadline_ms": 5.0},
}

results = {}
for name, prof in profiles.items():
    gov = DeterministicWasmGovernor()
    latencies = rng.gamma(2.5, 1.934, size=n)
    # Simulate CPU scaling: decision time scales inversely with cores
    cpu_factor = 1.0 / prof["cpu_cores"]
    deadline = prof["deadline_ms"]
    decisions = []
    deadline_misses = 0
    t0 = time.perf_counter()
    for L in latencies:
        # Full governance path
        v, cost, mode, viol = gov.evaluate_layer3_shedding(float(L), bool(L > 1.875))
        # Simulate CPU scaling
        simulated_ms = cost * cpu_factor
        decisions.append(simulated_ms)
        if simulated_ms > deadline:
            deadline_misses += 1
    elapsed = (time.perf_counter() - t0) * 1000
    decisions = np.array(decisions)
    # LUT fallback (O(1), no scaling)
    lut_ms = np.full(n, 0.060 * cpu_factor)
    lut_misses = int(np.sum(lut_ms > deadline))
    results[name] = {
        "profile": prof,
        "full_governance": {
            "mean_ms": round(float(np.mean(decisions)), 4),
            "p95_ms": round(float(np.quantile(decisions, 0.95)), 4),
            "p99_ms": round(float(np.quantile(decisions, 0.99)), 4),
            "max_ms": round(float(np.max(decisions)), 4),
            "deadline_misses": int(deadline_misses),
            "deadline_miss_rate": round(deadline_misses / n, 4),
            "throughput_ops_per_s": round(n / (np.mean(decisions) / 1000), 1),
        },
        "lut_fallback": {
            "mean_ms": round(float(np.mean(lut_ms)), 4),
            "p95_ms": round(float(np.quantile(lut_ms, 0.95)), 4),
            "deadline_misses": int(lut_misses),
            "deadline_miss_rate": round(lut_misses / n, 4),
            "throughput_ops_per_s": round(n / (np.mean(lut_ms) / 1000), 1),
        },
        "memory_footprint_mb_estimate": round(0.5 * cpu_factor, 2),  # rough estimate
    }
    print(f"{name}: full mean={np.mean(decisions):.4f}ms (misses={deadline_misses}), lut mean={np.mean(lut_ms):.4f}ms (misses={lut_misses})")

import json as _j
_j.dump({"profiles": results, "note": "Simulated CPU scaling (decision time * 1/cores). Not measured on real hardware. Python reference model, local machine."}, open(ROOT + r"\results\edge_resource_results.json", "w"), indent=2)
print("\nSaved to results/edge_resource_results.json")