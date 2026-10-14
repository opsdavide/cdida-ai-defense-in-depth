import asyncio
import time
import httpx
from tqdm.asyncio import tqdm

AI_SERVER_URL = "http://localhost:5001"
CONCURRENT_REQUESTS = 100
HEAVY_PROMPT = "A" * 400

async def send_single_request(client: httpx.AsyncClient, idx: int):
    url = f"{AI_SERVER_URL}/inference"
    payload = {"text": HEAVY_PROMPT}
    start = time.time()
    try:
        response = await client.post(url, json=payload, timeout=30.0)
        latency = time.time() - start
        return response.status_code, latency
    except Exception as e:
        latency = time.time() - start
        return 0, latency  # 0 status code represents network/timeout error

async def get_metrics():
    url = f"{AI_SERVER_URL}/metrics"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=5.0)
            return resp.json()
    except Exception:
        return None

async def poll_metrics_task(stop_event: asyncio.Event, poll_interval: float = 0.3):
    """
    Background task to sample metrics during the burst.
    This task is completely silent and does not write to the terminal.
    """
    cpu_peaks = []
    while not stop_event.is_set():
        try:
            metrics = await get_metrics()
            if metrics:
                cpu_peaks.append(metrics.get("cpu_peak_during_burst", 0.0))
        except Exception:
            pass
        await asyncio.sleep(poll_interval)
    return cpu_peaks

async def run_scenario_a():
    print("=" * 60)
    print("SCENARIO A: Direct Attack Simulation (No Protections)")
    print(f"Targeting AI Application Server directly at: {AI_SERVER_URL}")
    print(f"Sending {CONCURRENT_REQUESTS} heavy requests concurrently...")
    print("=" * 60)

    initial_metrics = await get_metrics()
    if not initial_metrics:
        print("[WARNING] Could not retrieve initial metrics. Make sure docker-compose is running!")
    
    start_time = time.time()
    
    # Start background polling of metrics (completely silent during burst)
    stop_event = asyncio.Event()
    polling_task = asyncio.create_task(poll_metrics_task(stop_event, poll_interval=0.3))
    
    limits = httpx.Limits(max_keepalive_connections=200, max_connections=200)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [send_single_request(client, i) for i in range(CONCURRENT_REQUESTS)]
        results = await tqdm.gather(*tasks, desc="Attacking AI Server")

    # Stop polling
    stop_event.set()
    polled_cpu_peaks = await polling_task
    
    total_time = time.time() - start_time
    
    # Analyze responses
    status_counts = {}
    for code, _ in results:
        status_counts[code] = status_counts.get(code, 0) + 1
        
    success_count = status_counts.get(200, 0)
    failure_count = len(results) - success_count
    
    # Calculate times for accepted vs rejected/failed requests
    accepted_latencies = [lat for code, lat in results if code == 200]
    rejected_latencies = [lat for code, lat in results if code != 200]
    
    sum_accepted_time = sum(accepted_latencies)
    sum_rejected_time = sum(rejected_latencies)
    
    latencies = [latency for _, latency in results]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    final_metrics = await get_metrics()
    
    cpu_peak_percent = max(polled_cpu_peaks) if polled_cpu_peaks else (final_metrics.get("cpu_peak_during_burst", 0.0) if final_metrics else 0.0)
    cpu_post_test_percent = final_metrics.get("cpu_current", 0.0) if final_metrics else 0.0
    memory_usage = final_metrics.get("memory_usage_percent", 0.0) if final_metrics else 0.0
    total_received = final_metrics.get("total_requests_received", 0) if final_metrics else 0

    # Format output according to the requested template
    print("\n" + "=" * 60)
    print("RESULTS - SCENARIO A (UNPROTECTED)")
    print("-" * 60)
    print(f"Total Requests Sent:   {CONCURRENT_REQUESTS}")
    print("Response breakdown:")
    for code, count in sorted(status_counts.items()):
        if code == 200:
            print(f"  HTTP 200 (Success):  {count}")
        elif code == 429:
            print(f"  HTTP 429 (Blocked):  {count}")
        elif code == 0:
            print(f"  Network Error:       {count}")
        else:
            print(f"  HTTP {code}:         {count}")
    print("-" * 60)
    print("AI Server Status:")
    print(f"  CPU Peak (Burst):    {cpu_peak_percent:.1f}% (Simulated/Analytical)")
    print(f"  CPU Current:         {cpu_post_test_percent:.1f}% (Real Process CPU)")
    print(f"  RAM Usage:           {memory_usage:.1f}%")
    print(f"  Total Req Received:  {total_received}")
    print("=" * 60)

    # Save statistics report
    # Note on execution time: The total elapsed time does not scale linearly with accepted requests
    # because all requests run in parallel (concurrency). Rejected requests complete instantly but
    # require network/TCP overhead, while accepted requests run concurrently on the AI server.
    with open("scenario_a_results.csv", "w") as f:
        f.write("scenario,total_req,success_req,failed_req,avg_latency_s,elapsed_time_s,accepted_cumulative_s,rejected_cumulative_s,cpu_peak_pct,cpu_post_test_pct\n")
        f.write(f"A_unprotected,{CONCURRENT_REQUESTS},{success_count},{failure_count},{avg_latency:.2f},{total_time:.2f},{sum_accepted_time:.2f},{sum_rejected_time:.2f},{cpu_peak_percent},{cpu_post_test_percent}\n")
        f.write("\n# Spiegazione Tempo di Esecuzione: Il tempo totale reale di esecuzione del test (elapsed time) non scala linearmente con le richieste accettate poiche tutte le richieste vengono inviate in parallelo (concorrenza). Le richieste respinte/fallite liberano il client quasi subito ma consumano comunque frazioni di secondo per l'overhead di rete/TCP, mentre le richieste accettate competono per le risorse di inferenza in parallelo sul backend.\n")
    print("Report saved to scenario_a_results.csv")

if __name__ == "__main__":
    asyncio.run(run_scenario_a())
