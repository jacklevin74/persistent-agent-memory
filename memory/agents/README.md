# Per-Agent Memory Directories

Each agent in the Theo/OpenClaw stack has its own memory directory here.
Agents append daily log entries as `YYYY-MM-DD.md` files.

## Convention

- **One directory per agent-id** — matches the `--agent-id` used in `boot_agent.py`
- **Daily files** — `YYYY-MM-DD.md` (e.g. `2026-03-01.md`)
- **Append-only** — agents add timestamped entries, never delete
- **Private scope** — each agent's directory is only read by that agent (via boot script)

## Log Entry Format

```markdown
## [HH:MM HST] Task: <short description>
- What was done
- What was found / decided
- What to watch for next time
- Cross-agent writes: [list of shared brain files updated]
```

## Active Agents

| Directory | Agent | Purpose |
|-----------|-------|---------|
| `theo-main/` | Main Telegram/DM agent | Primary session |
| `theo-xchat/` | xChat agent | Wallet-based chat sessions |
| `cyberdyne-director/` | Cyberdyne group sessions | Community governance |
| `vero-watcher/` | Vero markets cron | Prediction market monitoring |
| `x1-token-sync/` | Token DB hourly cron | X1 token data sync |
| `nightly-contemplation/` | Opus reflection cron | Nightly self-reflection |
| `x-scanner/` | X/Twitter intel cron | Social intel gathering |

## Related

- **Shared brain:** `shared-brain/` — cross-agent state files
- **Boot script:** `scripts/boot_agent.py` — loads last 2 days + shared brain before each session
- **Write helper:** `scripts/write_agent_memory.py` — appends entries to daily log
