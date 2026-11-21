"""Exp20 Cross Dataset

PURPOSE: Cross-dataset generalization
INPUTS: Edge-IIoTset + CIC-IoT2023
OUTPUTS: results/exp20_crossdataset_results.json
DATA TYPE: REAL (datasets)
PAPER ALIGNMENT: RQ2
"""
import json, numpy as np, pandas as pd
ROOT = r"."

# Load Edge-IIoTset (training distribution)
edge_path = r".\Edge-IIoTset\Edge-IIoTset dataset\Selected dataset for ML and DL\ML-EdgeIIoT-dataset.csv"
edge = pd.read_csv(edge_path, usecols=['ip.src_host','tcp.dstport','tcp.len','Attack_label'], nrows=20000)
print("Edge-IIoTset loaded:", len(edge))

# Load CIC-IoT2023 (test distribution — different dataset)
cic_path = r".\CIC_IOT_Dataset2023"
import glob, os
cic_files = glob.glob(os.path.join(cic_path, "**", "*.csv"), recursive=True)
print("CIC files found:", len(cic_files))
# Try to load first CSV
# Load CIC-IoT2023: combine benign + one attack type
cic_files = glob.glob(os.path.join(cic_path, "CSV", "*", "*.csv"), recursive=True)
benign_files = [f for f in cic_files if 'Benign' in f]
attack_files = [f for f in cic_files if 'Benign' not in f]
print("Benign files:", len(benign_files), "Attack files:", len(attack_files))

# Sample 5000 benign + 5000 attack
rng_cic = np.random.default_rng(99)
benign_dfs = []
for f in benign_files[:3]:
    try:
        d = pd.read_csv(f)
        benign_dfs.append(d.sample(n=min(2000, len(d)), random_state=42))
    except Exception as e:
        print("skip benign", f, str(e)[:40])
benign_df = pd.concat(benign_dfs, ignore_index=True).sample(n=5000, random_state=42) if benign_dfs else pd.DataFrame()

attack_dfs = []
for f in attack_files[:2]:
    try:
        d = pd.read_csv(f)
        attack_dfs.append(d.sample(n=min(2500, len(d)), random_state=42))
    except Exception as e:
        print("skip attack", f, str(e)[:40])
attack_df = pd.concat(attack_dfs, ignore_index=True).sample(n=5000, random_state=42) if attack_dfs else pd.DataFrame()

benign_df['Attack_label'] = 0
attack_df['Attack_label'] = 1
cic = pd.concat([benign_df, attack_df], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
print("CIC combined shape:", cic.shape)

# Normalize CIC columns to match Edge format
# Find label column
label_col = None
for c in cic.columns:
    if 'label' in c.lower() or 'attack' in c.lower():
        label_col = c; break
if label_col is None:
    label_col = cic.columns[-1]
print("Label column:", label_col)

# Map CIC to governance predicates (same mapping as Edge)
KNOWN_IPS = set(edge[edge['Attack_label']==0]['ip.src_host'].value_counts().head(100).index)
STANDARD_PORTS = {80, 443, 1883, 502, 53, 22, 21, 25, 110, 143, 3306, 5432}

def govern(src_ip, port, tcp_len):
    A = src_ip in KNOWN_IPS
    P = port in STANDARD_PORTS
    F = True
    C = 0 < tcp_len < 1500
    B = tcp_len < 1400
    I = True
    D = True
    return A and P and F and C and B and I and D

# Edge-IIoTset evaluation (in-distribution)
edge_sample = edge.sample(n=10000, random_state=42)
edge_allow = np.array([govern(r['ip.src_host'], r['tcp.dstport'] if pd.notna(r['tcp.dstport']) else 0,
                             r['tcp.len'] if pd.notna(r['tcp.len']) else 0) for _, r in edge_sample.iterrows()])
edge_labels = edge_sample['Attack_label'].values
edge_fa = ((edge_allow==True)&(edge_labels==1)).mean()
edge_fd = ((edge_allow==False)&(edge_labels==0)).mean()
edge_acc = ((edge_allow==False)&(edge_labels==1)).sum() + ((edge_allow==True)&(edge_labels==0)).sum()
edge_acc /= len(edge_labels)

# CIC evaluation (out-of-distribution)
cic_sample = cic.sample(n=min(10000, len(cic)), random_state=42)
# Map CIC columns (no IP/port; use protocol type and traffic features)
proto_cols = [c for c in cic.columns if c in ['TCP','UDP','HTTP','HTTPS','DNS','Telnet','SMTP','SSH','IRC','ICMP','IGMP','ARP','IPv','LLC','DHCP']]
size_col = 'Tot size' if 'Tot size' in cic.columns else None
rate_col = 'Rate' if 'Rate' in cic.columns else None
iat_col = 'IAT' if 'IAT' in cic.columns else None

def govern_cic(row):
    # A_k: no identity data -> assume valid (limitation)
    A = True
    # P_k: protocol is a known/allowed protocol
    P = any(row.get(c, 0) == 1 for c in proto_cols) if proto_cols else True
    # F_k: inter-arrival time not extreme (not a replay)
    F = True
    if iat_col and pd.notna(row.get(iat_col)):
        F = float(row[iat_col]) > 0
    # C_k: packet size in valid range
    C = True
    if size_col and pd.notna(row.get(size_col)):
        C = 0 < float(row[size_col]) < 100000
    # B_k: rate not extreme
    B = True
    if rate_col and pd.notna(row.get(rate_col)):
        B = float(row[rate_col]) < 1e6
    I = True
    D = True
    return A and P and F and C and B and I and D

cic_allow = np.array([govern_cic(r) for _, r in cic_sample.iterrows()])
cic_allow = np.array(cic_allow)
cic_labels = cic_sample[label_col].values
# Normalize labels to 0/1 (CIC might use different encoding)
if cic_labels.dtype == object:
    cic_labels = (cic_labels != 'Benign').astype(int) if 'Benign' in str(cic_labels[0]) else cic_labels.astype(int)
else:
    cic_labels = (cic_labels > 0).astype(int)
cic_fa = ((cic_allow==True)&(cic_labels==1)).mean()
cic_fd = ((cic_allow==False)&(cic_labels==0)).mean()
cic_acc = (((cic_allow==False)&(cic_labels==1)).sum() + ((cic_allow==True)&(cic_labels==0)).sum()) / len(cic_labels)

result = {
    "experiment": "Cross-dataset zero-day generalization",
    "train_dataset": "Edge-IIoTset (20,000 flows)",
    "test_dataset": "CIC-IoT2023" if cic_files else "Synthetic CIC-like",
    "edge_iiot": {
        "n": len(edge_sample),
        "false_allow_rate": round(float(edge_fa), 4),
        "false_deny_rate": round(float(edge_fd), 4),
        "accuracy": round(float(edge_acc), 4),
    },
    "cic_iot": {
        "n": len(cic_sample),
        "false_allow_rate": round(float(cic_fa), 4),
        "false_deny_rate": round(float(cic_fd), 4),
        "accuracy": round(float(cic_acc), 4),
    },
    "interpretation": "Governance predicates trained on Edge-IIoTset (known IPs, standard ports) are applied to CIC-IoT2023 (different IP ranges, different attack types). False-allow rate on unseen data measures generalization. If predicates are too specific to Edge-IIoTset (e.g., known IP list), false-allow will be high on CIC. This demonstrates the need for deployment-specific calibration.",
    "limitations": "Predicate mapping is a construct. CIC column names may differ from Edge-IIoTset. Label encoding may need normalization. This is a preliminary cross-dataset test, not a validated generalization study.",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\exp20_crossdataset_results.json", "w"), indent=2)
print(_j.dumps(result, indent=2))