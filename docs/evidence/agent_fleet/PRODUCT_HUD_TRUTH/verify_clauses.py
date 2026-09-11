"""product-hud-truth-01 — the clause checker (P1-P5; P6 is the blind judge's).

    python verify_clauses.py <dir-with-keyframe_docs.json> <out-verify-txt>

Evaluates the PREREGISTRATION.md clauses against a run's captured records.
Zero tolerance choices made here: every bound is the preregistered one.
The run1 F2 age failure is EXPECTED to fire here (retained evidence); the
correction note in VERIFICATION.md records why the origin semantics changed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

THETA_TOL = 0.05      # P1/P2: displayed vs commanded (deg)
CLOCK_TOL = 0.10      # P3: readout value / delta vs declared timeline (s)
PEAKS = {"shoulder_R": 36.0, "elbow_R": 75.0}
DRIVEN = set(PEAKS)
FPS = 10


def theta_of(row: str, name: str) -> float | None:
    """Parse '<name><+d.dd>' out of a HUD-row / readout string."""
    i = row.find(name)
    if i < 0:
        return None
    j = i + len(name)
    k = j
    while k < len(row) and (row[k] in "+-.0123456789"):
        k += 1
    try:
        return float(row[j:k])
    except ValueError:
        return None


def main() -> int:
    run_dir = Path(sys.argv[1])
    docs = json.loads((run_dir / "keyframe_docs.json").read_text())
    lines: list[tuple[str, str, str]] = []      # (verdict, clause, detail)

    def check(clause: str, ok: bool, detail: str) -> None:
        lines.append(("PASS" if ok else "FAIL", clause, detail))

    # commanded thetas per keyframe (the PR #97 script law, recomputed)
    peaks = dict(PEAKS)

    def commanded(i: int) -> dict[str, float]:
        import math
        s = 0.0
        if i >= 10 and i < 20:
            x = (i - 9) / 10.0
            s = x * x * (3 - 2 * x)
        elif i >= 20 and i < 30:
            s = 1.0
        elif i >= 30:
            x = (i - 29) / 15.0
            s = 1.0 - x * x * (3 - 2 * x)
        return {n: s * v for n, v in peaks.items()}

    rows_by_i: dict[int, str] = {}
    readout_by_i: dict[int, str] = {}   # transcribed glass readout, injected below
    for d in docs:
        i = d["i"]
        rows = d["studio_chrome"].get("hud_rows") or []
        rows_by_i[i] = rows[0] if rows else ""
        show = d.get("show") or {}
        # P3 numeric channel: the pinned clock
        want = round(i / FPS, 6)
        got = show.get("time")
        check(f"P3.show_pin(i={i})", got is not None and abs(got - want) <= 0.001,
              f"GET /show time={got} want={want}")
        # P2: engine truth thetas vs commanded
        jt = {j.get("name"): j.get("theta") for j in (d["joints"].get("joints") or [])
              if j.get("name") in DRIVEN}
        cmd = commanded(i)
        for n in PEAKS:
            ok = n in jt and jt[n] is not None and abs(jt[n] - cmd[n]) <= THETA_TOL
            check(f"P2.engine_theta(i={i},{n})", ok,
                  f"st+7={jt.get(n)} commanded={cmd[n]}")

    # P1: the joint row
    for d in docs:
        i = d["i"]
        row = rows_by_i.get(i, "")
        cmd = commanded(i)
        if i < 10:
            check(f"P4.row_prefix(i={i})", row.startswith("SHOW "), row[:40])
            continue
        check(f"P1.row_prefix(i={i})", row.startswith("EDIT "), row[:40])
        named_ok = all(n in row for n in ("shoulder_R", "elbow_R"))
        check(f"P1.row_names(i={i})", named_ok, row)
        for n in PEAKS:
            v = theta_of(row, n)
            ok = v is not None and abs(v - cmd[n]) <= THETA_TOL
            check(f"P1.row_theta(i={i},{n})", ok,
                  f"row={v} commanded={cmd[n]}")
    for i in (20, 25):
        row = rows_by_i.get(i, "")
        ok = (theta_of(row, "shoulder_R") is not None
              and abs(theta_of(row, "shoulder_R") - 36.0) <= THETA_TOL
              and abs(theta_of(row, "elbow_R") - 75.0) <= THETA_TOL)
        check(f"P1.peaks(g{i:03d})", ok, row)

    # P3 glass: transcribed readouts (hand-transcribed from the keyframe PNGs;
    # the transcription file feeds this check)
    tr_path = run_dir / "readout_transcription.json"
    if tr_path.exists():
        tr = json.loads(tr_path.read_text())
        for i, txt in sorted(tr.items(), key=lambda kv: int(kv[0])):
            i = int(i)
            if i < 10:
                continue
            check(f"P3.readout_prefix(i={i})", txt.startswith("EDIT t = "), txt[:60])
            check(f"P3.readout_no_lap(i={i})", "(lap" not in txt and "112.0" not in txt, txt[:80])
            check(f"P3.readout_paused(i={i})", "sweep paused" in txt, txt[-60:])
            want = round(i / FPS, 6)
            # the readout's clock number is the token after 't = '
            try:
                num = float(txt.split("t = ")[1].split(" s")[0])
                check(f"P3.readout_clock(i={i})", abs(num - want) <= CLOCK_TOL,
                      f"readout={num} want={want}")
            except (IndexError, ValueError) as e:
                check(f"P3.readout_clock(i={i})", False, f"unparsed: {e}")
        ks = sorted(int(k) for k in tr if int(k) >= 12)
        for a, b in zip(ks, ks[1:]):
            try:
                da = float(tr[str(a)].split("t = ")[1].split(" s")[0])
                db = float(tr[str(b)].split("t = ")[1].split(" s")[0])
                want = (b - a) / FPS
                check(f"P3.delta(g{a:03d}->g{b:03d})", abs((db - da) - want) <= CLOCK_TOL,
                      f"delta={db - da:.3f} want={want}")
            except (IndexError, ValueError) as e:
                check(f"P3.delta(g{a:03d}->g{b:03d})", False, f"unparsed: {e}")
    else:
        check("P3.readout_transcription", False, f"missing {tr_path}")

    # P5: the reel's newest entry in the driven regime
    for d in docs:
        i = d["i"]
        if i < 25:      # the 12-entry ring carries pre-drive tail early; declared
            continue
        ent = (d.get("reel") or {}).get("entries") or []
        newest = ent[-1] if ent else {}
        j = str(newest.get("joint", ""))
        check(f"P5.reel_edit(i={i})", j.startswith("EDIT ") or "EDIT" in j,
              f"joint={j!r} theta={newest.get('theta')}")

    fails = [l for l in lines if l[0] == "FAIL"]
    out = "\n".join(f"[{v}] {c} {det}" for v, c, det in lines) + \
        f"\n\nTOTAL {len(lines)} checks, {len(fails)} FAIL\n"
    (run_dir / sys.argv[2]).write_text(out)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
