# config/settings.py
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # load .env once, everywhere else just import SETTINGS

def _env(name: str, default: str | None = None) -> str:
    v = os.getenv(name, default)
    if v is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def _redact(v: str, keep: int = 6) -> str:
    if not v: return ""
    return v[:keep] + "…" if len(v) > keep else "…"

@dataclass(frozen=True)
class _Settings:
    # --- LLM / Embeddings (Gemini default) ---
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")             # openai|gemini
    LLM_MODEL: str    = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # embeddings: sentence-transformers local by default with Gemini stack
    EMBEDDINGS_PROVIDER: str = os.getenv("EMBEDDINGS_PROVIDER", "openai")
    EMBEDDING_MODEL: str     = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # --- Search / Fetch ---
    SEARCH_PROVIDER: str = os.getenv("SEARCH_PROVIDER", "serpapi")     # duckduckgo|serpapi
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "20"))
    MAX_PAGES_TO_SCRAPE: int = int(os.getenv("MAX_PAGES_TO_SCRAPE", "20"))
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))
    USER_AGENT: str = os.getenv("USER_AGENT", "ResearchAgent/1.0 (+https://example.com/contact)")

    # --- Vector Store / RAG ---
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")
    CHROMA_COLLECTION_PREFIX: str = os.getenv("CHROMA_COLLECTION_PREFIX", "research_")
    CHUNK_SIZE_TOKENS: int = int(os.getenv("CHUNK_SIZE_TOKENS", "800"))
    CHUNK_OVERLAP_TOKENS: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "120"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "6"))
    MMR_LAMBDA: float = float(os.getenv("MMR_LAMBDA", "0.5"))

    # --- Policy / Limits ---
    RATE_LIMIT_RPS: float = float(os.getenv("RATE_LIMIT_RPS", "2"))
    MAX_TOTAL_CHUNKS: int = int(os.getenv("MAX_TOTAL_CHUNKS", "200"))

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PRINT_CONFIG_ON_STARTUP: bool = os.getenv("PRINT_CONFIG_ON_STARTUP", "true").lower() == "true"

    # --- Secrets (validated in __post_init__) ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")           # for OpenAI
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")         # only if SEARCH_PROVIDER=serpapi
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    def __post_init__(self):
        # Validate LLM key based on provider
        if self.LLM_PROVIDER == "gemini":
            if not self.GOOGLE_API_KEY:
                raise RuntimeError("LLM_PROVIDER=gemini but GOOGLE_API_KEY is missing in .env")
        elif self.LLM_PROVIDER == "openai":
            if not self.OPENAI_API_KEY:
                raise RuntimeError("LLM_PROVIDER=openai but OPENAI_API_KEY is missing in .env")
        elif self.LLM_PROVIDER == "ollama":
            pass  # local; no key required
        elif self.LLM_PROVIDER == "groq":
            if not self.GROQ_API_KEY:
                raise RuntimeError("LLM_PROVIDER=groq but GROQ_API_KEY is missing in .env")
        else:
            raise RuntimeError("LLM_PROVIDER must be 'gemini', 'openai', 'ollama', or 'groq'")

        # Validate search provider
        if self.SEARCH_PROVIDER == "serpapi" and not self.SERPAPI_API_KEY:
            raise RuntimeError("SEARCH_PROVIDER=serpapi but SERPAPI_API_KEY is missing in .env")

        # Ensure vector dir exists
        os.makedirs(self.CHROMA_PERSIST_DIR, exist_ok=True)

    def pretty(self) -> str:
        return (
            "=== Settings ===\n"
            f"LLM_PROVIDER: {self.LLM_PROVIDER}\n"
            f"LLM_MODEL: {self.LLM_MODEL}\n"
            f"EMBEDDINGS_PROVIDER: {self.EMBEDDINGS_PROVIDER}\n"
            f"EMBEDDING_MODEL: {self.EMBEDDING_MODEL}\n"
            f"SEARCH_PROVIDER: {self.SEARCH_PROVIDER}\n"
            f"MAX_SEARCH_RESULTS: {self.MAX_SEARCH_RESULTS} | MAX_PAGES_TO_SCRAPE: {self.MAX_PAGES_TO_SCRAPE}\n"
            f"TIMEOUT: {self.REQUEST_TIMEOUT_SECONDS}s | RETRIES: {self.MAX_RETRIES}\n"
            f"CHROMA_DIR: {self.CHROMA_PERSIST_DIR} | PREFIX: {self.CHROMA_COLLECTION_PREFIX}\n"
            f"CHUNK: {self.CHUNK_SIZE_TOKENS}/{self.CHUNK_OVERLAP_TOKENS} | TOP_K: {self.RETRIEVAL_TOP_K} | MMR: {self.MMR_LAMBDA}\n"
            f"RATE_LIMIT_RPS: {self.RATE_LIMIT_RPS} | MAX_TOTAL_CHUNKS: {self.MAX_TOTAL_CHUNKS}\n"
            f"LOG_LEVEL: {self.LOG_LEVEL}\n"

            f"SERPAPI_API_KEY: {_redact(self.SERPAPI_API_KEY)}\n"
            f"GROQ_API_KEY: {_redact(self.GROQ_API_KEY)} | "

        )

SETTINGS = _Settings()

# Optional: print a quick summary on import (no secrets leaked)
if SETTINGS.PRINT_CONFIG_ON_STARTUP:
    print(SETTINGS.pretty())
