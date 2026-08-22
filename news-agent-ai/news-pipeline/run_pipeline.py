"""
News pipeline orchestrator: ETL for Colombian president news.

Usage:
  python run_pipeline.py            # local Ollama (free, offline)
  python run_pipeline.py gemini     # Gemini (better quality, free tier)
"""

import sys

from ingest import fetch_all
from load import deduplicate, save
from transform import enrich_articles


def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else "ollama"
    print(f"=== News pipeline (provider: {provider}) ===\n")

    # 1. Extract
    print("[1/3] Fetching news...")
    articles = fetch_all()
    print(f"      {len(articles)} unique articles fetched\n")

    # 2. Dedup against previous runs
    print("[2/3] Filtering already-seen articles...")
    fresh = deduplicate(articles)
    print(f"      {len(fresh)} new articles\n")

    if not fresh:
        print("Nothing new. Done.")
        return

    # 3. Transform (LLM analysis)
    print(f"[3/3] Analyzing with LLM ({provider})...")
    enriched = enrich_articles(fresh, provider=provider)

    relevant = [a for a in enriched if a.get("analysis", {}).get("relevant")]
    print(f"      {len(relevant)} relevant articles\n")

    # 4. Load
    out_path = save(enriched)
    print(f"Saved {len(enriched)} articles to {out_path}")


if __name__ == "__main__":
    main()
