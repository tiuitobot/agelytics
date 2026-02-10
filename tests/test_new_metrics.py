"""Testes para as métricas determinísticas adicionadas."""

import pytest
from agelytics.metrics import (
    farm_gap_average,
    military_timing_index,
    tc_count_progression,
    tc_idle_percent,
)


def test_farm_gap_average_insufficient_data():
    """Farm gap deve retornar None quando não há dados suficientes."""
    match = {
        "age_ups": [{"player": "Player1", "age": "Castle Age", "timestamp_secs": 600}],
        "_farm_build_timestamps": {"Player1": [650]},  # Apenas 1 farm
    }
    assert farm_gap_average(match, "Player1") is None


def test_farm_gap_average_calculation():
    """Farm gap deve calcular média corretamente."""
    match = {
        "age_ups": [{"player": "Player1", "age": "Castle Age", "timestamp_secs": 600}],
        "_farm_build_timestamps": {
            "Player1": [650, 680, 710, 750]  # Gaps: 30, 30, 40
        },
    }
    result = farm_gap_average(match, "Player1")
    assert result is not None
    assert 30 <= result <= 35  # Média dos gaps: (30+30+40)/3 = 33.33


def test_military_timing_index_before_castle():
    """Timing militar antes de Castle Age deve ser < 1.0 (rush)."""
    match = {
        "age_ups": [{"player": "Player1", "age": "Castle Age", "timestamp_secs": 600}],
        "_first_military_timestamp": {"Player1": 400},
    }
    result = military_timing_index(match, "Player1")
    assert result is not None
    assert result < 1.0


def test_military_timing_index_after_castle():
    """Timing militar após Castle Age deve ser > 1.0 (boom)."""
    match = {
        "age_ups": [{"player": "Player1", "age": "Castle Age", "timestamp_secs": 600}],
        "_first_military_timestamp": {"Player1": 720},
    }
    result = military_timing_index(match, "Player1")
    assert result is not None
    assert result > 1.0


def test_tc_count_progression_basic():
    """TC progression deve incluir TC inicial e TCs adicionais."""
    match = {
        "_tc_build_timestamps": {"Player1": [400, 700]},
    }
    result = tc_count_progression(match, "Player1")
    assert result is not None
    assert len(result) == 3  # (0,1), (400,2), (700,3)
    assert result[0] == (0.0, 1)  # TC inicial
    assert result[1] == (400.0, 2)
    assert result[2] == (700.0, 3)


def test_tc_count_progression_no_additional_tcs():
    """TC progression deve retornar apenas TC inicial se não há builds."""
    match = {
        "_tc_build_timestamps": {"Player1": []},
        "buildings": {"Player1": {"Town Center": 0}},
    }
    result = tc_count_progression(match, "Player1")
    assert result is not None
    assert result == [(0.0, 1)]


def test_tc_idle_percent():
    """TC idle percent deve calcular corretamente."""
    match = {
        "duration_secs": 1200,
        "tc_idle": {"Player1": 120},
    }
    result = tc_idle_percent(match, "Player1")
    assert result == 10.0  # 120/1200 * 100


def test_tc_idle_percent_no_data():
    """TC idle percent deve retornar None sem dados."""
    match = {
        "duration_secs": 1200,
        "tc_idle": {},
    }
    assert tc_idle_percent(match, "Player1") is None
