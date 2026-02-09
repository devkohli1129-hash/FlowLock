import time
import statistics
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse # Added JSONResponse here
from collections import defaultdict, deque

# 1. App initialization
app = FastAPI(title="Flow Lock - Enterprise Behavioral Defense")

# 2. Global variables
request_logs = defaultdict(lambda: deque(maxlen=100))
blocked_ips = {}

# 3. Helper functions (Kunsh's Sensors)
def extract_behavior_features(ip: str):
    logs = list(request_logs[ip])
    if len(logs) < 2:
        return {"rpm": len(logs), "variance": 1.0}

    now = time.time()
    recent_requests = [t for t in logs if t > (now - 60)]
    rpm = len(recent_requests)
    gaps = [logs[i] - logs[i-1] for i in range(1, len(logs))]
    
    try:
        if len(gaps) > 1:
            var_value = statistics.variance(gaps)
        else:
            var_value = 0.0
    except:
        var_value = 0.0

    return {"rpm": rpm, "variance": round(var_value, 6)}

# 4. Risk scoring logic (Fail-Proof Demo Version)
def calculate_risk_score(features):
    score = 0
    rpm = features['rpm']
    variance = features['variance']
    
    # RULE 1: Velocity
    if rpm > 10: 
        score += 50
    elif rpm > 5:
        score += 20
    
    # RULE 2: Robotic Consistency 
    # We are broadening this significantly. 
    # Even if your computer is laggy, a bot's variance is almost always < 2.0
    if rpm > 2 and variance < 2.0:
        score += 50
        
    # RULE 3: Extreme Speed Override
    # If they hit 15 RPM, we don't care about variance, they are blocked.
    if rpm >= 15:
        score = 100
        
    return min(score, 100)

# 5. Middleware (The Shield) - UPDATED WITH DASHBOARD WHITELIST
@app.middleware("http")
async def abuse_detection_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # NEW: If the user is trying to look at the Dashboard, let them through!
    # This prevents the "Black Screen" on the dashboard during the attack.
    if request.url.path == "/status":
        return await call_next(request)

    # A. Check if IP is in the "Penalty Box"
    if client_ip in blocked_ips:
        remaining = int(blocked_ips[client_ip] - now)
        if remaining > 0:
            return JSONResponse(
                status_code=403, 
                content={"detail": f"Quarantined. Retry in {remaining}s."},
                headers={"Retry-After": str(remaining)}
            )
        else:
            del blocked_ips[client_ip] 

    # B. Record behavior and Analyze
    request_logs[client_ip].append(now)
    features = extract_behavior_features(client_ip)
    risk_score = calculate_risk_score(features)
    
    # C. Execute Block if Risk reaches 100
    if risk_score >= 100:
        blocked_ips[client_ip] = now + 60
        return JSONResponse(
            status_code=403, 
            content={"detail": "Robotic patterns detected. IP Blocked."},
            headers={"Retry-After": "60"}
        )

    # D. Process Request
    try:
        response = await call_next(request)
        response.headers["X-Risk-Score"] = str(risk_score)
        return response
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Bad Request"})

# 6. ENHANCED SECURE DATA ENDPOINT
@app.get("/data", response_class=HTMLResponse)
async def get_data(request: Request):
    risk_score = request.scope.get("risk_score", 0) # Pulling risk from middleware if available
    
    return f"""
    <html>
        <head>
            <title>Secure Data Vault</title>
            <style>
                body {{ 
                    background: #020617; color: #f8fafc; font-family: 'Courier New', monospace; 
                    display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;
                }}
                .vault-card {{
                    border: 2px solid #1e293b; background: #0f172a; padding: 40px;
                    border-radius: 10px; box-shadow: 0 0 50px rgba(56, 189, 248, 0.1);
                    text-align: center; max-width: 500px;
                }}
                .glitch {{ font-size: 1.5rem; font-weight: bold; color: #38bdf8; margin-bottom: 20px; }}
                .data-box {{ 
                    background: #1e293b; padding: 20px; border-radius: 5px; 
                    border-left: 4px solid #38bdf8; text-align: left;
                }}
                .status-line {{ color: #94a3b8; font-size: 0.8rem; margin-top: 20px; }}
                .scanline {{
                    width: 100%; height: 2px; background: rgba(56, 189, 248, 0.2);
                    position: absolute; top: 0; left: 0; animation: scan 4s linear infinite;
                }}
                @keyframes scan {{ 0% {{ top: 0; }} 100% {{ top: 100%; }} }}
            </style>
        </head>
        <body>
            <div class="scanline"></div>
            <div class="vault-card">
                <div class="glitch">UNLOCKED: SECURE_CORE_v4.2</div>
                <div class="data-box">
                    <p style="margin:0; color: #22c55e;">> CONNECTION: ENCRYPTED</p>
                    <p style="margin:10px 0; color: #cbd5e1;">> CONTENT: "Financial_Report_2026.pdf"</p>
                    <p style="margin:0; color: #cbd5e1;">> LOCATION: SERVER_RACK_09</p>
                </div>
                <div class="status-line">
                    PROTECTION: FLOW LOCK ACTIVE <br>
                    REFRESH TO SYNC DATA
                </div>
            </div>
        </body>
    </html>
    """

# 7. MODERN 3D COMMAND CENTER
@app.get("/status", response_class=HTMLResponse)
async def get_status():
    active_rows = ""
    for ip in request_logs.keys():
        feat = extract_behavior_features(ip)
        risk = calculate_risk_score(feat)
        # Dynamic color logic
        color = "#22c55e" if risk < 50 else "#f59e0b"
        shadow = "0 0 10px #22c55e55" if risk < 50 else "0 0 10px #f59e0b55"
        
        active_rows += f"""
        <tr class="glass-row">
            <td><span class="ip-badge">{ip}</span></td>
            <td>{feat['rpm']} <small>req/m</small></td>
            <td>{feat['variance']}</td>
            <td><div class="risk-pill" style="background:{color}; box-shadow:{shadow}">{risk}%</div></td>
        </tr>"""

    blocked_rows = ""
    for ip, expiry in blocked_ips.items():
        time_left = max(0, int(expiry - time.time()))
        blocked_rows += f"""
        <tr class="blocked-row">
            <td>{ip}</td>
            <td><span class="status-tag">QUARANTINED</span></td>
            <td class="timer-text">{time_left}s</td>
        </tr>"""
    
    if not blocked_ips:
        blocked_rows = "<tr><td colspan='3' style='color:#64748b; padding:20px;'>System Secure - No active threats</td></tr>"

    return f"""
    <html>
        <head>
            <title>Flow Lock | Intelligence</title>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <style>
                :root {{ --bg: #030712; --card: #111827; --accent: #38bdf8; --danger: #ef4444; }}
                body {{ 
                    background: var(--bg); color: white; font-family: 'Inter', sans-serif; 
                    margin: 0; padding: 40px; display: flex; flex-direction: column; align-items: center;
                    background: radial-gradient(circle at top right, #1e1b4b, #030712);
                }}
                .header {{ text-align: left; width: 90%; max-width: 1100px; margin-bottom: 30px; }}
                h1 {{ margin: 0; font-size: 2.5rem; letter-spacing: -1px; color: var(--accent); text-shadow: 0 0 20px rgba(56, 189, 248, 0.3); }}
                .container {{ 
                    width: 95%; max-width: 1100px; display: grid; grid-template-columns: 1.5fr 1fr; gap: 25px; 
                }}
                .card {{ 
                    background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px;
                    padding: 25px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    transition: transform 0.3s ease, border-color 0.3s ease;
                }}
                .card:hover {{ transform: translateY(-5px) perspective(1000px) rotateX(2deg); border-color: var(--accent); }}
                
                table {{ width: 100%; border-collapse: separate; border-spacing: 0 8px; }}
                th {{ text-align: left; color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; padding: 10px; }}
                td {{ padding: 15px 10px; background: rgba(255,255,255,0.03); }}
                td:first-child {{ border-radius: 10px 0 0 10px; }}
                td:last-child {{ border-radius: 0 10px 10px 0; }}

                .risk-pill {{ 
                    padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.8rem; 
                    display: inline-block; color: white;
                }}
                .ip-badge {{ font-family: monospace; color: var(--accent); font-weight: bold; }}
                .status-tag {{ 
                    color: var(--danger); font-weight: bold; font-size: 0.8rem;
                    animation: pulse 2s infinite; 
                }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
                .timer-text {{ color: #94a3b8; font-weight: bold; }}
                
                .indicator {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #22c55e; margin-right: 10px; box-shadow: 0 0 10px #22c55e; }}
            </style>
            <meta http-equiv="refresh" content="2">
        </head>
        <body>
            <div class="header">
                <h1>🛡️ FLOW LOCK <small style="font-size: 1rem; color: #94a3b8; vertical-align: middle;">| BEHAVIORAL ANALYTICS</small></h1>
                <p><span class="indicator"></span> System Online - Monitoring Layer 7 Traffic</p>
            </div>
            <div class="container">
                <div class="card">
                    <h3 style="margin-top:0">📡 REAL-TIME THREAT RADAR</h3>
                    <table>
                        <tr><th>Target IP</th><th>Velocity</th><th>Variance</th><th>Risk</th></tr>
                        {active_rows}
                    </table>
                </div>
                <div class="card" style="border-left: 4px solid var(--danger);">
                    <h3 style="margin-top:0; color: var(--danger);">🚫 QUARANTINE ZONE</h3>
                    <table>
                        <tr><th>Attacker IP</th><th>Status</th><th>Expires</th></tr>
                        {blocked_rows}
                    </table>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)