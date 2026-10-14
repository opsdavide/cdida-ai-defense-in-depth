# C-DIDA: Cloud Defense-in-Depth for Enterprise AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Architecture: Cloud-Native](https://img.shields.io/badge/Architecture-Cloud--Native-green.svg)](docs/)
[![Security: OWASP LLM04](https://img.shields.io/badge/Security-OWASP%20LLM04-red.svg)](docs/)
[![Docker: Compose v2](https://img.shields.io/badge/Docker-Compose%20v2-2496ED.svg?logo=docker&logoColor=white)](docker-compose.yml)
[![FastAPI: Gateway](https://img.shields.io/badge/FastAPI-Gateway-009688.svg?logo=fastapi&logoColor=white)](gateway/)
[![Redis: Rate Limiting](https://img.shields.io/badge/Redis-Rate%20Limiting-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Nginx: Reverse Proxy](https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639.svg?logo=nginx&logoColor=white)](reverse-proxy/)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)

**C-DIDA** (*Cloud Defense-in-Depth for Enterprise AI*) is a modular, cloud-native security architecture engineered to mitigate **Distributed Denial of Service (DDoS)** and **computational resource exhaustion (Semantic DoS)** attacks targeting Large Language Model (LLM) inference microservices.

---

## Architecture Overview

Enterprise AI inference services exhibit an extreme computational asymmetry: an attacker can trigger seconds of heavy GPU/CPU tensor calculations with a lightweight HTTP request ($<1\,\text{KB}$). C-DIDA neutralizes this vector through three sequential defense layers:

```
[ Client / Internet ]
          |
          v (Port 8080)
+-------------------------------------------------------------+
| LAYER 1: Perimeter Volumetric Filter (Nginx Reverse Proxy)  |
| - IP-based rate limiting (10 r/s, burst=5, nodelay)         |
| - Fast-drop (<2 ms) via HTTP 429 Too Many Requests          |
+-------------------------------------------------------------+
          | (Forward safe requests)
          v (Port 8000)
+-------------------------------------------------------------+
| LAYER 2 & 3: Cloud-Native API Gateway (FastAPI + Redis)      |
| - Layer 2: RBAC JWT Authentication & Redis Sliding Window   |
|   Role quotas: Guest (5 r/m), Employee (60 r/m), Admin (inf)|
| - Layer 3: Payload Inspector IDS Heuristics                 |
|   Length cap (500 chars) & token repetition analysis        |
| - Forensics: Tamper-evident HMAC-SHA256 Signed Audit Log   |
+-------------------------------------------------------------+
          | (Forward validated inference)
          v (Port 5001 - Isolated backend_net)
+-------------------------------------------------------------+
| BACKEND: AI Inference Application Server                    |
| - Protected inference execution                             |
| - Real-time metrics telemetries (/metrics)                  |
+-------------------------------------------------------------+
```

---

## Repository Structure

```text
cdida-ai-defense-in-depth/
├── docker-compose.yml       # Multi-service topology and isolated bridge networks
├── .env.example             # Template for security keys and thresholds
├── reverse-proxy/           # Layer 1: Nginx configuration with memory rate limit zone
├── gateway/                 # Layer 2 & 3: FastAPI Gateway, Redis limiter, Payload IDS
├── ai-server/               # Backend AI service with CPU telemetry
├── load-test/               # Benchmark attack simulation scripts (Scenarios A, B, C, D)
├── examples/minimal/        # Self-contained minimal reproducible verification suite
├── docs/                    # Technical research paper (LaTeX sources, PDF, and figures)
├── LICENSE                  # MIT License (2026, Davide Torelli)
└── README.md
```

---

## Prerequisites & Docker Desktop Setup

Before starting the microservices stack, ensure you have:
- **Docker & Docker Compose v2+** (via Docker Desktop or Docker Engine on Linux).
- **Python 3.11+** (for executing test suites and benchmark scripts).

### Recommended Setup on Windows (WSL 2)
1. **WSL 2 Engine**: In Docker Desktop settings (*Settings > General*), confirm that **Use the WSL 2 based engine** is checked.
2. **Distribution Integration**: Under *Settings > Resources > WSL Integration*, enable integration with your installed Linux distribution (e.g. `Ubuntu`).
3. **Engine Status**: Ensure the Docker Desktop status indicator displays **Engine running** (green icon) before executing commands from terminal (PowerShell, Command Prompt, or WSL).

---

## Quick Start & Service Orchestration

### 1. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

### 2. Start the Microservices Cluster
Launch the stack in detached (background) mode with automatic image build:
```bash
docker compose up -d --build
```
This initializes four isolated microservices across two dedicated bridge networks (`frontend_net` and `backend_net`):
- `reverse-proxy` (Nginx, exposed on port `8080`)
- `gateway` (FastAPI API Gateway, port `8000`)
- `ai-application-server` (Backend inference simulation on isolated port `5001`)
- `redis` (In-memory token bucket & sliding window store)

### 3. Docker Lifecycle & Operations Cheat Sheet

| Operation | Command | Description |
| :--- | :--- | :--- |
| **Build & Launch** | `docker compose up -d --build` | Builds container images and launches services in background |
| **Service Status** | `docker compose ps` | Displays health status and port bindings for all containers |
| **Gateway Logs** | `docker compose logs -f gateway` | Streams live API Gateway logs, rate limit decisions, and HMAC audit trails |
| **Reverse Proxy Logs**| `docker compose logs -f reverse-proxy` | Streams Nginx Layer 1 perimeter blocks (HTTP 429) |
| **AI Server Logs** | `docker compose logs -f ai-application-server` | Monitors simulated inference processing and CPU load |
| **Stop Services** | `docker compose down` | Stops and removes containers while preserving image cache |
| **Deep Reset** | `docker compose down -v` | Stops services and flushes all Redis volumes and persistent cache |

---

## Verification & Benchmarks

### 1. Minimal Verification Suite
Run the lightweight validation script to verify all three defense layers:
```bash
cd examples/minimal
pip install httpx pyjwt
python demo_layers.py
```

### 2. Benchmark Attack Scenarios
To run full benchmark stress tests against the cluster:
```bash
# Scenario A: Baseline attack against unprotected AI backend (Port 5001 direct)
python load-test/attack_simulation.py

# Scenario B: Perimeter protection benchmark (Guest traffic via Nginx, Port 8080)
python load-test/protected_run.py --role guest

# Scenario C: Employee quota evaluation (Bypassing Nginx to isolate Gateway RBAC, Port 8000)
python load-test/protected_run.py --role employee --bypass-nginx

# Scenario D: Admin privileged access evaluation
python load-test/protected_run.py --role admin --bypass-nginx
```

---

## Documentation

Full academic paper and formal security analysis:
- **PDF Report**: [`docs/Cloud-Native_Network_Architecture_for_Defense-in-Depth_of_Enterprise_AI_Services.pdf`](docs/Cloud-Native_Network_Architecture_for_Defense-in-Depth_of_Enterprise_AI_Services.pdf)
- **LaTeX Sources**: [`docs/latex/`](docs/latex/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
