import os
#!/usr/bin/env python3
"""
sync_llm_usage.py — Populate data/llm_usage.db from OpenClaw session JSONL files.

Reads per-message usage data (prompt tokens, output tokens, cache tokens, cost)
from session JSONL files and aggregates per-session into the runs table.

Data source: OpenClaw session JSONL files (~/.openclaw/agents/main/sessions/*.jsonl)
"""

import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DB_PATH = WORKSPACE / "data" / "llm_usage.db"
SESSIONS_DIR = Path(os.environ.get("OPENCLAW_SESSIONS_DIR", os.path.expanduser("~/.openclaw/agents/main/sessions")))
SESSIONS_JSON = SESSIONS_DIR / "sessions.json"


def get_agent_id(session_key: str) -> str:
    """Map session key to agent ID."""
    key = session_key.lower()
    if "xchat" in key:
        return "theo-xchat"
    if "subagent" in key or "subag" in key:
        return "subagent"
    if "telegram:group:-1003871569011" in key:
        return "cyberdyne-director"
    if "telegram:direct" in key:
        return "theo-main"
    if "cron:" in key:
        return "cron-job"
    if session_key == "agent:main:main":
        return "theo-main"
    return "unknown"


def parse_session_jsonl(filepath: Path) -> dict:
    """
    Parse a session JSONL file and aggregate usage data.
    Returns dict with: model, prompt_tokens, output_tokens, cache_tokens,
                        cost_usd, timestamp, task_summary
    """
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_write = 0
    total_cost = 0.0
    model = None
    first_timestamp = None
    task_summary = None

    try:
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")

                # Grab session timestamp
                if entry_type == "session" and not first_timestamp:
                    ts = entry.get("timestamp")
                    if ts:
                        try:
                            first_timestamp = int(
                                datetime.fromisoformat(
                                    ts.replace("Z", "+00:00")
                                ).timestamp()
                                * 1000
                            )
                        except Exception:
                            pass

                # Extract usage from assistant messages
                if entry_type == "message":
                    msg = entry.get("message", {})
                    if not isinstance(msg, dict):
                        continue

                    # Get model from first assistant message
                    if msg.get("role") == "assistant" and not model:
                        model = msg.get("model")

                    # Extract task summary from first user message
                    if msg.get("role") == "user" and not task_summary:
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            task_summary = content[:200]
                        elif isinstance(content, list):
                            for part in content:
                                if isinstance(part, dict) and part.get("type") == "text":
                                    task_summary = part.get("text", "")[:200]
                                    break

                    usage = msg.get("usage", {})
                    if usage:
                        total_input += usage.get("input", 0)
                        total_output += usage.get("output", 0)
                        total_cache_read += usage.get("cacheRead", 0)
                        total_cache_write += usage.get("cacheWrite", 0)
                        cost = usage.get("cost", {})
                        if isinstance(cost, dict):
                            total_cost += cost.get("total", 0)
                        elif isinstance(cost, (int, float)):
                            total_cost += cost

    except Exception as e:
        return None

    if total_input == 0 and total_output == 0 and total_cache_read == 0:
        return None

    return {
        "model": model or "unknown",
        "prompt_tokens": total_input,
        "output_tokens": total_output,
        "cache_tokens": total_cache_read + total_cache_write,
        "cost_usd": round(total_cost, 6),
        "timestamp": first_timestamp or 0,
        "task_summary": task_summary,
    }


def init_db():
    """Ensure the runs table exists."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            agent_id TEXT NOT NULL,
            session_key TEXT,
            model TEXT NOT NULL,
            task_summary TEXT,
            prompt_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0,
            timestamp INTEGER NOT NULL
        )"""
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON runs(timestamp)"
    )
    conn.commit()
    conn.close()


def get_existing_ids(conn) -> set:
    """Get set of already-inserted run IDs."""
    cursor = conn.execute("SELECT id FROM runs")
    return {row[0] for row in cursor.fetchall()}


def main():
    init_db()

    # Load session key → session ID mapping
    if not SESSIONS_JSON.exists():
        print("ERROR: sessions.json not found")
        return

    with open(SESSIONS_JSON) as f:
        sessions_meta = json.load(f)

    # Build session_id → session_key mapping
    id_to_key = {}
    for key, meta in sessions_meta.items():
        sid = meta.get("sessionId", "")
        if sid:
            id_to_key[sid] = key

    # Get all JSONL files (active + deleted for historical data)
    jsonl_files = list(SESSIONS_DIR.glob("*.jsonl"))
    # Also include .deleted files for history
    jsonl_files += list(SESSIONS_DIR.glob("*.jsonl.deleted.*"))

    print(f"Found {len(jsonl_files)} session files to scan")
    print(f"Session keys in registry: {len(sessions_meta)}")

    conn = sqlite3.connect(DB_PATH)
    existing_ids = get_existing_ids(conn)
    print(f"Already in DB: {len(existing_ids)} rows")

    inserted = 0
    skipped = 0
    errors = 0

    for filepath in jsonl_files:
        # Extract session ID from filename
        # Format: UUID.jsonl or UUID-topic-XXXX.jsonl or UUID.jsonl.deleted.TIMESTAMP
        fname = filepath.name
        # Get just the UUID part
        session_id = fname.split(".jsonl")[0]
        # Handle topic suffixes: UUID-topic-XXXX
        base_id = session_id.split("-topic-")[0] if "-topic-" in session_id else session_id

        # Create a unique run ID from the file path (handles duplicates)
        run_id = hashlib.md5(fname.encode()).hexdigest()[:16]

        if run_id in existing_ids:
            skipped += 1
            continue

        # Find session key
        session_key = id_to_key.get(base_id, "")
        if not session_key:
            # Try the full session_id with topic
            session_key = id_to_key.get(session_id, "")
        if not session_key:
            # Derive from filename patterns if possible
            if "-topic-" in session_id:
                # Could be a group topic - check if we can find it
                for key, meta in sessions_meta.items():
                    if meta.get("sessionId") == base_id:
                        session_key = key
                        break

        agent_id = get_agent_id(session_key) if session_key else "unknown"

        # Parse the JSONL file for usage data
        result = parse_session_jsonl(filepath)
        if not result:
            continue

        try:
            conn.execute(
                """INSERT OR IGNORE INTO runs
                   (id, agent_id, session_key, model, task_summary,
                    prompt_tokens, output_tokens, cache_tokens, cost_usd, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    run_id,
                    agent_id,
                    session_key,
                    result["model"],
                    result["task_summary"],
                    result["prompt_tokens"],
                    result["output_tokens"],
                    result["cache_tokens"],
                    result["cost_usd"],
                    result["timestamp"],
                ),
            )
            inserted += 1
        except Exception as e:
            errors += 1

    conn.commit()

    # Print summary stats
    total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    total_cost = conn.execute("SELECT SUM(cost_usd) FROM runs").fetchone()[0] or 0
    total_prompt = conn.execute("SELECT SUM(prompt_tokens) FROM runs").fetchone()[0] or 0
    total_output = conn.execute("SELECT SUM(output_tokens) FROM runs").fetchone()[0] or 0
    total_cache = conn.execute("SELECT SUM(cache_tokens) FROM runs").fetchone()[0] or 0

    # Per-agent breakdown
    agent_stats = conn.execute(
        """SELECT agent_id, COUNT(*), SUM(cost_usd), SUM(prompt_tokens), SUM(output_tokens)
           FROM runs GROUP BY agent_id ORDER BY SUM(cost_usd) DESC"""
    ).fetchall()

    # Per-model breakdown
    model_stats = conn.execute(
        """SELECT model, COUNT(*), SUM(cost_usd)
           FROM runs GROUP BY model ORDER BY SUM(cost_usd) DESC"""
    ).fetchall()

    conn.close()

    print(f"\n{'='*50}")
    print(f"Sync complete:")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped (already in DB): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  Total rows in DB: {total}")
    print(f"\nToken Usage:")
    print(f"  Prompt tokens:  {total_prompt:>12,}")
    print(f"  Output tokens:  {total_output:>12,}")
    print(f"  Cache tokens:   {total_cache:>12,}")
    print(f"  Total cost:     ${total_cost:>11,.4f}")

    print(f"\nPer-Agent Breakdown:")
    for agent_id, count, cost, prompt, output in agent_stats:
        cost = cost or 0
        print(f"  {agent_id:<25} {count:>5} runs  ${cost:>9,.4f}  ({prompt or 0:,} in / {output or 0:,} out)")

    print(f"\nPer-Model Breakdown:")
    for model, count, cost in model_stats:
        cost = cost or 0
        print(f"  {model:<30} {count:>5} runs  ${cost:>9,.4f}")


if __name__ == "__main__":
    main()
