#!/usr/bin/env python3
"""
Log a social media post to social_analytics.db
Usage: python3 scripts/log_social_post.py --platform twitter --post-id <id> --content "text" --type reply --url "https://..."
"""
import argparse, sqlite3, uuid
from datetime import datetime
from pathlib import Path

DB = Path("./data/social_analytics.db")

def log_post(platform, post_id, content, post_type, agent_id, url=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    row_id = str(uuid.uuid4())
    cur.execute("""
        INSERT OR IGNORE INTO posts (id, platform, post_id, content, posted_at, post_type, agent_id, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (row_id, platform, post_id, content, int(datetime.utcnow().timestamp()), post_type, agent_id, url))
    conn.commit()
    conn.close()
    print(f"Logged post {post_id} ({post_type}) to social_analytics.db")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="twitter")
    parser.add_argument("--post-id", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--type", dest="post_type", default="reply")
    parser.add_argument("--agent-id", default="theo-main")
    parser.add_argument("--url")
    args = parser.parse_args()
    log_post(args.platform, args.post_id, args.content, args.post_type, args.agent_id, args.url)
