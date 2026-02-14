<!-- maintained by agent:agelytics -->
# Agelytics 📊⚔️

**AI-powered Age of Empires 2 DE replay analyzer, coaching system, and progress tracker.**

Local-first, privacy-respecting. Parses replays directly from disk — no external APIs, no uploads, no accounts.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Features

### Core (100% Python, zero AI)
- 🎮 Parse `.aoe2record` replay files using `mgz`
- 💾 SQLite storage with automatic deduplication
- 📊 Detailed post-match reports: age-ups, army composition, economy, key techs, TC idle time
- 📈 Player statistics: ELO tracking, winrates, civ distribution
- 🔍 Pattern detection: matchup stats, age-up trends, eco health, ELO trajectory
- 🗺️ 50+ map types, 45+ civilizations

### AI Analysis (requires LLM)
- 🧠 **Análise IA**: Quick match overview with coaching points and rating (1-10)
- 🔬 **Deep Coach**: Forensic-level analysis — action density, timeline, micro/macro, causal chains, cross-match patterns
- 📋 **Daily Summary**: AI-generated day overview with ELO progression and recurring patterns
- 🏫 **Knowledge Base**: Domain-specific coaching rules evaluated against your data

### Automation
- 🔄 **Watcher**: Linux cron detects new replays every 2 minutes
- 📱 **Telegram Integration**: Instant notifications with inline buttons for reports/analysis
- 🔊 **Voice Summaries**: TTS audio post-match summaries (optional)

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   Agelytics                       │
├──────────────────────────────────────────────────┤
│  Layer 1: Match Data (SQLite)                    │
│  parser.py → db.py → aoe2_matches.db            │
│  Deterministic. Every replay parsed identically. │
├──────────────────────────────────────────────────┤
│  Layer 2: Pattern Detection                      │
│  patterns.py → data/patterns.json                │
│  Aggregate stats, trends, correlations.          │
│  100% Python/SQL. Updated after each match.      │
├──────────────────────────────────────────────────┤
│  Layer 3: Knowledge Base                         │
│  knowledge/aoe2/*.json|md                        │
│  Civ data, benchmarks, matchups, coaching rules. │
│  Static (curated) + auto-generated (profiles).   │
├──────────────────────────────────────────────────┤
│  Layer 4: AI Analysis (optional)                 │
│  External LLM consumes Layers 1-3 as context.    │
│  Match data + patterns + KB → coaching insights. │
└──────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/tiuitobot/agelytics.git
cd agelytics
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Ingest replays
agelytics ingest "/path/to/Age of Empires 2 DE/<steam_id>/savegame/"

# View last match
agelytics report --last -p YourName

# View stats
agelytics stats YourName

# Generate patterns
agelytics patterns -p YourName
```

## Commands

### `ingest` — Import replay files

```bash
agelytics ingest /path/to/savegame/          # All replays in directory
agelytics ingest match.aoe2record             # Single file
agelytics ingest /path/to/savegame/ -v        # Verbose output
```

### `report` — Match reports

```bash
agelytics report --last -p blzulian           # Last match
agelytics report --id 145 -p blzulian         # Specific match
agelytics report --all -p blzulian            # List all matches
agelytics report --all -p blzulian --limit 20 # Limit results
```

### `stats` — Player statistics

```bash
agelytics stats blzulian
```

### `patterns` — Pattern analysis

```bash
agelytics patterns -p blzulian
```

Output includes: ELO trend, age-up trends, eco health, top civs, map performance, best/worst matchups.

## Report Example

```
════════════════════════════════════════
  AGELYTICS — Match Report
════════════════════════════════════════

  🏆 VITÓRIA
  blzulian (Franks) vs Ilyada555 (Italians)

  📅 2026-02-09 13:02 | 🗺️ Arabia | ⏱️ 45:58

  ⏫ Age-Up Times:
     Age          blzulian     Ilyada555
     Feudal       10:02        10:26
     Castle       23:00        20:37
     Imperial     41:21        —

  ⚔️ Army: Knight ×55, Spearman ×14, Militia ×12

  🏠 Economy:
     blzulian: 114 vills, 34 farms, TC idle 28:33
     Ilyada555: 103 vills, 25 farms, TC idle 26:32
```

## Knowledge Base

The `knowledge/aoe2/` directory contains domain-specific data:

| File | Description |
|------|-------------|
| `civilizations.json` | Civ bonuses, strengths, weaknesses, counters |
| `benchmarks.json` | Age-up targets by ELO bracket |
| `matchups.json` | Matchup theory + player winrate data |
| `strategies.md` | Build orders and principles |
| `coaching-rules.md` | IF/THEN coaching rule engine |
| `player-profile.json` | Auto-generated player analysis |

## Automated Watcher

For continuous monitoring, set up a Linux cron job:

```bash
# Run every 2 minutes
*/2 * * * * /path/to/agelytics/scripts/watch_cron.sh
```

The watcher:
1. Scans the replay directory for new files
2. Parses and ingests new matches
3. Regenerates pattern analysis
4. Sends Telegram notification with inline buttons (optional)

## Data Storage

```
data/
├── aoe2_matches.db        # SQLite database (all match data)
├── patterns.json           # Generated pattern analysis
└── watcher_state.json      # Watcher state (seen files)
```

### Database Schema

- `matches` — Game metadata (date, map, duration, speed, pop)
- `match_players` — Per-player data (civ, ELO, eAPM, winner, TC idle)
- `match_age_ups` — Age advancement timestamps
- `match_units` — Unit production counts
- `match_researches` — Technology research timestamps
- `match_buildings` — Building construction counts

## Requirements

- Python 3.8+
- `mgz` — AoE2 replay parser
- SQLite3 (built-in)
- Optional: Telegram Bot Token (for notifications)
- Optional: LLM API access (for AI analysis)

## Project Structure

```
agelytics/
├── agelytics/               # Core framework (deterministic, no AI)
│   ├── cli.py               #   CLI entry point
│   ├── parser.py            #   Replay file parser (mgz)
│   ├── db.py                #   SQLite storage layer
│   ├── report.py            #   Report formatting
│   ├── patterns.py          #   Pattern detection (aggregates)
│   └── data.py              #   Civ/map ID mappings
├── knowledge/               # Domain knowledge (generic, tracked)
│   └── aoe2/
│       ├── civilizations.json
│       ├── benchmarks.json
│       ├── matchups.json
│       ├── strategies.md
│       ├── coaching-rules.md
│       └── player-profile.json  ← auto-generated, gitignored
├── integrations/            # External integrations (optional)
│   └── openclaw/
│       ├── watcher.py       #   Replay watcher + Telegram notifications
│       └── watch_cron.sh    #   Linux cron wrapper
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   └── CHANGELOG.md
├── plans/                   # Design documents
├── data/                    # Personal data (gitignored)
│   ├── aoe2_matches.db      ← your match database
│   └── patterns.json         ← your pattern analysis
└── README.md
```

### Separation of Concerns

The repo contains **two distinct layers**:

1. **Core Framework** (`agelytics/` + `knowledge/`) — 100% deterministic Python. No AI, no external services. Install with `pip` and use the CLI. **Shareable with anyone.**

2. **Integrations** (`integrations/`) — Optional extensions for specific platforms. The OpenClaw integration adds Telegram notifications, AI analysis (Deep Coach), and voice summaries. **Requires OpenClaw + LLM.**

Personal data (`data/`, `player-profile.json`, `.env`) is gitignored. The repo ships clean.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Open issues or pull requests.

**Replay parsing** is deterministic and reproducible. AI analysis is optional and runs externally. This separation ensures the core tool is reliable and shareable.

---

**Built with ❤️ for the AoE2 community**
