"""Experiment 4: Resource envelope profiling (3 tiers)."""
import json, time, numpy as np
ROOT = r"."
rng = np.random.default_rng(42)
n = 10000
latencies = rng.gamma(2.5, 1.934, size=n)

tiers = {
    "Tier1_UltraConstrained": {"cpu": 0.15, "ram_mb": 128, "deadline_ms": 5.0},
    "Tier2_MidEdge": {"cpu": 0.25, "ram_mb": 256, "deadline_ms": 10.0},
    "Tier3_Gateway": {"cpu": 0.5, "ram_mb": 512, "deadline_ms": 20.0},
}

results = {}
for name, t in tiers.items():
    cpu_factor = 1.0 / t["cpu"]
    deadline = t["deadline_ms"]
    full_lat = np.array([min(l, 1.875) * cpu_factor if l > 1.875 else l * cpu_factor for l in latencies])
    # Actually: if l > tau_crit, fallback cost 0.06 * cpu_factor
    full_lat = np.where(latencies > 1.875, 0.060 * cpu_factor, latencies * cpu_factor)
    misses = int(np.sum(full_lat > deadline))
    lut_lat = np.full(n, 0.060 * cpu_factor)
    lut_misses = int(np.sum(lut_lat > deadline))
    mem_footprint = 0.5 * cpu_factor  # rough estimate in MB
    oom = mem_footprint > t["ram_mb"]
    results[name] = {
        "tier": t,
        "full_governance": {
            "mean_ms": round(float(np.mean(full_lat)), 4),
            "p95_ms": round(float(np.quantile(full_lat, 0.95)), 4),
            "p99_ms": round(float(np.quantile(full_lat, 0.99)), 4),
            "max_ms": round(float(np.max(full_lat)), 4),
            "deadline_misses": misses,
            "deadline_miss_rate": round(misses / n, 4),
            "throughput_ops_per_s": round(n / (np.mean(full_lat) / 1000), 1),
            "memory_footprint_mb": round(mem_footprint, 2),
            "oom_risk": bool(oom),
        },
        "lut_fallback": {
            "mean_ms": round(float(np.mean(lut_lat)), 4),
            "p95_ms": round(float(np.quantile(lut_lat, 0.95)), 4),
            "deadline_misses": lut_misses,
            "deadline_miss_rate": round(lut_misses / n, 4),
            "throughput_ops_per_s": round(n / (np.mean(lut_lat) / 1000), 1),
        },
    }
    print(f"{name}: full mean={np.mean(full_lat):.4f}ms misses={misses} ({100*misses/n:.2f}%), lut mean={np.mean(lut_lat):.4f}ms misses={lut_misses}")

import json as _j
_j.dump({"tiers": results, "note": "Simulated CPU scaling (decision time * 1/cores). Not measured on real hardware. Python reference model, local machine."}, open(ROOT + r"\results\exp4_resource_results.json", "w"), indent=2)
print("\nSaved to results/exp4_resource_results.json")