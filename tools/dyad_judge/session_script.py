"""session_script.py -- the blind-compliant PLAY, as a command sequence.

The judge is a STRANGER: everything below goes through the playbook driver's
rendered-page commands only (click / type / key / text / shot). Coordinates are
the ones two prior playbook sessions proved on this page (judge1_session,
dryrun_H5): name input ~(720,484), PLAY ~(720,546), creature torso ~(545,430).
The lesson "press" uses SPACE (the page binds press to SPACE keydown and ends
it on keyup), so the hold is keydown -> wait -> keyup -- the D1 driver
extension. The verdict text is read back with {"do":"text"} exactly as a buyer
reads the screen; nothing is parsed from page internals.

S1 cold landing -> S2 enter -> S3 three lessons -> S4 press/hold/release/
recover -> S5 free play -> S6 quit. Stalls are whatever the text/shot record
shows; the judge (verdict writer) reads them from the artifacts, not from us.
"""
from __future__ import annotations

import time


class SendTimeout(RuntimeError):
    pass


class Session:
    """One command file per step, response-matched, wall-clock annotated."""

    def __init__(self, cmd_dir, resp_path, timeline, cmd_seq=0):
        self.cmd_dir = cmd_dir
        self.resp = resp_path
        self.tl = timeline
        self.seq = cmd_seq
        self.press = {}          # {down_ms, up_ms} -- published to watch/pixel
        self.last_text = ""

    def send(self, cmd: dict, timeout_s: float = 45.0) -> dict:
        import json as _json
        from pathlib import Path
        self.seq += 1
        f = Path(self.cmd_dir) / f"a{self.seq:04d}.json"
        t_send = time.time()
        f.write_text(_json.dumps(cmd) + "\n", encoding="utf-8")
        want = cmd.get("do")
        deadline = t_send + timeout_s
        # BYTE offsets against BYTES: resp.jsonl carries non-ASCII (em-dashes in
        # page text), so a byte size sliced from a decoded string skips the
        # wrong span and the reader goes blind (the 223515 run's defect).
        pos = Path(self.resp).stat().st_size if Path(self.resp).exists() else 0
        while time.time() < deadline:
            p = Path(self.resp)
            if p.exists() and p.stat().st_size > pos:
                chunk = p.read_bytes()[pos:]
                pos = p.stat().st_size
                for ln in chunk.decode("utf-8", errors="replace").splitlines():
                    try:
                        o = _json.loads(ln)
                    except Exception:
                        continue
                    if o.get("did") != want:
                        continue                      # a capture shot's line, etc.
                    if want == "shot" and cmd.get("name") not in (o.get("file") or ""):
                        continue
                    self.tl.event("session", f"{want} -> ok={o.get('ok')}",
                                  cmd=want, resp_ms=round((time.time() - t_send) * 1000))
                    return o
            time.sleep(0.15)
        self.tl.event("session", f"{want} TIMEOUT", cmd=want)
        raise SendTimeout(f"no response for {cmd} within {timeout_s}s")

    # -- convenience ---------------------------------------------------------
    def shot(self, name):
        return self.send({"do": "shot", "name": name})

    def wait(self, ms):
        return self.send({"do": "wait", "ms": ms})

    def text(self, maxch=4000):
        o = self.send({"do": "text", "max": maxch})
        self.last_text = o.get("text") or ""
        return self.last_text

    def press_hold(self, hold_ms, witness: bool = False):
        """SPACE down -> HOLD -> up. The page ends the press on keyup.
        witness=True marks THE press test (S4): only a witnessed press owns
        press['down_ms'/'up_ms'], the window the dyad measures -- lesson and
        free-play presses are recorded separately so they cannot clobber it."""
        down = round(time.time() * 1000)
        self.send({"do": "keydown", "key": " "})
        self.wait(hold_ms)
        self.send({"do": "keyup", "key": " "})
        up = round(time.time() * 1000)
        if witness:
            self.press["down_ms"], self.press["up_ms"] = down, up
        else:
            self.press.setdefault("other", []).append({"down_ms": down, "up_ms": up})


def _try(S, cmd: dict, timeout_s: float = 45.0) -> bool:
    """Best-effort command: a failure is the PAGE's truth (recorded in
    resp.jsonl for the judge), never a crash."""
    try:
        o = S.send(cmd, timeout_s=timeout_s)
        return bool(o.get("ok"))
    except SendTimeout:
        return False


def play(S: Session, judge_name: str, lessons: int = 3):
    """The playbook session flow. Yields (step, note) so the orchestrator can
    log progress; every screen read lands in resp.jsonl for the judge."""
    # S1 -- cold landing
    S.shot("01_landing")
    S.wait(5000)
    S.shot("02_landing_settled")
    S.text()
    # S2 -- self-taught entry (name -> PLAY -> greeting overlay)
    # the progress namespace is fresh per RUN: judge name + run time, so no
    # earlier player's progress is ever resumed or overwritten
    progress_name = f"{judge_name}-{time.strftime('%H%M%S')}"
    S.send({"do": "click", "x": 720, "y": 484})
    S.send({"do": "type", "text": progress_name})
    S.send({"do": "click", "x": 720, "y": 546})
    S.wait(2500)
    S.text()
    if not _try(S, {"do": "clickText", "text": "Begin", "timeout": 3000}):
        pass                                    # no card up; the page decides
    S.wait(1200)
    S.text()
    # S3 -- lessons (at least `lessons`, each to the page's own pass/fail text)
    for i in range(1, lessons + 1):
        S.shot(f"10_lesson{i}_start")
        S.text()
        if i > 1:                               # advance the pager (› button)
            if not _try(S, {"do": "clickText", "text": "›", "exact": True, "timeout": 3000}):
                S.send({"do": "click", "x": 1390, "y": 109})   # proven fallback click
            S.wait(1000)
            _try(S, {"do": "clickText", "text": "Begin", "timeout": 3000})
        S.wait(800)
            # the lesson's press: SPACE hold (default hand force; a stall here is
        # the PAGE's truth, recorded in the text/shots for the judge)
        S.press_hold(4000)
        S.shot(f"11_lesson{i}_held")
        _try(S, {"do": "clickText", "text": "let go", "timeout": 2500})
        S.wait(3000)
        _try(S, {"do": "clickText", "text": "stand at rest", "timeout": 2500})
        S.wait(4000)
        S.shot(f"12_lesson{i}_result")
        S.text()
    # S4 -- the press test, witnessed: hold, release, keep watching
    S.shot("20_press_before")
    S.press_hold(5000, witness=True)
    S.shot("21_press_held")
    S.wait(2000)
    S.shot("22_released")
    _try(S, {"do": "clickText", "text": "let go", "timeout": 2500})
    S.wait(4000)
    S.shot("23_recover_mid")
    S.wait(4000)
    S.shot("24_recover_settled")
    S.text()
    # S5 -- free play: zoom, orbit, one more press
    S.send({"do": "wheel", "dx": 0, "dy": -240})
    S.wait(800)
    S.send({"do": "move", "x": 400, "y": 500, "steps": 6})
    S.send({"do": "down"})
    S.send({"do": "move", "x": 620, "y": 380, "steps": 10})
    S.send({"do": "up"})
    S.wait(800)
    S.shot("30_freeplay_orbit")
    S.press_hold(2500)
    S.shot("31_freeplay_press")
    S.wait(3000)
    S.shot("32_freeplay_after")
    S.text()
    # S6 -- quit (the driver exits immediately: a missing response is fine)
    _try(S, {"do": "quit"}, timeout_s=8)
