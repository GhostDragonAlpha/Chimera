"""run_judge.py -- ONE COMMAND: a blind-judge dyad run, registered.

    python tools/dyad_judge/run_judge.py --name <judge-name> [--base http://127.0.0.1:8206]
                                           [--wait-verdict 900] [--gate-report]

Merges the R8/R4 blind-judge playbook (docs/evidence/agent_fleet/SHIP/
R8_R4_PLAYBOOK/PLAYBOOK.md -- the judge protocol that works) with the standing
dyad machinery (senses, encode_movie, the verdict registry) into one pipeline.
THE STANDING RULE (operator directive 2026-09-14): no serial single-threaded
Python -- the phases OVERLAP:

    T_capture (thread)  timed screenshots through the playbook driver -- the
                        recording accumulates WHILE the judge plays.
    P_encode (process)  ffmpeg-segments the frames as they land
                        (multiprocessing: CPU-bound libx264 must not steal the
                        GIL from the I/O threads) -> recording.mp4.
    T_watch  (thread)   the dyad eye reads key frames ONE IMAGE PER CALL
                        (senses' one-image wall) WHILE they are captured and
                        encoded: senses eye first; if dark, the clearly-labeled
                        ollama-fallback; if dark, recorded dark.
    T_session (main)    the blind-compliant play script (landing -> controls ->
                        >=3 lessons -> press/hold/release/recover -> free play).

Every interval is logged in WALL-CLOCK ms (timeline.jsonl / encode_log.jsonl /
watch_log.jsonl share the epoch), so the overlap is MEASURED, not asserted.

Rule 0: the membrane is OPENED (statement+prediction+falsifier) BEFORE the run
and CLOSED after, with the dyadAnalysis: the NUMBER (novelty + dent/recovery
metrics) and the TERM (the buyer term from the verdict quotes), aligned. The
entry lands in tools/verdict_registry.json through tools/verdict.py's own
VerdictLedger, so `python tools/verdict.py status` shows it untouched.

THE VERDICT SHAPE SHIPPED: a tool cannot spawn a fresh agent session from
inside this lane, so the tool (a) writes judge_task.md -- the exact briefing a
fresh judge agent needs -- and waits (--wait-verdict N) for verdict.json to
appear in the session dir, (b) accepts --verdict-file for an already-written
verdict, and (c) supports --late-register for a verdict that arrives after the
run ended (reads the OPEN membrane number from run_state.json).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from multiprocessing import Process
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent
ROOT = TOOLS.parent
EVIDENCE = ROOT / "docs" / "evidence" / "agent_fleet" / "SHIP" / "DYAD_JUDGE"
CAPTURE_MS = 1200
SEG_FRAMES = 16
WATCH_DEADLINE_S = 300


def wall_ms() -> int:
    return round(time.time() * 1000)


# ── timeline: one append-only record of WHO ran WHEN (the overlap proof) ────
class Timeline:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()

    def event(self, phase: str, note: str, **extra):
        rec = {"wall_ms": wall_ms(),
               "wall": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "phase": phase, "note": note}
        rec.update(extra)
        with self.lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")


def _log_jsonl(path: Path, rec: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


# ── P_encode: segmented ffmpeg encode in its OWN PROCESS (CPU-bound) ────────
def _encode_worker(session_dir: str, fps: float, t0_ms: int):
    """Encode capture frames as they land, SEG_FRAMES at a time; concat at EOS.
    Writes encode_log.jsonl (single writer: this process). Intervals are logged
    against the PARENT's wall-clock epoch (t0_ms) so overlap is measurable."""
    sdir = Path(session_dir)
    shots = sdir / "shots"
    segs = sdir / "segs"
    segs.mkdir(parents=True, exist_ok=True)
    log = sdir / "encode_log.jsonl"
    sys.path.insert(0, str(ROOT / "ChimeraEngine"))
    start = wall_ms()

    def note(ev, **kw):
        _log_jsonl(log, {"wall_ms": wall_ms(), "rel_ms": wall_ms() - start,
                         "t0_ms": t0_ms, "ev": ev, **kw})

    note("start", pid=_pid())
    done_segs = 0
    consumed = 0
    while True:
        frames = sorted(shots.glob("cap_*.png")) if shots.exists() else []
        ready = len(frames) - consumed
        if ready >= SEG_FRAMES or (ready > 0 and (sdir / "_EOS").exists()):
            chunk = frames[consumed:consumed + SEG_FRAMES]
            consumed += len(chunk)
            seg = segs / f"seg_{done_segs:04d}.mp4"
            s = wall_ms()
            try:
                from cpp_bridge import encode_movie
                encode_movie([str(f) for f in chunk], str(seg), fps=fps)
                note("segment", seg=seg.name, frames=len(chunk),
                     ms=wall_ms() - s, ok=True, start_ms=s)
            except Exception as e:
                note("segment", seg=seg.name, ok=False, error=f"{type(e).__name__}: {e}")
            done_segs += 1
            continue
        if (sdir / "_EOS").exists():
            break
        time.sleep(1.5)
    seg_files = sorted(segs.glob("seg_*.mp4"))
    rec = sdir / "recording.mp4"
    if seg_files:
        lst = segs / "concat.txt"
        lst.write_text("".join(f"file '{f.as_posix()}'\n" for f in seg_files), encoding="utf-8")
        s = wall_ms()
        r = subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                            "-c", "copy", str(rec)], capture_output=True, text=True)
        note("concat", segments=len(seg_files), ok=r.returncode == 0,
             out=rec.name, ms=wall_ms() - s,
             error=None if r.returncode == 0 else r.stderr[-300:])
    else:
        note("concat", ok=False, error="no segments encoded")
    note("end")


def _pid():
    import os
    return os.getpid()


# ── T_capture: the timed recording, accumulated WHILE the judge plays ───────
class Capture(threading.Thread):
    def __init__(self, session, shots: Path, tl: Timeline, done: threading.Event):
        super().__init__(daemon=True, name="T_capture")
        self.session, self.shots, self.tl, self.done = session, shots, tl, done
        self.frames: list[tuple[str, int]] = []   # (path, wall_ms when the PNG landed)
        self.lock = threading.Condition()
        self.stop = False

    def run(self):
        n = 0
        fails = 0
        while not (self.stop and self.done.is_set()):
            if not self.stop:
                n += 1
                name = f"cap_{n:04d}"
                try:
                    self.session.send({"do": "shot", "name": name}, timeout_s=20.0)
                    f = self.shots / f"{name}.png"
                    if f.exists():
                        t = wall_ms()
                        with self.lock:
                            self.frames.append((str(f), t))
                            self.lock.notify_all()
                        self.tl.event("capture", name, frame=name, wall_ms=t)
                    fails = 0
                except Exception as e:
                    fails += 1
                    self.tl.event("capture", f"failed: {type(e).__name__}: {e}")
                    # a wedged or dead driver never answers again: stop feeding
                    # it (the 223911 run spammed a closed browser for 6 minutes
                    # because only the literal word TIMEOUT latched the stop)
                    if fails >= 2:
                        self.stop = True
            self.done.wait(CAPTURE_MS / 1000.0)


# ── T_watch: the dyad eye, reading frames WHILE they are produced ───────────
class Watch(threading.Thread):
    """Drip-reads early frames (max 3) until the press window is announced,
    then prioritizes the press window (hold + recovery), max 8 there.
    ONE IMAGE PER CALL -- the one-image wall, honored by construction."""

    MAX_DRIP = 3
    MAX_WINDOW = 8

    def __init__(self, session_dir: Path, session, tl: Timeline, done: threading.Event):
        super().__init__(daemon=True, name="T_watch")
        self.session_dir, self.session, self.tl, self.done = session_dir, session, tl, done
        self.read: set[str] = set()
        self.reports: list[dict] = []
        self.log = session_dir / "watch_log.jsonl"
        self.status = {"lane": "unprobed", "model": None, "reason": None}

    def _press_window(self):
        p = self.session.press
        return p if p.get("down_ms") and p.get("up_ms") else None

    def _pick(self, frames):
        press = self._press_window()
        if press:
            lo, hi = press["down_ms"] - 2500, press["up_ms"] + 12000
            in_win = [fr for fr in frames if fr[0] not in self.read and lo <= fr[1] <= hi]
            have = sum(1 for r in self.reports if r.get("in_window"))
            if in_win and have < self.MAX_WINDOW:
                return in_win[0][0], in_win[0][1], True
            # a press was announced but nothing new in-window: do not drip past it
            return None
        unread = [fr for fr in frames if fr[0] not in self.read]
        drips = sum(1 for r in self.reports if not r.get("in_window"))
        if unread and drips < self.MAX_DRIP:
            return unread[0][0], unread[0][1], False
        return None

    def run(self):
        from eye import DEFAULT_PROMPT, eye_status, read_frame
        deadline = time.time() + WATCH_DEADLINE_S
        self.status = eye_status()
        self.tl.event("watch", f"eye lane: {self.status['lane']} ({self.status['model']})",
                      lane=self.status["lane"], model=self.status["model"],
                      reason=self.status["reason"], wall_ms=wall_ms())
        cap = self.session.capture
        while time.time() < deadline:
            with cap.lock:
                frames = list(cap.frames)
            pick = self._pick(frames)
            if pick is None:
                if self.done.is_set() and not self._press_window():
                    break
                if self.done.is_set() and self._press_window() and \
                        len(frames) and all(f in self.read for f, _ in frames[-3:]) and \
                        not self._new_in_window(frames):
                    break
                time.sleep(1.0)
                continue
            f, t, in_win = pick
            self.read.add(f)
            t_start = wall_ms()
            r = read_frame(f, DEFAULT_PROMPT, self.status, self.session_dir)
            r["t_ms"] = t
            r["start_ms"] = t_start
            r["in_window"] = in_win
            dent = None
            if r["report"]:
                m = re.search(r"^\s*1[.)].*?\b(yes|no)\b", r["report"], re.I | re.M)
                dent = (m.group(1).lower() == "yes") if m else None
            r["dent_yes"] = dent
            r["end_ms"] = wall_ms()
            self.reports.append(r)
            _log_jsonl(self.log, r)
            self.tl.event("watch", f"read {Path(f).name} lane={r['lane']} dent_yes={dent}",
                          frame=Path(f).name, lane=r["lane"], wall_ms=r["start_ms"])
        skipped = [Path(f).name for f, _ in cap.frames if f not in self.read]
        if skipped:
            _log_jsonl(self.log, {"skipped": skipped[:64], "reason": "deadline or session end"})

    def _new_in_window(self, frames) -> bool:
        press = self._press_window()
        if not press:
            return False
        lo, hi = press["down_ms"] - 2500, press["up_ms"] + 12000
        return any(f not in self.read and lo <= t <= hi for f, t in frames)


# ── Session: command sender bound to this run's driver ──────────────────────
from session_script import SendTimeout, Session, play  # noqa: E402


def wait_ready(resp: Path, timeout_s: float = 40.0) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        if resp.exists():
            if '"did": "ready"' in resp.read_text(encoding="utf-8", errors="replace") or \
                    '"did":"ready"' in resp.read_text(encoding="utf-8", errors="replace"):
                return True
        time.sleep(0.2)
    return False


def setup_playwright(session_dir: Path, tl: Timeline) -> None:
    import shutil
    chk = subprocess.run(["node", "-e", "require('playwright'); console.log('ok')"],
                         cwd=session_dir, capture_output=True, text=True, shell=True)
    if chk.returncode == 0:
        tl.event("prepare", "playwright present")
        return
    src = ROOT / "docs" / "evidence" / "agent_fleet" / "SHIP" / "R8_R4_PLAYBOOK" / \
        "dryrun_H5" / "node_modules"
    if src.exists():
        tl.event("prepare", "copying local playwright install", src=str(src))
        shutil.copytree(src, session_dir / "node_modules", dirs_exist_ok=True)
        chk = subprocess.run(["node", "-e", "require('playwright')"], cwd=session_dir,
                             capture_output=True, text=True, shell=True)
        if chk.returncode == 0:
            return
    tl.event("prepare", "npm i playwright (slow path)")
    subprocess.run(["npm", "i", "playwright", "--no-audit", "--no-fund"], cwd=session_dir,
                   capture_output=True, text=True, shell=True, timeout=300)


def probe_env(base: str) -> list[str]:
    """Fail fast, with reasons. The tool never starts servers: the demo front
    door is `python tools/game_shell/server.py 8206` (owned elsewhere)."""
    import shutil
    problems = []
    try:
        with urllib.request.urlopen(base, timeout=5) as r:
            if r.status != 200:
                problems.append(f"{base} answered HTTP {r.status}")
    except Exception as e:
        problems.append(f"demo {base} unreachable ({e}) -- start it with "
                        f"`python tools/game_shell/server.py 8206`")
    if not shutil.which("ffmpeg"):
        problems.append("ffmpeg not in PATH (encode_movie needs it)")
    if not shutil.which("node"):
        problems.append("node not in PATH (the playbook driver needs it)")
    return problems


# ── verdict ─────────────────────────────────────────────────────────────────
def parse_verdict_json(path: Path) -> dict | None:
    try:
        v = json.loads(path.read_text(encoding="utf-8"))
        for k in ("pay_15_20", "pay_25", "novelty", "quotes", "term"):
            if k not in v:
                return None
        return v
    except Exception:
        return None


def parse_verdict_md(path: Path) -> dict | None:
    """Fallback for a human-relayed verdict.md (the playbook template)."""
    t = path.read_text(encoding="utf-8", errors="replace")

    def yn(pat):
        m = re.search(pat, t, re.I)
        return m.group(1).lower() == "yes" if m else None

    pay = yn(r"PAY \(\$15-20\)\s*:\s*\**\s*(yes|no)")
    pay25 = yn(r"WOULD PAY \$25\s*:\s*\**\s*(yes|no)")
    m = re.search(r"NOVELTY:\s*\**\s*(\d+)\s*/\s*10", t, re.I)
    quotes = re.findall(r'^\s*-\s+"(.+?)"\s*$', t, re.M | re.S)
    if pay is None or pay25 is None or not m:
        return None
    return {"pay_15_20": pay, "pay_25": pay25, "novelty": int(m.group(1)),
            "quotes": quotes[:3], "term": "", "source": "verdict.md"}


def judge_task_md(judge: str, session_dir: Path) -> str:
    return f"""# JUDGE TASK — blind-judge dyad run `{judge}`

You are a **stranger with a wallet**. Your briefing is
`docs/evidence/agent_fleet/SHIP/R8_R4_PLAYBOOK/PLAYBOOK.md` — read it and obey
its BLIND RULES exactly; this session's artifacts are in

    {session_dir}

The pipeline has already PLAYED the session for the mechanics record
(`resp.jsonl` = every command and every screen read, `shots/` = the timed
recording, `session.log` = timestamps). Your job is the JUDGMENT, which no
pipeline can supply: read `resp.jsonl`'s `"did":"text"` screen reads and the
shots AS A BUYER would watch them, then write your verdict.

Write BOTH of these into this directory:

1. `verdict.md` — the playbook's verdict template, filled verbatim.
2. `verdict.json` — the same verdict, machine-readable, EXACTLY this shape:

```json
{{
  "judge": "{judge}",
  "date": "<YYYY-MM-DD>",
  "what_is_this": "<your words>",
  "pay_15_20": false,
  "pay_25": false,
  "novelty": 0,
  "novelty_line": "<one line: what it's like, what you've never seen before>",
  "quotes": ["<3 sharpest, verbatim from your answers>"],
  "term": "<2-4 words: the buyer NAME for what this product is -- the dyad term>",
  "lessons_completed": 0,
  "press_test_performed": true,
  "stalls": 0,
  "honesty_note": "<did you know this project before? a judge who peeked must say so>"
}}
```

The registry entry (tools/verdict_registry.json, lane "blind-judge") is opened
already with a Rule-0 prediction; your verdict is what CLOSES it. Do not read
any repository file beyond PLAYBOOK.md and this directory.
"""


# ── the pipeline ────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="blind-judge dyad run -> verdict registry")
    ap.add_argument("--name", default="", help="judge name (fresh progress namespace)")
    ap.add_argument("--base", default="http://127.0.0.1:8206")
    ap.add_argument("--lessons", type=int, default=3)
    ap.add_argument("--wait-verdict", type=int, default=0,
                    help="seconds to wait for verdict.json in the session dir")
    ap.add_argument("--verdict-file", default="", help="path to an existing verdict.json")
    ap.add_argument("--late-register", action="store_true",
                    help="finish ALIGN+REGISTER for a completed session (no new play)")
    ap.add_argument("--session-dir", default="", help="(late-register) the session to finish")
    ap.add_argument("--p-novelty", type=int, default=8)
    ap.add_argument("--p-dent-frames", type=int, default=2)
    ap.add_argument("--p-recovery-ms", type=int, default=10000)
    ap.add_argument("--p-pay25", type=lambda s: s.lower() == "true", default=True)
    ap.add_argument("--statement", default="")
    ap.add_argument("--prediction", default="")
    ap.add_argument("--falsifier", default="")
    ap.add_argument("--gate-report", action="store_true")
    a = ap.parse_args()

    sys.path.insert(0, str(HERE))
    import registry as reg

    if a.gate_report:
        g = reg.gate25()
        print(f"$25 GATE: {g['gate']}  ({g['rule']})")
        for r in g["history"]:
            print(f"  V{r['number']:<4} {r['status']:<7} {str(r['result']):<10} "
                  f"judge={r['judge']!r:<20} pay25={r['pay25']} novelty={r['novelty']} -> {r['evidence']}")
        return 0

    if not a.name:
        print("BLOCKED: --name is required for a run (the judge's identity and "
              "fresh progress namespace)")
        return 2

    if a.late_register and not a.session_dir:
        print("BLOCKED: --late-register needs --session-dir")
        return 2

    preds = {"novelty": a.p_novelty, "dent_frames": a.p_dent_frames,
             "recovery_ms": a.p_recovery_ms, "pay25": a.p_pay25}

    # ── PREPARE ──────────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    sdir = Path(a.session_dir) if a.session_dir else \
        EVIDENCE / "sessions" / f"{a.name}_{ts}"
    if not a.late_register:
        sdir.mkdir(parents=True, exist_ok=True)
        tl = Timeline(sdir / "timeline.jsonl")
        tl.event("prepare", f"session dir {sdir}")
        problems = probe_env(a.base)
        if problems:
            for p in problems:
                tl.event("prepare", f"ENV BLOCK: {p}")
                print(f"BLOCKED: {p}")
            return 2
        tl.event("prepare", "env probed ok (demo reachable, ffmpeg+node present)")
        setup_playwright(sdir, tl)
        (sdir / "judge_drive.js").write_text(
            (HERE / "judge_drive.js").read_text(encoding="utf-8"), encoding="utf-8")
        reg.backup(EVIDENCE / "verdict_registry.pre_dyad_judge.json")
        tl.event("prepare", "registry backed up (first-write guard)")

    state_path = sdir / "run_state.json"
    tl = Timeline(sdir / "timeline.jsonl")
    if a.late_register:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        vnum = state["verdict_number"]
        preds = state["predictions"]
        return align_and_register(sdir, state, vnum, tl, a.verdict_file, wait_s=a.wait_verdict)

    state = {"judge": a.name, "base": a.base, "predictions": preds,
             "session_dir": str(sdir), "started_ts": time.time()}
    # Rule 0 BEFORE the run: the membrane opens with all three parts.
    statement = a.statement or (
        f"blind-judge dyad [{a.name}]: a buyer-judge playing the live demo blind "
        f"(R8 playbook, recorded) witnesses an answered press -- a visible dent on "
        f"held frames and calm recovery after release -- and delivers buyer pay-intent")
    prediction = a.prediction or (
        f"novelty >= {preds['novelty']}/10 AND dent_visible_frames >= {preds['dent_frames']} "
        f"AND recovery-to-calm <= {preds['recovery_ms']} ms AND pay25 == {preds['pay25']}")
    falsifier = a.falsifier or (
        f"novelty < {preds['novelty']} OR zero press-dented held frames OR no calm "
        f"recovery within {preds['recovery_ms']} ms OR pay25 != {preds['pay25']}")
    r = reg.open_membrane(statement, prediction, falsifier,
                          probe="tools/dyad_judge/run_judge.py")
    if not r["ok"]:
        print("REFUSED by the ledger:", r["error"])
        return 2
    vnum = r["verdict"]["number"]
    state["verdict_number"] = vnum
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    tl.event("prepare", f"membrane OPEN as V{vnum} (Rule 0: all three parts)")
    print(f"[run_judge] membrane OPEN: V{vnum}")

    # ── SESSION (+ overlapping capture / encode / watch) ─────────────────
    resp = sdir / "resp.jsonl"
    proc = subprocess.Popen(["node", "judge_drive.js", a.base, "."], cwd=sdir,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
    if not wait_ready(resp):
        tl.event("session", "driver never became ready")
        print("BLOCKED: the playbook driver did not start (see session.log)")
        proc.terminate()
        return 2
    tl.event("session", "driver ready", wall_ms=wall_ms())

    S = Session(sdir / "cmd", resp, tl)
    done = threading.Event()
    cap = Capture(S, sdir / "shots", tl, done)
    S.capture = cap
    wat = Watch(sdir, S, tl, done)
    enc = Process(target=_encode_worker,
                  args=(str(sdir), round(1000.0 / CAPTURE_MS, 3), wall_ms()), daemon=True)
    cap.start(); wat.start(); enc.start()
    tl.event("pipeline", "T_capture + T_watch + P_encode running OVERLAPPED with T_session",
             wall_ms=wall_ms())

    err = None
    try:
        play(S, state["judge"], lessons=a.lessons)
        tl.event("session", "play script complete", wall_ms=wall_ms())
    except SendTimeout as e:
        err = str(e)
        tl.event("session", f"play aborted: {err}", wall_ms=wall_ms())
    finally:
        (sdir / "_EOS").write_text("session complete\n", encoding="utf-8")
        done.set()
        if err:  # the driver polls cmd/ forever -- tell it to quit
            try:
                S.seq += 1
                (sdir / "cmd" / f"a{S.seq:04d}.json").write_text('{"do":"quit"}\n',
                                                                 encoding="utf-8")
                tl.event("session", "quit sent after abort", wall_ms=wall_ms())
            except Exception:
                pass
    (sdir / "press_window.json").write_text(json.dumps(S.press, indent=2) + "\n", encoding="utf-8")
    try:
        proc.wait(timeout=20)
    except Exception:
        proc.terminate()
    tl.event("session", f"driver exited rc={proc.poll()}", wall_ms=wall_ms())

    enc.join(timeout=240)
    wat.join(timeout=WATCH_DEADLINE_S)
    tl.event("pipeline", "T_encode + T_watch joined", wall_ms=wall_ms())

    # ── VERDICT (the fresh judge agent writes verdict.json into sdir) ────
    vf = Path(a.verdict_file) if a.verdict_file else None
    if vf is None:
        (sdir / "judge_task.md").write_text(judge_task_md(state["judge"], sdir), encoding="utf-8")
        tl.event("verdict", "judge_task.md written; waiting for verdict.json", wall_ms=wall_ms())
    return align_and_register(sdir, state, vnum, tl,
                              str(vf) if vf else None, wait_s=a.wait_verdict)


def align_and_register(sdir: Path, state: dict, vnum: int, tl: Timeline,
                       verdict_file: str | None, wait_s: int) -> int:
    """ALIGN (the dyadAnalysis: NUMBER + TERM) + REGISTER + REPORT."""
    import registry as reg
    from eye import pixel_read

    preds = state["predictions"]
    vj = sdir / "verdict.json"
    deadline = time.time() + wait_s
    verdict = parse_verdict_json(vj) if vj.exists() else None
    while verdict is None and time.time() < deadline:
        if vj.exists():
            verdict = parse_verdict_json(vj)
            if verdict:
                break
        if (sdir / "verdict.md").exists():
            verdict = parse_verdict_md(sdir / "verdict.md")
            if verdict:
                tl.event("verdict", "parsed verdict.md (human-relayed template)")
                break
        time.sleep(3)
    if verdict is None and verdict_file:
        p = Path(verdict_file)
        verdict = parse_verdict_json(p) or parse_verdict_md(p)

    if verdict is None:
        tl.event("verdict", "no verdict arrived; membrane stays OPEN (Rule 0 intact)")
        print(f"[run_judge] session artifacts complete in {sdir}; membrane V{vnum} "
              f"still OPEN -- finish with --late-register once the judge writes verdict.json")
        return 0

    # the measured half (pixel read over the capture, per recorded press)
    press_data = {}
    pw = sdir / "press_window.json"
    if pw.exists():
        press_data = json.loads(pw.read_text(encoding="utf-8"))
    frames = []
    shots = sdir / "shots"
    tl_path = sdir / "timeline.jsonl"
    cap_t = {}
    if tl_path.exists():
        for ln in tl_path.read_text(encoding="utf-8").splitlines():
            try:
                o = json.loads(ln)
            except Exception:
                continue
            if o.get("phase") == "capture" and o.get("frame"):
                cap_t[o["frame"]] = o.get("wall_ms")
    if shots.exists():
        for f in sorted(shots.glob("cap_*.png")):
            t = cap_t.get(f.stem)
            if t is not None:
                frames.append((str(f), t))
    windows = []
    if press_data.get("down_ms") and press_data.get("up_ms"):
        windows.append({"label": "witnessed_S4",
                        "down_ms": press_data["down_ms"], "up_ms": press_data["up_ms"]})
    for i, o in enumerate(press_data.get("other") or []):
        windows.append({"label": f"press_{i + 1}", "down_ms": o["down_ms"], "up_ms": o["up_ms"]})
    pxs = []
    for w in windows:
        r = pixel_read(frames, w, box=(260, 180, 1100, 820)) if frames else \
            {"error": "no capture frames mapped", "dent_visible_frames": None}
        r["label"] = w["label"]
        pxs.append(r)
    # the product's claim is "A press answers", not "the Nth press answers":
    # the clause is evaluated on the BEST witnessed press, every press recorded
    best = max(pxs, key=lambda p: (p.get("dent_visible_frames") or 0)) if pxs else None
    px = best if best else {"error": "no press windows recorded", "dent_visible_frames": None}
    px["per_press"] = [{k: p.get(k) for k in ("label", "hold_frames", "dent_visible_frames",
                                              "recovery_ms", "hold_peak_score")} for p in pxs]

    reads = []
    watch_log = sdir / "watch_log.jsonl"
    if watch_log.exists():
        for ln in watch_log.read_text(encoding="utf-8").splitlines():
            try:
                reads.append(json.loads(ln))
            except Exception:
                continue
    good = [r for r in reads if r.get("report")]
    eye_dent_yes = sum(1 for r in good if r.get("dent_yes") is True)
    # alignment: eye semantic read vs pixel measured read on frames both saw
    agree = None
    if good and px.get("per_frame"):
        by_name = {p["frame"]: p["above"] for p in px["per_frame"]}
        pairs = [(r["dent_yes"], by_name.get(Path(r["frame"]).name))
                 for r in good if Path(r["frame"]).name in by_name
                 and r.get("dent_yes") is not None]
        if pairs:
            agree = round(sum(1 for d, p in pairs if d == p) / len(pairs), 3)

    metrics = {"novelty": verdict.get("novelty"),
               "pay": verdict.get("pay_15_20"), "pay25": verdict.get("pay_25"),
               "dent_visible_frames": px.get("dent_visible_frames"),
               "hold_frames": px.get("hold_frames"),
               "recovery_ms": px.get("recovery_ms"),
               "hold_peak_score": px.get("hold_peak_score"),
               "best_press": px.get("label"),
               "per_press": px.get("per_press"),
               "eye_reports": len(good), "eye_dent_yes": eye_dent_yes,
               "eye_lane": (reads[0].get("lane") if reads else None),
               "lessons_completed": verdict.get("lessons_completed"),
               "stalls": verdict.get("stalls")}

    # result: every prediction clause checked, mechanically
    novelty_ok = (metrics["novelty"] or 0) >= preds["novelty"]
    dent_ok = metrics["dent_visible_frames"] is not None and \
        metrics["dent_visible_frames"] >= preds["dent_frames"]
    rec_ok = metrics["recovery_ms"] is not None and metrics["recovery_ms"] <= preds["recovery_ms"]
    pay_ok = metrics["pay25"] == preds["pay25"]
    measured_missing = metrics["dent_visible_frames"] is None
    if measured_missing and novelty_ok and pay_ok:
        result, note = "MARGINAL", "subjective clauses held but the measured half failed (pixel read)"
    elif novelty_ok and dent_ok and rec_ok and pay_ok:
        result, note = "PASS", "all Rule-0 prediction clauses held"
    else:
        result, note = "FALSIFIED", (
            f"clauses: novelty_ok={novelty_ok} dent_ok={dent_ok} recovery_ok={rec_ok} pay_ok={pay_ok}")

    term = (verdict.get("term") or "").strip()
    dyad = {"number": {k: metrics[k] for k in
                       ("novelty", "dent_visible_frames", "hold_frames", "recovery_ms",
                        "eye_reports", "eye_dent_yes")},
            "term": term, "alignment": agree}
    eye_note = next((r.get("note") for r in reads if r.get("note")), None)
    prov = {"lane": "blind-judge", "judge": verdict.get("judge", state["judge"]),
            "judge_kind": verdict.get("source", "agent"),
            "session_dir": str(sdir),
            "recording": str(sdir / "recording.mp4"),
            "eye": (reads[0].get("lane") if reads else "no-reads"),
            "eye_reason": eye_note,
            "metrics": metrics, "quotes": verdict.get("quotes", []),
            "dyad_analysis": dyad, "date": verdict.get("date")}

    r = reg.close_membrane(vnum, result,
                           evidence=sdir.relative_to(ROOT).as_posix(),
                           note=f"{note}. metrics={json.dumps(metrics)}",
                           provenance=prov)
    if term:
        reg.verdict.VerdictLedger(reg.REGISTRY).link(vnum, term)
    if not r.get("ok"):
        print("REGISTER REFUSED:", r.get("error"))
        return 2

    tl.event("register", f"V{vnum} CLOSED {result}", term=term, alignment=agree, wall_ms=wall_ms())
    write_summary(sdir, state, vnum, result, verdict, metrics, dyad)
    g = reg.gate25()
    print(f"[run_judge] V{vnum} CLOSED {result} | term={term!r} | novelty={metrics['novelty']} "
          f"| dent {metrics['dent_visible_frames']}/{metrics['hold_frames']} frames "
          f"| recovery={metrics['recovery_ms']}ms | eye={metrics['eye_lane']}")
    print("[run_judge] registry: tools/verdict_registry.json (verdict.py status shows it)")
    print(f"[run_judge] $25 GATE: {g['gate']}")
    return 0


def write_summary(sdir, state, vnum, result, verdict, metrics, dyad):
    """One-page report.md in the session dir (the evidence copy links to it)."""
    ol = overlap_report(sdir)
    lines = [
        f"# blind-judge dyad run — {state['judge']} (V{vnum}, {result})",
        "",
        f"- registry: `tools/verdict_registry.json` V{vnum}, lane `blind-judge`",
        f"- recording: `{sdir / 'recording.mp4'}`",
        f"- eye lane: {metrics.get('eye_lane')} — reports: {metrics['eye_reports']}, "
        f"dent-yes: {metrics['eye_dent_yes']}",
        f"- dyadAnalysis: number={json.dumps(dyad['number'])} term={dyad['term']!r} "
        f"alignment={dyad['alignment']}",
        f"- verdict: novelty {metrics['novelty']}/10, pay={metrics['pay']}, pay25={metrics['pay25']}",
        f"- quotes: {' | '.join(verdict.get('quotes', [])[:3])}",
        f"- overlap (measured, shared wall-clock epoch): {ol}",
    ]
    (sdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def overlap_report(sdir: Path) -> str:
    """Measure the overlap from the logs -- all epochs are parent wall-clock ms."""
    sess_iv, segs, reads = None, [], []
    tl = sdir / "timeline.jsonl"
    if tl.exists():
        evs = [json.loads(l) for l in tl.read_text(encoding="utf-8").splitlines() if l.strip()]
        s = [e["wall_ms"] for e in evs if e.get("phase") == "session" and e.get("wall_ms")]
        if s:
            sess_iv = (min(s), max(s))
    enc = sdir / "encode_log.jsonl"
    if enc.exists():
        for l in enc.read_text(encoding="utf-8").splitlines():
            o = json.loads(l)
            if o.get("ev") == "segment" and o.get("ok") and o.get("start_ms"):
                segs.append((o["start_ms"], o["start_ms"] + o["ms"]))
    wat = sdir / "watch_log.jsonl"
    if wat.exists():
        for l in wat.read_text(encoding="utf-8").splitlines():
            o = json.loads(l)
            if o.get("report") and o.get("start_ms"):
                reads.append((o["start_ms"], o.get("end_ms") or
                              o["start_ms"] + round(o.get("elapsed_s", 0) * 1000)))

    def iv_overlap(a, b_ivs):
        return sum(max(0, min(a[1], y) - max(a[0], x)) for x, y in b_ivs) if a else 0

    def iv_count(a, b_ivs):
        return sum(1 for x, y in b_ivs if a and y > a[0] and x < a[1])

    parts = []
    if sess_iv:
        parts.append(f"session span {(sess_iv[1] - sess_iv[0]) / 1000:.1f}s")
    if sess_iv and segs:
        parts.append(f"encode {iv_count(sess_iv, segs)}/{len(segs)} segments INSIDE the "
                     f"session ({iv_overlap(sess_iv, segs) / 1000:.1f}s of ffmpeg work)")
    if sess_iv and reads:
        parts.append(f"watch {iv_count(sess_iv, reads)}/{len(reads)} reads INSIDE the "
                     f"session ({iv_overlap(sess_iv, reads) / 1000:.1f}s of eye time)")
    if segs and reads:
        both = sum(1 for x, y in reads
                   for sx, sy in segs if min(y, sy) - max(x, sx) > 0)
        parts.append(f"watch reads overlapping encode work: {both}")
    return "; ".join(parts) if parts else "no overlap data"


if __name__ == "__main__":
    sys.exit(main())
