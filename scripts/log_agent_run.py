#!/usr/bin/env python3
"""
Log an agent run to agent_runs.db
Usage:
  python3 scripts/log_agent_run.py --start --job "X Scanner" --agent-id x-scanner
  python3 scripts/log_agent_run.py --finish --run-id <id> --status ok --summary "33 tweets"
  python3 scripts/log_agent_run.py --oneshot --job "X Scanner" --agent-id x-scanner --status ok --summary "33 tweets"
"""
import argparse, sqlite3, uuid, json
from datetime import datetime
from pathlib import Path

DB = Path("./data/agent_runs.db")

def start_run(job_name, agent_id):
    conn = sqlite3.connect(DB)
    run_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO runs (id, job_name, agent_id, started_at, status)
        VALUES (?, ?, ?, ?, 'running')
    """, (run_id, job_name, agent_id, int(datetime.utcnow().timestamp())))
    conn.commit()
    conn.close()
    print(run_id)  # print so caller can capture
    return run_id

def finish_run(run_id, status, summary=None, error=None):
    conn = sqlite3.connect(DB)
    conn.execute("""
        UPDATE runs SET ended_at=?, status=?, summary=?, error=? WHERE id=?
    """, (int(datetime.utcnow().timestamp()), status, summary, error, run_id))
    conn.commit()
    conn.close()

def oneshot(job_name, agent_id, status, summary=None, error=None):
    conn = sqlite3.connect(DB)
    run_id = str(uuid.uuid4())
    now = int(datetime.utcnow().timestamp())
    conn.execute("""
        INSERT INTO runs (id, job_name, agent_id, started_at, ended_at, status, summary, error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (run_id, job_name, agent_id, now, now, status, summary, error))
    conn.commit()
    conn.close()
    print(f"Logged run: {job_name} [{status}]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--finish", action="store_true")
    parser.add_argument("--oneshot", action="store_true")
    parser.add_argument("--job", help="Job name")
    parser.add_argument("--agent-id", default="theo-main")
    parser.add_argument("--run-id", help="Run ID (for --finish)")
    parser.add_argument("--status", default="ok")
    parser.add_argument("--summary")
    parser.add_argument("--error")
    args = parser.parse_args()

    if args.start:
        start_run(args.job, args.agent_id)
    elif args.finish:
        finish_run(args.run_id, args.status, args.summary, args.error)
    elif args.oneshot:
        oneshot(args.job, args.agent_id, args.status, args.summary, args.error)
