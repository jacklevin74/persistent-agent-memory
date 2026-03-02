#!/usr/bin/env python3
"""
init_databases.py — Create all 5 Persistent Agent Memory v2 databases.
Idempotent: safe to re-run. Uses IF NOT EXISTS for all tables/indexes.
"""

import sqlite3
import os

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE, "data")


def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def init_knowledge_db():
    db_path = os.path.join(DATA_DIR, "knowledge.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source TEXT,
            agent_id TEXT,
            tags TEXT,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kb_entities (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            description TEXT,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kb_sources (
            id TEXT PRIMARY KEY,
            title TEXT,
            url TEXT,
            added_by TEXT,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_agent ON chunks(agent_id);
        CREATE INDEX IF NOT EXISTS idx_chunks_created ON chunks(created_at);
    """)
    conn.commit()
    conn.close()
    print(f"  ✓ knowledge.db ({db_path})")


def init_crm_db():
    db_path = os.path.join(DATA_DIR, "crm.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            wallet TEXT UNIQUE,
            telegram_id TEXT,
            telegram_username TEXT,
            name TEXT,
            channel TEXT,
            first_seen INTEGER NOT NULL,
            last_seen INTEGER NOT NULL,
            trust_level TEXT DEFAULT 'unknown',
            notes TEXT
        );
        CREATE TABLE IF NOT EXISTS interactions (
            id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            summary TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        );
        CREATE TABLE IF NOT EXISTS outreach_log (
            id TEXT PRIMARY KEY,
            contact_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            topic TEXT,
            outcome TEXT,
            timestamp INTEGER NOT NULL,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_contacts_wallet ON contacts(wallet);
        CREATE INDEX IF NOT EXISTS idx_contacts_tgid ON contacts(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_interactions_contact ON interactions(contact_id);
        CREATE INDEX IF NOT EXISTS idx_outreach_contact ON outreach_log(contact_id);
    """)
    conn.commit()
    conn.close()
    print(f"  ✓ crm.db ({db_path})")


def init_social_analytics_db():
    db_path = os.path.join(DATA_DIR, "social_analytics.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            post_id TEXT UNIQUE,
            content TEXT NOT NULL,
            posted_at INTEGER NOT NULL,
            post_type TEXT,
            agent_id TEXT,
            url TEXT
        );
        CREATE TABLE IF NOT EXISTS performance (
            id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            checked_at INTEGER NOT NULL,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        );
        CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform, posted_at);
        CREATE INDEX IF NOT EXISTS idx_perf_post ON performance(post_id);
    """)
    conn.commit()
    conn.close()
    print(f"  ✓ social_analytics.db ({db_path})")


def init_llm_usage_db():
    db_path = os.path.join(DATA_DIR, "llm_usage.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
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
        );
        CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_runs_model ON runs(model, timestamp);
    """)
    conn.commit()
    conn.close()
    print(f"  ✓ llm_usage.db ({db_path})")


def init_agent_runs_db():
    db_path = os.path.join(DATA_DIR, "agent_runs.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            job_name TEXT,
            agent_id TEXT NOT NULL,
            started_at INTEGER NOT NULL,
            ended_at INTEGER,
            status TEXT DEFAULT 'running',
            summary TEXT,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id, started_at);
        CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
    """)
    conn.commit()
    conn.close()
    print(f"  ✓ agent_runs.db ({db_path})")


def main():
    print("Initializing Persistent Agent Memory v2 databases...")
    ensure_dir()
    init_knowledge_db()
    init_crm_db()
    init_social_analytics_db()
    init_llm_usage_db()
    init_agent_runs_db()
    print("\nAll 5 databases created successfully.")


if __name__ == "__main__":
    main()
