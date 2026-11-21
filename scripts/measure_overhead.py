"""Measured overhead: time the governor's admission decision."""
import time, json, numpy as np
import sys
sys.path.insert(0, r".")
from rerun_sil_experiments import DeterministicWasmGovernor

gov = DeterministicWasmGovernor()
rng = np.random.default_rng(42)
n = 10000

# Passthrough (no governance): just return ALLOW
t0 = time.perf_counter()
for i in range(n):
    _ = "ALLOW"
passthrough_ms = (time.perf_counter() - t0) * 1000

# Full governance: evaluate_layer3_shedding
latencies = rng.gamma(2.5, 1.934, size=n)
t0 = time.perf_counter()
for L in latencies:
    gov.evaluate_layer3_shedding(float(L), bool(L > 1.875))
full_ms = (time.perf_counter() - t0) * 1000

# M3 attestation
ref_p = rng.random((n, 8)); int4_p = ref_p + rng.normal(0, 0.001, (n,8))
t0 = time.perf_counter()
for i in range(n):
    gov.evaluate_layer5_attestation(ref_p[i], int4_p[i])
m3_ms = (time.perf_counter() - t0) * 1000

# M4 causal gate
t0 = time.perf_counter()
for i in range(n):
    gov2 = DeterministicWasmGovernor()
    gov2.evaluate_layer4_epoch_gate(0, f"cmd_{i}", [i+1,0], [i,0])
m4_ms = (time.perf_counter() - t0) * 1000

result = {
    "n_operations": n,
    "passthrough_ms_total": round(passthrough_ms, 3),
    "full_governance_ms_total": round(full_ms, 3),
    "governance_overhead_ms_total": round(full_ms - passthrough_ms, 3),
    "governance_overhead_per_decision_us": round((full_ms - passthrough_ms) / n * 1000, 3),
    "m3_attestation_ms_total": round(m3_ms, 3),
    "m3_per_decision_us": round(m3_ms / n * 1000, 3),
    "m4_causal_gate_ms_total": round(m4_ms, 3),
    "m4_per_decision_us": round(m4_ms / n * 1000, 3),
    "note": "Measured on local machine (Python reference model, not Wasm). Representative of decision logic cost, not production runtime."
}
import json as _j
_j.dump(result, open(r".\results\overhead_results.json","w"), indent=2)
print(_j.dumps(result, indent=2))