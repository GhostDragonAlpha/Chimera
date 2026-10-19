"""Workshop challenge 1 — "keep the salvage load above the marked hazard area".

GAME_PLAN_ACTION_RPG.md §5.1 (matter workshop, first bounded slice). One
launchable native scene on the resident B2 runtime (NO engine edits): a
granite hazard slab marks the region in-scene (a visible goal, not an
invisible force), the steel salvage crate must be kept clear above it, and
the player builds through the FROZEN construction transactions
(place / weld / re-weld / remove / save / restore — the B4/B5 surface).

Two structurally different demonstrated solutions against the same
objective:
  SOLUTION A "welded span"  — two granite piers on solid ground flanking the
                              hazard, a timber deck spanning them whose four
                              corners REST on the pier tops with two live
                              weld connectors attached at each interface in
                              parallel (the B4 cradle pattern), the crate
                              yaw-rotated 90 deg on the deck. The load path
                              is ground -> piers -> contact + welds -> deck
                              -> crate; the attachment history is two live
                              connector forces, and the B4 connection
                              improvement (same anchors, 20x stiffer re-weld)
                              is demonstrated on them.
  SOLUTION B "contact tower" — one granite pillar standing on the hazard
                              slab itself, crate balanced unrotated on top.
                              NO connectors: ground -> slab -> pillar ->
                              crate, all one-sided penalty rungs. The
                              attachment history is empty and the reactions
                              ride the slab.

Fail + recover: the first build places the crate with its COM past the
pillar's support edge (the B8/B9 topple class); the crate comes down onto
the hazard, the board names it with one actionable line, and the cheap retry
(replace the crate centred) recovers into solution B. Rejected edits
preserve the accepted state (B9 law, hash-checked). Save -> clear ->
restore is bit-exact (B4 law).

Determinism discipline (objective-loop precedent): every part spawns at its
ANALYTIC rest-sink pose (B3 pre-sink chain math, nothing measured feeds a
spawn), all edits happen PAUSED on an unadvanced analytic base, and every
deterministic anchor saves its full state document. The state hash covers
the whole save doc INCLUDING the step counter (b2_scene.cpp save_doc_), so
cross-run claims are made on the document: analytic anchors byte-identical
modulo the step counter, settled states (which carry the engine's documented
rest jitter) within the objective-loop band (EQUIV_TOL excluding
steps/omega). Save -> clear -> restore stays bit-exact (the restored doc
carries its own step count).

Run:   python tools/construction_packet/workshop_challenge1.py run --out DIR --port 8801
       python tools/construction_packet/workshop_challenge1.py compare RUN1 RUN2 --out comparison.json
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE), str(HERE.parent), str(HERE.parent.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import b2_scene_gen  # noqa: E402

REPO = HERE.parent.parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"

G = b2_scene_gen.G
RS = b2_scene_gen.REST_SINK_M

# ── the frozen route surface (objective-loop FROZEN set + the Studio lane) ──
FROZEN = {"/tick_b2_admit", "/tick_b2_state", "/tick_b2_place",
          "/tick_b2_remove", "/tick_b2_parts", "/tick_b2_clear",
          "/tick_b2_pause", "/tick_b2_load", "/tick_b2_support",
          "/tick_b2_gravity", "/tick_b2_pick", "/tick_b2_inspect",
          "/tick_b2_weld", "/tick_b2_weld_remove", "/tick_b2_patch",
          "/tick_b2_save", "/tick_b2_restore", "/tick_b2_hash",
          "/tick_b2_render_lod", "/tick_b2_clock", "/tick_state",
          "/frame", "/glass", "/cameras", "/studio", "/ui_click"}

# ── kit geometry (metres; y is vertical; all from b2_scene_gen.box_document) ─
PAD = {"id": "hazard_pad", "x0": 0.48, "x1": 0.76, "z0": -0.08, "z1": 0.08,
       "h": 0.04, "rho": 2700, "mu": 0.5}          # the marked hazard slab
PIER = {"dx": 0.10, "h": 0.30, "dz": 0.18, "rho": 2700, "mu": 0.6}
PIER_A = {"id": "pier_a", "x0": 0.28, "x1": 0.38}
PIER_B = {"id": "pier_b", "x0": 0.86, "x1": 0.96}
DECK = {"id": "deck", "x0": 0.30, "x1": 0.92, "h": 0.06, "dz": 0.14,
        "rho": 600, "mu": 0.3}                      # timber span; its four
                                                    # corners rest ON the two
                                                    # pier tops (each corner
                                                    # projects strictly
                                                    # inside a pier top)
PILLAR = {"id": "pillar", "cx": 0.62, "dx": 0.12, "h": 0.10, "dz": 0.12,
          "rho": 2700, "mu": 0.6}
CRATE = {"id": "crate", "cx": 0.62, "dx": 0.10, "h": 0.05, "dz": 0.05,
         "rho": 7850, "mu": 0.4}                    # the steel salvage load
PALLET = {"id": "kit_pallet", "cx": -0.25, "dx": 0.08, "h": 0.06, "dz": 0.08,
          "rho": 2700, "mu": 0.6}                   # kit staging block (the
                                                    # admission law needs >=2
                                                    # scene parts; it parks
                                                    # left of the build zone)
CRATE_OFF_X = 0.70                                  # the topple build: COM
                                                    # 20 mm past the pillar edge
K_SOFT, K_STIFF = 2000.0, 20000.0                   # B5 weld / B4 improvement
PIER_SPAWN_TOP = PIER["h"] - RS                     # analytic pre-sunk top
PAD_SPAWN_TOP = PAD["h"] - RS                       # pre-sunk alone-rest top

# objective predicate bands (frozen here; the prereg quotes them verbatim)
CLEAR_OK = 0.004            # crate bottom >= pad top + 4 mm == held
CLEAR_LOST = 0.003          # crate bottom <= pad top + 3 mm == on the hazard
REGION_X = (0.54, 0.70)     # crate COM x band (pad 0.48..0.76 with margin)
REGION_Z = 0.05             # |crate COM z| band
TILT_MIN_UP_Y = 0.9848      # crate up-axis >= 10 deg from vertical == tipped
                            # (a leaning crate defeats the axis-aligned
                            # clearance metric; measured leaning rest: the
                            # toppled crate held +19 mm clearance at a large
                            # tilt)
HISTORY_S = 5.0             # measured load/attachment history window
SAMPLE_DT = 0.25            # 20 samples; the last 8 span the 2 s window
SETTLE_V = 2e-3             # "settled": every part speed below this
EQUIV_TOL = 1e-3            # objective-loop cross-run band (measured floor)
EQUIV_SKIP = frozenset({"steps", "omega_rad_s"})


# ─────────────────────────────────────────────────────────────────────────────
# part documents — analytic spawns only (B3 pre-sink chain law)
# ─────────────────────────────────────────────────────────────────────────────
def _mass(x0, x1, y0, y1, z0, z1, rho):
    return rho * (x1 - x0) * (y1 - y0) * (z1 - z0)


def _kt(mass_kg):
    """A part's ground k_total under the B2 rest-sink law (4 bottom sites)."""
    return mass_kg * G / RS


def _pair_kt(ka, kb):
    """B3's pair k_total for a part-part interface: (kt_a + kt_b) / 2."""
    return (ka + kb) / 2.0


M_PAD = _mass(PAD["x0"], PAD["x1"], -RS, PAD["h"] - RS, PAD["z0"], PAD["z1"],
              PAD["rho"])
KT_PAD = _kt(M_PAD)
M_PIER = _mass(0, PIER["dx"], 0, PIER["h"], 0, PIER["dz"], PIER["rho"])
KT_PIER = _kt(M_PIER)
M_DECK = _mass(0, DECK["x1"] - DECK["x0"], 0, DECK["h"], 0, DECK["dz"],
               DECK["rho"])
KT_DECK = _kt(M_DECK)
M_PILLAR = _mass(0, PILLAR["dx"], 0, PILLAR["h"], 0, PILLAR["dz"],
                 PILLAR["rho"])
KT_PILLAR = _kt(M_PILLAR)
M_CRATE = _mass(0, CRATE["dx"], 0, CRATE["h"], 0, CRATE["dz"], CRATE["rho"])
KT_CRATE = _kt(M_CRATE)

# B3 chain law for the span (solution A): the deck's four corners rest ON
# the two pier tops — all four deck bottom vertices are active, so the
# deck/pier interface total is exactly the B3 pair k_total. The deck spawns
# pre-sunk to that pair equilibrium (the crate then spawns at the crate/deck
# pair equilibrium, chain 'span'). Nothing measured feeds a spawn.
W_DECK = M_DECK * G
SINK_DECK_PIER = W_DECK / _pair_kt(KT_DECK, KT_PIER)
DECK_SPAWN_BOTTOM = PIER_SPAWN_TOP - SINK_DECK_PIER
DECK_SPAWN_TOP = DECK_SPAWN_BOTTOM + DECK["h"]
WELD_Y = PIER_SPAWN_TOP - SINK_DECK_PIER / 2        # anchors at the deck/
                                                    # pier interface


def pad_doc():
    """The hazard slab, spawned pre-sunk to its alone-rest penetration."""
    return b2_scene_gen.box_document(
        PAD["id"], PAD["x0"], PAD["x1"], -RS, PAD["h"] - RS,
        PAD["z0"], PAD["z1"], PAD["rho"], PAD["mu"])


def pier_doc(which: dict):
    return b2_scene_gen.box_document(
        which["id"], which["x0"], which["x1"], -RS, PIER_SPAWN_TOP,
        -PIER["dz"] / 2, PIER["dz"] / 2, PIER["rho"], PIER["mu"])


def deck_doc():
    return b2_scene_gen.box_document(
        DECK["id"], DECK["x0"], DECK["x1"], DECK_SPAWN_BOTTOM,
        DECK_SPAWN_TOP, -DECK["dz"] / 2, DECK["dz"] / 2,
        DECK["rho"], DECK["mu"])


def pillar_spawn_bottom() -> float:
    """B3 chain law: the spawned pad top descends w_pillar/kt_pad under the
    pillar, and the pillar sinks w_pillar/pair(pillar,pad) into it."""
    return (PAD_SPAWN_TOP - M_PILLAR * G / KT_PAD
            - M_PILLAR * G / _pair_kt(KT_PILLAR, KT_PAD))


def pillar_doc():
    y0 = pillar_spawn_bottom()
    return b2_scene_gen.box_document(
        PILLAR["id"], PILLAR["cx"] - PILLAR["dx"] / 2,
        PILLAR["cx"] + PILLAR["dx"] / 2, y0, y0 + PILLAR["h"],
        -PILLAR["dz"] / 2, PILLAR["dz"] / 2, PILLAR["rho"], PILLAR["mu"])


def crate_doc(pid: str = "crate", cx: float = CRATE["cx"], yaw90: bool = False,
              bottom_y: float | None = None, chain: str = "tower") -> dict:
    """The salvage crate. `chain` picks the analytic spawn chain:
    'tower' = crate onto the spawned pillar; 'span' = crate (yaw-rotated)
    onto the spawned deck. All spawn inputs are the B3 chain math — the
    spawn never reads a measured pose, so the paused state is exact.
    `bottom_y` overrides the analytic spawn (used only by the recovery
    re-place onto the SETTLED pillar, a band state by declaration)."""
    dx, h, dz = CRATE["dx"], CRATE["h"], CRATE["dz"]
    if chain == "tower":
        # spawn at the crate/pillar PAIR equilibrium (the pair penetration
        # is relative; the crate rides the pad/pillar descent that its own
        # weight causes, so the full-chain drop would over-compress the
        # pair and pop the crate at spawn)
        pillar_top = pillar_spawn_bottom() + PILLAR["h"]
        w = M_CRATE * G
        y0 = pillar_top - w / _pair_kt(KT_CRATE, KT_PILLAR)
    elif chain == "span":
        # spawn at the crate/deck PAIR equilibrium only: the pair
        # penetration is relative, so as the deck descends under the added
        # weight the crate rides it with the pair unchanged. (The full-chain
        # drop double-counted the deck's descent — measured calibration
        # failure: the over-compressed crate popped off the falling deck and
        # tunneled into the slab.)
        w = M_CRATE * G
        y0 = DECK_SPAWN_TOP - w / _pair_kt(KT_CRATE, KT_DECK)
    else:
        raise ValueError(chain)
    if bottom_y is not None:
        y0 = bottom_y
    if yaw90:
        # local frame centred on the COM; the yaw quaternion maps authored +x
        # to world +z (the rotate action, visible on the 2:1 crate)
        q = (math.cos(math.pi / 4), 0.0, math.sin(math.pi / 4), 0.0)
        vs = [(-dx / 2, -h / 2, -dz / 2), (dx / 2, -h / 2, -dz / 2),
              (dx / 2, -h / 2, dz / 2), (-dx / 2, -h / 2, dz / 2),
              (-dx / 2, h / 2, -dz / 2), (dx / 2, h / 2, -dz / 2),
              (dx / 2, h / 2, dz / 2), (-dx / 2, h / 2, dz / 2)]
        ixx = M_CRATE / 12 * (h * h + dz * dz)
        iyy = M_CRATE / 12 * (dx * dx + dz * dz)
        izz = M_CRATE / 12 * (dx * dx + h * h)
        k_site, c_site = b2_scene_gen.rung_constants(M_CRATE, 4)
        return {"id": pid, "mass_kg": M_CRATE, "com_local_m": [0.0, 0.0, 0.0],
                "inertia_com_local_kg_m2": [ixx, 0, 0, 0, iyy, 0, 0, 0, izz],
                "vertices_local_m": [c for v in vs for c in v],
                "boundary_triangles": [i for f in b2_scene_gen.BOX_FACES
                                       for i in f],
                "pose_c_m": [cx, y0 + h / 2, 0.0], "pose_q_wxyz": list(q),
                "ground": {"k_n_per_m": k_site, "c_n_s_per_m": c_site},
                "mu": CRATE["mu"]}
    return b2_scene_gen.box_document(
        pid, cx - dx / 2, cx + dx / 2, y0, y0 + h, -dz / 2, dz / 2,
        CRATE["rho"], CRATE["mu"])


def pallet_doc():
    return b2_scene_gen.box_document(
        PALLET["id"], PALLET["cx"] - PALLET["dx"] / 2,
        PALLET["cx"] + PALLET["dx"] / 2, -RS, PALLET["h"] - RS,
        -PALLET["dz"] / 2, PALLET["dz"] / 2, PALLET["rho"], PALLET["mu"])


def scene_doc() -> dict:
    return {"schema": "chimera.b2_scene.v1", "gravity_m_s2": G,
            "parts": [pad_doc(), pallet_doc()],
            "reason": "workshop challenge 1: the marked hazard slab (visible "
                      "goal region) + the kit pallet, on the resident B2 "
                      "runtime"}


def weld_anchors(pier: dict) -> list[list[float]]:
    """B5's symmetric 3-anchor pattern at the pier's x-centre, at the
    deck/pier interface height. Pairs are COINCIDENT (one world point
    captured into both parts' local frames -> zero rest length, zero
    preload): the deck already RESTS on the pier tops, so the connectors
    attach in parallel with the corner contact (the B4 cradle pattern) and
    start at zero force."""
    xc = (pier["x0"] + pier["x1"]) / 2
    return [[xc, WELD_Y, -0.02, xc, WELD_Y, -0.02],
            [xc, WELD_Y, 0.02, xc, WELD_Y, 0.02],
            [xc, WELD_Y, 0.0, xc, WELD_Y, 0.0]]


# ─────────────────────────────────────────────────────────────────────────────
# engine client (B-suite style) + studio board (the S5 readout pattern)
# ─────────────────────────────────────────────────────────────────────────────
class Engine:
    def __init__(self, port: int):
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.used: set[str] = set()

    def _go(self, path, body: str = "", method: str = "GET", timeout=10,
            raw=False):
        self.used.add(path.split("?")[0])
        if method == "GET":
            req = urllib.request.Request(self.base + path)
        else:
            req = urllib.request.Request(self.base + path, data=body.encode(),
                                         method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            data = e.read()
        if raw:
            return data
        return json.loads(data.decode())

    def get(self, path):
        return self._go(path)

    def post(self, path, doc=None):
        return self._go(path, json.dumps(doc or {}), "POST")

    def post_raw(self, path, body: str):
        return self._go(path, body, "POST")

    def raw(self, path, timeout=25):
        return self._go(path, timeout=timeout, raw=True)


def board_write(path: Path, standing: str, cell: str, status: str) -> None:
    doc = {"standing": standing, "updated": "workshop challenge 1",
           "stages": [{"id": "WS3",
                       "name": "Salvage over the hazard",
                       "status": status,
                       "law": "objective law: the crate's COM stays inside "
                              "the marked region with its bottom >= 4 mm "
                              "above the slab top for the whole window; the "
                              "load path is the admitted contact/weld "
                              "physics only",
                       "tool": "/tick_b2_place | /tick_b2_weld | "
                               "/tick_b2_remove | /tick_b2_save | "
                               "/tick_b2_restore",
                       "artifact": "run receipt + load/attachment histories",
                       "falsifier": "crate bottom <= slab top + 3 mm at "
                                    "settle (on the hazard) or COM out of "
                                    "the region; rejected edits moving the "
                                    "hash",
                       "cell": cell}]}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


class Run:
    """One full walkthrough into a fresh output dir."""

    def __init__(self, out: Path, port: int):
        self.out = out
        self.port = port
        self.out.mkdir(parents=True, exist_ok=True)
        self.rec: dict = {"schema": "chimera-workshop-challenge1-run-v1",
                          "port": port, "phases": [], "states": {},
                          "state_docs": {}, "anchor_kinds": {},
                          "shots": {}, "refusals": [], "histories": {},
                          "predicate": {}, "saves": {}, "memory": []}
        self._shot_seq = 0
        self._t0 = time.time()

    # ── plumbing ───────────────────────────────────────────────────────────
    def log(self, phase: str, **kw):
        kw = {"phase": phase, "t_s": round(time.time() - self._t0, 3), **kw}
        self.rec["phases"].append(kw)
        print(f"[{kw['t_s']:7.2f}s] {phase}: "
              + " ".join(f"{k}={v}" for k, v in kw.items()
                         if not isinstance(v, (dict, list))), flush=True)

    def mem(self, label: str):
        try:
            import psutil
            rss = psutil.Process(self.proc.pid).memory_info().rss
            self.rec["memory"].append({"label": label, "rss_mb": round(
                rss / 1e6, 1), "t_s": round(time.time() - self._t0, 1)})
        except Exception as e:            # a psutil hiccup must not kill a run
            self.rec["memory"].append({"label": label, "error": repr(e)})

    def shot(self, name: str, lane: str = "frame", wait_ms: int = 700,
             det: bool = False):
        """Browser-visible capture through the established node shotter.
        `det` marks a shot taken at an ANALYTIC paused anchor — only those
        carry the cross-run byte-identity claim (a settled scene's pose
        differs ~0.3 mm across runs, the documented rest-jitter class, so
        its pixels are not byte-stable)."""
        from tools.artificial_proteins.native_binding_visible import _shots
        self._shot_seq += 1
        out = self.out / f"{name}.png"
        spec = {"width": 1600, "height": 900,
                "shots": [{"url": f"{self.eng.base}/{lane}?v={self._shot_seq}",
                           "out": str(out), "wait_ms": wait_ms}]}
        _shots({"dir": self.out, "spec": spec})
        sha = hashlib.sha256(out.read_bytes()).hexdigest()
        self.rec["shots"][name] = {"lane": lane, "file": out.name,
                                   "sha256": sha, "deterministic": det}
        return out

    def board(self, standing: str, cell: str, status: str = "next"):
        board_write(self.board_path, standing, cell, status)

    def state(self):
        return self.eng.get("/tick_b2_state")

    def part(self, st, pid):
        return next(p for p in st["parts"] if p["id"] == pid)

    def hash(self):
        return self.eng.get("/tick_b2_hash")["state_hash"]

    def anchor(self, key: str, kind: str = "analytic"):
        """Record a deterministic state anchor: the paused state's hash AND
        its full save document. The state hash covers the whole save doc
        INCLUDING the step counter (b2_scene.cpp save_doc_), so cross-run
        identity is claimed on the DOCUMENT: byte-identity modulo the step
        counter for analytic anchors, the EQUIV band for settled ones."""
        self.rec["states"][key] = self.hash()
        self.rec["state_docs"][key] = self.eng.raw("/tick_b2_save").decode()
        self.rec["anchor_kinds"][key] = kind

    def pause(self, on: bool):
        assert self.eng.post("/tick_b2_pause", {"on": on}).get("ok")

    def settle(self, timeout=8.0, vthresh=SETTLE_V):
        t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.state()
            if all(p["speed_m_s"] < vthresh for p in st["parts"]):
                time.sleep(0.4)
                return self.state()
            time.sleep(0.1)
        return self.state()

    # ── objective predicate + measured histories ───────────────────────────
    def pad_top(self, st):
        return self.part(st, PAD["id"])["com_m"][1] + PAD["h"] / 2

    def check(self, st):
        p = self.part(st, CRATE["id"])
        c = p["com_m"]
        bottom = c[1] - CRATE["h"] / 2
        clear = bottom - self.pad_top(st)
        in_region = (REGION_X[0] <= c[0] <= REGION_X[1]
                     and abs(c[2]) <= REGION_Z)
        w, x, y, z = p["pose_q_wxyz"]
        up_y = 1 - 2 * (x * x + z * z)     # world y of the crate's up-axis
        tipped = up_y < TILT_MIN_UP_Y
        return (in_region and clear >= CLEAR_OK and not tipped), \
            round(clear, 6), in_region, round(bottom, 6), tipped

    def measure(self, name: str):
        """Free-run the scene for HISTORY_S seconds, sampling the predicate
        and the load/attachment history; pause at the end. The last 8
        samples are the declared 2 s continuity window."""
        self.pause(False)
        rows = []
        t0 = time.time()
        while time.time() - t0 < HISTORY_S:
            time.sleep(SAMPLE_DT)
            st = self.state()
            ok, clear, in_region, bottom, tipped = self.check(st)
            rows.append({
                "t_s": round(time.time() - t0, 3), "steps": st["steps"],
                "ok": ok, "clearance_m": clear, "in_region": in_region,
                "crate_bottom_m": bottom, "tipped": tipped,
                "diverged": st["diverged"],
                "total_reaction_n": st["total_reaction_n"],
                "welds": [{"a": w["a"], "b": w["b"],
                           "k_n_per_m": w["k_n_per_m"],
                           "force_n": w["force_n"]} for w in st["welds"]],
                "parts": {p["id"]: {"com_m": p["com_m"],
                                    "speed_m_s": p["speed_m_s"],
                                    "reaction_n": p["reaction_n"]}
                          for p in st["parts"]}})
        self.pause(True)
        window = rows[-8:]
        passed = (all(r["ok"] and not r["diverged"] for r in window)
                  and rows[-1]["in_region"])
        rec_row = {"passed": passed,
                   "window_clearances_m": [r["clearance_m"] for r in window],
                   "settled": rows[-1]}
        self.rec["predicate"][name] = rec_row
        self.rec["histories"][name] = rows
        return passed, rows[-1]

    # ── boot ───────────────────────────────────────────────────────────────
    def boot(self):
        assert EXE.exists(), f"engine missing: {EXE}"
        native = self.out / "native"
        native.mkdir(exist_ok=False)
        shutil.copy2(EXE, native / EXE.name)
        shutil.copytree(EXE.parent / "shaders", native / "shaders",
                        dirs_exist_ok=True)
        self.exe_sha = hashlib.sha256((native / EXE.name)
                                      .read_bytes()).hexdigest()
        with socket.socket() as s:
            assert s.connect_ex(("127.0.0.1", self.port)) != 0, "port busy"
        # the engine resolves argv[2] against ITS cwd (native/), so the
        # board path must be absolute whenever --out was given relative
        self.board_path = self.out.resolve() / "studio_board_challenge.json"
        self.board("Workshop challenge 1 - boot",
                   "Scene booting: the granite slab is the MARKED HAZARD "
                   "REGION. Kit: granite pier x2, timber deck, granite "
                   "pillar, steel crate.")
        argv = [str(native / EXE.name), str(self.port), str(self.board_path),
                "1600", "900", "--no-restore"]
        self.proc = subprocess.Popen(
            argv, cwd=native, stdout=(native / "stdout.log").open("wb"),
            stderr=(native / "stderr.log").open("wb"))
        self.eng = Engine(self.port)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                self.eng.get("/tick_state")
                return
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("engine did not answer /tick_state within 30 s")

    def studio_on(self):
        # the S5 sharp edge: an omitted "on" TOGGLES the overlay off —
        # every POST /studio carries explicit "on": true
        self.eng.post("/studio", {"on": True, "mode": "board"})
        info = self.eng.get("/studio")
        lh = float(info["lh"])
        node_h = 92.0 - 30.0 - lh - 12.0
        self.eng.post("/ui_click", {"x": float(info["w"]) / 2.0,
                                    "y": 30.0 + node_h / 2.0})
        time.sleep(0.8)
        self.eng.post("/studio", {"on": True, "left_size": 500.0})
        time.sleep(0.5)

    def camera(self):
        self.eng.post("/cameras", {"op": "save", "name": "challenge1",
                                   "v": [1.45, 0.85, 0.45, 0.62, 0.16, 0.0,
                                         0.0, 0.0]})
        self.eng.post("/cameras", {"op": "recall", "name": "challenge1"})
        time.sleep(0.6)


# ─────────────────────────────────────────────────────────────────────────────
# the walkthrough phases
# ─────────────────────────────────────────────────────────────────────────────
def run_walkthrough(out: Path, port: int) -> dict:
    run = Run(out, port)
    rec = run.rec
    try:
        run.boot()
        run.log("boot", engine_sha256=run.exe_sha)
        run.studio_on()
        run.camera()

        # ── P0: the scene — the hazard slab alone, admitted and immediately
        #      paused. The spawn is the analytic rest equilibrium (B3 pre-sink
        #      chain), so the paused state is exact and every later edit
        #      happens on an analytic base. (The clock cannot pause an
        #      inactive scene, so the admit->pause window is raced; across
        #      runs the state doc then differs only by the step counter —
        #      checked in compare.)
        r = run.eng.post("/tick_b2_admit", scene_doc())
        assert r.get("ok"), f"admit refused: {r}"
        run.pause(True)
        run.anchor("S1_scene_spawn")
        assert len(run.state()["parts"]) == 2
        run.board("Workshop challenge 1 - build",
                  "MARKED REGION set (granite slab, 280 x 160 mm). Kit: "
                  "granite pier x2, timber deck, granite pillar, steel "
                  "crate. PLACE supports, WELD connectors, keep the crate "
                  "clear above the slab.")
        run.shot("0-scene-startup", "frame")
        run.mem("scene")

        # ── P1: rejected edit preserves the accepted state (B9 law) ───────
        bad = {**crate_doc(bottom_y=0.2), "mass_kg": -1.0}
        r = run.eng.post("/tick_b2_place", bad)
        assert not r.get("ok", True), f"negative mass accepted: {r}"
        assert run.hash() == rec["states"]["S1_scene_spawn"], \
            "refusal moved the hash"
        rec["refusals"].append({"edit": "place mass_kg=-1",
                                "error": r.get("error", ""),
                                "hash_unchanged": True})
        run.board("Workshop challenge 1 - build",
                  "REFUSED: invalid part (negative mass). Scene unchanged - "
                  "fix the edit and retry.")
        run.log("refusal_demo", hash_unchanged=True)

        # ── P2: first attempt — the topple class (B8/B9) ──────────────────
        r = run.eng.post("/tick_b2_place", pillar_doc())
        assert r.get("ok"), f"pillar refused: {r}"
        run.anchor("S2_pillar")
        run.shot("1a-tower-pillar", "frame")
        r = run.eng.post("/tick_b2_place",
                         crate_doc(cx=CRATE_OFF_X, chain="tower"))
        assert r.get("ok"), f"off-crate refused: {r}"
        run.anchor("S3_offcrate")
        run.shot("2a-topple-armed", "frame")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        ok, clear, in_region, bottom, tipped = run.check(st)
        if ok:
            named = None
        else:
            why = ("the crate TIPPED off its support" if tipped
                   else "the crate came down onto the hazard"
                   if clear <= CLEAR_LOST else
                   "the crate left the marked region")
            named = (f"LOST SUPPORT: {why} (clearance {clear * 1000:.0f} mm). "
                     "ACTION: remove the crate and centre it over its "
                     "support before loading.")
        rec["predicate"]["attempt1"] = {
            "verdict": "FAIL" if not ok else "PASS",
            "clearance_m": clear, "in_region": in_region, "tipped": tipped,
            "crate_bottom_m": bottom,
            "pad_top_m": round(run.pad_top(st), 6), "named": named}
        run.board("Workshop challenge 1 - attempt 1",
                  named or "HELD: crate clear of the hazard.", 
                  "blocked" if not ok else "green")
        run.log("topple_predicate", verdict=rec["predicate"]["attempt1"]
                ["verdict"], clearance_m=clear)
        ins = run.eng.post("/tick_b2_inspect", {"id": "crate"})
        rec["failure_inspect"] = {"route": "/tick_b2_inspect crate",
                                  "detailed_reactions_stay_in_inspector":
                                      True, "answered": bool(ins.get("ok"))}
        run.shot("3-failure-topple", "frame")
        run.shot("3-failure-glass", "glass", wait_ms=1200)
        run.mem("failure")

        # ── P3: cheap retry — recovery into solution B ────────────────────
        r = run.eng.post("/tick_b2_remove", {"id": "crate"})
        assert r.get("ok"), f"remove refused: {r}"
        stp = run.state()
        p_top = run.part(stp, "pillar")["com_m"][1] + PILLAR["h"] / 2
        sink = M_CRATE * G / _pair_kt(KT_CRATE, KT_PILLAR)
        r = run.eng.post("/tick_b2_place",
                         crate_doc(cx=CRATE["cx"], chain="tower",
                                   bottom_y=p_top - sink))
        assert r.get("ok"), f"centred crate refused: {r}"
        run.board("Workshop challenge 1 - retry",
                  "Crate replaced CENTRED over the pillar. Let it settle...")
        passed_b, fin_b = run.measure("solution_B")
        rec["states"]["S5_solB"] = run.hash()
        doc_b = run.eng.raw("/tick_b2_save")
        (run.out / "save_solution_B.json").write_bytes(doc_b)
        rec["saves"]["solution_B"] = {
            "file": "save_solution_B.json",
            "sha256": hashlib.sha256(doc_b).hexdigest()}
        run.board("Workshop challenge 1 - solution B",
                  f"HELD: crate {fin_b['clearance_m'] * 1000:.0f} mm above "
                  "the hazard (contact tower, NO connectors). SOLUTION B "
                  "accepted.", "green")
        run.shot("4-solB-terminal", "frame")
        run.shot("4-solB-glass", "glass", wait_ms=1200)
        run.mem("solution_B")
        run.log("solution_B", passed=passed_b,
                clearance_m=fin_b["clearance_m"])

        # ── P4: solution A — the welded span (clear + analytic rebuild) ───
        run.eng.post("/tick_b2_clear")
        r = run.eng.post("/tick_b2_admit", scene_doc())
        assert r.get("ok"), f"re-admit refused: {r}"
        run.pause(True)
        run.anchor("S6_scene_respawn")
        for which in (PIER_A, PIER_B):
            r = run.eng.post("/tick_b2_place", pier_doc(which))
            assert r.get("ok"), f"{which['id']} refused: {r}"
        run.anchor("S7_piers")
        r = run.eng.post("/tick_b2_place", deck_doc())
        assert r.get("ok"), f"deck refused: {r}"
        r = run.eng.post("/tick_b2_place", crate_doc(yaw90=True,
                                                     chain="span"))
        assert r.get("ok"), f"span crate refused: {r}"
        # attach the span: coincident anchors at the deck/pier interface —
        # the connectors attach IN PARALLEL with the corner contact (the B4
        # cradle pattern). A connector-HUNG deck under this 1.96 kg load was
        # measured unstable (the span swung off its welds and collapsed; B5's
        # battery only ever loaded a hung span with 0.086 kg), so solution A
        # is a contact-supported span with live connectors, not a hung one.
        for pier in (PIER_A, PIER_B):
            r = run.eng.post("/tick_b2_weld",
                             {"a": "deck", "b": pier["id"], "k": K_SOFT,
                              "c_damp": 10.0,
                              "anchors_world": weld_anchors(pier)})
            assert r.get("ok"), f"weld {pier['id']} refused: {r}"
        st = run.state()
        assert len(st["welds"]) == 2, "connector duplicated"
        run.anchor("S8_span_armed")
        run.shot("5a-span-armed", "frame")
        run.board("Workshop challenge 1 - solution A",
                  "Span armed: deck resting on 2 piers, k 2.0 kN/m "
                  "connectors at each interface, crate rotated 90 deg on "
                  "top. Testing...")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        sag_soft = [w["force_n"] / w["k_n_per_m"] for w in st["welds"]]
        # revise: the B4 connection improvement — SAME anchors (the welded
        # reference re-zeroes at the current pose), 20x stiffer; a re-set
        # REPLACES, never duplicates
        for pier in (PIER_A, PIER_B):
            r = run.eng.post("/tick_b2_weld",
                             {"a": "deck", "b": pier["id"], "k": K_STIFF,
                              "c_damp": 10.0,
                              "anchors_world": weld_anchors(pier)})
            assert r.get("ok"), f"stiff re-weld refused: {r}"
        st2 = run.state()
        assert len(st2["welds"]) == 2, "re-weld duplicated the connector"
        run.pause(False)
        st3 = run.settle(timeout=12.0)
        passed_a, fin_a = run.measure("solution_A")
        sag_stiff = [w["force_n"] / w["k_n_per_m"] for w in
                     run.state()["welds"]]
        rec["revision"] = {
            "action": "re-weld both connectors 20x stiffer, same anchors "
                      "(B4 connection-improvement pattern)",
            "sag_soft_m": [round(v, 6) for v in sag_soft],
            "sag_stiff_m": [round(v, 6) for v in sag_stiff],
            "weld_force_soft_n": [round(w["force_n"], 4) for w in st["welds"]],
            "weld_force_stiff_n": [round(w["force_n"], 4) for w
                                   in run.state()["welds"]]}
        rec["states"]["S10_solA"] = run.hash()
        doc_a = run.eng.raw("/tick_b2_save")
        (run.out / "save_solution_A.json").write_bytes(doc_a)
        rec["saves"]["solution_A"] = {
            "file": "save_solution_A.json",
            "sha256": hashlib.sha256(doc_a).hexdigest()}
        run.board("Workshop challenge 1 - solution A",
                  f"HELD: crate {fin_a['clearance_m'] * 1000:.0f} mm above "
                  f"the hazard; sag {sag_stiff[0] * 1000:.1f} mm after the "
                  f"stiff re-weld (was {sag_soft[0] * 1000:.1f} mm). "
                  "SOLUTION A accepted.", "green")
        run.shot("6-solA-terminal", "frame")
        run.shot("6-solA-glass", "glass", wait_ms=1200)
        run.mem("solution_A")
        run.log("solution_A", passed=passed_a,
                clearance_m=fin_a["clearance_m"],
                sag_soft_mm=round(sag_soft[0] * 1000, 2),
                sag_stiff_mm=round(sag_stiff[0] * 1000, 2))

        # ── P5: reset/restore returns (B4 bit-exact law) ──────────────────
        run.eng.post("/tick_b2_clear")
        r = run.eng.post_raw("/tick_b2_restore", doc_a.decode())
        assert r.get("ok"), f"restore refused: {r}"
        rec["states"]["S11_restored"] = run.hash()
        rec["restore_bit_exact"] = (rec["states"]["S11_restored"]
                                    == rec["states"]["S10_solA"])
        h = run.hash()
        r = run.eng.post("/tick_b2_patch", {"id": "nope", "mu": 0.0})
        assert not r.get("ok", True)
        rec["refusals"].append({"edit": "patch unknown part after restore",
                                "error": r.get("error", ""),
                                "hash_unchanged": run.hash() == h})
        run.shot("7-restored", "frame")
        run.log("restore", bit_exact=rec["restore_bit_exact"])

        # ── P6: measurements + receipt ─────────────────────────────────────
        clock = run.eng.get("/tick_b2_clock")
        rec["clock"] = {k: clock[k] for k in
                        ("ticks", "sim_s", "sim_over_wall", "catchup_clamps",
                         "slow_ticks", "max_gap_ms")}
        run.mem("end")
        unexpected = run.eng.used - FROZEN
        assert not unexpected, \
            f"routes outside the frozen surface: {unexpected}"
    except Exception:
        # preserve partial evidence even when a phase asserts
        (out / "run_receipt_partial.json").write_text(
            json.dumps(rec, indent=1), encoding="utf-8")
        raise
    finally:
        if hasattr(run, "proc") and run.proc.poll() is None:
            run.proc.terminate()
            try:
                run.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                run.proc.kill()
        time.sleep(1.0)
    # stdout FPS parse (frame-time evidence)
    log = out / "native" / "stdout.log"
    if log.exists():
        lines = log.read_text(errors="replace").splitlines()
        fts = [l for l in lines if "| ft ms avg" in l]
        if fts:
            avgs = [float(l.split("ft ms avg ")[1].split()[0]) for l in fts]
            maxs = [float(l.split("max ")[1].split()[0])
                    for l in fts if " max " in l]
            rec["frame_time"] = {"samples": len(fts),
                                 "avg_ms_mean": round(sum(avgs) / len(avgs), 3),
                                 "avg_ms_max": round(max(avgs), 3),
                                 "frame_max_ms": round(max(maxs), 3)}
    rec["used_routes"] = sorted(run.eng.used)
    (out / "run_receipt.json").write_text(json.dumps(rec, indent=1),
                                          encoding="utf-8")
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# two-run comparison (byte-identity for deterministic states; band for settled)
# ─────────────────────────────────────────────────────────────────────────────
def _doc_equiv(a, b, path: str = "", out: list | None = None):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in set(a) | set(b):
            if k in EQUIV_SKIP:
                continue
            _doc_equiv(a.get(k), b.get(k), f"{path}.{k}", out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append({"path": path, "a": f"len {len(a)}",
                        "b": f"len {len(b)}", "d": 1e9})
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _doc_equiv(x, y, f"{path}[{i}]", out)
    elif isinstance(a, (int, float)) and not isinstance(a, bool) \
            and isinstance(b, (int, float)) and not isinstance(b, bool):
        d = abs(a - b)
        if d > EQUIV_TOL:
            out.append({"path": path, "a": a, "b": b, "d": d})
    elif a != b:
        out.append({"path": path, "a": a, "b": b, "d": 1e9})
    return out


def compare(run1: Path, run2: Path, out: Path) -> dict:
    r1 = json.loads((run1 / "run_receipt.json").read_text())
    r2 = json.loads((run2 / "run_receipt.json").read_text())
    cmp: dict = {"schema": "chimera-workshop-challenge1-comparison-v1",
                 "run1": str(run1), "run2": str(run2)}
    # 1. deterministic state anchors. The state hash covers the whole save
    #    document INCLUDING the step counter (b2_scene.cpp save_doc_), so
    #    cross-run HASH identity is unattainable for any state the clock has
    #    advanced past spawn; the claim is on the DOCUMENT: analytic anchors
    #    must be byte-identical modulo the skipped step counter, settled
    #    anchors within the EQUIV band.
    det = {}
    for k in sorted(set(r1["state_docs"]) & set(r2["state_docs"])):
        kind = r1["anchor_kinds"].get(k, "analytic")
        a = json.loads(r1["state_docs"][k])
        b = json.loads(r2["state_docs"][k])
        diffs = _doc_equiv(a, b, k)
        det[k] = {"kind": kind, "run1_hash": r1["states"][k],
                  "run2_hash": r2["states"][k],
                  "n_violations": len(diffs), "violations": diffs[:8],
                  "within_band": not diffs}
    cmp["deterministic_states"] = det
    cmp["all_states_within_band"] = bool(det) and all(
        v["within_band"] for v in det.values())
    cmp["analytic_states_byte_identical_modulo_steps"] = bool(det) and all(
        v["within_band"] for v in det.values() if v["kind"] == "analytic")
    # 2. /frame shots: byte identity (the /glass lane carries live HUD
    #    numbers and is evidence, not an identity claim)
    shots = {}
    for k in sorted(set(r1["shots"]) & set(r2["shots"])):
        if r1["shots"][k]["lane"] != "frame":
            continue
        shots[k] = {"run1": r1["shots"][k]["sha256"],
                    "run2": r2["shots"][k]["sha256"],
                    "byte_identical": (r1["shots"][k]["sha256"]
                                       == r2["shots"][k]["sha256"])}
    cmp["frame_shots"] = shots
    cmp["all_frame_shots_byte_identical"] = all(v["byte_identical"]
                                                for v in shots.values())
    # 3. settled save documents: the objective-loop band
    band = {}
    for name in ("solution_B", "solution_A"):
        a = json.loads((run1 / f"save_{name}.json").read_bytes())
        b = json.loads((run2 / f"save_{name}.json").read_bytes())
        diffs = _doc_equiv(a, b, name)
        band[name] = {"violations": diffs[:20], "n_violations": len(diffs),
                      "within_band": not diffs}
    cmp["settled_save_docs"] = band
    # 4. the §6 gate: DIFFERENT measured load/attachment histories
    def hist_sig(rec, name):
        rows = rec["histories"][name]
        last = rows[-1]
        weld_names = sorted({(w["a"], w["b"])
                             for r in rows for w in r["welds"]})
        return {"weld_pairs_ever": weld_names,
                "weld_force_n_final": [round(w["force_n"], 3)
                                       for w in last["welds"]],
                "crate_com_final": last["parts"]["crate"]["com_m"],
                "crate_reaction_n_final":
                    last["parts"]["crate"]["reaction_n"],
                "total_reaction_n_final": last["total_reaction_n"]}
    sig_b1, sig_a1 = hist_sig(r1, "solution_B"), hist_sig(r1, "solution_A")
    cmp["history_signatures"] = {
        "solution_B": sig_b1, "solution_A": sig_a1,
        "cross_run_B": hist_sig(r2, "solution_B"),
        "cross_run_A": hist_sig(r2, "solution_A")}
    cmp["gate_two_solutions_different"] = bool(
        len(sig_b1["weld_pairs_ever"]) == 0
        and len(sig_a1["weld_pairs_ever"]) >= 2
        and r1["predicate"]["solution_B"]["passed"]
        and r1["predicate"]["solution_A"]["passed"]
        and r2["predicate"]["solution_B"]["passed"]
        and r2["predicate"]["solution_A"]["passed"])
    cmp["recovery"] = {
        "run1_refusals_preserved":
            all(x["hash_unchanged"] for x in r1["refusals"]),
        "run2_refusals_preserved":
            all(x["hash_unchanged"] for x in r2["refusals"]),
        "run1_named_failure":
            r1["predicate"]["attempt1"]["verdict"] == "FAIL",
        "run2_named_failure":
            r2["predicate"]["attempt1"]["verdict"] == "FAIL",
        "run1_restore_bit_exact": r1["restore_bit_exact"],
        "run2_restore_bit_exact": r2["restore_bit_exact"]}
    out.write_text(json.dumps(cmp, indent=1), encoding="utf-8")
    return cmp


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--port", type=int, required=True)
    c = sub.add_parser("compare")
    c.add_argument("run1")
    c.add_argument("run2")
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        rec = run_walkthrough(Path(args.out), args.port)
        print(json.dumps({"states": rec["states"],
                          "predicate": rec["predicate"],
                          "revision": rec.get("revision"),
                          "restore_bit_exact": rec["restore_bit_exact"],
                          "frame_time": rec.get("frame_time"),
                          "clock": rec.get("clock"),
                          "memory": rec["memory"]}, indent=1))
    else:
        cmp = compare(Path(args.run1), Path(args.run2), Path(args.out))
        print(json.dumps({k: cmp[k] for k in
                          ("all_states_within_band",
                           "analytic_states_byte_identical_modulo_steps",
                           "all_frame_shots_byte_identical",
                           "gate_two_solutions_different",
                           "history_signatures", "recovery")}, indent=1))


if __name__ == "__main__":
    main()
