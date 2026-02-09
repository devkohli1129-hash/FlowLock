import requests
import time
import random

for i in range(5):
    response = requests.get("http://127.0.0.1:8000/data")
    print(f"Request {i}: Status {response.status_code}, Risk: {response.headers.get('X-Risk-Score')}")
    time.sleep(random.uniform(1, 3)) # Random delays = HUMAN