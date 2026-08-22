"""
Load layer: store enriched articles as daily JSON files + a master index.

Load (L) of the ETL pipeline. Storage layout:

  data/
    articles-YYYY-MM-DD.json   <- one file per run
    index.json                 <- all links ever seen (for dedup)
"""

import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")


def _load_index() -> dict:
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"links": []}


def deduplicate(articles: list[dict]) -> list[dict]:
    """Drop articles we've already stored in previous runs."""
    index = _load_index()
    seen = set(index["links"])
    fresh = [a for a in articles if a["link"] not in seen]
    return fresh


def save(articles: list[dict]) -> str:
    """Save today's articles and update the dedup index. Returns output path."""
    os.makedirs(DATA_DIR, exist_ok=True)

    # Daily file
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = os.path.join(DATA_DIR, f"articles-{today}.json")

    existing = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            existing = json.load(f)

    existing.extend(articles)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # Update index
    index = _load_index()
    index["links"].extend(a["link"] for a in articles)
    index["last_run"] = datetime.now(timezone.utc).isoformat()
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return out_path


if __name__ == "__main__":
    print(save([{"link": "test", "title": "test"}]))
