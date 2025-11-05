# utils/common.py
from __future__ import annotations
import re
import unicodedata
from datetime import datetime, timezone

def slugify(text: str, maxlen: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:maxlen] or "topic"

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
