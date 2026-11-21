"""Run Ciciot Official Experiment

PURPOSE: Official CIC-IoT2023 eval
INPUTS: CIC-IoT2023 official
OUTPUTS: results/ciciot_official_results.json
DATA TYPE: REAL (dataset)
PAPER ALIGNMENT: RQ2
"""
import json, os, numpy as np, pandas as pd, glob, os
ROOT = r"."
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CIC_DIR = os.path.join(SCRIPT_DIR, "..", "..", "..", "CIC-IoT2023 Official IoT Flow Feature Dataset")
CIC_DIR = os.path.normpath(CIC_DIR)

files = sorted(glob.glob(os.path.join(CIC_DIR, "Merged*.csv")))
print("Files found:", len(files))

# Load and sample 50k stratified
dfs = []
for f in files[:5]:
    try:
        d = pd.read_csv(f)
        dfs.append(d)
    except Exception as e:
        print("skip", f, str(e)[:40])
df = pd.concat(dfs, ignore_index=True)
print("Total loaded:", len(df))

# Stratified sample
normal = df[df['Label']=='BENIGN']
attack = df[df['Label']!='BENIGN']
n_normal = min(7500, len(normal))
n_attack = min(42500, len(attack))
ns = normal.sample(n=n_normal, random_state=42)
ats = attack.sample(n=n_attack, random_state=42)
df = pd.concat([ns, ats]).sample(frac=1, random_state=42).reset_index(drop=True)
print("Sampled:", len(df), "normal:", (df['Label']=='BENIGN').sum(), "attack:", (df['Label']!='BENIGN').sum())

# Governance predicates on CIC flow features
# A_k: no identity data -> True (limitation)
# P_k: protocol type in allowed set (TCP/UDP/HTTP/HTTPS/DNS/SSH/ICMP/ARP)
# F_k: IAT > 0 (not a replay)
# C_k: packet size in valid range
# B_k: rate not extreme
# I_k: True (no model artefact)
# D_k: True (no budget constraint)

def govern(row):
    A = True
    proto = row.get('Protocol Type', 0)
    P = proto in [0, 1, 2, 3, 4, 5, 6]  # TCP, UDP, HTTP, HTTPS, DNS, SSH, ICMP
    F = True
    iat = row.get('IAT', 0)
    if pd.notna(iat) and iat is not None:
        try:
            F = float(iat) > 0
        except Exception:
            F = True
    C = True
    ts = row.get('Tot size', 0)
    if pd.notna(ts):
        try:
            C = 0 < float(ts) < 100000
        except Exception:
            C = True
    B = True
    rate = row.get('Rate', 0)
    if pd.notna(rate):
        try:
            B = float(rate) < 1e6
        except Exception:
            B = True
    I = True
    D = True
    return A and P and F and C and B and I and D

df['G'] = df.apply(govern, axis=1)
labels = (df['Label'] != 'BENIGN').astype(int).values
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

# Per-predicate failure rates
pred_fail = {}
for col in ['A','P','F','C','B','I','D']:
    # Compute per-predicate by re-deriving
    pass
# Compute per-predicate failure rates manually
A_fail = 0; P_fail = 0; F_fail = 0; C_fail = 0; B_fail = 0
for _, row in df.iterrows():
    proto = row.get('Protocol Type', 0)
    P = proto in [0,1,2,3,4,5,6]
    if not P: P_fail += 1
    iat = row.get('IAT', 0)
    F = True
    if pd.notna(iat):
        try: F = float(iat) > 0
        except: F = True
    if not F: F_fail += 1
    ts = row.get('Tot size', 0)
    C = True
    if pd.notna(ts):
        try: C = 0 < float(ts) < 100000
        except: C = True
    if not C: C_fail += 1
    rate = row.get('Rate', 0)
    B = True
    if pd.notna(rate):
        try: B = float(rate) < 1e6
        except: B = True
    if not B: B_fail += 1

pred_fail = {"A": 0.0, "P": round(P_fail/len(df),4), "F": round(F_fail/len(df),4),
             "C": round(C_fail/len(df),4), "B": round(B_fail/len(df),4), "I": 0.0, "D": 0.0}

# Per-attack-type false-allow (top 10)
per_attack = {}
for atype, grp in df.groupby('Label'):
    if atype == 'BENIGN':
        continue
    per_attack[atype] = round(float((grp['G']==True).mean()), 4)

print("Full governance:", gov_m)
print("No governance:", base_m)
print("Per-predicate failures:", pred_fail)
print("Per-attack (top 5):", dict(list(per_attack.items())[:5]))

result = {
    "dataset": "CIC-IoT2023 Official Flow Feature Dataset",
    "n_sampled": len(df),
    "n_normal": int((df['Label']=='BENIGN').sum()),
    "n_attack": int((df['Label']!='BENIGN').sum()),
    "n_attack_types": int(df['Label'].nunique() - 1),
    "full_governance": gov_m,
    "no_governance": base_m,
    "per_predicate_failure_rate": pred_fail,
    "per_attack_false_allow": per_attack,
    "limitations": "A_k is trivially True (no identity data in CIC-IoT2023). P_k uses protocol type flags. F_k uses IAT. C_k uses packet size. B_k uses rate. Predicates are constructs on available features.",
}
import json as _j
_j.dump(result, open(ROOT + r"\results\ciciot_official_results.json", "w"), indent=2)
print("\nSaved to results/ciciot_official_results.json")