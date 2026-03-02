#!/usr/bin/env python3
"""
boot_agent.py — Startup injection for Persistent Agent Memory v2.

Loads the last 2 days of per-agent memory + relevant shared-brain JSON files,
then prints a formatted context block to stdout for injection into agent sessions.

Usage:
    python3 scripts/boot_agent.py --agent-id theo-main
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(WORKSPACE, "memory", "agents")
SHARED_BRAIN_DIR = os.path.join(WORKSPACE, "shared-brain")

# Agent → shared brain file mapping
AGENT_BRAIN_MAP = {
    "theo-main": ["intel-feed.json", "agent-handoffs.json", "x1-ecosystem-state.json"],
    "theo-xchat": ["xchat-handoffs.json", "outreach-log.json", "x1-ecosystem-state.json"],
    "cyberdyne-director": ["cyberdyne-pulse.json", "intel-feed.json", "agent-handoffs.json"],
    "vero-watcher": ["x1-ecosystem-state.json"],
    "x1-token-sync": ["x1-ecosystem-state.json"],
    "nightly-contemplation": ["agent-handoffs.json", "cyberdyne-pulse.json"],
    "x-scanner": ["intel-feed.json", "content-vault.json"],
    "openclaw-scanner": ["openclaw-enhancements.json"],
}


def load_recent_memory(agent_id: str, days: int = 2) -> str:
    """Load the last N days of agent memory logs."""
    agent_dir = os.path.join(AGENTS_DIR, agent_id)
    if not os.path.isdir(agent_dir):
        return ""

    lines = []
    today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=i)
        filename = date.strftime("%Y-%m-%d") + ".md"
        filepath = os.path.join(agent_dir, filename)
        if os.path.isfile(filepath):
            with open(filepath, "r") as f:
                content = f.read().strip()
            if content:
                lines.append(f"### {filename}")
                lines.append(content)
                lines.append("")

    return "\n".join(lines)


def load_shared_brain(agent_id: str) -> str:
    """Load the shared brain files relevant to this agent."""
    brain_files = AGENT_BRAIN_MAP.get(agent_id, [])
    if not brain_files:
        return ""

    sections = []
    for filename in brain_files:
        filepath = os.path.join(SHARED_BRAIN_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            # Only include if there's actual content
            entries = data.get("entries", [])
            has_content = bool(entries)
            # Check other meaningful fields
            for key, val in data.items():
                if key in ("lastUpdatedBy", "lastUpdatedAt", "schemaVersion", "entries"):
                    continue
                if val and val not in (0, [], None, False):
                    has_content = True
                    break

            if has_content:
                sections.append(f"#### {filename}")
                sections.append(f"Last updated by: {data.get('lastUpdatedBy', 'never')}")
                sections.append(f"Last updated at: {data.get('lastUpdatedAt', 'never')}")
                # Show non-entry metadata
                for key, val in data.items():
                    if key in ("lastUpdatedBy", "lastUpdatedAt", "schemaVersion", "entries"):
                        continue
                    sections.append(f"{key}: {json.dumps(val)}")
                # Show recent entries (last 10)
                if entries:
                    recent = entries[-10:]
                    sections.append(f"Recent entries ({len(recent)} of {len(entries)}):")
                    for entry in recent:
                        sections.append(f"  - {json.dumps(entry)}")
                sections.append("")
            else:
                sections.append(f"#### {filename}")
                sections.append("(empty — no entries yet)")
                sections.append("")
        except (json.JSONDecodeError, IOError) as e:
            sections.append(f"#### {filename}")
            sections.append(f"(error loading: {e})")
            sections.append("")

    return "\n".join(sections)


def main():
    parser = argparse.ArgumentParser(description="Boot agent context injection")
    parser.add_argument("--agent-id", required=True, help="Agent identifier (e.g. theo-main)")
    parser.add_argument("--days", type=int, default=2, help="Days of memory to load (default: 2)")
    args = parser.parse_args()

    agent_id = args.agent_id

    if agent_id not in AGENT_BRAIN_MAP:
        print(f"⚠ Unknown agent-id '{agent_id}'. Known agents: {', '.join(AGENT_BRAIN_MAP.keys())}", file=sys.stderr)
        # Still proceed — agent may just not have shared brain mappings

    output = []
    output.append(f"═══ Agent Context: {agent_id} ═══")
    output.append("")

    # Section 1: Recent memory
    memory = load_recent_memory(agent_id, args.days)
    output.append("## Recent Agent Memory")
    if memory:
        output.append(memory)
    else:
        output.append("(no recent memory logs)")
    output.append("")

    # Section 2: Shared brain
    brain = load_shared_brain(agent_id)
    output.append("## Shared Brain State")
    if brain:
        output.append(brain)
    else:
        output.append("(no shared brain files mapped for this agent)")
    output.append("")

    output.append(f"═══ End Agent Context ═══")

    print("\n".join(output))


if __name__ == "__main__":
    main()
