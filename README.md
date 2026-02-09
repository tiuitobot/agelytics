# Agelytics 📊⚔️

**Age of Empires 2 DE Replay Analyzer**

Local-first, 100% Python AoE2 DE replay parser and statistics tracker. No external APIs required.

## Features

- 🎮 Parse `.aoe2record` replay files using the `mgz` library
- 💾 Store match data in SQLite with automatic deduplication (file hash)
- 📈 Generate detailed post-match reports with ELO, civs, and results
- 🏆 Track player evolution, win rates, and favorite civilizations
- 🗺️ Support for 50+ map types and 45+ civilization mappings
- ⚡ Fast CLI with zero external API dependencies

## Installation

```bash
git clone https://github.com/tiuitobot/agelytics.git
cd agelytics
pip install -e .
```

### Requirements

- Python 3.8+
- `mgz` library (installed automatically via pip)

## Usage

### Ingest Replays

Import replay files into the database:

```bash
# Import all replays from AoE2 DE savegame folder
agelytics ingest "/path/to/Age of Empires 2 DE/76561198028659538/savegame/"

# Import a single replay
agelytics ingest match.aoe2record

# Verbose output
agelytics ingest /path/to/savegame/ -v
```

### View Match Reports

Show detailed information about a match:

```bash
# Show last match
agelytics report --last

# Show specific match by ID
agelytics report --id 42

# Show from a specific player's perspective
agelytics report --last -p YourPlayerName

# List all matches (compact table)
agelytics report --all -p YourPlayerName
```

**Example output:**

```
════════════════════════════════════════
  AGELYTICS — Match Report
════════════════════════════════════════

  🏆 VITÓRIA
  blzulian (Franks) vs opponent (Italians)

  📅 2026-02-09 14:35
  🗺️  Arabia
  ⏱️  45:58
  🎮 1v1 | RM | Fast

  ────────────────────────────────────
  Players:
  👑 blzulian — Franks (ELO 598, eAPM 45) ◄
     opponent — Italians (ELO 605, eAPM 52)
  📊 ELO gap: +7 (opponent higher)
  ────────────────────────────────────
```

### Player Statistics

View aggregate stats for a player:

```bash
agelytics stats YourPlayerName
```

**Example output:**

```
════════════════════════════════════════
  AGELYTICS — Player: blzulian
════════════════════════════════════════

  Matches: 141 (78W / 63L)
  Win rate: 55.3%
  ELO: 598 (min 420, max 652)
  Avg eAPM: 43

  Top civs:
    Franks: 35 games (60% WR)
    Britons: 28 games (54% WR)
    Mayans: 18 games (50% WR)
```

## Running as Module

You can also run Agelytics as a Python module:

```bash
python -m agelytics ingest /path/to/savegame/
python -m agelytics report --last
python -m agelytics stats PlayerName
```

## Data Storage

- Database: `data/aoe2_matches.db` (SQLite)
- Automatic deduplication by file hash
- Indexed for fast queries by player name and date

## Dependencies

- **mgz**: Python library for parsing AoE2 DE `.mgz`/`.aoe2record` files
- **sqlite3**: Built-in Python SQLite support (no external database needed)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Feel free to open issues or pull requests.

---

**Built with ❤️ for the AoE2 community**
