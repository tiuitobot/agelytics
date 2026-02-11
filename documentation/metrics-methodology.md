# Metrics Methodology — Agelytics

**Version:** 1.0  
**Last updated:** 2026-02-11  
**Rule:** Any metric change MUST update this file. No exceptions.

---

## Classification Legend

| Badge | Meaning | Definition |
|-------|---------|------------|
| ✅ | Deterministic | Directly computed from replay data, no estimation |
| 🔬 | Experimental | Uses heuristics or estimation, known limitations |
| 📐 | Derived | Computed from other metrics, inherits their classification |

---

## Match-Level Metrics

### TC Idle Time ✅
- **Definition:** Sum of gaps >5s between consecutive TC tasks (villager queue + TC researches)
- **Formula:** For each gap where `click_time > tc_free_at`: `idle += click_time - tc_free_at` (if gap >5s)
- **Multi-TC handling:** Task duration divided by TC count at that timestamp (simplified parallel queue)
- **Unit:** Seconds
- **Limitations:** Does not account for intentional idle (military micro trade-off). Does not detect housing-induced idle (TC blocked but not "idle").
- **Source:** Replay action log (Queue, Research commands)

### TC Idle by Era ✅
- **Definition:** TC Idle Time broken down by game era (Dark, Feudal, Castle, Imperial)
- **Era boundaries:** Player's age-up research completion timestamps
- **Inherits:** Same methodology as TC Idle Time

### TC Idle Breakdown (Intra-match) ✅
- **Definition:** Classification of individual TC idle gaps by duration
- **Categories:**
  - **Micro-idle (5-15s):** Brief lapses — improvable with build order practice
  - **Macro-idle (15-60s):** Extended gaps — typically military micro trade-offs
  - **AFK-idle (60s+):** Very long gaps — likely AFK, alt-tab, or tilt
- **Purpose:** Separates trainable skill gaps from noise
- **Reports:** Match Report, Deep Coach

### Housed Count 🔬
- **Definition:** Number of times player was likely housed (population cap hit)
- **Method:** Detects bursts of 2+ house builds within 10s of each other
- **Assumption:** Building 2+ houses in rapid succession indicates emergency response to housing
- **Limitations:** False positives in Dark Age (normal house building looks like burst). Does not detect housing without house-building response.
- **Source:** Replay action log (Build commands for Houses)

### Housed Time — Lower Bound 🔬
- **Definition:** Conservative estimate of time spent housed
- **Method:** Gaps in villager queue where 2+ houses were built during/shortly after the gap. Housed time = gap duration - villager train time (25s).
- **Bias:** Underestimates (only detects housing with evidence of house-building reaction)
- **By-era variant:** Same calculation, attributed to era based on gap midpoint timestamp
- **Limitations:** Misses housing events where player didn't build houses. False positives in Dark Age (normal expansion housing).

### Housed Time — Upper Bound 🔬
- **Definition:** Liberal estimate of time spent housed
- **Method:** Deterministic population timeline simulation:
  1. **Capacity timeline:** Starting TC (5 pop) + each house completion (+5, build time 25s) + each TC completion (+5, build time 150s)
  2. **Pop produced timeline:** Starting units (4) + each unit completion (Queue timestamp + unit train time)
  3. **Deaths timeline:** Player Delete commands (exact) + military death estimation (last action >120s before game end → dead at last_action + 60s)
  4. **Housing:** Each second where `pop_alive >= capacity` counts as housed
- **Bias:** Overestimates (cannot track combat deaths for villagers; military death estimation is conservative)
- **By-era variant:** Same calculation, attributed to era based on timestamp
- **Limitations:** Overestimates significantly in Castle/Imperial due to untracked combat deaths. Most reliable in Dark/Feudal.

### TC Idle Effective 📐
- **Definition:** Total TC production time lost, including housing
- **Formula:** `TC Idle + Housed Time`
- **Reported as range:** `[TC Idle + Housed Lower, TC Idle + Housed Upper]`
- **Confidence interpretation:** Narrow range = high confidence. Wide range = significant uncertainty (typically Castle+ with combat deaths).

### Housed Time Range Interpretation
- **Feudal:** Both bounds typically converge — **high confidence**
- **Dark Age:** Lower may show false positives (normal house building); upper is reliable (pop is trackable)
- **Castle/Imperial:** Upper inflates due to untracked deaths — **lower bound more reliable**
- **Cross-validation:** If upper < lower for an era, lower has false positives → discard lower for that era

---

## Player Metrics

### eAPM ✅
- **Definition:** Effective Actions Per Minute
- **Formula:** Total non-duplicate player commands / game duration in minutes
- **Source:** Replay action log (all input types)

### Age-up Times ✅
- **Definition:** Timestamp of each age advancement completion
- **Source:** Replay Research commands (Feudal Age, Castle Age, Imperial Age)
- **Unit:** Seconds from game start

### Opening Strategy 🔬
- **Definition:** Classified early-game military strategy
- **Method:** Pattern matching on first military units produced and key researches
- **Categories:** Straight Archers, M@A→Archers, Scouts, M@A→Scouts, FC, Drush, Tower Rush, etc.
- **Limitations:** Heuristic classification; edge cases may misclassify

### Wall Tiles by Era ✅
- **Definition:** Count of wall segments built per era
- **Source:** Replay Build commands for wall types

---

## Aggregate Metrics (Scouting Report)

### Win Rate ✅
- **Definition:** Games won / total games × 100
- **Data source rule:** If ≥5 1v1 matches available, use 1v1 only. Otherwise include TG with warning tag.

### Average Metrics (inter-match) 📐
- **Definition:** Central tendency across multiple matches
- **Method:** Winsorized mean (10%) OR median + IQR
- **Outlier handling:** Matches with values >2σ from mean flagged as outliers in charts
- **Applies to:** TC Idle, eAPM, Feudal time, Duration, Housed time

### ELO Evolution ✅ (with API) / 🔬 (replay only)
- **With API enrichment:** Real per-match ratings from aoe2companion API — deterministic
- **Replay only:** Static snapshot from replay header — same value across concurrent matches
- **Note in report:** "ELO from replay header (snapshot)" when API not available

### Civ Distribution ✅
- **Definition:** Frequency count of civilizations played

### Civ Win Rate ✅
- **Definition:** Win rate per civilization (minimum 2 games to display)

---

## Data Source Rules

| Scenario | Action |
|----------|--------|
| ≥5 1v1 matches | Use 1v1 only |
| <5 1v1 matches | Include TG + warning tag "⚠️ Includes TG data" |
| TG matches in charts | Marked with ★ marker (vs ● for 1v1) |
| API ELO available | Use API ratings (real per-match) |
| API ELO unavailable | Use replay header (static snapshot) + note |

---

## Report Badges

All reports must display:
- Badge (✅/🔬/📐) next to each metric
- Disclaimer page (final page) listing all metrics used with classification
- Methodology version number
- "Experimental metrics may change in future versions"

---

## Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-02-11 | Initial methodology. TC Idle, Housed dual-bound, eAPM, age-ups, openings, aggregate rules. |
