# tools/split_chunks.py
from __future__ import annotations

import hashlib
import logging
from typing import Dict, List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _hash_id(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def split_chunks(
    doc_text: str,
    url: str,
    title: str,
    chunk_size_tokens: int | None = None,
    overlap_tokens: int | None = None,
) -> List[Dict[str, object]]:
    """
    LangChain-based, token-aware splitter with overlap.

    Inputs:
        doc_text: full cleaned article text
        url:      source URL (for metadata)
        title:    source title (for metadata)
        chunk_size_tokens: defaults to SETTINGS.CHUNK_SIZE_TOKENS
        overlap_tokens:    defaults to SETTINGS.CHUNK_OVERLAP_TOKENS

    Output:
        List of dicts:
        {
          "chunk_id": str,   # stable hash of url|order|first_40_chars
          "text": str,
          "url": str,
          "title": str,
          "order": int
        }
    """
    if not doc_text:
        return []

    chunk_size_tokens = chunk_size_tokens or SETTINGS.CHUNK_SIZE_TOKENS
    overlap_tokens = overlap_tokens or SETTINGS.CHUNK_OVERLAP_TOKENS

    splitter = RecursiveCharacterTextSplitter(
        # OpenAI-compatible tokenizer
        # encoding_name="cl100k_base",
        chunk_size=chunk_size_tokens,
        chunk_overlap=overlap_tokens,
        # Optional: try to keep boundaries natural
        # (Recursive splitter uses a hierarchy of separators internally)
    )

    pieces: List[str] = splitter.split_text(doc_text)
    out: List[Dict[str, object]] = []

    for order, text in enumerate(pieces):
        text = (text or "").strip()
        if not text:
            continue
        prefix = text[:40].replace("\n", " ")
        chunk_id = _hash_id(f"{url}|{order}|{prefix}")
        out.append({
            "chunk_id": chunk_id,
            "text": text,
            "url": url,
            "title": title or "",
            "order": order,
        })

    return out


if __name__ == "__main__":
    logging.basicConfig(level=getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))
    sample = ("Multimodal models combine text and images. " * 80) + \
             ("They often use contrastive pretraining and instruction tuning. " * 40)
    chunks = split_chunks(sample, url="https://example.com/demo", title="Demo")
    print(f"chunks: {len(chunks)} (size={SETTINGS.CHUNK_SIZE_TOKENS}, overlap={SETTINGS.CHUNK_OVERLAP_TOKENS})")
    for c in chunks[:2]:
        print(f"- order={c['order']} id={c['chunk_id'][:8]} text_preview={c['text'][:80]!r}")
