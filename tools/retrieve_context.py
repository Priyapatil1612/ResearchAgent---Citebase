# tools/retrieve_context.py
from __future__ import annotations

import logging
from typing import Dict, List

import chromadb
from chromadb.config import Settings as ChromaSettings

try:
    from openai import OpenAI
except ImportError:
    # Fallback for older versions - create a mock class
    class OpenAI:
        def __init__(self, *args, **kwargs):
            pass
        
        def embeddings(self, *args, **kwargs):
            # Return mock embeddings
            return {"data": [{"embedding": [0.0] * 1536}]}

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _collection_name(namespace: str) -> str:
    return f"{SETTINGS.CHROMA_COLLECTION_PREFIX}{namespace}".strip()



def _embed_query(text: str) -> List[float]:
    text = (text or "").strip()
    if not text:
        return []

    if SETTINGS.EMBEDDINGS_PROVIDER.lower() == "sentencetransformers":
        from sentence_transformers import SentenceTransformer
        st = SentenceTransformer(SETTINGS.EMBEDDING_MODEL)
        # normalize=True so cosine distance behaves well
        return st.encode([text], normalize_embeddings=True)[0].tolist()

    # OpenAI path
    from openai import OpenAI
    client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
    resp = client.embeddings.create(model=SETTINGS.EMBEDDING_MODEL, input=[text])
    return resp.data[0].embedding


def retrieve_context(
    namespace: str,
    question: str,
    top_k: int | None = None,
) -> List[Dict[str, object]]:
    """
    Inputs:
      - namespace: collection suffix for this topic
      - question:  user question to embed and search with
      - top_k:     how many chunks to return (default = SETTINGS.RETRIEVAL_TOP_K)

    Output:
      - List[{ "text": str, "url": str, "title": str, "score": float }]
        (higher score ≈ more similar)
    """
    if not namespace or not question:
        return []

    top_k = top_k or SETTINGS.RETRIEVAL_TOP_K
    col_name = _collection_name(namespace)

    client = chromadb.PersistentClient(
        path=SETTINGS.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(allow_reset=False),
    )

    try:
        collection = client.get_collection(name=col_name)
    except Exception:
        logger.warning(f"retrieve_context: collection '{col_name}' not found")
        return []

    qvec = _embed_query(question)
    if not qvec:
        return []

    res = collection.query(
        query_embeddings=[qvec],
        n_results=max(1, int(top_k)),
        include=["distances", "documents", "metadatas"],
    )

    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]

    out: List[Dict[str, object]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        # convert distance → “similarity-ish” score
        try:
            sim = 1.0 - float(dist)
        except Exception:
            sim = 0.0
        out.append({
            "text": doc or "",
            "url": (meta or {}).get("url", ""),
            "title": (meta or {}).get("title", ""),
            "score": sim,
        })

    out.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return out


if __name__ == "__main__":
    ns = "demo_ns"  # set to your actual namespace
    results = retrieve_context(ns, "what are the key takeaways?", top_k=3)
    print(f"hits: {len(results)}")
    for r in results:
        print(f"- {r['title']} | {r['url']} | score={r['score']:.4f}")
