"""Métricas derivadas determinísticas para Agelytics.

Funções puras que calculam métricas a partir de dados de partida parseados.
Retornam None quando não há dados suficientes.

Para métricas que precisam de timestamps por evento (farm_gap, military_timing,
tc_count_progression), é necessário primeiro enriquecer o dict da partida com
`enrich_match_for_metrics(summary)` — que extrai dados adicionais do replay
sem modificar o parser existente.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Métricas que funcionam com dados parseados existentes
# ---------------------------------------------------------------------------

def tc_idle_percent(match: dict, player: str) -> Optional[float]:
    """Percentual de tempo ocioso do TC em relação à duração da partida.

    Formaliza o TC idle já calculado pelo parser (baseado em gaps na produção
    de aldeões > 30s) como percentual da duração total.

    Args:
        match: dict de partida parseado pelo Agelytics.
        player: nome do jogador.

    Returns:
        Percentual (0-100) de idle time, ou None se dados insuficientes.
    """
    duration = match.get("duration_secs", 0)
    tc_idle = match.get("tc_idle", {})

    if not duration or duration <= 0:
        return None

    idle_secs = tc_idle.get(player)
    if idle_secs is None:
        return None

    return round((idle_secs / duration) * 100, 2)


# ---------------------------------------------------------------------------
# Métricas que precisam de dados enriquecidos (timestamps por evento)
# ---------------------------------------------------------------------------

def farm_gap_average(match: dict, player: str) -> Optional[float]:
    """Tempo médio (segundos) entre farms construídas consecutivas após Castle Age.

    Como o replay não fornece eventos de depleção de farm, usamos o gap entre
    comandos de construção de farm consecutivos após Castle Age como proxy.
    Gaps muito grandes (>120s) são ignorados (provavelmente pausas ou transições).

    Requer dados enriquecidos via `enrich_match_for_metrics()`.

    Args:
        match: dict de partida (enriquecido).
        player: nome do jogador.

    Returns:
        Média em segundos dos gaps entre farms, ou None se dados insuficientes.
    """
    farm_timestamps = match.get("_farm_build_timestamps", {}).get(player, [])
    castle_age_ts = _get_age_timestamp(match, player, "Castle Age")

    if castle_age_ts is None or len(farm_timestamps) < 2:
        return None

    # Filtrar apenas farms após Castle Age
    post_castle = sorted(ts for ts in farm_timestamps if ts >= castle_age_ts)

    if len(post_castle) < 2:
        return None

    gaps = []
    for i in range(1, len(post_castle)):
        gap = post_castle[i] - post_castle[i - 1]
        if 0 < gap <= 120:  # Ignorar gaps absurdos
            gaps.append(gap)

    if not gaps:
        return None

    return round(sum(gaps) / len(gaps), 2)


def military_timing_index(match: dict, player: str) -> Optional[float]:
    """Índice de timing militar: timestamp da primeira unidade militar / Castle Age.

    Valores < 0.5 indicam rush agressivo (militar muito antes de Castle).
    Valores > 1.0 indicam boom (militar só após Castle).
    Valor ~1.0 indica timing padrão.

    Requer dados enriquecidos via `enrich_match_for_metrics()`.

    Args:
        match: dict de partida (enriquecido).
        player: nome do jogador.

    Returns:
        Índice normalizado (float), ou None se dados insuficientes.
    """
    first_military_ts = match.get("_first_military_timestamp", {}).get(player)
    castle_age_ts = _get_age_timestamp(match, player, "Castle Age")

    if first_military_ts is None or castle_age_ts is None or castle_age_ts <= 0:
        return None

    return round(first_military_ts / castle_age_ts, 3)


def tc_count_progression(match: dict, player: str) -> Optional[list[tuple[float, int]]]:
    """Progressão de TCs construídos ao longo da partida.

    Retorna lista de tuplas (timestamp_secs, contagem_acumulada_de_tcs).
    O primeiro TC (inicial) é incluído como (0, 1).

    Requer dados enriquecidos via `enrich_match_for_metrics()`.

    Args:
        match: dict de partida (enriquecido).
        player: nome do jogador.

    Returns:
        Lista de (timestamp, tc_count), ou None se dados insuficientes.
    """
    tc_timestamps = match.get("_tc_build_timestamps", {}).get(player, [])

    # Sempre há pelo menos 1 TC (inicial)
    progression = [(0.0, 1)]

    if not tc_timestamps:
        # Verificar se buildings indica TCs construídos
        tc_count = match.get("buildings", {}).get(player, {}).get("Town Center", 0)
        if tc_count <= 0:
            return progression  # Só o TC inicial
        # Sem timestamps, não podemos determinar quando — retornar None
        return None

    sorted_ts = sorted(tc_timestamps)
    for i, ts in enumerate(sorted_ts):
        progression.append((ts, i + 2))  # +2 porque TC inicial = 1

    return progression


# ---------------------------------------------------------------------------
# Enriquecimento de dados (extrai timestamps do replay sem modificar o parser)
# ---------------------------------------------------------------------------

# Unidades econômicas / não-militares
_ECO_UNITS = {
    "Villager", "Scout Cavalry", "Trade Cart", "Trade Cog",
    "Fishing Ship", "Transport Ship", "Monk", "Missionary",
}


def enrich_match_for_metrics(summary) -> dict:
    """Extrai dados adicionais com timestamps do replay para métricas.

    NÃO modifica o parser. Retorna um dict com chaves prefixadas por '_'
    que pode ser merged no dict de partida existente.

    Args:
        summary: objeto mgz.summary.Summary do replay.

    Returns:
        Dict com:
        - _farm_build_timestamps: {player: [timestamps]}
        - _first_military_timestamp: {player: timestamp}
        - _tc_build_timestamps: {player: [timestamps]}
    """
    farm_timestamps: dict[str, list[float]] = defaultdict(list)
    tc_timestamps: dict[str, list[float]] = defaultdict(list)
    first_military: dict[str, float] = {}

    try:
        match = summary.match
        if not hasattr(match, "inputs") or not match.inputs:
            return {}

        for inp in match.inputs:
            try:
                player_name = inp.player.name if hasattr(inp.player, "name") else None
                if not player_name:
                    continue

                ts = inp.timestamp.total_seconds() if hasattr(inp.timestamp, "total_seconds") else 0

                if inp.type == "Build" and hasattr(inp, "payload") and inp.payload:
                    building = inp.payload.get("building", "")
                    if building == "Farm":
                        farm_timestamps[player_name].append(ts)
                    elif building == "Town Center":
                        tc_timestamps[player_name].append(ts)

                elif inp.type == "Queue" and hasattr(inp, "payload") and inp.payload:
                    unit = inp.payload.get("unit", "")
                    if unit and unit not in _ECO_UNITS and player_name not in first_military:
                        first_military[player_name] = ts

            except Exception:
                continue

    except Exception:
        return {}

    return {
        "_farm_build_timestamps": dict(farm_timestamps),
        "_first_military_timestamp": dict(first_military),
        "_tc_build_timestamps": dict(tc_timestamps),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_age_timestamp(match: dict, player: str, age: str) -> Optional[float]:
    """Busca timestamp de um age-up específico para um jogador."""
    for age_up in match.get("age_ups", []):
        if age_up["player"] == player and age_up["age"] == age:
            return age_up["timestamp_secs"]
    return None


def estimated_idle_villager_time(match: dict, player: str) -> Optional[float]:
    """Tempo estimado de aldeões ociosos (PROXY).

    PROXY: Baseada em gaps entre comandos econômicos > 30s no action log.
    O replay só contém inputs do jogador, não o estado real dos aldeões.
    Gaps grandes entre comandos econômicos sugerem que aldeões podem estar
    ociosos, mas não é uma medida exata.

    Args:
        match: dict de partida parseado.
        player: nome do jogador.

    Returns:
        Tempo estimado em segundos, ou None se dados insuficientes.
    """
    idle_data = match.get("estimated_idle_villager_time", {})
    value = idle_data.get(player)
    if value is None:
        return None
    return value


def villager_production_rate_by_age(match: dict, player: str) -> Optional[dict]:
    """Aldeões produzidos por minuto, breakdown por age.

    Calcula a taxa de produção de aldeões em cada age (Dark, Feudal, Castle, Imperial).
    Benchmark: ~2.4/min (1 aldeão a cada 25s) é o ideal em Dark/Feudal.

    Args:
        match: dict de partida parseado (com vill_queue_timestamps).
        player: nome do jogador.

    Returns:
        Dict {age_name: rate_per_min} ou None se dados insuficientes.
    """
    vill_timestamps = match.get("vill_queue_timestamps", {}).get(player, [])
    if not vill_timestamps:
        return None

    age_ups = match.get("age_ups", [])
    duration = match.get("duration_secs", 0)
    if not duration:
        return None

    # Build age boundaries for this player
    player_ages = {}
    for au in age_ups:
        if au["player"] == player:
            player_ages[au["age"]] = au["timestamp_secs"]

    # Define age ranges: (start, end)
    boundaries = []
    boundaries.append(("Dark Age", 0.0, player_ages.get("Feudal Age", duration)))
    if "Feudal Age" in player_ages:
        boundaries.append(("Feudal Age", player_ages["Feudal Age"],
                          player_ages.get("Castle Age", duration)))
    if "Castle Age" in player_ages:
        boundaries.append(("Castle Age", player_ages["Castle Age"],
                          player_ages.get("Imperial Age", duration)))
    if "Imperial Age" in player_ages:
        boundaries.append(("Imperial Age", player_ages["Imperial Age"], duration))

    sorted_ts = sorted(vill_timestamps)
    result = {}
    for age_name, start, end in boundaries:
        age_duration_min = (end - start) / 60.0
        if age_duration_min <= 0:
            continue
        count = sum(1 for t in sorted_ts if start <= t < end)
        result[age_name] = round(count / age_duration_min, 2)

    return result if result else None


def resource_collection_efficiency(match: dict, player: str) -> Optional[float]:
    """Score de recursos coletados dividido por aldeões produzidos.

    Eficiência por aldeão: quanto cada aldeão contribuiu em recursos.
    Usa o resource_score do summary (se disponível) ou soma de recursos.

    Args:
        match: dict de partida parseado.
        player: nome do jogador.

    Returns:
        Recursos por aldeão (float), ou None se dados insuficientes.
    """
    # Villager count from unit_production
    units = match.get("unit_production", {}).get(player, {})
    vill_count = units.get("Villager", 0)
    if vill_count <= 0:
        return None

    # Resource score: try resource_score field, then summary
    resource_score = None
    # Check player data for score
    for p in match.get("players", []):
        if p.get("name") == player or (hasattr(p, "get") and p.get("name", "").lower() == player.lower()):
            resource_score = p.get("resource_score") or p.get("economy_score")
            break

    if resource_score is None:
        # Fallback: estimate from duration and vill count (rough)
        # Avg villager gathers ~25 resources/min
        duration_min = match.get("duration_secs", 0) / 60.0
        if duration_min <= 0:
            return None
        # Estimate: avg active vills * 25 res/min * duration
        # This is very rough, better to return None if no score
        return None

    return round(resource_score / vill_count, 1)


def compute_all_metrics(match: dict, player: str) -> dict:
    """Calcula todas as métricas disponíveis para um jogador em uma partida.

    Conveniência para chamar todas as métricas de uma vez.

    Args:
        match: dict de partida (idealmente enriquecido).
        player: nome do jogador.

    Returns:
        Dict com nome_da_metrica → valor (ou None).
    """
    return {
        "tc_idle_percent": tc_idle_percent(match, player),
        "farm_gap_average": farm_gap_average(match, player),
        "military_timing_index": military_timing_index(match, player),
        "tc_count_progression": tc_count_progression(match, player),
        "estimated_idle_villager_time": estimated_idle_villager_time(match, player),
        "villager_production_rate_by_age": villager_production_rate_by_age(match, player),
        "resource_collection_efficiency": resource_collection_efficiency(match, player),
    }
