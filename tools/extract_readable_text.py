# # tools/extract_readable_text.py
# from __future__ import annotations

# import logging
# import re
# from typing import Dict

# from bs4 import BeautifulSoup
# # top of file
# try:
#     from readability import Document  # preferred path (readability-lxml provides this)
# except Exception:
#     # fallback path for namespace-package collisions (Anaconda/base installs)
#     from readability.readability import Document

# from config.settings import SETTINGS

# logger = logging.getLogger(__name__)
# logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


# def _collapse_ws(s: str) -> str:
#     # Normalize whitespace: replace NBSP, collapse runs, trim blank lines
#     s = s.replace("\u00a0", " ")
#     s = re.sub(r"[ \t]+\n", "\n", s)          # strip trailing spaces
#     s = re.sub(r"\n{3,}", "\n\n", s)          # max 2 consecutive newlines
#     s = re.sub(r"[ \t]{2,}", " ", s)          # collapse spaces
#     return s.strip()


# def _strip_boilerplate(soup: BeautifulSoup) -> None:
#     # Remove obvious non-content blocks
#     for tag in soup(["script", "style", "noscript", "iframe", "canvas", "svg"]):
#         tag.decompose()
#     for sel in ["header", "footer", "nav", "aside", "form"]:
#         for t in soup.select(sel):
#             t.decompose()
#     # Common class/id noise (best-effort; safe to ignore if not present)
#     noisy = [
#         "[class*=cookie]", "[id*=cookie]", "[class*=advert]", "[id*=advert]",
#         "[class*=promo]", "[class*=subscribe]", "[class*=signup]",
#         "[class*=share]", "[class*=social]"
#     ]
#     for sel in noisy:
#         for t in soup.select(sel):
#             t.decompose()


# def extract_readable_text(html: str, url: str) -> Dict[str, str]:
#     """
#     Convert raw HTML into a clean article-like text blob.

#     Inputs:
#         html: raw HTML string
#         url : source URL (for metadata/fallbacks)

#     Output:
#         { "url": str, "title": str, "text": str }
#         - 'text' may be empty if the HTML isn't an article or is too short.
#     """
#     if not html:
#         return {"url": url, "title": "", "text": ""}

#     title = ""
#     main_text = ""

#     try:
#         # 1) Use Readability to find main content
#         doc = Document(html)
#         title = (doc.short_title() or "").strip()
#         readable_html = doc.summary(html_partial=True)
#         soup = BeautifulSoup(readable_html, "lxml")
#         _strip_boilerplate(soup)
#         main_text = _collapse_ws(soup.get_text("\n"))
#     except Exception as e:
#         logger.debug(f"readability failed for {url}: {e}")
#         # Fallback: parse original HTML directly
#         soup_full = BeautifulSoup(html, "lxml")
#         if not title:
#             title_tag = soup_full.find("title")
#             title = (title_tag.get_text(strip=True) if title_tag else "") or title
#         _strip_boilerplate(soup_full)
#         main_text = _collapse_ws(soup_full.get_text("\n"))

#     # Final title fallback from original HTML if empty
#     if not title:
#         soup_full = BeautifulSoup(html, "lxml")
#         t = soup_full.find("title")
#         if t:
#             title = t.get_text(strip=True)

#     # Safety trims
#     if len(main_text) > 0:
#         # remove leading site-name runs if present (very light heuristic)
#         main_text = re.sub(r"^\s*(?:[A-Za-z0-9\-\|: ]{1,80}\n){0,2}", "", main_text)

#     return {"url": url, "title": title or "", "text": main_text or ""}


# if __name__ == "__main__":
#     # Smoke test: pair with your fetcher
#     import logging
#     from tools.fetch_page import fetch_page

#     logging.basicConfig(level=getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))
#     test_url = "https://en.wikipedia.org/wiki/Multimodal_learning"
#     fetched = fetch_page(test_url)
#     out = extract_readable_text(fetched["html"], fetched["url"])
#     print(f"title: {out['title'][:120]}")
#     print(f"text_len: {len(out['text'])}")
#     print(out["text"][:500].replace("\n", " ") + " ...")


# tools/extract_readable_text.py
from __future__ import annotations

import logging
import re
from typing import Dict, Iterable, Optional, Tuple

from bs4 import BeautifulSoup, Tag
from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))


# --------------------------- utilities ---------------------------

def _collapse_ws(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s.strip()


def _strip_boilerplate(soup: BeautifulSoup | Tag) -> None:
    # Nuke obvious non-content
    for t in soup(["script", "style", "noscript", "iframe", "canvas", "svg", "template"]):
        t.decompose()

    # Layout chrome
    for sel in ["header", "footer", "nav", "aside", "form"]:
        for t in soup.select(sel):
            t.decompose()

    # Common site furniture
    noisy = [
        "[class*=cookie]", "[id*=cookie]",
        "[class*=advert]", "[id*=advert]", "[class*=ad-]", "[id*=ad-]",
        "[class*=promo]", "[class*=subscribe]", "[class*=signup]",
        "[class*=share]", "[class*=social]", "[class*=breadcrumb]", "[class*=footer]"
    ]
    for sel in noisy:
        for t in soup.select(sel):
            t.decompose()


def _meta_content(soup: BeautifulSoup, *names: Tuple[str, str]) -> Optional[str]:
    # names: tuples like ("property","og:title") or ("name","twitter:title")
    for attr, val in names:
        m = soup.find("meta", attrs={attr: val})
        if m and m.get("content"):
            return m["content"].strip()
    return None


def _extract_title(soup: BeautifulSoup) -> str:
    # Priority: og:title / twitter:title / <h1> / <title>
    t = _meta_content(soup, ("property", "og:title")) \
        or _meta_content(soup, ("name", "twitter:title"))
    if t:
        return t

    h1 = soup.find("h1")
    if h1:
        ht = h1.get_text(" ", strip=True)
        if ht:
            return ht

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    return ""


def _p_text_len(node: Tag) -> int:
    return sum(len((p.get_text(" ", strip=True) or "")) for p in node.find_all("p"))


def _para_count(node: Tag) -> int:
    return sum(1 for _ in node.find_all("p"))


def _link_density(node: Tag) -> float:
    text = node.get_text(" ", strip=True) or ""
    link_text = " ".join(a.get_text(" ", strip=True) or "" for a in node.find_all("a"))
    if not text:
        return 0.0
    return min(1.0, len(link_text) / max(1, len(text)))


def _score_node(node: Tag) -> float:
    """Heuristic score for 'is this the main article body?'"""
    p_len = _p_text_len(node)                 # total paragraph text length
    p_cnt = _para_count(node)                 # number of paragraphs
    ld = _link_density(node)                  # lower is better
    heading_bonus = 80 if node.find(["h1", "h2"]) else 0
    figure_bonus = 40 if node.find(["figure", "img"]) else 0

    # Penalize nav-like blocks
    nav_penalty = 150 if node.has_attr("role") and node["role"] in {"navigation", "banner"} else 0
    class_id = (node.get("class") or []) + ([node.get("id")] if node.get("id") else [])
    class_txt = " ".join(class_id).lower()
    if any(k in class_txt for k in ("nav", "menu", "footer", "header", "sidebar")):
        nav_penalty += 200

    # Core score: paragraph mass with mild diminishing returns, minus linkiness, plus bonuses
    score = (p_len ** 0.9) + (p_cnt * 40) - (ld * 120) + heading_bonus + figure_bonus - nav_penalty
    return score


def _candidate_nodes(soup: BeautifulSoup) -> Iterable[Tag]:
    # Obvious first: article-ish containers
    selectors = [
        "article", "main", "[role=main]", "[itemprop=articleBody]",
        ".article", ".article-body", ".post", ".post-content", ".entry-content",
        "#content", "#main", ".content"
    ]
    seen = set()
    for sel in selectors:
        for n in soup.select(sel):
            if isinstance(n, Tag) and n not in seen:
                seen.add(n)
                yield n

    # Fallback: big div/section blocks
    for n in soup.find_all(["div", "section"]):
        # Prefer blocks with at least 2 paragraphs
        if _para_count(n) >= 2:
            yield n


def _pick_best_node(soup: BeautifulSoup) -> Optional[Tag]:
    best_node, best_score = None, 0.0
    for n in _candidate_nodes(soup):
        score = _score_node(n)
        if score > best_score:
            best_node, best_score = n, score
    return best_node


# --------------------------- main API ---------------------------

def extract_readable_text(html: str, url: str) -> Dict[str, str]:
    """
    Convert raw HTML into a clean article-like text blob (no readability dependency).
    Output:
      { "url": str, "title": str, "text": str }
    """
    if not html:
        return {"url": url, "title": "", "text": ""}

    # Parse full page
    soup_full = BeautifulSoup(html, "lxml")

    # Title first (from metas/h1/title)
    title = _extract_title(soup_full)

    # Remove obvious chrome globally to help scoring
    _strip_boilerplate(soup_full)

    # Find best content node
    best = _pick_best_node(soup_full)

    if not best:
        # Fallback: take body text (trimmed), but try to keep it short if it's a nav-like page
        body = soup_full.body or soup_full
        text = _collapse_ws(body.get_text("\n"))
        # If super long and likely noisy, keep first ~3k chars
        main_text = text[:3000]
    else:
        # Work on a clone-like object by re-parsing best fragment's HTML for a clean pass
        best_html = str(best)
        best_soup = BeautifulSoup(best_html, "lxml")
        _strip_boilerplate(best_soup)

        # Prefer only <p>, <li> text to avoid navs in deep descendants
        parts = []
        for blk in best_soup.find_all(["p", "li"]):
            t = blk.get_text(" ", strip=True)
            if t and len(t) > 30:
                parts.append(t)
        # If that was too strict, fall back to full text
        if not parts:
            parts.append(best_soup.get_text(" ", strip=True))
        main_text = _collapse_ws("\n\n".join(parts))

    # Final light cleanup: drop leading site-name lines (heuristic)
    if main_text:
        main_text = re.sub(r"^\s*(?:[A-Za-z0-9\-\|: ]{1,80}\n){0,2}", "", main_text)

    return {"url": url, "title": title or "", "text": main_text or ""}


# --------------------------- smoke test ---------------------------

if __name__ == "__main__":
    # quick check with your fetcher
    import logging
    from tools.fetch_page import fetch_page

    logging.basicConfig(level=getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))
    test_url = "https://en.wikipedia.org/wiki/Multimodal_learning"
    fetched = fetch_page(test_url)
    out = extract_readable_text(fetched["html"], fetched["url"])
    print(f"title: {out['title'][:120]}")
    print(f"text_len: {len(out['text'])}")
    print(out["text"][:500].replace("\n", " ") + " ...")
