# Métricas Determinísticas - Agelytics

## Visão Geral

Este documento descreve as métricas determinísticas implementadas no Agelytics para análise de partidas de Age of Empires II: Definitive Edition.

## Métricas Implementadas

### 1. Farm Gap Average (Média de Intervalo entre Farms)

**Função:** `farm_gap_average(match, player)`

**Descrição:**  
Calcula o tempo médio (em segundos) entre farms construídas consecutivas após atingir Castle Age.

**Interpretação:**
- **Valores baixos (< 20s):** Boa eficiência de economia, farms sendo construídas continuamente
- **Valores médios (20-40s):** Eficiência normal
- **Valores altos (> 40s):** Possíveis gaps de produção, falta de madeira ou atenção

**Limitações:**
- Apenas considera farms construídas após Castle Age
- Gaps muito grandes (> 120s) são ignorados (assumidos como pausas ou transições de estratégia)
- Não captura depleção de farms, apenas comandos de construção

---

### 2. Military Timing Index (Índice de Timing Militar)

**Função:** `military_timing_index(match, player)`

**Descrição:**  
Calcula a relação entre o timestamp da primeira unidade militar produzida e o timestamp de Castle Age.

**Fórmula:**  
```
military_timing_index = timestamp_primeira_unidade_militar / timestamp_castle_age
```

**Interpretação:**
- **< 0.7:** Rush agressivo (militar muito antes de Castle)
- **0.7 - 1.2:** Timing padrão/balanceado
- **> 1.2:** Estratégia de boom (foco em economia antes de militar)

**Notas:**
- Valor de 1.0 indica que a primeira unidade militar foi produzida exatamente quando Castle Age foi atingido
- Útil para identificar estilos de jogo e estratégias

---

### 3. TC Count Progression (Progressão de Town Centers)

**Função:** `tc_count_progression(match, player)`

**Descrição:**  
Retorna a evolução do número de Town Centers (TCs) construídos ao longo da partida.

**Formato de Retorno:**  
Lista de tuplas `(timestamp_secs, contagem_acumulada_de_tcs)`.

**Exemplo:**
```python
[
    (0.0, 1),      # TC inicial
    (420.5, 2),    # Segundo TC em 7min
    (680.0, 3),    # Terceiro TC em 11min20s
]
```

**Interpretação:**
- **Expansão rápida:** Múltiplos TCs construídos cedo (< 10min)
- **Expansão tardia:** TCs adicionais após 15min
- **Jogo de 1 TC:** Estratégias all-in ou rush sem expansão

**Uso:**
- Indicador de expansão econômica
- Comparação entre jogadores em timing de boom
- Análise de viabilidade de estratégias

---

## Implementação Técnica

### Enriquecimento de Dados

As métricas dependem de timestamps de eventos específicos que não estão no parser padrão. A função `enrich_match_for_metrics(summary)` extrai:

- `_farm_build_timestamps`: Timestamps de construção de farms por jogador
- `_first_military_timestamp`: Timestamp da primeira unidade militar por jogador
- `_tc_build_timestamps`: Timestamps de construção de TCs por jogador

Esses dados são prefixados com `_` para indicar que são internos/auxiliares.

### Integração no Fluxo

1. **Parser** (`parser.py`): Chama `enrich_match_for_metrics()` e `compute_all_metrics()` para cada jogador
2. **Banco de Dados** (`db.py`): Novas colunas em `match_players`:
   - `farm_gap_average` (REAL)
   - `military_timing_index` (REAL)
   - `tc_count_final` (INTEGER) - número final de TCs
3. **Reports** (`report.py`): Exibe métricas em seção "📊 Métricas Avançadas"

### Testes

Testes unitários em `tests/test_new_metrics.py` validam:
- Cálculos corretos das métricas
- Comportamento com dados insuficientes (retorna `None`)
- Edge cases (apenas 1 farm, sem militar, etc.)

## Limitações e Considerações

### Dados do Replay

As métricas dependem dos **inputs do jogador** registrados no replay, não do estado real do jogo:

- **Farm gap:** Baseado em comandos de construção, não em depleção real de farms
- **Military timing:** Baseado em comandos de queue, não em produção concluída
- **TC progression:** Baseado em comandos de construção, não em conclusão de build

### Dados Insuficientes

Todas as métricas retornam `None` quando:
- Dados necessários não estão disponíveis no replay
- Jogador não executou ações relevantes (ex: sem farms em Castle Age)
- Replay corrompido ou incompleto

### Comparabilidade

Para comparações significativas:
- Considerar duração da partida
- Comparar apenas partidas de mesmo tipo (1v1, team games, etc.)
- Considerar mapas e recursos disponíveis

## Uso Prático

### Análise Individual

Identificar pontos de melhoria:
- Farm gap alto → Melhorar gestão de madeira e eco timing
- Military timing muito alto → Considerar pressão militar mais cedo
- TC progression lento → Trabalhar expansão e segurança

### Análise Comparativa

Comparar com oponentes:
- Quem expandiu mais rápido?
- Quem priorizou militar vs economia?
- Diferenças de estilo entre jogadores

### Análise de Evolução

Acompanhar progresso ao longo do tempo:
- Farm gap diminuindo → Melhoria em macro
- Military timing mais consistente → Melhor execução de builds
- TC progression mais agressivo → Confiança em expansão

## Roadmap Futuro

Possíveis métricas adicionais:

- **Age-up efficiency:** Comparar tempo de age-up com benchmark ideal
- **Villager efficiency:** Tempo médio de produção de aldeões
- **Resource balance:** Análise de acúmulo excessivo de recursos
- **Military production rate:** Taxa de produção militar por idade
- **Micro indicators:** Análise de APM em momentos críticos

---

**Data de Implementação:** 10 de Fevereiro de 2026  
**Autor:** Claude (subagent via OpenClaw)  
**Versão:** 1.0
