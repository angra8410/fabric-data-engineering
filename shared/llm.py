"""
Shared LLM setup for all agents.

Usage:
    from shared.llm import get_llm
    llm = get_llm("ollama")   # local, free, offline
    llm = get_llm("gemini")   # cloud, better quality (needs GOOGLE_API_KEY)
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(provider: str = "ollama"):
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model="gemma4:latest",
        temperature=0,
        base_url="http://127.0.0.1:11434",
    )


def extract_text(response) -> str:
    """Extract plain text from an LLM response (str or content blocks)."""
    content = response.content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in content
        )
    return content
