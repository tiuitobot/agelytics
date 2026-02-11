# OpenClaw Integration

AI-powered features that extend the Agelytics framework via [OpenClaw](https://github.com/openclaw/openclaw).

## What's Here

| File | Description |
|------|-------------|
| `watcher.py` | Watches for new replays, ingests, sends Telegram notifications with inline buttons |
| `watch_cron.sh` | Linux cron wrapper for the watcher (runs every 2 minutes) |

## What Lives in the OpenClaw Workspace

These files are in the OpenClaw workspace (not this repo), as they depend on the full agent infrastructure:

- **`scripts/agelytics_callback.sh`** — Routes Telegram button callbacks to appropriate handlers
- **Deep Coach prompts** — AI analysis using action log data + knowledge base
- **TTS summaries** — Voice post-match summaries via XTTS
- **Coaching rules evaluation** — LLM evaluates `knowledge/aoe2/coaching-rules.md` against match data

## Setup

1. Install Agelytics: `pip install -e /path/to/agelytics`
2. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`
3. Ensure `python3` is available (scripts assume `python3`, not `python`).
4. Add to crontab:
   ```bash
   */2 * * * * /path/to/agelytics/integrations/openclaw/watch_cron.sh
   ```

## Telegram Callback Flow

```
New replay detected
    → watcher.py parses + ingests + generates patterns
    → Sends Telegram notification:
      [📊 Report] [🧠 Análise IA] [🔬 Deep Coach]
      [📋 Menu do dia] [📈 Stats]
    → User clicks button
    → OpenClaw routes callback to handler
    → Response sent back
```

### Callback Patterns

| Pattern | Handler | Description |
|---------|---------|-------------|
| `agelytics_report_{id}` | Deterministic | Match report from CLI |
| `agelytics_analyze_{id}` | AI (Opus) | Quick coaching analysis |
| `agelytics_deep_{id}` | AI (Opus) | Forensic Deep Coach |
| `agelytics_stats` | Deterministic | Player stats from CLI |
| `agelytics_day_{date}` | Deterministic | Day match list |
| `agelytics_ai_daily` | AI (Opus) | Day summary with coaching |
