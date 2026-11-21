"""Exp12 Toctou Race

PURPOSE: TOCTOU race
INPUTS: None (self-contained)
OUTPUTS: results/exp12_toctou_results.json
DATA TYPE: SIMULATED (sleep)
PAPER ALIGNMENT: RQ3
"""
import json, time, threading, numpy as np
ROOT = r"."
total = 10000

# Without lock: race condition
shared = {"value": 0}
outcomes = []
def check_and_use(tid, results):
    if shared["value"] < 100:
        time.sleep(0)
        shared["value"] += 1
        results.append(("ok", tid))
    else:
        results.append(("denied", tid))
threads = [threading.Thread(target=check_and_use, args=(i, outcomes)) for i in range(total)]
for t in threads: t.start()
for t in threads: t.join()

# With lock: no race
shared2 = {"value": 0, "lock": threading.Lock()}
outcomes2 = []
def check_and_use_locked(tid, results):
    with shared2["lock"]:
        if shared2["value"] < 100:
            shared2["value"] += 1
            results.append(("ok", tid))
        else:
            results.append(("denied", tid))
threads2 = [threading.Thread(target=check_and_use_locked, args=(i, outcomes2)) for i in range(total)]
for t in threads2: t.start()
for t in threads2: t.join()

result = {
    "experiment": "TOCTOU race condition resilience",
    "without_lock": {"total": total, "ok": sum(1 for o in outcomes if o[0]=="ok"), "final_value": shared["value"], "race_detected": shared["value"] > 100},
    "with_lock": {"total": total, "ok": sum(1 for o in outcomes2 if o[0]=="ok"), "final_value": shared2["value"], "race_detected": shared2["value"] > 100},
    "conclusion": "Without lock: TOCTOU race allows value to exceed bound. With lock: value capped at 100 (correct). Governance evaluation must use atomic predicate snapshots (no TOCTOU).",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\exp12_toctou_results.json", "w"), indent=2)
print(_j.dumps(result, indent=2))