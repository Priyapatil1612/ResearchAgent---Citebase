# tools/synthesize_answer.py
from __future__ import annotations

import logging
from typing import Dict, List

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _format_contexts(ctxs: List[Dict[str, object]]) -> str:
    lines = []
    for i, c in enumerate(ctxs, 1):
        title = (c.get("title") or "").strip()
        url = (c.get("url") or "").strip()
        text = (c.get("text") or "").strip()
        lines.append(f"[{i}] {title}\nURL: {url}\n---\n{text}\n")
    return "\n".join(lines)


def _dedupe_urls(ctxs: List[Dict[str, object]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for c in ctxs:
        u = (c.get("url") or "").strip()
        t = (c.get("title") or "").strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append({"url": u, "title": t})
    return out


def synthesize_answer(
    question: str,
    contexts: List[Dict[str, object]],
    style: str = "concise",
    temperature: float = 0.2,
) -> Dict[str, object]:
    """
    Inputs:
      - question: user question
      - contexts: List[{text,url,title,score}] from retrieve_context()
      - style: "concise" | "detailed"
      - temperature: generation temperature

    Output:
      { "content": str, "citations": List[{url,title}] }
    """
    if not contexts:
        return {
            "content": "I don’t have any supporting context yet. Try ingesting more sources for this topic.",
            "citations": [],
        }

    sys_prompt = (
        "You are a careful research assistant. Use ONLY the provided context blocks to answer.\n"
        "Cite sources by listing the URLs you relied on. If info is insufficient, say so explicitly.\n"
        "Structure the reply as:\n"
        "• A short paragraph answer.\n"
        "• 3-6 bullet points with key facts.\n"
        "• A 'Sources:' section with URLs (deduplicated).\n"
    )

    ctx_block = _format_contexts(contexts)
    # (Optional) Trim to fit local LLM context limits
    if len(ctx_block) > 12000:
        ctx_block = ctx_block[:12000]

    user_prompt = (
        f"Question: {question}\n\n"
        f"Context blocks (use these as your only sources; cite their URLs):\n"
        f"{ctx_block}\n\n"
        f"Style: {style}"
    )

    provider = SETTINGS.LLM_PROVIDER.lower().strip()
    content = ""

    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=SETTINGS.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=SETTINGS.LLM_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = resp.choices[0].message.content.strip()

    elif provider == "ollama":
        import requests
        payload = {
            "model": SETTINGS.LLM_MODEL,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": float(temperature)},
        }
        r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=180)
        if r.status_code == 404:
            # fallback to /api/generate
            prompt = f"{sys_prompt}\n\n{user_prompt}"
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": SETTINGS.LLM_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": float(temperature)}},
                timeout=180,
            )
        r.raise_for_status()
        js = r.json()
        msg = js.get("message") or {}
        content = (msg.get("content") or js.get("response") or "").strip()

    elif provider == "groq":
        from groq import Groq
        client = Groq(api_key=SETTINGS.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=SETTINGS.LLM_MODEL,  # e.g., "llama-3.1-8b-instant"
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        content = resp.choices[0].message.content.strip()

    else:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {SETTINGS.LLM_PROVIDER}")

    return {
        "content": content,
        "citations": _dedupe_urls(contexts),
    }


if __name__ == "__main__":
    fake_ctx = [{
        "title": "Example Source",
        "url": "https://example.com/a",
        "text": "This is some context about a topic, long enough to be meaningful.",
        "score": 0.9,
    }]
    out = synthesize_answer("summarize the topic", fake_ctx)
    print(out["content"])
    print("Citations:", [c["url"] for c in out["citations"]])
