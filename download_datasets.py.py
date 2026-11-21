#!/usr/bin/env python3
"""Deprecated compatibility stub.

This filename previously generated synthetic CSV files inside directories
named after public datasets, which could incorrectly imply those records were
real dataset samples. It no longer creates dataset-like files. Obtain datasets
from their official distribution channels, record their versions and hashes,
and implement explicit loaders before describing an experiment as dataset-backed.
"""
if __name__ == "__main__":
    print("This script no longer downloads datasets or fabricates dataset traces.")
    print("The current rerun_sil_experiments.py uses synthetic inputs only.")
    print("See README.md for scope, reproducibility, and dataset-provenance requirements.")
