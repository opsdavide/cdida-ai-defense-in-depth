# C-DIDA Minimal Reproducible Example

This folder contains a minimal verification test demonstrating how each of the three protective layers intercepts malicious or non-compliant traffic:

1. **Layer 1 (Perimeter Volumetric Filter)**: Nginx drops high-frequency request bursts with `HTTP 429 Too Many Requests` in `<2ms`.
2. **Layer 2 (API Gateway RBAC & Sliding Window)**: Validates JWT signature and role quotas (`guest`, `employee`, `admin`) backed by Redis.
3. **Layer 3 (Payload Inspector IDS)**: Heuristically rejects oversized prompts (>500 chars) and repetitive token floods with `HTTP 400 Bad Request`.

## Prerequisites

1. Ensure the Docker Compose stack is running:
   ```bash
   docker compose up -d
   ```
2. Install client dependencies:
   ```bash
   pip install httpx pyjwt
   ```

## Running the Verification

Execute the test script:
```bash
python demo_layers.py
```

### Expected Output
- **Layer 1**: 15 rapid requests dispatched $\to$ 5 accepted in burst, subsequent requests dropped with HTTP 429.
- **Layer 2**: Unauthenticated requests rejected with HTTP 401; exceeding the 5 req/min guest quota returns HTTP 429.
- **Layer 3**: Prompts with $>500$ characters or high lexical repetition rejected with HTTP 400 Bad Request.
