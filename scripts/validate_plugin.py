#!/usr/bin/env python3
"""Validate the plugin manifests and skill files.

Run locally with: python scripts/validate_plugin.py

This exists because the repo is a single-plugin marketplace that resolves the
default branch directly. There is no staging: a malformed manifest on main
breaks the install for everyone on their next update.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []


def error(message):
    errors.append(message)


def load_json(relative_path):
    path = ROOT / relative_path
    if not path.is_file():
        error(f"{relative_path}: missing")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(f"{relative_path}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}")
        return None


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


plugin = load_json(".claude-plugin/plugin.json")
marketplace = load_json(".claude-plugin/marketplace.json")
load_json("hbs-event-email-digest.config.example.json")

plugin_name = None
if plugin is not None:
    for field in ("name", "version", "description"):
        if not plugin.get(field):
            error(f".claude-plugin/plugin.json: missing required field '{field}'")
    plugin_name = plugin.get("name")

if marketplace is not None:
    if not marketplace.get("name"):
        error(".claude-plugin/marketplace.json: missing required field 'name'")
    if not marketplace.get("owner"):
        error(".claude-plugin/marketplace.json: missing required field 'owner'")

    listed = marketplace.get("plugins")
    if not isinstance(listed, list) or not listed:
        error(".claude-plugin/marketplace.json: 'plugins' must be a non-empty array")
    else:
        for entry in listed:
            name = entry.get("name")
            source = entry.get("source")
            if not name:
                error(".claude-plugin/marketplace.json: a plugin entry is missing 'name'")
            elif plugin_name and name != plugin_name:
                error(
                    f".claude-plugin/marketplace.json: plugin entry '{name}' does not match "
                    f"plugin.json name '{plugin_name}'. The marketplace install would resolve nothing."
                )
            if not source:
                error(f".claude-plugin/marketplace.json: plugin entry '{name}' is missing 'source'")
            elif not (ROOT / source).is_dir():
                error(f".claude-plugin/marketplace.json: plugin source '{source}' is not a directory")

skills_dir = ROOT / "skills"
if not skills_dir.is_dir():
    error("skills/: missing")
else:
    skill_dirs = [d for d in sorted(skills_dir.iterdir()) if d.is_dir()]
    if not skill_dirs:
        error("skills/: contains no skill directories")
    for skill in skill_dirs:
        manifest = skill / "SKILL.md"
        relative = f"skills/{skill.name}/SKILL.md"
        if not manifest.is_file():
            error(f"{relative}: missing")
            continue
        fields = parse_frontmatter(manifest)
        if fields is None:
            error(f"{relative}: missing YAML frontmatter (must open with a '---' line)")
            continue
        if not fields.get("name"):
            error(f"{relative}: frontmatter missing 'name'")
        elif fields["name"] != skill.name:
            error(
                f"{relative}: frontmatter name '{fields['name']}' does not match its directory "
                f"'{skill.name}'. The skill will not load."
            )
        if not fields.get("description"):
            error(f"{relative}: frontmatter missing 'description'")

if errors:
    print("Plugin validation failed:\n")
    for message in errors:
        print(f"  - {message}")
    sys.exit(1)

print("Plugin validation passed.")
