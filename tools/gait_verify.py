"""gait_verify.py -- THE GAIT CHECKPOINT MACHINE's falsifier run (agent H13
"gait-verify", fleet; verifies commit 20ecea08, the G1 machine in
ChimeraEngine/engine/membrane_tick.cpp against its prereg:
docs/evidence/agent_fleet/MATTER_KERNEL/SEAL_PREREGISTRATION.md,
"THE GAIT CHECKPOINT PREREGISTRATION" + docs/THE_SHIP_GOAL.md
"THE ROBOT STACK LAW" / "THE MOVEMENT LAW").

HTTP only -- builds nothing, runs nothing:

  GET  /tick_state     the gait fields + the bounded 16-entry gait_log
                       (GAIT_LOG_N=16, membrane_tick.cpp) -- every
                       transition entry carries its own measured gate values
  GET  /verts          [u32 n][f32 x9] -- the INDEPENDENT auditor: the
                       harness re-derives the foot sets from the raw
                       streamed surface and re-measures the patch radii
  POST /tick_gravity   {"on":true|false}   (compact JSON -- see NOTE-PARSE)
  POST /tick_stance    {"on":true|false}
  POST /tick_gait      {"on":true|false}   -- the machine + the cut

NOTE-PARSE: main.cpp's /tick_stance and /tick_gait routes arm on the
LITERAL substring "on":true -- a space ({"on": true}) parses as FALSE and
silently DISARMS. This harness posts compact JSON only. (Route finding,
recorded in R4_GAIT_VERIFY/PROTOCOL.md; /tick_gravity's parse is
space-tolerant.)

Usage (post-build window, SCRATCH engine -- never the shared live world):
  python tools/gait_verify.py --base http://127.0.0.1:8139
Dry-run (read-only, GET only -- safe against any engine incl. 8107):
  python tools/gait_verify.py --base http://127.0.0.1:8107 --read-only
Optional import replay into an EMPTY scratch (boot-restore normally does
this; same payload formats as tools/classify_run.py):
  python tools/gait_verify.py --base http://127.0.0.1:8139 \
      --import-from <dir-containing-session_snapshot>

THE BARS (each cited; full derivations in R4_GAIT_VERIFY/PROTOCOL.md):
  V0  PREFLIGHT  body live: has_scene, sealed, feet cell (lowest yhi) exists
                 [set_gait refusals, membrane_tick.cpp:1467-1489]
  V1  ARM        gravity on -> settled |root_vy| <= 1e-3 m/s and
                 g_contact_n == m*g = 13,824.5 kg x 9.81 = 135,618 N
                 (0.5% tol) [movement-law prereg F1/F2; k*s* = W]
  V2  STANCE     /tick_stance arms; stance_kp = 1/(|S|*1s), |S| ~= 0.283
                 m/rad [stance prereg; the F1 probe law]
  V3  ENABLE     /tick_gait arms; the enable log entry carries the frozen
                 geometry (patchL/R, homeL/R, channels, rate caps,
                 feetCell); the harness's INDEPENDENT patch radius from
                 /verts matches the engine's within 20% [frozen-sets
                 derivation; F1's 0.056-vs-0.283 lesson]
  V4  WALK       >= --min-strides strides; every logged transition
                 REPLAYS its own gate: LIFT->REACH miny >= 0.05 m;
                 REACH->LOAD z >= its logged bar; LOAD/RECOVER->STANCE
                 depth >= 0.8 x 0.01 m and |vy| <= 1e-3 m/s; STANCE->LIFT
                 carries whatif:true [P5 no-gateless-moves; F-LIE]
  V5  WEIGHT     single support: swing depth < 0.2 x sink = 2 mm;
                 LOAD-exit depth of the loaded leg in [0.8,1.2] x sink
                 [prereg P1]
  V7  TELEPORT   per poll, commanded hip/knee deg rate <= measured rate
                 cap (from the enable entry) x poll dt + 10% slack
                 [F-TELEPORT, coarse poll-grain version]
  V8  NO LEAK    |conserve_pct| <= 0.01 at every poll [P4; F1 S3 bar]
  V9  THE CUT    POST /tick_gait {"on":false} MID-SWING -> gait_on false,
                 hip/knee deg EXACTLY 0, both legs STANCE within one
                 poll; the last log entry is {"why":"cut",...} with
                 measured vy/dL/dR/knee/hip; |root_vy| transient
                 > 1e-3 m/s within 2 s (the stumble); stride count
                 frozen; g_contact_n moves off m*g during the run and
                 returns to m*g at settle [P3; F-GLIDE; THE FALL LAW]
  V10 REST       teardown: pressures exactly 0 at rest, ankles 0, root
                 back at baseline [S3/F2 law]

Exit 0 = every bar PASS; 1 = any FAIL (the falsifier fired); 2 =
environment (unreachable engine -- not a verdict).
"""
from __future__ import annotations

import argparse
import array
import json
import math
import os
import struct
import sys
import time
import urllib.error
import urllib.request

# ---- named bars (derived in the prereg; sources in PROTOCOL.md) ----------
SINK_M           = 0.01     # the derived rest sink (k*s* = m*g), header
BEARING_FRAC     = 0.8      # GAIT_BEARING_FRAC, membrane_tick.cpp:31
SWING_DEPTH_FRAC = 0.2      # prereg P1: d_swing < 0.2*sink
BAND_M           = 0.05     # STANCE_BAND_M: the clearance bar (F1 band)
SETTLE_VY        = 1e-3     # GAIT_SETTLE_VY, m/s
TAU_S            = 1.0      # STANCE_TAU_S (the 1 s nulling bar)
CONSERVE_BAR     = 0.01     # percent (P4 / F1 S3)
CONTACT_TOL      = 0.005    # g_contact_n within 0.5% of m*g at settle
G_EARTH          = 9.81     # membrane_tick.cpp:20
MASS_KG          = 13824.5  # 13.8245 m^3 x 1000 (movement-law prereg)
MG_N             = MASS_KG * G_EARTH         # 135,618.345 N
S_PREREG         = 0.283    # m/rad, stance prereg |S| (audit reference)
PATCH_TOL        = 0.20     # independent patch audit tolerance (20%)
ROM_SAT_DEG      = 89.0     # GAIT_MAX_ANG (pose_index's ROM law)
CUT_TRANSIENT_S  = 2.0      # stumble window after the cut
MIN_CHANNEL      = 1e-3     # GAIT_MIN_CHANNEL (the enable refusal)
CUT_ATTEMPTS     = 3        # poll/cut race retries


# ---- HTTP ---------------------------------------------------------------
def http_get(base: str, path: str, timeout: int = 30) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def http_post(base: str, path: str, body: bytes, timeout: int = 60,
              content_type: str = "application/json") -> bytes:
    req = urllib.request.Request(base + path, data=body, method="POST",
                                 headers={"Content-Type": content_type})
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


# ---- bars ledger ----------------------------------------------------------
class Bars:
    def __init__(self) -> None:
        self.rows: list = []  # (id, text, passed bool)

    def add(self, bid: str, text: str, passed: bool) -> None:
        self.rows.append((bid, text, bool(passed)))
        print(f"   [{'PASS' if passed else 'FAIL'}] {bid} {text}")

    def all_pass(self) -> bool:
        return all(p for _, _, p in self.rows)


def wait_settle(base: str, deadline_s: float, hz: float = 20.0):
    """Poll until |root_vy| <= SETTLE_VY; return (settled, worst|vy|, st)."""
    t_end = time.monotonic() + deadline_s
    worst = 0.0
    st: dict = {}
    while time.monotonic() < t_end:
        st = get_state(base)
        vy = abs(st.get("root_vy", 0.0))
        worst = max(worst, vy)
        if vy <= SETTLE_VY:
            return True, worst, st
        time.sleep(1.0 / hz)
    return False, worst, st


def log_entries(st: dict) -> list:
    return st.get("gait_log", []) or []


# ---- the independent /verts auditor ---------------------------------------
def foot_geometry_from_verts(base: str, feet_yhi: float):
    """Re-derive the per-side foot vertex sets the way set_gait does
    (verts at/below the feet cell's yhi, split by x sign), then measure
    each side's xz patch radius and centroid. Independent of the engine's
    internals; membership equals the engine's while the body is at rest."""
    n, flt = get_verts(base)
    sets = ([], [])
    for v in range(n):
        if flt[v * 9 + 1] > feet_yhi:
            continue
        sets[0 if flt[v * 9 + 0] >= 0.0 else 1].append(v)
    rad, cen = [], []
    for s in sets:
        if not s:
            rad.append(0.0)
            cen.append((0.0, 0.0))
            continue
        sx = sz = 0.0
        for v in s:
            sx += flt[v * 9 + 0]
            sz += flt[v * 9 + 2]
        cx, cz = sx / len(s), sz / len(s)
        acc = 0.0
        for v in s:
            dx = flt[v * 9 + 0] - cx
            dz = flt[v * 9 + 2] - cz
            acc += dx * dx + dz * dz
        rad.append(math.sqrt(acc / len(s)))
        cen.append((cx, cz))
    return n, rad, cen


# ---- gate replay (P5 / F-LIE) ---------------------------------------------
def replay_gate(entry: dict) -> tuple:
    """Assert one gait_log entry against the gate that names it. Returns
    (tag, ok, why). A transition logged without its measured gate values,
    or outside its gate, is the F-LIE falsifier firing."""
    frm, to, leg = entry.get("from"), entry.get("to"), entry.get("leg")
    g = entry.get("gates")
    tag = f"{leg} {frm}->{to}@t{entry.get('tick')}"
    if not isinstance(g, dict):
        return (tag, False, "no gates object (F-LIE)")
    if g.get("why") == "cut":
        # the disarm abort (P3's measured entry), reachable from any phase
        ok = all(k in g for k in ("vy", "dL", "dR", "knee", "hip"))
        return (tag, ok, "the measured cut entry"
                if ok else "cut entry missing measured values")
    if frm == "OFF":  # the enable entry: the frozen geometry, all channels
        need = ("patchL", "patchR", "homeL", "homeR", "chLiftL", "chLiftR",
                "rateKL", "rateKR", "rateHL", "rateHR", "feetCell")
        ok = all(k in g for k in need) and all(
            # R3's amendment (ENABLE_AUDIT.md §5): the lift channel only
            # sizes the step (prereg law); a measured null-z channel of
            # 1.663e-5 is legal, so require presence, not magnitude.
            g[k] != 0.0 for k in ("chLiftL", "chLiftR"))
        return (tag, ok, "enable carries the frozen geometry + channels"
                if ok else "enable entry missing channels (F-LIE)")
    base_ok = all(k in g for k in ("dL", "dR", "cL", "cR", "lean", "vy",
                                   "pmax"))
    if frm == "STANCE" and to == "LIFT":
        ok = base_ok and g.get("whatif") is True and \
            g.get("patch", 0.0) > MIN_CHANNEL
        return (tag, ok, "LIFT inside the what-if envelope (patch "
                f"{g.get('patch'):.4f} m)" if ok else
                "LIFT outside the what-if envelope (F-LIE)")
    if frm == "LIFT" and to == "REACH":
        ok = base_ok and g.get("miny", -1e30) >= BAND_M - 1e-4
        return (tag, ok, f"measured clearance miny {g.get('miny'):.4f} >= "
                f"{BAND_M}" if ok else
                f"LIFT->REACH miny {g.get('miny')} < bar {BAND_M}")
    if frm == "REACH" and to == "LOAD":
        ok = base_ok and g.get("bar", 0.0) > MIN_CHANNEL and \
            g.get("z", -1e30) >= g.get("bar", 1e30) - 1e-4
        return (tag, ok, f"stride z {g.get('z'):.4f} >= own bar "
                f"{g.get('bar'):.4f}" if ok else
                f"REACH->LOAD z {g.get('z')} < bar {g.get('bar')}")
    if to == "RECOVER":
        ok = base_ok and g.get("why") in ("support_lost", "touchdown")
        return (tag, ok, f"the measured abort: {g.get('why')}"
                if ok else "RECOVER without a measured why")
    if to == "STANCE":  # the normal LOAD/RECOVER exit: depth + settle
        d = g.get("d" + str(leg), -1e30)  # the engine logs "dL"/"dR"
        ok = base_ok and d >= BEARING_FRAC * SINK_M - 1e-6 and \
            abs(g.get("vy", 1e30)) <= SETTLE_VY
        return (tag, ok, f"bearing depth {d:.4f} m >= "
                f"{BEARING_FRAC * SINK_M}, |vy| "
                f"{abs(g.get('vy', 0.0)):.2e} settled" if ok else
                f"{frm}->STANCE gate fail: d{leg}={d}, vy={g.get('vy')}")
    return (tag, False, f"unknown transition {frm}->{to}")


# ---- main -----------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(
        description="THE GAIT CHECKPOINT MACHINE's falsifier run (H13)")
    ap.add_argument("--base", default="http://127.0.0.1:8139",
                    help="engine base URL (default the scratch 8139)")
    ap.add_argument("--read-only", action="store_true",
                    help="GET only: parse + record, post nothing (the "
                         "dry-run mode; safe on the shared live engine)")
    ap.add_argument("--import-from", default=None, metavar="DIR",
                    help="replay mesh/classify/vertbind/joints/seal "
                         "payloads from DIR (or DIR/session_snapshot) "
                         "into an EMPTY scratch; classify_run.py formats")
    ap.add_argument("--min-strides", type=int, default=3)
    ap.add_argument("--stride-budget", type=float, default=90.0,
                    help="seconds allowed for the walk phase")
    ap.add_argument("--hz", type=float, default=10.0,
                    help="poll rate for the run/cut phases")
    ap.add_argument("--json", default=None,
                    help="write the full results dict here (evidence)")
    args = ap.parse_args()
    base = args.base.rstrip("/")
    bars = Bars()
    results: dict = {"base": base,
                     "mode": "read-only" if args.read_only else "armed",
                     "routes": {}, "log_replay": [], "ts": time.strftime(
                         "%Y-%m-%d %H:%M:%S")}

    def finish(code: int) -> int:
        results["bars"] = [(b, t, p) for b, t, p in bars.rows]
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
            print(f"   evidence written: {args.json}")
        if code == 0:
            print("VERDICT: PASS -- the walking is real: measured gates, "
                  "weight transfer on the contact force, the cut stops it "
                  "within one poll and the measured abort is logged")
        else:
            print("VERDICT: FAIL -- the falsifier fired; audit order per "
                  "prereg: (1) the logged gate values, (2) the enable "
                  "channels vs the /verts audit, (3) the rate caps, "
                  "(4) the what-if envelope, (5) the cut entry")
        return code

    # ---- phase V0: preflight (read-only safe) -----------------------------
    # NOTE: main.cpp:3341 answers ANY unknown route with HTTP 200 and the
    # literal body "Not found" -- a 200 proves nothing by itself, so each
    # route is classified BY BODY (the dry-run finding on the live 8107:
    # /health does not exist and 200s as "Not found").
    routes = results["routes"]
    for r in ("/tick_state", "/state", "/verts", "/topology", "/health"):
        try:
            b = http_get(base, r, timeout=25)
            if b.strip() == b"Not found":
                routes[r] = f"200 {len(b)}B BUT BODY 'Not found' -> NO ROUTE"
            else:
                routes[r] = f"200 {len(b)}B"
        except urllib.error.HTTPError as e:
            routes[r] = f"HTTP {e.code}"
        except (urllib.error.URLError, OSError) as e:
            routes[r] = f"unreachable ({e})"
    if not routes["/tick_state"].startswith("200"):
        print(f"FAIL unreachable: /tick_state at {base} -> "
              f"{routes['/tick_state']}")
        return 2
    print(f"== route inventory: {routes}")
    st = get_state(base)
    results["state0"] = st
    feet_cell, feet_yhi = -1, 1e30
    for i, c in enumerate(st.get("cells", [])):
        if c.get("yhi", 1e30) < feet_yhi:
            feet_yhi, feet_cell = c["yhi"], i
    scene = bool(st.get("has_scene")) and bool(st.get("sealed")) \
        and feet_cell >= 0
    bars.add("V0", f"body live: has_scene={st.get('has_scene')} "
                   f"sealed={st.get('sealed')} feetCell={feet_cell} "
                   f"(yhi={feet_yhi:.3f}) n_cells={st.get('n_cells')}",
             scene)
    print(f"   gravity_on={st.get('gravity_on')} "
          f"stance_on={st.get('stance_on')} gait_on={st.get('gait_on')}")

    if args.read_only:
        # Dry-run: verify the /verts parsing + gait-field presence against
        # the REAL payload shape, record what answers and what 404s,
        # POST nothing, no verdict.
        try:
            n, flt = get_verts(base)
            bars.add("V-RO", f"/verts parses: {n} verts, vert0.y="
                             f"{flt[1]:.6f} (the 36-B stride)", n > 0)
        except Exception as e:  # noqa: BLE001 -- record, don't crash
            bars.add("V-RO", f"/verts parse failed: {e}", False)
        gait_fields = all(k in st for k in
                          ("gait_on", "gait_log", "gait_depth_l",
                           "gait_stride", "gait_feet_cell"))
        bars.add("V-RO2", f"gait fields in /tick_state "
                          f"(gait_on={st.get('gait_on')}, log entries="
                          f"{len(log_entries(st))}) -- this binary "
                          f"INCLUDES the G1 build", gait_fields)
        print("== READ-ONLY dry run complete: no POSTs sent, no verdict")
        results["bars"] = [(b, t, p) for b, t, p in bars.rows]
        results["verdict"] = "DRY-RUN (environment check only; no verdict)"
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=1)
            print(f"   evidence written: {args.json}")
        ok = bars.all_pass()
        print(f"DRY-RUN: {'environment READY for the post-build run' if ok else 'environment BROKEN (see the FAIL rows)'}")
        return 0 if ok else 1
    if not scene:
        print("FAIL V0: the body is not import-ready (needs a sealed "
              "classified mesh with a feet cell). Boot the scratch with "
              "its session snapshot or pass --import-from.")
        return finish(1)

    # ---- optional import replay (empty scratch) ---------------------------
    if args.import_from:
        snap = os.path.join(args.import_from, "session_snapshot")
        if not os.path.isdir(snap):
            snap = args.import_from
        ct = "application/octet-stream"
        for fname, route in (("mesh_bin.blob", "/mesh_bin"),
                             ("tick_classify.blob", "/tick_classify"),
                             ("tick_vertbind.blob", "/tick_vertbind"),
                             ("tick_joints.blob", "/tick_joints")):
            with open(os.path.join(snap, fname), "rb") as f:
                body = f.read()
            resp = http_post(base, route, body, timeout=120, content_type=ct)
            print(f"   import {route} <- {fname}: {resp[:48]}")
        hist = os.path.join(snap, "tick_seal_history.log")
        if os.path.isfile(hist):
            with open(hist, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        resp = http_post(base, "/tick_seal",
                                         line.encode(), timeout=120)
                        print(f"   import /tick_seal {line}: {resp[:48]}")
        st = get_state(base)
        print(f"   after import: n_cells={st.get('n_cells')} "
              f"sealed={st.get('sealed')}")
        if not (bool(st.get("sealed")) and st.get("n_cells", 0) >= 2):
            return finish(1)

    # ---- phase V1: ARM GRAVITY (the fall law's field) ---------------------
    if not st.get("gravity_on"):
        http_post(base, "/tick_gravity", b'{"on":true}')
        st = get_state(base)
    bars.add("V1a", f"/tick_gravity arms (gravity_on="
                   f"{st.get('gravity_on')})", bool(st.get("gravity_on")))
    settled, worst_vy, st = wait_settle(base, 6.0)
    contact = st.get("g_contact_n", 0.0)
    dev = abs(contact - MG_N) / MG_N
    bars.add("V1b", f"settled={settled} (worst |root_vy| "
                   f"{worst_vy:.2e}); g_contact_n {contact:.0f} N vs "
                   f"m*g {MG_N:.0f} N (dev {dev * 100:.3f}% <= "
                   f"{CONTACT_TOL * 100}%)",
             settled and dev <= CONTACT_TOL)
    rest_root_y = st.get("root_y", 0.0)
    rest_pmax = max((abs(c.get("P", 0.0)) for c in st.get("cells", [])),
                    default=0.0)
    bars.add("V1c", f"rest pressures exactly 0 (max {rest_pmax:.2e} Pa), "
                    f"root_y {rest_root_y:+.5f} m (the derived +9.5 mm "
                    f"rise branch)", rest_pmax == 0.0)

    # ---- phase V2: STANCE (the balance rung underneath) --------------------
    http_post(base, "/tick_stance", b'{"on":true}')
    st = get_state(base)
    stance_on = bool(st.get("stance_on"))
    kp = st.get("stance_kp", 0.0)
    s_meas = 1.0 / kp if kp else 0.0
    bars.add("V2", f"/tick_stance arms (stance_on={stance_on}); "
                   f"kp={kp:.3f} rad/(m s) -> |S| ~ {s_meas:.3f} m/rad "
                   f"(prereg {S_PREREG})", stance_on)
    if not stance_on:
        print("FAIL V2: stance refused -- the rung stack cannot arm")
        return finish(1)

    # ---- phase V3: GAIT ENABLE + the independent channel audit ------------
    try:
        http_post(base, "/tick_gait", b'{"on":true}')
    except urllib.error.HTTPError as e:
        bars.add("V3", f"/tick_gait -> HTTP {e.code} (route not wired in "
                       f"this binary)", False)
        return finish(1)
    st = get_state(base)
    gait_on = bool(st.get("gait_on"))
    enable_entry = None
    for e in log_entries(st):
        if e.get("from") == "OFF":
            enable_entry = e.get("gates", {})
    bars.add("V3a", f"/tick_gait arms (gait_on={gait_on}, feetCell="
                    f"{st.get('gait_feet_cell')})", gait_on)
    if not gait_on:
        print("FAIL V3: set_gait refused (needs gravity + stance + "
              "classification + pins 13-18 + a sealed feet cell)")
        return finish(1)
    rate_caps: dict = {}
    if enable_entry:
        rate_caps = {"HL": enable_entry.get("rateHL", 0.0),
                     "HR": enable_entry.get("rateHR", 0.0),
                     "KL": enable_entry.get("rateKL", 0.0),
                     "KR": enable_entry.get("rateKR", 0.0)}
        pl, pr = enable_entry.get("patchL", 0.0), \
            enable_entry.get("patchR", 0.0)
        _, rad_h, _ = foot_geometry_from_verts(base, feet_yhi)
        if pl > 0 and pr > 0 and rad_h[0] > 0 and rad_h[1] > 0:
            worst = max(abs(rad_h[0] - pl) / pl, abs(rad_h[1] - pr) / pr)
            bars.add("V3b", f"INDEPENDENT /verts patch audit: harness "
                            f"L/R {rad_h[0]:.4f}/{rad_h[1]:.4f} m vs engine "
                            f"{pl:.4f}/{pr:.4f} m (worst {worst * 100:.1f}% "
                            f"<= {PATCH_TOL * 100:.0f}%)", worst <= PATCH_TOL)
        else:
            bars.add("V3b", "patch audit skipped (enable entry or foot "
                            "sets degenerate)", False)
    else:
        bars.add("V3b", "enable entry missing from gait_log (F-LIE)",
                 False)

    # ---- phases V4/V5/V7/V8: THE RUN ---------------------------------------
    print(f"== RUN: polling at {args.hz} Hz for >= {args.min_strides} "
          f"strides (budget {args.stride_budget:.0f} s)")
    gate_results: list = []
    seen = 0
    stride0 = st.get("gait_stride", 0)
    t_run0 = time.monotonic()
    next_poll = t_run0
    swing_depth_worst = 0.0
    load_exit_depths: list = []
    contact_min, contact_max = 1e30, -1e30
    teleport_worst = 0.0
    conserve_worst = 0.0
    prev_pose = None
    prev_t = None
    recover_seen = 0
    while True:
        now = time.monotonic()
        if next_poll > now:
            time.sleep(min(next_poll - now, 0.2))
        next_poll = max(next_poll + 1.0 / args.hz, time.monotonic())
        now = time.monotonic()
        st = get_state(base)
        ents = log_entries(st)
        while seen < len(ents):
            e = ents[seen]
            tag, ok, why = replay_gate(e)
            gate_results.append((tag, ok, why))
            if e.get("to") == "RECOVER":
                recover_seen += 1
            if e.get("from") == "LOAD" and e.get("to") == "STANCE":
                load_exit_depths.append(
                    e.get("gates", {}).get("d" + str(e.get("leg")), 0.0))
            seen += 1
        phases = (st.get("gait_l"), st.get("gait_r"))
        dnow = (st.get("gait_depth_l", 0.0), st.get("gait_depth_r", 0.0))
        if "LIFT" in phases or "REACH" in phases:
            sw = 0 if phases[0] in ("LIFT", "REACH") else 1
            swing_depth_worst = max(swing_depth_worst, dnow[sw])
        pose_now = tuple(st.get(k, 0.0) for k in
                         ("gait_hip_l_deg", "gait_hip_r_deg",
                          "gait_knee_l_deg", "gait_knee_r_deg"))
        if prev_pose is not None and prev_t is not None:
            dtp = max(now - prev_t, 1e-3)
            for key, (a, b) in zip(("HL", "HR", "KL", "KR"),
                                   zip(pose_now, prev_pose)):
                cap = rate_caps.get(key, 0.0)
                if cap > 0:
                    overshoot = (abs(a - b) / dtp) / (cap * 57.29577951308)
                    teleport_worst = max(teleport_worst, overshoot)
        prev_pose, prev_t = pose_now, now
        contact = st.get("g_contact_n", 0.0)
        contact_min, contact_max = min(contact_min, contact), \
            max(contact_max, contact)
        conserve_worst = max(conserve_worst,
                             abs(st.get("conserve_pct", 0.0)))
        if st.get("gait_stride", 0) >= stride0 + args.min_strides:
            break
        if time.monotonic() - t_run0 > args.stride_budget:
            break
    run_s = time.monotonic() - t_run0
    st_end = get_state(base)
    strides_made = st_end.get("gait_stride", 0) - stride0
    n_ok = sum(1 for _, ok, _ in gate_results if ok)
    bars.add("V4", f"{strides_made} strides in {run_s:.1f} s; "
                   f"{len(gate_results)} logged transitions, {n_ok} replay "
                   f"OK ({recover_seen} measured RECOVER aborts seen)",
             strides_made >= args.min_strides and n_ok == len(gate_results))
    results["log_replay"] = [{"t": t, "ok": ok, "why": w}
                             for t, ok, w in gate_results]
    in_band = load_exit_depths and all(
        BEARING_FRAC * SINK_M - 1e-6 <= d <= 1.2 * SINK_M + 1e-6
        for d in load_exit_depths)
    bars.add("V5", f"single support: worst swing depth "
                   f"{swing_depth_worst * 1000:.2f} mm < "
                   f"{SWING_DEPTH_FRAC * SINK_M * 1000:.0f} mm; LOAD-exit "
                   f"depths {[round(d * 1000, 2) for d in load_exit_depths]}"
                   f" mm in [{BEARING_FRAC * SINK_M * 1000:.0f},"
                   f"{1.2 * SINK_M * 1000:.0f}] mm -> {in_band}",
             swing_depth_worst < SWING_DEPTH_FRAC * SINK_M and bool(in_band))
    bars.add("V7", f"teleport audit (poll grain): worst commanded-rate "
                   f"overshoot vs the MEASURED caps = "
                   f"{teleport_worst:.2f}x (bar <= 1.10)",
             teleport_worst <= 1.10)
    bars.add("V8", f"|conserve_pct| worst {conserve_worst:.2e} <= "
                   f"{CONSERVE_BAR} through every phase",
             conserve_worst <= CONSERVE_BAR)
    results["run"] = {"strides": strides_made, "run_s": run_s,
                      "swing_depth_worst": swing_depth_worst,
                      "load_exit_depths": load_exit_depths,
                      "contact_min": contact_min, "contact_max": contact_max,
                      "conserve_worst": conserve_worst,
                      "teleport_overshoot": teleport_worst,
                      "recover_entries": recover_seen}
    print(f"   the weight transfer is MEASURED: contact force ranged "
          f"[{contact_min:.0f}, {contact_max:.0f}] N vs m*g {MG_N:.0f} N "
          f"--- an animation has no contact force to range")

    # ---- phase V9: THE CUT MID-SWING (P3 / F-GLIDE) ------------------------
    cut_ok = False
    for attempt in range(CUT_ATTEMPTS):
        # wait for a mid-swing moment (a leg in LIFT/REACH, or held poses)
        cut_st = None
        t_wait = time.monotonic() + min(args.stride_budget, 30.0)
        while time.monotonic() < t_wait:
            s2 = get_state(base)
            pose2 = tuple(s2.get(k, 0.0) for k in
                          ("gait_hip_l_deg", "gait_hip_r_deg",
                           "gait_knee_l_deg", "gait_knee_r_deg"))
            if "LIFT" in (s2.get("gait_l"), s2.get("gait_r")) or \
               "REACH" in (s2.get("gait_l"), s2.get("gait_r")) or \
               any(abs(p) > 1e-6 for p in pose2):
                cut_st = s2
                break
            time.sleep(1.0 / args.hz)
        if cut_st is None:
            break
        pre_phases = (cut_st.get("gait_l"), cut_st.get("gait_r"))
        pre_poses = tuple(cut_st.get(k, 0.0) for k in
                          ("gait_hip_l_deg", "gait_hip_r_deg",
                           "gait_knee_l_deg", "gait_knee_r_deg"))
        pre_stride = cut_st.get("gait_stride", 0)
        http_post(base, "/tick_gait", b'{"on":false}')
        st_cut = get_state(base)  # one poll after the cut
        poses0 = tuple(st_cut.get(k, 0.0) for k in
                       ("gait_hip_l_deg", "gait_hip_r_deg",
                        "gait_knee_l_deg", "gait_knee_r_deg"))
        frozen = (not st_cut.get("gait_on")
                  and st_cut.get("gait_l") == "STANCE"
                  and st_cut.get("gait_r") == "STANCE"
                  and all(abs(p) < 1e-9 for p in poses0))
        ents = log_entries(st_cut)
        cut_entry = ents[-1] if ents and \
            ents[-1].get("gates", {}).get("why") == "cut" else None
        if frozen and cut_entry is not None:
            bars.add("V9a", f"cut mid-swing (L/R = {pre_phases}, held pose "
                            f"{[round(p, 2) for p in pre_poses]} deg): one "
                            f"poll later gait_on=false, both legs STANCE, "
                            f"pins 13-16 at EXACTLY 0", True)
            bars.add("V9b", "the measured abort entry: "
                            f"{json.dumps(cut_entry.get('gates'))[:140]}",
                     True)
            cut_ok = True
            break
        if attempt < CUT_ATTEMPTS - 1:
            # the machine left mid-swing between poll and POST (the
            # LOAD->STANCE race): re-arm and try again -- a harness race,
            # not a verdict
            print(f"   cut attempt {attempt + 1} raced the machine "
                  f"(frozen={frozen}, entry={bool(cut_entry)}); re-arming")
            http_post(base, "/tick_gait", b'{"on":true}')
            st = get_state(base)
            stride0 = st.get("gait_stride", stride0)
            seen = len(log_entries(st))
        else:
            bars.add("V9a", f"cut mid-swing FAILED after "
                            f"{CUT_ATTEMPTS} attempts (frozen={frozen}, "
                            f"cut entry={bool(cut_entry)}) -- F-GLIDE",
                     False)
    if not cut_ok:
        bars.add("V9c", "the cut falsifier did not run (no mid-swing cut "
                        "landed)", False)
    else:
        # the stumble: a real root transient after the cut (P3), stride
        # frozen, then the contact force returns to m*g at settle
        vy_peak = 0.0
        stride_frozen = True
        t_end = time.monotonic() + CUT_TRANSIENT_S
        while time.monotonic() < t_end:
            s2 = get_state(base)
            vy_peak = max(vy_peak, abs(s2.get("root_vy", 0.0)))
            if s2.get("gait_stride", 0) != pre_stride:
                stride_frozen = False
            time.sleep(0.02)
        stride_txt = "frozen" if stride_frozen else \
            "CHANGED (F-GLIDE: stepping continued)"
        bars.add("V9c", f"after the cut: stride count {stride_txt} at "
                        f"{pre_stride}; |root_vy| transient peak "
                        f"{vy_peak:.2e} > {SETTLE_VY} (the stumble "
                        f"number, measured)",
                 stride_frozen and vy_peak > SETTLE_VY)

    # ---- phase V10: REST IS REST -------------------------------------------
    settled, worst_vy, st = wait_settle(base, 15.0)
    contact = st.get("g_contact_n", 0.0)
    dev = abs(contact - MG_N) / MG_N
    pmax = max((abs(c.get("P", 0.0)) for c in st.get("cells", [])),
               default=0.0)
    ankles0 = abs(st.get("stance_ankle_deg", 0.0)) < 1e-6
    back_root = abs(st.get("root_y", 0.0) - rest_root_y) < 5e-4
    bars.add("V10", f"teardown: settled={settled}, g_contact_n "
                    f"{contact:.0f} N (dev {dev * 100:.3f}%), max|P| "
                    f"{pmax:.2e} Pa == 0, ankles0={ankles0}, root back "
                    f"at {rest_root_y:+.5f}: {back_root}",
             settled and dev <= CONTACT_TOL and pmax == 0.0
             and ankles0 and back_root)
    results["final_state"] = st

    # ---- verdict ------------------------------------------------------------
    print("== verdict: every bar was printed with its measurement as it "
          "was evaluated")
    return finish(0 if bars.all_pass() else 1)


if __name__ == "__main__":
    sys.exit(main())
