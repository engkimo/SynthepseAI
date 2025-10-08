#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
milestones_path = repo_root / ".github" / "milestones.json"
milestones = json.loads(milestones_path.read_text(encoding="utf-8"))

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

for m in milestones:
    title = m["title"]
    state = m.get("state", "open")
    desc = m.get("description", "")
    # Try create; if exists, update
    create = run(["gh", "api", "repos/{owner}/{repo}/milestones", "-f", f"title={title}", "-f", f"state={state}", "-f", f"description={desc}"])
    if create.returncode != 0:
        # Find milestone number by title, then update
        ls = run(["gh", "api", "repos/{owner}/{repo}/milestones?state=all"])
        if ls.returncode == 0:
            import sys
            data = json.loads(ls.stdout or "[]")
            number = next((x["number"] for x in data if x.get("title") == title), None)
            if number:
                run(["gh", "api", f"repos/{{owner}}/{{repo}}/milestones/{number}", "-X", "PATCH", "-f", f"title={title}", "-f", f"state={state}", "-f", f"description={desc}"])
