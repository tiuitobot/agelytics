# Agelytics Phase 2 Roadmap

> Determinístico primeiro, IA segundo.

## Overview

Phase 2 extends Agelytics from a replay analysis tool into a **real-time scouting assistant**
(v1.1.0) and a **population-level benchmark engine** (v1.2.0). v1.1.0 is fully deterministic;
v1.2.0 introduces the first ML components (xELO).

---

## v1.1.0 — Scouting Overlay + API Data Collection

### Objectives

1. Show a transparent in-game overlay with opponent intel when a match starts.
2. Integrate with the AoE4 public API for live player/match data.
3. Zero AI — all lookups are deterministic (API data + static knowledge base).

### Features

| Feature | Source | Notes |
|---|---|---|
| Opponent ELO, favorite civs, win-rate trend (30d) | API | `matchHistory` + `leaderboards` |
| Opening tendency (rush / boom / turtle / hybrid) | API + `opening.py` | Classify from recent match history |
| Civ pros/cons | Static KB (`knowledge/`) | Fully deterministic |
| Matchup favorability (civ vs civ, ELO-bucketed) | API + KB | Win % lookup table |
| Noob-friendly civ info toggle | Config | Optional; off by default for experienced players |
| Post-game overlay | — | **Stretch goal** — only if tech debt is low |

### Architecture

```
game.log (match start event)
        │
        ▼
  log_watcher.py ──► api_client.py ──► aoe-api.worldsedgelink.com
        │                                   (~570ms/req, no auth)
        ▼
  scouting_engine.py
   ├─ player_profile (ELO, civs, trend)
   ├─ opening_classifier (reuses opening.py)
   ├─ civ_kb (static lookup)
   └─ matchup_table (precomputed)
        │
        ▼
  overlay_ui.py (tkinter transparent window)
   └─ 10-min auto-hide timer
```

**Key decisions:**
- Python + tkinter for overlay (lightweight, no Electron overhead for v1).
- Game log polling to detect match start (no memory injection).
- API responses cached per session to avoid redundant calls.

### Dependencies

- `parser.py`, `db.py`, `opening.py` from v1.0.0
- `aoe-api.worldsedgelink.com` (public, no auth, no throttling detected)
- `knowledge/` civ KB (already exists)
- `tkinter` (stdlib) or optional Electron upgrade later

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| API goes down or adds auth | Overlay shows stale/no data | Graceful fallback: show cached data or "unavailable" |
| Game log format changes | Match detection breaks | Abstract log parser; version-pin game build |
| Overlay blocks game UI | UX problem | Configurable position + transparency + hotkey toggle |
| API latency spike (>2s) | Overlay feels slow | Async fetch; show skeleton UI immediately |

### Success Criteria

- [ ] Overlay appears within 5s of match start with opponent data
- [ ] Auto-hides after 10 minutes
- [ ] All displayed data is deterministic (no ML)
- [ ] Works on 1920×1080 and 2560×1440 without UI clipping
- [ ] Hotkey to manually show/hide

---

## v1.2.0 — Population Benchmarks + xELO

### Objectives

1. Build a replay corpus (~50k replays) for population-level analysis.
2. Compute hierarchical population benchmarks (L1–L4).
3. Introduce xELO (expected ELO) via XGBoost regression.
4. Track meta drift across patches.

### Data Collection

```
aoe-api blob storage (.gz replays)
        │
        ▼
  replay_downloader.py ──► ~50k replays (~35GB)
        │                    batch overnight (~7h parse)
        ▼
  parser.py ──► db.py (SQLite / DuckDB)
```

- Target: 50,000 replays minimum.
- Storage: ~35GB raw, parsed into structured DB.
- Schedule: overnight batch job (cron).

### Hierarchical Benchmarks (L1–L4)

| Level | Condition | Example |
|---|---|---|
| L1 | Global | "Average pop at 10min across all games" |
| L2 | By ELO bucket | "Average pop at 10min, 1200–1400 ELO" |
| L3 | By civ | "English pop at 10min, 1200–1400 ELO" |
| L4 | By civ + opening | "English longbow rush pop at 10min, 1200–1400" |

**Fallback rule:** If n < 30 at current level, fall back to parent level.

### xELO (Expected ELO)

- **Model:** XGBoost regression on replay features.
- **Features:** resource collection rates, pop curves, build order timing, APM proxies.
- **Clustering:** K-Means or HDBSCAN for player profile archetypes.
- **Output:** xELO score per player + archetype label.

### Meta Drift Detection

- Every replay tagged with `patch_version`.
- Rolling window: 60–90 days.
- Compare benchmark distributions pre/post patch.
- Alert when civ win-rate shifts > 2σ from rolling mean.

### Architecture

```
  replay_downloader.py
        │
        ▼
  parser.py ──► db.py
        │
        ├──► benchmark_engine.py (L1-L4 hierarchical)
        │         └─ fallback when n < 30
        │
        ├──► xelo_model.py (XGBoost + clustering)
        │         └─ train pipeline + inference
        │
        └──► meta_drift.py (patch-aware rolling stats)
```

### Dependencies

- `parser.py`, `db.py` from v1.0.0
- `xgboost`, `scikit-learn`, `pandas`
- Sufficient disk (~40GB) and overnight compute window
- Patch version mapping (manual or scraped)

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Replay format changes between patches | Parser breaks | Version-aware parser; test suite per patch |
| 50k replays insufficient for L4 granularity | Sparse buckets | Fallback rule (n < 30 → parent level) |
| xELO overfits to meta snapshot | Stale model | Retrain monthly; patch field in features |
| Blob storage access removed | No new replays | Cache aggressively; document alternative sources |
| 7h parse time blocks machine | Resource contention | Nice/ionice; run overnight only |

### Success Criteria

- [ ] ≥50k replays downloaded and parsed
- [ ] L1–L4 benchmarks computed with n ≥ 30 enforcement
- [ ] xELO model trained with R² > 0.6 on holdout set
- [ ] Meta drift alerts fire correctly on known patch boundaries
- [ ] Full pipeline runs unattended overnight

---

## v1.2.1 — Tactical Impact Analysis (Causal Inference)

### Objectives

1. Measure the **causal impact** of player tactics by comparing opponent's in-game metrics
   against their personal baseline (from downloaded replay history).
2. Present results with statistical confidence scoring (🟢🟡🔴).
3. Deliver instant post-game feedback: "Your scout rush reduced opponent eco by ~25%."

### Core Concept

The opponent's replay history serves as a **natural control group**. The current game is the
"treatment." The difference between observed metrics and opponent baseline = estimated tactical
impact.

```
Opponent baseline (N replays)     Current game
  avg vills@15min: 28               vills@15min: 21
  avg castle time: 16:30            castle time: 19:00
  avg TC idle: 12%                  TC idle: 25%
                                          │
                                          ▼
                              Tactical Impact Report
                    "Scout rush reduced eco by ~25% (🟢 high confidence)"
```

### Confidence Scoring

| Level | Criteria | Display |
|---|---|---|
| 🟢 High | n ≥ 30, \|z\| > 2.0 | "High confidence" |
| 🟡 Moderate | n ≥ 10, \|z\| > 1.5 | "Moderate confidence" |
| 🔴 Low | n < 10 or \|z\| < 1.5 | "Low confidence — treat as estimate" |

**Method:** z-score or Welch's t-test comparing observed value against opponent's distribution
(mean ± std). No heavy libraries needed — basic arithmetic with mean and standard deviation.

**UX:** Color indicator + one-line summary by default. Expandable detail: n, std dev,
confidence interval, z-score.

### Background Pipeline

```
overlay shows (10min) ──► overlay hides
                               │
                    replay_downloader.py (background thread)
                    downloads opponent replay history during game
                               │
                          game ends
                               │
                          parser.py processes opponent replays
                               │
                    tactical_impact.py compares metrics
                               │
                    Instant post-game report with confidence
```

**Key insight:** Download starts when overlay appears (opponent identified), parsing happens
in background during the game. By game end, baseline is ready → instant feedback.

### Metrics for Impact Analysis

- Villager count at key timestamps (10, 15, 20, 25 min)
- Age-up timings (Feudal, Castle, Imperial)
- TC idle percentage
- Military unit composition timings
- Resource collection rates
- Walling completion (if detectable)

### Dependencies

- v1.2.0 parser + benchmark infrastructure
- Opponent replay download pipeline (from v1.1.0 API client)
- Sufficient opponent history (n ≥ 10 for any analysis, n ≥ 30 for high confidence)

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Opponent has few replays (n < 10) | No baseline | Show 🔴 or skip metric; fallback to population benchmark |
| Causal attribution is imperfect (map/civ confounds) | Misleading conclusions | Disclaimer: "estimated impact"; condition on civ+map when n allows |
| Download time exceeds game length | Baseline not ready | Progressive analysis: start with whatever is ready, refine async |
| Opponent plays different style per civ | Baseline mismatch | Filter baseline by civ when n ≥ 10; fallback to all-civ baseline |

### Success Criteria

- [ ] Post-game tactical impact report within 30s of game end
- [ ] Confidence scoring (🟢🟡🔴) on every metric
- [ ] Expandable detail view with statistical backing
- [ ] Graceful degradation when opponent history is sparse
- [ ] Zero false "high confidence" claims (validated against known matchups)

---

## v1.3.0 — Multi-User Monitoring

### Objectives

1. Monitor any player's matches via API (no local replay files needed).
2. Run the full analysis pipeline (report + AI analysis + Deep Coach) for monitored players.
3. Deliver results via Telegram (or other configured channel).

### Features

| Feature | Description |
|---|---|
| Watchlist management | Add/remove players by username or profile ID |
| API-based match detection | Poll match history for new completed games |
| Replay download + parse | Fetch replay from blob storage → parser pipeline |
| Full report generation | Match Report PDF + AI Analysis + Deep Coach (same as local) |
| Telegram delivery | Send reports to configured chat when new match detected |
| Opponent scouting feed | "Player X played 10 games this week, practicing Mongols, switched to tower rush" |

### Architecture

```
  watchlist.json (player IDs + config)
        │
        ▼
  api_watcher.py (polls match history every N minutes)
        │
        ├── new match detected?
        │         │
        │         ▼
        │   replay_downloader.py (blob storage)
        │         │
        │         ▼
        │   parser.py ──► db.py
        │         │
        │         ▼
        │   report pipeline (PDF + AI + Deep Coach)
        │         │
        │         ▼
        │   delivery.py (Telegram / webhook)
        │
        └── no new match → sleep(interval)
```

**Key difference from v1.0.0 watcher:** Current watcher monitors local replay folder.
v1.3.0 watcher polls the API — no access to the monitored player's machine needed.

### Use Cases

- **Impress friends:** Monitor Lucas's Dota... just kidding. Monitor friends' AoE2 games,
  send them analysis they didn't ask for.
- **Pro player scouting:** Track recurring opponents — detect pattern changes, new openings,
  civ pool shifts over time.
- **Team coaching:** Coach monitors all team members, reviews reports centrally.
- **Self-monitoring on other devices:** Play on a different PC, reports still generated.

### Configuration

```json
{
  "watchlist": [
    {
      "profileId": "76561198...",
      "name": "Lucas",
      "pollInterval": 300,
      "reports": ["match", "ai"],
      "delivery": "telegram:chat_id"
    }
  ]
}
```

### Dependencies

- v1.1.0 API client (player profiles, match history)
- v1.2.0 parser infrastructure (replay download + parse)
- v1.2.1 tactical impact (optional — enables impact analysis for monitored players too)
- Telegram bot integration (already exists in v1.0.0)

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| API rate limits with many monitored players | Delayed detection | Stagger polls; batch requests; respect backoff |
| Replay unavailable (private/expired) | Missing analysis | Log and notify; retry once after delay |
| Storage growth with many players | Disk usage | Configurable retention; delete raw replays after parse |
| Notification spam | Annoyed users | Configurable: instant / daily digest / silent (just store) |

### Success Criteria

- [ ] Add player to watchlist, detect their next match within poll interval
- [ ] Full report generated without any local replay file
- [ ] Telegram delivery within 2 minutes of match completion + poll
- [ ] Handles 10+ monitored players without API throttling
- [ ] Configurable report tiers per player (match only / +AI / +Deep Coach)

---

## Release Sequence

```
v1.0.0 ──► v1.1.0 ──► v1.2.0 ──► v1.2.1 ──► v1.3.0
replay    scouting   benchmarks  tactical   multi-user
analysis  overlay    + xELO      impact     monitoring
determ    determ     determ+ML   determ+stats  determ
```

## Conventions

- **Semver** for all releases.
- **n ≥ 30** minimum sample size for any displayed statistic.
- **English** for all code, docs, and UI.
- **Max 200 lines** per module (split if exceeded).
