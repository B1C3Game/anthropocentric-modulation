"""Tests for b1c3_clock_engine — all four axioms + colours + main API."""

import pytest
from datetime import datetime, date, timezone

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from b1c3_clock_engine import (
    calculate_bout,
    calculate_recovery_cycle,
    calculate_fermentation_phase,
    calculate_colors,
    get_clock_state,
    is_sleeping,
    is_in_recovery,
    FERMENTATION_PHASES,
)


def ts(hour: int, minute: int = 0) -> datetime:
    """Convenience: build a UTC datetime on 2026-03-27."""
    return datetime(2026, 3, 27, hour, minute, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Axiom 1: Bout (4-hour blocks)
# ---------------------------------------------------------------------------

class TestCalculateBout:
    def test_midnight(self):
        assert calculate_bout(ts(0)) == 0

    def test_3am(self):
        assert calculate_bout(ts(3, 59)) == 0

    def test_4am_starts_bout_1(self):
        assert calculate_bout(ts(4)) == 1

    def test_8am_starts_bout_2(self):
        assert calculate_bout(ts(8)) == 2

    def test_noon_is_bout_3(self):
        assert calculate_bout(ts(12)) == 3

    def test_16h_is_bout_4(self):
        assert calculate_bout(ts(16)) == 4

    def test_17h27_is_bout_4(self):
        assert calculate_bout(ts(17, 27)) == 4

    def test_20h_is_bout_5(self):
        assert calculate_bout(ts(20)) == 5

    def test_23h59_is_still_bout_5(self):
        assert calculate_bout(ts(23, 59)) == 5

    def test_six_bouts_cover_full_day(self):
        seen = {calculate_bout(ts(h)) for h in range(24)}
        assert seen == {0, 1, 2, 3, 4, 5}


# ---------------------------------------------------------------------------
# Axiom 2: Sleeping / Waking Arc
# ---------------------------------------------------------------------------

class TestIsSleeping:
    def test_bout_0_sleeping(self):
        assert is_sleeping(0) is True

    def test_bout_1_sleeping(self):
        assert is_sleeping(1) is True

    def test_bout_2_waking(self):
        assert is_sleeping(2) is False

    def test_bout_5_waking(self):
        assert is_sleeping(5) is False

    def test_sleeping_covers_8h(self):
        sleeping_hours = [h for h in range(24) if is_sleeping(h // 4)]
        assert len(sleeping_hours) == 8

    def test_waking_covers_16h(self):
        waking_hours = [h for h in range(24) if not is_sleeping(h // 4)]
        assert len(waking_hours) == 16


# ---------------------------------------------------------------------------
# Axiom 4: Recovery cycle (30-minute segments)
# ---------------------------------------------------------------------------

class TestCalculateRecoveryCycle:
    def test_start_of_bout_is_cycle_0(self):
        assert calculate_recovery_cycle(ts(8, 0)) == 0

    def test_29min_still_cycle_0(self):
        assert calculate_recovery_cycle(ts(8, 29)) == 0

    def test_30min_is_cycle_1(self):
        assert calculate_recovery_cycle(ts(8, 30)) == 1

    def test_60min_is_cycle_2(self):
        assert calculate_recovery_cycle(ts(9, 0)) == 2

    def test_210min_is_cycle_7(self):
        # bout 2 starts at 08:00; 08:00 + 3h30m = 11:30
        assert calculate_recovery_cycle(ts(11, 30)) == 7

    def test_cycle_within_second_bout(self):
        # bout 1 starts at 04:00; 04:45 → 45 min in → cycle 1
        assert calculate_recovery_cycle(ts(4, 45)) == 1

    def test_eight_cycles_per_bout(self):
        # All 240 minutes of bout 2 (08:00–12:00) should map to exactly cycles 0–7
        from datetime import timedelta
        base = datetime(2026, 3, 27, 8, 0, tzinfo=timezone.utc)
        cycles = {calculate_recovery_cycle(base + timedelta(minutes=m)) for m in range(240)}
        assert cycles == set(range(8))


class TestIsInRecovery:
    def test_cycle_0_is_active(self):
        assert is_in_recovery(0) is False

    def test_cycle_6_is_active(self):
        assert is_in_recovery(6) is False

    def test_cycle_7_is_recovery(self):
        assert is_in_recovery(7) is True

    def test_only_last_cycle_is_recovery(self):
        recovery_cycles = [c for c in range(8) if is_in_recovery(c)]
        assert recovery_cycles == [7]


# ---------------------------------------------------------------------------
# Fermentation phases
# ---------------------------------------------------------------------------

class TestCalculateFermentationPhase:
    def test_same_day_is_sealed(self):
        result = calculate_fermentation_phase(date(2026, 3, 27), date(2026, 3, 27))
        assert result["phase_name"] == "Sealed"
        assert result["days_elapsed"] == 1

    def test_day_1_is_bubbling(self):
        result = calculate_fermentation_phase(date(2026, 3, 26), date(2026, 3, 27))
        assert result["phase_name"] == "Bubbling"

    def test_day_2_is_peak(self):
        result = calculate_fermentation_phase(date(2026, 3, 25), date(2026, 3, 27))
        assert result["phase_name"] == "Peak"

    def test_day_3_is_calming(self):
        result = calculate_fermentation_phase(date(2026, 3, 24), date(2026, 3, 27))
        assert result["phase_name"] == "Calming"

    def test_day_4_is_settled(self):
        result = calculate_fermentation_phase(date(2026, 3, 23), date(2026, 3, 27))
        assert result["phase_name"] == "Settled"

    def test_day_5_is_ready(self):
        result = calculate_fermentation_phase(date(2026, 3, 22), date(2026, 3, 27))
        assert result["phase_name"] == "Ready"

    def test_day_6_is_peaked(self):
        result = calculate_fermentation_phase(date(2026, 3, 21), date(2026, 3, 27))
        assert result["phase_name"] == "Peaked"

    def test_clamped_above_6(self):
        result = calculate_fermentation_phase(date(2026, 3, 1), date(2026, 3, 27))
        assert result["days_elapsed"] == 7
        assert result["phase_name"] == "Peaked"

    def test_clamped_below_0(self):
        # fermentation start in the future — should clamp to day 1
        result = calculate_fermentation_phase(date(2026, 3, 28), date(2026, 3, 27))
        assert result["days_elapsed"] == 1

    def test_total_phases(self):
        result = calculate_fermentation_phase(date(2026, 3, 24), date(2026, 3, 27))
        assert result["total_phases"] == 7

    def test_all_phases_reachable(self):
        from datetime import timedelta
        start = date(2026, 3, 21)
        names = [
            calculate_fermentation_phase(start, start + timedelta(days=i))["phase_name"]
            for i in range(7)
        ]
        assert names == FERMENTATION_PHASES


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

class TestCalculateColors:
    def test_day_0_is_sky_blue(self):
        result = calculate_colors(0, False)
        assert result["base_color"] == "#87ceeb"

    def test_day_6_is_grass_green(self):
        result = calculate_colors(6, False)
        assert result["base_color"] == "#7ec850"

    def test_not_muted_when_active(self):
        result = calculate_colors(3, False)
        assert result["is_muted"] is False

    def test_muted_when_in_recovery(self):
        result = calculate_colors(3, True)
        assert result["is_muted"] is True


# ---------------------------------------------------------------------------
# Full state: get_clock_state
# ---------------------------------------------------------------------------

class TestGetClockState:
    FERM_START = date(2026, 3, 24)

    def test_raises_on_naive_timestamp(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            get_clock_state(datetime(2026, 3, 27, 17, 27), self.FERM_START)

    def test_17h27_bout_5_waking(self):
        state = get_clock_state(ts(17, 27), self.FERM_START)
        dc = state["day_cycle"]
        assert dc["bout_index"] == 4        # 0-based
        assert dc["bout_number"] == 5       # 1-based
        assert dc["is_waking"] is True
        assert dc["label"] == "Waking"

    def test_17h27_recovery_cycle_3_active(self):
        # Bout 4 starts at 16:00. 17:27 → 87 min in → cycle 2 (0-based) = 3 (1-based)
        state = get_clock_state(ts(17, 27), self.FERM_START)
        rs = state["recovery_state"]
        assert rs["cycle_index"] == 2
        assert rs["cycle_number"] == 3
        assert rs["is_active"] is True
        assert rs["state_label"] == "ACTIVE"

    def test_17h27_fermentation_calming(self):
        # 2026-03-27 minus 2026-03-24 = 3 days → Calming
        state = get_clock_state(ts(17, 27), self.FERM_START)
        assert state["fermentation"]["phase_name"] == "Calming"

    def test_sleeping_bout(self):
        state = get_clock_state(ts(3, 0), self.FERM_START)
        assert state["day_cycle"]["is_sleeping"] is True
        assert state["day_cycle"]["label"] == "Sleeping"

    def test_last_cycle_of_bout_is_recovery(self):
        # Bout 2 starts at 08:00; last cycle starts at 11:30
        state = get_clock_state(ts(11, 30), self.FERM_START)
        rs = state["recovery_state"]
        assert rs["cycle_index"] == 7
        assert rs["is_in_recovery"] is True
        assert rs["state_label"] == "RECOVERY"

    def test_timestamp_in_output(self):
        now = datetime(2026, 3, 27, 17, 27, tzinfo=timezone.utc)
        state = get_clock_state(now, self.FERM_START)
        assert state["timestamp"] == now.isoformat()

    def test_output_keys_present(self):
        state = get_clock_state(ts(12, 0), self.FERM_START)
        assert {"timestamp", "day_cycle", "recovery_state", "fermentation", "colors"} <= set(state)
