# Agelytics Deep Analysis — Plano v1

**Objetivo:** Análise de coaching IA inédita na comunidade AoE2, usando dados determinísticos do action log + interpretação por IA.

**Data:** 2026-02-09
**Status:** Planejamento

---

## Dados Disponíveis no Action Log (confirmado)

Tudo abaixo é extraível deterministicamente do replay:

### Por Jogador
- **Action density por janela de tempo** (5min windows) — proxy de atividade/idle
- **Primeiro unit militar produzido** + timestamp
- **Timeline completa de pesquisas** com timestamps exatos
- **Timeline de edifícios-chave** (Castle, TC, Monastery, Siege Workshop, University)
- **Composição de exército** acumulada (unidades produzidas por tipo)
- **Age-up times** (Feudal, Castle, Imperial)
- **eAPM** (ações efetivas por minuto)
- **Resign timing**
- **Garrison/Ungarrison events**
- **Gate placement** (indica walling)
- **Farm autoqueue** (indica late-game eco management)

### Timing Windows
- **Move/Order/Target density** = proxy de micro management
- **Queue density** = proxy de macro management (produção)
- **Gaps de atividade** = idle time (potencial idle TC detectável)

---

## Estrutura da Análise IA Profunda

### 1. 📊 Overview (determinístico)
- Resultado, civs, mapa, duração, ELO gap
- Age-up times comparados
- eAPM comparado

### 2. ⏱️ Timeline de Momentos-Chave
Extraído do action log, formatado cronologicamente:
- Primeiro militar produzido (timing + tipo = indica estratégia)
- Cada age-up (quem chegou primeiro, gap)
- Primeiro Castle construído
- Primeiro Siege Workshop (indica push timing)
- Imperial age-up
- Resign

**Exemplo:**
```
00:00-08:00  Dark Age — ambos jogadores em eco
08:15        blzulian → Feudal (3min antes do oponente!)
11:28        Koromeister → Feudal
13:37        blzulian produz primeiro Spearman
19:12        blzulian → Castle (4:41 antes!)
19:27        Koromeister produz primeiro Militia (ATRASADO)
...
```

### 3. 🎯 Análise Macro (IA)
Baseado nos dados determinísticos, IA interpreta:
- **Eco management:** Villagers produzidos vs tempo, farms timing, TCs expandidos quando
- **Transições:** Dark→Feudal→Castle→Imp — foi smooth ou houve idle/delay?
- **Tech choices:** Priorizou o que? Fez sentido pro matchup?
- **Composição de exército:** Counter-composition correta? Adaptou ao oponente?
- **Comparação com benchmarks:** Feudal <10:00 pra ELO 600? Castle <20:00?

### 4. 🖱️ Análise Micro (IA)
- **Action density curve:** Onde esteve mais ativo? Onde idle?
- **Picos de atividade** = engajamentos militares (muitos Order/Target/Move em curto período)
- **Quedas de atividade** = idle (potencial eco floating, TC idle)
- **Move/Order ratio** = está micro-ing unidades ou só move-commanding?
- **Multi-tasking:** Ações alternando entre zonas diferentes?

### 5. 🏗️ Análise Estratégica (IA)
- **Build order inference:** Sequência de builds iniciais → qual strategy?
- **Timing attacks:** Detectar pushes (cluster de military production + moves)
- **Defensive vs offensive:** Ratio de builds defensivos vs ofensivos
- **Castle/TC placement timing:** Quando expandiu? Cedo demais? Tarde?
- **Siege timing:** Quando começou trebs/mangonels? Efetivo?

### 6. 💡 Coaching Points (IA)
Resumo acionável:
- **Top 3 erros** com timestamp e sugestão de correção
- **Top 3 acertos** com explicação do por quê funcionou
- **Próximo passo de melhoria** (1 coisa pra focar no próximo jogo)
- **Nota:** 1-10 com justificativa

### 7. 📈 Comparação Histórica (determinístico)
- ELO progression nas últimas 10-20 partidas
- Feudal time trend (melhorando?)
- eAPM trend
- Winrate por civ, por mapa
- Desempenho contra a mesma civ do oponente

---

## Dados a Extrair (novo no parser)

Para viabilizar a análise profunda, extrair adicionalmente:

1. **action_density:** Dict de `{player: {window_start_min: action_count}}` (janelas de 1min)
2. **research_timeline:** Lista completa de `{player, tech, timestamp}` (JÁ EXISTE em match_researches)
3. **building_timeline:** `{player, building, timestamp}` individual (hoje só temos count, não timing)
4. **first_military:** `{player, unit, timestamp}` — primeiro unit não-eco produzido
5. **key_moments:** Lista de timestamps com mudanças significativas (age-ups, first castle, resign)
6. **move_density:** Contagem de Move/Order/Target por janela de tempo por player

### Schema DB novo (proposta)
```sql
CREATE TABLE IF NOT EXISTS match_action_density (
    id INTEGER PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    player TEXT,
    minute INTEGER,
    action_count INTEGER,
    move_count INTEGER,
    order_count INTEGER
);

CREATE TABLE IF NOT EXISTS match_building_timeline (
    id INTEGER PRIMARY KEY,
    match_id INTEGER REFERENCES matches(id),
    player TEXT,
    building TEXT,
    timestamp_secs REAL
);
```

---

## Por que é Inédito

Ferramentas existentes na comunidade AoE2:
- **aoe2.net/aoe2companion:** Stats agregados, leaderboard, matchup winrates. Sem análise de replay.
- **AoE Insights:** Parser de replays com timeline visual. Mostra dados mas não interpreta.
- **CaptureAge:** Spectator tool com overlay. Tempo real, não pós-jogo.

**O que nenhuma faz:**
- Interpretação tática dos dados por IA
- Coaching personalizado ("você deveria ter feito X no minuto Y")
- Detecção de padrões de erro recorrentes entre partidas
- Comparação com benchmarks por faixa de ELO
- Sugestão de próximo passo de melhoria baseada no histórico

**Agelytics Deep Analysis = AoE Insights (dados) + IA coach (interpretação)**

---

## Implementação

### Fase 1 — Extração expandida (determinístico)
- Adicionar `action_density`, `building_timeline`, `first_military` ao parser
- Novas tabelas no DB
- Re-ingerir todas as partidas

### Fase 2 — Template de análise
- Prompt template que recebe todos os dados extraídos
- Structured output: momentos-chave, macro, micro, estratégia, coaching points
- Testar com 3-5 partidas variadas

### Fase 3 — Integração
- Botão "🧠 Análise IA" gera análise completa
- Cache em DB (não regenerar se já analisada)
- Versão texto + versão áudio (TTS dos coaching points)

### Fase 4 — Cross-match analysis
- Detectar padrões recorrentes entre partidas
- "Nos últimos 10 jogos, seu Castle time piorou 2min"
- "Contra Britons você perde 80% — considere counter-pick"
