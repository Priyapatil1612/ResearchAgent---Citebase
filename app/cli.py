# app/cli.py
from __future__ import annotations

import argparse
import sys
import textwrap

from agent.agent_react import ResearchAgent
from utils.common import slugify


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(prog="research-agent", description="Research Assistant Agent CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("research", help="Ingest web knowledge for a topic")
    p_ing.add_argument("topic", type=str, help="Topic to research")
    p_ing.add_argument("--ns", type=str, default=None, help="Optional namespace (slug). Default = slug(topic)")
    p_ing.add_argument("--force", action="store_true", help="Force re-ingest even if namespace exists")

    p_ask = sub.add_parser("ask", help="Ask a question using an existing namespace")
    p_ask.add_argument("question", type=str, help="Your question")
    p_ask.add_argument("--ns", type=str, required=True, help="Namespace used during ingest")
    p_ask.add_argument("--top-k", type=int, default=None, help="Override retrieval top_k")

    args = parser.parse_args(argv)
    agent = ResearchAgent()

    if args.cmd == "research":
        out = agent.research(args.topic, namespace=args.ns, force=args.force)
        ns = out["namespace"]
        print(f"\nNamespace: {ns}")
        print("Did ingest:", out["did_ingest"])
        if out["did_ingest"]:
            s = out["ingest_summary"]
            print(f"Indexed pages: {s['indexed_pages']} | Indexed chunks: {s['indexed_chunks']} | Skipped pages: {s['skipped_pages']}")
            print("\nSources:")
            for src in s["sources"]:
                print(f" - {src['title'][:90]}  ({src['text_len']} chars)\n   {src['url']}")
        print("\nTrace:")
        for step in out["trace"]:
            print("  ", step)

    elif args.cmd == "ask":
        out = agent.ask(args.question, namespace=args.ns, top_k=args.top_k)
        print(f"\nNamespace: {out['namespace']}")
        print("\nAnswer:\n")
        print(textwrap.fill(out["content"], width=100))
        print("\nCitations:")
        for c in out["citations"]:
            print(" -", c["title"][:90], "\n   ", c["url"])
        print("\nTrace:")
        for step in out["trace"]:
            print("  ", step)


if __name__ == "__main__":
    main()
