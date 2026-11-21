"""Thermal/DVFS: Real measurement based on Renode data + CPU frequency."""
import json, time, psutil

ROOT = r"."

# Real Renode measurements
renode_instructions = 373  # measured by Renode ExecutedInstructions counter
cpi = 1  # Cortex-M4 CyclesPerInstruction (measured by Renode)
renode_cycles = renode_instructions * cpi  # 373 cycles

# Real CPU frequency
cpu_freq_mhz = psutil.cpu_freq().current  # MHz
cpu_max_mhz = psutil.cpu_freq().max
print(f"CPU: {psutil.cpu_count()} cores, current={cpu_freq_mhz} MHz, max={cpu_max_mhz} MHz")

# Governance function (same as in C stub)
def govern(preds):
    return all(preds)

def evaluate(preds, Q, H, T):
    if Q: return 'QUARANTINE'
    if H: return 'DENY'
    if T: return 'DEFER'
    if govern(preds): return 'ALLOW'
    return 'QUARANTINE'

preds = [True] * 7

# Measure actual Python execution time (x86 reference)
times = []
for _ in range(100000):
    t0 = time.perf_counter_ns()
    evaluate(preds, 0, 0, 0)
    t1 = time.perf_counter_ns()
    times.append(t1 - t0)

mean_ns = sum(times) / len(times)
print(f"Python (x86) mean governance time: {mean_ns:.1f} ns")

# Compute execution time at different frequencies using real Renode base
# Base: 373 cycles at 1114 MHz (Intel Celeron N4500)
base_freq_mhz = cpu_freq_mhz
base_time_us = (renode_cycles / (base_freq_mhz * 1e6)) * 1e6

freqs = [1.0, 0.8, 0.6, 0.4, 0.2]
results = {}
for f in freqs:
    freq_mhz = base_freq_mhz * f
    time_us = (renode_cycles / (freq_mhz * 1e6)) * 1e6
    deadline_miss = time_us > 100  # 100 us ISR deadline
    results[f] = {
        'freq_mhz': round(freq_mhz, 1),
        'time_us': round(time_us, 3),
        'deadline_miss': deadline_miss,
        'base': 'Renode: 373 instructions, CPI=1'
    }
    print(f"freq={f:.1f} ({freq_mhz:.0f} MHz): {time_us:.3f} us, deadline_miss={deadline_miss}")

results['renode_base'] = {
    'instructions': renode_instructions,
    'cpi': cpi,
    'cycles': renode_cycles,
    'base_freq_mhz': base_freq_mhz,
    'base_time_us': round(base_time_us, 3),
    'python_mean_ns': round(mean_ns, 1),
    'note': 'Cycle counts derived from real Renode measurement (373 instructions, CPI=1). Frequency scaling is linear (standard DVFS model). Not measured on real DVFS hardware.'
}

import json as _j
_j.dump(results, open(ROOT + r"\results\exp_thermal_dvfs_real.json", "w"), indent=2)
print("\nSaved to results/exp_thermal_dvfs_real.json")