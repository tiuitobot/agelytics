# Domain Knowledge System — Template

**How to replicate the Agelytics knowledge system for any domain.**

This document abstracts the 4-layer pattern used in Agelytics into a reusable template. The same architecture works for any domain where you have structured data + want AI-powered insights.

---

## The Pattern

```
Layer 1: Raw Data (structured, deterministic)
    ↓ aggregation queries
Layer 2: Pattern Detection (statistical, no AI)
    ↓ auto-promotion (threshold-based)
Layer 3: Knowledge Base (curated + auto-generated)
    ↓ context injection
Layer 4: AI Analysis (LLM consumes Layers 1-3)
```

Each layer is independent. You can use Layer 1 alone, or all 4. AI is always optional.

---

## Layer 1: Raw Data

**What:** Structured storage of domain events/records.

**Implementation:** SQLite database with normalized tables.

**Template:**
```
data/
├── <domain>.db          # SQLite database
└── README.md            # Schema documentation
```

**AoE2 example:** `aoe2_matches.db` with tables `matches`, `match_players`, `match_age_ups`, `match_units`, `match_researches`, `match_buildings`.

**Requirements:**
- Deterministic parser (input → structured data)
- Deduplication (hash-based or ID-based)
- Indexed for fast queries

**Other domain examples:**
| Domain | Data Source | Storage |
|--------|-----------|---------|
| Cooking | Recipe attempts, ingredient substitutions | recipes.db |
| Finance | Transactions, investments, budgets | finance.db |
| Fitness | Workouts, measurements, sleep | fitness.db |
| Language Learning | Flashcards, quiz results, reading logs | language.db |
| Chess | PGN game files | chess_games.db |

---

## Layer 2: Pattern Detection

**What:** Aggregate queries that surface trends, correlations, and anomalies from raw data.

**Implementation:** Python module with SQL queries. Output: `data/patterns.json`.

**Template file:** `<project>/patterns.py`

**Required functions:**
```python
def generate_patterns(entity: str, db_path: str = None) -> dict:
    """Run all pattern queries and save to patterns.json."""
    
def format_patterns_text(patterns: dict) -> str:
    """Human-readable summary of patterns."""
```

**Standard pattern categories:**

| Category | What it detects | Example (AoE2) | Example (Cooking) |
|----------|----------------|-----------------|-------------------|
| **Performance by category** | Win/success rate by sub-type | Winrate per civ | Success rate per cuisine |
| **Trend analysis** | Metric improving/worsening over time | Age-up times | Cook time accuracy |
| **Cross-category stats** | Performance across dimensions | Map winrates | Weekday vs weekend cooking |
| **Health metrics** | Domain-specific quality indicators | TC idle %, eco collapse rate | Waste %, ingredient substitution success |
| **Trajectory** | Overall progress direction | ELO trend | Complexity score trend |
| **Matchup/comparison** | Performance against specific opponents/challenges | Civ vs civ winrate | Recipe difficulty vs success |

**Key principles:**
- 100% deterministic (Python/SQL only, zero AI)
- Fast enough to run after every new data point
- Output is JSON — consumable by both code and LLM

---

## Layer 3: Knowledge Base

**What:** Domain-specific knowledge, both curated (static) and auto-generated (from patterns).

**Implementation:** JSON + Markdown files in `knowledge/<domain>/`.

**Template structure:**
```
knowledge/<domain>/
├── README.md              # Index and meta-information
├── reference.json         # Core domain reference data (static, curated)
├── benchmarks.json        # Performance benchmarks by skill level
├── strategies.md          # Best practices, approaches, techniques
├── rules.md               # IF/THEN coaching/advisory rules
├── entity-profile.json    # Auto-generated from patterns (gitignored)
└── changelog.md           # Auto-generated promotion log
```

### File Types

**Static (tracked in git, manually curated):**
- `reference.json` — Domain entities with properties (civs, ingredients, exercises...)
- `benchmarks.json` — Performance targets by skill/experience level
- `strategies.md` — Best practices and approaches
- `rules.md` — Coaching/advisory rule engine

**Auto-generated (gitignored):**
- `entity-profile.json` — User/player profile derived from patterns
- `changelog.md` — Log of auto-promotions (can be tracked or gitignored)

### Coaching Rules Format

```markdown
| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| R1 | metric > threshold | "Actionable suggestion with {data}" | HIGH |
| R2 | trend == worsening | "Warning about regression" | MEDIUM |
```

Rules should be:
- Evaluable against data (not vague)
- Actionable (tell the user what to DO)
- Prioritized (CRITICAL > HIGH > MEDIUM > LOW)

---

## Layer 3.5: Auto-Promotion

**What:** Automatically update KB when patterns reach confidence thresholds.

**Implementation:** Function in `patterns.py` called after every pattern generation.

**Template:**
```python
def auto_promote(patterns: dict) -> list[str]:
    """Promote consistent patterns to Knowledge Base.
    
    Rules:
    - Category with >= N_MIN entries: add/update in reference data
    - New entity encountered >= N_MIN times: flag as missing
    - Log all changes to changelog.md
    
    Returns list of changes made.
    """
```

**Promotion rules by confidence:**

| Threshold | Action | Example |
|-----------|--------|---------|
| >= 5 occurrences | Auto-add statistical data | Matchup winrate |
| >= 3 occurrences | Flag as potentially interesting | New civ encountered |
| Trend confirmed over 10+ data points | Update profile | Age-up trend |
| Manual review | Add theoretical knowledge | Strategy suggestions |

**Key principle:** Auto-promote DATA (statistics, counts, rates). Never auto-promote THEORY (strategies, explanations). Theory requires human curation.

---

## Layer 4: AI Analysis

**What:** LLM consumes Layers 1-3 as context for domain-specific insights.

**Implementation:** Context builder that assembles a structured prompt.

**Template file:** `integrations/<platform>/analysis.py`

```python
def build_prompt(record_id: int, entity: str) -> str:
    """Build analysis prompt with full KB context.
    
    Loads:
    - Record data (from Layer 1)
    - Benchmarks for entity's level (from Layer 3)
    - Relevant reference data (from Layer 3)
    - Entity profile (from Layer 3, auto-generated)
    - Trends (from Layer 2)
    - Coaching rules (from Layer 3)
    - Raw detail data if available
    
    Returns structured prompt for LLM.
    """
```

**Analysis tiers:**
| Tier | Speed | Depth | Model |
|------|-------|-------|-------|
| Quick Overview | Fast | Surface | Haiku/Sonnet |
| Standard Analysis | Medium | Good | Sonnet |
| Deep/Forensic | Slow | Maximum | Opus |

**Prompt structure:**
1. Record summary (what happened)
2. Benchmarks (what was expected)
3. Reference data (domain context)
4. Entity profile (historical context)
5. Trends (trajectory context)
6. Detail data (raw events if available)
7. Coaching rules (what to evaluate)
8. Instructions (what to produce)

---

## Implementation Checklist

### Phase 1: Data + Patterns
- [ ] Define data model (what are you tracking?)
- [ ] Implement parser (input → structured data)
- [ ] Implement storage (SQLite + dedup)
- [ ] Implement pattern queries (aggregates, trends)
- [ ] CLI: `ingest`, `report`, `stats`, `patterns`

### Phase 2: Knowledge Base
- [ ] Create `knowledge/<domain>/` structure
- [ ] Populate reference data (entities, properties)
- [ ] Define benchmarks by skill level
- [ ] Write strategies/best practices
- [ ] Define coaching rules (IF/THEN)

### Phase 3: AI Integration
- [ ] Build context assembler (loads all KB for prompt)
- [ ] Define analysis tiers (quick/standard/deep)
- [ ] Create prompt templates
- [ ] Test with sample records

### Phase 4: Auto-Promotion
- [ ] Define promotion thresholds
- [ ] Implement auto-promote function
- [ ] Add changelog logging
- [ ] Integrate into pattern generation pipeline

### Phase 5: Documentation
- [ ] README with architecture diagram
- [ ] ARCHITECTURE.md with module responsibilities
- [ ] CHANGELOG.md with project history
- [ ] This template for replication

---

## Examples: Applying to Other Domains

### Cooking
```
knowledge/cooking/
├── ingredients.json      # Nutritional data, substitutions
├── techniques.json       # Cooking methods, temperatures
├── benchmarks.json       # Expected times by difficulty
├── rules.md              # "IF overcooked THEN reduce temp/time"
└── cook-profile.json     # Auto: preferred cuisines, success rates
```

### Personal Finance
```
knowledge/finance/
├── categories.json       # Expense categories, budgets
├── benchmarks.json       # Savings rate by income bracket
├── strategies.md         # Investment principles, tax optimization
├── rules.md              # "IF spending > budget THEN alert"
└── financial-profile.json # Auto: spending patterns, trends
```

### Chess
```
knowledge/chess/
├── openings.json         # Opening theory, ECO codes
├── benchmarks.json       # Rating-appropriate accuracy targets
├── strategies.md         # Middlegame principles, endgame technique
├── rules.md              # "IF blunder rate > 2/game THEN focus tactics"
└── player-profile.json   # Auto: opening repertoire, time management
```

---

## Key Insights from Agelytics

1. **Deterministic metrics communicate more than AI narratives.** "TC idle 27min in 44min game" > 3 paragraphs of analysis.

2. **Auto-promote data, curate theory.** Statistics can be automated. Strategy explanations need human judgment.

3. **Separation of concerns matters.** Framework (anyone can use) vs Integration (platform-specific) vs Personal data (gitignored).

4. **The pipeline should be fully automatic after setup.** New data → patterns → profile → KB updates → all without intervention.

5. **Start with patterns, not the KB.** The patterns tell you what knowledge is actually needed. Don't pre-build a massive KB — let usage drive it.
