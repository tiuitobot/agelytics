"""Testes básicos para agelytics.metrics."""

from agelytics.metrics import (
    tc_idle_percent,
    farm_gap_average,
    military_timing_index,
    tc_count_progression,
    compute_all_metrics,
    estimated_idle_villager_time,
    villager_production_rate_by_age,
    resource_collection_efficiency,
)


def _base_match(**overrides):
    """Match base para testes."""
    m = {
        "duration_secs": 2400.0,
        "age_ups": [
            {"player": "Alice", "age": "Feudal Age", "timestamp_secs": 600.0},
            {"player": "Alice", "age": "Castle Age", "timestamp_secs": 1000.0},
            {"player": "Alice", "age": "Imperial Age", "timestamp_secs": 1800.0},
        ],
        "tc_idle": {"Alice": 240.0},
        "estimated_idle_villager_time": {"Alice": 180.5},
        "vill_queue_timestamps": {"Alice": [
            # Dark Age (0-600): 10 vills
            25, 50, 75, 100, 125, 150, 175, 200, 225, 250,
            # Feudal (600-1000): 8 vills  
            625, 650, 675, 700, 725, 750, 775, 800,
            # Castle (1000-1800): 5 vills
            1050, 1100, 1200, 1400, 1600,
            # Imperial (1800-2400): 2 vills
            1900, 2100,
        ]},
        "players": [{"name": "Alice", "resource_score": 8000}],
        "buildings": {"Alice": {"Farm": 20, "Town Center": 2}},
        "unit_production": {"Alice": {"Knight": 15, "Villager": 80}},
        "_farm_build_timestamps": {"Alice": [
            500, 520, 540,  # pre-castle
            1010, 1040, 1070, 1100, 1130, 1160,  # post-castle
        ]},
        "_first_military_timestamp": {"Alice": 700.0},
        "_tc_build_timestamps": {"Alice": [1100.0, 1400.0]},
    }
    m.update(overrides)
    return m


class TestTcIdlePercent:
    def test_basic(self):
        m = _base_match()
        result = tc_idle_percent(m, "Alice")
        assert result == 10.0  # 240/2400 * 100

    def test_no_data(self):
        m = _base_match(tc_idle={})
        assert tc_idle_percent(m, "Alice") is None

    def test_zero_duration(self):
        m = _base_match(duration_secs=0)
        assert tc_idle_percent(m, "Alice") is None

    def test_unknown_player(self):
        m = _base_match()
        assert tc_idle_percent(m, "Bob") is None


class TestFarmGapAverage:
    def test_basic(self):
        m = _base_match()
        result = farm_gap_average(m, "Alice")
        # Post-castle: 1010,1040,1070,1100,1130,1160 → gaps: 30,30,30,30,30
        assert result == 30.0

    def test_no_castle_age(self):
        m = _base_match(age_ups=[])
        assert farm_gap_average(m, "Alice") is None

    def test_no_farm_timestamps(self):
        m = _base_match(_farm_build_timestamps={})
        assert farm_gap_average(m, "Alice") is None

    def test_ignores_large_gaps(self):
        m = _base_match(_farm_build_timestamps={
            "Alice": [1010, 1040, 1200]  # gap de 160s ignorado
        })
        result = farm_gap_average(m, "Alice")
        assert result == 30.0  # só o gap de 30


class TestMilitaryTimingIndex:
    def test_basic(self):
        m = _base_match()
        result = military_timing_index(m, "Alice")
        assert result == 0.7  # 700/1000

    def test_early_rush(self):
        m = _base_match(_first_military_timestamp={"Alice": 400.0})
        assert military_timing_index(m, "Alice") == 0.4

    def test_no_military(self):
        m = _base_match(_first_military_timestamp={})
        assert military_timing_index(m, "Alice") is None

    def test_no_castle(self):
        m = _base_match(age_ups=[])
        assert military_timing_index(m, "Alice") is None


class TestTcCountProgression:
    def test_basic(self):
        m = _base_match()
        result = tc_count_progression(m, "Alice")
        assert result == [(0.0, 1), (1100.0, 2), (1400.0, 3)]

    def test_no_extra_tcs(self):
        m = _base_match(_tc_build_timestamps={}, buildings={"Alice": {"Town Center": 0}})
        result = tc_count_progression(m, "Alice")
        assert result == [(0.0, 1)]

    def test_no_timestamps_but_count(self):
        """Sem timestamps mas com contagem — retorna None (não pode determinar quando)."""
        m = _base_match(_tc_build_timestamps={})
        result = tc_count_progression(m, "Alice")
        assert result is None


class TestEstimatedIdleVillagerTime:
    def test_basic(self):
        m = _base_match()
        result = estimated_idle_villager_time(m, "Alice")
        assert result == 180.5

    def test_no_data(self):
        m = _base_match(estimated_idle_villager_time={})
        assert estimated_idle_villager_time(m, "Alice") is None

    def test_unknown_player(self):
        m = _base_match()
        assert estimated_idle_villager_time(m, "Bob") is None


class TestVillagerProductionRateByAge:
    def test_basic(self):
        m = _base_match()
        result = villager_production_rate_by_age(m, "Alice")
        assert result is not None
        assert "Dark Age" in result
        assert "Feudal Age" in result
        assert "Castle Age" in result
        assert "Imperial Age" in result
        # Dark Age: 10 vills in 10 min = 1.0/min
        assert result["Dark Age"] == 1.0

    def test_no_data(self):
        m = _base_match(vill_queue_timestamps={})
        assert villager_production_rate_by_age(m, "Alice") is None

    def test_no_age_ups(self):
        """Sem age ups, tudo é Dark Age."""
        m = _base_match(age_ups=[])
        result = villager_production_rate_by_age(m, "Alice")
        assert result is not None
        assert "Dark Age" in result
        assert len(result) == 1  # só Dark Age


class TestResourceCollectionEfficiency:
    def test_basic(self):
        m = _base_match()
        result = resource_collection_efficiency(m, "Alice")
        assert result == 100.0  # 8000 / 80

    def test_no_villagers(self):
        m = _base_match(unit_production={"Alice": {"Knight": 15}})
        assert resource_collection_efficiency(m, "Alice") is None

    def test_no_resource_score(self):
        m = _base_match(players=[{"name": "Alice"}])
        assert resource_collection_efficiency(m, "Alice") is None


class TestComputeAll:
    def test_returns_all_keys(self):
        m = _base_match()
        result = compute_all_metrics(m, "Alice")
        assert set(result.keys()) == {
            "tc_idle_percent", "farm_gap_average",
            "military_timing_index", "tc_count_progression",
            "estimated_idle_villager_time", "villager_production_rate_by_age",
            "resource_collection_efficiency",
        }
