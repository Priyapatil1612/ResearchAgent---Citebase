# agent/agent_react.py
from __future__ import annotations

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import SETTINGS
from pipelines.ingest import ingest_topic
from pipelines.qa import answer_question
from utils.common import slugify

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _namespace_exists(ns: str) -> bool:
    client = chromadb.PersistentClient(
        path=SETTINGS.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(allow_reset=False),
    )
    try:
        client.get_collection(name=f"{SETTINGS.CHROMA_COLLECTION_PREFIX}{ns}")
        return True
    except Exception:
        return False


class ResearchAgent:
    """
    Minimal ReAct-style research agent:
      - If namespace doesn't exist (new topic) or force==True → INGEST pipeline
      - Else → QA pipeline over existing index
    """

    def research(self, topic: str, namespace: Optional[str] = None, force: bool = False) -> dict:
        ns = namespace or slugify(topic)
        trace = []

        # Thought
        trace.append(f"Thought: Need to decide whether to ingest new knowledge for topic '{topic}'.")
        # Action
        need_ingest = force or (not _namespace_exists(ns))
        if need_ingest:
            trace.append(f"Action: ingest_topic(query='{topic}', namespace='{ns}')")
            obs = ingest_topic(topic, namespace=ns)
            trace.append(f"Observation: indexed_pages={obs['indexed_pages']}, indexed_chunks={obs['indexed_chunks']}, skipped_pages={obs['skipped_pages']}")
            result = {
                "namespace": ns,
                "did_ingest": True,
                "ingest_summary": obs,
                "trace": trace,
            }
        else:
            trace.append(f"Observation: Namespace '{ns}' already exists. Skipping ingest.")
            result = {
                "namespace": ns,
                "did_ingest": False,
                "trace": trace,
            }

        return result

    def ask(self, question: str, namespace: str, top_k: Optional[int] = None) -> dict:
        trace = []
        # Thought
        trace.append(f"Thought: Answer a question using only indexed context in namespace '{namespace}'.")
        # Action
        trace.append(f"Action: answer_question(question=?, namespace='{namespace}', top_k={top_k or SETTINGS.RETRIEVAL_TOP_K})")
        obs = answer_question(question, namespace, top_k=top_k or SETTINGS.RETRIEVAL_TOP_K)
        # Observation
        used = len(obs.get("citations", []))
        trace.append(f"Observation: got content with {used} citation(s).")

        return {
            "namespace": namespace,
            "question": question,
            "content": obs["content"],
            "citations": obs["citations"],
            "trace": trace,
        }
