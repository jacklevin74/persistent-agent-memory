#!/usr/bin/env python3
"""
Add or update a contact in crm.db
Usage: python3 scripts/log_crm_contact.py --name "Owl" --telegram-username "Owl_of_Atena" --channel telegram --trust focal
"""
import argparse, sqlite3, uuid
from datetime import datetime
from pathlib import Path

DB = Path("./data/crm.db")

def upsert_contact(name, wallet=None, telegram_id=None, telegram_username=None, channel=None, trust_level="known", notes=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Check if exists by telegram_username or wallet
    existing = None
    if telegram_username:
        cur.execute("SELECT id FROM contacts WHERE telegram_username=?", (telegram_username,))
        existing = cur.fetchone()
    if not existing and wallet:
        cur.execute("SELECT id FROM contacts WHERE wallet=?", (wallet,))
        existing = cur.fetchone()

    now = int(datetime.utcnow().timestamp())
    if existing:
        cur.execute("""
            UPDATE contacts SET name=?, telegram_id=?, telegram_username=?, wallet=?, channel=?,
            trust_level=?, notes=?, last_seen=? WHERE id=?
        """, (name, telegram_id, telegram_username, wallet, channel, trust_level, notes, now, existing[0]))
        print(f"Updated contact: {name}")
    else:
        contact_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO contacts (id, name, wallet, telegram_id, telegram_username, channel, first_seen, last_seen, trust_level, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (contact_id, name, wallet, telegram_id, telegram_username, channel, now, now, trust_level, notes))
        print(f"Added contact: {name}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--wallet")
    parser.add_argument("--telegram-id")
    parser.add_argument("--telegram-username")
    parser.add_argument("--channel", default="telegram")
    parser.add_argument("--trust", dest="trust_level", default="known")
    parser.add_argument("--notes")
    args = parser.parse_args()
    upsert_contact(args.name, args.wallet, args.telegram_id, args.telegram_username, args.channel, args.trust_level, args.notes)
