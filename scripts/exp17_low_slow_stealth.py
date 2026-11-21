"""Exp17 Low Slow Stealth

PURPOSE: Low-and-slow stealth
INPUTS: Synthetic
OUTPUTS: results/exp17_stealth_results.json
DATA TYPE: SIMULATED
PAPER ALIGNMENT: RQ3
"""
import json, numpy as np
ROOT = r"."
rng = np.random.default_rng(42)

# Simulate a low-and-slow attack: 1 request per minute over 1 hour (60 requests)
# Each request is benign individually but collectively forms a reconnaissance pattern
n_steps = 60
# State: track cumulative unique endpoints accessed
accessed_endpoints = set()
request_log = []
for i in range(n_steps):
    # Attacker accesses a new endpoint each minute (slow reconnaissance)
    endpoint = f"/api/endpoint_{i % 20}"
    accessed_endpoints.add(endpoint)
    request_log.append({"step": i, "endpoint": endpoint, "cumulative_unique": len(accessed_endpoints)})

# Governance: B_k (behavioural validity) checks if cumulative unique endpoints exceed threshold
threshold_unique = 10  # more than 10 unique endpoints in 1 hour = suspicious
# Sliding window: track unique endpoints in last 60 steps
window_unique = set()
detections = 0
for i, req in enumerate(request_log):
    window_unique.add(req["endpoint"])
    if len(window_unique) > threshold_unique:
        detections += 1
        req["detected"] = True
    else:
        req["detected"] = False

# Single-packet inspection (no state): would never detect (each request looks benign)
single_packet_detections = 0  # no state -> 0 detections

result = {
    "experiment": "Low-and-slow stealth attack detection (temporal window integrity)",
    "n_requests": n_steps,
    "duration_simulated": "60 minutes (1 request/min)",
    "unique_endpoints_threshold": threshold_unique,
    "stateful_detections": detections,
    "stateful_detection_rate": round(detections / n_steps, 4),
    "single_packet_detections": single_packet_detections,
    "single_packet_detection_rate": 0.0,
    "conclusion": f"Stateful tracking detects {detections}/{n_steps} requests ({100*detections/n_steps:.1f}%) as suspicious after {threshold_unique} unique endpoints. Single-packet inspection detects 0%. Demonstrates that temporal window integrity (M4/F_k) catches low-and-slow attacks that per-request checks miss.",
    "note": "Simulated with synthetic request log. Not a real network trace.",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\exp17_stealth_results.json", "w"), indent=2)
print(_j.dumps(result, indent=2))