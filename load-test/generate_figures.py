import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Output directory for figures
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "figures"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Set style and aesthetic defaults
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'

# -------------------------------------------------------------
# 1. FIGURA: Architettura di Rete Defense-in-Depth (Simmetrica T-Layout)
# -------------------------------------------------------------
def generate_architecture_diagram():
    fig, ax = plt.subplots(figsize=(14.0, 8.5), dpi=300)
    ax.set_xlim(0, 14.0)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    # Main Title
    ax.text(7.0, 8.05, "Architettura di Rete Cloud-Native Defense-in-Depth", 
            ha='center', va='center', fontsize=16, fontweight='bold', color='#0f172a')

    # External Zone (Internet / Client)
    rect_ext = patches.FancyBboxPatch((0.4, 0.8), 2.8, 6.7, boxstyle="round,pad=0.15", 
                                      ec="#94a3b8", fc="#f8fafc", lw=1.5, linestyle=":")
    ax.add_patch(rect_ext)
    ax.text(1.8, 7.15, "Ambiente Host / Internet", ha='center', fontsize=10.5, fontweight='bold', color="#475569")

    # Client Box
    box_client = patches.FancyBboxPatch((0.6, 4.8), 2.4, 1.8, boxstyle="round,pad=0.1", ec="#334155", fc="#ffffff", lw=1.5)
    ax.add_patch(box_client)
    ax.text(1.8, 5.9, "Client / Attacker\n(Load Test Script)", ha='center', va='center', fontsize=10, fontweight='bold', color="#1e293b")
    ax.text(1.8, 5.2, "Traffico Concorrente\n(100 Richieste)", ha='center', va='center', fontsize=8.5, color="#64748b")

    # VPC Container Boundary
    rect_vpc = patches.FancyBboxPatch((3.6, 0.5), 10.0, 7.0, boxstyle="round,pad=0.2", 
                                      ec="#cbd5e1", fc="#ffffff", lw=1.2)
    ax.add_patch(rect_vpc)
    ax.text(3.9, 7.2, "Docker Environment / Virtual Private Cloud (VPC)", fontsize=11, fontweight='bold', color="#334155")

    # Subnet 1: frontend_net (Public DMZ)
    rect_front = patches.FancyBboxPatch((3.9, 4.3), 9.4, 2.6, boxstyle="round,pad=0.15", 
                                        ec="#3b82f6", fc="#eff6ff", lw=1.5, linestyle="--")
    ax.add_patch(rect_front)
    ax.text(4.2, 6.55, "Subnet Pubblica (frontend_net - Bridge DMZ)", fontsize=10.5, fontweight='bold', color="#1d4ed8")

    # Nginx Proxy Box (Centered in DMZ)
    box_nginx = patches.FancyBboxPatch((6.8, 4.6), 3.6, 1.6, boxstyle="round,pad=0.1", ec="#2563eb", fc="#dbeafe", lw=1.5)
    ax.add_patch(box_nginx)
    ax.text(8.6, 5.6, "Nginx Reverse Proxy\n(Layer 1 - Filtro Volumetrico)", ha='center', va='center', fontsize=10, fontweight='bold', color="#1e40af")
    ax.text(8.6, 4.95, "Porta 8080 (10 req/s, Burst: 5)", ha='center', va='center', fontsize=8.5, color="#1e3a8a")

    # Subnet 2: backend_net (Isolated Private)
    rect_back = patches.FancyBboxPatch((3.9, 0.8), 9.4, 3.1, boxstyle="round,pad=0.15", 
                                       ec="#ef4444", fc="#fef2f2", lw=1.5, linestyle="--")
    ax.add_patch(rect_back)
    ax.text(4.2, 3.55, "Subnet Privata Isolata (backend_net - internal: true)", fontsize=10.5, fontweight='bold', color="#b91c1c")

    # Redis Box (Left in Backend)
    box_redis = patches.FancyBboxPatch((4.2, 1.1), 2.2, 2.1, boxstyle="round,pad=0.1", ec="#dc2626", fc="#fee2e2", lw=1.5)
    ax.add_patch(box_redis)
    ax.text(5.3, 2.45, "Redis Cache", ha='center', va='center', fontsize=10, fontweight='bold', color="#991b1b")
    ax.text(5.3, 1.95, "• Sliding Window Log\n• Operazioni ZSET", ha='center', va='center', fontsize=8, color="#7f1d1d")
    ax.text(5.3, 1.4, "Porta 6379 (Isolata)", ha='center', va='center', fontsize=8, color="#991b1b", fontweight='bold')

    # Gateway Box (Center in Backend)
    box_gw = patches.FancyBboxPatch((7.1, 1.0), 3.0, 2.3, boxstyle="round,pad=0.1", ec="#059669", fc="#d1fae5", lw=1.5)
    ax.add_patch(box_gw)
    ax.text(8.6, 2.75, "API Gateway (FastAPI)", ha='center', va='center', fontsize=10.5, fontweight='bold', color="#065f46")
    ax.text(8.6, 2.0, "• Layer 2: RBAC JWT\n• Layer 3: Payload Inspector IDS\n• Audit Log HMAC-SHA256", ha='center', va='center', fontsize=8, color="#047857")
    ax.text(8.6, 1.3, "Porta 8000 (Dual Network)", ha='center', va='center', fontsize=8, color="#065f46", fontweight='bold')

    # AI Server Box (Right in Backend)
    box_ai = patches.FancyBboxPatch((10.7, 1.1), 2.3, 2.1, boxstyle="round,pad=0.1", ec="#7c3aed", fc="#ede9fe", lw=1.5)
    ax.add_patch(box_ai)
    ax.text(11.85, 2.45, "AI Server (LLM)", ha='center', va='center', fontsize=10, fontweight='bold', color="#5b21b6")
    ax.text(11.85, 1.95, "• Inference Engine\n• Metriche CPU\n• /inference", ha='center', va='center', fontsize=8, color="#4c1d95")
    ax.text(11.85, 1.4, "Porta 5001 (Isolata)", ha='center', va='center', fontsize=8, color="#5b21b6", fontweight='bold')

    # --- ARROWS & FLOWS ---
    # 1. Client -> Nginx (Port 8080)
    ax.annotate("", xy=(6.8, 5.4), xytext=(3.0, 5.4),
                arrowprops=dict(arrowstyle="->", lw=2.2, color="#2563eb"))
    ax.text(4.9, 5.7, "1. HTTP Request (Porta 8080)", ha='center', fontsize=9, fontweight='bold', color="#1d4ed8")

    # 2. Nginx -> Gateway (Clean Vertical Flow with white background badge)
    ax.annotate("", xy=(8.6, 3.3), xytext=(8.6, 4.6),
                arrowprops=dict(arrowstyle="->", lw=2.2, color="#059669"))
    ax.text(8.6, 3.95, "2. Inoltro Safe Requests", ha='center', va='center', fontsize=8.5, fontweight='bold', color="#065f46",
            bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec="#059669", lw=0.8))

    # 3. Gateway <-> Redis (Sliding Window Log)
    ax.annotate("", xy=(6.4, 2.05), xytext=(7.1, 2.05),
                arrowprops=dict(arrowstyle="<->", lw=2.0, color="#dc2626"))
    ax.text(6.75, 2.35, "ZSET", ha='center', fontsize=8.5, fontweight='bold', color="#991b1b")

    # 4. Gateway -> AI Server (Authorized Inference)
    ax.annotate("", xy=(10.7, 2.05), xytext=(10.1, 2.05),
                arrowprops=dict(arrowstyle="->", lw=2.2, color="#7c3aed"))
    ax.text(10.4, 2.35, "3. Safe", ha='center', fontsize=8.5, fontweight='bold', color="#5b21b6")

    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "architettura_rete.png")
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generated: {png_path}")

# -------------------------------------------------------------
# 2. FIGURA: Benchmark Comparativo CPU Peak
# -------------------------------------------------------------
def generate_cpu_benchmark():
    fig, ax = plt.subplots(figsize=(11.5, 7.0), dpi=300)

    scenarios = [
        'Scenario A\n(Attacco Diretto,\nNessuna Protezione)',
        'Scenario B\n(Ruolo Guest,\nNginx + Gateway)',
        'Scenario C\n(Ruolo Employee,\nGateway Isolato)',
        'Scenario D\n(Ruolo Admin,\nBypass Rate Limit)'
    ]
    
    cpu_peaks = [98.5, 10.0, 60.0, 98.5]
    requests_dropped = [0, 95, 40, 0]

    x = np.arange(len(scenarios))
    width = 0.32

    rects1 = ax.bar(x - width/2, cpu_peaks, width, label='Picco CPU Backend (%)', 
                    color=['#ef4444', '#10b981', '#3b82f6', '#8b5cf6'], edgecolor='black', lw=0.8)
    rects2 = ax.bar(x + width/2, requests_dropped, width, label='Richieste Respinte (%)', 
                    color=['#9ca3af', '#34d399', '#60a5fa', '#c084fc'], alpha=0.7, hatch='//', edgecolor='black', lw=0.8)

    ax.set_ylabel('Percentuale (%)', fontsize=11.5, fontweight='bold', color='#1e293b')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=10, fontweight='bold', color='#334155')
    ax.set_ylim(0, 135)

    # Title with generous top space
    fig.suptitle('Confronto Prestazionale e Resilienza della CPU (100 Richieste Concorrenti)', 
                 fontsize=14.5, fontweight='bold', color='#0f172a', y=0.98)

    # Legend cleanly placed below the title
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.08), ncol=2, fontsize=10.5, 
              frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', framealpha=0.95)

    # Value labels above bars
    for rect in rects1:
        height = rect.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9.5, fontweight='bold', color='#0f172a')

    for rect in rects2:
        height = rect.get_height()
        ax.annotate(f'{int(height)}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9.5, fontstyle='italic', color='#475569')

    # Callout badge with generous clearance above the 95% bar
    ax.text(1, 118, "Protezione Massima (Guest):\n-90% Picco CPU | 95% Drop", 
            ha='center', va='center', fontsize=9.5, fontweight='bold', color="#065f46",
            bbox=dict(boxstyle="round,pad=0.4", fc="#ecfdf5", ec="#10b981", lw=1.2))

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    png_path = os.path.join(OUTPUT_DIR, "benchmark_cpu_peak.png")
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generated: {png_path}")

# -------------------------------------------------------------
# 3. FIGURA: Tempo di Risposta e Latenza di Scarto
# -------------------------------------------------------------
def generate_latency_benchmark():
    fig, ax = plt.subplots(figsize=(9.5, 5.0), dpi=300)

    categories = [
        'Inferenza AI Backend\n(Elaborazione Accettata)', 
        'Scarto Nginx (HTTP 429)\n(Drop Volumetrico)', 
        'Scarto Gateway (HTTP 429/400)\n(Sliding Window / IDS)'
    ]
    avg_times_ms = [2000.0, 1.8, 3.5]
    colors = ['#f97316', '#3b82f6', '#10b981']

    bars = ax.barh(categories, avg_times_ms, color=colors, edgecolor='black', lw=0.8, height=0.5)
    ax.set_xscale('log')
    ax.set_xlabel('Tempo di Risposta Medio (Millisecondi - Scala Logaritmica)', fontsize=10.5, fontweight='bold')
    ax.set_title('Efficienza Temporale: Elaborazione Backend vs Scarto al Perimetro', fontsize=12.5, fontweight='bold', pad=15)

    for bar in bars:
        width = bar.get_width()
        if width > 100:
            label = f'  {width:.0f} ms (~{width/1000:.1f}s)'
        else:
            label = f'  {width:.1f} ms'
        ax.annotate(label,
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=10, fontweight='bold')

    ax.set_xlim(0.5, 15000)
    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "benchmark_latency_time.png")
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generated: {png_path}")

# -------------------------------------------------------------
# 4. FIGURA: Diagramma di Sequenza a 3 Livelli
# -------------------------------------------------------------
def generate_sequence_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8.5)
    ax.axis('off')

    ax.text(5.5, 8.1, "Flusso di Ispezione Sequenziale a 3 Livelli (Defense-in-Depth)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#0f172a')

    # Lifelines headers
    nodes = [
        ("Client\nAttaccante", 1.2), 
        ("Nginx Proxy\n(Layer 1)", 4.0), 
        ("API Gateway\n(Layer 2 & 3)", 7.0), 
        ("AI Server\n(Backend)", 9.8)
    ]
    
    for name, x in nodes:
        ax.text(x, 7.2, name, ha='center', va='center', fontsize=9.5, fontweight='bold', 
                bbox=dict(boxstyle="round,pad=0.3", fc="#f1f5f9", ec="#475569", lw=1))
        ax.plot([x, x], [0.5, 6.6], color="#94a3b8", linestyle=":", lw=1.2)

    # 1. Client -> Nginx
    ax.annotate("", xy=(4.0, 6.0), xytext=(1.2, 6.0), arrowprops=dict(arrowstyle="->", lw=1.8, color="#2563eb"))
    ax.text(2.6, 6.25, "1. HTTP Request Flood (100 req)", ha='center', fontsize=8.5, color="#1e40af", fontweight='bold')

    # Check 1 at Nginx
    ax.text(4.0, 5.45, "[L1] Rate Limit Check\n(10 r/s, burst=5)", ha='center', fontsize=8, color="#1e3a8a",
            bbox=dict(boxstyle="round,pad=0.2", fc="#dbeafe", ec="#3b82f6", lw=0.8))

    # Reject at Nginx (L1 Drop)
    ax.annotate("", xy=(1.2, 4.8), xytext=(4.0, 4.8), arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626", linestyle="--"))
    ax.text(2.6, 5.05, "Drop Volumetrico: HTTP 429 (<2ms)", ha='center', fontsize=8, color="#b91c1c", fontweight='bold')

    # 2. Forward Safe to Gateway
    ax.annotate("", xy=(7.0, 4.1), xytext=(4.0, 4.1), arrowprops=dict(arrowstyle="->", lw=1.8, color="#059669"))
    ax.text(5.5, 4.35, "2. Inoltro Safe Requests", ha='center', fontsize=8.5, color="#065f46", fontweight='bold')

    # Check 2 & 3 at Gateway
    ax.text(7.0, 3.45, "[L2] JWT Role & Redis Sliding Window\n[L3] Payload Inspector (Repetition/Spam)", 
            ha='center', fontsize=8, color="#047857",
            bbox=dict(boxstyle="round,pad=0.2", fc="#d1fae5", ec="#10b981", lw=0.8))

    # Reject at Gateway (L2/L3 Drop)
    ax.annotate("", xy=(1.2, 2.65), xytext=(7.0, 2.65), arrowprops=dict(arrowstyle="->", lw=1.5, color="#dc2626", linestyle="--"))
    ax.text(4.1, 2.9, "Violazione Policy: HTTP 429 / HTTP 400 + HMAC Log", ha='center', fontsize=8, color="#b91c1c", fontweight='bold')

    # 3. Gateway -> AI Server
    ax.annotate("", xy=(9.8, 1.8), xytext=(7.0, 1.8), arrowprops=dict(arrowstyle="->", lw=1.8, color="#7c3aed"))
    ax.text(8.4, 2.05, "3. Safe Inference", ha='center', fontsize=8.5, color="#5b21b6", fontweight='bold')

    # 4. AI Server -> Gateway
    ax.annotate("", xy=(7.0, 1.2), xytext=(9.8, 1.2), arrowprops=dict(arrowstyle="->", lw=1.5, color="#7c3aed", linestyle="-."))
    ax.text(8.4, 1.45, "4. Result (HTTP 200)", ha='center', fontsize=8, color="#5b21b6")

    # 5. Gateway -> Client (Success Return)
    ax.annotate("", xy=(1.2, 0.7), xytext=(7.0, 0.7), arrowprops=dict(arrowstyle="->", lw=1.5, color="#059669", linestyle="-."))
    ax.text(4.1, 0.95, "5. HTTP 200 OK Safe Completion", ha='center', fontsize=8, color="#065f46", fontweight='bold')

    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "sequence_defense_layers.png")
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generated: {png_path}")

# -------------------------------------------------------------
# 5. FIGURA: Matrice delle Minacce (Card Visual Infographic)
# -------------------------------------------------------------
def generate_threat_matrix():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6.8)
    ax.axis('off')

    ax.text(6.0, 6.4, "Matrice di Threat Modeling e Meccanismi di Mitigazione", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#0f172a')

    rows = [
        ("HTTP Flood Volumetrico (L7)", "Livello 1 (Perimetro)", "Nginx (limit_req)", "HTTP 429 istantaneo (<2ms)", "#2563eb"),
        ("SYN Flood / IP Spoofing (L4)", "Livello 1 (Socket/TCP)", "TCP 3-Way Handshake", "Impossibile hijack sessione TCP", "#1d4ed8"),
        ("Abuso Quota Utente / Credenziali", "Livello 2 (Gateway)", "Redis Sliding Window", "Blocco 429 granulare RBAC", "#059669"),
        ("DoS Semantico (Prompt >500 char)", "Livello 3 (IDS)", "Payload Inspector (Length)", "HTTP 400 Bad Request", "#d97706"),
        ("Prompt Flood Ripetitivo (Spam)", "Livello 3 (IDS)", "MD5 Duplicate & Entropy", "HTTP 400 (Risk Score > 0.7)", "#dc2626"),
        ("Manomissione Log di Audit", "Transversale (Forensics)", "HMAC-SHA256 Signer", "Integrità garantita tamper-evident", "#7c3aed")
    ]

    y_start = 5.5
    for i, (attack, layer, tech, outcome, col) in enumerate(rows):
        y = y_start - (i * 0.85)
        # Row card background with extra width
        card = patches.FancyBboxPatch((0.4, y - 0.35), 11.2, 0.7, boxstyle="round,pad=0.08", 
                                      ec=col, fc="#f8fafc", lw=1.2)
        ax.add_patch(card)
        
        # Color bar indicator on the left
        bar = patches.Rectangle((0.4, y - 0.35), 0.25, 0.7, color=col)
        ax.add_patch(bar)

        ax.text(0.9, y, attack, fontsize=9.5, fontweight='bold', color="#1e293b", va='center')
        ax.text(4.2, y, layer, fontsize=8.5, color="#475569", va='center')
        ax.text(6.3, y, tech, fontsize=8.5, color="#334155", va='center', fontstyle='italic')
        ax.text(8.4, y, outcome, fontsize=8.5, fontweight='bold', color="#065f46", va='center')

    plt.tight_layout()
    png_path = os.path.join(OUTPUT_DIR, "threat_model_mitigation.png")
    plt.savefig(png_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Generated: {png_path}")

if __name__ == "__main__":
    print("Generating publication-ready PNG figures (PDF generation disabled)...")
    generate_architecture_diagram()
    generate_cpu_benchmark()
    generate_latency_benchmark()
    generate_sequence_diagram()
    generate_threat_matrix()
    print(f"All figures successfully generated in: {OUTPUT_DIR}")
