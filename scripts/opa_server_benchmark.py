"""Benchmark OPA in server mode (HTTP) — more representative than CLI.

PURPOSE: Benchmark Open Policy Agent (OPA) in server mode for comparison
INPUTS: None (self-contained, requires OPA binary)
OUTPUTS: results/opa_server_benchmark_results.json
DATA TYPE: REAL (actual OPA HTTP API)
PAPER ALIGNMENT: RQ4, comparison with OPA
"""
import json, time, subprocess, os, numpy as np, urllib.request, sys
ROOT = r"."
OPA = r".\AppData\Local\Temp\opencode\opa.exe"
POLICY = r".\AppData\Local\Temp\opencode\opa_policy.rego"
sys.path.insert(0, ROOT)

rng = np.random.default_rng(42)
N = 500
workload = [{"A": bool(rng.random()>0.2), "P": bool(rng.random()>0.15), "F": bool(rng.random()>0.1),
             "C": bool(rng.random()>0.1), "B": bool(rng.random()>0.2), "I": bool(rng.random()>0.05),
             "D": bool(rng.random()>0.1)} for _ in range(N)]

# Start OPA server
proc = subprocess.Popen([OPA, "run", "--server", "--addr", "localhost:8182", POLICY],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)

# Warm up
for w in workload[:20]:
    data = json.dumps({"input": w}).encode()
    req = urllib.request.Request("http://localhost:8182/v1/data/governance/allow", data=data,
                                headers={"Content-Type": "application/json"})
    try: urllib.request.urlopen(req, timeout=5)
    except: pass

# Benchmark
t0 = time.perf_counter()
success = 0
for w in workload:
    data = json.dumps({"input": w}).encode()
    req = urllib.request.Request("http://localhost:8182/v1/data/governance/allow", data=data,
                                headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=5); success += 1
    except Exception as e:
        pass
opa_ms = (time.perf_counter() - t0) * 1000
proc.terminate(); proc.wait()

# In-process
t0 = time.perf_counter()
for w in workload:
    _ = all(w[k] for k in "APFCBID")
inprocess_ms = (time.perf_counter() - t0) * 1000

result = {
    "n_operations": N,
    "inprocess_per_decision_us": round(inprocess_ms / N * 1000, 3),
    "opa_server_per_decision_us": round(opa_ms / N * 1000, 3),
    "opa_success_count": success,
    "speedup": round(opa_ms / inprocess_ms, 1) if inprocess_ms > 0 else None,
    "note": "OPA measured via HTTP (includes JSON serialization + IPC + network loopback). In-process measured via direct Python evaluation. OPA server mode (long-running process) is more representative than CLI mode but still includes HTTP overhead. Production OPA deployments typically use a sidecar with local socket (lower overhead than HTTP/TCP).",
}
json.dump(result, open(ROOT + r"\results\opa_server_benchmark_results.json", "w"), indent=2)
print(json.dumps(result, indent=2))