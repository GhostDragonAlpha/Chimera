"""Workshop challenge 2 — saved-recipe transfer + constraint variation.

GAME_PLAN_ACTION_RPG.md §5.1: challenge 1 (commit 39ec3d9c) proved build ->
test -> named failure -> recovery -> save -> restore. This challenge proves
the workshop promise "inventions can be REUSED": the player's SAVED solution
loads into a FRESH world and still works, and when the world changes under
it, the game names what changed and the player's small edit recovers it.

Walkthrough (two engines, one receipt):
  ENGINE 1 (build + save)  solution B rebuilt exactly as challenge 1 built
                           it (granite pillar on the hazard slab, steel
                           crate centred on top, NO connectors); settled;
                           predicate PASS; /tick_b2_save -> save_B.json;
                           engine shut down cleanly by handle.
  ENGINE 2 (fresh world)   a SECOND fresh engine process, no build step:
                           /tick_b2_restore(save_B.json) -- the engine's
                           restore validates and ACTIVATES a scene
                           (b2_scene.cpp: active_ = true), so a fresh
                           world takes a saved recipe directly. Settle;
                           the SAME predicate must PASS; the restored
                           hash must equal engine 1's saved hash.
  VARIATION                the world changes under the recipe: the crate
                           load is DOUBLED via /tick_b2_patch mass_kg
                           (the engine's patch law rescales mass, inertia
                           AND the ground-rung k/c by the same ratio, so
                           rest sink is preserved -- a load change is a
                           legal, non-geometric world edit). Settle; the
                           predicate FAILS (smoke-measured twice, -8.9 mm:
                           the 2x step load punched the crate down through
                           the pillar, the engine's over-compression
                           tunnel class); the board names it with an
                           ACTION line.
  RECOVERY EDIT            the brief's "add the second pillar beside the
                           first": two UNROTATED pillars straddle under
                           the crate, so the doubled load rides two
                           supports (each back in the proven 1x regime);
                           the crate re-places at the POST-patch pair
                           equilibrium while paused and the mass patch
                           lands before the unpause -- no step load.
                           Predicate PASS ~76.5 mm (original margin
                           restored under the doubled load).
  PROBES                   terminal save; /tick_b2_restore of the same
                           document must be hash-identical (B4 bit-exact
                           law); one refused-edit hash probe.

ENGINE FINDING (probe matrix, .tmp/wc2_probe): a ROTATED part acting as
the contact SURFACE does not hold a vertex-resting load in this build --
the crate free-fell (exact 0.5*g*t^2, zero pair force) through a 90-deg
yawed support at BOTH 2.4 mm and 6.7 mm spawn penetration, while the
GEOMETRICALLY IDENTICAL unrotated support held at both depths (yawed
square-pillar control included). Challenge 1 never hit this: every
support there was unrotated; its rotated parts were only vertex owners.
All supports must be placed unrotated; flagged as a suspected engine
contact bug (rotated face owner) for upstream.

Determinism discipline inherited from challenge 1: analytic spawns only on
an unadvanced base; every deterministic anchor saves its full state
document; cross-run claims on the DOCUMENT (analytic anchors byte-identical
modulo the step counter, settled states in the EQUIV band); glass shots
carried the board and were byte-identical in challenge 1 -- compared, not
assumed.

Predeclared physics prediction (B3 chain law, the challenge-1 math that
reproduces its measured 79.882 mm clearance): clearance above the pad top
is the support height minus the two pair penetrations (the pad's own ground
descent carries crate and support together and cancels):
    clear = h_sup - 2*RS*(m_sup+m_crate)/(m_sup+M_PAD)
              - 2*RS*m_crate/(m_sup+m_crate)
  solution B rebuilt:        79.88 mm  (challenge-1 measured: 79.882 --
                             the smoke run reproduced it exactly)
  doubled crate load:        72.05 mm QUASI-STATICALLY -- but the smoke
                             run measured a genuine FAILURE (-8.9 mm): the
                             2x step load, applied to the settled tower,
                             drove the crate through the pillar (the
                             engine's documented over-compression pop/
                             tunnel class, challenge-1 calibration
                             lesson). Upright, in-region, undiverged,
                             settled: the board names it LOST SUPPORT with
                             an ACTION line. Quasi-static failure would
                             need ~30 kg (~15x); the DYNAMIC step-load
                             failure needs only 2x.
  two-pillar straddle:       76.5 mm -- the doubled load rides two
                             supports, each back in the proven 1x regime;
                             the crate spawns at the POST-patch pair
                             equilibrium (10.05 mm) with the mass patch
                             applied while paused, so the unpause starts
                             balanced -- no step load.

Run:   python tools/construction_packet/workshop_challenge2.py run --out DIR --port 8810
       python tools/construction_packet/workshop_challenge2.py compare RUN1 RUN2 --out comparison.json
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).

Reuse: IMPORTS the published challenge-1 driver (workshop_challenge1.py,
commit 39ec3d9c -- not edited): its Run machinery, constants, document
builders and comparison band. Copies below are attributed inline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE), str(HERE.parent), str(HERE.parent.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import b2_scene_gen                     # (via challenge 1's path setup)
import workshop_challenge1 as wc1       # published evidence -- imported only

REPO = HERE.parent.parent
EXE = wc1.EXE
G, RS = wc1.G, wc1.RS
FROZEN = wc1.FROZEN

# kit pieces (challenge-1 constants, reused verbatim)
PAD, PILLAR, PIER, CRATE = wc1.PAD, wc1.PILLAR, wc1.PIER, wc1.CRATE
M_CRATE, M_PILLAR = wc1.M_CRATE, wc1.M_PILLAR
KT_PAD, KT_PILLAR, KT_CRATE = wc1.KT_PAD, wc1.KT_PILLAR, wc1.KT_CRATE
_pair_kt = wc1._pair_kt                 # B3 pair k_total law
scene_doc, pillar_doc, crate_doc, pad_doc = (wc1.scene_doc, wc1.pillar_doc,
                                             wc1.crate_doc, wc1.pad_doc)
EQUIV_TOL, EQUIV_SKIP, SETTLE_V = wc1.EQUIV_TOL, wc1.EQUIV_SKIP, wc1.SETTLE_V

LOAD_FACTOR = 2.0                       # the world change: crate load x2
M_CRATE_2X = LOAD_FACTOR * M_CRATE      # the world's doubled crate
PILLAR_L_CX = 0.555                     # the two recovery pillars: each
PILLAR_R_CX = 0.685                     # 120 mm wide, footprints
                                        # 0.495..0.615 / 0.625..0.745 inside
                                        # the pad (0.48..0.76), z +/-0.06
                                        # inside +/-0.08, 10 mm apart; the
                                        # crate's corners land strictly
                                        # inside each top face
# post-patch pair equilibrium of the crate on a pillar top (B3 pair law):
SINK_2X = 2 * RS * M_CRATE_2X / (M_CRATE_2X + M_PILLAR)


# ── predeclared predictions (B3 chain law; see module docstring) ────────────
def predict_clearance(h_sup: float, m_sup: float, m_crate: float) -> float:
    d2 = 2 * RS * (m_sup + m_crate) / (m_sup + wc1.M_PAD)
    d3 = 2 * RS * m_crate / (m_sup + m_crate)
    return h_sup - d2 - d3


def predict_straddle_mm() -> float:
    """Two pillars share the doubled crate: each pillar/pad pair carries
    pillar + crate-half, and the crate/pillar pair penetration is the
    post-patch pair law (SINK_2X)."""
    d2 = 2 * RS * (M_PILLAR + M_CRATE_2X / 2) / (M_PILLAR + wc1.M_PAD)
    return (PILLAR["h"] - d2 - SINK_2X) * 1000


def failure_threshold_mass_kg(h_sup: float, m_sup: float,
                              lo: float = 1.0, hi: float = 400.0) -> float:
    """Crate mass at which the tower's clearance hits the 4 mm HELD band
    (bisection on the chain law) -- the receipt's overload headroom."""
    f = lambda m: predict_clearance(h_sup, m_sup, m) - wc1.CLEAR_OK
    a, b = lo, hi
    for _ in range(80):
        mid = (a + b) / 2
        if f(mid) > 0:
            a = mid
        else:
            b = mid
    return (a + b) / 2


PRED_BUILD_MM = predict_clearance(PILLAR["h"], M_PILLAR, M_CRATE) * 1000
PRED_DOUBLE_MM = predict_clearance(PILLAR["h"], M_PILLAR,
                                   LOAD_FACTOR * M_CRATE) * 1000
PRED_STRADDLE_MM = predict_straddle_mm()
PRED_FAIL_MASS = failure_threshold_mass_kg(PILLAR["h"], M_PILLAR)


# ─────────────────────────────────────────────────────────────────────────────
# the recovery supports (UNROTATED -- see the engine finding in the header)
# ─────────────────────────────────────────────────────────────────────────────
def pillar_at_doc(pid: str, cx: float, spawn_bottom: float) -> dict:
    """The kit pillar at another x, spawned with its bottom at
    `spawn_bottom` (the caller's PAIR-sink spawn on the settled pad --
    challenge-1 recovery pattern). Unrotated: a rotated face-owner support
    drops vertex-resting loads in this build (probe matrix D/E)."""
    dx, h, dz = PILLAR["dx"], PILLAR["h"], PILLAR["dz"]
    return b2_scene_gen.box_document(
        pid, cx - dx / 2, cx + dx / 2, spawn_bottom, spawn_bottom + h,
        -dz / 2, dz / 2, PILLAR["rho"], PILLAR["mu"])


# ─────────────────────────────────────────────────────────────────────────────
# studio board (challenge-1 writer pattern, challenge-2 chip)
# ─────────────────────────────────────────────────────────────────────────────
def board2_write(path: Path, standing: str, cell: str, status: str) -> None:
    doc = {"standing": standing, "updated": "workshop challenge 2",
           "stages": [{"id": "WS4",
                       "name": "Salvage recipe, reused",
                       "status": status,
                       "law": "objective law: the crate's COM stays inside "
                              "the marked region with its bottom >= 4 mm "
                              "above the slab top for the whole window; the "
                              "load path is the admitted contact physics "
                              "only",
                       "tool": "/tick_b2_place | /tick_b2_remove | "
                               "/tick_b2_patch | /tick_b2_save | "
                               "/tick_b2_restore",
                       "artifact": "run receipt + transfer/variation "
                                   "margins",
                       "falsifier": "crate bottom <= slab top + 3 mm at "
                                    "settle (on the hazard) or COM out of "
                                    "the region; the transferred recipe "
                                    "fails its predicate in a fresh "
                                    "world; refused edits moving the hash",
                       "cell": cell}]}
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    os.replace(tmp, path)


class Run2(wc1.Run):
    """Challenge-1 Run machinery (boot/shots/settle/predicate/histories are
    inherited unmodified); board text and the boot chip are challenge 2's,
    and boot() takes a per-engine subdir so ONE receipt spans both engines."""

    def __init__(self, out: Path, port: int):
        super().__init__(out, port)
        self.rec["schema"] = "chimera-workshop-challenge2-run-v1"
        self.rec["transfer"] = {}
        self.rec["variation"] = {}
        self.rec["recovery"] = {}

    def board(self, standing: str, cell: str, status: str = "next"):
        board2_write(self.board_path, standing, cell, status)

    def boot(self, sub: str = "native1"):
        # copy of wc1.Run.boot (attribution: workshop_challenge1.py:499) --
        # the only changes are the per-engine native/ subdir and the chip
        # text; the argv shape (exe, port, ABSOLUTE board path, cwd=native/)
        # and the port-free assert are challenge 1's.
        assert EXE.exists(), f"engine missing: {EXE}"
        native = self.out / sub
        native.mkdir(exist_ok=False)
        import shutil
        shutil.copy2(EXE, native / EXE.name)
        shutil.copytree(EXE.parent / "shaders", native / "shaders",
                        dirs_exist_ok=True)
        self.exe_sha = hashlib.sha256((native / EXE.name)
                                      .read_bytes()).hexdigest()
        import socket
        with socket.socket() as s:
            assert s.connect_ex(("127.0.0.1", self.port)) != 0, "port busy"
        # the engine resolves argv[2] against ITS cwd (native/), so the
        # board path must be absolute whenever --out was given relative
        self.board_path = self.out.resolve() / "studio_board_challenge.json"
        self.board("Workshop challenge 2 - boot",
                   "Fresh world. The saved salvage recipe will be RESTORED "
                   "here and tested under a changed constraint. Kit: "
                   "granite pier x2, timber deck, granite pillar, steel "
                   "crate.")
        argv = [str(native / EXE.name), str(self.port), str(self.board_path),
                "1600", "900", "--no-restore"]
        self.proc = subprocess.Popen(
            argv, cwd=native, stdout=(native / "stdout.log").open("wb"),
            stderr=(native / "stderr.log").open("wb"))
        self.eng = wc1.Engine(self.port)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                self.eng.get("/tick_state")
                return
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("engine did not answer /tick_state within 30 s")

    def camera(self):
        self.eng.post("/cameras", {"op": "save", "name": "challenge2",
                                   "v": [1.45, 0.85, 0.45, 0.62, 0.16, 0.0,
                                         0.0, 0.0]})
        self.eng.post("/cameras", {"op": "recall", "name": "challenge2"})
        time.sleep(0.6)

    def shutdown(self):
        """Clean shutdown by handle (challenge-1 finally-block pattern,
        used mid-walkthrough between engine 1 and engine 2)."""
        if hasattr(self, "proc") and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        time.sleep(1.0)


# ─────────────────────────────────────────────────────────────────────────────
# the walkthrough
# ─────────────────────────────────────────────────────────────────────────────
def run_walkthrough(out: Path, port1: int, port2: int) -> dict:
    run = Run2(out, port1)
    rec = run.rec
    try:
        # ══ ENGINE 1: build solution B exactly as challenge 1 does ═══════
        run.boot("native1")
        run.log("boot_engine1", engine_sha256=run.exe_sha)
        run.studio_on()
        run.camera()

        r = run.eng.post("/tick_b2_admit", scene_doc())
        assert r.get("ok"), f"admit refused: {r}"
        run.pause(True)
        run.anchor("S1_scene_spawn")            # analytic
        assert len(run.state()["parts"]) == 2
        run.board("Workshop challenge 2 - build",
                  "MARKED REGION set (granite slab). Rebuilding SOLUTION B "
                  "(contact tower) so it can be SAVED and reused.")
        run.shot("0-scene-startup", "frame")
        run.mem("engine1_scene")

        r = run.eng.post("/tick_b2_place", pillar_doc())
        assert r.get("ok"), f"pillar refused: {r}"
        run.anchor("S2_pillar")                 # analytic
        run.shot("1-tower-pillar", "frame")
        r = run.eng.post("/tick_b2_place", crate_doc(chain="tower"))
        assert r.get("ok"), f"crate refused: {r}"
        run.anchor("S3_solB_armed")             # analytic
        run.shot("2-solB-armed", "frame")
        run.board("Workshop challenge 2 - build",
                  "Contact tower armed: granite pillar on the slab, crate "
                  "centred, NO connectors. Testing...")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        ok, clear, in_region, bottom, tipped = run.check(st)
        run.board("Workshop challenge 2 - solution B",
                  f"HELD: crate {clear * 1000:.1f} mm above the hazard "
                  f"(predicted {PRED_BUILD_MM:.1f} mm); total reaction "
                  f"{st['total_reaction_n']:.1f} N. SAVING the recipe.",
                  "green")
        passed_b, fin_b = run.measure("recipe_build")
        assert passed_b, "solution B failed to hold in engine 1"
        run.anchor("S4_solB_settled", kind="settled")
        doc_b = run.eng.raw("/tick_b2_save")
        (out / "save_B.json").write_bytes(doc_b)
        rec["saves"]["solution_B"] = {
            "file": "save_B.json",
            "sha256": hashlib.sha256(doc_b).hexdigest()}
        run.shot("3-solB-engine1-glass", "glass", wait_ms=1200)
        run.mem("engine1_solutionB")
        run.log("engine1_solutionB", passed=passed_b,
                clearance_mm=round(fin_b["clearance_m"] * 1000, 3),
                predicted_mm=round(PRED_BUILD_MM, 3),
                total_reaction_n=st["total_reaction_n"])

        # ══ clean shutdown of engine 1 (by handle) ═══════════════════════
        run.shutdown()
        run.log("engine1_shutdown", clean=True)

        # ══ ENGINE 2: a FRESH world, restore the saved recipe ════════════
        run.port = port2
        run.boot("native2")
        run.log("boot_engine2", engine_sha256=run.exe_sha,
                fresh_world=True, note="no build step; scene never admitted")
        run.studio_on()
        run.camera()
        r = run.eng.post_raw("/tick_b2_restore",
                             (out / "save_B.json").read_bytes().decode())
        assert r.get("ok"), f"restore refused: {r}"
        run.anchor("S5_restored", kind="settled")
        restored_exact = (run.hash() == rec["states"]["S4_solB_settled"])
        rec["transfer"] = {
            "save_file": "save_B.json",
            "save_sha256": rec["saves"]["solution_B"]["sha256"],
            "engine1_port": port1, "engine2_port": port2,
            "restored_hash_equals_engine1_saved": restored_exact,
            "parts": len(run.state()["parts"])}
        run.board("Workshop challenge 2 - transfer",
                  "TRANSFER: the SAVED recipe loaded into a FRESH world "
                  "(no rebuild). Verdict pending: testing...")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        passed_t, fin_t = run.measure("transfer")
        assert passed_t, "the transferred recipe failed its own predicate"
        rec["transfer"]["verdict"] = "PASS"
        rec["transfer"]["clearance_m"] = fin_t["clearance_m"]
        rec["transfer"]["total_reaction_n"] = run.state()["total_reaction_n"]
        run.board("Workshop challenge 2 - transfer",
                  f"TRANSFER VERDICT: the saved recipe works in a fresh "
                  f"world UNCHANGED - crate {fin_t['clearance_m'] * 1000:.1f} "
                  f"mm above the hazard. The invention is REUSABLE.",
                  "green")
        run.shot("4-transfer-glass", "glass", wait_ms=1200)
        run.mem("transfer")
        run.log("transfer", passed=passed_t, restored_exact=restored_exact,
                clearance_mm=round(fin_t["clearance_m"] * 1000, 3))

        # ══ VARIATION: the world changes under the recipe ════════════════
        m_before = M_CRATE
        m_after = LOAD_FACTOR * M_CRATE
        r = run.eng.post("/tick_b2_patch",
                         {"id": "crate", "mass_kg": m_after})
        assert r.get("ok"), f"patch refused: {r}"
        ins = run.eng.post("/tick_b2_inspect", {"id": "crate"})
        rec["variation"] = {
            "action": f"/tick_b2_patch crate mass_kg {m_before:.4f} -> "
                      f"{m_after:.4f} (the client doubled the load)",
            "mass_before_kg": m_before, "mass_after_kg": m_after,
            "margin_before_mm": round(fin_t["clearance_m"] * 1000, 3),
            "predicted_margin_mm": round(PRED_DOUBLE_MM, 3),
            "overload_headroom_mass_kg": round(PRED_FAIL_MASS, 1),
            "prediction_note": "the patch law rescales k/c with mass (rest "
                               "sink preserved), so the QUASI-STATIC "
                               "prediction was a margin shrink to "
                               "72.0 mm; the measured outcome was the "
                               "engine's over-compression punch-through "
                               "(tunnel) class at the 2x step load",
            "inspect_answered": bool(ins.get("ok"))}
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        ok_v, clear_v, in_region_v, bottom_v, tipped_v = run.check(st)
        passed_v, fin_v = run.measure("variation_double_load")
        rec["variation"]["predicate"] = rec["predicate"][
            "variation_double_load"]
        rec["variation"]["margin_after_mm"] = round(
            fin_v["clearance_m"] * 1000, 3)
        rec["variation"]["verdict"] = ("FAIL" if not passed_v else "PASS")
        if not passed_v:
            verdict = (f"LOST SUPPORT: the doubled load punched the crate "
                       f"down through its support onto the hazard "
                       f"(clearance {fin_v['clearance_m'] * 1000:.0f} mm). "
                       f"ACTION: add the second pillar beside the first "
                       f"and reload the crate across both.")
        else:
            verdict = (f"OVERLOADED: the doubled load compressed the tower; "
                       f"clearance {fin_t['clearance_m'] * 1000:.0f} -> "
                       f"{fin_v['clearance_m'] * 1000:.0f} mm (still above "
                       f"the 4 mm band; headroom ~{PRED_FAIL_MASS:.0f} kg). "
                       f"ACTION: add the second pillar beside the first to "
                       f"restore the margin.")
        rec["variation"]["board_verdict"] = verdict
        run.board("Workshop challenge 2 - variation", verdict,
                  "blocked" if not passed_v else "next")
        run.shot("5-variation-glass", "glass", wait_ms=1200)
        run.mem("variation")
        run.log("variation", passed=passed_v,
                margin_before_mm=rec["variation"]["margin_before_mm"],
                margin_after_mm=rec["variation"]["margin_after_mm"],
                predicted_mm=round(PRED_DOUBLE_MM, 3))

        # ══ RECOVERY EDIT: the second pillar beside the first ════════════
        r = run.eng.post("/tick_b2_remove", {"id": "crate"})
        assert r.get("ok"), f"remove crate refused: {r}"
        r = run.eng.post("/tick_b2_remove", {"id": "pillar"})
        assert r.get("ok"), f"remove pillar refused: {r}"
        # the pad is still depressed by the failed tower; let it spring
        # back to its alone-rest pose before anything spawns on it
        run.pause(False)
        run.settle(timeout=8.0)
        run.pause(True)
        stp = run.state()
        pad_top = (run.part(stp, PAD["id"])["com_m"][1] + PAD["h"] / 2)
        # the pillars spawn at their PAIR sink only on the settled pad
        # (challenge-1 recovery pattern: the pad's descent under the new
        # load is dynamic and the pillars ride it)
        sup_sink = M_PILLAR * G / _pair_kt(KT_PILLAR, wc1.KT_PAD)
        r = run.eng.post("/tick_b2_place",
                         pillar_at_doc("pillar_l", PILLAR_L_CX,
                                       pad_top - sup_sink))
        assert r.get("ok"), f"pillar_l refused: {r}"
        r = run.eng.post("/tick_b2_place",
                         pillar_at_doc("pillar_r", PILLAR_R_CX,
                                       pad_top - sup_sink))
        assert r.get("ok"), f"pillar_r refused: {r}"
        # the pad's creep under the two pillars is SLOW (smoke-run lesson:
        # a loose threshold left ~20 mm of descent pending and the crate
        # placed on that moving base punched through). The base must be
        # truly static before the crate spawns: long settle, strict
        # threshold (0.4 s of drift at 0.5 mm/s is 0.2 mm, well inside the
        # crate's pair budget).
        run.pause(False)
        run.settle(timeout=30.0, vthresh=5e-4)
        run.pause(True)
        stp = run.state()
        sup_top = (run.part(stp, "pillar_l")["com_m"][1] + PILLAR["h"] / 2)
        # the crate re-places at its POST-patch pair equilibrium on the
        # settled tops; the mass patch lands while STILL paused, so the
        # unpause starts balanced -- no step load (the step load is exactly
        # what punched the crate through the single pillar)
        r = run.eng.post("/tick_b2_place",
                         crate_doc(chain="tower",
                                   bottom_y=sup_top - SINK_2X))
        assert r.get("ok"), f"recovery crate refused: {r}"
        r = run.eng.post("/tick_b2_patch",
                         {"id": "crate", "mass_kg": M_CRATE_2X})
        assert r.get("ok"), f"recovery mass patch refused: {r}"
        run.anchor("S6_recovery_armed", kind="settled")
        rec["recovery"] = {
            "action": "remove the punched-through tower; let the pad "
                      "spring back; add the SECOND PILLAR beside the first "
                      "(unrotated supports at x 0.555/0.685 -- the brief's "
                      "'wider base' recovery; rotated face-owner supports "
                      "drop vertex-resting loads in this build); re-place "
                      "the crate straddling both tops at the POST-patch "
                      "pair equilibrium, then apply the doubled mass "
                      "before the unpause (no step load)",
            "pad_top_after_springback_m": round(pad_top, 6),
            "pillar_spawn_bottom_m": round(pad_top - sup_sink, 6),
            "pillar_top_settled_m": round(sup_top, 6),
            "crate_spawn_sink_m": round(SINK_2X, 6),
            "predicted_clearance_mm": round(PRED_STRADDLE_MM, 3)}
        run.board("Workshop challenge 2 - recovery",
                  "EDIT: a SECOND pillar added beside the first (wider "
                  "base); the doubled load will ride two supports. "
                  "Testing...")
        run.pause(False)
        st = run.settle(timeout=12.0)
        run.pause(True)
        passed_r, fin_r = run.measure("recovery")
        assert passed_r, "the recovery edit did not recover"
        rec["recovery"]["verdict"] = "PASS"
        rec["recovery"]["clearance_m"] = fin_r["clearance_m"]
        rec["recovery"]["total_reaction_n"] = run.state()["total_reaction_n"]
        run.board("Workshop challenge 2 - recovered",
                  f"RECOVERED: the doubled load now rides TWO pillars - "
                  f"crate {fin_r['clearance_m'] * 1000:.0f} mm above the "
                  f"hazard (was {fin_v['clearance_m'] * 1000:.0f} mm, "
                  f"through the tower). The recipe was reused, the world "
                  f"changed, one edit recovered it.", "green")
        run.shot("6-recovered-terminal", "frame")
        run.shot("6-recovered-glass", "glass", wait_ms=1200)
        run.mem("recovery")
        run.log("recovery", passed=passed_r,
                clearance_mm=round(fin_r["clearance_m"] * 1000, 3),
                predicted_mm=round(PRED_STRADDLE_MM, 3))

        # ══ terminal save + B4 bit-exactness + refusal probe ═════════════
        doc_t = run.eng.raw("/tick_b2_save")
        (out / "save_terminal.json").write_bytes(doc_t)
        rec["saves"]["terminal"] = {
            "file": "save_terminal.json",
            "sha256": hashlib.sha256(doc_t).hexdigest()}
        h_pre = run.hash()
        r = run.eng.post_raw("/tick_b2_restore", doc_t.decode())
        assert r.get("ok"), f"terminal restore refused: {r}"
        h_post = run.hash()
        rec["restore_bit_exact"] = bool(h_pre == h_post)
        r = run.eng.post("/tick_b2_patch", {"id": "nope", "mu": 0.0})
        assert not r.get("ok", True), "patch of unknown part accepted"
        rec["refusals"].append({
            "edit": "patch unknown part after terminal restore",
            "error": r.get("error", ""),
            "hash_unchanged": run.hash() == h_post})
        run.shot("7-terminal-restored", "frame")
        run.log("terminal", restore_bit_exact=rec["restore_bit_exact"])

        # ══ measurements + frozen-surface check ══════════════════════════
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
        run.shutdown()
    # stdout FPS parse (frame-time evidence; challenge-1 pattern)
    log = out / "native2" / "stdout.log"
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
    rec["exe_sha256"] = run.exe_sha
    (out / "run_receipt.json").write_text(json.dumps(rec, indent=1),
                                          encoding="utf-8")
    return rec


# ─────────────────────────────────────────────────────────────────────────────
# two-run comparison (challenge-1 band machinery; glass identity compared)
# ─────────────────────────────────────────────────────────────────────────────
def compare(run1: Path, run2: Path, out: Path) -> dict:
    r1 = json.loads((run1 / "run_receipt.json").read_text())
    r2 = json.loads((run2 / "run_receipt.json").read_text())
    cmp: dict = {"schema": "chimera-workshop-challenge2-comparison-v1",
                 "run1": str(run1), "run2": str(run2)}
    # 1. deterministic state anchors on the DOCUMENT (challenge-1 law)
    det = {}
    for k in sorted(set(r1["state_docs"]) & set(r2["state_docs"])):
        kind = r1["anchor_kinds"].get(k, "analytic")
        a = json.loads(r1["state_docs"][k])
        b = json.loads(r2["state_docs"][k])
        diffs = wc1._doc_equiv(a, b, k)
        det[k] = {"kind": kind, "run1_hash": r1["states"][k],
                  "run2_hash": r2["states"][k],
                  "n_violations": len(diffs), "violations": diffs[:8],
                  "within_band": not diffs}
    cmp["deterministic_states"] = det
    cmp["analytic_states_byte_identical_modulo_steps"] = bool(det) and all(
        v["within_band"] for v in det.values() if v["kind"] == "analytic")
    cmp["all_states_within_band"] = bool(det) and all(
        v["within_band"] for v in det.values())
    # 2. shots: /frame byte identity claimed; /glass compared too (the board
    #    glass shots were byte-identical in challenge 1 -- measured, with
    #    live-HUD lanes excluded from the gate only if they differ)
    for lane in ("frame", "glass"):
        shots = {}
        for k in sorted(set(r1["shots"]) & set(r2["shots"])):
            if r1["shots"][k]["lane"] != lane:
                continue
            shots[k] = {"run1": r1["shots"][k]["sha256"],
                        "run2": r2["shots"][k]["sha256"],
                        "byte_identical": (r1["shots"][k]["sha256"]
                                           == r2["shots"][k]["sha256"])}
        cmp[f"{lane}_shots"] = shots
        cmp[f"all_{lane}_shots_byte_identical"] = bool(shots) and all(
            v["byte_identical"] for v in shots.values())
    # 3. settled save documents within the objective-loop band
    band = {}
    for name, fname in (("solution_B", "save_B.json"),
                        ("terminal", "save_terminal.json")):
        a = json.loads((run1 / fname).read_bytes())
        b = json.loads((run2 / fname).read_bytes())
        diffs = wc1._doc_equiv(a, b, name)
        band[name] = {"violations": diffs[:20], "n_violations": len(diffs),
                      "within_band": not diffs}
    cmp["settled_save_docs"] = band
    # 4. the challenge-2 gate
    def gate(rec):
        v = rec["variation"]
        return {
            "build_passed": rec["predicate"]["recipe_build"]["passed"],
            "transfer_passed": rec["predicate"]["transfer"]["passed"],
            "restored_hash_equals_engine1_saved":
                rec["transfer"]["restored_hash_equals_engine1_saved"],
            "variation_measured":
                "margin_after_mm" in v
                and v["margin_after_mm"] < v["margin_before_mm"],
            "variation_verdict": v.get("verdict"),
            "recovery_passed": rec["predicate"]["recovery"]["passed"],
            "restore_bit_exact": rec["restore_bit_exact"],
            "refusals_preserved":
                all(x["hash_unchanged"] for x in rec["refusals"])}
    g1, g2 = gate(r1), gate(r2)
    cmp["gate_challenge2"] = {"run1": g1, "run2": g2}
    cmp["gate_pass"] = all(
        [g1["build_passed"], g2["build_passed"],
         g1["transfer_passed"], g2["transfer_passed"],
         g1["restored_hash_equals_engine1_saved"],
         g2["restored_hash_equals_engine1_saved"],
         g1["variation_measured"], g2["variation_measured"],
         g1["recovery_passed"], g2["recovery_passed"],
         g1["restore_bit_exact"], g2["restore_bit_exact"],
         g1["refusals_preserved"], g2["refusals_preserved"]])
    out.write_text(json.dumps(cmp, indent=1), encoding="utf-8")
    return cmp


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--out", required=True)
    r.add_argument("--port", type=int, required=True)
    r.add_argument("--port2", type=int, default=None)
    c = sub.add_parser("compare")
    c.add_argument("run1")
    c.add_argument("run2")
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    if args.cmd == "run":
        port2 = args.port2 if args.port2 is not None else args.port + 1
        rec = run_walkthrough(Path(args.out), args.port, port2)
        print(json.dumps({"states": rec["states"],
                          "transfer": rec["transfer"],
                          "variation": rec["variation"],
                          "recovery": rec["recovery"],
                          "restore_bit_exact": rec["restore_bit_exact"],
                          "frame_time": rec.get("frame_time"),
                          "clock": rec.get("clock"),
                          "memory": rec["memory"]}, indent=1))
    else:
        cmp = compare(Path(args.run1), Path(args.run2), Path(args.out))
        print(json.dumps({k: cmp[k] for k in
                          ("analytic_states_byte_identical_modulo_steps",
                           "all_states_within_band",
                           "all_frame_shots_byte_identical",
                           "all_glass_shots_byte_identical",
                           "settled_save_docs",
                           "gate_challenge2", "gate_pass")}, indent=1))


if __name__ == "__main__":
    main()
