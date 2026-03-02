import os
#!/usr/bin/env python3
"""Quick status check across all agent memory DBs"""
import sqlite3
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(os.environ.get("AGENT_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DBS = {
    "x1_tokens.db": ["tokens", "pools"],
    "knowledge.db": ["chunks", "kb_entities", "kb_sources"],
    "crm.db": ["contacts", "interactions", "outreach_log"],
    "social_analytics.db": ["posts", "performance"],
    "llm_usage.db": ["runs"],
    "agent_runs.db": ["runs"],
}

for db_name, tables in DBS.items():
    db_path = WORKSPACE / "data" / db_name
    if not db_path.exists():
        print(f"❌ {db_name}: NOT FOUND")
        continue
    try:
        conn = sqlite3.connect(db_path)
        parts = []
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            parts.append(f"{table}={count}")
        conn.close()
        size_kb = db_path.stat().st_size // 1024
        print(f"✅ {db_name} ({size_kb}KB): {', '.join(parts)}")
    except Exception as e:
        print(f"⚠️  {db_name}: {e}")
