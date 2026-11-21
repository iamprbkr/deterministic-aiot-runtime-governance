# Docker and WSL Status for Experiments

## Current State

### Docker Desktop
- **Installed:** Yes (v29.9.3)
- **Daemon Status:** Not running (service stopped, cannot be started)
- **Images Available:** hello-world, mongo, open5gs, nexus3 (no OpenPLC image)
- **OpenPLC Image Pull:** Failed (pull access denied / timeout)

### WSL
- **Installed:** Yes (WSL2)
- **Status:** Available but not used for experiments
- **Linux Kernel:** Available via WSL2

### Docker Compose (docker-compose.yml)
- **Defined:** 3 services (iot-edge, web-backend, adversary)
- **Status:** NOT executed (Docker daemon not running)
- **Purpose:** Simulate IoT edge (0.25 CPU, 256MB), web backend (1.0 CPU, 1GB), and adversary on a shared network

### Dockerfile
- **Defined:** Python 3.11 slim with numpy/pandas
- **Status:** NOT built (Docker daemon not running)
- **Purpose:** Container for running governance harness

## What Docker/WSL Was Supposed to Do

### 1. OpenPLC Runtime (Critical for IoT validation)
- **What:** Run OpenPLC v3 runtime in a Docker container
- **Why:** OpenPLC is the reference open-source PLC for industrial control
- **What it would enable:** Real Modbus/TCP server with real PLC program execution
- **Current status:** NOT AVAILABLE. Docker daemon won't start. OpenPLC image not pullable.
- **Workaround:** pymodbus simulation (real Modbus communication, but no real PLC)

### 2. Multi-Container Testbed (docker-compose.yml)
- **What:** 3-container setup simulating IoT edge + web backend + adversary
- **Why:** Test governance under realistic network conditions with resource constraints
- **What it would enable:** Real network latency, real resource contention, real adversarial traffic
- **Current status:** NOT EXECUTED. Docker daemon not running.
- **Workaround:** Single-machine simulation (no network, no resource contention)

### 3. Edge Resource Constraints
- **What:** Docker cgroups to limit CPU (0.25 core) and memory (256MB)
- **Why:** Simulate constrained IoT edge devices
- **What it would enable:** Real resource-constrained governance measurement
- **Current status:** NOT TESTED. Simulated via Python (0.48ms mean, 13.08% deadline misses on constrained profile).
- **Workaround:** Python-based resource simulation

### 4. Network Isolation (NET_ADMIN)
- **What:** Docker network namespace with traffic control (tc)
- **Why:** Simulate real network latency, packet loss, jitter
- **What it would enable:** Real network-condition governance testing
- **Current status:** NOT TESTED. No network simulation.
- **Workaround:** None

## What's Missing for Q1-Grade IoT Validation

### Critical Gaps
1. **Real OpenPLC runtime**: Requires Docker (daemon not starting) or native compilation
2. **Real resource constraints**: Docker cgroups or actual edge hardware (Raspberry Pi)
3. **Real network conditions**: Docker network + tc (traffic control) or real network
4. **Real thermal management**: DVFS control requires OS-level frequency scaling (not available on Windows)

### What Would Fix This
1. **Start Docker Desktop**: Service needs to be running (currently stopped)
2. **Pull OpenPLC image**: `docker pull fdamador/openplc` (or build from source)
3. **Run docker-compose**: `docker-compose up` for multi-container testbed
4. **Use WSL2**: Run experiments in WSL2 with Linux tools (tc, cpufreq, etc.)

### WSL2 Opportunities
- **tc (traffic control)**: Simulate network latency/loss for governance testing
- **cpufreq**: Control CPU frequency for real DVFS testing
- **perf**: Profile governance code with hardware counters
- **OpenPLC native**: Compile OpenPLC from source on Linux
- **Docker in WSL2**: Run Docker containers inside WSL2 (more reliable than Docker Desktop)

## Recommendation

For Q1-grade IoT validation, the following must be done on a Linux machine or WSL2:

1. **Install WSL2** (if not already): `wsl --install`
2. **Install Docker in WSL2**: `sudo apt install docker.io`
3. **Build OpenPLC from source**: Follow OpenPLC v3 build instructions
4. **Run OpenPLC runtime**: Start the PLC runtime with a test program
5. **Run Modbus/TCP traffic**: Use pymodbus client to send real requests
6. **Measure governance**: Apply governance to each Modbus transaction
7. **Control DVFS**: Use `cpufreq-set` to change CPU frequency
8. **Measure thermal**: Use `sensors` (lm-sensors) for CPU temperature
9. **Simulate network**: Use `tc` (traffic control) for latency/loss

## Current Workarounds (Honest Status)

| What's Needed | Current Workaround | Limitation |
|---|---|---|
| OpenPLC runtime | pymodbus simulation | No real PLC, no real program execution |
| Resource constraints | Python simulation | No real cgroups, no real contention |
| Network conditions | None | No latency/loss simulation |
| DVFS | Linear model | No real frequency change |
| Thermal | None | No temperature measurement |
| Multi-container | Single machine | No network isolation |

## Conclusion

Docker and WSL are available on this machine but were NOT successfully used for experiments. The Docker daemon is stopped and cannot be started. OpenPLC image pulls fail. The experiments that were supposed to use Docker/WSL (OpenPLC runtime, multi-container testbed, resource constraints, network simulation) were replaced with Python simulations.

For Q1-grade validation, these experiments must be re-run on a Linux machine with working Docker/WSL.