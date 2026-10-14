import asyncio
import time
import httpx
from tqdm.asyncio import tqdm

PROXY_URL = "http://localhost:8080"
GATEWAY_URL = "http://localhost:8000"
AI_SERVER_URL = "http://localhost:5001"  # Read AI metrics directly from host
CONCURRENT_REQUESTS = 100
HEAVY_PROMPT = "A" * 400

async def get_token(role: str, target_url: str) -> str:
    url = f"{target_url}/api/v1/auth/token?role={role}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, timeout=5.0)
            if resp.status_code == 200:
                return resp.json().get("access_token")
            else:
                print(f"[ERROR] Failed to obtain token from {url}: {resp.text}")
                return None
    except Exception as e:
        print(f"[ERROR] Connection to {url} failed: {e}")
        return None

async def send_single_request(client: httpx.AsyncClient, token: str, idx: int, target_url: str):
    url = f"{target_url}/api/v1/inference"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"prompt": HEAVY_PROMPT}
    start = time.time()
    try:
        response = await client.post(url, json=payload, headers=headers, timeout=30.0)
        latency = time.time() - start
        return response.status_code, latency
    except Exception as e:
        latency = time.time() - start
        return 0, latency

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

async def run_scenario(role: str = "guest", bypass_nginx: bool = False):
    target_url = PROXY_URL
    is_bypassed = False
    if bypass_nginx:
        if role in ["admin", "employee"]:
            target_url = GATEWAY_URL
            is_bypassed = True
        else:
            print("[WARNING] Nginx bypass is only permitted/applicable for roles 'employee' and 'admin'. Routing through Nginx proxy instead.")

    # Mapping to formal scenarios
    scenario_map = {
        "guest": ("B", "Ruolo Guest - Limite 5 req/min"),
        "employee": ("C", "Ruolo Employee - Quota 60 req/min"),
        "admin": ("D", "Ruolo Admin - Accesso Illimitato")
    }
    scenario_letter, scenario_desc = scenario_map.get(role, ("B", role))

    print("=" * 60)
    print(f"SCENARIO {scenario_letter}: Protetto ({scenario_desc})")
    if is_bypassed:
        print(f"Ingresso: API Gateway DIRETTO (Porta 8000, Nginx Bypassed)")
    else:
        print(f"Ingresso: Reverse Proxy Nginx (Porta 8080)")
        if role in ["employee", "admin"]:
            print(f"[NOTA] Il traffico da singolo IP è soggetto al filtro Layer 1 di Nginx (burst=5).")
            print(f"       Per testare le quote RBAC del Gateway isolato, usa: --bypass-nginx")
    print(f"Autenticazione JWT: Ruolo '{role}'")
    print("=" * 60)
    
    token = await get_token(role, target_url)
    if not token:
        print("[ERROR] Impossibile acquisire il token JWT. Verificare che Docker Compose sia attivo.")
        return
        
    print(f"JWT acquisito con successo.")
    if is_bypassed:
        print(f"Invio di {CONCURRENT_REQUESTS} richieste concorrenti direttamente al Gateway...")
    else:
        print(f"Invio di {CONCURRENT_REQUESTS} richieste concorrenti tramite Nginx Proxy...")
    print("-" * 60)

    start_time = time.time()
    
    # Start background polling of metrics (completely silent during burst)
    stop_event = asyncio.Event()
    polling_task = asyncio.create_task(poll_metrics_task(stop_event, poll_interval=0.3))
    
    limits = httpx.Limits(max_keepalive_connections=200, max_connections=200)
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [send_single_request(client, token, i, target_url) for i in range(CONCURRENT_REQUESTS)]
        results = await tqdm.gather(*tasks, desc="Sending protected traffic")
        
    # Stop polling
    stop_event.set()
    polled_cpu_peaks = await polling_task
    
    total_time = time.time() - start_time
    
    # Parse status codes and latencies
    status_counts = {}
    latencies = []
    
    # Calculate times for accepted vs rejected/failed requests
    accepted_latencies = []
    rejected_latencies = []
    
    for status_code, latency in results:
        status_counts[status_code] = status_counts.get(status_code, 0) + 1
        latencies.append(latency)
        if status_code == 200:
            accepted_latencies.append(latency)
        else:
            rejected_latencies.append(latency)
        
    sum_accepted_time = sum(accepted_latencies)
    sum_rejected_time = sum(rejected_latencies)
    
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    final_metrics = await get_metrics()
    
    cpu_peak_percent = max(polled_cpu_peaks) if polled_cpu_peaks else (final_metrics.get("cpu_peak_during_burst", 0.0) if final_metrics else 0.0)
    cpu_post_test_percent = final_metrics.get("cpu_current", 0.0) if final_metrics else 0.0
    memory_usage = final_metrics.get("memory_usage_percent", 0.0) if final_metrics else 0.0
    total_received = final_metrics.get("total_requests_received", 0) if final_metrics else 0

    # Format output according to the requested template
    print("\n" + "=" * 60)
    bypass_tag = " - BYPASS NGINX" if is_bypassed else ""
    print(f"RISULTATI - SCENARIO {scenario_letter} (PROTETTO - {role.upper()}{bypass_tag})")
    print("-" * 60)
    print(f"Richieste Totali Inviate:   {CONCURRENT_REQUESTS}")
    print("Dettaglio Risposte HTTP:")
    for code, count in sorted(status_counts.items()):
        if code == 200:
            print(f"  HTTP 200 (Successo):       {count}")
        elif code == 429:
            print(f"  HTTP 429 (Bloccate/Quota): {count}")
        elif code == 400:
            print(f"  HTTP 400 (Bloccate/IDS):   {count}")
        elif code == 0:
            print(f"  Errore di Rete:            {count}")
        else:
            print(f"  HTTP {code}:               {count}")
    print("-" * 60)
    print("Stato Risorse AI Server:")
    print(f"  CPU Peak (Burst):          {cpu_peak_percent:.1f}% (Analitico/Simulato)")
    print(f"  CPU Current:               {cpu_post_test_percent:.1f}% (Processo Reale)")
    print(f"  RAM Usage:                 {memory_usage:.1f}%")
    print(f"  Totale Richieste Ricevute: {total_received}")
    print("=" * 60)

    # Save statistics report
    scenario_filename = f"scenario_{scenario_letter.lower()}_results.csv"
    with open(scenario_filename, "w") as f:
        f.write("scenario,role,total_req,success_req,rate_limited_req,invalid_payload_req,avg_latency_s,elapsed_time_s,accepted_cumulative_s,rejected_cumulative_s,cpu_peak_pct,cpu_post_test_pct\n")
        f.write(f"{scenario_letter}_{role},{role},{CONCURRENT_REQUESTS},{status_counts.get(200, 0)},{status_counts.get(429, 0)},{status_counts.get(400, 0)},{avg_latency:.2f},{total_time:.2f},{sum_accepted_time:.2f},{sum_rejected_time:.2f},{cpu_peak_percent},{cpu_post_test_percent}\n")
    print(f"Report salvato in {scenario_filename}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Esegui Test di Carico Protetto (Scenari B, C, D)")
    parser.add_argument(
        "pos_role", 
        choices=["guest", "employee", "admin"], 
        nargs="?", 
        default=None,
        help="Ruolo per il test: guest (Scenario B), employee (Scenario C), admin (Scenario D)."
    )
    parser.add_argument(
        "--role", "-r",
        choices=["guest", "employee", "admin"], 
        default=None,
        help="Flag esplicito per il ruolo (guest, employee, admin)."
    )
    parser.add_argument(
        "--bypass-nginx", 
        action="store_true",
        help="Bypassa il proxy Nginx (porta 8080) e invia il traffico direttamente all'API Gateway (porta 8000) per testare le quote RBAC per employee e admin."
    )
    args = parser.parse_args()
    
    selected_role = args.role or args.pos_role or "guest"
    asyncio.run(run_scenario(selected_role, args.bypass_nginx))
