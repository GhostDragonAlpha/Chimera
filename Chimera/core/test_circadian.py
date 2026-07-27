"""Tests for core.circadian — run: python core/test_circadian.py"""

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PASS = TOTAL = 0


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    print(("  ok  " if cond else "FAIL  ") + name)
    PASS += cond


def main():
    import core.circadian as c
    tmp = Path(tempfile.mkdtemp(prefix="circ_test_"))
    c.LAST_NIGHT = tmp / "last_night.json"

    # 1: phase mapping across the day
    check("phase: 02:00 is night", c.phase_of(2) == "night")
    check("phase: 23:00 is night", c.phase_of(23) == "night")
    check("phase: 07:00 is dawn", c.phase_of(7) == "dawn")
    check("phase: 13:00 is day", c.phase_of(13) == "day")
    check("phase: 20:00 is dusk", c.phase_of(20) == "dusk")

    # 2: night window start (most recent 22:00)
    ws_evening = c._night_window_start(datetime(2026, 7, 12, 23, 30))
    check("window start: evening -> today 22:00",
          ws_evening == datetime(2026, 7, 12, 22, 0))
    ws_smallhours = c._night_window_start(datetime(2026, 7, 13, 3, 0))
    check("window start: small hours -> yesterday 22:00",
          ws_smallhours == datetime(2026, 7, 12, 22, 0))

    # 3: no record yet -> due
    due, _ = c.night_due(datetime(2026, 7, 12, 23, 0))
    check("no record -> night due", due)

    # 4: mark + not-due same evening
    c.mark_night_ran(datetime(2026, 7, 12, 22, 30))
    due, reason = c.night_due(datetime(2026, 7, 12, 23, 0))
    check("just ran this window -> not due", not due)

    # 5: overdue safety (>20h) even during day
    c.mark_night_ran(datetime(2026, 7, 11, 22, 30))
    due, reason = c.night_due(datetime(2026, 7, 12, 22, 0))   # ~23.5h later, day/dusk edge
    check("overdue >20h -> due regardless of hour", due and "overdue" in reason)

    # 6: night hours, last night before this window opened -> due
    c.mark_night_ran(datetime(2026, 7, 12, 21, 0))            # before 22:00 window
    due, reason = c.night_due(datetime(2026, 7, 12, 23, 0))
    check("night hours + stale window -> due", due and "window" in reason)

    # 7: tick self-paces (run=False never runs; status well-formed)
    st = c.tick(run=False, now=datetime(2026, 7, 12, 13, 0))
    check("tick status shape + no run when run=False",
          st["phase"] == "day" and st["ran_night"] is False and "night_due" in st)

    # 8: preflight_line renders the directive when due
    c.mark_night_ran(datetime(2026, 7, 10, 22, 0))            # very stale
    line = c.preflight_line(datetime(2026, 7, 12, 23, 0))
    check("preflight line shouts when night due",
          "[0] Circadian" in line and "NIGHT IS DUE" in line)

    print(f"\n{PASS}/{TOTAL} tests passed")
    return 0 if PASS == TOTAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
