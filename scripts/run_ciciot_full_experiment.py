"""Run Ciciot Full Experiment

PURPOSE: Governance on CIC-IoT2023
INPUTS: CIC-IoT2023 CSV (7k)
OUTPUTS: results/ciciot_full_results.json — 74.13% FA
DATA TYPE: REAL (dataset)
PAPER ALIGNMENT: RQ2
"""
import json, os, numpy as np, pandas as pd, glob, os
ROOT = r"."
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CIC = os.path.join(SCRIPT_DIR, "..", "..", "..", "CIC_IOT_Dataset2023", "CSV")
CIC = os.path.normpath(CIC)

# Load benign + attack samples
benign_files = glob.glob(os.path.join(CIC, "Benign_Final", "*.csv"))
attack_files = [f for f in glob.glob(os.path.join(CIC, "*", "*.csv")) if "Benign" not in f]

print("Benign files:", len(benign_files), "Attack files:", len(attack_files))

# Sample 5000 benign
benign_dfs = []
for f in benign_files:
    try:
        d = pd.read_csv(f)
        benign_dfs.append(d.sample(n=min(500, len(d)), random_state=42))
    except Exception as e:
        pass
benign_df = pd.concat(benign_dfs, ignore_index=True).sample(n=min(5000, len(pd.concat(benign_dfs))), random_state=42)
benign_df['label'] = 0
benign_df['attack_type'] = 'Benign'

# Sample 5000 attack (stratified across types)
attack_dfs = []
for f in attack_files:
    try:
        d = pd.read_csv(f)
        atype = os.path.basename(os.path.dirname(f))
        d['attack_type'] = atype
        d['label'] = 1
        attack_dfs.append(d.sample(n=min(200, len(d)), random_state=42))
    except Exception as e:
        pass
attack_df = pd.concat(attack_dfs, ignore_index=True).sample(n=min(5000, len(pd.concat(attack_dfs))), random_state=42)

df = pd.concat([benign_df, attack_df], ignore_index=True).sample(frac=1, random_state=42).reset_index(drop=True)
print("Total:", len(df), "benign:", (df['label']==0).sum(), "attack:", (df['label']==1).sum())

# Governance predicates on CIC features
# CIC has no IP addresses; use protocol type and traffic features
proto_cols = ['TCP','UDP','HTTP','HTTPS','DNS','Telnet','SMTP','SSH','IRC','ICMP','IGMP','ARP','IPv','LLC','DHCP']
size_col = 'Tot size' if 'Tot size' in df.columns else None
rate_col = 'Rate' if 'Rate' in df.columns else None
iat_col = 'IAT' if 'IAT' in df.columns else None

def govern(row):
    A = True  # no identity data (limitation)
    P = any(row.get(c, 0) == 1 for c in proto_cols) if proto_cols else True
    F = True
    if iat_col and pd.notna(row.get(iat_col)):
        F = float(row[iat_col]) > 0
    C = True
    if size_col and pd.notna(row.get(size_col)):
        C = 0 < float(row[size_col]) < 100000
    B = True
    if rate_col and pd.notna(row.get(rate_col)):
        B = float(row[rate_col]) < 1e6
    I = True
    D = True
    return A and P and F and C and B and I and D

df['G'] = df.apply(govern, axis=1)
labels = df['label'].values
gov_allow = df['G'].values

def metrics(allow_mask, labels):
    tp = int(((allow_mask==False)&(labels==1)).sum())
    fp = int(((allow_mask==False)&(labels==0)).sum())
    tn = int(((allow_mask==True)&(labels==0)).sum())
    fn = int(((allow_mask==True)&(labels==1)).sum())
    return {"n":len(labels),"TP":tp,"FP":fp,"TN":tn,"FN":fn,
            "false_allow_rate": round(fn/(fn+tp),4) if (fn+tp)>0 else 0,
            "false_deny_rate": round(fp/(fp+tn),4) if (fp+tn)>0 else 0,
            "accuracy": round((tp+tn)/len(labels),4)}

gov_m = metrics(gov_allow, labels)
base_allow = np.ones(len(labels), dtype=bool)
base_m = metrics(base_allow, labels)

# Per-attack-type false-allow
per_attack = {}
for atype, grp in df.groupby('attack_type'):
    if atype == 'Benign':
        continue
    per_attack[atype] = round(float((grp['G']==True).mean()), 4)

print("Full governance:", gov_m)
print("No governance:", base_m)
print("Per-attack false-allow (top 5):", dict(list(per_attack.items())[:5]))

result = {
    "dataset": "CIC-IoT2023 (33 attack types + benign)",
    "n_sampled": len(df),
    "n_normal": int((df['label']==0).sum()),
    "n_attack": int((df['label']==1).sum()),
    "n_attack_types": int(df['attack_type'].nunique() - 1),
    "full_governance": gov_m,
    "no_governance": base_m,
    "per_attack_false_allow": per_attack,
    "limitations": "A_k is trivially True (no identity data in CIC-IoT2023). P_k uses protocol type. F_k uses IAT. C_k uses packet size. Predicates are constructs on available features. This is a construct-based evaluation, not a validated deployment mapping.",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\ciciot_full_results.json", "w"), indent=2)
print("\nSaved to results/ciciot_full_results.json")