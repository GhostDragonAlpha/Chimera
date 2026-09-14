"""walk_test.py -- THE STANCE: the F1 bar script for the balance rung
(prereg appended to docs/evidence/agent_fleet/MATTER_KERNEL/
SEAL_PREREGISTRATION.md, "THE STANCE PREREGISTRATION").
Supersedes the lead-staged stub: that one parsed /verts at a 12-byte
stride (the record is 36), aimed the touch at a point the engine's
on-skin truthfulness check refuses, and its verdict passed with no
controller at all. This one measures and bars, per the prereg.

HTTP only, no engine build/run from here:
  GET  /tick_state    baseline + per-phase: gravity_on, stance_on,
                      stance_ankle_deg, stance_kp, conserve_pct, P cells
  POST /tick_gravity  {"on": true}   -- ensured on (the fall law is
                      gravity's; stance runs only in a gravity field)
  POST /tick_stance   {"on": true|false}  -- THE LEAD WIRES THIS ROUTE
                      at the build window (MembraneTick::set_stance).
                      Until then run with --skip-stance: instrument
                      mode (S2/B3 only), no verdict.
  POST /tick_touch    {"hit":[x,y,z],"force_n":F}  (S1: 20 kN at the
                      +z-most hip vert, held, then cleared)
  POST /tick_touch_clear
  POST /tick_pose     {"joint_index":i,"deg":d}  (the disturbance
                      channel: symmetric wrists 11/12, elbows 9/10 --
                      the measured arm-swing mass shift)
  GET  /verts         [u32 n][f32 x9 per vert] -- the auditor: lean is
                      measured here INDEPENDENTLY of the engine, from
                      the raw streamed surface.

THE MEASURE (prereg): lean = whole-body posed centroid (xz) minus the
FROZEN support centroid. The support set is the min-y band (y <= lowest
+ 5 cm) frozen at baseline -- the engine freezes the same membership at
set_stance(true); a re-selected band chases the ankle pitch and
self-cancels the channel (measured |S| 0.056 vs 0.283 m/rad).

Bars (from the prereg):
  B1  S1 touch nulling: held 20 kN sagittal hip touch, residual
      <= max(25% of excursion, 0.02 mm) at 2 s, ankles within 5 deg.
  B2  S1b pose-lean nulling: the ~2 cm wrist-step lean nulled
      <= 0.5 cm at 2 s, no ankle saturation; unwinds after release.
  B3  S2 the FALL direction (stance OFF): the ramped arm-swing lean
      crosses 10 cm and holds >= 90% through the hold (un-righted).
  B4  S2b the AUTHORITY LAW (stance ON, same ramp): ankles pin at
      5.0 +- 0.2 deg, measured authority |lean_off| - |lean_on| at the
      hold in [2.3, 3.3] cm (derived 2.76 cm), no oscillation.
  B5  S3 nothing else lies: |conserve_pct| <= 0.01, pressures exactly 0
      at rest, teardown returns ankles to 0 and lean to baseline.
"""
from __future__ import annotations

import argparse
import array
import json
import struct
import sys
import time
import urllib.error
import urllib.request

# named bars -- derived in the prereg, not tuned here
STANCE_BAND_M    = 0.05    # support band: sole + 5 cm
TOUCH_FORCE_N    = 20000.0 # S1's held touch
TOUCH_NULL_FRAC  = 0.25    # residual <= 25% of excursion at 2 s (tau = 1 s)
TOUCH_NULL_ABS_M = 2e-5    # ... with a 0.02 mm determinism floor
POSE_NULL_BAR_M  = 0.005   # the 2 cm pose step nulls under 0.5 cm at 2 s
POSE_TARGET_M    = 0.02    # S1b disturbance size (m of lean)
PERSIST_FRAC     = 0.90    # S2: stance-off holds >= 90% through the hold
FALL_BAR_M       = 0.10    # S2: the 10 cm crossing
AUTH_LO_M        = 0.023   # S2b authority bar [2.3, 3.3] cm
AUTH_HI_M        = 0.033   #   (derived 2.76 cm at |S|(5 deg) = 0.316 m/rad)
ANKLE_SAT_DEG    = 5.0
ANKLE_SAT_TOL    = 0.2
CONSERVE_BAR     = 0.01    # percent
WRIST_L, WRIST_R = 11, 12  # joints28 order: the disturbance pins
ELBOW_L, ELBOW_R = 9, 10
PROBE_DEG        = 3.0     # wrist sensitivity probe
RAMP_STEP_DEG    = 5.0
RAMP_MAX_STEPS   = 12      # 60 deg cap (wrists' flex ROM bar)


def http_get(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes, timeout: int = 30) -> bytes:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_state(base: str) -> dict:
    return json.loads(http_get(base, "/tick_state"))


def get_verts(base: str):
    """(n, floats) -- 9 f32 per vertex (pos at [0:3]), from GET /verts."""
    raw = http_get(base, "/verts")
    (n,) = struct.unpack_from("<I", raw, 0)
    if len(raw) < 4 + n * 36:
        raise RuntimeError(f"/verts short: {len(raw)} bytes for {n} verts")
    flt = array.array("f")
    flt.frombytes(raw[4:4 + n * 36])
    return n, flt


def lean_of(flt, sup):
    """lean (x, z) = whole-body centroid minus frozen-support centroid."""
    n = len(flt) // 9
    cx = cz = 0.0
    for v in range(n):
        cx += flt[v * 9 + 0]
        cz += flt[v * 9 + 2]
    cx /= n
    cz /= n
    if not sup:
        return cx, cz
    sx = sz = 0.0
    for v in sup:
        sx += flt[v * 9 + 0]
        sz += flt[v * 9 + 2]
    sx /= len(sup)
    sz /= len(sup)
    return cx - sx, cz - sz


def freeze_support(flt, band_m: float):
    """The rest contact patch: min-y band indices (the engine freezes
    the same membership at set_stance(true))."""
    n = len(flt) // 9
    lo = min(flt[v * 9 + 1] for v in range(n))
    return [v for v in range(n) if flt[v * 9 + 1] <= lo + band_m]


def sample_seconds(base, sup, seconds, hz, states=None):
    """Sample (t, lean_x, lean_z) at hz; optionally collect /tick_state."""
    out = []
    t_end = time.monotonic() + seconds
    period = 1.0 / hz
    nxt = time.monotonic()
    while True:
        now = time.monotonic()
        if now >= t_end:
            break
        if nxt > now:
            time.sleep(min(nxt - now, period))
        nxt += period
        _, flt = get_verts(base)
        lx, lz = lean_of(flt, sup)
        row = [seconds - (t_end - time.monotonic()), lx, lz]
        if states is not None:
            states.append(get_state(base))
        out.append(row)
        print(f"   t={row[0]:6.3f}  lean_z={lz * 100:+8.4f} cm  "
              f"lean_x={lx * 100:+8.4f} cm")
    return out


def max_ankle(states):
    return max((abs(s.get("stance_ankle_deg", 0.0)) for s in states if s),
               default=0.0)


def main() -> int:
    ap = argparse.ArgumentParser(description="THE STANCE: balance F-bar")
    ap.add_argument("--base", default="http://127.0.0.1:8080")
    ap.add_argument("--hz", type=float, default=10.0)
    ap.add_argument("--skip-stance", action="store_true",
                    help="do not POST /tick_stance (route not wired yet); "
                         "instrument mode: S2/B3 only, no verdict")
    ap.add_argument("--skip-touch", action="store_true",
                    help="skip the S1 touch phase")
    ap.add_argument("--skip-calibrate", action="store_true",
                    help="skip the wrist-sensitivity probe")
    ap.add_argument("--touch-force", type=float, default=TOUCH_FORCE_N)
    ap.add_argument("--fall-bar", type=float, default=FALL_BAR_M)
    args = ap.parse_args()
    base = args.base.rstrip("/")
    bars = []  # (name, passed)

    try:
        st = get_state(base)
    except (urllib.error.URLError, OSError) as e:
        print(f"FAIL unreachable: the engine at {base} is not answering ({e})")
        return 2

    print("== preflight /tick_state")
    print(f"   gravity_on={st.get('gravity_on')} stance_on={st.get('stance_on')} "
          f"sealed={st.get('sealed')} conserve_pct="
          f"{st.get('conserve_pct', 0.0):.2e}")
    if not st.get("gravity_on"):
        try:
            http_post(base, "/tick_gravity", b'{"on": true}')
            st = get_state(base)
            print("   gravity was off -- POSTed /tick_gravity "
                  '{"on": true} (stance balances only in a gravity field)')
        except urllib.error.HTTPError as e:
            print(f"FAIL route: /tick_gravity -> HTTP {e.code}")
            return 2

    # the auditor's support set, frozen at rest (the engine freezes the
    # same membership at enable; the body is at rest here in both frames)
    n, flt = get_verts(base)
    sup = freeze_support(flt, STANCE_BAND_M)
    lean_rest = lean_of(flt, sup)
    print(f"== frozen support: {len(sup)}/{n} verts; rest lean "
          f"({lean_rest[0] * 100:+.4f}, {lean_rest[1] * 100:+.4f}) cm "
          f"(the tail owns the z term)")

    def pose(idx: int, deg: float):
        try:
            http_post(base, "/tick_pose",
                      json.dumps({"joint_index": idx, "deg": deg}).encode())
        except urllib.error.HTTPError as e:
            print(f"   /tick_pose {idx} {deg} -> HTTP {e.code}")

    # -- wrist sensitivity probe (stance OFF; poses are static so this
    #    settles instantly; pins 11/12 are the measured mass channel)
    sens = None  # cm of lean_z per deg
    if not args.skip_calibrate:
        print(f"== wrist sensitivity probe (pins {WRIST_L}/{WRIST_R} "
              f"+{PROBE_DEG} deg, stance off)")
        pose(WRIST_L, PROBE_DEG)
        pose(WRIST_R, PROBE_DEG)
        time.sleep(0.6)
        _, flt1 = get_verts(base)
        lz1 = lean_of(flt1, sup)[1]
        sens = abs(lz1 - lean_rest[1]) * 100.0 / PROBE_DEG
        pose(WRIST_L, 0.0)
        pose(WRIST_R, 0.0)
        time.sleep(0.4)
        print(f"   measured |d(lean_z)| = {sens:.4f} cm/deg "
              f"(prereg: 0.16 cm/deg symmetric wrists)")
        if sens < 1e-4:
            print("FAIL calibrate: the wrist channel did not move the "
                  "surface -- is the body classified (vertbind live)?")
            return 2

    # -- enable stance
    stance_wired = False
    if not args.skip_stance:
        try:
            http_post(base, "/tick_stance", b'{"on": true}')
        except urllib.error.HTTPError as e:
            print(f"FAIL route: POST /tick_stance -> HTTP {e.code}; the lead "
                  f"must wire it to MembraneTick::set_stance at the build "
                  f"window. Until then: python tools/walk_test.py "
                  f"--skip-stance")
            return 2
        st = get_state(base)
        stance_wired = bool(st.get("stance_on"))
        kp = st.get("stance_kp", 0.0)
        if kp:
            print(f"== stance ON (state stance_on={stance_wired}, kp={kp:.4f} "
                  f"rad/(m s) = 1/(|S|*1s) -> |S| ~= {1.0 / kp:.4f} m/rad; "
                  f"prereg: 0.283)")
        else:
            print(f"== stance ON (state stance_on={stance_wired})")
        print("   sampling 1 s rest baseline under the servo")
        base_s = sample_seconds(base, sup, 1.0, args.hz)
        base_lz = base_s[-1][2]
    else:
        base_lz = lean_rest[1]
        print("== --skip-stance: instrument mode (S2/B3 only, no verdict)")

    # -- S1: the held 20 kN sagittal hip touch
    if not args.skip_touch:
        print("== S1: held touch at the +z-most hip vert")
        n2, flt2 = get_verts(base)
        hit_i, hit_z = -1, -1e30
        for v in range(n2):
            y, z = flt2[v * 9 + 1], flt2[v * 9 + 2]
            if 2.0 <= y <= 4.5 and z > hit_z:
                hit_i, hit_z = v, z
        hit = [flt2[hit_i * 9 + 0], flt2[hit_i * 9 + 1],
               flt2[hit_i * 9 + 2]]
        print(f"   hit vert {hit_i} at ({hit[0]:+.4f}, {hit[1]:+.4f}, "
              f"{hit[2]:+.4f}) (prereg measured vert 16140 at "
              f"(-2.68, 3.32, 0.83))")
        try:
            http_post(base, "/tick_touch",
                      json.dumps({"hit": hit,
                                  "force_n": args.touch_force}).encode())
        except urllib.error.HTTPError as e:
            print(f"FAIL route: /tick_touch -> HTTP {e.code}")
            return 2
        st_s = []
        s1 = sample_seconds(base, sup, 3.0, args.hz, states=st_s)
        exc = max(abs(r[2] - base_lz) for r in s1 if r[0] <= 0.5)
        resid = max(abs(r[2] - base_lz) for r in s1 if 1.8 <= r[0] <= 2.2)
        bar = max(exc * TOUCH_NULL_FRAC, TOUCH_NULL_ABS_M)
        amax = max_ankle(st_s)
        bars.append((f"B1 S1 touch nulled: excursion {exc * 1000:.3f} mm, "
                     f"residual {resid * 1000:.4f} mm <= bar "
                     f"{bar * 1000:.4f} mm at 2 s", resid <= bar))
        bars.append((f"B1a S1 ankles within {ANKLE_SAT_DEG} deg "
                     f"(max {amax:.3f})", amax <= ANKLE_SAT_DEG + 1e-6))
        http_post(base, "/tick_touch_clear")
        print("   cleared; waiting 4.5 s (dimple tau 0.5 s, the 0.1 mm "
              "cutoff at ~4.2 s)")
        time.sleep(4.5)
        _, flt3 = get_verts(base)
        lzr = lean_of(flt3, sup)[1]
        ok1b = abs(lzr - base_lz) <= bar
        bars.append((f"B1b S1 post-clear recovery: |dlean| "
                     f"{abs(lzr - base_lz) * 1000:.4f} mm <= bar "
                     f"{bar * 1000:.4f} mm", ok1b))

    # -- S1b: the ~2 cm pose-lean step (within authority: predicted
    #    theta_ss = D/|S| ~ 3.8 deg, no saturation)
    if stance_wired:
        print("== S1b: symmetric wrist step (the measured mass shift)")
        deg = POSE_TARGET_M * 100.0 / sens if sens else 12.5
        deg = min(max(deg, 5.0), 30.0)
        print(f"   step = +{deg:.1f} deg on pins {WRIST_L}/{WRIST_R} "
              f"(target lean ~{POSE_TARGET_M * 100:.0f} cm)")
        pose(WRIST_L, deg)
        pose(WRIST_R, deg)
        st_s = []
        s1b = sample_seconds(base, sup, 3.0, args.hz, states=st_s)
        exc = max(abs(r[2] - base_lz) for r in s1b if r[0] <= 0.5)
        resid = max(abs(r[2] - base_lz) for r in s1b if 1.8 <= r[0] <= 2.2)
        amax = max_ankle(st_s)
        bars.append((f"B2 S1b pose lean nulled: excursion {exc * 100:.3f} cm, "
                     f"residual {resid * 100:.3f} cm <= "
                     f"{POSE_NULL_BAR_M * 100:.1f} cm at 2 s",
                     exc >= 0.005 and resid <= POSE_NULL_BAR_M))
        bars.append((f"B2a S1b no ankle saturation (max {amax:.3f} deg "
                     f"<= {ANKLE_SAT_DEG})", amax <= ANKLE_SAT_DEG + 1e-6))
        pose(WRIST_L, 0.0)
        pose(WRIST_R, 0.0)
        print("   released; sampling 2 s unwind")
        s1c = sample_seconds(base, sup, 2.0, args.hz)
        resid2 = max(abs(r[2] - base_lz) for r in s1c if r[0] >= 1.8)
        bars.append((f"B2b S1b unwind after release: residual "
                     f"{resid2 * 100:.3f} cm <= "
                     f"{exc * TOUCH_NULL_FRAC * 100:.2f} cm",
                     resid2 <= exc * TOUCH_NULL_FRAC))

    # -- the ramp: wrists+elbows in +5 deg steps until the fall bar
    def ramp(steps: int):
        seq = []
        for k in range(1, steps + 1):
            d = k * RAMP_STEP_DEG
            for j in (WRIST_L, WRIST_R, ELBOW_L, ELBOW_R):
                pose(j, d)
            time.sleep(0.7)
            _, fltk = get_verts(base)
            lx, lz = lean_of(fltk, sup)
            seq.append((d, lx, lz))
            print(f"   ramp {d:5.1f} deg: |lean_z| = {abs(lz) * 100:7.3f} cm")
            if abs(lz) >= args.fall_bar:
                break
        return seq

    def reset_ramp_pins():
        for j in (WRIST_L, WRIST_R, ELBOW_L, ELBOW_R):
            pose(j, 0.0)

    # -- S2: the FALL direction (stance OFF)
    print("== S2: stance OFF -- the ramped arm-swing lean (no righting)")
    try:
        http_post(base, "/tick_stance", b'{"on": false}')
    except urllib.error.HTTPError:
        pass
    time.sleep(0.5)
    seq2 = ramp(RAMP_MAX_STEPS)
    s2 = sample_seconds(base, sup, 2.0, args.hz)
    peak = max((abs(r[2]) for r in s2), default=0.0)
    keep = min((abs(r[2]) for r in s2), default=0.0)
    crossed = max((abs(r[2]) for r in seq2), default=0.0) >= args.fall_bar
    bars.append((f"B3 S2 lean crossed {args.fall_bar * 100:.0f} cm "
                 f"(max {max((abs(r[2]) for r in seq2), default=0.0) * 100:.2f} cm)",
                 crossed))
    bars.append((f"B3a S2 un-righted: the hold keeps >= "
                 f"{PERSIST_FRAC * 100:.0f}% ({keep * 100:.2f}/"
                 f"{peak * 100:.2f} cm)", peak > 0 and keep >= PERSIST_FRAC * peak))
    steps_used = len(seq2)
    reset_ramp_pins()
    time.sleep(1.0)

    # -- S2b: the AUTHORITY LAW (stance ON, the same ramp)
    if stance_wired:
        print("== S2b: stance ON -- the same ramp (the servo answers)")
        http_post(base, "/tick_stance", b'{"on": true}')
        time.sleep(1.0)
        seq2b = ramp(steps_used)
        st_s = []
        s2b = sample_seconds(base, sup, 2.0, args.hz, states=st_s)
        lean_off = seq2[-1][2] if seq2 else 0.0
        lean_on = s2b[-1][2] if s2b else 0.0
        a_meas = abs(abs(lean_off) - abs(lean_on))
        anks = [abs(s.get("stance_ankle_deg", 0.0)) for s in st_s if s]
        pin_min = min(anks[-int(args.hz):]) if anks else 0.0
        pinned = pin_min >= ANKLE_SAT_DEG - ANKLE_SAT_TOL
        signs = []
        for i in range(1, len(s2b)):
            dl = s2b[i][2] - s2b[i - 1][2]
            if abs(dl) > 1e-7:
                signs.append(dl > 0)
        flips = sum(1 for i in range(1, len(signs))
                    if signs[i] != signs[i - 1])
        bars.append((f"B4 S2b authority: |lean_off| - |lean_on| = "
                     f"{a_meas * 100:.2f} cm in [{AUTH_LO_M * 100:.1f}, "
                     f"{AUTH_HI_M * 100:.1f}] cm (derived 2.76)",
                     AUTH_LO_M <= a_meas <= AUTH_HI_M))
        bars.append((f"B4a S2b ankles pinned at {ANKLE_SAT_DEG} +- "
                     f"{ANKLE_SAT_TOL} deg (min |ankle| in hold "
                     f"{pin_min:.3f})", pinned))
        bars.append((f"B4b S2b no oscillation across the hold "
                     f"({flips} sign flips <= 2)", flips <= 2))
        http_post(base, "/tick_stance", b'{"on": false}')

    # -- S3: nothing else lies
    print("== S3: teardown -- rest is rest")
    reset_ramp_pins()
    time.sleep(5.0)   # dimple decay (tau 0.5 s) past the 0.1 mm cutoff
    st = get_state(base)
    _, fltf = get_verts(base)
    lxf, lzf = lean_of(fltf, sup)
    pcells = [abs(c["P"]) for c in st.get("cells", [])]
    conserve = abs(st.get("conserve_pct", 0.0))
    ankles0 = abs(st.get("stance_ankle_deg", 0.0)) < 1e-6
    back = (abs(lzf - lean_rest[1]) <= 0.0005
            and abs(lxf - lean_rest[0]) <= 0.0005)
    bars.append((f"B5 S3 conservation |conserve_pct| = {conserve:.2e} "
                 f"<= {CONSERVE_BAR}", conserve <= CONSERVE_BAR))
    if st.get("sealed"):
        pmax = max(pcells) if pcells else 0.0
        bars.append((f"B5a S3 rest pressures exactly 0 (max |P| = "
                     f"{pmax:.3e} Pa)", pmax == 0.0))
    bars.append((f"B5b S3 ankles returned to 0 ({ankles0})", ankles0))
    bars.append((f"B5c S3 lean back at rest (dz "
                 f"{abs(lzf - lean_rest[1]) * 100:.4f} cm, dx "
                 f"{abs(lxf - lean_rest[0]) * 100:.4f} cm <= 0.05 cm)", back))

    # -- verdict
    print("== verdict")
    ok = True
    for name, passed in bars:
        print(f"   [{'PASS' if passed else 'FAIL'}] {name}")
        ok &= passed
    if not stance_wired:
        print("VERDICT: INSTRUMENT-ONLY (S2/B3 ran; wire /tick_stance, "
              "then rerun without --skip-stance for the full "
              "S1/S1b/S2b bars)")
        return 0
    verdict = ("PASS -- the balance law answers" if ok else
               "FAIL -- the falsifier fired; gain audit, in order: "
               "(1) the sign of S in step(), (2) the frozen support set, "
               "(3) the |S| probe vs 0.283 m/rad, (4) the dt clamp, "
               "(5) the rest reference")
    print(f"VERDICT: {verdict}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
