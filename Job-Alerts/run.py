"""
Job Boards Agent — daily digest of relevant job postings.

Flow:
1. Fetch job listings from RSS feeds (config.FEEDS)
2. Filter by age, keywords, and dedupe against previously seen jobs
3. LLM scores each candidate for relevance to your profile
4. Send a digest via shared.notify (Telegram/Discord/console)

Run:  python job-boards/run.py
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser

from shared.llm import get_llm, extract_text
from shared.notify import notify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import FEEDS, MUST_HAVE, EXCLUDE, TOP_N, MAX_AGE_DAYS, LLM_PROVIDER

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SEEN_FILE = os.path.join(DATA_DIR, "seen.json")


def load_seen() -> dict:
    """id -> first-seen ISO date"""
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_seen(seen: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


def fetch_jobs() -> list[dict]:
    """Collect job postings from all configured RSS feeds."""
    jobs = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                published = None
                for attr in ("published_parsed", "updated_parsed"):
                    if getattr(e, attr, None):
                        published = datetime.fromtimestamp(
                            time.mktime(e[attr]), tz=timezone.utc
                        )
                        break
                jobs.append(
                    {
                        "id": e.get("id") or e.get("link", ""),
                        "title": e.get("title", "").strip(),
                        "company": e.get("author", "").strip() or "Unknown",
                        "link": e.get("link", ""),
                        "summary": _clean(e.get("summary", "")),
                        "published": published,
                        "source": feed.feed.get("title", url),
                    }
                )
        except Exception as exc:
            print(f"Feed failed ({url}): {exc}")
    return jobs


def _clean(text: str, limit: int = 600) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _fetch_json(url: str):
    import requests

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_remotive() -> list[dict]:
    """Remotive JSON API (their RSS feed is dead)."""
    jobs = []
    try:
        for j in _fetch_json("https://remotive.com/api/remote-jobs").get("jobs", []):
            pub = j["publication_date"]
            published = (
                datetime.fromisoformat(pub.replace("Z", "+00:00"))
                if isinstance(pub, str)
                else datetime.fromtimestamp(int(pub), tz=timezone.utc)
            )
            jobs.append(
                {
                    "id": j["url"],
                    "title": j.get("title", "").strip(),
                    "company": j.get("company_name", "").strip() or "Unknown",
                    "link": j["url"],
                    "summary": _clean(j.get("description", "")),
                    "published": published,
                    "source": "Remotive",
                }
            )
    except Exception as exc:
        print(f"Remotive API failed: {exc}")
    return jobs


def fetch_remoteok() -> list[dict]:
    """RemoteOK JSON API (their RSS feed is dead). First element is metadata."""
    jobs = []
    try:
        for j in _fetch_json("https://remoteok.com/api")[1:]:
            jobs.append(
                {
                    "id": j.get("url") or j.get("apply_url", ""),
                    "title": (j.get("position") or "").strip(),
                    "company": (j.get("company") or "").strip() or "Unknown",
                    "link": j.get("url") or j.get("apply_url", ""),
                    "summary": _clean(j.get("description", "")),
                    "published": datetime.fromtimestamp(
                        int(j.get("epoch", 0)), tz=timezone.utc
                    ),
                    "source": "Remote OK",
                }
            )
    except Exception as exc:
        print(f"RemoteOK API failed: {exc}")
    return jobs


def keyword_filter(job: dict) -> bool:
    text = f"{job['title']} {job['summary']}".lower()
    if any(k.lower() in text for k in EXCLUDE):
        return False
    if MUST_HAVE and not any(k.lower() in text for k in MUST_HAVE):
        return False
    return True


def age_filter(job: dict) -> bool:
    if not job["published"]:
        return True  # keep unknown-age postings
    published = job["published"]
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    return published >= cutoff


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Ask the LLM to score each job 0-10 for relevance."""
    llm = get_llm(LLM_PROVIDER)
    scored = []
    for job in jobs:
        prompt = (
            "You are a job-match assistant. Score this job posting 0-10 for "
            "relevance to a Data Analyst / Power BI Developer seeking remote work. "
            "Respond with ONLY the integer score.\n\n"
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Summary: {job['summary']}"
        )
        try:
            resp = llm.invoke(prompt)
            score = int("".join(c for c in extract_text(resp) if c.isdigit())[:2] or 0)
        except Exception as exc:
            print(f"Scoring failed for '{job['title']}': {exc}")
            score = 0
        job["score"] = min(score, 10)
        scored.append(job)
    return sorted(scored, key=lambda j: j["score"], reverse=True)


def build_digest(jobs: list[dict]) -> str:
    lines = [f"💼 <b>Daily Job Digest</b> — {datetime.now():%Y-%m-%d}\n"]
    for i, job in enumerate(jobs[:TOP_N], 1):
        lines.append(
            f"{i}. <b>{job['title']}</b> @ {job['company']} "
            f"(score {job['score']}/10)\n"
            f"{job['link']}\n"
        )
    if len(jobs) > TOP_N:
        lines.append(f"...and {len(jobs) - TOP_N} more matches.")
    return "\n".join(lines)


def main() -> None:
    print("Fetching feeds...")
    jobs = fetch_jobs()
    print(f"Fetched {len(jobs)} postings from RSS")

    api_jobs = fetch_remotive() + fetch_remoteok()
    print(f"Fetched {len(api_jobs)} postings from JSON APIs")
    jobs += api_jobs

    api_jobs = fetch_remotive() + fetch_remoteok()
    print(f"Fetched {len(api_jobs)} postings from JSON APIs")
    jobs += api_jobs

    seen = load_seen()
    fresh = [j for j in jobs if j["id"] and j["id"] not in seen]
    print(f"{len(fresh)} new postings")

    fresh = [j for j in fresh if age_filter(j) and keyword_filter(j)]
    print(f"{len(fresh)} after filters")

    if not fresh:
        notify("💼 No new matching jobs today.")
        return

    print("Scoring with LLM...")
    ranked = score_jobs(fresh)

    # Mark all as seen regardless of score
    today = datetime.now().strftime("%Y-%m-%d")
    for job in fresh:
        seen[job["id"]] = today
    save_seen(seen)

    digest = build_digest(ranked)
    notify(digest)
    print("Digest sent.")


if __name__ == "__main__":
    main()
