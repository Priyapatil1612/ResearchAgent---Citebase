# tools/embed_chunks.py
from __future__ import annotations
import logging, time
from typing import Dict, List

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))

_BATCH_SIZE = 64

def _batched(seq: List, n: int):
    for i in range(0, len(seq), n):
        yield i, seq[i:i+n]

def embed_chunks(
    chunks: List[Dict[str, object]],
    model: str | None = None,
    batch_size: int = _BATCH_SIZE,
) -> List[Dict[str, object]]:
    if not chunks:
        return []
    model = model or SETTINGS.EMBEDDING_MODEL

    items = [(c["chunk_id"], (c.get("text") or "").strip()) for c in chunks]
    items = [(cid, txt) for cid, txt in items if txt]
    if not items:
        return []

    outputs: List[Dict[str, object]] = []

    if SETTINGS.EMBEDDINGS_PROVIDER.lower() == "sentencetransformers":
        # ---- Local embeddings path ----
        from sentence_transformers import SentenceTransformer
        st_model = SentenceTransformer(model)
        for _, batch in _batched(items, batch_size):
            ids = [cid for cid, _ in batch]
            texts = [txt for _, txt in batch]
            vecs = st_model.encode(texts, show_progress_bar=False, normalize_embeddings=True).tolist()
            for cid, vec in zip(ids, vecs):
                outputs.append({"chunk_id": cid, "embedding": vec})
        # keep input order
        order_map = {c["chunk_id"]: i for i, c in enumerate(chunks)}
        outputs.sort(key=lambda r: order_map.get(r["chunk_id"], 1_000_000))
        return outputs

    # ---- OpenAI path (unchanged) ----
    from openai import OpenAI, APIError, RateLimitError, APITimeoutError
    client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
    max_attempts = SETTINGS.MAX_RETRIES + 1

    for start_idx, batch in _batched(items, batch_size):
        ids = [cid for cid, _ in batch]
        texts = [txt for _, txt in batch]
        attempt, backoff = 0, 1.0
        while attempt < max_attempts:
            attempt += 1
            try:
                resp = client.embeddings.create(model=model, input=texts)
                vecs = [d.embedding for d in resp.data]
                for cid, vec in zip(ids, vecs):
                    outputs.append({"chunk_id": cid, "embedding": vec})
                break
            except (RateLimitError, APITimeoutError) as e:
                if attempt < max_attempts:
                    logger.warning(f"embed_chunks: rate/timeout on batch {start_idx}: {e} — retry in {backoff:.1f}s")
                    time.sleep(backoff); backoff *= 2
                else:
                    logger.error(f"embed_chunks: failed after retries on batch {start_idx}: {e}")
                    break
            except APIError as e:
                logger.error(f"embed_chunks: APIError on batch {start_idx}: {e}")
                break

    order_map = {c["chunk_id"]: i for i, c in enumerate(chunks)}
    outputs.sort(key=lambda r: order_map.get(r["chunk_id"], 1_000_000))
    return outputs