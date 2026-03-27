# B1C3 Clock — Current State

**Timestamp:** 2026-03-27 19:57 UTC (Friday)

---

## What the webapp should be showing

### Ring 1 — Day Cycle (outer ring)
- 6 segments total
- Segments 1–2 are dark (sleeping arc, 00:00–08:00)
- Segments 3–6 are lit (waking arc, 08:00–24:00)
- **Segment 5 is highlighted/glowing** — we are in Bout 5 of 6 (16:00–20:00)

### Ring 2 — Recovery (middle ring)
- 8 segments total
- **Segment 8 is highlighted and muted/desaturated** — this is the recovery segment
- State label reads: **RECOVERY**
- We are in the final 30-minute window of Bout 5 (19:30–20:00)

### Ring 3 — Fermentation (centre)
- 7 phases total
- **Segment 5 is highlighted** — Day 5: Settled
- Colour is mid-gradient between sky blue and grass green (~`#81ca83`)
- It is Friday; the week started Monday (Mon = Day 1)

### Colour
- Base colour: `#81ca83` (muted, because state is RECOVERY)
- All highlighted segments should appear desaturated/dimmed relative to ACTIVE state

---

## Summary in plain language

> It is Friday evening. The fifth work bout of the day is in its final recovery window — the last 30 minutes before the day's final bout begins. The week is well into its second half: things have settled and the energy is stable, not frantic. Nothing is urgent. The clock says: coast into the weekend.
