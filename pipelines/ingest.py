# pipelines/ingest.py
from __future__ import annotations

import logging
from typing import Dict, List

from config.settings import SETTINGS
from tools.search_web import search_web
from tools.fetch_page import fetch_page
from tools.extract_readable_text import extract_readable_text
from tools.split_chunks import split_chunks
from tools.embed_chunks import embed_chunks
from tools.upsert_vectors import upsert_vectors
from utils.common import slugify, now_iso

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))

_MIN_TEXT_LEN = 1200  # drop very short pages to keep quality high

def _quality_filter(doc: Dict[str, str]) -> bool:
    return len((doc.get("text") or "")) >= _MIN_TEXT_LEN

def ingest_topic(query: str, namespace: str | None = None) -> Dict[str, object]:
    """
    Full ingestion pipeline for a topic. Idempotent wrt chunk IDs.
    Output shape:
      {
        "namespace": str,
        "indexed_pages": int,
        "indexed_chunks": int,
        "skipped_pages": int,
        "sources": List[{title,url,text_len}]
      }
    """
    ns = namespace or slugify(query)
    want = SETTINGS.MAX_PAGES_TO_SCRAPE

    # 1) Search
    raw = search_web(query, k=want * 2)  # oversample a bit; we’ll filter by quality
    if not raw:
        return {"namespace": ns, "indexed_pages": 0, "indexed_chunks": 0, "skipped_pages": 0, "sources": []}
    hits = raw[:want]

    # 2) Fetch + extract (quality gate)
    docs: List[Dict[str, str]] = []
    skipped = 0
    for item in hits:
        r = fetch_page(item["url"])
        if r["status"] != 200 or not r["html"]:
            skipped += 1
            continue
        doc = extract_readable_text(r["html"], r["url"])
        if not _quality_filter(doc):
            skipped += 1
            continue
        docs.append(doc)

    if not docs:
        return {"namespace": ns, "indexed_pages": 0, "indexed_chunks": 0, "skipped_pages": skipped, "sources": []}

    # 3) Chunk
    chunks = []
    for d in docs:
        chunks.extend(split_chunks(d["text"], url=d["url"], title=d["title"]))

    if not chunks:
        return {"namespace": ns, "indexed_pages": len(docs), "indexed_chunks": 0, "skipped_pages": skipped, "sources": []}

    # Cap to control spend
    if len(chunks) > SETTINGS.MAX_TOTAL_CHUNKS:
        chunks = chunks[:SETTINGS.MAX_TOTAL_CHUNKS]

    # 4) Embed
    vecs = embed_chunks(chunks, model=SETTINGS.EMBEDDING_MODEL, batch_size=64)
    by_id = {v["chunk_id"]: v["embedding"] for v in vecs}

    # 5) Upsert
    ts = now_iso()
    records = []
    for ch in chunks:
        emb = by_id.get(ch["chunk_id"])
        if emb is None:
            continue
        records.append({
            "id": ch["chunk_id"],
            "embedding": emb,
            "document": ch["text"],
            "metadata": {
                "url": ch["url"],
                "title": ch["title"],
                "order": ch["order"],
                "added_at": ts,
            }
        })

    up = upsert_vectors(ns, records)

    return {
        "namespace": ns,
        "indexed_pages": len(docs),
        "indexed_chunks": up["count_upserted"],
        "skipped_pages": skipped,
        "sources": [{"title": d["title"], "url": d["url"], "text_len": len(d["text"])} for d in docs],
    }

if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))
    print(ingest_topic("multimodal LLM survey 2024 2025"))
