# pipelines/qa.py
from __future__ import annotations

import logging
from typing import Dict, List

from config.settings import SETTINGS
from tools.retrieve_context import retrieve_context
from tools.synthesize_answer import synthesize_answer

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))

def answer_question(question: str, namespace: str, top_k: int | None = None) -> Dict[str, object]:
    """
    Retrieve top-k contexts from Chroma and compose a grounded answer.
    Output:
      { "content": str, "citations": List[{url,title}] }
    """
    k = top_k or SETTINGS.RETRIEVAL_TOP_K
    ctxs = retrieve_context(namespace, question, top_k=k)
    if not ctxs:
        return {
            "content": "I couldn’t find relevant context in this namespace. Try ingesting more sources or re-ingesting with --force.",
            "citations": [],
        }
    return synthesize_answer(question, ctxs, style="concise", temperature=0.2)

if __name__ == "__main__":
    # expects you to have ingested something under this namespace already
    ns = "demo-ns"
    out = answer_question("What are the leading multimodal LLMs?", ns)
    print(out["content"])
    print("\nCitations:", [c["url"] for c in out["citations"]])
