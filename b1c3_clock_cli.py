#!/usr/bin/env python3
"""
B1C3 Clock — CLI

Usage:
  python b1c3_clock_cli.py [--ferm-start YYYY-MM-DD] [--time YYYY-MM-DDTHH:MM[Z]] [--json]

Defaults: current UTC time; fermentation start = today (day 0 / Sealed).
"""
import argparse
import json
import sys
from datetime import datetime, date, timezone

from b1c3_clock_engine import get_clock_state, get_week_start, FERMENTATION_PHASES


# -----------------------------------------------------------------------
# ASCII art bar helpers
# -----------------------------------------------------------------------

def _bar(filled: int, total: int, width: int = 20) -> str:
    """Render a filled bar like [████░░░░░░]."""
    n = round(filled / total * width)
    return "[" + "█" * n + "░" * (width - n) + "]"


def _arc_bar(bout_index: int, total: int = 6, width: int = 22) -> str:
    """Outer ring: sleeping bouts are ▒, waking bouts are █, current is highlighted."""
    from b1c3_clock_engine import is_sleeping
    chars = []
    seg_w = width // total
    for i in range(total):
        if i == bout_index:
            chars.append("▓" * seg_w)
        elif is_sleeping(i):
            chars.append("░" * seg_w)
        else:
            chars.append("█" * seg_w)
    return "[" + "".join(chars) + "]"


def _recovery_bar(cycle_index: int, total: int = 8, width: int = 16) -> str:
    """Inner ring: current segment bright, last segment muted."""
    chars = []
    seg_w = width // total
    for i in range(total):
        if i == cycle_index:
            ch = "▓"
        elif i == 7:
            ch = "░"
        else:
            ch = "█"
        chars.append(ch * seg_w)
    return "[" + "".join(chars) + "]"


# -----------------------------------------------------------------------
# Renderer
# -----------------------------------------------------------------------

PHASE_ICONS = ["⬜", "💧", "🔵", "🟡", "🟢", "✅", "🔴"]


def render_text(state: dict) -> str:
    dc = state["day_cycle"]
    rs = state["recovery_state"]
    fm = state["fermentation"]
    ts = state["timestamp"]

    bout_bar  = _arc_bar(dc["bout_index"])
    cycle_bar = _recovery_bar(rs["cycle_index"])
    icon      = PHASE_ICONS[fm["phase_index"]]
    state_tag = f"({'RECOVERY' if rs['is_in_recovery'] else 'ACTIVE'})"

    lines = [
        f"B1C3 Clock  [{ts[:16].replace('T', ' ')} UTC]",
        "",
        f"  Day Cycle    Bout {dc['bout_number']} of {dc['total_bouts']}  ({dc['label']})",
        f"  {bout_bar}",
        "",
        f"  Recovery     Cycle {rs['cycle_number']} of {rs['total_cycles']}  {state_tag}",
        f"  {cycle_bar}",
        "",
        f"  Fermentation Day {fm['days_elapsed']} of {fm['total_phases']}  {icon}  {fm['phase_name']}",
        "",
    ]
    return "\n".join(lines)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="B1C3 Clock — show current time as B1C3 state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--ferm-start",
        metavar="YYYY-MM-DD",
        default=None,
        help="Fermentation start date (default: Monday of current week)",
    )
    p.add_argument(
        "--time",
        metavar="DATETIME",
        default=None,
        help="ISO datetime to query (default: now UTC). Append Z for UTC.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit raw JSON state instead of text",
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Resolve timestamp
    if args.time:
        raw = args.time.rstrip("Z")
        try:
            ts = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: cannot parse --time value '{args.time}'", file=sys.stderr)
            sys.exit(1)
    else:
        ts = datetime.now(tz=timezone.utc)

    # Resolve fermentation start
    if args.ferm_start:
        try:
            ferm_start = date.fromisoformat(args.ferm_start)
        except ValueError:
            print(f"Error: cannot parse --ferm-start value '{args.ferm_start}'", file=sys.stderr)
            sys.exit(1)
    else:
        ferm_start = get_week_start(ts.date())  # Monday of current week

    state = get_clock_state(ts, ferm_start)

    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(render_text(state))


if __name__ == "__main__":
    main()
