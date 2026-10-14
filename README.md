# C-DIDA: Cloud Defense-in-Depth for Enterprise AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Architecture: Cloud-Native](https://img.shields.io/badge/Architecture-Cloud--Native-green.svg)](docs/)
[![Security: OWASP LLM04](https://img.shields.io/badge/Security-OWASP%20LLM04-red.svg)](docs/)

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

## Quick Start

### 1. Environment Setup
```bash
cp .env.example .env
docker compose up -d --build
```

### 2. Verify Defense Layers
```bash
cd examples/minimal
pip install httpx pyjwt
python demo_layers.py
```

### 3. Run Benchmark Scenarios
```bash
# Scenario A: Baseline attack against unprotected AI backend
python load-test/attack_simulation.py

# Scenario B: Perimeter protection benchmark (Guest traffic via Nginx)
python load-test/protected_run.py --role guest

# Scenario C: Employee quota evaluation (Bypassing Nginx to isolate Gateway RBAC)
python load-test/protected_run.py --role employee --bypass-nginx
```

---

## Documentation

Full academic paper and formal security analysis:
- **PDF Report**: [`docs/Cloud-Native_Network_Architecture_for_Defense-in-Depth_of_Enterprise_AI_Services.pdf`](docs/Cloud-Native_Network_Architecture_for_Defense-in-Depth_of_Enterprise_AI_Services.pdf)
- **LaTeX Sources**: [`docs/latex/`](docs/latex/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
