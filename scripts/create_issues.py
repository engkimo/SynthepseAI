#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
seeds_path = repo_root / ".github" / "issue_seeds.json"
seeds = json.loads(seeds_path.read_text(encoding="utf-8"))

def run(cmd):
    return subprocess.run(cmd, text=True, capture_output=True)

# Build milestone title -> number map
ms = run(["gh", "api", "repos/{owner}/{repo}/milestones?state=all"])
title_to_num = {}
if ms.returncode == 0 and ms.stdout:
    data = json.loads(ms.stdout)
    title_to_num = {x.get("title"): x.get("number") for x in data}

for s in seeds:
    title = s["title"]
    body = s.get("body", "")
    labels = s.get("labels", [])
    assignees = s.get("assignees", [])
    milestone_title = s.get("milestone")
    milestone_number = title_to_num.get(milestone_title) if milestone_title else None

    args = ["gh", "issue", "create", "--title", title, "--body", body]
    if labels:
        args += sum([["--label", l] for l in labels], [])
    if assignees:
        args += sum([["--assignee", a] for a in assignees], [])
    if milestone_number:
        args += ["--milestone", str(milestone_number)]

    run(args)
