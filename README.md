# Agelytics

Age of Empires 2 DE replay analyzer. Local-first, no API dependencies.

## Features
- Parse .aoe2record replay files
- Store match data in SQLite
- Generate post-match reports (CLI)
- Track player evolution over time

## Quick Start
```bash
pip install -e .
agelytics ingest /path/to/savegame/
agelytics report --last
```

## License
MIT
