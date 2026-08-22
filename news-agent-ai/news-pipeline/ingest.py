"""
Ingestion layer: fetch news from Google News RSS (free, no API key).

Extract (E) of the ETL pipeline.
"""

from datetime import datetime, timezone

import feedparser
import requests

# Google News RSS search queries — Spanish + English coverage
QUERIES = [
    "presidente de Colombia",
    "Colombia president",
    "gobierno Colombia",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def fetch_google_news(query: str, limit: int = 20) -> list[dict]:
    """Fetch articles for one query from Google News RSS."""
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=es-419&gl=CO&ceid=CO:es-419"
    feed = feedparser.parse(url, agent=USER_AGENT)
    articles = []
    for entry in feed.entries[:limit]:
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        articles.append(
            {
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", ""),
                "source": entry.get("source", {}).get("title", "unknown"),
                "published_at": published.isoformat() if published else None,
                "fetched_query": query,
                "summary_raw": entry.get("summary", "")[:2000],
            }
        )
    return articles


def fetch_all() -> list[dict]:
    """Fetch and merge articles from all queries, deduplicated by link."""
    seen: set[str] = set()
    all_articles: list[dict] = []
    for query in QUERIES:
        try:
            for article in fetch_google_news(query):
                link = article["link"]
                if link and link not in seen:
                    seen.add(link)
                    all_articles.append(article)
        except Exception as e:
            print(f"  ! query '{query}' failed: {e}")
    return all_articles


if __name__ == "__main__":
    arts = fetch_all()
    print(f"Fetched {len(arts)} unique articles")
    for a in arts[:5]:
        print(f"- [{a['source']}] {a['title'][:80]}")
