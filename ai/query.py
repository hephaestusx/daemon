import json
from openai import OpenAI
import anthropic
from agent import ollama as ollama_agent

SYSTEM_PROMPT = """You are Daemon, a read-only AI assistant for homelab infrastructure.
You have been given live data from the user's homelab. Answer in plain English -- 
clear, concise, no unnecessary jargon.

Rules:
- READ ONLY. Never suggest commands that modify the system unless explicitly asked for advice.
- Be specific. Use actual container names, VM IDs, and real numbers from the data.
- If something looks wrong, say so clearly and explain why.
- Keep answers short. One paragraph max unless the question genuinely needs more.
- If the data does not contain enough to answer, say so honestly.
- MARKDOWN RULE: If your response requires a markdown document or structured output,
  generate exactly ONE markdown block. If multiple could apply, generate only the first
  and most relevant one. Notify the user at the end with a single line:
  "Note: only the first markdown block was generated to prevent model hallucination ."
"""

EXPORT_PROMPT = """Generate a concise homelab documentation file in markdown.
Structure it exactly like this and nothing else:

# Homelab Documentation

## Running Services
For each running container or VM write exactly:
- Name, what it does in one sentence, current resource usage.

## Stopped Services
List any stopped containers with a one line status.

## Notes
Flag anything that looks wrong or worth attention.

Be factual. Use only data provided. No examples, no external links, no filler."""

def build_context(homelab_data: dict) -> str:
    return f"Current homelab state:\n{json.dumps(homelab_data, indent=2)}"

def ask_openai(question: str, context: str, config: dict) -> str:
    base_url = config.get("base_url")
    client = OpenAI(
        api_key=config.get("api_key", "daemon"),
        base_url=base_url if base_url else None
    )
    response = client.chat.completions.create(
        model=config.get("model", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{context}\n\nQuestion: {question}"},
        ],
        max_tokens=600,
    )
    return response.choices[0].message.content

def ask_anthropic(question: str, context: str, config: dict) -> str:
    client = anthropic.Anthropic(api_key=config["api_key"])
    response = client.messages.create(
        model=config.get("model", "claude-haiku-4-5-20251001"),
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"{context}\n\nQuestion: {question}"}],
    )
    return response.content[0].text

def ask_ollama(question: str, context: str, config: dict) -> str:
    return ollama_agent.chat(
        model=config.get("model", "llama3.2"),
        system=SYSTEM_PROMPT,
        user=f"{context}\n\nQuestion: {question}"
    )

def query(question: str, homelab_data: dict, ai_config: dict) -> str:
    context = build_context(homelab_data)

    # use tighter export prompt for export and document commands
    is_export = any(word in question.lower() for word in ["document", "documentation", "export", "markdown file"])
    system = EXPORT_PROMPT if is_export else SYSTEM_PROMPT

    provider = ai_config.get("provider", "openai")
    try:
        if provider == "anthropic":
            return ask_anthropic(question, context, ai_config)
        elif provider == "ollama":
            return ask_ollama(question, context, ai_config)
        else:
            return ask_openai(question, context, ai_config)
    except Exception as e:
        return f"AI error: {e}"
