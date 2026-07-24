# Daemon

Ask your homelab anything. Plain English. 5 minutes.

Daemon is a read-only AI assistant for your homelab. Point it at your Proxmox node, Docker host, or TrueNAS box: ask it questions, document your setup, pin reminders, get health summaries. No dashboards. No agents. No setup hell.

```bash
python3 daemon.py ask "why is my plex container using so much RAM"
# Your plex container is consuming 4.2GB RAM (87% of its limit).
# This is likely caused by transcoding. Consider setting a RAM transcode
# limit in Plex settings or increasing the container memory cap.
```

## Why Daemon

You have seen Hermes agent and n8n. You know it is powerful. You also know it takes a weekend to configure properly, requires a running server, and has more moving parts than your actual homelab.

Daemon is the other thing. One tool. Read only. Ready in 5 minutes. It answers questions and gets out of your way.

## How Daemon works

You ask a question. Daemon pulls live data from your homelab using read-only API calls. That data gets sent to your chosen AI provider along with your question. The AI reads the actual state of your system and answers in plain English. Nothing is stored remotely via openrouter. The AI has no ability to change anything as its a communication between python script calling the info > Ai interpreting > Return to sender with the info.

## Install

```bash
git clone https://github.com/hephaestusx/daemon
cd daemon
pip3 install -r requirements.txt
cp confing.example.yaml && config.yaml
python3 daemon.py serve
```

Open http://localhost:6789 and complete the setup wizard.

## Commands

```bash
python3 daemon.py ask "what is eating my disk space"
python3 daemon.py ask "which containers have not been used in a week" --pin
python3 daemon.py ask "is anything on my network that should not be there" --email
python3 daemon.py health
python3 daemon.py document plex
python3 daemon.py export homelab.md
python3 daemon.py note "migrate VM 104 after RAM upgrade" --resource proxmox
python3 daemon.py notes
python3 daemon.py forget 1
python3 daemon.py status
python3 daemon.py serve
```

## REST API

Start the server with `python3 daemon.py serve` then hit http://localhost:6789

```
GET  /api/status              raw homelab data
GET  /api/health              plain English health summary
GET  /api/query?q=question    ask anything
GET  /api/containers          Docker containers
GET  /api/vms                 Proxmox VMs
GET  /api/notes               sticky notes
POST /api/notes               add a note
DELETE /api/notes/:id         delete a note
```

The API is local only. Nothing leaves your machine except AI queries to your chosen provider (P.S: Openrouter for simplicity now, but open to suggestions).

## Configuration

Fill in `config.yaml` once. The setup wizard handles this for you.

```yaml
ai:
  provider: openai
  api_key: YOUR_OPENROUTER_KEY
  base_url: https://openrouter.ai/api/v1
  model: meta-llama/llama-3.1-8b-instruct

docker:
  enabled: true
  socket: /var/run/docker.sock

proxmox:
  enabled: false
  host: 192.168.1.100
  user: root@pam
  token_name: daemon
  token_value: YOUR_TOKEN

smtp:
  enabled: false
  host: smtp.gmail.com
  port: 465
  encryption: ssl
  user: you@gmail.com
  password: your-app-password
  to: you@gmail.com

server:
  bind: 0.0.0.0
  port: 6789
```

## AI

Daemon works with OpenRouter for cloud models or fully local models through Ollama or any OpenAI-compatible endpoint. Your key is stored locally in config.yaml and only used to reach your provider directly. It never leaves your machine.

## Philosophy

Read only. Daemon observes. It never executes commands on your system.

One tool. Not a platform. Not a framework. A tool that does one thing well.

Your data stays home. Nothing is stored remotely. No telemetry. No tracking.

Simplify, then add lightness.

## Build on top of Daemon

The API is yours. Do whatever you want with it, you have my full aproval:

Fork it, Clone it, Build plugins, sell another commercial version, just credit the original. The world is your oyster here. 

## Supported Integrations

| Integration | Status |
|---|---|
| Docker | Supported |
| Proxmox | Supported |
| TrueNAS | Community PR welcome |
| Unraid | Community PR welcome |
| Home Assistant | Community PR welcome |
| pfSense | Community PR welcome |

## License

MIT.
