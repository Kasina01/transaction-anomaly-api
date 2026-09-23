"""
case_search.py

Searches a folder of plain-text case documents (KYC notes, dispute chat logs,
SAR narratives) for files related to a given customer_id, transaction_id, or
device_id. 
"""

import os
from pathlib import Path
from typing import List, Dict

CASES_DIR = Path(__file__).parent / "sample_cases"


def _read_case_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def search_cases(customer_id: str = None, device_id: str = None) -> List[Dict]:
    """
    Search sample_cases/ for any .txt file whose content or filename
    references the given customer_id or device_id.

    Returns a list of dicts: {"case_id": str, "file": str, "content": str}
    """
    if not CASES_DIR.exists():
        return []

    matches = []
    for file_path in sorted(CASES_DIR.glob("*.txt")):
        content = _read_case_file(file_path)

        matched = False
        if customer_id and customer_id.lower() in content.lower():
            matched = True
        if device_id and device_id.lower() in content.lower():
            matched = True
        # also allow matching on filename prefix, e.g. CUST1042_case1.txt
        if customer_id and customer_id.lower() in file_path.stem.lower():
            matched = True

        if matched:
            case_id_line = next(
                (line for line in content.splitlines() if line.startswith("Case ID:")),
                "Case ID: UNKNOWN",
            )
            case_id = case_id_line.replace("Case ID:", "").strip()
            matches.append({
                "case_id": case_id,
                "file": file_path.name,
                "content": content.strip(),
            })

    return matches