# Agent Instructions — Persistent Memory Protocol

> Copy the relevant sections below into your agent's system prompt or workspace config (AGENTS.md, CLAUDE.md, etc.)

---

## Write Protocol (MANDATORY — after every meaningful task)

1. **Append to your daily agent log:**
   ```bash
   python3 scripts/write_agent_memory.py --agent-id <your-agent-id> --entry "Brief summary of what was done, found, decided"
   ```
   File lands in: `memory/agents/<your-agent-id>/YYYY-MM-DD.md`

2. **Update relevant shared-brain JSON** if your task has cross-agent value:
   - External signals → `shared-brain/intel-feed.json`
   - Cross-agent tasks → `shared-brain/agent-handoffs.json`
   - Published content → `shared-brain/content-vault.json`
   - New contacts → `shared-brain/outreach-log.json`

3. **If handing off to another agent** → append to `shared-brain/agent-handoffs.json`:
   ```json
   {
     "timestamp": "ISO-8601",
     "from": "agent-alpha",
     "to": "agent-beta",
     "task": "description",
     "status": "pending",
     "context": "relevant details"
   }
   ```

---

## Read Protocol (MANDATORY — before every task involving known context)

Boot injection runs automatically via `scripts/boot_agent.py --agent-id <your-agent-id>`.

If you need to manually check what was done recently:
```bash
# Last 2 days of your agent log
cat memory/agents/<your-agent-id>/$(date +%Y-%m-%d).md 2>/dev/null
cat memory/agents/<your-agent-id>/$(date -d yesterday +%Y-%m-%d).md 2>/dev/null

# Check agent handoffs
cat shared-brain/agent-handoffs.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
for e in d.get('entries', []):
    print(e['from'], '→', e['to'], ':', e['task'], '[' + e['status'] + ']')
"
```

---

## Shared Brain Files (what to read/write)

| File | Read when | Write when |
|------|-----------|------------|
| `intel-feed.json` | Before posting content, answering ecosystem questions | After scanning external sources |
| `agent-handoffs.json` | Starting any task | After spawning a task for another agent |
| `content-vault.json` | Before writing/publishing | After publishing content |
| `outreach-log.json` | Before contacting anyone | After any outreach |

---

## Boot Injection Directive

Add this to your agent's startup sequence:

```
Before doing anything else in a new session:
1. Run: python3 scripts/boot_agent.py --agent-id <your-agent-id>
2. Read the output — it contains your recent logs and shared brain state
3. This is your memory. Use it.
```

---

## Memory Maintenance (periodic)

Every few sessions, review and maintain:
1. Read recent `memory/agents/<id>/YYYY-MM-DD.md` files
2. Archive shared-brain files exceeding 500KB → `shared-brain/archive/`
3. Prune outdated entries from active shared-brain files

---

## Agent ID Convention

Choose a unique, descriptive agent ID:
```
main-assistant     # Primary conversational agent
content-scanner    # Social media monitoring
ecosystem-sync     # Data aggregation
chat-agent-alpha   # Per-channel chat agents
```

Use this ID consistently across:
- `write_agent_memory.py --agent-id`
- `boot_agent.py --agent-id`
- `shared-brain/*.json` entries (`lastUpdatedBy`, handoff `from`/`to`)
- `log_agent_run.py --agent-id`

---

## Write Guard Rules

- **Never write secrets** (API keys, passwords, private keys) to shared brain files
- `shared-brain/` is readable by all agents — treat as semi-public
- Per-agent memory dirs (`memory/agents/<id>/`) are private to that agent
- Max shared brain file: 500KB (archive old entries when exceeded)
- Daily logs are append-only — never overwrite previous entries

---

## Example: Wiring Into an OpenClaw Agent

In your `AGENTS.md` or system prompt:

```markdown
## Persistent Agent Memory v2 Protocol

### After Every Task
1. Log it: `python3 scripts/write_agent_memory.py --agent-id my-agent --entry "summary"`
2. Update shared brain if cross-agent relevant
3. Log handoff if spawning work for another agent

### Before Every Task
Boot injection loads your last 2 days + shared brain automatically.
If unsure about context, check your recent logs manually.

### Agent ID: my-agent
### Shared Brain Access: intel-feed.json, agent-handoffs.json
```

---

## Example: Wiring Into a Cron Job

At the end of your cron script:

```bash
# Log the run
python3 scripts/log_agent_run.py \
  --agent-id my-scanner \
  --task "Scanned 50 tweets, found 3 new signals" \
  --status completed

# Update shared brain
python3 scripts/write_agent_memory.py \
  --agent-id my-scanner \
  --entry "Scan complete: 3 new entries added to intel-feed.json"
```
