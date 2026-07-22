# daemon

**Ask your homelab anything. plain English. 5 minutes.**

Daemon is a read-only AI assistant for your homelab. Point it at your Proxmox node, Docker host, or TrueNAS box: ask it questions, document your setup, pin reminders, get health summaries. No dashboards. No agents. No setup hell.

```bash
python daemon.py ask "why is my plex container using so much RAM"
# → Your plex container is consuming 4.2GB RAM (87% of its limit).
#   This is likely caused by transcoding. Consider setting a RAM transcode
#   limit in Plex settings or increasing the container memory cap.
```

---

## Why Daemon

You've seen Hermes agent. You know it's powerful. You also know it takes a weekend to configure properly, requires a running server, and has more moving parts than your actual homelab.

Daemon is the other thing. One tool. Read only. Ready in 5 minutes. It answers questions and gets out of your way.

---

## Install

```bash
git clone https://github.com/hapheastusx/daemon
cd daemon
pip install -r requirements.txt
cp config.yaml config.yaml  # fill in your details
python daemon.py setup
```

---

## Commands

```bash
# Ask anything
python daemon.py ask "what's eating my disk space"
python daemon.py ask "which containers haven't been used in a week" --pin
python daemon.py ask "is anything on my network that shouldn't be" --email

# Health summary
python daemon.py health

# Document a specific resource
python daemon.py document plex

# Export full lab docs to markdown
python daemon.py export homelab.md

# Sticky notes
python daemon.py note "migrate VM 104 after RAM upgrade" --resource proxmox
python daemon.py notes
python daemon.py forget 1

# Raw data view
python daemon.py status

# Local REST API (for integrations)
python daemon.py serve
```

---

## REST API

```bash
python daemon.py serve  # starts at http://localhost:6789
```

```
GET  /api/status              # raw homelab data
GET  /api/health              # plain English health summary
GET  /api/query?q=question    # ask anything
GET  /api/containers          # Docker containers
GET  /api/vms                 # Proxmox VMs
GET  /api/notes               # sticky notes
POST /api/notes               # add a note
DELETE /api/notes/:id         # delete a note
```

The API is local only. Nothing leaves your machine except AI queries to your chosen provider.

---

## Configuration

Fill in `config.yaml` once. Never touch it again.

```yaml
ai:
  provider: openai       # or anthropic
  api_key: YOUR_KEY
  model: gpt-oss:20b     # cheap and more than enough

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
  user: you@gmail.com
  password: your-app-password
  to: you@gmail.com
```

---

## Bring Your Own API Key

Daemon never touches your tokens. You connect directly to OpenAI or Anthropic with your own key. At typical homelab usage (a few questions a week) expect to spend $1-3/month directly. We never see it.

Want to run fully offline? Point Daemon at your local Ollama endpoint instead.

---

## Philosophy

- **Read only.** Daemon observes. It never executes commands on your system.
- **One tool.** Not a platform. Not a framework. A tool that does one thing well.
- **Your data stays home.** Nothing is stored remotely. No telemetry. No tracking.
- **Simplify, then add lightness.** — Chapman

---

## Build on top of Daemon

The API is yours. Do whatever you want with it.

Fork it. Spin it off. Build plugins. Sell your own version. I don't care. Just credit the original and have fun.

---

## Supported Integrations

| Integration | Status |
|---|---|
| Docker |  Supported |
| Proxmox |  Supported |
| TrueNAS |  Coming |
| Unraid |  Community PR welcome |
| Home Assistant |  Community PR welcome |
| pfSense |  Community PR welcome |

---

## License

MIT. Do whatever you want.
