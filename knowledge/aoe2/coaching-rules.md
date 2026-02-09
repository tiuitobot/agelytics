# Coaching Rules

Rules engine for automated coaching suggestions. Format: IF condition THEN suggestion.

## Economy

| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| E1 | TC idle > 30% of game time | "TC idle muito alto ({pct}%). Foque em produzir villagers sem parar." | HIGH |
| E2 | TC idle in wins similar to losses | "TC idle não diferencia suas vitórias de derrotas — problema sistêmico." | HIGH |
| E3 | Farm gap > 5min detected | "Gap de {gap}min sem fazer farms (min {start}-{end}). Farms devem ser replantadas constantemente." | MEDIUM |
| E4 | Villager count < benchmark for ELO | "Produziu {count} villagers (benchmark: {benchmark}). Mais villagers = mais eco = mais militar." | MEDIUM |
| E5 | No second TC by Castle +3min | "Sem segundo TC até {time}. Faça 2-3 TCs imediatamente ao chegar em Castle." | HIGH |

## Military

| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| M1 | First military > benchmark + 5min | "Primeira unidade militar aos {time} — {diff}min acima do esperado. Produza militar desde a Feudal." | HIGH |
| M2 | First military > 20min | "Zero militar até min {time}. Isso é uma emergência — qualquer rush te mataria." | CRITICAL |
| M3 | Win correlation: early military = wins | "Padrão: quando produz militar antes de {threshold}, ganha {wr}% das vezes." | MEDIUM |
| M4 | No military adaptation to opponent composition | "Oponente fez {opp_units}, você fez {my_units}. Considere {counter_units}." | MEDIUM |

## Age-Up Timing

| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| A1 | Feudal > benchmark + 1min | "Feudal em {time} — {diff}s acima do benchmark ({bench}). Dark Age precisa ser mais eficiente." | MEDIUM |
| A2 | Castle > benchmark + 3min | "Castle em {time} — muito lento. Transição Feudal→Castle precisa melhorar." | HIGH |
| A3 | Castle time worsening trend | "Castle time piorando (média recente {recent} vs anterior {older}). Atenção à transição." | MEDIUM |
| A4 | Never reached Imperial in 40+ min game | "Jogo de {duration} sem Imperial Age. Se passa de 35min, investir em Imperial." | LOW |

## Matchup-Specific

| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| S1 | Playing civ X vs counter Y with <30% WR | "Seu WR de {wr}% contra {opp_civ} com {my_civ} é crítico. Consulte estratégias alternativas." | HIGH |
| S2 | Making countered unit into counter | "Produzindo {unit} contra {opp_unit} — desfavorável. Considere {alternative}." | HIGH |
| S3 | Same civ >80% of games | "Jogou {civ} em {pct}% das partidas. Considere diversificar para aprender counters." | LOW |

## Cross-Match Patterns

| # | Condition | Suggestion | Priority |
|---|-----------|------------|----------|
| X1 | ELO falling (slope < -2/game) | "ELO em queda ({slope}/jogo). Pode estar tiltado — considere pausar." | MEDIUM |
| X2 | Eco collapse in >20% of recent games | "Eco collapse detectado em {pct}% dos jogos recentes. Padrão recorrente." | HIGH |
| X3 | Arabia WR significantly < Arena WR | "WR Arabia {a_wr}% vs Arena {r_wr}%. Open maps são mais fracos — praticar pressão Feudal." | MEDIUM |
