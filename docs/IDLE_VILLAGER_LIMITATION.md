# Idle Villager Time — Limitação Técnica

## Status: Não implementável via replay

## Por que não é possível

Replays de AoE2 (`.aoe2record`) gravam apenas **inputs do jogador** (comandos),
não o estado interno do jogo. O arquivo contém ações como Move, Order, Build,
Queue, Research, etc., mas **não registra quando uma unidade termina sua tarefa
e fica idle**.

Para calcular idle villager time seria necessário **simular o engine do jogo
inteiro** — incluindo pathfinding, tempos de coleta de recursos, depleção de
recursos, tempos de construção, etc. Isso está fora do escopo do mgz e do
Agelytics.

### Campos encontrados no mgz

O header do replay tem `idle_timer`, `idle_timeout` e `adjusted_idle_timeout`
em `mgz/header/objects.py`, mas esses são **valores iniciais de configuração
dos objetos**, não métricas acumuladas durante a partida.

## Proxies disponíveis

### 1. TC Idle (já implementado)
- **O que mede:** Gaps na produção de aldeões > 30s
- **Proxy para:** Eficiência de produção contínua do TC
- **Limitação:** Não mede idle villager, mede idle TC

### 2. eAPM (já disponível)
- **O que mede:** Ações efetivas por minuto
- **Proxy para:** Atividade geral do jogador — jogadores com eAPM alto
  tendem a ter menos idle villagers porque estão constantemente dando comandos

### 3. Villager Production Rate (proposta futura)
- **O que mediria:** Aldeões produzidos por minuto
- **Proxy para:** Eficiência econômica geral
- **Como:** `villagers_produced / (duration_mins - dark_age_mins)`

## Conclusão

Idle villager time é uma métrica **in-game** que requer simulação de estado.
O Agelytics trabalha com dados de replay (input log) e não consegue extrair
essa informação. As melhores proxies disponíveis são TC idle time e eAPM.
