"""
Starter AI Agent: LangGraph + Google Gemini (free tier).

A ReAct-style agent that can use tools in a Reason -> Act -> Observe loop.
Run: python agent.py
"""

import os
import warnings

warnings.filterwarnings("ignore", message=".*create_react_agent.*")

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Load GOOGLE_API_KEY from .env
load_dotenv()


# ---------- Tools ----------
@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression, e.g. '23 * 19 + 12'."""
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: only numbers and + - * / ( ) are allowed."
    try:
        return str(eval(expression))  # noqa: S307 - input sanitized above
    except Exception as e:
        return f"Error: {e}"


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def write_note(filename: str, content: str) -> str:
    """Write text content to a file inside the ./notes folder."""
    os.makedirs("notes", exist_ok=True)
    path = os.path.join("notes", os.path.basename(filename))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved to {path}"


TOOLS = [calculator, get_current_time, write_note]


# ---------- Agent ----------
def build_agent(provider: str = "ollama"):
    """Build the agent. provider: 'ollama' (local, instant) or 'gemini' (cloud)."""
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            temperature=0,
            # Disable "thinking" mode for faster, cheaper responses
            model_kwargs={"thinking_config": {"thinking_budget": 0}},
        )
    else:
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model="gemma4:latest",
            temperature=0,
            # Explicit loopback: OLLAMA_HOST env may be 0.0.0.0 (bind-only addr)
            base_url="http://127.0.0.1:11434",
        )

    return create_react_agent(
        llm,
        tools=TOOLS,
        prompt=(
            "You are a helpful assistant. Use the available tools when they "
            "help answer the question. Be concise."
        ),
    )


def main():
    import sys

    provider = sys.argv[1] if len(sys.argv) > 1 else "ollama"
    if provider == "gemini" and not os.getenv("GOOGLE_API_KEY"):
        print("Missing GOOGLE_API_KEY. Copy .env.example to .env and add your key.")
        return

    print(f"Provider: {provider}")
    agent = build_agent(provider)
    print("Agent ready! Type your question (or 'quit' to exit).\n")

    history = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        result = agent.invoke({"messages": history})
        history = result["messages"]

        reply = history[-1]
        # Extract plain text from content blocks (handles str or list-of-blocks)
        if isinstance(reply.content, list):
            text = "".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in reply.content
            )
        else:
            text = reply.content
        print(f"Agent: {text}\n")


if __name__ == "__main__":
    main()
