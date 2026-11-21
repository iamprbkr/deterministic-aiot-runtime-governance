#!/usr/bin/env python3
"""Compatibility entry point for the current synthetic-input harness.

PURPOSE: Thin wrapper for rerun_sil_experiments.py (backward compatibility)
INPUTS: CLI args (passed through to rerun_sil_experiments)
OUTPUTS: Same as rerun_sil_experiments.py
DATA TYPE: SIMULATED (synthetic workloads)
PAPER ALIGNMENT: RQ1-RQ4 (all mechanisms)

The previous version of this file contained metric overrides and legacy
simulation logic. It is intentionally replaced by a thin wrapper so that the
repository has one authoritative experiment implementation.
"""
from rerun_sil_experiments import main

if __name__ == "__main__":
    main()
