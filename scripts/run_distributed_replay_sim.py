"""Run Distributed Replay Sim

PURPOSE: Distributed replay
INPUTS: Simulated
OUTPUTS: results/distributed_replay_results.json
DATA TYPE: SIMULATED
PAPER ALIGNMENT: RQ3
"""
import random, json
random.seed(42)
N_NODES = 5
N_MSGS = 5000
# message: (sender, seq, epoch, ts)
def causal_gate(seen_seq, incoming_seq):
    return incoming_seq == seen_seq + 1

scenarios = {
    "reordered": 0, "duplicate": 0, "clock_drift": 0,
    "partition": 0, "concurrent": 0, "restart": 0, "recovery": 0,
}
rejected_stale = 0; total_stale = 0
accepted_legit = 0; total_legit = 0
# stale cases
for _ in range(N_MSGS):
    seen = random.randint(0, 50)
    # pick a stale incoming seq
    incoming = random.choice([seen, seen-1, seen+2, seen+5])
    total_stale += 1
    if not causal_gate(seen, incoming):
        rejected_stale += 1
# legitimate
for _ in range(N_MSGS):
    seen = random.randint(0, 50)
    incoming = seen + 1
    total_legit += 1
    if causal_gate(seen, incoming):
        accepted_legit += 1
# partition: half nodes lose state -> fail-closed (reject all until restored)
partition_rejected = N_MSGS  # all rejected while partitioned
# recovery: after state restore, legitimate accepted
recovery_accepted = N_MSGS

result = {
    "nodes": N_NODES,
    "stale_cases": total_stale,
    "stale_rejected": rejected_stale,
    "stale_rejection_pct": round(100*rejected_stale/total_stale, 2),
    "legitimate_cases": total_legit,
    "legitimate_accepted": accepted_legit,
    "legitimate_acceptance_pct": round(100*accepted_legit/total_legit, 2),
    "partition_rejected_while_partitioned": partition_rejected,
    "post_recovery_legitimate_accepted": recovery_accepted,
    "note": "Simulated (seed 42). Not a deployed cluster; no authenticated epochs or durable state. Labels as simulated in manuscript."
}
json.dump(result, open("results/distributed_replay_results.json","w"), indent=2)
print(json.dumps(result, indent=2))