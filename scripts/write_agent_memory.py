#!/usr/bin/env python3
"""
write_agent_memory.py — Append a timestamped entry to an agent's daily memory log.

Usage:
    python3 scripts/write_agent_memory.py --agent-id theo-main --entry "Did X, found Y, watch for Z"
"""

import argparse
import os
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS_DIR = os.path.join(WORKSPACE, "memory", "agents")


def main():
    parser = argparse.ArgumentParser(description="Write an entry to agent daily memory")
    parser.add_argument("--agent-id", required=True, help="Agent identifier (e.g. theo-main)")
    parser.add_argument("--entry", required=True, help="Log entry text")
    args = parser.parse_args()

    agent_dir = os.path.join(AGENTS_DIR, args.agent_id)
    os.makedirs(agent_dir, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    filepath = os.path.join(agent_dir, f"{date_str}.md")

    # Build the entry
    entry = f"\n## [{time_str}] {args.entry}\n"

    # Append to today's file (create if needed)
    is_new = not os.path.isfile(filepath)
    with open(filepath, "a") as f:
        if is_new:
            f.write(f"# Agent Memory: {args.agent_id} — {date_str}\n")
        f.write(entry)

    print(f"✓ Wrote to {filepath}")


if __name__ == "__main__":
    main()
