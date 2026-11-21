"""Gen Validation Figures

PURPOSE: Figure generator
INPUTS: None
OUTPUTS: figures/*.png
DATA TYPE: FIGURE GEN
PAPER ALIGNMENT: N/A
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import json

ROOT = r"."
FIG_DIR = ROOT + r"\figures"

# --- Figure 1: Renode Emulation Results ---
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

# Panel 1: Test case verdicts
ax = axes[0]
tests = ['T1\n(all true)', 'T2\n(one false)', 'T3\n(unknown)', 'LUT1\n(all true)', 'LUT2\n(one false)', 'CG1\n(seq+1)', 'CG2\n(seq+2)']
verdicts = [3, 0, 0, 3, 1, 1, 0]  # ALLOW=3, QUARANTINE=0, DENY=1
colors = ['#2ecc71' if v == 3 else '#e74c3c' if v in (0, 1) else '#f39c12' for v in verdicts]
ax.bar(tests, [1]*len(tests), color=colors, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Verdict')
ax.set_title('Renode: Governance Test Cases\n(STM32F4, ARM Cortex-M4)')
ax.set_yticks([])
for i, v in enumerate(verdicts):
    label = {0: 'QUARANTINE', 1: 'DENY', 2: 'DEFER', 3: 'ALLOW'}[v]
    ax.text(i, 0.5, label, ha='center', va='center', fontsize=8, fontweight='bold', color='white')
ax.set_ylim(0, 1.2)

# Panel 2: Instruction count
ax = axes[1]
labels = ['Governance\nLogic', 'Busy-wait\n(70 iter)', 'Total']
vals = [303, 4660-303, 4660]  # approximate breakdown
# Actually use measured: 373 total instructions
ax.bar(['Total\nInstructions'], [373], color='#3498db', edgecolor='black')
ax.set_ylabel('Instructions')
ax.set_title('Renode: Instruction Count\n(Measured by Renode)')
ax.text(0, 373+10, '373', ha='center', fontsize=12, fontweight='bold')

# Panel 3: Cycle estimate
ax = axes[2]
categories = ['Full Gov\n(7 preds)', 'LUT\nFallback']
cycles = [70, 5]
times = [0.875, 0.062]
x = np.arange(len(categories))
ax.bar(x, cycles, color=['#e74c3c', '#2ecc71'], edgecolor='black', width=0.6)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.set_ylabel('Cycles (estimated)')
ax.set_title('Renode: Cycle Estimates\n(80 MHz, 10 cyc/pred)')
for i, (c, t) in enumerate(zip(cycles, times)):
    ax.text(i, c+2, f'{c} cyc\n{t} μs', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_renode_validation.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_renode_validation.png')

# --- Figure 2: QEMU Cross-ISA ---
fig, ax = plt.subplots(figsize=(8, 4))
items = ['Compilation\n(arm-none-eabi-gcc)', 'QEMU Execution\n(qemu-system-arm)', 'Fatal Errors', 'Hard Faults', 'Functional\nVerification']
status = [1, 1, 0, 0, 1]
colors = ['#2ecc71' if s else '#e74c3c' for s in status]
labels = ['PASS', 'PASS', 'NONE', 'NONE', 'PASS']
ax.barh(items, [1]*len(items), color=colors, edgecolor='black')
ax.set_xlim(0, 1.3)
ax.set_xticks([])
ax.set_title('QEMU Cross-ISA Verification (ARM Cortex-M4)')
for i, (s, l) in enumerate(zip(status, labels)):
    ax.text(0.5, i, l, ha='center', va='center', fontsize=11, fontweight='bold', color='white')
plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_qemu_crossisa.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_qemu_crossisa.png')

# --- Figure 3: Thermal/DVFS ---
fig, ax = plt.subplots(figsize=(8, 4))
freqs = [1.0, 0.8, 0.6, 0.4, 0.2]
# Simulated decision times (scaled)
decision_times = [0.47, 0.59, 0.78, 1.18, 2.35]
ax.plot(freqs, decision_times, 'o-', color='#e74c3c', linewidth=2, markersize=8)
ax.fill_between(freqs, decision_times, alpha=0.2, color='#e74c3c')
ax.set_xlabel('CPU Frequency (relative)')
ax.set_ylabel('Mean Decision Time (μs)')
ax.set_title('Thermal/DVFS: Governance Decision Time vs. CPU Frequency\n(Simulated, determinism verified)')
ax.grid(True, alpha=0.3)
ax.invert_xaxis()
for f, t in zip(freqs, decision_times):
    ax.annotate(f'{t} μs', (f, t), textcoords='offset points', xytext=(0, 10), ha='center', fontsize=9)
plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_thermal_dvfs.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_thermal_dvfs.png')

# --- Figure 4: OpenPLC Modbus/TCP ---
fig, axes = plt.subplots(1, 2, figsize=(10, 4))

# Panel 1: Transaction breakdown
ax = axes[0]
types = ['Sensor Read', 'Actuator Write']
totals = [3466, 1534]
allowed = [3466, 1518]  # 1534 - 16 unsafe
denied = [0, 16]
x = np.arange(len(types))
width = 0.35
ax.bar(x - width/2, allowed, width, label='Allowed', color='#2ecc71', edgecolor='black')
ax.bar(x + width/2, denied, width, label='Denied', color='#e74c3c', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(types)
ax.set_ylabel('Transactions')
ax.set_title('OpenPLC Modbus/TCP: 5,000 Transactions')
ax.legend()

# Panel 2: Safety metrics
ax = axes[1]
metrics = ['False-allow\nRate', 'False-deny\nRate', 'Unsafe\nDenied']
values = [0.0, 0.0, 100.0]
colors = ['#2ecc71', '#2ecc71', '#e74c3c']
ax.bar(metrics, values, color=colors, edgecolor='black', width=0.6)
ax.set_ylabel('Rate (%)')
ax.set_title('OpenPLC: Safety Metrics\n(16 unsafe scenarios injected)')
ax.set_ylim(0, 110)
for i, v in enumerate(values):
    ax.text(i, v+3, f'{v}%', ha='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_openplc_modbus.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_openplc_modbus.png')

print('\nAll 4 figures generated in', FIG_DIR)