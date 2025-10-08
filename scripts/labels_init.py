#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
labels_path = repo_root / ".github" / "labels.json"
labels = json.loads(labels_path.read_text(encoding="utf-8"))

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

for l in labels:
    name = l["name"]
    color = l.get("color", "ededed")
    desc = l.get("description", "")
    # Try create, otherwise update
    create = run(["gh", "label", "create", name, "--color", color, "--description", desc])
    if create.returncode != 0:
        run(["gh", "label", "edit", name, "--color", color, "--description", desc])
