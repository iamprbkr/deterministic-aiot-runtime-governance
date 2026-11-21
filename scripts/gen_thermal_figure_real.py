"""Gen Thermal Figure Real

PURPOSE: Thermal figure
INPUTS: None
OUTPUTS: figures/fig_thermal_dvfs.png
DATA TYPE: FIGURE GEN
PAPER ALIGNMENT: N/A
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json

ROOT = r"."
FIG_DIR = ROOT + r"\figures"

data = json.load(open(ROOT + r"\results\exp_thermal_dvfs_real.json"))

freqs = [1.0, 0.8, 0.6, 0.4, 0.2]
times = [data[str(f)]['time_us'] for f in freqs]
freq_mhz = [data[str(f)]['freq_mhz'] for f in freqs]

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(freqs, times, 'o-', color='#c0392b', linewidth=2.5, markersize=10)
ax.fill_between(freqs, times, alpha=0.15, color='#c0392b')

ax.set_xlabel('CPU Frequency (relative to max)', fontsize=12)
ax.set_ylabel('Governance Decision Time (μs)', fontsize=12)
ax.set_title('Thermal/DVFS: Governance Decision Time vs. CPU Frequency\n(Base: Renode measured 373 instructions, CPI=1, CPU: Intel Celeron N4500 @ 1114 MHz)', fontsize=11)
ax.grid(True, alpha=0.3)
ax.invert_xaxis()

for f, t, fm in zip(freqs, times, freq_mhz):
    ax.annotate(f'{t:.3f} μs\n({fm:.0f} MHz)', (f, t), textcoords='offset points', xytext=(0, 12), ha='center', fontsize=9)

# Add deadline line
ax.axhline(y=100, color='red', linestyle='--', linewidth=1.5, label='ISR Deadline (100 μs)')
ax.legend(loc='upper left')

# Add annotation
ax.text(0.5, 0.02, 'Base: Renode measured 373 instructions (ExecutedInstructions counter). Frequency scaling: linear (standard DVFS model). No deadline misses at any frequency.',
        transform=ax.transAxes, fontsize=8, style='italic', ha='center', color='gray')

plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_thermal_dvfs.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_thermal_dvfs.png')