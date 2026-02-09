# AoE2 Knowledge Base

Domain-specific knowledge for AI-powered match analysis and coaching.

## Files

| File | Type | Description | Updated |
|------|------|-------------|---------|
| `benchmarks.json` | Static | Age-up and eco benchmarks by ELO bracket | Manual |
| `civilizations.json` | Static | Civ bonuses, strengths, weaknesses, counters | Manual |
| `matchups.json` | Static + Data | Matchup theory + player-specific winrates | Manual + Auto |
| `strategies.md` | Static | Build orders, principles, common mistakes | Manual |
| `coaching-rules.md` | Static | IF/THEN coaching rule engine | Manual |
| `player-profile.json` | Auto-generated | Player strengths, weaknesses, trends | Every match |

## How It's Used

1. **Pattern Detection** (`agelytics/patterns.py`) generates aggregate stats from match history
2. **Player Profile** is auto-regenerated from patterns after each match
3. **Deep Coach** loads KB files as context for AI analysis
4. **Coaching Rules** are evaluated against match data for automated suggestions

## Contributing

- Static files: edit directly, update `last_updated` field
- `player-profile.json`: auto-generated, don't edit manually
- Add new civs to `civilizations.json` as they're encountered
- Add matchup entries to `matchups.json` after 3+ games against a civ
