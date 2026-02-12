#!/usr/bin/env python3
"""Quick deterministic report for Telegram — no AI needed.
Outputs KPI text + PDF path for a match.
Usage: python3 -m integrations.openclaw.quick_report <match_id>
"""
import sys
from agelytics.db import get_db, get_match_by_id

def fmt_time(s):
    if s is None:
        return "—"
    return f"{int(s//60)}:{int(s%60):02d}"

def quick_report(match_id: int) -> str:
    db = get_db()
    m = get_match_by_id(db, match_id)
    if not m:
        return f"Match {match_id} not found"

    p1 = next((p for p in m['players'] if p['name'] == 'blzulian'), None)
    p2 = next((p for p in m['players'] if p['name'] != 'blzulian'), None)
    if not p1 or not p2:
        return f"Player data incomplete for match {match_id}"

    result = "✅ VITÓRIA" if p1['winner'] == 1 else "❌ DERROTA"
    dur = m['duration_secs']

    # Age ups
    feudal = castle = imperial = None
    for a in m.get('age_ups', []):
        if a['player'] == 'blzulian':
            if a['age'] == 'Feudal Age': feudal = a['timestamp_secs']
            elif a['age'] == 'Castle Age': castle = a['timestamp_secs']
            elif a['age'] == 'Imperial Age': imperial = a['timestamp_secs']

    # Top units
    units = m.get('unit_production', {}).get('blzulian', {})
    top_units = sorted([(k, v) for k, v in units.items() if k != 'Villager'], key=lambda x: -x[1])[:4]
    units_str = ", ".join(f"{n} ×{c}" for n, c in top_units)

    # Opponent units
    opp_units = m.get('unit_production', {}).get(p2['name'], {})
    opp_top = sorted([(k, v) for k, v in opp_units.items() if k != 'Villager'], key=lambda x: -x[1])[:3]
    opp_str = ", ".join(f"{n} ×{c}" for n, c in opp_top)

    # TC idle breakdown by age (if available)
    tc_idle_detail = ""
    if p1.get('tc_idle_dark') is not None:
        parts = []
        for age, key in [('D', 'tc_idle_dark'), ('F', 'tc_idle_feudal'), ('C', 'tc_idle_castle'), ('I', 'tc_idle_imperial')]:
            val = p1.get(key, 0)
            if val and val > 0:
                parts.append(f"{age}={fmt_time(val)}")
        if parts:
            tc_idle_detail = f" ({', '.join(parts)})"

    lines = [
        f"📊 **Match #{match_id}**",
        f"**{result}** | {p1['civ_name']} vs {p2['civ_name']} | {m['map_name']} | {fmt_time(dur)}",
        f"ELO: {p1['elo']} vs {p2['elo']}",
        "",
        f"⏱ Feudal: {fmt_time(feudal)} | Castle: {fmt_time(castle)} | Imperial: {fmt_time(imperial)}",
        f"⚡ eAPM: {p1['eapm']} | 🗡 Opening: {p1['opening_strategy'] or '—'}",
        f"🏚 TC idle: {fmt_time(p1['tc_idle_secs'])}{tc_idle_detail}",
        f"🏠 Housed: {p1['housed_count']}x | 🏰 TCs: {p1['tc_count_final']}",
        f"⚔️ Army: {units_str}",
        f"🛡 Opp: {opp_str}",
    ]

    # Resign info
    if m.get('resign_player'):
        lines.append(f"🏳️ Resign: {m['resign_player']}")

    return "\n".join(lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m integrations.openclaw.quick_report <match_id>")
        sys.exit(1)
    print(quick_report(int(sys.argv[1])))
