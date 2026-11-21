"""Exp7 Scalability

PURPOSE: Scalability
INPUTS: Simulated
OUTPUTS: results/exp7_scalability_results.json
DATA TYPE: SIMULATED
PAPER ALIGNMENT: RQ3
"""
import json, time, numpy as np
ROOT = r"."
rng = np.random.default_rng(42)

client_counts = [10, 50, 100, 500, 1000]
results = {}
for n_clients in client_counts:
    n_ops = n_clients * 10  # 10 ops per client
    # Simulate queue: arrivals = clients, service rate = 100 ops/s
    service_rate = 100.0
    queue = 0; max_queue = 0; wait_times = []; drops = 0
    t0 = time.perf_counter()
    for i in range(n_ops):
        arrival = rng.poisson(lam=n_clients/10.0)
        queue = max(0, queue + arrival - 1)
        if queue > 0:
            wait = queue / service_rate
            wait_times.append(wait)
        if queue > 1000:
            drops += 1
            queue = 1000
        max_queue = max(max_queue, queue)
    elapsed = (time.perf_counter() - t0) * 1000
    throughput = n_ops / (elapsed / 1000) if elapsed > 0 else 0
    results[f"clients_{n_clients}"] = {
        "n_clients": n_clients,
        "n_ops": n_ops,
        "throughput_ops_per_s": round(throughput, 1),
        "mean_queue_wait_ms": round(float(np.mean(wait_times)) * 1000, 3) if wait_times else 0,
        "max_queue_depth": int(max_queue),
        "drops": int(drops),
        "deadline_miss_rate": round(drops / n_ops, 4),
    }
    print(f"clients={n_clients}: throughput={throughput:.0f} ops/s, mean_wait={np.mean(wait_times)*1000:.3f}ms, max_queue={max_queue}, drops={drops}")

import json as _j
_j.dump({"scalability": results, "note": "Simulated queue model. Service rate 100 ops/s. Not measured on real hardware."}, open(ROOT + r"\results\exp7_scalability_results.json", "w"), indent=2)
print("\nSaved to results/exp7_scalability_results.json")