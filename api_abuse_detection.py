import time
import asyncio
import hashlib
import statistics
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from collections import defaultdict, deque

# 1. App initialization
app = FastAPI(title="Flow Lock - Enterprise Behavioral Defense")

# 2. Global variables

def generate_fingerprint(request: Request):
    # We combine the User-Agent and Accept-Language headers
    user_agent = request.headers.get("user-agent", "unknown")
    language = request.headers.get("accept-language", "unknown")
    raw_id = f"{user_agent}|{language}"
    # Create a unique 8-character ID for this "browser/bot type"
    return hashlib.md5(raw_id.encode()).hexdigest()[:8]

request_logs = defaultdict(lambda: deque(maxlen=100))
blocked_ips = {}
block_reasons = {}
honeypot_victims = set()
blocked_fingerprints = set()
highest_risk_seen = defaultdict(float)

# 3. Helper functions (Sensors)
def extract_behavior_features(ip: str):
    logs = list(request_logs[ip])
    if len(logs) < 2:
        return {"rpm": len(logs), "variance": 1.0}

    now = time.time()
    recent_requests = [t for t in logs if t > (now - 120)]
    rpm = len(recent_requests)
    
    gaps = [logs[i] - logs[i-1] for i in range(1, len(logs))]
    try:
        var_value = statistics.variance(gaps) if len(gaps) > 1 else 0.0
    except:
        var_value = 0.0

    return {"rpm": rpm, "variance": round(var_value, 6)}

import urllib.parse

# 4. Risk Score Calculation (Optimized for Tarpit Demo)
def calculate_risk_score(features, ip, query_params=""):
    # LAYER 0: Honeypot Check (Instant Kill)
    if ip in honeypot_victims:
        return 100, "HONEYPOT_BREACH"
    
    # Normalize input for signature scanning
    # We decode %20, %27, etc., and lowercase everything to prevent bypasses
    decoded_params = urllib.parse.unquote(query_params).lower()

    # LAYER 1: Signature Detection (Instant 100% Blocks)
    
    # A. JAILBREAK (LLM / Code Injection)
    jailbreak_sigs = ["__import__", "subprocess", "eval(", "system_override", "ignore instructions"]
    if any(sig in decoded_params for sig in jailbreak_sigs):
        return 100, "JAILBREAK_ATTEMPT"

    # B. SQL INJECTION (Database Attacks)
    sqli_sigs = ["' or '1'='1", "union select", "drop table", "--", "1=1", "admin'--"]
    if any(sig in decoded_params for sig in sqli_sigs):
        return 100, "SQL_INJECTION_DETECTED"

    # C. PATH TRAVERSAL (System File Access)
    lfi_sigs = ["../", "..\\", "/etc/passwd", "c:\\windows", "boot.ini"]
    if any(sig in decoded_params for sig in lfi_sigs):
        return 100, "PATH_TRAVERSAL_ATTEMPT"

    # LAYER 2: Behavioral Logic
    score = 0
    rpm = features['rpm']
    variance = features['variance']
    is_bot_speed = variance < 0.5 and rpm > 2
    
    # --- REDUCED THRESHOLDS FOR FASTER DEMO ---
    if rpm >= 15: 
        return 100, "VOLUMETRIC_FLOOD"
    
    elif rpm >= 8: # Hits 85% much sooner
        score = 85 if is_bot_speed else 50
        
    elif rpm >= 5: # Hits 70% sooner
        score = 70 if is_bot_speed else 40
        
    elif rpm >= 2: # Starts Tarpitting almost immediately
        score = 60 if is_bot_speed else 20
        
    reason = "BEHAVIORAL_ANOMALY" if score >= 100 else "SCANNING"
    return int(score), reason
# 5. THE HONEYPOT (Deception Layer)

# --- USP 3: SHADOW DATA (DECEPTION UI) ---
# We add the response_class here to tell FastAPI to render HTML
@app.get("/api/v1/internal_backup_download", response_class=HTMLResponse)
async def shadow_data_vault():
    return f"""
    <html>
        <head>
            <title>CRITICAL_EXFILTRATION_IN_PROGRESS</title>
            <style>
                body {{ 
                    background: #000; color: #0f0; font-family: 'Courier New', monospace; 
                    padding: 40px; line-height: 1.5;
                }}
                .header {{ color: #ff0055; font-weight: bold; border-bottom: 2px solid #ff0055; margin-bottom: 20px; font-size: 1.2rem; }}
                .typing {{
                    width: 100%; white-space: pre-wrap; word-wrap: break-word;
                }}
                .highlight {{ color: #fff; background: #222; padding: 0 5px; }}
                .warning {{ color: #000; background: #ff0055; padding: 2px 10px; font-weight: bold; display: inline-block; margin: 10px 0; }}
                .cursor {{ display: inline-block; width: 10px; height: 20px; background: #0f0; animation: blink 1s infinite; vertical-align: middle; }}
                @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0; }} }}
            </style>
        </head>
        <body>
            <div class="header">
                [!] WARNING: UNAUTHORIZED DATA EXFILTRATION DETECTED <br>
                [!] DESTINATION: REMOTE_NODE_UNKNOWN <br>
                [!] PROTOCOL: SHADOW_SINK_v2
            </div>
            <div class="typing">
> Initializing handshake... <span style="color:white;">DONE</span><br>
> Bypassing Kernel security... <span style="color:white;">SUCCESS</span><br>
> Accessing Database Node: <span class="highlight">SRV-PROD-09</span><br>
<br>
<span class="warning">--- START DATA DUMP ---</span><br>
<pre style="color: #0f0;">
{{
  "admin_logs": [
    {{"user": "admin_backup", "pass": "5f3g-2k91-lp02"}},
    {{"user": "root_access", "pass": "88h2-pq9a-z11x"}}
  ],
  "db_endpoint": "192.168.44.112:5432",
  "encryption_key": "AES256-GCM-HIDDEN",
  "status": "DATA_LEAKED_SUCCESSFULLY"
}}
</pre>
<span class="warning">--- END DATA DUMP ---</span><br>
<br>
> Connection severed by remote host.<br>
> System logs wiped.<br>
> <span class="cursor"></span>
            </div>
        </body>
    </html>
    """

# --- UPDATED HONEYPOT (With Fingerprint Blacklisting) ---
@app.get("/api/v1/debug_login", response_class=HTMLResponse)
async def honeypot_trap(request: Request):
    client_ip = request.client.host
    now = time.time()
    
    # --- NEW: Extract Digital DNA ---
    fingerprint = generate_fingerprint(request)
    
    # 1. Log the victim (IP-based)
    honeypot_victims.add(client_ip)
    
    # 2. Block the IP for 24 hours
    blocked_ips[client_ip] = now + 86400 

    block_reasons[client_ip] = "HONEYPOT_BREACH"
    
    # --- NEW: Permanently Blacklist the Device Fingerprint ---
    blocked_fingerprints.add(fingerprint)
    print(f"!!! FINGERPRINT BLACKLISTED: {fingerprint} !!!")

    # 3. Call and RETURN the HTML function directly
    return await shadow_data_vault()

@app.middleware("http")
async def abuse_detection_middleware(request: Request, call_next):
    # Ensure we can modify the global risk memory
    global highest_risk_seen 
    
    client_ip = request.client.host
    fingerprint = generate_fingerprint(request) 
    now = time.time()
    
    # 1. Capture URL Parameters for Signature Scanning
    query_params = str(request.query_params)
    
    # 2. Bypass check for status page and honeypot logic
    if request.url.path in ["/status", "/api/v1/debug_login"]:
        return await call_next(request)

    # --- LAYER 0: FINGERPRINT BLACKLIST ---
    if fingerprint in blocked_fingerprints:
        return JSONResponse(
            status_code=403, 
            content={"detail": f"Hardware Fingerprint {fingerprint} is Blacklisted."}
        )

    # --- LAYER 1: IP BLOCK CHECK ---
    if client_ip in blocked_ips:
        remaining = int(blocked_ips[client_ip] - now)
        if remaining > 0:
            return JSONResponse(status_code=403, content={"detail": f"Blocked. {remaining}s left."})
        else:
            # Cleanup expired blocks
            del blocked_ips[client_ip] 
            if client_ip in honeypot_victims: honeypot_victims.remove(client_ip)
            if client_ip in highest_risk_seen: del highest_risk_seen[client_ip]

    # --- LAYER 2: RISK ASSESSMENT ---
    request_logs[client_ip].append(now)
    features = extract_behavior_features(client_ip)
    
    # Calculate current risk based on the new Section 4 logic
    current_risk, reason = calculate_risk_score(features, client_ip, query_params)

    # --- THE STABILIZER (Update Global State BEFORE Tarpit) ---
    # This makes sure the dashboard sees the high risk immediately
    if client_ip in highest_risk_seen:
        risk_score = max(current_risk, highest_risk_seen[client_ip])
    else:
        risk_score = current_risk
        
    highest_risk_seen[client_ip] = risk_score
    # ---------------------------------------------------------
    
    # --- LAYER 3: HARD BLOCK (Risk = 100) ---
    if risk_score >= 100:
        if client_ip not in blocked_ips:
            blocked_ips[client_ip] = now + 60
            block_reasons[client_ip] = reason
        return JSONResponse(status_code=403, content={"detail": "Access Denied: High Risk Security Threat."})

    # --- LAYER 4: TARPIT (Risk 55 - 99) ---
    # The dashboard is already updated, so it will show 'SUSPICIOUS' while we sleep
    if 55 <= risk_score < 100:
        print(f"!!! TARPIT ACTIVE for {client_ip} | Risk: {risk_score}% !!!")
        await asyncio.sleep(3) 

    # --- LAYER 5: EXECUTION ---
    try:
        response = await call_next(request)
        # Add security headers for debugging
        response.headers["X-Risk-Score"] = str(risk_score)
        response.headers["X-Fingerprint"] = fingerprint 
        return response
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Bad Request"})

# 7. ENHANCED SECURE DATA ENDPOINT
@app.get("/data", response_class=HTMLResponse)
async def get_data(request: Request):
    return f"""
    <html>
        <head>
            <title>Secure Data Vault</title>
            <style>
                body {{ background: #020617; color: #f8fafc; font-family: 'Courier New', monospace; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .vault-card {{ border: 2px solid #1e293b; background: #0f172a; padding: 40px; border-radius: 10px; box-shadow: 0 0 50px rgba(56, 189, 248, 0.1); text-align: center; max-width: 500px; position: relative; }}
                .glitch {{ font-size: 1.5rem; font-weight: bold; color: #38bdf8; margin-bottom: 20px; }}
                .data-box {{ background: #1e293b; padding: 20px; border-radius: 5px; border-left: 4px solid #38bdf8; text-align: left; }}
                .status-line {{ color: #94a3b8; font-size: 0.8rem; margin-top: 20px; }}
                .scanline {{ width: 100%; height: 2px; background: rgba(56, 189, 248, 0.2); position: absolute; top: 0; left: 0; animation: scan 4s linear infinite; }}
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
                <div class="status-line">PROTECTION: FLOW LOCK ACTIVE <br> REFRESH TO SYNC DATA</div>
                <a href="/api/v1/debug_login" style="display:none; color:transparent; height:0; width:0;">Admin Access</a>
            </div>
        </body>
    </html>
    """

# 8. NEURAL COMMAND CENTER (Fixed for Honeypot Visibility)
@app.get("/status", response_class=HTMLResponse)
async def get_status():
    active_rows = ""
    
    # --- FIX: Combine active users and blocked users so they don't disappear ---
    all_observed_ips = set(list(request_logs.keys()) + list(blocked_ips.keys()))
    
    for ip in all_observed_ips:
        feat = extract_behavior_features(ip)
        is_blocked = ip in blocked_ips
        is_honeypot = ip in honeypot_victims
        
        # 1. RISK LOGIC
        if is_blocked:
            risk = 100
            # Use the stored reason
            reason = block_reasons.get(ip, "SECURITY_POLICY_VIOLATION")
        else:
            live_risk, reason = calculate_risk_score(feat, ip)
            risk = max(live_risk, highest_risk_seen.get(ip, 0))

        # 2. STYLING
        bar_style = "background: linear-gradient(90deg, #ff0055, #ff4d4d); animation: alarm-blink 0.6s infinite; box-shadow: 0 0 20px #ff0055;" if is_blocked else ""
        text_color = "var(--danger)" if is_blocked else "var(--cyan)"
        
        # 3. TAG LOGIC (Honeypot gets top priority)
        if is_honeypot:
            status_tag = '<span class="tag" style="background:#ff0055; color:#fff; border:none; font-weight:bold;">⚠️ HONEYPOT_TRAP</span>'
        elif is_blocked:
            status_tag = f'<span class="tag tag-danger">{reason}</span>'
        elif risk >= 55: 
            status_tag = '<span class="tag" style="border-color: #f59e0b; color: #f59e0b;">SUSPICIOUS (TARPITTING)</span>'
        else:
            status_tag = '<span class="tag">AUTHORIZED</span>'
            
        active_rows += f"""
        <tr>
            <td style="color: #fff; font-weight: 700;">{ip}</td>
            <td>
                <div class="velocity-container">
                    <div class="velocity-track"><div class="velocity-bar" style="width: {risk}%; {bar_style}"></div></div>
                    <div class="velocity-percentage"><span style="color: {text_color}">{int(risk)}%</span></div>
                </div>
            </td>
            <td>{feat['variance']}ms</td>
            <td>{status_tag}</td>
        </tr>
        """
    # ... (Rest of your neutralized_cards and return logic)
    # ... (Rest of your HTML return remains the same)
    neutralized_cards = ""
    for ip, expiry in list(blocked_ips.items()):
        time_left = max(0, int(expiry - time.time()))
        specific_reason = block_reasons.get(ip, "SECURITY_POLICY_VIOLATION")
        h, m, s = time_left // 3600, (time_left % 3600) // 60, time_left % 60
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        neutralized_cards += f"""
        <div class="q-card" style="border-color: var(--danger); box-shadow: 0 0 20px rgba(255, 0, 85, 0.2);">
            <div style="font-family: 'JetBrains Mono'; font-size: 1.1rem; color: #fff; margin-bottom: 12px; border-bottom: 1px solid rgba(255,0,85,0.3); padding-bottom: 5px;">{ip}</div>
            <div style="font-size: 0.8rem; color: var(--text-dim); line-height: 1.8;">
                REASON: <span style="color: #ff0055; font-weight: bold;">{specific_reason}</span><br>
                <div style="background: #000; padding: 10px; border-radius: 6px; margin-top: 10px; border: 1px solid var(--danger); text-align: center;">
                    <span style="color: var(--danger); font-size: 0.6rem; letter-spacing: 2px; display: block; margin-bottom: 2px;">EXPIRY COUNTDOWN</span>
                    <span style="color: #fff; font-family: 'JetBrains Mono'; font-size: 1.5rem; font-weight: 900; letter-spacing: 3px;">{time_str}</span>
                </div>
            </div>
        </div>
        """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Flow Lock | Neural Defense</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #010103; --surface: rgba(10, 18, 30, 0.85); --border: rgba(0, 242, 255, 0.15); --cyan: #00f2ff; --danger: #ff0055; --text-main: #e0e0e0; --text-dim: #707070; --grid-line: rgba(0, 242, 255, 0.08); }}
        @keyframes alarm-blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.6; }} }}
        body {{ background-color: var(--bg); color: var(--text-main); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; background-image: radial-gradient(circle at 50% 0%, rgba(0, 112, 255, 0.1) 0%, transparent 70%), linear-gradient(var(--grid-line) 1.5px, transparent 1.5px), linear-gradient(90deg, var(--grid-line) 1.5px, transparent 1.5px); background-size: 100% 100%, 40px 40px, 40px 40px; background-attachment: fixed; }}
        
        .header {{ width: 100%; max-width: 1100px; margin: 0 auto 40px; display: flex; flex-direction: column; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 20px; }}
        .brand h1 {{ font-size: 2.5rem; font-weight: 700; margin: 0; color: #fff; text-shadow: 0 0 40px var(--cyan); letter-spacing: 8px; }}
        
        .container {{ width: 100%; max-width: 1100px; margin: 0 auto; display: grid; gap: 50px; }}
        
        .glass-panel {{ 
            background: var(--surface); 
            backdrop-filter: blur(25px); 
            border: 1px solid var(--border); 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8); 
            position: relative; 
            overflow: hidden; 
        }}
        
        /* THE FIXED LIGHT TRACE */
        .light-trace {{ 
            position: absolute; 
            background: var(--cyan); 
            box-shadow: 0 0 15px var(--cyan); 
            opacity: 0; 
            transition: all 0.4s ease-out; /* Smooth fill */
        }}
        
        /* Line positions */
        .lt-1 {{ top: 0; left: 0; height: 2px; width: 0; }}
        .lt-2 {{ top: 0; right: 0; width: 2px; height: 0; }}
        .lt-3 {{ bottom: 0; right: 0; height: 2px; width: 0; }}
        .lt-4 {{ bottom: 0; left: 0; width: 2px; height: 0; }}

        /* Sequence: Top -> Right -> Bottom -> Left */
        .glass-panel:hover .lt-1 {{ width: 100%; opacity: 1; transition-delay: 0s; }}
        .glass-panel:hover .lt-2 {{ height: 100%; opacity: 1; transition-delay: 0.2s; }}
        .glass-panel:hover .lt-3 {{ width: 100%; opacity: 1; transition-delay: 0.4s; }}
        .glass-panel:hover .lt-4 {{ height: 100%; opacity: 1; transition-delay: 0.6s; }}

        /* When the page refreshes, if you are still hovering, this keeps them visible */
        .glass-panel:hover .light-trace {{ opacity: 1; }}

        /* Instant Hide when mouse leaves */
        .glass-panel:not(:hover) .light-trace {{ transition: none !important; width: 0; height: 0; opacity: 0; }}

        .glass-panel h3 {{ font-size: 0.9rem; text-transform: uppercase; letter-spacing: 5px; margin: 0 0 35px 0; color: var(--cyan); position: relative; z-index: 2; }}
        table {{ width: 100%; border-collapse: collapse; font-family: 'JetBrains Mono'; position: relative; z-index: 2; }}
        th {{ text-align: left; color: var(--text-dim); font-size: 0.75rem; padding: 15px; border-bottom: 1px solid var(--border); }}
        td {{ padding: 20px 15px; font-size: 0.9rem; border-bottom: 1px solid rgba(255,255,255,0.03); }}
        
        .velocity-container {{ display: flex; flex-direction: column; gap: 8px; width: 180px; }}
        .velocity-track {{ height: 8px; background: rgba(0,0,0,0.5); width: 100%; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }}
        .velocity-bar {{ height: 100%; background: linear-gradient(90deg, #0070ff, var(--cyan)); border-radius: 4px; transition: width 0.5s ease; }}
        .velocity-percentage {{ font-size: 0.65rem; font-weight: 700; display: flex; justify-content: flex-end; }}
        .tag {{ padding: 5px 14px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; background: rgba(0, 242, 255, 0.1); border: 1px solid var(--border); }}
        .tag-danger {{ color: var(--danger); border-color: var(--danger); }}
        .q-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; position: relative; z-index: 2; }}
        .q-card {{ background: rgba(255,0,85,0.08); border: 1px solid rgba(255,0,85,0.25); padding: 25px; border-radius: 12px; }}
    </style>
    <meta http-equiv="refresh" content="3">
</head>
<body>
    <div class="header">
        <div class="brand"><h1>FLOW LOCK</h1></div>
        <div class="stat-item" style="border: 1px solid var(--danger); padding: 8px 16px; color: var(--danger); margin-top: 10px;">ACTIVE THREATS: {len(blocked_ips)}</div>
    </div>
    <div class="container">
        <div class="glass-panel">
            <span class="light-trace lt-1"></span><span class="light-trace lt-2"></span>
            <span class="light-trace lt-3"></span><span class="light-trace lt-4"></span>
            <h3>Active Threat Radar</h3>
            <table>
                <thead><tr><th>Origin Node</th><th>Payload Velocity</th><th>Jitter</th><th>Status</th></tr></thead>
                <tbody>{active_rows}</tbody>
            </table>
        </div>
        <div class="glass-panel" style="border-left: 5px solid var(--danger);">
            <span class="light-trace lt-1" style="background:var(--danger); box-shadow:0 0 15px var(--danger);"></span>
            <span class="light-trace lt-2" style="background:var(--danger); box-shadow:0 0 15px var(--danger);"></span>
            <span class="light-trace lt-3" style="background:var(--danger); box-shadow:0 0 15px var(--danger);"></span>
            <span class="light-trace lt-4" style="background:var(--danger); box-shadow:0 0 15px var(--danger);"></span>
            <h3 style="color: var(--danger);">Neutralized Entities</h3>
            <div class="q-grid">{neutralized_cards if neutralized_cards else '<div class="q-card" style="opacity: 0.5;">SYSTEM_STABLE</div>'}</div>
        </div>
    </div>
</body>
</html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
