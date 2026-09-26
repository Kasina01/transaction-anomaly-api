"""
start_all_services.py
Convenience launcher to run the IBM Fraud Detection & Curtailment Platform.
By default, launches the Unified Single-URL Gateway on http://127.0.0.1:8000
connecting all 3 tracks (Data Science, BI, and Product Development).
"""

import sys
import subprocess
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent


def run_unified():
    print("=" * 72)
    print("🚀 LAUNCHING UNIFIED FRAUD PLATFORM (SINGLE ENTRYPOINT: PORT 8000)")
    print("=" * 72)
    print("• Central Control Hub:       http://127.0.0.1:8000/")
    print("• Investigator Portal:       http://127.0.0.1:8000/dashboard")
    print("• Unified API Swagger Docs:  http://127.0.0.1:8000/docs")
    print("• Watson Orchestrate Skill:  http://127.0.0.1:8000/orchestrate-skill.json")
    print("=" * 72)
    print("All 3 tracks (Data Science, BI, Product) are unified under this single URL.\n")

    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "gateway:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
            cwd=str(ROOT_DIR)
        )
    except KeyboardInterrupt:
        print("\nGateway stopped.")


if __name__ == "__main__":
    run_unified()
