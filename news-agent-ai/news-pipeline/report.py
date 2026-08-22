"""
Generate a monthly report from the news archive.

Usage:
  python report.py                 # current month
  python report.py 2026-08         # specific month (YYYY-MM)

Output: reports/report-YYYY-MM.md
"""

import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def load_month(month: str) -> list[dict]:
    """Load all articles from daily files matching YYYY-MM."""
    articles = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, f"articles-{month}-*.json"))):
        with open(path, encoding="utf-8") as f:
            articles.extend(json.load(f))
    return articles


def _get_llm(provider: str = "gemini"):
    """LLM for writing the executive summary."""
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model="gemma4:latest",
            temperature=0.3,
            base_url="http://127.0.0.1:11434",
        )
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model="gemini-3.6-flash")


def executive_summary(provider: str, month: str, relevant: list[dict],
                      topics: Counter, sentiments: Counter) -> str:
    """Ask the LLM to write a prose overview of the month's coverage."""
    headlines = "\n".join(
        f"- [{a.get('source','')}] {a['title']} — {a['analysis'].get('summary_es','')[:200]}"
        for a in relevant[:40]
    )
    prompt = (
        f"Eres un analista político. Con base en la cobertura de noticias de "
        f"agosto {month} sobre el presidente de Colombia, escribe un resumen "
        f"ejecutivo de 3-4 párrafos en español. Cubre: los hechos más "
        f"importantes, el tono general de la prensa ({dict(sentiments)}) y los "
        f"temas dominantes ({[t for t,_ in topics.most_common(5)]}).\n\n"
        f"Titulares y resúmenes:\n{headlines}"
    )
    try:
        response = _get_llm(provider).invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )
        return content.strip()
    except Exception as e:
        return f"_(No se pudo generar el resumen ejecutivo: {e})_"


def build_report(month: str, articles: list[dict], provider: str = "gemini") -> str:
    relevant = [a for a in articles if a.get("analysis", {}).get("relevant")]

    topics = Counter()
    sentiments = Counter()
    sources = Counter()
    for a in relevant:
        analysis = a["analysis"]
        topics.update(analysis.get("topics", []))
        sentiments[analysis.get("sentiment", "unknown")] += 1
        sources[a.get("source", "unknown")] += 1

    top_articles = sorted(
        relevant,
        key=lambda a: len(a["analysis"].get("summary_es", "")),
        reverse=True,
    )[:10]

    lines = [
        f"# Informe mensual — Presidencia de Colombia ({month})",
        "",
        f"- **Artículos recolectados:** {len(articles)}",
        f"- **Artículos relevantes:** {len(relevant)}",
        f"- **Generado:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Resumen ejecutivo",
        "",
        executive_summary(provider, month, relevant, topics, sentiments),
        "",
        "## Sentimiento de la cobertura",
        "",
    ]
    total = sum(sentiments.values()) or 1
    for sentiment, count in sentiments.most_common():
        pct = count / total * 100
        bar = "█" * int(pct / 5)
        lines.append(f"- **{sentiment}:** {count} ({pct:.0f}%) {bar}")

    lines += ["", "## Temas principales", ""]
    for topic, count in topics.most_common(10):
        lines.append(f"- {topic}: {count} artículos")

    lines += ["", "## Fuentes más activas", ""]
    for source, count in sources.most_common(8):
        lines.append(f"- {source}: {count}")

    lines += ["", "## Artículos destacados", ""]
    for a in top_articles:
        summary = a["analysis"].get("summary_es", "").strip()
        lines += [
            f"### {a['title']}",
            f"*{a.get('source', '')} · {a.get('published_at', '')[:10]}*",
            "",
            summary,
            f"[Leer artículo]({a['link']})",
            "",
        ]

    return "\n".join(lines)


def main():
    month = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y-%m")
    provider = sys.argv[2] if len(sys.argv) > 2 else "gemini"

    articles = load_month(month)
    if not articles:
        print(f"No articles found for {month}")
        return

    report = build_report(month, articles, provider=provider)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f"report-{month}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report saved to {out_path}")


if __name__ == "__main__":
    main()
