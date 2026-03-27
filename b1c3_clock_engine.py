"""
B1C3 Clock Engine — Pure state calculation, no side effects.

All public functions are deterministic given the same inputs.
ACTIVE/RECOVERY: the final 30-min segment of each 4-hour bout is RECOVERY,
all other segments are ACTIVE.
"""

from datetime import datetime, date, timedelta, timezone
from typing import Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Bouts 0 and 1 cover 00:00–08:00. Convention: sleep occupies first 8 h.
SLEEPING_BOUTS: frozenset = frozenset({0, 1})

FERMENTATION_PHASES = [
    "Sealed",    # day 0 — beginning
    "Bubbling",  # day 1 — active fermentation
    "Peak",      # day 2 — most active
    "Calming",   # day 3 — stabilising
    "Settled",   # day 4 — clear
    "Ready",     # day 5 — mature
    "Peaked",    # day 6+ — past prime / archive
]

# Colour gradient: sky blue → grass green (day 0 → day 6)
_SKY_BLUE: Tuple[int, int, int] = (135, 206, 235)
_GRASS_GREEN: Tuple[int, int, int] = (126, 200, 80)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _lerp_color(
    c1: Tuple[int, int, int],
    c2: Tuple[int, int, int],
    t: float,
) -> str:
    """Linear interpolation between two RGB colours; returns hex string."""
    t = max(0.0, min(t, 1.0))
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ---------------------------------------------------------------------------
# Axiom calculations
# ---------------------------------------------------------------------------

def get_week_start(d: date) -> date:
    """Return the Monday of the week containing *d* (ISO week: Mon=0)."""
    return d - timedelta(days=d.weekday())


def calculate_bout(timestamp: datetime) -> int:
    """
    Bout index (0–5) for the given timestamp.
    Each bout spans exactly 4 hours:
      0 → 00:00–04:00  (sleeping)
      1 → 04:00–08:00  (sleeping)
      2 → 08:00–12:00  (waking)
      3 → 12:00–16:00  (waking)
      4 → 16:00–20:00  (waking)
      5 → 20:00–24:00  (waking)
    """
    return timestamp.hour // 4


def calculate_recovery_cycle(timestamp: datetime) -> int:
    """
    Recovery-cycle index (0–7) within the current bout.
    Each cycle spans 30 minutes (8 × 30 min = 4 h).
    """
    minutes_in_bout = (timestamp.hour % 4) * 60 + timestamp.minute
    return minutes_in_bout // 30


def is_sleeping(bout_index: int) -> bool:
    """True when the bout falls in the sleeping arc (bouts 0–1)."""
    return bout_index in SLEEPING_BOUTS


def is_in_recovery(recovery_cycle_index: int) -> bool:
    """
    True when the current 30-min segment is a recovery segment.
    Convention: cycle 7 (the final 30 min of each bout) is RECOVERY.
    """
    return recovery_cycle_index == 7


def calculate_fermentation_phase(
    fermentation_start: date,
    current_date: date,
) -> dict:
    """
    Returns phase info for the multi-day fermentation process.
    Clamped to 0–6 days (maps to the 7 named phases).
    """
    days_elapsed = (current_date - fermentation_start).days
    days_elapsed = max(0, min(days_elapsed, 6))
    return {
        "days_elapsed": days_elapsed + 1,  # 1-based (1-7): Mon=1 … Sun=7
        "phase_index": days_elapsed,         # 0-based, internal array index
        "phase_name": FERMENTATION_PHASES[days_elapsed],
        "total_phases": 7,
        "start_date": fermentation_start.isoformat(),
    }


def calculate_colors(fermentation_days: int, in_recovery: bool) -> dict:
    """
    Base colour from sky-blue→grass-green gradient keyed on fermentation day.
    Muted flag toggled during recovery segments.
    """
    t = fermentation_days / 6.0
    base_hex = _lerp_color(_SKY_BLUE, _GRASS_GREEN, t)
    return {
        "base_color": base_hex,
        "is_muted": in_recovery,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_clock_state(timestamp: datetime, fermentation_start: date) -> dict:
    """
    Primary engine function.  Returns the complete, frozen clock state for
    the given moment.

    Parameters
    ----------
    timestamp : datetime
        Timezone-aware datetime.  Raises ValueError if naive.
    fermentation_start : date
        Calendar date on which the current fermentation cycle began.

    Returns
    -------
    dict
        Complete clock state.  Suitable for JSON serialisation.
    """
    if timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware (e.g. use timezone.utc)")

    bout_index = calculate_bout(timestamp)
    recovery_index = calculate_recovery_cycle(timestamp)
    sleeping = is_sleeping(bout_index)
    in_recovery = is_in_recovery(recovery_index)

    fermentation = calculate_fermentation_phase(
        fermentation_start, timestamp.date()
    )
    colors = calculate_colors(fermentation["phase_index"], in_recovery)

    return {
        "timestamp": timestamp.isoformat(),
        "day_cycle": {
            "bout_index": bout_index,           # 0-based
            "bout_number": bout_index + 1,      # 1-based (human-readable)
            "total_bouts": 6,
            "is_sleeping": sleeping,
            "is_waking": not sleeping,
            "label": "Sleeping" if sleeping else "Waking",
        },
        "recovery_state": {
            "cycle_index": recovery_index,          # 0-based
            "cycle_number": recovery_index + 1,     # 1-based (human-readable)
            "total_cycles": 8,
            "is_active": not in_recovery,
            "is_in_recovery": in_recovery,
            "state_label": "RECOVERY" if in_recovery else "ACTIVE",
        },
        "fermentation": fermentation,
        "colors": colors,
    }
