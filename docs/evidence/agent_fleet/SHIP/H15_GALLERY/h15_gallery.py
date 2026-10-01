"""h15_gallery.py -- THE ALIVENESS GALLERY, one-command driver (agent H15).

Re-proofs the bring-alive law (import -> classify -> bind -> seal, then
pose + 10 kN touch) on all five watertight shapes from G4's round
(tools/gallery/generate.py + tools/gallery/obj/*.obj, commit e0422599),
against a THROWAWAY engine per creature on a PRIVATE port (default 8140).
Adapted from tools/gallery/run_gallery.py (G4, commit 39341be2) with four
changes this audit needs:

  1. --base style control: --port selects the throwaway port; every
     engine is booted and killed BY THIS SCRIPT (boot -> run -> kill,
     per creature, in a finally block). The live stack is never touched.
  2. All outputs land in --out (the evidence dir): gallery_results.json
     + one framed portrait per creature. Nothing is written to the
     operator's desktop.
  3. A GUARD WATCH: every JSON response is scanned for refusal strings
     ('degenerate', 'refus', 'guard') -- the degenerate-split guard
     landing in membrane_tick.cpp must show up HERE, per shape, so the
     after-run can tell "junk split correctly refused" from
     "legitimate seal broken".
  4. A2 gains a vertex-displacement answer (max/RMS displacement of the
     whole skin under the mid-spine flex, measured /verts vs /verts),
     and the script CLOSES THE LOOP ITSELF: each shape is judged
     against the expected table (cells=2, |conserve_pct| <= 0.001,
     dimple 0.198944 m +/- 0.005, torus loops=2) and the process exit
     code is 0 iff 5/5 ALIVE -- the one-command pass/fail for the
     post-build after-run (see PROTOCOL.md).

Isolation (G4's measured recipe, kept): each throwaway runs with
--hidden in a PRIVATE cwd (scratch root, one subdir per creature) hold-
ing a copy of shaders/, so its session_snapshot/ lands in the scratch
dir and boot restore finds no blobs -- the tick is born EMPTY (asserted
sealed==false before every import) and the LIVE engine's snapshot files
are never read, written, or deleted. NOTE: --no-restore is NOT used:
measured 2/2 by G4 on this binary lineage, --no-restore + --hidden
fail-fast at boot (0xC0000409); --hidden alone in an isolated cwd gives
the same empty-boot semantics without the crash. (If --base is given,
the script drives that ALREADY-RUNNING engine instead of booting -- for
targeted one-shape probes only; the standard run boots its own.)

Usage:
  python h15_gallery.py                       # full 5-shape after-run
  python h15_gallery.py --port 8140           # explicit private port
  python h15_gallery.py --shapes torus        # one-shape probe
  python h15_gallery.py --base http://127.0.0.1:8140 --shapes torus
"""
from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent          # the evidence dir
REPO = HERE.parents[4]                          # E:\ChimeraWork\slot-01
OBJ_DIR = REPO / "tools" / "gallery" / "obj"
SCRATCH = REPO / ".h15_scratch"                 # untracked scratch root

TOUCH_FORCE_N = 10_000.0                        # the 10 kN bar

# the expected table (G4 round 2, commit 39341be2 -- the BEFORE bar the
# after-run must re-meet on the post-guard binary):
EXPECT_CONSERVE_PCT = 0.001     # |conserve_pct| band (ship bar: 0.000)
EXPECT_DIMPLE_M = 0.198944      # force-determined, shape-independent
EXPECT_DIMPLE_TOL = 0.005
EXPECT_CELLS = 2                # every mid-height seal: exactly 2 cells
GUARD_STRINGS = ("degenerate", "refus", "guard")


# -- HTTP (octet-stream contract of /mesh_import and friends) ------------
def post(base: str, path: str, body: bytes | str, timeout: int = 300) -> dict:
    data = body.encode() if isinstance(body, str) else body
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.loads(r.read().decode())
    return watch_guard(path, out)


def get_json(base: str, path: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        out = json.loads(r.read().decode())
    return watch_guard(path, out)


def get_raw(base: str, path: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def watch_guard(path: str, out: dict) -> dict:
    """GUARD WATCH: surface any refusal/degenerate/guard string the
    engine puts in a response, per endpoint, into the record."""
    blob = json.dumps(out).lower()
    hits = [s for s in GUARD_STRINGS if s in blob]
    if hits:
        out.setdefault("_guard_watch", []).append(
            {"endpoint": path, "strings": hits})
    return out


def get_verts(base: str):
    """-> (nv, pos (nv,3) f32) from the engine's own store."""
    vbuf = np.frombuffer(get_raw(base, "/verts"), dtype=np.float32)
    nv = struct.unpack_from("<I", vbuf, 0)[0]
    return nv, vbuf[1:].reshape(nv, 9)[:, 0:3].copy()


# -- throwaway engine lifecycle (G4's Engine, port + cwd re-rooted) ------
class Engine:
    def __init__(self, port: int, engine_exe: Path):
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.engine_exe = engine_exe
        self.proc: subprocess.Popen | None = None
        self.run_dir = SCRATCH / f"cwd_{port}_{time.strftime('%H%M%S')}"
        self.log_path = self.run_dir / "engine.log"

    def start(self, wait_s: float = 90.0) -> None:
        assert self.engine_exe.is_file(), f"engine missing: {self.engine_exe}"
        shaders = self.engine_exe.parent / "shaders"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(shaders, self.run_dir / "shaders", dirs_exist_ok=True)
        logf = open(self.log_path, "ab")
        # --hidden ONLY, isolated cwd (G4's measured recipe -- see header)
        self.proc = subprocess.Popen(
            [str(self.engine_exe), str(self.port), "--hidden"],
            cwd=str(self.run_dir), stdout=logf, stderr=logf,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        deadline = time.time() + wait_s
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f"engine exited at boot (code {self.proc.returncode}); "
                    f"log {self.log_path}")
            try:
                st = get_json(self.base, "/tick_state", timeout=2)
                assert st.get("sealed") is not True, \
                    "throwaway booted SEALED -- the isolated cwd failed"
                get_json(self.base, "/state", timeout=2)
                time.sleep(1.0)                  # settle: first frames render
                return
            except (urllib.error.URLError, OSError):
                time.sleep(0.5)
        raise RuntimeError(f"engine did not answer /state in {wait_s}s")

    def alive(self) -> bool:
        if self.proc is not None and self.proc.poll() is not None:
            return False
        try:
            get_json(self.base, "/state", timeout=3)
            return True
        except (urllib.error.URLError, OSError):
            return False

    def kill(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            subprocess.run(["taskkill", "/F", "/T", "/PID",
                            str(self.proc.pid)], capture_output=True)
            self.proc.wait(timeout=15)
        time.sleep(1.0)

    def log_tail(self, lines: int = 40) -> str:
        try:
            return "\n".join(self.log_path.read_text(
                errors="replace").splitlines()[-lines:])
        except OSError:
            return "(log unreadable)"


# -- the law, one creature ------------------------------------------------
def spine_pins(ylo: float, yhi: float, k: int, cx: float, cz: float):
    ys = ylo + (np.arange(k, dtype=np.float32) + 0.5) * (yhi - ylo) / k
    pins = np.empty((k, 3), dtype=np.float32)
    pins[:, 0], pins[:, 1], pins[:, 2] = cx, ys, cz
    return pins


def bring_alive(eng: Engine, obj: Path, k_joints: int,
                pose_deg: float) -> dict:
    base = eng.base
    rec: dict = {"name": obj.stem, "obj_bytes": obj.stat().st_size}

    # 1. IMPORT -- 'O' + bytes
    raw = obj.read_bytes()
    imp = post(base, "/mesh_import", b"O" + raw, timeout=300)
    rec["import"] = imp
    if not imp.get("ok"):
        rec["alive"] = False
        rec["refusal"] = imp.get("error", "(no error field)")
        print(f"  IMPORT REFUSED: {rec['refusal']}")
        return rec
    nv_imp, nt_imp = imp["verts"], imp["tris"]
    print(f"  import: {nv_imp:,} verts {nt_imp:,} tris V={imp['volume']:.6g}"
          + (", winding flipped" if imp.get("winding_flipped") else ""))

    # geometry from the ENGINE's own store
    topo = get_raw(base, "/topology")
    n_tri = struct.unpack_from("<I", topo, 0)[0]
    idx = np.frombuffer(topo, dtype=np.uint32, count=n_tri * 3,
                        offset=4).reshape(n_tri, 3)
    nv, pos = get_verts(base)
    assert n_tri == nt_imp and nv == nv_imp, "upload did not land"

    # 2-4. JOINTS / CLASSIFY / VERTBIND
    ylo, yhi = float(imp["ymin"]), float(imp["ymax"])
    pins = spine_pins(ylo, yhi, k_joints, float(pos[:, 0].mean()),
                      float(pos[:, 2].mean()))
    rec["joints"] = post(base, "/tick_joints",
                         struct.pack("<I", k_joints)
                         + np.ascontiguousarray(pins).tobytes())
    centroids = pos[idx].mean(axis=1)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    rec["classify"] = post(base, "/tick_classify",
                           struct.pack("<I", n_tri) + tri_joint.tobytes())
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    order = np.argsort(d2v, axis=1)[:, :3]
    d3 = np.take_along_axis(d2v, order, axis=1)
    w = 1.0 / (d3 + 1e-6) ** 2
    w /= w.sum(axis=1, keepdims=True)
    vb = np.empty((nv, 15), dtype=np.uint8)
    for c in range(3):
        vb[:, c] = order[:, c].astype(np.uint8)
    for c in range(3):
        vb[:, 3 + c * 4:7 + c * 4] = np.frombuffer(
            np.ascontiguousarray(w[:, c], dtype=np.float32).tobytes(),
            dtype=np.uint8).reshape(nv, 4)
    rec["vertbind"] = post(base, "/tick_vertbind",
                           struct.pack("<I", nv) + vb.tobytes(), timeout=300)

    # 5. SEAL at mid-height  (the path the degenerate-split guard shares)
    y_cut = 0.5 * (ylo + yhi)
    rec["seal"] = post(base, "/tick_seal", json.dumps({"y": y_cut}),
                       timeout=300)
    print(f"  seal y={y_cut:.4g}: {rec['seal']}")

    # A1: cells conserve
    st = get_json(base, "/tick_state")
    a1 = abs(st.get("conserve_pct", 1e9)) <= 1.0 and bool(st.get("sealed")) \
        and st.get("n_cells", 0) >= 2
    rec["a1"] = {"sealed": st.get("sealed"), "n_cells": st.get("n_cells"),
                 "V_whole": st.get("V_whole"),
                 "V_cells": [c.get("V") for c in st.get("cells", [])],
                 "conserve_pct": st.get("conserve_pct"),
                 "seal_loops": st.get("seal_loops"),
                 "seal_cuts": st.get("seal_cuts"),
                 "seal_caps": st.get("seal_caps"),
                 "pass": bool(a1)}
    print(f"  A1 conserve: cells={st.get('n_cells')} "
          f"V_whole={st.get('V_whole'):.6g} "
          f"conserve={st.get('conserve_pct'):.4f}% "
          f"loops={st.get('seal_loops')} -> {'PASS' if a1 else 'FAIL'}")

    # A2: pose flex -- conservation UNDER pose + VERTEX DISPLACEMENT,
    # then rest (the rest must come back). The flex joint is the G4 mid
    # pin first; if that pin has no arm on this shape (measured today:
    # the torus mid pin sits in the HOLE, displacement exactly 0), the
    # pose answer falls back to the best-armed joint -- the pin owning
    # the most vertices under the same nearest-3 binding this run sent.
    nv2, rest_pos = get_verts(base)               # rest skin (post-seal)
    mid = k_joints // 2
    dominant = order[:, 0]
    armed = np.bincount(dominant, minlength=k_joints)
    pose_joint = mid
    p1 = post(base, "/tick_pose", json.dumps({"joint_index": pose_joint,
                                              "deg": pose_deg}))
    time.sleep(0.8)                      # the pose eases over ticks: let
    st2 = get_json(base, "/tick_state")  # it LAND before reading skin
    nv3, posed_pos = get_verts(base)     # posed skin
    d = (np.linalg.norm(posed_pos - rest_pos, axis=1)
         if nv2 == nv3 else None)
    alt = None
    if d is not None and d.max() < 1e-4 and int(armed.argmax()) != mid:
        pose_joint = int(armed.argmax())          # the best-armed pin
        alt = {"joint": pose_joint, "armed_verts": int(armed.max())}
        p1 = post(base, "/tick_pose", json.dumps({"joint_index": pose_joint,
                                                  "deg": pose_deg}))
        time.sleep(0.8)
        st2 = get_json(base, "/tick_state")
        nv3, posed_pos = get_verts(base)
        d = (np.linalg.norm(posed_pos - rest_pos, axis=1)
             if nv2 == nv3 else None)
    p2 = post(base, "/tick_pose",
              json.dumps({"joint_index": pose_joint, "deg": 0}))
    time.sleep(0.8)                      # let the rest pose land on ticks
    st3 = get_json(base, "/tick_state")
    nv4, rest2_pos = get_verts(base)              # back to rest
    disp = None
    if d is not None and nv2 == nv4:
        d_rest = np.linalg.norm(rest2_pos - rest_pos, axis=1)
        disp = {"joint": pose_joint, "max_m": float(d.max()), "rms_m":
                float(np.sqrt((d ** 2).mean())),
                "moved_verts_gt_1mm": int((d > 1e-3).sum()),
                "rest_return_max_m": float(d_rest.max()),
                "fallback": alt}
    a2 = bool(p1.get("ok") and p2.get("ok")
              and abs(st2.get("conserve_pct", 1e9)) <= 1.0
              and abs(st3.get("conserve_pct", 1e9)) <= 1.0
              and disp is not None and disp["max_m"] > 0.0)
    rec["a2"] = {"pose_ok": p1.get("ok"), "conserve_posed":
                 st2.get("conserve_pct"), "conserve_rest":
                 st3.get("conserve_pct"), "displacement": disp,
                 "pass": bool(a2)}
    dmax = disp["max_m"] if disp else float("nan")
    print(f"  A2 pose joint {pose_joint} +{pose_deg:g} deg: conserve_posed="
          f"{st2.get('conserve_pct'):.4f}% conserve_rest="
          f"{st3.get('conserve_pct'):.4f}% maxdisp={dmax:.4f} m "
          f"-> {'PASS' if a2 else 'FAIL'}")

    # A3: the 10 kN touch answers (hit = topmost LIVE vertex, on skin)
    top_i = int(np.argmax(rest_pos[:, 1]))
    hit = [float(x) for x in rest_pos[top_i]]
    rest = get_json(base, "/tick_state")
    p_rest = [rest.get("P_lower"), rest.get("P_upper")]
    t1 = post(base, "/tick_touch", json.dumps(
        {"hit": hit, "force_n": TOUCH_FORCE_N}))
    time.sleep(1.5)                      # the engine ticks at 60 Hz
    pressed = get_json(base, "/tick_state")
    post(base, "/tick_touch_clear", "{}")
    time.sleep(0.8)
    after = get_json(base, "/tick_state")
    dP = [pressed.get("P_lower", 0) - (p_rest[0] or 0),
          pressed.get("P_upper", 0) - (p_rest[1] or 0)]
    a3 = bool(t1.get("ok")) and (
        abs(dP[0]) > 0 or abs(dP[1]) > 0
        or abs(pressed.get("dimple_m", 0)) > 0)
    rec["a3"] = {"hit": hit, "force_n": TOUCH_FORCE_N, "touch_ok":
                 t1.get("ok"), "P_rest": p_rest,
                 "P_pressed": [pressed.get("P_lower"),
                               pressed.get("P_upper")], "dP": dP,
                 "dimple_m": pressed.get("dimple_m"),
                 "P_after_release": [after.get("P_lower"),
                                     after.get("P_upper")],
                 "pass": a3}
    print(f"  A3 touch 10 kN at ({hit[0]:.3f},{hit[1]:.3f},{hit[2]:.3f}): "
          f"ok={t1.get('ok')} dP={dP[0]:+.1f}/{dP[1]:+.1f} "
          f"dimple={pressed.get('dimple_m')} -> {'PASS' if a3 else 'FAIL'}")

    # the framed portrait: fit the eye, capture
    fit = post(base, "/cameras", json.dumps({"op": "fit"}), timeout=60)
    time.sleep(0.8)
    png = get_raw(base, "/frame?w=900", timeout=120)
    if png[:8] == b"\x89PNG\r\n\x1a\n":
        out = HERE / f"{obj.stem}_alive.png"
        out.write_bytes(png)
        rec["frame"] = {"path": str(out), "bytes": len(png), "fit":
                        fit.get("ok")}
        print(f"  frame: {out.name} ({len(png):,} B)")
    else:
        rec["frame"] = {"error": png[:120].decode(errors="replace")}
        print(f"  frame FAILED: {rec['frame']['error']}")

    rec["alive"] = bool(a1 and a2 and a3 and rec.get("frame", {})
                        .get("path"))
    return rec


def judge(rec: dict) -> dict:
    """Close the loop: judge one shape against the expected table."""
    v: dict = {"name": rec.get("name", "?")}
    imp = rec.get("import", {})
    a1, a2, a3 = rec.get("a1", {}), rec.get("a2", {}), rec.get("a3", {})
    cells = a1.get("V_cells") or []
    v["import_ok"] = bool(imp.get("ok"))
    v["cells"] = a1.get("n_cells")
    v["cells_ok"] = a1.get("n_cells") == EXPECT_CELLS
    cons = a1.get("conserve_pct")
    v["conserve_pct"] = cons
    v["conserve_ok"] = cons is not None and abs(cons) <= EXPECT_CONSERVE_PCT
    dimple = a3.get("dimple_m")
    v["dimple_m"] = dimple
    v["dimple_ok"] = (dimple is not None
                      and abs(dimple - EXPECT_DIMPLE_M) <= EXPECT_DIMPLE_TOL)
    v["pose_disp_m"] = (a2.get("displacement") or {}).get("max_m")
    v["pose_ok"] = bool(a2.get("pass"))
    v["touch_ok"] = bool(a3.get("pass"))
    v["portrait_ok"] = bool(rec.get("frame", {}).get("path"))
    if rec.get("name") == "torus":
        v["torus_loops"] = a1.get("seal_loops")
        v["torus_loops_ok"] = a1.get("seal_loops") == 2
    v["guard_watch"] = [w for k in ("import", "joints", "classify",
                                    "vertbind", "seal")
                        for w in (rec.get(k, {}) or {}).get("_guard_watch",
                                                            [])]
    v["alive"] = bool(rec.get("alive"))
    v["verdict"] = "ALIVE" if v["alive"] else "NOT ALIVE"
    if v["alive"] and not all([v["cells_ok"], v["conserve_ok"],
                               v["dimple_ok"], v["pose_ok"], v["touch_ok"],
                               v["portrait_ok"]]
                              + ([v["torus_loops_ok"]]
                                 if rec.get("name") == "torus" else [])):
        v["verdict"] = "ALIVE-BUT-OFF-EXPECTED"
    return v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8140)
    ap.add_argument("--engine", default=str(REPO / ".tmp" / "build_tick"
                                            / "Release"
                                            / "chimera_engine.exe"))
    ap.add_argument("--pose-deg", type=float, default=25.0)
    ap.add_argument("--joints", type=int, default=9)
    ap.add_argument("--shapes", default="blob,torus,capsule,peanut,rbox",
                    help="comma subset for one-shape probes")
    ap.add_argument("--base", default=None,
                    help="drive an ALREADY-RUNNING engine instead of "
                         "booting (probe mode; the standard run boots)")
    args = ap.parse_args()
    engine_exe = Path(args.engine)
    shapes = [s.strip() for s in args.shapes.split(",") if s.strip()]
    objs = [OBJ_DIR / f"{s}.obj" for s in shapes]
    for o in objs:
        assert o.is_file(), f"missing creature mesh: {o}"

    results, verdicts = [], []
    for obj in objs:
        print(f"\n=== {obj.stem} ===")
        eng = None if args.base else Engine(args.port, engine_exe)
        base = args.base or eng.base
        rec: dict = {"name": obj.stem}
        try:
            if eng is not None:
                eng.start()
            rec = bring_alive(type("B", (), {"base": base})(), obj,
                              args.joints, args.pose_deg)
        except Exception as exc:             # noqa: BLE001 -- a gallery
            rec["alive"] = False             # row must survive anything
            rec["crash"] = {"exc": f"{type(exc).__name__}: {exc}",
                            "engine_alive_after":
                            eng.alive() if eng else None,
                            "log_tail": eng.log_tail(15) if eng else ""}
            print(f"  CRASH/FAULT: {rec['crash']['exc']}")
        finally:
            if eng is not None:
                eng.kill()
        rec["judge"] = judge(rec)
        verdicts.append(rec["judge"])
        results.append(rec)
        print(f"  VERDICT: {obj.stem} -> {rec['judge']['verdict']}")

    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_json = HERE / f"gallery_results_{stamp}.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    latest = HERE / "gallery_results.json"
    latest.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n=== GALLERY TABLE ===")
    print(f"{'creature':9s} {'verts':>6s} {'tris':>6s} {'cells':>5s} "
          f"{'V_whole':>9s} {'cons%':>8s} {'loops':>5s} {'dimple':>8s} "
          f"{'maxdisp':>8s}  verdict")
    all_ok = True
    for r in results:
        j = r["judge"]
        all_ok &= j["alive"] and j["verdict"] == "ALIVE"
        if "import" not in r or not r["import"].get("ok"):
            print(f"{r['name']:9s} REFUSED: "
                  f"{r.get('refusal', r.get('crash'))}")
            continue
        a1, a2, a3 = r.get("a1", {}), r.get("a2", {}), r.get("a3", {})
        disp = (a2.get("displacement") or {}).get("max_m", float("nan"))
        print(f"{r['name']:9s} {r['import']['verts']:6d} "
              f"{r['import']['tris']:6d} {a1.get('n_cells', 0):5d} "
              f"{a1.get('V_whole', 0):9.4f} "
              f"{a1.get('conserve_pct', 0):8.5f} "
              f"{a1.get('seal_loops', 0):5d} "
              f"{a3.get('dimple_m', 0):8.4f} {disp:8.4f}  "
              f"{j['verdict']}")
    print(f"\nresults: {out_json}")
    print(f"ONE-COMMAND VERDICT: "
          f"{'PASS 5/5 ALIVE' if all_ok else 'FAIL -- GALLERY NOT RE-PROVEN'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
