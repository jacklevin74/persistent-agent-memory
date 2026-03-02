# Persistent Agent Memory Architecture v2
**Author:** Theo  
**Date:** March 1, 2026  
**Status:** Design — Not Yet Implemented  
**Inspired by:** Vadim Strizheus' agent memory pattern (X, Mar 1 2026)

---

## Overview

Today, agents on this stack start each session with limited context — loaded from workspace files, heartbeat state, and manual memory searches. While functional, this is brittle: agents repeat work, lose cross-session continuity, and have no structured way to hand off state to each other.

This architecture formalizes a **4-layer persistent memory system** that gives every agent a reliable context injection before it touches any task, and a disciplined write protocol after. The goal: agents that compound instead of reset.

---

## Design Principles

1. **No middleware, no central server** — files and SQLite only. Same pattern that already works.
2. **Build on existing infrastructure** — QMD (semantic search), `session_recall.py` (identity/recall), `xchat-identity-registry.json` (wallet identity). Don't reinvent what works.
3. **Write after every task. Read before every task.** — Enforced via AGENTS.md protocol, not code.
4. **Per-agent scope + shared brain** — agents have private logs AND publish to shared state for cross-agent consumption.
5. **Startup injection is automatic** — agents never start cold. The boot script runs before first inference.

---

## Layer 1: Databases

### Existing (keep as-is)
| Database | Location | Purpose |
|----------|----------|---------|
| `x1_tokens.db` | `data/x1_tokens.db` | X1 token prices, pools, history |
| QMD index | `~/.local/share/qmd/` | Semantic search across workspace |

### New Databases to Create
| Database | Location | Purpose |
|----------|----------|---------|
| `knowledge.db` | `data/knowledge.db` | Agent-dropped facts with vector embeddings. Tables: `chunks`, `kb_entities`, `kb_sources`. Semantic retrieval via QMD (no re-inventing embedding layer). |
| `crm.db` | `data/crm.db` | Contact tracking for xChat/Telegram interactions. Tables: `contacts` (wallet/tg_id, name, first_seen, trust_level), `interactions` (timestamp, agent, channel, summary), `outreach_log` (who contacted, when, outcome). |
| `social_analytics.db` | `data/social_analytics.db` | Tweet/post performance over time. Tables: `posts` (tweet_id, text, posted_at, type), `performance` (tweet_id, checked_at, views, likes, rts, replies). SCRIBE reads this before writing. |
| `llm_usage.db` | `data/llm_usage.db` | Per-agent token and cost tracking. Tables: `runs` (agent_id, session_key, model, prompt_tokens, output_tokens, cache_tokens, cost_usd, timestamp). |
| `agent_runs.db` | `data/agent_runs.db` | Cron job and subagent execution history. Tables: `runs` (job_name, agent_id, started_at, ended_at, status, summary). |

---

## Layer 2: Per-Agent Memory Directories

Each agent gets a dedicated memory directory with daily `.md` log files. The agent appends to today's log after every task, and reads the last 2 days before starting.

### Directory Structure
```
memory/agents/
  theo-main/              ← Main Telegram/DM agent (current session)
    2026-03-01.md
    2026-02-28.md
    ...
  theo-xchat/             ← xChat agent (workspace-xchat)
    2026-03-01.md
    ...
  cyberdyne-director/     ← Cyberdyne group sessions
    2026-03-01.md
    ...
  vero-watcher/           ← Vero markets cron agent
    2026-03-01.md
    ...
  x1-token-sync/          ← Token DB hourly cron
    2026-03-01.md
    ...
  nightly-contemplation/  ← Opus reflection cron
    2026-03-01.md
    ...
  x-scanner/              ← X/Twitter intel cron
    2026-03-01.md
    ...
```

### Log Format (per entry)
```markdown
## [HH:MM HST] Task: <short description>
- What was done
- What was found / decided
- What to watch for next time
- Cross-agent writes: [list of shared brain files updated]
```

### Existing Per-User Memory (keep, extend)
`workspace-xchat/memory/users/{wallet-first-8}.md` stays. xChat agent continues writing here. The agent-level log (`theo-xchat/YYYY-MM-DD.md`) captures operational notes; the user files capture relationship context. Both get injected at startup.

---

## Layer 3: Shared Brain Files

Shared JSON files that agents write to after tasks and read before tasks. These are the cross-agent communication layer — no sessions_send required for state handoffs.

### File Registry

| File | Location | Owner (writes) | Readers | Content |
|------|----------|----------------|---------|---------|
| `intel-feed.json` | `shared-brain/intel-feed.json` | x-scanner cron (every 2h) | Cyberdyne director, main agent, SCRIBE analog | Hot X topics, trending X1 content, notable posts |
| `xchat-handoffs.json` | `shared-brain/xchat-handoffs.json` | xChat agent | xChat agent (next session) | Per-wallet session summaries — what was discussed, what's pending, last response |
| `cyberdyne-pulse.json` | `shared-brain/cyberdyne-pulse.json` | Cyberdyne group sessions | All Cyberdyne-adjacent agents | Builder scores, active citizen projects, group mood, recent rulings |
| `x1-ecosystem-state.json` | `shared-brain/x1-ecosystem-state.json` | Token sync cron | Any agent answering X1 questions | Current token prices, new listings, bridge state, validator health snapshot |
| `agent-handoffs.json` | `shared-brain/agent-handoffs.json` | All agents | All agents | Active cross-agent task queue — what was requested, by whom, status |
| `outreach-log.json` | `shared-brain/outreach-log.json` | Main agent, xChat agent | xChat agent, main agent | Who we've contacted, on what platform, what about — prevents repeating outreach |
| `content-vault.json` | `shared-brain/content-vault.json` | Main agent (after posting) | SCRIBE analog, main agent | Approved posts, engagement results, style patterns that worked |

### JSON Schema Conventions
- All files: `{ "lastUpdatedBy": "<agent-id>", "lastUpdatedAt": "<ISO>", "entries": [...] }`
- Entries always include: `{ "timestamp", "agent", "content", "tags": [] }`
- Max file size: 500KB. If exceeded, agent archives old entries to `shared-brain/archive/` and starts fresh.

---

## Layer 4: Startup Injection (Boot Script)

Every agent session, before first inference, runs `scripts/boot_agent.py`. This replaces the current ad-hoc "read HANDOFF.md" heartbeat pattern with a structured, per-agent, automatic context prime.

### Boot Script Logic (`scripts/boot_agent.py`)

```
1. Detect agent-id (from env var OPENCLAW_AGENT_ID or arg)
2. Load agent identity file (memory/agents/{agent-id}/IDENTITY.md if exists)
3. Read last 2 days of memory/agents/{agent-id}/YYYY-MM-DD.md
4. Load relevant shared brain JSONs based on agent-role mapping (see below)
5. Load per-user context if applicable (xchat: wallet lookup → user file)
6. Return structured context block → injected into system prompt
```

### Agent → Shared Brain Mapping

| Agent | Shared Brain Files Loaded |
|-------|--------------------------|
| `theo-main` | `intel-feed.json`, `agent-handoffs.json`, `x1-ecosystem-state.json` |
| `theo-xchat` | `xchat-handoffs.json`, `outreach-log.json`, `x1-ecosystem-state.json` |
| `cyberdyne-director` | `cyberdyne-pulse.json`, `intel-feed.json`, `agent-handoffs.json` |
| `vero-watcher` | `x1-ecosystem-state.json` |
| `x1-token-sync` | `x1-ecosystem-state.json` (writes only) |
| `x-scanner` | `intel-feed.json` (writes only), `content-vault.json` |

### Integration with Existing `session_recall.py`
`session_recall.py` handles identity graph lookups (focal trust, CAST episodes). `boot_agent.py` handles operational context (what the agent has been doing). They run sequentially — recall first, then boot — and both outputs are merged into the pre-inference context block.

---

## Write Protocol (Discipline Layer)

Architecture is only as good as the discipline enforcing it. These rules go into AGENTS.md for all agents:

### After Every Meaningful Task
```
1. Append to memory/agents/{my-agent-id}/YYYY-MM-DD.md
2. Update any relevant shared-brain/*.json files
3. If a cross-agent handoff is needed → append to agent-handoffs.json
```

### Before Every Task
```
1. boot_agent.py has already injected context (automatic)
2. If task involves a known person → check crm.db or xchat user file
3. If task involves X1 ecosystem → check x1-ecosystem-state.json
```

### Write Guard Rules
- Never write private data (private keys, personal info) to shared brain files
- shared-brain/ files are readable by all agents — treat as semi-public
- Per-agent memory dirs are private to that agent
- `xchat-handoffs.json` contains wallet addresses → never expose outside xchat workspace

---

## Open Questions (Resolve Before Implementation)

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | Who owns `intel-feed.json`? | New dedicated cron vs. repurpose heartbeat | New cron, every 2h, lightweight `theobird` scan |
| 2 | xChat per-wallet context location? | Stay in `workspace-xchat/memory/users/` vs. shared brain | Keep in xchat workspace — wallet addresses must stay scoped |
| 3 | LLM cost tracking source? | Pull from session stats API vs. instrument per-agent | Start with session stats API (already available), instrument later |
| 4 | Boot script entry point? | Modify `session_recall.py` vs. new `boot_agent.py` | New `boot_agent.py` — keep concerns separate |
| 5 | `knowledge.db` embedding backend? | SQLite-vec vs. QMD | QMD — already running, don't duplicate the embedding infra |
| 6 | `crm.db` scope? | xChat only vs. all channels | All channels — dedup contacts across Telegram, xChat, WhatsApp |

---

## Implementation Phases

### Phase 1 — Foundation (1 subagent pass)
- Create `data/` DB files with schemas (knowledge, crm, social_analytics, llm_usage, agent_runs)
- Create `memory/agents/` directory structure
- Create `shared-brain/` with empty JSON stubs for all 7 files
- Write `scripts/boot_agent.py` with hardcoded agent-role mappings

### Phase 2 — Agent Integration (1-2 subagent passes)
- Update AGENTS.md with write protocol rules
- Wire `boot_agent.py` into HEARTBEAT.md and main session start
- Update `workspace-xchat/AGENTS.md` to write `xchat-handoffs.json` after sessions
- Update Cyberdyne group sessions to write `cyberdyne-pulse.json`

### Phase 3 — Intelligence Layer (1 subagent pass)
- Create x-scanner cron (every 2h, `theobird` → `intel-feed.json`)
- Token sync cron writes to `x1-ecosystem-state.json`
- Wire `social_analytics.db` to post-publish flow on @TheoThePrime_AI

### Phase 4 — CRM + Analytics (future)
- Populate `crm.db` from existing xChat session transcripts
- `social_analytics.db` backfill from tweet archive
- Dashboard for LLM cost tracking by agent

---

## Estimated Token Cost per Agent Boot

| Component | Chars | Tokens (approx) |
|-----------|-------|-----------------|
| Agent identity | ~500 | ~125 |
| Last 2 days logs | ~2,000 | ~500 |
| Shared brain JSONs (2-3 files) | ~3,000 | ~750 |
| Total overhead per session | ~5,500 | ~1,375 |

At $3/M tokens (opus), that's ~$0.004 per agent boot. Negligible.

---

## Summary

This is not a new system — it's a formalization of what we're already doing informally, with the gaps filled in. The xChat agent already writes per-wallet memory. Heartbeats already read daily logs. QMD already does semantic search. 

What's missing: the discipline layer (shared brain protocol), the automation (boot script), and a few missing DBs (CRM, analytics, usage). Three opus subagent passes to wire it up cleanly.

The result: agents that don't forget, don't repeat themselves, and hand off context to each other without human intervention. That's the actual agentic era.

---

*Architecture by Theo · March 1, 2026*  
*Implementation pending Jack's go-ahead*
