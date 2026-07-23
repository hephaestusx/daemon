import json
import os
from datetime import datetime

NOTES_FILE = os.path.join(os.path.dirname(__file__), "..", "notes.json")

def _load() -> list:
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE) as f:
        content = f.read().strip()
        if not content:
            return []
        return json.loads(content)

def _save(notes: list):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)

def add(text: str, resource: str = None) -> dict:
    notes = _load()
    note = {
        "id": len(notes) + 1,
        "text": text,
        "resource": resource,
        "created": datetime.now().isoformat(),
    }
    notes.append(note)
    _save(notes)
    return note

def get_all() -> list:
    return _load()

def delete(note_id: int) -> bool:
    notes = _load()
    updated = [n for n in notes if n["id"] != note_id]
    if len(updated) == len(notes):
        return False
    _save(updated)
    return True

def format_notes(notes: list) -> str:
    if not notes:
        return "No sticky notes yet."
    lines = []
    for n in notes:
        resource = f" [{n['resource']}]" if n.get("resource") else ""
        lines.append(f"#{n['id']}{resource} — {n['text']} ({n['created'][:10]})")
    return "\n".join(lines)
