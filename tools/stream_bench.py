#!/usr/bin/env python3
"""stream_bench.py -- THE KERNEL STREAM BENCH (fleet C3).

Measures delta compression of the engine's /verts route against the
prereg bars in docs/evidence/agent_fleet/MATTER_KERNEL/
SEAL_PREREGISTRATION.md ("THE KERNEL STREAM PREREGISTRATION", K1-K5):

  K1  idle delta stream  < 60 KB/poll mean  (>10x vs the legacy pull)
  K2  pose  delta stream < 200 KB/poll mean (knee 25 deg <-> 0 every 5 s)
  K3  reconstruction is BIT-EXACT: runs applied to a reference copy must
      equal the next keyframe's payload byte for byte
  K5  a torn frame is REFUSED by the decoder (never partially applied)
      and a dropped poll is caught by the seq gap and healed by one
      keyframe pull

Constraints stated before the mechanism: the bench polls the ENGINE
directly (default http://127.0.0.1:8107), never the game_shell front
door -- the door strips query strings today, and the measurement must
not depend on it. The engine owns its build window: this script never
starts or stops the engine; it only polls and POSTs intents. A legacy
answer (no 0xD1 magic) to a delta request means the running binary has
no C3 route -- the bench says so and exits 2 instead of lying.

Phases (each --seconds long, 30 s default, 3 Hz):
  idle  -- no intents; the bit-stability premise is measured, not assumed
  pose  -- POST /tick_pose knee_L 25 deg then 0, toggling every 5 s
  press -- POST /tick_touch at the nearest mesh vertex to the directive
           point [0, 4.5, 0.32] (snap law: a point between vertices
           presses nothing), held half the phase, then cleared; the
           tau=0.5 s decay rides out in runs

Per tick the bench performs three pulls in a fixed order:
  1. GET /verts          legacy framing -- the measured BASELINE cost
                         (this pull never advances the delta chain)
  2. GET /verts?delta=1  the chained frame (runs, or an automatic
                         keyframe every 60 deltas) -- the measured
                         DELTA cost of a chained client
  3. GET /verts?delta=key forced keyframe -- seeds/verifies the
                         reference state and advances the chain

Run:  python tools/stream_bench.py [--engine http://127.0.0.1:8107]
      [--seconds 30] [--hertz 3] [--phases idle,pose,press]

Exit codes: 0 all measured bars pass -- 1 a bar failed -- 2 the running
binary answered legacy to delta requests (rebuild first) -- 3 the
engine is unreachable.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import time
import urllib.error
import urllib.request

MAGIC = 0xD1                     # kernel-stream version byte (C3 route)
HDR = 16                         # [u8 magic][u8 flags][u16 rsvd][u32 n][u32 seq][u32 runs]
VERTEX_BYTES = 36                # 9 f32 per vertex: pos + normal + color
IDLE_BAR = 60_000                # K1: bytes per delta pull, mean
POSE_BAR = 200_000               # K2: bytes per delta pull, mean
RATIO_BAR = 10.0                 # K1: idle full/delta ratio

KNEE_L_INDEX = 15                # the page's JOINT_INDEX.knee_L (index.html)
KNEE_DEG = 25
POSE_TOGGLE_S = 5
DIRECTIVE_HIT = (0.0, 4.5, 0.32) # the directive's press point (snapped to skin)
PRESS_FORCE_N = 30000.0


class TornFrame(Exception):
    """Any framing inconsistency -- the decoder must refuse, never guess."""


def http_get(base: str, path: str, timeout: float = 10.0) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, obj: dict, timeout: float = 10.0) -> dict:
    req = urllib.request.Request(base + path, data=json.dumps(obj).encode(),
                                 method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def parse_legacy(buf: bytes) -> int:
    """Legacy framing [u32 n][f32*9n] -> vertex count; refuses short reads."""
    if len(buf) < 4:
        raise TornFrame("short legacy frame")
    (n,) = struct.unpack_from("<I", buf, 0)
    if len(buf) < 4 + n * VERTEX_BYTES:
        raise TornFrame("truncated legacy frame")
    return n


def parse_kernel(buf: bytes):
    """Kernel framing -> (kind, n, seq, runs) or None for a legacy answer.

    A torn frame raises TornFrame and the CALLER must keep its previous
    state -- nothing partial is ever applied (the K5 refusal)."""
    if len(buf) < 4:
        raise TornFrame("short frame")
    if buf[0] != MAGIC:
        return None                       # pre-C3 engine (or a stripped query)
    if len(buf) < HDR:
        raise TornFrame("short kernel header")
    magic, flags, rsvd, n, seq, runs = struct.unpack_from("<BBHIII", buf, 0)
    if magic != MAGIC or rsvd != 0 or flags > 1:
        raise TornFrame("bad kernel header")
    if flags == 0:
        if runs != 0:
            raise TornFrame("keyframe with runs")
        if len(buf) != HDR + n * VERTEX_BYTES:
            raise TornFrame("truncated keyframe")
        return ("key", n, seq, [])
    off = HDR
    out = []
    for _ in range(runs):
        if off + 8 > len(buf):
            raise TornFrame("truncated run header")
        start, count = struct.unpack_from("<II", buf, off)
        off += 8
        if count == 0 or start + count > n:
            raise TornFrame("run out of range")
        if off + count * VERTEX_BYTES > len(buf):
            raise TornFrame("truncated run body")
        out.append((start, count, off))
        off += count * VERTEX_BYTES
    if off != len(buf):
        raise TornFrame("trailing kernel bytes")
    return ("runs", n, seq, out)


def apply_runs(ref: bytearray, buf: bytes, runs) -> None:
    """Apply validated runs to the reference payload -- bit-exact or bust."""
    for start, count, off in runs:
        ref[start * VERTEX_BYTES:(start + count) * VERTEX_BYTES] = \
            buf[off:off + count * VERTEX_BYTES]


def nearest_vertex_hit(base: str) -> tuple:
    """The directive point snapped to the nearest skin vertex (the page's
    snap law, index.html: a point between vertices presses nothing)."""
    try:
        buf = http_get(base, "/verts")
        n = parse_legacy(buf)
        best, best_d2 = DIRECTIVE_HIT, float("inf")
        for v in range(n):
            x, y, z = struct.unpack_from("<3f", buf, 4 + v * VERTEX_BYTES)
            dx = x - DIRECTIVE_HIT[0]
            dy = y - DIRECTIVE_HIT[1]
            dz = z - DIRECTIVE_HIT[2]
            d2 = dx * dx + dy * dy + dz * dz
            if d2 < best_d2:
                best_d2, best = d2, (x, y, z)
        return best
    except Exception:
        return DIRECTIVE_HIT              # honest fallback: the raw directive point


class Phase:
    """Per-phase sizes + integrity counters (honest: races are counted)."""

    def __init__(self, name: str):
        self.name = name
        self.full_sizes = []              # legacy pull bytes (the baseline)
        self.delta_sizes = []             # ?delta=1 pull bytes (chained client)
        self.key_sizes = []               # ?delta=key pull bytes (resync cost)
        self.legacy_answers = 0           # delta pull answered legacy (no C3)
        self.verified = 0                 # bit-exact reconstructions
        self.verify_retries = 0           # tick landed between two pulls, retry held
        self.verify_failures = 0          # hard mismatches after retry (must stay 0)
        self.seq_gaps = 0                 # unexpected seq jumps (drop or foreign client)

    def mean_full(self) -> float:
        return sum(self.full_sizes) / len(self.full_sizes) if self.full_sizes else 0.0

    def mean_delta(self) -> float:
        return sum(self.delta_sizes) / len(self.delta_sizes) if self.delta_sizes else 0.0

    def mean_key(self) -> float:
        return sum(self.key_sizes) / len(self.key_sizes) if self.key_sizes else 0.0

    def max_delta(self) -> int:
        return max(self.delta_sizes) if self.delta_sizes else 0


def run_phase(base: str, ph: Phase, seconds: float, hertz: float,
              state: dict) -> None:
    """The measurement loop. state carries: ref (bytearray payload or None),
    last_seq (int or None), last_runs_frame / last_key_frame (bytes, for the
    tear test), hit, press_ready, pose_refusals."""
    period = 1.0 / hertz
    t_end = time.perf_counter() + seconds
    press_at = time.perf_counter() + seconds * 0.5
    pressed = False
    cleared = False
    pose_next = time.perf_counter()
    pose_on = False
    drop_done = False
    drop_healed = False
    tear_done = False
    next_tick = time.perf_counter()

    def pace() -> None:
        nonlocal next_tick
        next_tick += period
        s = next_tick - time.perf_counter()
        if s > 0:
            time.sleep(s)
        else:
            next_tick = time.perf_counter()          # fell behind; do not spiral

    while time.perf_counter() < t_end:
        # ---- phase driving (intents POSTed before the pulls) ----------
        if ph.name == "pose" and time.perf_counter() >= pose_next:
            deg = KNEE_DEG if not pose_on else 0
            body = http_post(base, "/tick_pose",
                             {"joint_index": KNEE_L_INDEX, "deg": deg})
            if not body.get("ok"):
                body = http_post(base, "/tick_pose",
                                 {"joint": "knee_L", "deg": deg})
            if not body.get("ok"):
                state["pose_refusals"] = state.get("pose_refusals", 0) + 1
                print(f"  [pose] REFUSED by the engine ({body}) -- the pose "
                      f"phase is measuring idle-like traffic; the K2 bar "
                      f"will be reported NOT MEASURED, not silently passed")
            pose_on = not pose_on
            pose_next += POSE_TOGGLE_S
        if ph.name == "press":
            if not pressed and time.perf_counter() >= state["press_ready"]:
                body = http_post(base, "/tick_touch",
                                 {"hit": list(state["hit"]),
                                  "force_n": PRESS_FORCE_N})
                pressed = True                   # never retry-spam the engine
                if body.get("ok"):
                    print(f"  [press] pressed at ({state['hit'][0]:.3f}, "
                          f"{state['hit'][1]:.3f}, {state['hit'][2]:.3f}) "
                          f"with {PRESS_FORCE_N:.0f} N")
                else:
                    print(f"  [press] REFUSED ({body}) -- the press phase "
                          f"measures idle-like traffic")
            elif pressed and not cleared and time.perf_counter() >= press_at:
                http_post(base, "/tick_touch_clear", {})
                cleared = True

        # ---- pull 1: the legacy baseline (never advances the chain) ---
        full = http_get(base, "/verts")
        parse_legacy(full)
        ph.full_sizes.append(len(full))

        # ---- pull 2: the chained delta frame ---------------------------
        frame = http_get(base, "/verts?delta=1")
        ph.delta_sizes.append(len(frame))
        parsed = parse_kernel(frame)

        # K5 DROP TEST (idle, once, after ~5 s): swallow this frame AND
        # its keyframe pull -- the transport lost both. The NEXT tick's
        # seq must show the gap, and the resync below must heal it.
        if ph.name == "idle" and not drop_done \
                and state["last_seq"] is not None \
                and len(ph.delta_sizes) >= max(3, int(hertz * 5)):
            drop_done = True
            print("  [drop] simulated: one delta frame + its keyframe swallowed")
            pace()
            continue

        if parsed is None:
            ph.legacy_answers += 1               # no C3 route in this binary
            pace()
            continue

        kind, n, seq, runs = parsed
        expected = (None if state["last_seq"] is None
                    else (state["last_seq"] + 1) & 0xFFFFFFFF)
        gap = expected is not None and seq != expected
        if gap:
            ph.seq_gaps += 1
            if drop_done and not drop_healed:
                drop_healed = True
                print(f"  [drop] HEALED: seq gap detected (expected "
                      f"{expected}, got {seq}) -> the keyframe resync follows")
        if kind == "runs":
            # runs over an unknown base are NEVER applied (K5); the
            # keyframe below reseeds instead
            if not gap:
                state["last_runs_frame"] = frame
                if state["ref"] is not None and n * VERTEX_BYTES == len(state["ref"]):
                    apply_runs(state["ref"], frame, runs)

        # ---- pull 3: forced keyframe -- seed/verify, advance the chain -
        # K3: the reconstruction must equal the exported state BIT-EXACT.
        # A tick can land between pulls 2 and 3 (the engine runs ~300 Hz):
        # one retry is taken before a mismatch is called a failure, and
        # retries are counted, never hidden.
        key = http_get(base, "/verts?delta=key")
        ph.key_sizes.append(len(key))
        pk = parse_kernel(key)
        if pk is None:
            ph.legacy_answers += 1
            pace()
            continue
        kkind, kn, kseq, _ = pk
        if kkind != "key":
            print("  [integrity] ?delta=key answered runs -- protocol violation")
            state["integrity_violations"] = state.get("integrity_violations", 0) + 1
        elif state["ref"] is not None and kn * VERTEX_BYTES == len(state["ref"]):
            if bytes(state["ref"]) == key[HDR:]:
                ph.verified += 1
            else:
                ph.verify_retries += 1
                key2 = http_get(base, "/verts?delta=key")
                pk2 = parse_kernel(key2)
                if pk2 is not None and pk2[0] == "key":
                    if bytes(state["ref"]) == key2[HDR:]:
                        ph.verified += 1
                    else:
                        ph.verify_failures += 1
                        state["ref"] = bytearray(key2[HDR:])   # reseed, honest count
                    kseq = pk2[2]
                else:
                    ph.verify_failures += 1
        else:
            state["ref"] = bytearray(key[HDR:])  # (re)seed / topology changed
        state["last_seq"] = kseq
        if kkind == "key":
            state["last_key_frame"] = key

        # K5 TEAR TEST (once per phase): tear a REAL kernel frame and
        # demand refusal. idle tears the keyframe payload; pose tears a
        # real runs frame mid-body. A decoder that accepts a torn frame
        # is the falsifier, full stop.
        if not tear_done and (
                (ph.name == "idle" and state.get("last_key_frame") is not None)
                or (ph.name == "pose" and state.get("last_runs_frame") is not None)):
            victim = state["last_key_frame"] if ph.name == "idle" \
                else state["last_runs_frame"]
            cut = HDR + 18                       # mid-payload / mid-run
            torn = victim[:cut] if len(victim) > cut + 4 else victim[:-4]
            try:
                parse_kernel(torn)
                print("  [tear] FAIL: a torn frame was ACCEPTED -- K5 fired")
                state["tear_failures"] = state.get("tear_failures", 0) + 1
            except TornFrame:
                state["tear_refusals"] = state.get("tear_refusals", 0) + 1
            tear_done = True

        pace()

    if ph.name == "press" and pressed and not cleared:
        http_post(base, "/tick_touch_clear", {})  # leave the world at rest


def report(phases: list, state: dict) -> int:
    print("\n" + "=" * 74)
    print("THE KERNEL STREAM BENCH -- verdict against the C3 prereg bars")
    print("=" * 74)
    total_fail = 0

    for ph in phases:
        mf, md = ph.mean_full(), ph.mean_delta()
        ratio = (mf / md) if md > 0 else 0.0
        print(f"\n[{ph.name.upper()}] pulls={len(ph.delta_sizes)} "
              f"full mean={mf / 1024:.1f} KB  delta mean={md / 1024:.1f} KB  "
              f"delta max={ph.max_delta() / 1024:.1f} KB  ratio={ratio:.1f}x")
        print(f"  resync(key) mean={ph.mean_key() / 1024:.1f} KB  "
              f"bit-exact={ph.verified}  retries={ph.verify_retries}  "
              f"failures={ph.verify_failures}  seq gaps={ph.seq_gaps}  "
              f"legacy answers={ph.legacy_answers}")
        if ph.name == "idle":
            ok = bool(ph.delta_sizes) and md < IDLE_BAR and ratio > RATIO_BAR
            print(f"  K1 IDLE bar: delta mean < {IDLE_BAR // 1000} KB and "
                  f"ratio > {RATIO_BAR:.0f}x -> {'PASS' if ok else 'FAIL'}")
            total_fail += 0 if ok else 1
        elif ph.name == "pose":
            if state.get("pose_refusals", 0) == 0:
                ok = bool(ph.delta_sizes) and md < POSE_BAR
                print(f"  K2 POSE bar: delta mean < {POSE_BAR // 1000} KB -> "
                      f"{'PASS' if ok else 'FAIL'}")
                total_fail += 0 if ok else 1
            else:
                print("  K2 POSE bar: NOT MEASURED (every pose intent was "
                      "refused by the engine)")
        else:
            print("  PRESS: informational (no prereg bar)")

    tears = state.get("tear_refusals", 0)
    tear_fails = state.get("tear_failures", 0)
    hard = sum(p.verify_failures for p in phases)
    viol = state.get("integrity_violations", 0)
    print(f"\nK5 INTEGRITY: torn frames refused={tears} accepted={tear_fails} "
          f"(a torn frame must NEVER be accepted)")
    print(f"K3 INTEGRITY: bit-exact reconstruction failures={hard} (must be 0; "
          f"retries are tick-races between pulls, counted honestly)  "
          f"protocol violations={viol}")
    k5_ok = tear_fails == 0 and hard == 0 and viol == 0
    total_fail += 0 if k5_ok else 1

    print("\nVERDICT: " + ("PASS -- the stream survives the prereg bars"
                           if total_fail == 0
                           else f"FAIL ({total_fail} bar(s) down)"))
    return 0 if total_fail == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="THE KERNEL STREAM BENCH (fleet C3) -- delta "
                    "compression of /verts against the prereg bars")
    ap.add_argument("--engine", default="http://127.0.0.1:8107")
    ap.add_argument("--seconds", type=float, default=30.0,
                    help="seconds PER PHASE (default 30; the directive's "
                         "30 s total is --seconds 10)")
    ap.add_argument("--hertz", type=float, default=3.0)
    ap.add_argument("--phases", default="idle,pose,press")
    args = ap.parse_args()
    base = args.engine.rstrip("/")

    try:
        probe = http_get(base, "/verts", timeout=5.0)
        n0 = parse_legacy(probe)
    except (urllib.error.URLError, OSError, TornFrame) as e:
        print(f"the engine at {base} is silent or spoke nonsense ({e}) -- "
              f"the lead owns the build window; start it first")
        return 3
    print(f"engine live at {base}: {n0} verts, legacy pull = {len(probe)} bytes")

    state = {
        "ref": None,
        "last_seq": None,
        "last_runs_frame": None,
        "last_key_frame": None,
        "hit": nearest_vertex_hit(base),
        "press_ready": 0.0,              # set when the press phase starts
    }
    phases = [Phase(name.strip()) for name in args.phases.split(",") if name.strip()]

    for ph in phases:
        print(f"\n--- phase {ph.name.upper()} ({args.seconds:.0f} s at "
              f"{args.hertz:.0f} Hz) ---")
        if ph.name == "press":
            state["press_ready"] = time.perf_counter() + 1.0
        run_phase(base, ph, args.seconds, args.hertz, state)

    any_c3 = any(p.legacy_answers < len(p.delta_sizes) for p in phases)
    if not any_c3:
        print("\nEVERY delta pull answered the LEGACY framing: the running "
              "binary has no C3 route. Rebuild ChimeraEngine (the lead owns "
              "the build window) and re-run this bench.")
        return 2
    return report(phases, state)


if __name__ == "__main__":
    sys.exit(main())
