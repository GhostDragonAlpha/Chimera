"""B4 gate battery: interactive cradle assembly on the resident runtime.

The §13 B4 evidence column: "Place, connect, test, release, mechanically
patch, save and reload admitted parts through transactions" with the
acceptance row "Rejected edits preserve state; no stale selections remain;
loaded release has the declared work/momentum consequence; player can
explain and improve a connection".

Scene: the B3 stack (granite/steel/timber) plus a placed timber BLOCK
(`cradle_block`) standing on the ground 40 mm clear of the granite base.
The block is ADMITTED BY PLACE, not by the scene document -- the place
transaction runs the same parse law as admission. The block<->granite
weld across the gap (virtual link points -> zero rest length, zero
preload, no contact) is the cradle connection; re-welding the same
anchors stiffer is the connection improvement.

The block spawns pre-sunk by the analytic rest sink (1 cm), so its ground
rung is active from step 0 and it never free-falls.

Run:  python tools/construction_packet/test_b4_assembly.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import unittest
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
PORT = 8793
BASE = f"http://127.0.0.1:{PORT}"

from tools.construction_packet.cradle_recipe import (
    G, IDS, MASS, BLOCK_ID, BLOCK_BOX, BLOCK_MASS, BLOCK_COM, WELD_ANCHORS, block_doc,
)

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read().decode())


def _raw(path: str) -> bytes:
    with urllib.request.urlopen(BASE + path, timeout=25) as r:
        return r.read()


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _part(st: dict, pid: str) -> dict:
    return next(p for p in st["parts"] if p["id"] == pid)


def _ids(st: dict) -> list[str]:
    return [p["id"] for p in st["parts"]]


def _settle(seconds: float) -> None:
    time.sleep(seconds)


def _wait(pred, timeout: float, dt: float = 0.05):
    deadline = time.time() + timeout
    st = _get("/tick_b2_state")
    while time.time() < deadline:
        if pred(st):
            return True, st
        time.sleep(dt)
        st = _get("/tick_b2_state")
    return pred(st), st


def _hash() -> str:
    return _get("/tick_b2_hash")["state_hash"]


def _pause(on: bool) -> None:
    assert _post("/tick_b2_pause", json.dumps({"on": on})).get("ok")


def _load(pid: str, force, point) -> None:
    assert _post("/tick_b2_load", json.dumps(
        {"part": pid, "force_n": list(force), "point_world": list(point)})).get("ok")


def _weld(a: str, b: str, k: float, c_damp: float = 10.0) -> None:
    # c_damp scales with the LIGHTEST part: the explicit dashpot needs
    # h*c/m << 1 (h = 250 us, m = 0.0864 kg -> c < ~30). The B3 stack weld
    # used 300 because its lightest part is 0.52 kg.
    assert _post("/tick_b2_weld", json.dumps(
        {"a": a, "b": b, "k": k, "c_damp": c_damp,
         "anchors_world": [[*p, *p] for p in WELD_ANCHORS]})).get("ok")




def setUpModule():
    global _proc
    assert EXE.exists(), f"engine missing: {EXE} (build Release first)"
    _proc = subprocess.Popen(
        [str(EXE), str(PORT), "--hidden", "1600", "900", "--no-restore"],
        cwd=str(EXE.parent))
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            _get("/tick_state")
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("engine did not answer /tick_state within 30 s")


def tearDownModule():
    if _proc and _proc.poll() is None:
        _proc.terminate()


class B4Assembly(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    def admit_stack(self):
        r = _post("/tick_b2_admit", json.dumps(b2_scene_gen.make_stack()))
        self.assertTrue(r.get("ok"), f"admit refused: {r}")
        _settle(2.5)

    def place(self, doc: dict) -> dict:
        return _post("/tick_b2_place", json.dumps(doc))

    # ── place + transactions: rejected edits preserve state ────────────────
    def test_place_and_transactions(self):
        self.admit_stack()
        _pause(True)
        h0 = _hash()
        st = _get("/tick_b2_state")
        self.assertTrue(st["paused"])
        self.assertEqual(len(st["parts"]), 3)

        r = self.place(block_doc())
        self.assertTrue(r.get("ok"), f"place refused: {r}")
        st = _get("/tick_b2_state")
        self.assertEqual(_ids(st), IDS + [BLOCK_ID])
        # no double mass: total weight is the sum of the four weights
        want_w = sum(MASS[i] for i in IDS) * G + BLOCK_MASS * G
        self.assertAlmostEqual(st["total_weight_n"], want_w, delta=1e-6 * want_w)
        h1 = _hash()
        self.assertNotEqual(h1, h0)

        # every rejected edit names itself and leaves the hash untouched
        bad = [
            ("place duplicate id", "/tick_b2_place", block_doc(), "duplicate part id"),
            ("place negative mass", "/tick_b2_place",
             {**block_doc("blk_x"), "mass_kg": -1.0}, "mass_kg"),
            ("place asymmetric inertia", "/tick_b2_place",
             {**block_doc("blk_y"),
              "inertia_com_local_kg_m2": [1, 123, 0, 0, 1, 0, 0, 0, 1]}, "symmetric"),
            ("patch unknown part", "/tick_b2_patch",
             {"id": "nope", "mu": 0.1}, "no part"),
            ("patch negative mu", "/tick_b2_patch",
             {"id": BLOCK_ID, "mu": -1.0}, "must be >= 0"),
            ("patch nothing", "/tick_b2_patch", {"id": BLOCK_ID}, "nothing to patch"),
            ("remove unknown", "/tick_b2_remove", {"id": "nope"}, "no part"),
        ]
        for name, route, doc, why in bad:
            r = _post(route, json.dumps(doc))
            self.assertFalse(r.get("ok", True), f"{name} was accepted: {r}")
            self.assertIn(why, r.get("error", ""), f"{name}: {r}")
            self.assertEqual(_hash(), h1, f"{name} mutated the scene")
            self.assertEqual(len(_get("/tick_b2_state")["parts"]), 4)

        # restore refusals (bad schema / corrupt json) preserve state too
        doc = json.loads(_raw("/tick_b2_save"))
        r = _post("/tick_b2_restore", json.dumps({**doc, "schema": "chimera.b2_state.v2"}))
        self.assertFalse(r.get("ok", True))
        self.assertIn("schema", r.get("error", ""))
        r = _post("/tick_b2_restore", json.dumps(doc)[:-4])   # truncated
        self.assertFalse(r.get("ok", True))
        self.assertEqual(_hash(), h1)

        # the scene cap: place up to 6, the 7th is refused
        self.assertTrue(self.place(block_doc("blk_2", x0=0.41)).get("ok"))
        self.assertTrue(self.place(block_doc("blk_3", x0=0.48)).get("ok"))
        r = self.place(block_doc("blk_4", x0=0.55))
        self.assertFalse(r.get("ok", True))
        self.assertIn("cap of 6", r.get("error", ""))
        _post("/tick_b2_remove", json.dumps({"id": "blk_2"}))
        _post("/tick_b2_remove", json.dumps({"id": "blk_3"}))

        # accepted mechanical patch: mass x2 scales weight AND the rung
        # constants (rest sink preserved), and the hash moves
        h2 = _hash()
        r = _post("/tick_b2_patch", json.dumps({"id": BLOCK_ID, "mass_kg": 2 * BLOCK_MASS}))
        self.assertTrue(r.get("ok"), f"patch refused: {r}")
        st = _get("/tick_b2_state")
        b = _part(st, BLOCK_ID)
        self.assertAlmostEqual(b["mass_kg"], 2 * BLOCK_MASS, delta=1e-9)
        self.assertAlmostEqual(b["weight_n"], 2 * BLOCK_MASS * G, delta=1e-6)
        self.assertAlmostEqual(b["ground"]["k_n_per_m"],
                               2 * block_doc()["ground"]["k_n_per_m"], delta=1e-6)
        self.assertNotEqual(_hash(), h2)

        # test: release the pause and the patched block settles on its rung
        _pause(False)
        ok, st = _wait(lambda s: _part(s, BLOCK_ID)["speed_m_s"] < 5e-3
                       and abs(_part(s, BLOCK_ID)["reaction_n"] - 2 * BLOCK_MASS * G)
                       < 0.02 * 2 * BLOCK_MASS * G, 4.0)
        self.assertTrue(ok, f"patched block never settled: {st}")
        self.assertFalse(st["diverged"])

    # ── connect + release: no stale selections ─────────────────────────────
    def test_connect_and_release_no_stale_selections(self):
        self.admit_stack()
        _pause(True)
        self.assertTrue(self.place(block_doc()).get("ok"))
        _weld("layer_base_granite", BLOCK_ID, 20000.0)
        _load(BLOCK_ID, [0.0, 0.4, 0.0], BLOCK_COM)  # 0.4 N < W = 0.848 N
        _pause(False)
        ok, st = _wait(lambda s: abs(s["welds"][0]["force_n"] - 0.4) < 0.02, 4.0)
        self.assertTrue(ok, f"weld never carried the lift: {st}")
        self.assertEqual(len(st["welds"]), 1)

        # the placed part is pickable by its stable ID (render/pick lane)
        # frame the whole assembly: camera on the +x side, target centred
        # between the stack and the block (the block is never occluded:
        # the ray from x > 1 stays outside the granite's x <= 0.30 slab)
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "save", "name": "b4test",
             "v": [1.2, 0.9, 0.35, 0.25, 0.10, 0.15, 0.0, 0.0]})).get("ok"))
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "recall", "name": "b4test"})).get("ok"))
        _settle(0.6)
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(_raw("/frame"))).convert("RGB")
        W, H = img.size
        bc = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"]
        pr = _post("/project", json.dumps(
            {"x": bc[0], "y": bc[1] + 0.021, "z": bc[2]}))   # top face centre
        self.assertTrue(pr.get("ok"), f"/project: {pr}")
        pk = _post("/tick_b2_pick", json.dumps(
            {"px": pr["sx"] / W, "py": pr["sy"] / H}))
        self.assertEqual(pk.get("id"), BLOCK_ID, f"pick the placed block: {pk}")

        # release: the part, its weld and its load all die together
        r = _post("/tick_b2_remove", json.dumps({"id": BLOCK_ID}))
        self.assertTrue(r.get("ok"), f"remove refused: {r}")
        st = _get("/tick_b2_state")
        self.assertEqual(_ids(st), IDS)
        self.assertEqual(st["welds"], [], "stale weld survived the release")
        for p in st["parts"]:
            self.assertEqual(p["load_n"], [0.0, 0.0, 0.0],
                             f"stale load survived on {p['id']}")
        want_w = sum(MASS[i] for i in IDS) * G
        self.assertAlmostEqual(st["total_weight_n"], want_w, delta=1e-6 * want_w)
        # the released ID is gone from every lane
        ins = _post("/tick_b2_inspect", json.dumps({"id": BLOCK_ID}))
        self.assertFalse(ins.get("ok", True), "inspect still answers for it")
        pk = _post("/tick_b2_pick", json.dumps(
            {"px": pr["sx"] / W, "py": pr["sy"] / H}))
        self.assertNotEqual(pk.get("id"), BLOCK_ID, "pick still returns it")
        r = _post("/tick_b2_weld", json.dumps(
            {"a": "layer_base_granite", "b": BLOCK_ID, "k": 1000.0, "c_damp": 0.0,
             "anchors_world": [[*p, *p] for p in WELD_ANCHORS]}))
        self.assertFalse(r.get("ok", True), "weld to a released part accepted")

    # ── mechanical patch changes the friction behaviour ────────────────────
    def test_mechanical_patch_changes_friction(self):
        self.admit_stack()
        _pause(True)
        self.assertTrue(self.place(block_doc()).get("ok"))
        _pause(False)
        _settle(2.0)
        _pause(True)
        z0 = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"][2]
        _load(BLOCK_ID, [0.0, 0.0, 0.15], BLOCK_COM)  # 0.15 N < mu*W = 0.254 N
        _pause(False)
        _settle(1.2)
        _pause(True)
        creep = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"][2] - z0
        self.assertLess(abs(creep), 0.005,
                        f"mu 0.3 must stick a 0.15 N push (crept {creep})")

        # the mechanical patch: same part, same load, softer material
        r = _post("/tick_b2_patch", json.dumps({"id": BLOCK_ID, "mu": 0.05}))
        self.assertTrue(r.get("ok"), f"patch refused: {r}")
        _pause(False)
        _settle(1.2)
        slip = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"][2] - z0
        self.assertGreater(slip, 0.1,
                           f"mu 0.05 must slide under the same push (slipped {slip})")

    # ── connection improvement: same anchors, stiffer weld ─────────────────
    def test_connection_improvement(self):
        self.admit_stack()
        _pause(True)
        self.assertTrue(self.place(block_doc()).get("ok"))
        y0 = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"][1]

        # The block stays on its ground rung (lift 0.4 N < W 0.848 N), so
        # ground and weld are springs in parallel: the weld carries
        #     F_w = 0.4 * k / (k + k_ground),  k_ground = m g / s* = 84.8 N/m
        # and the connector stretches by F_w / k. Improving the connection
        # (same anchors, stiffer weld) makes it carry MORE of the load and
        # stretch far less -- the load-sharing law the player explains.
        # (Stretch is read from the weld's own force telemetry, not the COM
        # rise: the block keeps a ~0.2 deg tilt on its corner rungs, which
        # adds ~45 um of geometric noise to the COM but nothing to F_w/k.)
        k_ground = BLOCK_MASS * G / b2_scene_gen.REST_SINK_M

        def settled_for(k: float):
            # clean slate: a re-set weld zeroes its reference AT THE CURRENT
            # pose, so each phase must start from the unloaded rest pose or
            # the second stretch would be measured off the first's offset
            _post("/tick_b2_weld_remove", json.dumps(
                {"a": "layer_base_granite", "b": BLOCK_ID}))
            _load(BLOCK_ID, [0.0, 0.0, 0.0], BLOCK_COM)
            _pause(False)
            _settle(1.5)
            _pause(True)
            y_ref = _part(_get("/tick_b2_state"), BLOCK_ID)["com_m"][1]
            _weld("layer_base_granite", BLOCK_ID, k)
            _load(BLOCK_ID, [0.0, 0.4, 0.0], BLOCK_COM)
            _pause(False)
            prev, st = None, _get("/tick_b2_state")
            deadline = time.time() + 4.0
            while time.time() < deadline:
                y = _part(st, BLOCK_ID)["com_m"][1]
                if prev is not None and abs(y - prev) < 1e-6:
                    break
                prev = y
                time.sleep(0.1)
                st = _get("/tick_b2_state")
            _pause(True)
            f_w = st["welds"][0]["force_n"]
            return f_w / k, f_w, _part(st, BLOCK_ID)["com_m"][1] - y_ref

        # the connection as built: 4 anchors, k = 1 kN/m
        d_soft, f_soft, dy_soft = settled_for(1000.0)
        self.assertGreater(d_soft, 0.0002, f"soft weld stretched {d_soft}")
        self.assertAlmostEqual(f_soft, 0.4 * 1000.0 / (1000.0 + k_ground),
                               delta=0.02, msg="soft weld load share")
        # the improvement: SAME anchors, 20x stiffer weld (re-set replaces)
        d_stiff, f_stiff, dy_stiff = settled_for(20000.0)
        self.assertLess(d_stiff, 0.2 * d_soft,
                        f"stiffer weld must stretch far less: {d_stiff} vs {d_soft}")
        self.assertGreater(f_stiff, f_soft, "stiffer connection must carry more")
        self.assertAlmostEqual(f_stiff, 0.4 * 20000.0 / (20000.0 + k_ground),
                               delta=0.01, msg="stiff weld load share")

    # ── save / reload: exact round-trip through the transaction ────────────
    def test_save_reload_exact(self):
        self.admit_stack()
        _pause(True)
        # put the scene into a DECLARED moving state: timber mid-shear
        _load("layer_top_timber", [3.0, 0.0, 0.0],
              [0.15, 0.26 + b2_scene_gen.stack_rest_offsets()[2], 0.15])
        _pause(False)
        _settle(0.35)
        _pause(True)
        doc = json.loads(_raw("/tick_b2_save"))
        h1 = _hash()
        st1 = _get("/tick_b2_state")
        self.assertTrue(st1["paused"])
        self.assertGreater(_part(st1, "layer_top_timber")["speed_m_s"], 0.02,
                           "the saved state must carry real momentum")

        _post("/tick_b2_clear")
        self.assertFalse(_get("/tick_b2_state")["active"])
        # a corrupt reload is refused and leaves the cleared scene cleared
        # (restore accepts 1..6 parts -- an empty parts list is the refusal)
        r = _post("/tick_b2_restore", json.dumps({**doc, "parts": []}))
        self.assertFalse(r.get("ok", True))
        self.assertFalse(_get("/tick_b2_state")["active"])

        r = _post("/tick_b2_restore", json.dumps(doc))
        self.assertTrue(r.get("ok"), f"restore refused: {r}")
        self.assertEqual(_hash(), h1, "reload did not reproduce the scene bit-for-bit")
        st2 = _get("/tick_b2_state")
        self.assertEqual(st2["steps"], st1["steps"])
        self.assertEqual(st2["paused"], True)
        for pid in IDS:
            a, b = _part(st1, pid), _part(st2, pid)
            self.assertEqual(a["com_m"], b["com_m"], f"{pid} pose drifted")
            self.assertEqual(a["speed_m_s"], b["speed_m_s"], f"{pid} momentum drifted")
            self.assertEqual(a["pose_q_wxyz"], b["pose_q_wxyz"], f"{pid} rotation drifted")
            self.assertEqual(a["load_n"], b["load_n"], f"{pid} load drifted")

        # the declared momentum consequence: the reload keeps shearing
        _pause(False)
        _settle(0.3)
        st3 = _get("/tick_b2_state")
        self.assertGreater(_part(st3, "layer_top_timber")["speed_m_s"], 0.02,
                           "the reloaded momentum must keep evolving")
        # and a rejected edit after the reload still preserves state
        _pause(True)          # freeze first: a stepping scene hashes per frame
        h2 = _hash()
        r = _post("/tick_b2_patch", json.dumps({"id": "nope", "mu": 0.0}))
        self.assertFalse(r.get("ok", True))
        self.assertEqual(_hash(), h2)

    # ── loaded release: the declared weight/momentum consequence ───────────
    def test_release_declared_consequence(self):
        self.admit_stack()
        st0 = _get("/tick_b2_state")
        r0 = st0["total_reaction_n"]
        want0 = sum(MASS[i] for i in IDS) * G
        self.assertAlmostEqual(r0, want0, delta=0.01 * want0)

        # put the top layer into a declared sliding state, then release it
        _pause(True)
        _load("layer_top_timber", [3.0, 0.0, 0.0],
              [0.15, 0.26 + b2_scene_gen.stack_rest_offsets()[2], 0.15])
        _pause(False)
        _settle(0.35)
        _pause(True)
        st1 = _get("/tick_b2_state")
        top = _part(st1, "layer_top_timber")
        self.assertGreater(top["speed_m_s"], 0.02, "top must be mid-slide")
        self.assertNotEqual(top["load_n"], [0.0, 0.0, 0.0], "top must carry the load")
        p_top = MASS["layer_top_timber"] * top["speed_m_s"]
        others0 = {i: _part(st1, i)["speed_m_s"] for i in IDS[:2]}

        r = _post("/tick_b2_remove", json.dumps({"id": "layer_top_timber"}))
        self.assertTrue(r.get("ok"), f"release refused: {r}")
        st2 = _get("/tick_b2_state")
        self.assertEqual(_ids(st2), IDS[:2])
        # the released momentum left with the part: the neighbours are
        # untouched (they were at rest and stay at rest)
        for i in IDS[:2]:
            self.assertLess(_part(st2, i)["speed_m_s"], 0.01,
                            f"{i} moved when the top was released")
        self.assertGreater(p_top, 0.0, "sanity: released momentum was real")
        # the released load died with the part
        for p in st2["parts"]:
            self.assertEqual(p["load_n"], [0.0, 0.0, 0.0])
        # the declared weight consequence: the ground now carries two parts
        want1 = (MASS["layer_base_granite"] + MASS["layer_mid_steel"]) * G
        ok, st3 = _wait(lambda s: abs(s["total_reaction_n"] - want1) < 0.01 * want1, 4.0)
        self.assertTrue(ok, f"reaction never dropped to the two-part weight: {st3}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
