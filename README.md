# Persistent Agent Memory

**A file-based architecture for stateful multi-agent systems.**

No middleware. No central server. Just SQLite, flat files, and a boot script.

> Agents that compound instead of reset.

📄 [Whitepaper (PDF)](persistent-agent-memory-whitepaper.pdf) · 🌐 [Architecture (HTML)](architecture.html)

---

## The Problem

LLM agents are stateless. Every session starts cold — no memory of prior work, no context from other agents, no operational history. RAG helps but it's reactive: you have to know what to search for. You can't search for what you forgot existed.

## The Solution

A 4-layer persistent memory system that gives every agent:
1. **Proactive context injection** at boot (not reactive retrieval)
2. **Enforced write-back** after every task
3. **Cross-agent state sharing** via filesystem (no message queues)

Cost: ~1,375 tokens per boot. About half a cent.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Layer 4: Boot Injection             │
│         boot_agent.py → pre-inference ctx        │
├─────────────────────────────────────────────────┤
│           Layer 3: Shared Brain (JSON)           │
│     Cross-agent state: intel, handoffs, vault    │
├─────────────────────────────────────────────────┤
│        Layer 2: Per-Agent Memory (Markdown)      │
│       memory/agents/{id}/YYYY-MM-DD.md           │
├─────────────────────────────────────────────────┤
│         Layer 1: Structured Storage (SQLite)     │
│   knowledge · crm · analytics · usage · runs     │
└─────────────────────────────────────────────────┘
```

### Layer 1: Databases

Five SQLite databases. No server, no setup.

| Database | Purpose |
|----------|---------|
| `knowledge.db` | Agent-contributed facts, semantic retrieval |
| `crm.db` | Contact tracking across channels |
| `social_analytics.db` | Post performance tracking |
| `llm_usage.db` | Per-agent token and cost tracking |
| `agent_runs.db` | Execution history for cron jobs and subagents |

### Layer 2: Per-Agent Memory

Each agent writes a daily markdown log. Reads last 2 days at startup.

```
memory/agents/
  agent-alpha/
    2026-03-01.md
    2026-03-02.md
  agent-beta/
    2026-03-02.md
```

Entry format:
```markdown
## [14:30] Task: Scanned X for ecosystem intel
- Found 33 tweets across 6 queries
- Updated shared-brain/intel-feed.json
- No high-signal finds, routine scan
```

### Layer 3: Shared Brain

Typed JSON files for async cross-agent communication. No direct messaging needed.

```
shared-brain/
  intel-feed.json          # External signal aggregation
  agent-handoffs.json      # Cross-agent task queue
  content-vault.json       # Published content + performance
  outreach-log.json        # Contact tracking
```

Schema convention:
```json
{
  "lastUpdatedBy": "agent-alpha",
  "lastUpdatedAt": "2026-03-02T07:00:00Z",
  "schemaVersion": "1.0",
  "entries": []
}
```

Max file size: 500KB. Auto-archive when exceeded.

### Layer 4: Boot Injection

`boot_agent.py` runs before first inference. Each agent loads only what's relevant:

```python
AGENT_BRAIN_MAP = {
    "agent-alpha": ["intel-feed.json", "agent-handoffs.json"],
    "agent-beta":  ["agent-handoffs.json", "outreach-log.json"],
    "scanner":     ["intel-feed.json", "content-vault.json"],
}
```

Token overhead:
| Component | Tokens |
|-----------|--------|
| Agent identity | ~125 |
| Last 2 days logs | ~500 |
| Shared brain (2-3 files) | ~750 |
| **Total** | **~1,375** |

At $3/M tokens: **~$0.004 per boot**.

---

## Quick Start

### 1. Initialize databases

```bash
python3 scripts/init_databases.py
```

### 2. Create agent memory directories

```bash
mkdir -p memory/agents/my-agent
```

### 3. Write after every task

```bash
python3 scripts/write_agent_memory.py \
  --agent-id my-agent \
  --entry "Did X, found Y, decided Z"
```

### 4. Boot before every session

```bash
python3 scripts/boot_agent.py --agent-id my-agent
```

### 5. Check status

```bash
python3 scripts/db_status.py
```

---

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `init_databases.py` | Create all 5 SQLite databases (idempotent) |
| `boot_agent.py` | Boot injection — load context for an agent |
| `write_agent_memory.py` | Append to an agent's daily log |
| `db_status.py` | Health check across all databases |
| `log_knowledge.py` | Add a knowledge chunk |
| `log_crm_contact.py` | Add/update a CRM contact |
| `log_social_post.py` | Log a social media post |
| `log_agent_run.py` | Log an agent/cron run |
| `sync_llm_usage.py` | Sync LLM usage from OpenClaw sessions |

---

## Write Protocol

Add to your agent's system instructions:

```
After every meaningful task:
1. Append to your daily agent log (write_agent_memory.py)
2. Update relevant shared-brain JSON if cross-agent value
3. If handing off to another agent → append to agent-handoffs.json
```

The key insight: **make writing trivial so compliance is high**. One CLI call per task.

---

## Comparison

| Approach | Proactive? | Infrastructure | Local-first? |
|----------|-----------|----------------|-------------|
| **This architecture** | ✅ Boot injection | None (files + SQLite) | ✅ |
| RAG only | ❌ Reactive | Vector DB | Depends |
| MemGPT / Letta | ✅ | Middleware server | ❌ |
| Pinecone / Weaviate | ❌ Reactive | Cloud service | ❌ |
| Read entire workspace | ✅ | None | ✅ (expensive) |

---

## Requirements

- Python 3.10+
- No external dependencies for core scripts (stdlib only)

---

## Status

**Implemented (Phases 1-3 live, Phase 4 future)**

- ✅ All 5 databases with schemas and write helpers
- ✅ Per-agent memory directories and daily log convention
- ✅ Shared brain JSON files with schema convention
- ✅ Boot injection script with agent-role mapping
- ✅ Write protocol enforced via agent instructions
- ✅ Intelligence layer (scanners, ecosystem state updater)
- ⬜ Phase 4: CRM backfill, archive import, cost dashboard

---

## License

MIT

---

*Architecture by Theo · March 2026 · Built on [OpenClaw](https://github.com/openclaw/openclaw)*
