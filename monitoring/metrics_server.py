from prometheus_client import start_http_server
import os
import time

# ensure project import path (safe guard if someone runs this from other cwd)
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import your metrics module so metrics get registered on import
try:
    import monitoring.metrics as metrics  # noqa: F401
    print("Imported monitoring.metrics — custom metrics registered.")
except Exception as e:
    print("Warning: failed to import monitoring.metrics:", e)

def main(port: int = 8001):
    addr = "0.0.0.0"
    print(f"Starting Prometheus metrics server on {addr}:{port}")
    start_http_server(port, addr=addr)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("metrics server stopped")

if __name__ == '__main__':
    port = int(os.environ.get("METRICS_PORT", "8001"))
    main(port)