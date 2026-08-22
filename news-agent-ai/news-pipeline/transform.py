"""
Transformation layer: LLM agent summarizes, classifies, and scores sentiment.

Transform (T) of the ETL pipeline. Uses local Ollama by default (free),
or Gemini with `provider="gemini"`.
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = (
    "Eres un analista de noticias. Para cada artículo devuelve SOLO un JSON "
    "(sin texto adicional) con estas claves:\n"
    '{"relevant": bool,          # ¿trata del presidente/gobierno de Colombia?\n'
    ' "summary_es": str,         # resumen en español, máx 3 frases\n'
    ' "topics": [str],           # ej: ["economía", "seguridad"]\n'
    ' "sentiment": str}          # uno de: positivo | neutral | negativo\n'
    "Si el artículo no es relevante, usa relevant=false y campos vacíos."
)


def _get_llm(provider: str = "ollama"):
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            temperature=0,
            model_kwargs={"thinking_config": {"thinking_budget": 0}},
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model="gemma4:latest",
        temperature=0,
        base_url="http://127.0.0.1:11434",
    )


def _parse_json(text: str) -> dict:
    """Extract the first JSON object from an LLM response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def analyze_article(llm, article: dict) -> dict:
    """Ask the LLM to analyze one article; returns analysis dict."""
    prompt = (
        f"Título: {article['title']}\n"
        f"Fuente: {article['source']}\n"
        f"Fecha: {article['published_at']}\n"
        f"Contenido: {article['summary_raw'][:1500]}"
    )
    try:
        response = llm.invoke(
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": prompt}]
        )
        content = response.content
        if isinstance(content, list):
            content = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )
        result = _parse_json(content)
        if not result:
            return {"relevant": False, "error": "unparseable response"}
        return result
    except Exception as e:
        return {"relevant": False, "error": str(e)}


def enrich_articles(articles: list[dict], provider: str = "ollama") -> list[dict]:
    """Analyze all articles and attach structured metadata."""
    llm = _get_llm(provider)
    enriched = []
    for i, article in enumerate(articles, 1):
        print(f"  [{i}/{len(articles)}] {article['title'][:60]}...")
        analysis = analyze_article(llm, article)
        enriched.append({**article, "analysis": analysis})
    return enriched


if __name__ == "__main__":
    from ingest import fetch_all

    arts = fetch_all()[:3]
    for a in enrich_articles(arts):
        print(json.dumps(a["analysis"], ensure_ascii=False, indent=2))
