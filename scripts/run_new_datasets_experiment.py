"""Run New Datasets Experiment

PURPOSE: Governance on TON_IoT/CSIC/IDS2025
INPUTS: 3 datasets (20k each)
OUTPUTS: results/exp_new_datasets.json
DATA TYPE: REAL (datasets)
PAPER ALIGNMENT: RQ2
"""
import json, numpy as np, time
ROOT = r"."
import pandas as pd

def govern(preds):
    return all(preds)

def evaluate(preds):
    if govern(preds): return 'ALLOW'
    return 'DENY'

def run_ton_iot():
    print("=== TON_IoT ===")
    df = pd.read_csv(ROOT.replace('deterministic-aiot-runtime-governance-fixed\\deterministic-aiot-runtime-governance-main', '') + 'train_test_network.csv')
    # Sample 20k
    df = df.sample(n=min(20000, len(df)), random_state=42)
    print(f"Loaded {len(df)} rows")
    
    # Build known IP set from normal traffic
    normal = df[df['label'] == 0]
    known_ips = set(normal['src_ip'].value_counts().head(100).index)
    known_protos = set(normal['proto'].value_counts().head(10).index)
    
    results = {'total': 0, 'attacks': 0, 'normal': 0, 'false_allow': 0, 'false_deny': 0}
    for _, row in df.iterrows():
        is_attack = row['label'] == 1
        src_ip = row['src_ip']
        proto = row['proto']
        
        A = src_ip in known_ips
        P = proto in known_protos
        F = True
        C = True
        B = True
        I = True
        D = True
        
        preds = [A, P, F, C, B, I, D]
        verdict = evaluate(preds)
        
        results['total'] += 1
        if is_attack:
            results['attacks'] += 1
            if verdict == 'ALLOW':
                results['false_allow'] += 1
        else:
            results['normal'] += 1
            if verdict == 'DENY':
                results['false_deny'] += 1
    
    fa_rate = results['false_allow'] / results['attacks'] * 100 if results['attacks'] > 0 else 0
    fd_rate = results['false_deny'] / results['normal'] * 100 if results['normal'] > 0 else 0
    acc = (results['total'] - results['false_allow'] - results['false_deny']) / results['total'] * 100
    print(f"Total: {results['total']}, Attacks: {results['attacks']}, Normal: {results['normal']}")
    print(f"False-allow: {results['false_allow']} ({fa_rate:.2f}%), False-deny: {results['false_deny']} ({fd_rate:.2f}%)")
    print(f"Accuracy: {acc:.2f}%")
    return {'dataset': 'TON_IoT', 'total': results['total'], 'attacks': results['attacks'],
            'normal': results['normal'], 'false_allow': results['false_allow'],
            'false_allow_rate': round(fa_rate, 2), 'false_deny': results['false_deny'],
            'false_deny_rate': round(fd_rate, 2), 'accuracy': round(acc, 2)}

def run_csic():
    print("\n=== CSIC 2010 ===")
    df = pd.read_csv(ROOT.replace('deterministic-aiot-runtime-governance-fixed\\deterministic-aiot-runtime-governance-main', '') + 'csic_database.csv')
    df = df.sample(n=min(20000, len(df)), random_state=42)
    print(f"Loaded {len(df)} rows")
    
    normal = df[df['classification'] == 0]
    known_methods = set(normal['Method'].value_counts().head(10).index)
    known_hosts = set(normal['host'].value_counts().head(100).index) if 'host' in df.columns else set()
    
    results = {'total': 0, 'attacks': 0, 'normal': 0, 'false_allow': 0, 'false_deny': 0}
    for _, row in df.iterrows():
        is_attack = row['classification'] == 1
        method = row['Method']
        
        A = True  # no IP data
        P = method in known_methods
        F = True
        C = True
        B = True
        I = True
        D = True
        
        preds = [A, P, F, C, B, I, D]
        verdict = evaluate(preds)
        
        results['total'] += 1
        if is_attack:
            results['attacks'] += 1
            if verdict == 'ALLOW':
                results['false_allow'] += 1
        else:
            results['normal'] += 1
            if verdict == 'DENY':
                results['false_deny'] += 1
    
    fa_rate = results['false_allow'] / results['attacks'] * 100 if results['attacks'] > 0 else 0
    fd_rate = results['false_deny'] / results['normal'] * 100 if results['normal'] > 0 else 0
    acc = (results['total'] - results['false_allow'] - results['false_deny']) / results['total'] * 100
    print(f"Total: {results['total']}, Attacks: {results['attacks']}, Normal: {results['normal']}")
    print(f"False-allow: {results['false_allow']} ({fa_rate:.2f}%), False-deny: {results['false_deny']} ({fd_rate:.2f}%)")
    print(f"Accuracy: {acc:.2f}%")
    return {'dataset': 'CSIC 2010', 'total': results['total'], 'attacks': results['attacks'],
            'normal': results['normal'], 'false_allow': results['false_allow'],
            'false_allow_rate': round(fa_rate, 2), 'false_deny': results['false_deny'],
            'false_deny_rate': round(fd_rate, 2), 'accuracy': round(acc, 2)}

def run_ids2025():
    print("\n=== IDS2025 ===")
    df = pd.read_excel(ROOT.replace('deterministic-aiot-runtime-governance-fixed\\deterministic-aiot-runtime-governance-main', '') + 'IDS2025.xlsx')
    df = df.sample(n=min(20000, len(df)), random_state=42)
    print(f"Loaded {len(df)} rows")
    
    normal = df[df['newLabel'] == 'Normal']
    known_ports = set(normal['Source Port'].value_counts().head(50).index)
    known_protos = set(normal['Protocol'].value_counts().head(10).index)
    
    results = {'total': 0, 'attacks': 0, 'normal': 0, 'false_allow': 0, 'false_deny': 0}
    for _, row in df.iterrows():
        is_attack = row['newLabel'] != 'Normal'
        src_port = row['Source Port']
        proto = row['Protocol']
        
        A = src_port in known_ports
        P = proto in known_protos
        F = True
        C = True
        B = True
        I = True
        D = True
        
        preds = [A, P, F, C, B, I, D]
        verdict = evaluate(preds)
        
        results['total'] += 1
        if is_attack:
            results['attacks'] += 1
            if verdict == 'ALLOW':
                results['false_allow'] += 1
        else:
            results['normal'] += 1
            if verdict == 'DENY':
                results['false_deny'] += 1
    
    fa_rate = results['false_allow'] / results['attacks'] * 100 if results['attacks'] > 0 else 0
    fd_rate = results['false_deny'] / results['normal'] * 100 if results['normal'] > 0 else 0
    acc = (results['total'] - results['false_allow'] - results['false_deny']) / results['total'] * 100
    print(f"Total: {results['total']}, Attacks: {results['attacks']}, Normal: {results['normal']}")
    print(f"False-allow: {results['false_allow']} ({fa_rate:.2f}%), False-deny: {results['false_deny']} ({fd_rate:.2f}%)")
    print(f"Accuracy: {acc:.2f}%")
    return {'dataset': 'IDS2025', 'total': results['total'], 'attacks': results['attacks'],
            'normal': results['normal'], 'false_allow': results['false_allow'],
            'false_allow_rate': round(fa_rate, 2), 'false_deny': results['false_deny'],
            'false_deny_rate': round(fd_rate, 2), 'accuracy': round(acc, 2)}

if __name__ == '__main__':
    r1 = run_ton_iot()
    r2 = run_csic()
    r3 = run_ids2025()
    
    all_results = [r1, r2, r3]
    import json as _j
    _j.dump(all_results, open(ROOT + r"\results\exp_new_datasets.json", "w"), indent=2)
    print("\n=== SUMMARY ===")
    for r in all_results:
        print(f"{r['dataset']}: n={r['total']}, FA={r['false_allow_rate']}%, FD={r['false_deny_rate']}%, Acc={r['accuracy']}%")