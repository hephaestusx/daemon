from flask import Flask, jsonify, request, send_from_directory
import yaml
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agent.docker import get_summary as docker_summary
from agent.proxmox import ProxmoxAgent
from agent.ollama import is_running as ollama_running, list_models, pull_model
from ai.query import query
from notes import sticky, email as emailer

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}

def gather_data(config: dict) -> dict:
    data = {}
    if config.get("docker", {}).get("enabled"):
        data["docker"] = docker_summary()
    if config.get("proxmox", {}).get("enabled"):
        agent = ProxmoxAgent(config["proxmox"])
        data["proxmox"] = agent.get_summary()
    return data

@app.route("/api/health", methods=["GET"])
def health():
    config = load_config()
    data = gather_data(config)
    answer = query("Give me a concise health summary. Flag anything that looks wrong.", data, config["ai"])
    return jsonify({"summary": answer, "raw": data})

@app.route("/api/query", methods=["GET"])
def ask():
    q = request.args.get("q")
    if not q:
        return jsonify({"error": "Missing ?q= parameter"}), 400
    config = load_config()
    data = gather_data(config)
    answer = query(q, data, config["ai"])
    return jsonify({"question": q, "answer": answer})

@app.route("/api/containers", methods=["GET"])
def containers():
    config = load_config()
    if not config.get("docker", {}).get("enabled"):
        return jsonify({"error": "Docker not enabled"}), 503
    return jsonify(docker_summary())

@app.route("/api/vms", methods=["GET"])
def vms():
    config = load_config()
    if not config.get("proxmox", {}).get("enabled"):
        return jsonify({"error": "Proxmox not enabled"}), 503
    agent = ProxmoxAgent(config["proxmox"])
    return jsonify(agent.get_summary())

@app.route("/api/notes", methods=["GET"])
def get_notes():
    return jsonify(sticky.get_all())

@app.route("/api/notes", methods=["POST"])
def add_note():
    body = request.json or {}
    text = body.get("text")
    resource = body.get("resource")
    if not text:
        return jsonify({"error": "Missing text"}), 400
    note = sticky.add(text, resource)
    config = load_config()
    if config.get("smtp", {}).get("enabled"):
        emailer.send_note(note, config["smtp"])
    return jsonify(note), 201

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    if sticky.delete(note_id):
        return jsonify({"deleted": note_id})
    return jsonify({"error": "Note not found"}), 404

@app.route("/api/status", methods=["GET"])
def status():
    config = load_config()
    data = gather_data(config)
    return jsonify(data)

@app.route("/", methods=["GET"])
def index():
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    return send_from_directory(web_dir, "ui.html")

@app.route("/api/config", methods=["POST"])
def save_config():
    try:
        new_config = request.json or {}

        # validate -- must have at minimum a valid ai block with an api_key
        # before we allow anything to be written to disk
        ai = new_config.get("ai", {})
        if not ai.get("api_key") and not ai.get("base_url"):
            return jsonify({"error": "Incomplete config -- ai.api_key required"}), 400

        # load existing so we never wipe keys that arent being updated
        try:
            existing = load_config()
        except Exception:
            existing = {}

        # deep merge only provided keys
        for key, val in new_config.items():
            if isinstance(val, dict) and key in existing and isinstance(existing[key], dict):
                existing[key].update(val)
            else:
                existing[key] = val

        with open(CONFIG_PATH, "w") as f:
            yaml.dump(existing, f, default_flow_style=False)

        return jsonify({"saved": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/config", methods=["GET"])
def get_config():
    try:
        config = load_config()
    except Exception:
        return jsonify({})
    safe = {}
    if "ai" in config:
        safe["ai"] = {"provider": config["ai"].get("provider"), "model": config["ai"].get("model"), "configured": bool(config["ai"].get("api_key"))}
    if "docker" in config:
        safe["docker"] = {"enabled": config["docker"].get("enabled")}
    if "proxmox" in config:
        safe["proxmox"] = {"enabled": config["proxmox"].get("enabled"), "host": config["proxmox"].get("host")}
    if "smtp" in config:
        safe["smtp"] = {"enabled": config["smtp"].get("enabled"), "to": config["smtp"].get("to")}
    return jsonify(safe)

@app.route("/api/ollama/status", methods=["GET"])
def ollama_status():
    running = ollama_running()
    models = list_models() if running else []
    return jsonify({"running": running, "models": [m["name"] for m in models]})

@app.route("/api/ollama/pull", methods=["GET"])
def ollama_pull():
    model = request.args.get("model")
    if not model:
        return jsonify({"error": "Missing ?model= parameter"}), 400
    def generate():
        for line in pull_model(model):
            yield f"data: {line}\n\n"
    return app.response_class(generate(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

def get_local_ip():
    """Get the real LAN IP, bypassing Debian/Pi OS hostname->127.0.1.1 mapping."""
    import socket
    # Method 1 -- UDP route trick, no packets actually sent
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if not ip.startswith("127."):
            return ip
    except Exception:
        pass
    # Method 2 -- scan all interfaces for a non-loopback address
    try:
        import subprocess
        result = subprocess.check_output(["hostname", "-I"], text=True).strip()
        for candidate in result.split():
            if not candidate.startswith("127.") and not candidate.startswith("172."):
                return candidate
    except Exception:
        pass
    return "localhost"

def start(port: int = 6789):
    try:
        config = load_config()
        bind = config.get("server", {}).get("bind", "0.0.0.0")
    except Exception:
        bind = "0.0.0.0"

    local_ip = get_local_ip()

    print(f"\n  Daemon is running\n")
    print(f"  Local:    http://localhost:{port}")
    if bind == "0.0.0.0":
        print(f"  Network:  http://{local_ip}:{port}")
    print(f"\n  Press Ctrl+C to stop.\n")
    app.run(host=bind, port=port, debug=False)
