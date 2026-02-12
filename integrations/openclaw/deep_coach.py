"""Deep Coach — KB-enriched context builder for AI analysis.

Loads match data + knowledge base + patterns to build a rich prompt context
that an LLM can use for forensic-level coaching analysis.
"""

import json
import os
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
KB_DIR = REPO_ROOT / "knowledge" / "aoe2"
DATA_DIR = REPO_ROOT / "data"


def load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict if missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_text(path: Path) -> str:
    """Load a text file, return empty string if missing."""
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""


def get_match_context(match_id: int, player: str = "blzulian") -> dict:
    """Load all context for a Deep Coach analysis."""
    from agelytics.db import get_db, get_match_by_id
    
    conn = get_db()
    match = get_match_by_id(conn, match_id)
    if not match:
        conn.close()
        return {"error": f"Match #{match_id} not found"}
    
    # Find opponent civ
    my_civ = None
    opp_civ = None
    for p in match["players"]:
        if p["name"].lower() == player.lower():
            my_civ = p["civ_name"]
        else:
            opp_civ = p["civ_name"]
    
    # Load KB
    benchmarks = load_json(KB_DIR / "benchmarks.json")
    civs = load_json(KB_DIR / "civilizations.json")
    matchups = load_json(KB_DIR / "matchups.json")
    coaching_rules = load_text(KB_DIR / "coaching-rules.md")
    strategies = load_text(KB_DIR / "strategies.md")
    
    # Load personal data
    patterns = load_json(DATA_DIR / "patterns.json")
    profile = load_json(KB_DIR / "player-profile.json")
    
    # Find ELO bracket
    my_elo = None
    for p in match["players"]:
        if p["name"].lower() == player.lower():
            my_elo = p.get("elo", 0)
    
    bracket = None
    if benchmarks.get("elo_brackets") and my_elo:
        for key, data in benchmarks["elo_brackets"].items():
            low, high = key.split("-") if "-" in key else (key.rstrip("+"), "9999")
            if int(low) <= my_elo <= int(high):
                bracket = data
                bracket["range"] = key
                break
    
    # Find matchup knowledge
    matchup_key = f"{my_civ}_vs_{opp_civ}"
    matchup_data = matchups.get("matchups", {}).get(matchup_key, {})
    
    # Find civ data
    my_civ_data = civs.get("civilizations", {}).get(my_civ, {})
    opp_civ_data = civs.get("civilizations", {}).get(opp_civ, {})
    
    # Find matchup stats from patterns
    matchup_stats = None
    for m in patterns.get("matchups", []):
        if m["my_civ"] == my_civ and m["opp_civ"] == opp_civ:
            matchup_stats = m
            break
    
    conn.close()
    
    return {
        "match": match,
        "player": player,
        "my_civ": my_civ,
        "opp_civ": opp_civ,
        "my_elo": my_elo,
        "benchmark": bracket,
        "matchup_theory": matchup_data,
        "matchup_stats": matchup_stats,
        "my_civ_data": my_civ_data,
        "opp_civ_data": opp_civ_data,
        "player_profile": profile,
        "age_up_trends": patterns.get("age_up_trends", {}),
        "elo_trend": patterns.get("elo_trend", {}),
        "coaching_rules": coaching_rules,
        "strategies": strategies,
    }


def build_prompt(match_id: int, player: str = "blzulian", 
                  action_log: str = "") -> str:
    """Build the full Deep Coach prompt with KB context."""
    ctx = get_match_context(match_id, player)
    
    if "error" in ctx:
        return f"Error: {ctx['error']}"
    
    match = ctx["match"]
    
    # Format match summary
    me = next((p for p in match["players"] if p["name"].lower() == player.lower()), {})
    opp = next((p for p in match["players"] if p["name"].lower() != player.lower()), {})
    
    is_win = bool(me.get("winner"))
    result = "VITÓRIA" if is_win else "DERROTA"
    duration_min = match.get("duration_secs", 0) / 60
    
    sections = []
    
    # Header
    sections.append(f"""# Deep Coach Analysis — Match #{match_id}

## Match
- **Resultado:** {result}
- **{ctx['my_civ']} vs {ctx['opp_civ']}** | {match.get('map_name', '?')} | {duration_min:.0f}min
- **ELO:** {me.get('elo', '?')} vs {opp.get('elo', '?')}
- **eAPM:** {me.get('eapm', '?')} vs {opp.get('eapm', '?')}
- **TC idle:** {(me.get('tc_idle_secs') or 0)/60:.1f}min ({ctx['player']}) vs {(opp.get('tc_idle_secs') or 0)/60:.1f}min ({opp.get('name', '?')})
""")
    
    # Age-ups
    age_ups = match.get("age_ups", [])
    if age_ups:
        sections.append("## Age-Up Times")
        for a in age_ups:
            t = a["timestamp_secs"]
            sections.append(f"- {a['player']}: {a['age']} at {int(t)//60}:{int(t)%60:02d}")
        sections.append("")
    
    # Army
    units = match.get("unit_production", {})
    if units:
        sections.append("## Army Composition")
        for pname, unit_dict in units.items():
            sorted_units = sorted(unit_dict.items(), key=lambda x: -x[1])
            top = [f"{u} ×{c}" for u, c in sorted_units[:8]]
            sections.append(f"- **{pname}:** {', '.join(top)}")
        sections.append("")
    
    # Benchmarks
    if ctx["benchmark"]:
        b = ctx["benchmark"]
        sections.append(f"""## Benchmarks (ELO {b['range']} — {b.get('label', '')})
- Feudal target: {b.get('feudal_secs', 0)//60}:{b.get('feudal_secs', 0)%60:02d}
- Castle target: {b.get('castle_secs', 0)//60}:{b.get('castle_secs', 0)%60:02d}
- First military target: {b.get('first_military_secs', 0)//60}:{b.get('first_military_secs', 0)%60:02d}
- eAPM expected: {b.get('eapm', '?')}
- Villager count @30min: {b.get('villager_count_30min', '?')}
""")
    
    # Matchup theory
    if ctx["matchup_theory"]:
        mt = ctx["matchup_theory"]
        sections.append(f"""## Matchup: {ctx['my_civ']} vs {ctx['opp_civ']}
- **Vantagem teórica:** {mt.get('theoretical_advantage', '?')}
- **Motivo:** {mt.get('reason', '?')}
- **Estratégia sugerida:** {mt.get('suggested_strategy', '?')}
""")
    
    # Player stats for this matchup
    if ctx["matchup_stats"]:
        ms = ctx["matchup_stats"]
        sections.append(f"""## Seu Histórico neste Matchup
- {ms['games']} jogos, {ms['wins']}W/{ms['games']-ms['wins']}L ({ms['winrate']*100:.0f}% WR)
- Duração média: {ms['avg_duration']/60:.0f}min
""")
    
    # Player profile
    if ctx["player_profile"]:
        pp = ctx["player_profile"]
        sections.append(f"""## Perfil do Jogador
- **ELO:** {pp.get('elo', {}).get('current', '?')} (trend: {pp.get('elo', {}).get('trend', '?')})
- **Main civ:** {pp.get('main_civ', '?')} | Playstyle: {pp.get('playstyle', '?')}
- **Strengths:** {', '.join(pp.get('strengths', [])) or 'none identified'}
- **Weaknesses:** {', '.join(pp.get('weaknesses', [])) or 'none identified'}
""")
    
    # Age-up trends
    trends = ctx.get("age_up_trends", {})
    if trends:
        sections.append("## Age-Up Trends (últimas 10 vs anteriores 10)")
        for age, data in trends.items():
            avg = data.get("avg_recent_secs", 0)
            diff = data.get("diff_secs", 0)
            sections.append(f"- {age.title()}: {int(avg)//60}:{int(avg)%60:02d} avg ({diff:+.0f}s, {data.get('trend', '?')})")
        sections.append("")
    
    # Civ data
    if ctx["my_civ_data"]:
        cd = ctx["my_civ_data"]
        sections.append(f"""## {ctx['my_civ']} — Strengths & Weaknesses
- **Strengths:** {', '.join(cd.get('strengths', []))}
- **Weaknesses:** {', '.join(cd.get('weaknesses', []))}
- **Countered by:** {', '.join(cd.get('countered_by', []))}
""")
    
    if ctx["opp_civ_data"]:
        cd = ctx["opp_civ_data"]
        sections.append(f"""## {ctx['opp_civ']} — Strengths & Weaknesses
- **Strengths:** {', '.join(cd.get('strengths', []))}
- **Weaknesses:** {', '.join(cd.get('weaknesses', []))}
- **Countered by:** {', '.join(cd.get('countered_by', []))}
""")
    
    # Action log (if provided)
    if action_log:
        sections.append(f"## Action Log Data\n\n{action_log}")
    
    # Coaching rules
    if ctx["coaching_rules"]:
        sections.append(f"## Coaching Rules\n\n{ctx['coaching_rules']}")
    
    # Instructions
    sections.append("""## Instruções para Análise

Baseando-se em TODOS os dados acima (match data, benchmarks, matchup theory, histórico do jogador, action log), produza:

1. **Timeline** — Eventos-chave com timestamps
2. **Cadeia causal** — Identifique a causa raiz (não liste erros independentes, encontre a cascata)
3. **Comparação com benchmarks** — Tempos vs esperado para este ELO
4. **Insights não-óbvios** — Coisas que o jogador provavelmente NÃO percebeu
5. **Cross-match patterns** — Se há padrões recorrentes do perfil, mencione
6. **Avaliação das coaching rules** — Quais regras se aplicam a esta partida?
7. **Nota (1-10)** com justificativa

Responda em português brasileiro. Seja direto e específico — dados > opinião.
""")
    
    return "\n".join(sections)


if __name__ == "__main__":
    import sys
    match_id = int(sys.argv[1]) if len(sys.argv) > 1 else 145
    player = sys.argv[2] if len(sys.argv) > 2 else "blzulian"
    print(build_prompt(match_id, player))
