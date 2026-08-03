"""slice_record.py -- the RECORDED SLICE SESSION, closed-loop (docs/THE_SLICE.md, Phase E rung 3).

WHY THIS FILE EXISTS. The first session (slice_session_20260803) was driven over HTTP with no
position feedback: the scripted drive OVERSHOT the stone, the carry never happened on tape, and
the blind read honestly reported "nothing carried" -- a recorder fault, not a world fault (F2
cause 2, measured). This is the fixed instrument: IN-PROCESS (no curl, no HTTP), CLOSED-LOOP
(every quarter-second the drive is recomputed from where the body actually IS), and it leaves a
temporal record the blind read can parse as motion -- per-beat contact sheets, one image each.

TRAPS ALREADY PAID FOR (do not re-pay):
  * the render thread idles at zero clients -- with nobody holding /stream, nothing integrates
    and nothing renders. We hold v._clients = 1 for the whole session (rung-1 trap).
  * walk_input() sets STATE, not a step: the last (fwd, strafe) persists and the render thread
    keeps integrating it. So the loop re-issues the drive every GOTO_DT and must ZERO it on
    arrival, or the body walks off forever.
  * jump is edge-latched by the viewer ("never drop a jump between frames"): one call with
    jump=True is enough; repeating it re-jumps on landing.

INSTRUMENT CONSTANTS (provenance, same discipline as touchables.py):
  GOTO_DT 0.25 s        THE HUMAN -- the servo rate: how often the loop re-reads position and
                        re-issues the drive. A recorder choice, not a physics.
  ARRIVE 0.4 m          THE HUMAN -- "there". Well inside the stone's 0.772 m ANSUR reach, so a
                        completed goto(stone) is always a legal pick-up.
  CAPTURE every 0.5 s   THE HUMAN -- ~2 Hz, the frame budget of the record. The render thread
                        runs ~8-10 fps on this scene, so 2 Hz never starves for a fresh frame.
  pitch +0.55 rad       THE HUMAN -- a HIGH third-person camera looking down. MEASURED, not tuned:
                        the ground's lattice-closing splats (0.95 m billboards) form a picket
                        fence ~0.47 m tall; a chest-height camera cannot see ANY ground object
                        past ~1 m over it (the 2026-08-03 probe: stone, pile and tuft all
                        invisible from chest height, all visible from +0.55). Taste in service
                        of the record, not physics.
  beat waypoints        THE HUMAN -- level design: the same placeholders touchables.spawn() uses.

Determinism note: the Walker carve (~13 s) happens once inside stand(); everything after is the
live loop at real time. Run:  python tools/slice_record.py
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ChimeraEngine"))

GOTO_DT = 0.25          # s -- the servo rate (see provenance above)
ARRIVE = 0.4            # m -- "there"
CAPTURE_DT = 0.5        # s -- ~2 Hz during a beat
DOWN_LOOK = -0.55       # my handed to look() once, at session start: look() SUBTRACTS dpitch, so
                        # negative my = +0.55 rad pitch = the camera rides HIGH, looking down over
                        # the ground-splat fence (measured -- see the provenance above)


# ── the servo ────────────────────────────────────────────────────────────────────────────────────

def goto(v, tx, ty, timeout_s, arrive=ARRIVE, capture=None):
    """Closed-loop drive to (tx, ty). Every GOTO_DT: read where the body IS, face the target
    (the third-person camera sits behind the facing -- a target we do not face is a target the
    record does not show), and re-issue a clipped (fwd, strafe) in the facing frame. Magnitude
    is proportional inside 1 m so the body does not lurch past the mark between servo ticks.
    Returns True on arrival; False on timeout (a verdict, not an exception -- the caller logs it).
    """
    w = v._walk
    t0 = time.time()
    last_cap = 0.0
    while time.time() - t0 < timeout_s:
        dx, dy = tx - w.x, ty - w.y
        dist = math.hypot(dx, dy)
        if dist <= arrive:
            v.walk_input()                                  # ZERO the state -- it persists
            return True
        # face the mark: yaw 0 is +Y with forward = (-sin, cos), so the yaw OF the mark is
        # atan2(-dx, dy); look() subtracts its argument, so hand it the wrapped yaw error.
        yaw_t = math.atan2(-dx, dy)
        dyaw = (w.yaw - yaw_t + math.pi) % (2.0 * math.pi) - math.pi
        # the position error in the facing frame: f = (-sin, cos), r = (cos, sin)
        c, s = math.cos(w.yaw), math.sin(w.yaw)
        fwd_err = dx * -s + dy * c
        strafe_err = dx * c + dy * s
        mag = min(1.0, dist / 1.0)                          # creep the last metre
        r = v.walk_input(fwd=max(-1.0, min(1.0, fwd_err * mag)),
                         strafe=max(-1.0, min(1.0, strafe_err * mag)),
                         mx=dyaw)
        if capture is not None and time.time() - last_cap >= CAPTURE_DT:
            capture(r.get("touch", ""))
            last_cap = time.time()
        time.sleep(GOTO_DT)
    v.walk_input()
    return False


def use(v):
    """One E press, closed-loop on the OUTCOME: the pick-up is only real when the stone says
    carried. Returns the touchables' own verdict."""
    r = v.walk_input(use=True)
    time.sleep(GOTO_DT)                                     # let the tick land
    stone = v._touch[0]
    return stone.carried, r.get("touch", "")


# ── the record ───────────────────────────────────────────────────────────────────────────────────

class Recorder:
    """Frames + a log. Frames are the JPEG bytes the viewer already publishes (the same bytes the
    operator watches); PIL only re-encodes them to disk. A beat is a named stretch of the session;
    its frames land in frames/beatNN_tTT.jpg and its last frame is the beat's HERO."""

    def __init__(self, root: Path):
        self.dir = root / f"slice_session_{datetime.now():%Y%m%d}"
        self.frames = self.dir / "frames"
        self.frames.mkdir(parents=True, exist_ok=True)
        # a re-run on the same day must not inherit stale beats from the last run (a shorter new
        # beat would keep the old run's trailing frames) -- clear only what this recorder writes
        for stale in list(self.frames.glob("beat*_t*.jpg")) + list(self.dir.glob("sheet_*.jpg")):
            stale.unlink()
        self.beat = -1
        self.beat_name = ""
        self.count = 0
        self.log = []
        self.heroes = []                                    # (beat label, path) for the master sheet
        self.beat_frames = {}                               # beat label -> [paths] for per-beat sheets

    def start_beat(self, name):
        self.beat += 1
        self.count = 0
        self.beat_name = name
        self.beat_frames[self.label] = []

    @property
    def label(self):
        return f"beat{self.beat:02d}"

    def snap(self, v, touch="", hero=False):
        jpg = v.frame()
        from PIL import Image
        img = Image.open(io.BytesIO(jpg))
        p = self.frames / f"{self.label}_t{self.count:02d}.jpg"
        img.save(p, "JPEG", quality=88)
        self.count += 1
        w = v._walk
        self.log.append({"beat": self.label, "name": self.beat_name,
                         "frame": p.name, "x": round(w.x, 2), "y": round(w.y, 2),
                         "touch": touch})
        self.beat_frames[self.label].append(p)
        if hero:
            self.heroes.append((f"{self.label} {self.beat_name}", p))
        return p

    def capture_fn(self, v):
        return lambda touch="": self.snap(v, touch)


def contact_sheet(paths, out: Path, label="", cols=4, tw=480, th=270, max_frames=12):
    """One image that reads as TIME. The blind-read instrument: a beat's temporal sequence laid
    out left-to-right, top-to-bottom, so a still reader sees the motion the frame folder holds."""
    from PIL import Image, ImageDraw
    paths = paths[:max_frames]
    if not paths:
        return
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (8, 9, 14))
    draw = ImageDraw.Draw(sheet)
    for i, p in enumerate(paths):
        tile = Image.open(p).resize((tw, th))
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.paste(tile, (x, y))
        draw.text((x + 6, y + 6), f"{label} [{i}]", fill=(255, 255, 255))
    sheet.save(out, "JPEG", quality=88)


# ── the session ──────────────────────────────────────────────────────────────────────────────────

def main() -> int:
    import live_viewer
    v = live_viewer.get_viewer()
    rec = Recorder(REPO / "ChimeraEngine" / "output")
    failures = []

    with v._lock:
        v._clients += 1                                     # wake the render thread (rung-1 trap)
    try:
        print("[slice_record] standing up (the carve is ~13 s, once)...")
        v.stand()
        v.set_view("third")
        v.walk_input(my=DOWN_LOOK)                          # the mild down-look, once
        time.sleep(2.0)                                     # let the first real frames render

        # beat 00 -- stood. The world as it opens.
        rec.start_beat("stood")
        rec.snap(v, hero=True)

        # beat 01 -- to the stone (3, 5)
        rec.start_beat("to the stone")
        if not goto(v, 3.0, 5.0, 40.0, capture=rec.capture_fn(v)):
            failures.append("beat01: never reached the stone")
        rec.snap(v, hero=True)

        # beat 02 -- E: pick up. Closed-loop on the OUTCOME, not the keystroke.
        rec.start_beat("pick up")
        carried, touch = use(v)
        tries = 0
        while not carried and tries < 3:                    # not in reach? step closer, press again
            goto(v, v._touch[0].x, v._touch[0].y, 10.0, arrive=0.25)
            carried, touch = use(v)
            tries += 1
        rec.snap(v, touch, hero=True)
        if not carried:
            failures.append("beat02: stone never carried (reach closed-loop exhausted)")

        # beat 03 -- carry it to (0, 10). The stone rides ahead-right at waist height; the
        # frames must show it near the body or the carry is not on tape (rung-3's lesson).
        rec.start_beat("carry")
        if not goto(v, 0.0, 10.0, 45.0, capture=rec.capture_fn(v)):
            failures.append("beat03: never reached the drop point")
        rec.snap(v, hero=True)

        # beat 04 -- E: put down at the feet
        rec.start_beat("drop")
        carried, touch = use(v)
        rec.snap(v, touch, hero=True)
        if carried:
            failures.append("beat04: stone still carried after the drop press")

        # beat 05 -- into the pile (4, 12): the approach shows the cone ahead
        rec.start_beat("to the pile")
        if not goto(v, 4.0, 12.0, 60.0, arrive=0.3, capture=rec.capture_fn(v)):
            failures.append("beat05: never reached the pile")
        rec.snap(v, hero=True)

        # beat 06 -- through it to (4, 16): boots scatter grains, then TURN BACK -- the footprint
        # is the pile's own record and it must face the camera to be read.
        rec.start_beat("through the pile")
        if not goto(v, 4.0, 16.0, 40.0, capture=rec.capture_fn(v)):
            failures.append("beat06: never cleared the pile")
        w = v._walk
        dyaw = (w.yaw - math.atan2(-(4.0 - w.x), 12.0 - w.y) + math.pi) % (2 * math.pi) - math.pi
        v.walk_input(mx=dyaw)                               # look back at the cone
        time.sleep(1.0)
        rec.snap(v, hero=True)

        # beat 07 -- stand IN the tuft (-3.5, 8): the disk is 0.2 m, so arrive inside it; the
        # aggregate spring flattens away from the body (theta_max 60 deg) while we hold there.
        rec.start_beat("in the tuft")
        if not goto(v, -3.5, 8.0, 60.0, arrive=0.12, capture=rec.capture_fn(v)):
            failures.append("beat07: never reached the tuft")
        time.sleep(0.6)                                     # let the bend reach its target
        rec.snap(v, hero=True)

        # beat 08 -- walk away and JUMP mid-walk: the jump is latched by the viewer, one press.
        rec.start_beat("walk + jump")
        w = v._walk
        sx, sy = w.x, w.y
        jumped = False
        t0 = time.time()
        while time.time() - t0 < 30.0:
            dx, dy = 0.0 - w.x, 2.0 - w.y
            if math.hypot(dx, dy) <= ARRIVE:
                break
            yaw_t = math.atan2(-dx, dy)
            dyaw = (w.yaw - yaw_t + math.pi) % (2.0 * math.pi) - math.pi
            c, s = math.cos(w.yaw), math.sin(w.yaw)
            r = v.walk_input(fwd=max(-1.0, min(1.0, dx * -s + dy * c)),
                             strafe=max(-1.0, min(1.0, dx * c + dy * s)),
                             mx=dyaw,
                             jump=(not jumped and math.hypot(w.x - sx, w.y - sy) > 2.0))
            if not jumped and math.hypot(w.x - sx, w.y - sy) > 2.0:
                jumped = True
            rec.snap(v, r.get("touch", ""))
            time.sleep(0.3 if not jumped else 0.2)          # denser frames around the jump
        v.walk_input()
        if not jumped:
            failures.append("beat08: jump never fired")
        rec.snap(v, hero=True)

        # beat 09 -- look back over the walked ground: the closing wide.
        rec.start_beat("look back")
        w = v._walk
        dyaw = (w.yaw - math.atan2(-(3.0 - w.x), 5.0 - w.y) + math.pi) % (2 * math.pi) - math.pi
        v.walk_input(mx=dyaw, my=0.0)
        time.sleep(1.0)
        rec.snap(v, hero=True)

    finally:
        v.walk_input()                                      # ZERO the drive, whatever happened
        with v._lock:
            v._clients = max(0, v._clients - 1)             # hand the 4090 back

    # the sheets: one per beat (the temporal read), one master of the heroes (the session at a glance)
    for label, paths in rec.beat_frames.items():
        contact_sheet(paths, rec.dir / f"sheet_{label}.jpg", label=label)
    contact_sheet([p for _, p in rec.heroes], rec.dir / "sheet_master.jpg",
                  label="hero", max_frames=12)
    (rec.dir / "session_log.json").write_text(json.dumps(rec.log, indent=1))

    print(f"[slice_record] {sum(len(p) for p in rec.beat_frames.values())} frames, "
          f"{len(rec.heroes)} heroes -> {rec.dir}")
    for label, paths in rec.beat_frames.items():
        print(f"  {label}: {len(paths)} frames + sheet_{label}.jpg")
    if v._err:
        print(f"[slice_record] RENDER THREAD ERROR: {v._err.splitlines()[0]}")
        return 1
    if failures:
        for f in failures:
            print(f"  [FAIL] {f}")
        return 1
    print("[slice_record] session complete, all beats landed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
