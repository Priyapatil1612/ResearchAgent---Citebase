# tools/fetch_page.py
from __future__ import annotations

import logging
import time
from typing import Dict
from urllib.parse import urlparse

import requests

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


def _is_http_url(u: str) -> bool:
    try:
        s = urlparse(u).scheme.lower()
        return s in ("http", "https")
    except Exception:
        return False


def fetch_page(url: str, timeout_sec: int = None) -> Dict[str, object]:
    """
    Download a web page.

    Inputs:
        url: http(s) URL to fetch
        timeout_sec: override request timeout (defaults to SETTINGS.REQUEST_TIMEOUT_SECONDS)

    Output (never raises):
        { "url": str, "html": str, "status": int }
        - html is "" on failure or when content-type isn't HTML.
    """
    if not _is_http_url(url):
        return {"url": url, "html": "", "status": 0}

    timeout = timeout_sec or SETTINGS.REQUEST_TIMEOUT_SECONDS

    headers = {
        "User-Agent": SETTINGS.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    attempt = 0
    backoff = 1.0
    max_attempts = SETTINGS.MAX_RETRIES + 1

    while attempt < max_attempts:
        attempt += 1
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            status = resp.status_code

            if status != 200:
                # Retry on transient server/network issues
                if status in (408, 409, 425, 429, 500, 502, 503, 504) and attempt < max_attempts:
                    logger.warning(f"fetch_page: {status} for {url} — retry {attempt}/{max_attempts-1} in {backoff:.1f}s")
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                # Non-retryable or out of retries
                return {"url": url, "html": "", "status": status}

            # Content-Type check: skip non-HTML (e.g., PDFs)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                logger.info(f"fetch_page: Non-HTML content ({ctype}) for {url}")
                return {"url": url, "html": "", "status": status}

            # Respect encoding if provided; otherwise let requests guess
            resp.encoding = resp.encoding or "utf-8"
            html = resp.text or ""
            return {"url": url, "html": html, "status": status}

        except requests.RequestException as e:
            if attempt < max_attempts:
                logger.warning(f"fetch_page: request error for {url}: {e} — retry in {backoff:.1f}s")
                time.sleep(backoff)
                backoff *= 2
                continue
            return {"url": url, "html": "", "status": 0}

    # Should not reach here
    return {"url": url, "html": "", "status": 0}


if __name__ == "__main__":
    # Simple smoke test
    logging.basicConfig(level=getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))
    test_url = "https://arxiv.org/abs/2408.00123"
    out = fetch_page(test_url)
    print(f"status={out['status']} len(html)={len(out['html'])} url={out['url']}")
