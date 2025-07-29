import time
import requests
import sys

max_attempts = 30
for i in range(max_attempts):
    try:
        response = requests.get('http://127.0.0.1:8501/_stcore/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Dashboard is healthy after {i+1} attempts")
            sys.exit(0)
    except:
        pass
    time.sleep(1)
    
print("❌ Dashboard failed health check")
sys.exit(1)
