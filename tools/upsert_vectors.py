# tools/upsert_vectors.py
from __future__ import annotations

import logging
from typing import Dict, List

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _collection_name(namespace: str) -> str:
    return f"{SETTINGS.CHROMA_COLLECTION_PREFIX}{namespace}".strip()


def upsert_vectors(namespace: str, records: List[Dict[str, object]]) -> Dict[str, int]:
    """
    Upsert pre-computed embeddings into a persistent Chroma collection.

    Inputs:
      - namespace: logical topic name (slug/ID)
      - records: list of dicts with keys:
          id:        str            # unique chunk id
          embedding: List[float]    # vector
          document:  str            # chunk text
          metadata:  dict           # MUST contain: url, title, order, added_at (ISO)

    Output:
      - { "count_upserted": int }

    Notes:
      - This tool does NOT compute embeddings; pass pre-embedded records.
      - Collection is persisted under SETTINGS.CHROMA_PERSIST_DIR.
    """
    if not namespace:
        raise ValueError("namespace is required")
    if not records:
        return {"count_upserted": 0}

    col_name = _collection_name(namespace)

    client = chromadb.PersistentClient(
        path=SETTINGS.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(allow_reset=False),
    )

    # We don't attach an embedding function because we supply embeddings ourselves
    collection = client.get_or_create_collection(
        name=col_name,
        metadata={"hnsw:space": "cosine"},  # common default for text embeddings
    )

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for r in records:
        rid = str(r.get("id", "")).strip()
        vec = r.get("embedding")
        doc = (r.get("document") or "").strip()
        meta = r.get("metadata") or {}
        if not rid or not isinstance(vec, list) or not doc:
            # Skip malformed entries quietly
            continue
        ids.append(rid)
        embeddings.append(vec)
        metadatas.append(meta)
        documents.append(doc)

    if not ids:
        return {"count_upserted": 0}

    # Upsert in one call; Chroma handles batched writes internally
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info(f"upsert_vectors: upserted {len(ids)} items into collection '{col_name}'")
    return {"count_upserted": len(ids)}


if __name__ == "__main__":
    # minimal smoke (structure only)
    import time
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ns = "demo_ns"
    recs = [{
        "id": "demo-1",
        "embedding": [0.0, 0.1, 0.2],  # dummy small vec — just to test shape; real use has 1536 dims
        "document": "hello world",
        "metadata": {"url": "https://example.com", "title": "Demo", "order": 0, "added_at": now},
    }]
    out = upsert_vectors(ns, recs)
    print(out)
