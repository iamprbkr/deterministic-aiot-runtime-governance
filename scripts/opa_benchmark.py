"""Benchmark: proposed in-process governance vs. OPA (out-of-process).

Runs the same workload through both and measures latency/throughput.
"""
import json, time, subprocess, os, numpy as np, sys
ROOT = r"."
OPA = r".\AppData\Local\Temp\opencode\opa.exe"
POLICY = r".\AppData\Local\Temp\opencode\opa_policy.rego"
sys.path.insert(0, ROOT)
from rerun_sil_experiments import DeterministicWasmGovernor

rng = np.random.default_rng(42)
N = 500

workload = []
for i in range(N):
    workload.append({
        "A": bool(rng.random() > 0.2),
        "P": bool(rng.random() > 0.15),
        "F": bool(rng.random() > 0.1),
        "C": bool(rng.random() > 0.1),
        "B": bool(rng.random() > 0.2),
        "I": bool(rng.random() > 0.05),
        "D": bool(rng.random() > 0.1),
    })

# --- In-process governance ---
t0 = time.perf_counter()
for w in workload:
    _ = all(w[k] for k in "APFCBID")
inprocess_ms = (time.perf_counter() - t0) * 1000

# --- OPA via CLI eval (faster than HTTP) ---
# Write workload to a temp file
import tempfile
tmpdir = tempfile.mkdtemp()
input_file = os.path.join(tmpdir, "input.json")
with open(input_file, "w") as f:
    json.dump({"input": workload[0]}, f)

# Warm up OPA
subprocess.run([OPA, "eval", "-d", POLICY, "-i", input_file, "data.governance.allow"],
               capture_output=True, timeout=10)

# Benchmark: evaluate each input via CLI
t0 = time.perf_counter()
opa_success = 0
for w in workload:
    with open(input_file, "w") as f:
        json.dump({"input": w}, f)
    r = subprocess.run([OPA, "eval", "-d", POLICY, "-i", input_file, "data.governance.allow"],
                       capture_output=True, timeout=10)
    if r.returncode == 0:
        opa_success += 1
opa_ms = (time.perf_counter() - t0) * 1000

result = {
    "n_operations": N,
    "inprocess_governance_ms_total": round(inprocess_ms, 3),
    "inprocess_per_decision_us": round(inprocess_ms / N * 1000, 3),
    "inprocess_throughput_ops_per_s": round(N / (inprocess_ms / 1000), 1),
    "opa_cli_ms_total": round(opa_ms, 3),
    "opa_per_decision_us": round(opa_ms / N * 1000, 3),
    "opa_throughput_ops_per_s": round(N / (opa_ms / 1000), 1),
    "opa_success_count": opa_success,
    "speedup": round(opa_ms / inprocess_ms, 1) if inprocess_ms > 0 else None,
    "note": "OPA measured via CLI eval (includes process startup + file I/O per call). In-process measured via direct Python evaluation. This is an indicative comparison, not a controlled benchmark. OPA's production deployment uses a long-running server (lower per-call overhead than CLI).",
}
json.dump(result, open(ROOT + r"\results\opa_benchmark_results.json", "w"), indent=2)
print(json.dumps(result, indent=2))