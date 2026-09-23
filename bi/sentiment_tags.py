"""
sentiment_tags.py


Scans case text for simple keyword markers associated with two behavioral
patterns relevant to fraud investigation:
  - distress / coercion language (possible social-engineering victim)
  - mule-ring language (evasiveness, inconsistent answers, rapid forwarding)

"""

from typing import List, Dict

DISTRESS_MARKERS = [
    "forced", "threatened", "urgent", "urgently", "told to send",
    "scared", "pressured", "had to move",
]

MULE_MARKERS = [
    "inconsistent", "evasive", "rapid", "forwarding", "does not recognize",
    "do not recognize", "multiple recipients", "same device", "matches two other",
]


def tag_case_text(text: str) -> Dict[str, List[str]]:
    """
    Returns which distress and mule-ring markers were found in the given
    case text, in the form:
      {"distress_signals": [...], "mule_ring_signals": [...]}
    Empty lists mean no markers of that type were found.
    """
    lowered = text.lower()

    distress_hits = [m for m in DISTRESS_MARKERS if m in lowered]
    mule_hits = [m for m in MULE_MARKERS if m in lowered]

    return {
        "distress_signals": distress_hits,
        "mule_ring_signals": mule_hits,
    }