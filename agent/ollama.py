import subprocess
import requests
import json

OLLAMA_BASE = "http://localhost:11434"

def is_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def list_models() -> list:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.json().get("models", [])
    except Exception:
        return []

def pull_model(model: str):
    """Generator that streams pull progress lines as JSON strings."""
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in proc.stdout:
            yield line.strip()
        proc.wait()
        if proc.returncode == 0:
            yield "__done__"
        else:
            yield "__error__"
    except FileNotFoundError:
        yield "__no_ollama__"
    except Exception as e:
        yield f"__error__ {e}"

def chat(model: str, system: str, user: str) -> str:
    """Single shot query to local Ollama model."""
    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            },
            timeout=120
        )
        return r.json()["message"]["content"]
    except Exception as e:
        return f"Ollama error: {e}"
