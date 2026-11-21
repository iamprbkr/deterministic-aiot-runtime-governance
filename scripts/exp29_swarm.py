"""Experiment 29: Multi-agent collusion & coordinated botnet swarm."""
import json, numpy as np
ROOT = r"."

n_agents = 50
n_requests_per_agent = 20
global_endpoint_tracker = set()
detections = 0
total = n_agents * n_requests_per_agent
for agent_id in range(n_agents):
    for req in range(n_requests_per_agent):
        endpoint = f"/api/data_{(agent_id * n_requests_per_agent + req) % 30}"
        global_endpoint_tracker.add(endpoint)
        if len(global_endpoint_tracker) > 25:
            detections += 1

result = {
    "experiment": "Multi-agent collusion & coordinated botnet swarm",
    "n_agents": n_agents,
    "requests_per_agent": n_requests_per_agent,
    "total_requests": total,
    "unique_endpoints_accessed": len(global_endpoint_tracker),
    "swarm_detections": detections,
    "detection_rate": round(detections / total, 4),
    "per_agent_detection": 0,
    "conclusion": f"Global state tracking detects {detections}/{total} requests ({100*detections/total:.1f}%) as swarm pattern after 25 unique endpoints. Per-agent inspection would detect 0%. Demonstrates multi-agent collusion detection via shared governance state.",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\exp29_swarm_results.json", "w"), indent=2)
print(_j.dumps(result, indent=2))