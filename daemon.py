#!/usr/bin/env python3
import click
import yaml
import os
import json
from agent.docker import get_summary as docker_summary
from agent.proxmox import ProxmoxAgent
from ai.query import query
from notes import sticky, email as emailer

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def gather_homelab_data(config: dict) -> dict:
    data = {}
    if config.get("docker", {}).get("enabled"):
        data["docker"] = docker_summary()
    if config.get("proxmox", {}).get("enabled"):
        agent = ProxmoxAgent(config["proxmox"])
        data["proxmox"] = agent.get_summary()
    return data

@click.group()
def cli():
    """Daemon — Ask your homelab anything."""
    pass

@cli.command()
@click.argument("question")
@click.option("--pin", is_flag=True, help="Pin the answer as a sticky note")
@click.option("--email", is_flag=True, help="Email the answer")
def ask(question, pin, email):
    """Ask your homelab a question in plain English."""
    config = load_config()
    click.echo("Gathering homelab data...")
    data = gather_homelab_data(config)
    if not data:
        click.echo("No integrations enabled. Check your config.yaml")
        return
    click.echo("Thinking...\n")
    answer = query(question, data, config["ai"])
    click.echo(f"Daemon: {answer}\n")
    if pin:
        note = sticky.add(f"Q: {question}\nA: {answer}")
        click.echo(f"Pinned as note #{note['id']}")
    if email and config.get("smtp", {}).get("enabled"):
        note = {"text": f"Q: {question}\nA: {answer}", "created": "now", "resource": None}
        emailer.send_note(note, config["smtp"])
        click.echo("Emailed.")

@cli.command()
def health():
    """Get a plain English health summary of your homelab."""
    config = load_config()
    data = gather_homelab_data(config)
    if not data:
        click.echo("No integrations enabled.")
        return
    answer = query("Give me a health summary of my homelab. Flag anything that looks wrong.", data, config["ai"])
    click.echo(f"\nDaemon Health Summary:\n{answer}\n")

@cli.command()
@click.option("--resource", default=None, help="Pin note to a specific resource")
@click.argument("text")
def note(text, resource):
    """Add a sticky note."""
    n = sticky.add(text, resource)
    click.echo(f"Note #{n['id']} saved.")
    config = load_config()
    if config.get("smtp", {}).get("enabled"):
        emailer.send_note(n, config["smtp"])
        click.echo("Emailed.")

@cli.command()
def notes():
    """List all sticky notes."""
    all_notes = sticky.get_all()
    click.echo(sticky.format_notes(all_notes))

@cli.command()
@click.argument("note_id", type=int)
def forget(note_id):
    """Delete a sticky note by ID."""
    if sticky.delete(note_id):
        click.echo(f"Note #{note_id} deleted.")
    else:
        click.echo(f"Note #{note_id} not found.")

@cli.command()
def status():
    """Show raw homelab data Daemon can see."""
    config = load_config()
    data = gather_homelab_data(config)
    click.echo(json.dumps(data, indent=2))

@cli.command()
def setup():
    """Interactive setup wizard."""
    click.echo("Welcome to Daemon setup.\n")
    click.echo("Open config.yaml and fill in your details.")
    click.echo("Enable docker: true if Docker is running on this machine.")
    click.echo("Enable proxmox: true and add your Proxmox API token to monitor VMs.")
    click.echo("Add your AI API key from openai.com or anthropic.com")
    click.echo("Add SMTP credentials if you want email reminders.\n")
    click.echo("Then run: python daemon.py ask 'what is running on my homelab'")

@cli.command()
@click.option("--port", default=6789, help="Port to run API on (default 6789)")
def serve(port):
    """Start the local REST API server for integrations."""
    from api.server import start
    start(port)

@cli.command()
@click.argument("output", default="homelab.md")
def export(output):
    """Export full homelab documentation as a markdown file."""
    config = load_config()
    click.echo("Gathering homelab data...")
    data = gather_homelab_data(config)
    if not data:
        click.echo("No integrations enabled.")
        return
    click.echo("Generating documentation...")
    doc = query(
        """Generate a complete markdown documentation file for this homelab.
        Include: overview, all running services, resource usage, and any concerns.
        Format it cleanly with headers, tables where useful, and bullet points.
        Write it as if documenting for a future self or a new team member.""",
        data,
        config["ai"]
    )
    notes_list = sticky.get_all()
    notes_section = "\n## Sticky Notes\n" + sticky.format_notes(notes_list) if notes_list else ""
    full_doc = f"{doc}{notes_section}"
    with open(output, "w") as f:
        f.write(full_doc)
    click.echo(f"Documentation saved to {output}")

@cli.command()
@click.argument("resource")
def document(resource):
    """Auto-generate a description for a specific VM or container."""
    config = load_config()
    data = gather_homelab_data(config)
    if not data:
        click.echo("No integrations enabled.")
        return
    answer = query(
        f"""Look at the resource named '{resource}' in the homelab data.
        Write a clear 2-3 sentence description of what it is, what it does,
        and anything worth knowing about its current state.""",
        data,
        config["ai"]
    )
    click.echo(f"\n{resource}:\n{answer}\n")
    if click.confirm("Pin this description as a sticky note?"):
        sticky.add(answer, resource=resource)
        click.echo("Pinned.")

if __name__ == "__main__":
    cli()
