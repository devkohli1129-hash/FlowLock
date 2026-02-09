import requests
import time

url = "http://127.0.0.1:8000/data"

print("--- STARTING FLOW LOCK ATTACK SIMULATION ---")
print(f"Targeting: {url}")
print("-" * 50)

for i in range(1, 61):
    try:
        # Send a rapid request
        response = requests.get(url)
        
        # Get security metrics from headers
        risk = response.headers.get("X-Risk-Score", "0")
        rpm = response.headers.get("X-RPM", "0")
        var = response.headers.get("X-Variance", "0")
        
        # Handle the successful requests (Status 200)
        if response.status_code == 200:
            print(f"Req {i:02} | Status: 200 | Risk: {risk}% | RPM: {rpm} | Var: {var}")
        
        # Handle the Blocked requests (Status 403)
        elif response.status_code == 403:
            data = response.json()
            retry_after = response.headers.get("Retry-After", "??")
            
            print(f"\n" + "!" * 50)
            print(f"Req {i:02} | STATUS: 403 FORBIDDEN")
            print(f"REASON: {data.get('detail')}")
            print(f"LOCKOUT DURATION: {retry_after} seconds")
            print("!" * 50)
            
            print("\n[SUCCESS] The behavioral engine successfully quarantined the bot.")
            break
            
        # Tiny delay to maintain "Robotic Consistency" for the demo
        time.sleep(0.01)
            
    except Exception as e:
        print(f"\n[!] Connection Error: {e}")
        break

print("\nSimulation Ended.")