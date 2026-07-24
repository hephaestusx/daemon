# Contributing to Daemon

Fork it. Build it. PR it. That is the whole process.

## What is most wanted right now

New integrations are the highest value contributions. Each one brings a new community to the project.

Adding an integration means creating a new file in `agent/` that follows the same pattern as `agent/docker.py`:

- Read only. Never write to or modify the target system.
- Return a clean dict that the AI can reason about.
- Handle connection failures gracefully and return an empty dict.
- Add your integration to `gather_homelab_data()` in `daemon.py`.

Integrations the community is asking for:

- TrueNAS -- `/agent/truenas.py`
- Unraid -- `/agent/unraid.py`
- Home Assistant -- `/agent/homeassistant.py`
- pfSense -- `/agent/pfsense.py`
- Portainer -- `/agent/portainer.py`
- Grafana -- `/agent/grafana.py`

## Guidelines

Keep it simple. Daemon's whole value is that it is not complex.

Read only always. No exceptions. If your integration writes to anything it will not be merged.

No new dependencies unless absolutely necessary. Prefer the standard library and what is already in requirements.txt.

Test it on real hardware before submitting.

## Credits

Every merged PR gets credited in the release notes by name. If you want to be listed differently just say so in the PR.
