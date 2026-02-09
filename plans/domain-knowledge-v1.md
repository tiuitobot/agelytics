# Domain Knowledge System — v1 Architecture

**Data:** 2026-02-09
**Status:** Draft
**Objetivo:** Sistema de aprendizado contínuo por domínio, usando AoE2/Agelytics como caso de teste. Generalizável para outros domínios depois.

---

## Problema

O Deep Coach hoje analisa cada partida isoladamente. Ele não sabe que:
- Franks vs Mongols tem histórico de derrotas
- Teu Castle time médio é 22min (acima do benchmark pra teu ELO)
- Knights não funcionam contra civs com Camels
- Teu Feudal time melhorou 30s nas últimas 20 partidas

Esse conhecimento existe nos dados (144 partidas no SQLite), mas não está estruturado pra ser consumido pela IA.

---

## Arquitetura Proposta

### 3 Camadas

```
┌─────────────────────────────────────────────┐
│  CAMADA 3: Knowledge Base (curada)          │
│  knowledge/aoe2/*.md|json                   │
│  Conhecimento estável, validado, permanente │
│  Ex: "Mangudai countera Knight"             │
└──────────────────┬──────────────────────────┘
                   │ promoção (manual ou auto)
┌──────────────────┴──────────────────────────┐
│  CAMADA 2: Patterns (emergentes)            │
│  data/patterns.json                         │
│  Padrões detectados de N partidas           │
│  Ex: "Franks vs Mongols: 1W/4L últimas 20" │
└──────────────────┬──────────────────────────┘
                   │ detecção automática
┌──────────────────┴──────────────────────────┐
│  CAMADA 1: Match Data (raw)                 │
│  data/aoe2_matches.db (SQLite)              │
│  Dados determinísticos de cada partida      │
└─────────────────────────────────────────────┘
```

### Fluxo

```
Partida nova → parse → DB (camada 1)
                         ↓
              Pattern detector (camada 2)
              - Agrega stats por matchup, mapa, período
              - Detecta trends (ELO subindo/descendo, tempos melhorando)
              - Identifica anomalias (outliers, eco collapse frequency)
                         ↓
              Se pattern consistente (>5 ocorrências, >70% confiança)
                         ↓
              Promoção pra KB (camada 3)
              - Auto: métricas estatísticas (winrate por civ, avg age-ups)
              - Manual: conhecimento de jogo (matchup theory, build orders)
```

---

## Camada 1: Match Data (já existe)

SQLite com 144 partidas. Tabelas: `matches`, `match_players`, `match_age_ups`, `match_units`, `match_techs`, `match_buildings`.

**Gaps a preencher:**
- [ ] TC idle time per-TC (corrigir cálculo atual)
- [ ] Action density por minuto (nova tabela)
- [ ] Building timeline com timestamps (não só contagem)
- [ ] First military unit timing
- [ ] Farm/gather gaps

---

## Camada 2: Pattern Detection

### 2a. Queries agregadas (determinísticas, Python)

Módulo novo: `agelytics/patterns.py`

```python
def matchup_stats(player, n_last=50):
    """Winrate por matchup (minha civ vs civ oponente)."""
    # SELECT my_civ, opp_civ, COUNT(*), SUM(winner), AVG(duration)
    # GROUP BY my_civ, opp_civ HAVING COUNT(*) >= 3
    # ORDER BY winrate ASC
    
def age_up_trends(player, n_last=30):
    """Evolução dos tempos de age-up ao longo do tempo."""
    # Feudal avg últimas 10 vs anteriores 10
    # Castle avg últimas 10 vs anteriores 10
    # Tendência: melhorando, estável, piorando
    
def map_performance(player, n_last=50):
    """Winrate por mapa."""
    
def military_timing_index(player, n_last=30):
    """Tempo médio até primeira unidade militar."""
    # Correlação com winrate
    
def eco_collapse_frequency(player, n_last=30):
    """Frequência de eco collapses detectados."""
    # Farm gap >5min + TC idle >3min simultâneos
    
def elo_trend(player, n_last=30):
    """Tendência de ELO (regressão linear simples)."""
    
def civ_diversity(player, n_last=50):
    """Distribuição de civs usadas. Concentração vs diversidade."""
```

### 2b. Output: `data/patterns.json`

```json
{
  "generated_at": "2026-02-09T19:00:00",
  "player": "blzulian",
  "match_count": 144,
  "patterns": {
    "matchups": [
      {
        "my_civ": "Franks",
        "opp_civ": "Mongols", 
        "games": 5,
        "wins": 1,
        "winrate": 0.20,
        "avg_duration_min": 38.2,
        "insight": "Franks vs Mongols muito desfavorável. Mangudai+Camel countera Knights."
      }
    ],
    "age_up_trends": {
      "feudal_avg_recent": 620,
      "feudal_avg_older": 645,
      "feudal_trend": "improving",
      "castle_avg_recent": 1320,
      "castle_avg_older": 1280,
      "castle_trend": "worsening"
    },
    "military_timing": {
      "avg_first_military_secs": 840,
      "win_avg": 720,
      "loss_avg": 1020,
      "correlation": "strong_negative"
    },
    "eco_health": {
      "collapse_rate": 0.15,
      "avg_tc_idle_pct": 0.45,
      "farm_gap_avg_secs": 180
    },
    "elo_trend": {
      "current": 614,
      "min": 392,
      "max": 953,
      "trend_30d": "rising",
      "slope": 2.1
    }
  }
}
```

### 2c. Quando rodar

- **Após cada ingest:** Recalcular patterns (leve, <1s em 144 partidas)
- **No watcher:** Após inserir match novo, chamar `update_patterns()`
- **100% Python, 0% IA** — Patterns são estatísticos, não interpretativos

---

## Camada 3: Knowledge Base

### Estrutura: `knowledge/aoe2/`

```
knowledge/aoe2/
├── README.md              # Índice e meta-informação
├── civilizations.json     # Civ data (bonus, UU, tech tree highlights)
├── matchups.json          # Matchup knowledge (counters, strategies)
├── benchmarks.json        # Tempos de referência por ELO bracket
├── strategies.md          # Build orders, aberturas, adaptações
├── player-profile.json    # Perfil derivado (auto-gerado dos patterns)
└── coaching-rules.md      # Regras de coaching (if X then suggest Y)
```

### 3a. Conteúdo estático (curado manualmente)

**civilizations.json:**
```json
{
  "Franks": {
    "type": "cavalry",
    "bonus": ["Farm upgrades free", "Foragers +15%", "Cavalry HP +20%"],
    "unique_unit": "Throwing Axeman",
    "unique_tech": ["Bearded Axe", "Chivalry"],
    "strengths": ["Knight rush", "Fast Castle", "Cheap castles"],
    "weaknesses": ["No Crossbowman", "Weak archers", "No Camels"]
  }
}
```

**benchmarks.json:**
```json
{
  "elo_brackets": {
    "500-700": {
      "feudal_target_secs": 620,
      "castle_target_secs": 1200,
      "first_military_target_secs": 780,
      "eapm_expected": "15-25"
    },
    "700-900": {
      "feudal_target_secs": 580,
      "castle_target_secs": 1100
    }
  }
}
```

**matchups.json:**
```json
{
  "Franks_vs_Mongols": {
    "advantage": "Mongols",
    "reason": "Mangudai counters cavalry, Camels counter Knights",
    "player_data": {"games": 5, "winrate": 0.20},
    "suggested_strategy": "Archer + Siege Workshop, avoid mass Knights"
  }
}
```

### 3b. Conteúdo auto-gerado (dos patterns)

**player-profile.json** — Regenerado automaticamente:
```json
{
  "player": "blzulian",
  "elo": 614,
  "main_civ": "Franks",
  "playstyle": "cavalry-focused",
  "strengths": ["dark_age_consistency", "farm_management"],
  "weaknesses": ["castle_time_slow", "late_military_production", "adaptation_to_counters"],
  "trends": {
    "feudal_time": "improving",
    "elo": "rising_slowly"
  }
}
```

### 3c. Promoção: patterns → KB

**Auto-promoção (sem intervenção):**
- Matchup winrate com >5 jogos → atualiza `matchups.json` campo `player_data`
- Age-up averages → atualiza `player-profile.json`
- Novo civ jogado >3x → adiciona a `player-profile.json`

**Promoção assistida (IA sugere, humano/IA valida):**
- Pattern "eco collapse em 20% dos jogos" → sugere coaching rule
- Pattern "Knights vs Camels = derrota" → sugere strategy note
- Deep Coach pode propor adições à KB que são revisadas no DREAM_CYCLE

---

## Integração com Deep Coach

### Hoje (sem KB)
```
match_data → prompt genérico → análise
```

### Com KB
```
match_data + player_profile + matchup_knowledge + benchmarks → prompt enriquecido → análise contextualizada
```

**Exemplo concreto:**

Sem KB: "Teu Castle time de 24:07 é um pouco lento."
Com KB: "Teu Castle time de 24:07 está 3:07 acima do benchmark pra teu ELO (21:00). Tua média das últimas 10 partidas é 22:30, piorando 1:30 vs as 10 anteriores. Contra Mongols especificamente, teu winrate é 20% — dados mostram que tuas vitórias vieram de jogos com militar antes do min 15."

---

## Implementação — Fases

### Fase 1: Pattern Detection (Python, determinístico)
- [ ] Criar `agelytics/patterns.py` com queries agregadas
- [ ] Gerar `data/patterns.json` após cada ingest
- [ ] Integrar no watcher (update_patterns após insert)
- [ ] CLI: `python -m agelytics patterns` (mostra patterns atuais)
- **Esforço:** ~200 linhas Python, ~2h

### Fase 2: Knowledge Base estática
- [ ] Criar `knowledge/aoe2/` no repo
- [ ] Popular `civilizations.json` (top 10 civs mais jogadas)
- [ ] Popular `benchmarks.json` (por ELO bracket)
- [ ] Criar `matchups.json` base (counters óbvios)
- [ ] Criar `player-profile.json` auto-gerado
- **Esforço:** ~curadoria manual + script de geração, ~3h

### Fase 3: Integração Deep Coach
- [ ] Deep Coach carrega KB antes de analisar
- [ ] Prompt template inclui: player profile + matchup data + benchmarks
- [ ] Comparação explícita: "teu X vs benchmark Y"
- **Esforço:** ~template de prompt + lógica de carregamento, ~1h

### Fase 4: Auto-promoção
- [ ] Após pattern detection, comparar com KB existente
- [ ] Se divergência (ex: winrate mudou significativamente) → atualizar
- [ ] Log de mudanças em `knowledge/aoe2/changelog.md`
- **Esforço:** ~100 linhas Python, ~1h

### Fase 5: Generalização
- [ ] Abstrair o padrão pra outros domínios
- [ ] Template: `knowledge/<domain>/` com mesma estrutura
- [ ] Documento de design pattern pra reuso
- **Esforço:** ~documentação + refactor, ~2h

---

## Decisões de Design

### D1: Onde mora a KB?
**Decisão:** No repo Agelytics (`knowledge/aoe2/`), não no workspace OpenClaw.
**Motivo:** É conhecimento do domínio, não do agente. Viaja com o projeto.

### D2: Formato dos arquivos?
**Decisão:** JSON para dados estruturados (civs, benchmarks, matchups), Markdown para texto livre (strategies, coaching rules).
**Motivo:** JSON é consumível por código Python diretamente. Markdown é legível pra humanos e editável.

### D3: Patterns: IA ou Python?
**Decisão:** 100% Python/SQL. Zero IA na detecção de patterns.
**Motivo:** Consistência com filosofia Agelytics (básico = determinístico). IA só na interpretação (Deep Coach).

### D4: Frequência de atualização dos patterns?
**Decisão:** A cada ingest (novo match). Leve computacionalmente.
**Motivo:** Sempre fresh. Com 144 partidas, aggregation queries rodam em <100ms.

### D5: Player profile — privado ou público?
**Decisão:** No repo (público), mas contém só dados derivados (não privados).
**Motivo:** Winrates e tempos médios não são dados sensíveis. Se compartilhar o repo, outros podem ver o profile como exemplo.

### D6: Como a KB chega no Deep Coach?
**Decisão:** O callback script carrega JSONs relevantes e injeta no prompt como contexto.
**Motivo:** Simples. Sem banco adicional, sem embedding, sem RAG. Direto.

### D7: Coaching rules — quem escreve?
**Decisão:** Inicialmente manual (Bruno + IA). Depois, Deep Coach sugere rules que são revisadas.
**Motivo:** Coaching rules ruins são piores que nenhuma rule. Curadoria > automação neste caso.

---

## Métricas de Sucesso

1. **Deep Coach cita dados cross-match** (não só da partida atual)
2. **Benchmarks aparecem na análise** ("teu X vs esperado Y")
3. **Patterns atualizados automaticamente** após cada partida
4. **Player profile reflete realidade** (validado por Bruno)
5. **Processo generalizável** — documentado pra replicar em outro domínio

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| KB desatualizada (meta do jogo muda) | `benchmarks.json` com campo `source_date`, review trimestral |
| Over-fitting em poucos dados | Mínimo de 5 jogos pra qualquer pattern |
| Coaching rules genéricas demais | Regras incluem condição de ELO bracket |
| Complexidade creep | Fases incrementais, cada uma entrega valor isolado |

---

## Conexão com Sistema de Memória Geral

Este é um **caso específico** do pipeline genérico:
```
signals → candidates → patterns → promoted (PASSIVE_MEMORY)
```

Aplicado a um domínio:
```
match_data → aggregations → patterns → knowledge_base
```

O padrão é o mesmo. Se funcionar aqui, pode ser template pra:
- **Cofre:** knowledge base de anonimização (regras LGPD, patterns de PII)
- **Cooking:** receitas testadas, substituições que funcionaram
- **Finance:** padrões de gasto, benchmarks de investimento

A diferença: em vez de signals textuais, a entrada é dados estruturados. O resto do pipeline é análogo.
