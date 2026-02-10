# Métricas do Agelytics

## Métricas Econômicas

### 1. TC Idle Percent
- **Definição:** Percentual do tempo total da partida em que o Town Center ficou ocioso (sem produzir aldeões).
- **Cálculo:** Gaps > 30s entre Queue Villager commands, subtraindo 25s (tempo de treino). Soma / duração * 100.
- **Fonte:** `match.inputs` (Queue Villager timestamps)

### 2. Estimated Idle Villager Time (PROXY) ⚠️
- **Definição:** Soma dos gaps > 30s entre comandos econômicos (Move, Build, Queue Villager, Gather, Repair, Waypoint).
- **⚠️ PROXY:** O replay contém apenas inputs do jogador, NÃO o estado real dos aldeões. Gaps grandes entre comandos econômicos *sugerem* que aldeões podem estar ociosos, mas não é uma medida exata. Aldeões podem estar coletando recursos normalmente sem comandos novos.
- **Threshold:** 30 segundos entre comandos eco.
- **Fonte:** `match.inputs` — filtro por tipos econômicos.
- **No report:** "Est. Idle Vill Time: Xm Ys (proxy)"

### 3. Villager Production Rate (por Age)
- **Definição:** Aldeões produzidos por minuto, breakdown por age (Dark, Feudal, Castle, Imperial).
- **Benchmark:** ~2.4/min (1 aldeão a cada 25s) é o ideal em Dark/Feudal Age.
- **Cálculo:** Conta Queue Villager commands em cada intervalo de age, divide pela duração do age em minutos.
- **Fonte:** `vill_queue_timestamps` + `age_ups` com timestamps.
- **No report:** "Vill Rate: Dark Age: X/min, Feudal Age: Y/min, ..."

### 4. Resource Collection Efficiency
- **Definição:** Score de recursos coletados (do summary/player data) dividido por aldeões produzidos.
- **Interpretação:** Eficiência por aldeão — quanto cada aldeão contribuiu em recursos ao longo da partida.
- **Fonte:** `players[].resource_score` / `unit_production[player].Villager`
- **No report:** "Res Efficiency: X res/villager"
- **Limitação:** Depende de `resource_score` estar disponível nos dados do player. Se ausente, retorna None.

## Métricas Militares/Estratégicas

### 5. Farm Gap Average
- **Definição:** Tempo médio entre farms construídas consecutivas após Castle Age.
- **Fonte:** Build Farm timestamps pós-Castle Age.

### 6. Military Timing Index
- **Definição:** Timestamp da primeira unidade militar / timestamp de Castle Age.
- **Valores:** < 0.5 = rush, ~1.0 = timing padrão, > 1.0 = boom.

### 7. TC Count Progression
- **Definição:** Progressão de TCs construídos ao longo da partida.
- **Formato:** Lista de (timestamp, contagem acumulada).
