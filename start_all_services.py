"""
start_all_services.py
Convenience launcher to run all 3 IBM Capstone microservices concurrently:
- Port 8000: Data Science Inference Engine (Kelly Kasina)
- Port 8001: Business Intelligence Investigation Layer
- Port 8002: Product Development Curtailment & Orchestration Portal
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def run_services():
    print("=" * 70)
    print("🚀 STARTING ALL 3 IBM CAPSTONE SERVICES")
    print("=" * 70)
    print("• Tier 1 (Port 8000): Data Science Inference API       -> http://127.0.0.1:8000/docs")
    print("• Tier 2 (Port 8001): BI Investigation Layer          -> http://127.0.0.1:8001/docs")
    print("• Tier 3 (Port 8002): Product Development Portal & UI -> http://127.0.0.1:8002/dashboard")
    print("=" * 70)

    processes = []
    try:
        # Start Data Science API (Port 8000)
        p1 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
            cwd=str(ROOT_DIR)
        )
        processes.append(p1)

        # Start BI API (Port 8001)
        p2 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8001"],
            cwd=str(ROOT_DIR / "bi")
        )
        processes.append(p2)

        # Start Product API (Port 8002)
        p3 = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--port", "8002"],
            cwd=str(ROOT_DIR / "product")
        )
        processes.append(p3)

        print("\nAll 3 services are running! Press Ctrl+C in this terminal to stop all.\n")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down all services gracefully...")
        for p in processes:
            p.terminate()
        print("Done.")


if __name__ == "__main__":
    run_services()
