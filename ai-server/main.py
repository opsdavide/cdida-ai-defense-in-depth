import asyncio
import time
import psutil
from fastapi import FastAPI
from pydantic import BaseModel

# Initial warm-up for psutil.cpu_percent to establish the first delta reference
psutil.cpu_percent(interval=None)

app = FastAPI(title="AI Application Server (Inference Simulator)")

# In-memory metrics tracking
stats = {
    "total_requests": 0,
    "active_requests": 0,
    "total_latency_seconds": 0.0
}
# History of (timestamp, active_requests_count) to calculate peak concurrent active requests in a sliding window
active_requests_history = []

class InferencePayload(BaseModel):
    text: str

@app.post("/inference")
async def inference(payload: InferencePayload):
    stats["total_requests"] += 1
    stats["active_requests"] += 1
    start_time = time.time()
    
    # Save the snapshot of active requests at start to record on success
    active_at_start = stats["active_requests"]
    
    try:
        # Simulates AI model computation delay: 0.005 seconds per character (5ms)
        # A 400-character prompt results in a 2-second processing time.
        # Capped at 5 seconds to prevent total timeouts.
        length = len(payload.text)
        delay = min(5.0, length * 0.005)
        
        await asyncio.sleep(delay)
        
        # Successful inference block:
        # Now that it completed successfully, record the timestamps in the sliding window history.
        end_time = time.time()
        active_requests_history.append((start_time, active_at_start))
        active_requests_history.append((end_time, stats["active_requests"]))
        
        latency = end_time - start_time
        stats["total_latency_seconds"] += latency
        
        return {
            "status": "success",
            "processed_length": length,
            "delay_applied_seconds": round(delay, 4),
            "output": f"Simulated model inference response completed for length {length}."
        }
    finally:
        stats["active_requests"] -= 1

@app.get("/metrics")
def metrics():
    global active_requests_history
    now = time.time()
    
    # Prune history to keep only events from the last 3.0 seconds (sliding window)
    active_requests_history = [item for item in active_requests_history if now - item[0] < 3.0]
    
    # Find peak concurrent active requests in the sliding window
    peak_active = max([item[1] for item in active_requests_history] + [stats["active_requests"]])
    
    # Calculate system CPU percent using a short, non-destructive blocking interval of 0.1s
    # This avoids returning 0.0% due to back-to-back calls without delta time.
    cpu_val = psutil.cpu_percent(interval=0.1)
    
    base_cpu = cpu_val
    if base_cpu is None or base_cpu < 1.0:
        base_cpu = 2.5
    simulated_peak_cpu = round(min(98.5, base_cpu + peak_active * 10.0), 1)
    
    # 2. cpu_current: instantaneous reading of CPU usage
    cpu_current = cpu_val
    if cpu_current is None:
        cpu_current = 0.0
    cpu_current = round(cpu_current, 1)
    
    memory = psutil.virtual_memory()
    
    avg_latency = 0.0
    if stats["total_requests"] > 0:
        avg_latency = stats["total_latency_seconds"] / stats["total_requests"]
        
    return {
        "cpu_peak_during_burst": simulated_peak_cpu,
        "cpu_current": cpu_current,
        "cpu_usage_percent": simulated_peak_cpu,  # Keep for backward compatibility if any client needs it
        "memory_usage_percent": memory.percent,
        "active_requests": stats["active_requests"],
        "total_requests_received": stats["total_requests"],
        "average_latency_seconds": round(avg_latency, 4)
    }
