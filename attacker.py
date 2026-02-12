import requests
import time

url = "http://127.0.0.1:8000/data"

print("--- STARTING FLOW LOCK ATTACK SIMULATION ---")
print(f"Targeting: {url}")
print("Note: Using 1s Timeout to bypass Tarpitting and force a 100% block.")
print("-" * 50)

for i in range(1, 31):
    try:
        # Use timeout=1 so the attacker doesn't wait for the 5-second "Slow Down"
        response = requests.get(url, timeout=5)
        
        risk = response.headers.get("X-Risk-Score", "0")
        
        if response.status_code == 200:
            print(f"Req {i:02} | Status: 200 | Risk: {risk}% | [FAST]")
        
        elif response.status_code == 403:
            print(f"\n" + "!" * 50)
            print(f"Req {i:02} | STATUS: 403 FORBIDDEN - ATTACK NEUTRALIZED")
            print("!" * 50)
            break
            
    except requests.exceptions.Timeout:
        # This is where the magic happens for the demo
        print(f"Req {i:02} | Status: DELAYED | [SERVER TARPITTING DETECTED]")
        # We don't 'break' here, we keep sending requests to hit that 100% block
        continue
        
    except Exception as e:
        print(f"\n[!] Connection Error: {e}")
        break

    time.sleep(0.1)

print("\nSimulation Ended.")
