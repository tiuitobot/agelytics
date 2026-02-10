# Bug Fix: Match 148 Empty action_log and Metrics

## Problem
Match 148 had:
- `action_log: []` (empty)
- `metrics: {}` (empty)
- Eco metrics returning None: `estimated_idle_villager_time`, `villager_production_rate_by_age`, `resource_collection_efficiency`

## Root Cause
The database fetching function `_match_with_players()` was NOT reconstructing:
1. The `action_log` field (needed by deep_coach)
2. The `metrics` dict (needed by analysis tools)
3. Helper data structures (`tc_idle`, `estimated_idle_villager_time`)

These were computed during parsing but not reconstructed when fetching from DB.

## Solution
Modified `agelytics/db.py` function `_match_with_players()` to:

1. **Reconstruct action_log** - Build formatted action log from stored age_ups and researches
2. **Reconstruct metrics** - Compute metrics dict for each player using:
   - Stored metric values from DB columns (farm_gap_average, military_timing_index, tc_count_final)
   - Computed values for metrics that can be derived (tc_idle_percent)
   - Helper data structures rebuilt from DB data
3. **Re-ingested match 148** - Deleted and re-parsed the replay to ensure all data is stored

## Results

### ✓ Fixed (all sources)
- `action_log`: 34 entries with formatted timestamps
- `metrics`: Dict populated for all players
- `estimated_idle_villager_time`: 253.8s (blzulian)
- `tc_idle_percent`: 57.68%
- `farm_gap_average`: 3.21s
- `military_timing_index`: 0.876
- `tc_count_progression`: [3 items]

### ⚠ Partial (works from fresh parse, None from DB)
- `villager_production_rate_by_age`: Requires `vill_queue_timestamps` (not stored in DB)
  - Fresh parse: `{'Dark Age': 1.73, 'Feudal Age': 1.39, 'Castle Age': 3.15, 'Imperial Age': 2.16}`
  - DB fetch: `None`

### ✗ Not available (missing source data)
- `resource_collection_efficiency`: Requires `resource_score` from mgz (not provided by library)
  - Returns `None` from both fresh parse and DB fetch

## Trade-offs
The solution prioritizes:
1. **Stored values** - Use pre-computed metrics from DB columns when available
2. **Graceful degradation** - Metrics return None if required data is missing
3. **No breaking changes** - Existing code continues to work

To get all metrics, parse replays fresh. DB-fetched matches will have most metrics but some may be None.

## Future Improvements
To fully support all metrics from DB:
1. Store `vill_queue_timestamps` as JSON in new column/table
2. Extract resource_score during parsing if mgz adds support
3. Consider storing enriched data (`_farm_build_timestamps`, etc.) for full metric reconstruction

## Commit
- SHA: 3b472c2
- Branch: master
- Pushed: 2026-02-10 18:20 BRT
