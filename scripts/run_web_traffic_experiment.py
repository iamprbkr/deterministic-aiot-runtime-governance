"""Run Web Traffic Experiment

PURPOSE: Web traffic governance
INPUTS: Synthetic (10k requests)
OUTPUTS: results/web_traffic_results.json — 19.86% FA
DATA TYPE: SIMULATED (synthetic)
PAPER ALIGNMENT: RQ2 web
"""
import json, numpy as np, pandas as pd
ROOT = r"."
rng = np.random.default_rng(42)

# Generate synthetic web traffic
n_benign = 5000; n_malicious = 5000
# Benign: mostly standard, but some overlap (new users, large uploads, high-rate legitimate)
benign = []
for i in range(n_benign):
    # 10% of benign look suspicious (new users, large uploads, high rate)
    suspicious = rng.random() < 0.10
    benign.append({
        "method": rng.choice(["GET","POST","PUT"]),
        "endpoint": rng.choice(["/api/users","/api/orders","/api/products","/health","/api/login","/api/search"]),
        "src_ip": f"10.0.{rng.integers(0,10)}.{rng.integers(1,50)}" if rng.random() > 0.15 else f"192.168.{rng.integers(0,256)}.{rng.integers(1,255)}",
        "payload_len": int(rng.integers(500,5000)) if suspicious else int(rng.integers(0,500)),
        "rate": int(rng.integers(50,500)) if suspicious and rng.random() < 0.5 else int(rng.integers(1,20)),
        "is_malicious": False,
    })
# Malicious: some look benign (stealthy attacks)
malicious = []
for i in range(n_malicious):
    atype = rng.choice(["sqli","xss","bruteforce","path_traversal","stealthy"])
    if atype == "stealthy":
        malicious.append({
            "method": "GET",
            "endpoint": rng.choice(["/api/users","/api/products","/health"]),
            "src_ip": f"10.0.{rng.integers(0,10)}.{rng.integers(1,50)}",
            "payload_len": int(rng.integers(0,200)),
            "rate": int(rng.integers(1,15)),
            "is_malicious": True,
            "attack_type": "stealthy",
        })
    else:
        malicious.append({
            "method": "POST" if atype in ("sqli","xss") else "GET",
            "endpoint": rng.choice(["/api/login","/api/search","/admin","/api/users"]),
            "src_ip": f"192.168.{rng.integers(0,256)}.{rng.integers(1,255)}",
            "payload_len": int(rng.integers(500,5000)) if atype in ("sqli","xss") else int(rng.integers(0,100)),
            "rate": int(rng.integers(50,500)) if atype=="bruteforce" else int(rng.integers(1,20)),
            "is_malicious": True,
            "attack_type": atype,
        })
df = pd.DataFrame(benign + malicious).sample(frac=1, random_state=42).reset_index(drop=True)

KNOWN_IPS = set(f"10.0.{i}.{j}" for i in range(10) for j in range(1,50))
ALLOWED_ENDPOINTS = {"/api/users","/api/orders","/api/products","/health","/api/login","/api/search"}
MAX_PAYLOAD = 1000
MAX_RATE = 30

def evaluate_request(req):
    A = req["src_ip"] in KNOWN_IPS  # authority: known client
    P = req["endpoint"] in ALLOWED_ENDPOINTS  # policy: endpoint allowed
    F = True  # freshness (no temporal data in synthetic)
    C = req["payload_len"] <= MAX_PAYLOAD  # context: payload size valid
    B = req["rate"] <= MAX_RATE  # behavioural: rate limit
    I = True  # artefact integrity (no model)
    D = True  # execution budget
    G = A and P and F and C and B and I and D
    return G, {"A":A,"P":P,"F":F,"C":C,"B":B,"I":I,"D":D}

labels = df["is_malicious"].astype(int).values
gov_allow = np.array([evaluate_request(r)[0] for _, r in df.iterrows()])

def metrics(allow_mask, labels, attack_types=None):
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
# static WAF: block if payload too large or rate too high
waf_allow = np.array([(r["payload_len"]<=MAX_PAYLOAD and r["rate"]<=MAX_RATE) for _, r in df.iterrows()])
waf_m = metrics(waf_allow, labels)

print("Full governance:", gov_m)
print("No governance:", base_m)
print("Static WAF:", waf_m)

# Per-attack-type false-allow
print("\nPer-attack false-allow (full governance):")
for atype in ["sqli","xss","bruteforce","path_traversal"]:
    mask = df["attack_type"].fillna("benign")==atype
    if mask.sum()==0: continue
    fa = (gov_allow[mask]==True).mean()
    print(f"  {atype}: n={mask.sum()}, false-allow={round(float(fa),4)}")

# Per-predicate failure on malicious
mal = df[df["is_malicious"]==True]
pred_fail = {k:0 for k in "APFCBID"}
for _, r in mal.iterrows():
    G, preds = evaluate_request(r)
    for k,v in preds.items():
        if not v: pred_fail[k]+=1
print("Malicious predicate failures:", {k: round(v/len(mal),4) for k,v in pred_fail.items()})

result = {
    "scenario": "HTTP/API traffic governance (5,000 benign, 5,000 malicious)",
    "n_requests": len(df),
    "full_governance": gov_m,
    "no_governance": base_m,
    "static_waf": waf_m,
    "malicious_predicate_failures": {k: round(v/len(mal),4) for k,v in pred_fail.items()},
    "per_attack_false_allow": {atype: round(float((gov_allow[df['attack_type'].fillna('benign')==atype]==True).mean()),4) for atype in ["sqli","xss","bruteforce","path_traversal","stealthy"]},
    "limitations": "Synthetic web traffic; not real HTTP logs. Demonstrates the admission rule on web-specific predicates."
}
import json as _j
_j.dump(result, open(ROOT + r"\results\web_traffic_results.json","w"), indent=2)
print("\nSaved to results/web_traffic_results.json")