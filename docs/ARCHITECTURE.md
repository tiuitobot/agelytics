# Agelytics Architecture

## Design Philosophy

1. **Deterministic core, AI optional** — The basic pipeline (parse → store → report → patterns) is 100% Python with zero AI dependency. AI only enters at the analysis/coaching layer.

2. **Local-first, privacy-respecting** — All data stays on disk. No uploads, no external APIs for core functionality. Replays are read directly from the game's savegame folder.

3. **Layered architecture** — Each layer builds on the previous one. You can use Layer 1 alone (just reports) or all 4 layers (AI coaching with knowledge base).

## Data Flow

```
.aoe2record files (on disk)
        │
        ▼
   parser.py (mgz library)
        │ Extracts: players, civs, age-ups, units,
        │ techs, buildings, TC idle, duration, map
        ▼
     db.py (SQLite)
        │ Stores in normalized tables
        │ Deduplicates by file hash
        ▼
   ┌────┴────┐
   │         │
report.py  patterns.py
   │         │ Aggregates: matchup winrates,
   │         │ age-up trends, eco health,
   │         │ ELO trajectory
   │         ▼
   │    patterns.json
   │         │
   │    knowledge/aoe2/
   │    (benchmarks, civs, matchups,
   │     coaching rules, player profile)
   │         │
   └────┬────┘
        │
        ▼
   AI Analysis Layer (external)
   Deep Coach / Análise IA
   Consumes: match data + patterns + KB
   Produces: coaching insights, ratings
```

## Module Responsibilities

### parser.py
- Reads `.aoe2record` files using `mgz.summary.Summary`
- Extracts all deterministic data from the replay
- Handles: players, civilizations, age-ups, unit production, researches, buildings, TC idle time
- Filters: only ranked 1v1 multiplayer matches
- Returns a dict ready for `db.insert_match()`

### db.py
- SQLite storage with WAL mode for concurrent access
- Auto-creates tables on first connection
- Deduplication via `file_hash` (MD5 of first 64KB)
- Provides: `insert_match`, `get_match_by_id`, `get_player_stats`, `get_all_matches`

### report.py
- Formats match data into human-readable text reports
- Handles: match reports, player summaries, match tables
- Output is plain text (works in terminal and Telegram code blocks)

### patterns.py
- Aggregate queries over match history
- Functions: `matchup_stats`, `civ_stats`, `age_up_trends`, `military_timing`, `eco_health`, `elo_trend`, `map_performance`
- Generates `data/patterns.json` — consumed by AI layer and player profile
- 100% SQL/Python, no AI

### watcher.py
- Monitors replay directory for new files
- Triggered by Linux cron (every 2 minutes)
- On new match: parse → insert → regenerate patterns → Telegram notification
- Writes `pending_notifications.json` for audio summary pickup

### cli.py
- Argparse-based CLI: `ingest`, `report`, `stats`, `patterns`
- Entry point: `python -m agelytics` or `agelytics` (if installed)

## Knowledge Base

### Static Files (curated manually)
- `civilizations.json` — Civ data, bonuses, strengths, weaknesses
- `benchmarks.json` — Age-up targets by ELO bracket
- `matchups.json` — Matchup theory with counter strategies
- `strategies.md` — Build orders and principles
- `coaching-rules.md` — IF/THEN rule engine for automated suggestions

### Auto-generated
- `player-profile.json` — Derived from patterns.json after each match
- Contains: ELO trend, strengths, weaknesses, playstyle, best/worst maps

## Database Schema

```sql
matches (id, file_hash, file_path, played_at, duration_secs, 
         map_name, game_type, speed, pop_limit, resign_player, ...)

match_players (match_id, name, civ_name, elo, eapm, winner, tc_idle_secs, ...)

match_age_ups (match_id, player, age, timestamp_secs)

match_units (match_id, player, unit, count)

match_researches (match_id, player, tech, timestamp_secs)

match_buildings (match_id, player, building, count)
```

## Telegram Integration

### Notification Flow
```
watcher detects new replay
    → parse + ingest
    → send Telegram message with inline buttons:
      [📊 Report] [🧠 Análise IA] [🔬 Deep Coach]
      [📋 Menu do dia] [📈 Stats]
    → user clicks button
    → callback routed to appropriate handler
    → response sent back to user
```

### Callback Routing
- `agelytics_report_{id}` → Deterministic report
- `agelytics_analyze_{id}` → AI quick analysis
- `agelytics_deep_{id}` → AI forensic analysis
- `agelytics_stats` → Player stats
- `agelytics_day_{date}` → Day menu with match buttons
- `agelytics_ai_daily` → AI daily summary

## Limitations

- **mgz parser**: `has_achievements()=False` and `get_postgame()=None` for DE replays. All data comes from action log parsing.
- **TC idle calculation**: Currently measures gaps in villager queue commands. With multiple TCs, this is a rough proxy (not per-TC tracking yet).
- **Telegram message limit**: 4096 chars max per message. Long reports/analyses are split.
- **Replay format**: Only `.aoe2record` (DE format). Classic/HD not supported.
