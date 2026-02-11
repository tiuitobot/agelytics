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

## Release Sequence

```
v1.0.0 (current)  ──►  v1.1.0 (overlay)  ──►  v1.2.0 (benchmarks)  ──►  v1.2.1 (impact)
   replay analysis      scouting 10min       population + xELO        causal inference
   deterministic        deterministic        determ + ML              determ + stats
```

## Conventions

- **Semver** for all releases.
- **n ≥ 30** minimum sample size for any displayed statistic.
- **English** for all code, docs, and UI.
- **Max 200 lines** per module (split if exceeded).
