# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-10

First stable release. Full replay analysis pipeline with deterministic metrics, AI coaching, and PDF reports.

### Added

#### Core
- Replay parser for AoE2 DE `.aoe2record` files (mgz-based)
- SQLite storage with normalized schema (matches, players, age_ups, units, researches, buildings)
- CLI interface (`ingest`, `report`, `stats`, `patterns`)

#### Metrics (Deterministic)
- Age-up times (Feudal, Castle, Imperial) — comparative per player
- Army composition — unit production by player (top 8, eco filtered)
- TC idle time — total + **by era** (Dark/Feudal/Castle/Imperial)
- TC idle v3 — queue simulation model (batch-aware, research-aware, multi-TC)
- Opening detection — 12+ categories (Scout Rush, Fast Castle, M@A, Drush, etc.)
- Farm gap average — reseeding efficiency
- Military timing index — rush vs boom classification
- Estimated idle villager time (proxy metric)
- Villager production rate by age
- Resource collection efficiency (res/villager)
- TC count progression
- eAPM (effective actions per minute)
- Production buildings by age (Rax, Stable, Range, Siege by era)
- Housed count detection
- Walling tiles by age (inspired by [AgeAlyser](https://github.com/byrnesy924/AgeAlyser_2), MIT)
- Key tech timings with Good/Poor assessment

#### AI Analysis (3 tiers)
- **Match Report** — deterministic text report with all metrics
- **AI Analysis** — LLM-powered analysis (timeline, chain causality, benchmarks, insights, score)
- **Deep Coach** — forensic analysis with Knowledge Base enrichment (matchup theory, player profile, coaching rules, cross-match patterns, action plan)

#### Knowledge Base
- Civilization data (strengths, weaknesses, counters)
- Matchup theory database
- ELO bracket benchmarks
- Coaching rules engine (condition → suggestion)
- Player profile with trend tracking
- Auto-promotion pipeline (patterns → KB)

#### PDF Reports
- Match Report PDF — 4 pages (dashboard KPIs, economy, military, infrastructure)
- AI Analysis PDF — blue accent, markdown-to-PDF renderer with score box
- Deep Coach PDF — purple accent, extended forensic format
- Charts: seaborn + pandas (age-up timeline, TC idle by era, army composition, walling, tech timings)

#### Integration
- OpenClaw watcher — auto-detect new replays via Linux cron (2min interval)
- Telegram notifications with inline buttons (Report / AI Analysis / Deep Coach / Day Menu / Stats)
- Audio service support (TTS delivery of reports)

#### Infrastructure
- Git repo with feature branch workflow
- Automated re-ingestion on parser updates
- Cross-game statistics aggregation
- Pattern detection system (5 phases)

### Credits
- TC idle queue simulation model inspired by replay analysis concepts
- Walling tile analysis inspired by [AgeAlyser](https://github.com/byrnesy924/AgeAlyser_2) by byrnesy924 (MIT License)
- Opening detection categories referenced from AgeAlyser's build order classification
