"""Gen Openplc Figure Real

PURPOSE: OpenPLC figure
INPUTS: None
OUTPUTS: figures/fig_openplc_modbus.png
DATA TYPE: FIGURE GEN
PAPER ALIGNMENT: N/A
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import numpy as np

ROOT = r"."
FIG_DIR = ROOT + r"\figures"

data = json.load(open(ROOT + r"\results\exp_openplc_modbus_real.json"))

fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

# Panel 1: Transaction breakdown
ax = axes[0]
types = ['Sensor Read', 'Actuator Write']
totals = [data['per_type']['read']['total'], data['per_type']['write']['total']]
allowed = [data['per_type']['read']['allowed'], data['per_type']['write']['allowed']]
denied = [totals[0]-allowed[0], totals[1]-allowed[1]]
x = np.arange(len(types))
width = 0.35
ax.bar(x - width/2, allowed, width, label='Allowed', color='#27ae60', edgecolor='black')
ax.bar(x + width/2, denied, width, label='Denied (unsafe)', color='#c0392b', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(types)
ax.set_ylabel('Transactions')
ax.set_title('OpenPLC Modbus/TCP: 500 Transactions\n(Real Modbus server/client)')
ax.legend()
for i in range(2):
    ax.text(i, totals[i]+5, f'n={totals[i]}', ha='center', fontsize=9)

# Panel 2: Safety metrics
ax = axes[1]
metrics = ['False-allow\nRate', 'False-deny\nRate', 'Unsafe\nDenied']
values = [data['false_allow_rate']*100, data['false_deny_rate']*100, 100.0]
colors = ['#27ae60', '#27ae60', '#c0392b']
ax.bar(metrics, values, color=colors, edgecolor='black', width=0.6)
ax.set_ylabel('Rate (%)')
ax.set_title('OpenPLC: Safety Metrics\n(20 unsafe scenarios injected)')
ax.set_ylim(0, 110)
for i, v in enumerate(values):
    ax.text(i, v+3, f'{v}%', ha='center', fontsize=11, fontweight='bold')

# Panel 3: Response time distribution
ax = axes[2]
rt_metrics = ['Mean', 'Median', 'Min', 'Max']
rt_values = [data['mean_response_us'], data['median_response_us'], data['min_response_us'], data['max_response_us']]
ax.bar(rt_metrics, rt_values, color=['#2980b9', '#2980b9', '#27ae60', '#c0392b'], edgecolor='black', width=0.6)
ax.set_ylabel('Response Time (μs)')
ax.set_title('OpenPLC: Modbus Response Times\n(Real I/O, pymodbus v3.16.2)')
for i, v in enumerate(rt_values):
    ax.text(i, v+20, f'{v:.0f}', ha='center', fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR + r'\fig_openplc_modbus.png', dpi=300, bbox_inches='tight')
plt.close()
print('Saved fig_openplc_modbus.png')