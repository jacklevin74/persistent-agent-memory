#!/usr/bin/env python3
"""
Drop a knowledge chunk into knowledge.db
Usage: python3 scripts/log_knowledge.py --agent-id theo-main --content "fact here" --source "TOOLS.md" --tags "x1,validators"
"""
import argparse, sqlite3, uuid
from datetime import datetime
from pathlib import Path

DB = Path("./data/knowledge.db")

def add_chunk(content, source=None, agent_id=None, tags=None):
    conn = sqlite3.connect(DB)
    chunk_id = str(uuid.uuid4())
    conn.execute("""
        INSERT OR IGNORE INTO chunks (id, content, source, agent_id, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (chunk_id, content, source, agent_id, tags, int(datetime.utcnow().timestamp())))
    conn.commit()
    conn.close()
    print(f"Added chunk from {source}: {content[:80]}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--content", required=True)
    parser.add_argument("--source")
    parser.add_argument("--agent-id", default="theo-main")
    parser.add_argument("--tags")
    args = parser.parse_args()
    add_chunk(args.content, args.source, args.agent_id, args.tags)
