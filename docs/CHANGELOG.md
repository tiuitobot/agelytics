# Changelog

All notable changes to Agelytics are documented here.

## [Unreleased]

### Documented
- **Idle Villager Time** — investigação técnica concluiu que replays AoE2 não
  expõem idle villager data (apenas inputs do jogador, não estado do jogo).
  Documentado em `docs/IDLE_VILLAGER_LIMITATION.md` com proxies recomendados.

### Added
- **Knowledge Base** (`knowledge/aoe2/`)
  - `civilizations.json` — 10 civs with bonuses, strengths, weaknesses, counters
  - `benchmarks.json` — Age-up targets by ELO bracket (400-1200+)
  - `matchups.json` — 9 matchup entries with theory + strategy suggestions
  - `strategies.md` — Build orders (Scouts into Knights, Fast Castle, Archer Rush)
  - `coaching-rules.md` — 16 coaching rules (economy, military, age-up, matchup, cross-match)
  - `player-profile.json` — Auto-generated player analysis from patterns
- Professional documentation (`docs/ARCHITECTURE.md`, `docs/CHANGELOG.md`)
- Updated README with full architecture diagram, examples, and project structure

## 2026-02-09

### Added
- **Pattern Detection** (`patterns.py`)
  - Matchup winrate analysis (by civ pair)
  - Civ performance stats
  - Age-up time trends (recent vs older, improving/worsening/stable)
  - Military timing analysis
  - Economy health metrics (TC idle %, villager count)
  - ELO trend with linear regression
  - Map performance breakdown
  - CLI command: `agelytics patterns`
  - Auto-regeneration after each match via watcher
- **TC Idle Time** in deterministic reports
  - Calculated from villager queue gaps (>30s = idle)
  - `tc_idle_secs` column in `match_players` table
  - Displayed in Economy section of reports
- **Deep Coach** analysis tier
  - 🔬 Button in Telegram inline keyboard
  - Forensic-level analysis: action density, timeline, micro/macro, causal chains
  - Cross-match pattern detection
- **Deep Analysis Plan** (`plans/deep-analysis-v1.md`)
  - Action density curves, building/research timeline
  - Eco collapse detection algorithm
  - Coaching points generation
- **eAPM outlier fix** — Filter `eapm < 100` for avg calculation (drops had 577-721 eAPM)
- **Duration bug fix** — Matches 143/144 re-ingested as 145/146. Parser already correct (`duration_ms / 1000.0`)
- **Day menu button** in initial notification
- Watcher migrated from OpenClaw AI cron to pure Linux crontab (`*/2 * * * *`)

### Changed
- Notification buttons: added 🔬 Deep Coach alongside 🧠 Análise IA
- Watcher now regenerates patterns.json after each new match ingest

## 2026-02-08

### Added
- Initial release
- Replay parser (`parser.py`) using `mgz` library
- SQLite database (`db.py`) with full schema
- Report formatter (`report.py`) — match reports, player summaries, match tables
- Watcher (`watcher.py`) — new replay detection with Telegram notification
- CLI (`cli.py`) — `ingest`, `report`, `stats` commands
- 144 ranked 1v1 matches ingested
- GitHub repository: `tiuitobot/agelytics` (public, MIT)
