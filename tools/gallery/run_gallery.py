"""run_gallery.py -- THE ALIVENESS GALLERY (agent G4).

Brings five varied watertight OBJ creatures (tools/gallery/generate.py)
alive on a THROWAWAY engine at 127.0.0.1:18107, one engine per creature,
and measures the bring-alive law's three bars on each:

  A1  cells conserve volume after /tick_seal        (|conserve_pct| <= 1)
  A2  a mid-spine flex holds conservation UNDER pose
  A3  a 10 kN touch answers (dimple_m, cell pressure dP)

Every creature runs on a FRESH engine (the import path had a crash class;
the throwaway on 18107 exists so a crash cannot hurt the live stack, and
the stale-seal guard refuses a second import onto a sealed tick anyway).
If an import kills the engine: restart, record the crash, move on.

Usage:  python tools/gallery/run_gallery.py [--port 18107] [--pose-deg 25]
Outputs: gallery_results.json + one framed PNG per alive creature in
C:\\Users\\allen\\Desktop\\CHIMERA_PROOF\\ALIVE_GALLERY\\
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

ROOT = Path(__file__).resolve().parents[2]          # E:\ChimeraWork\slot-01
ENGINE = ROOT / ".tmp" / "build_tick" / "Release" / "chimera_engine.exe"
SHADERS = ENGINE.parent / "shaders"
RUN_DIR = Path(__file__).resolve().parent / "run"   # ISOLATED cwd: the
OBJ_DIR = Path(__file__).resolve().parent / "obj"   # throwaway's session
GALLERY = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\ALIVE_GALLERY")
LOG_DIR = Path(__file__).resolve().parent / "logs"

TOUCH_FORCE_N = 10_000.0                            # the 10 kN bar


# ── HTTP (octet-stream contract of /mesh_import and friends) ────────────
def post(base: str, path: str, body: bytes | str, timeout: int = 300) -> dict:
    data = body.encode() if isinstance(body, str) else body
    req = urllib.request.Request(base + path, data=data, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(base: str, path: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_bytes(base: str, path: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


# ── throwaway engine lifecycle ──────────────────────────────────────────
class Engine:
    def __init__(self, port: int):
        self.port = port
        self.base = f"http://127.0.0.1:{port}"
        self.proc: subprocess.Popen | None = None
        self.log_path = LOG_DIR / f"engine_{port}_{time.strftime('%H%M%S')}.log"

    def start(self, wait_s: float = 90.0) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        assert ENGINE.is_file(), f"engine binary missing: {ENGINE}"
        # ISOLATED CWD: the engine reads shaders CWD-relative and keeps the
        # CWD when shaders\\render.vert.spv is found there -- so a run dir
        # with a shaders copy holds the throwaway's session_snapshot/,
        # session_*.jsonl and camera_bookmarks.txt away from the LIVE
        # engine's Release cwd. Boot restore (default-on) then finds no
        # blobs and the tick is born EMPTY -- the --no-restore semantics
        # without --no-restore itself, which on this build (measured,
        # 2/2) fails fast at boot (0xC0000409) when combined with
        # --hidden. /session clear was NOT an option: it deletes the
        # SHARED snapshot blobs the live stack's next boot depends on.
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SHADERS, RUN_DIR / "shaders", dirs_exist_ok=True)
        logf = open(self.log_path, "ab")
        self.proc = subprocess.Popen(
            [str(ENGINE), str(self.port), "--hidden"],
            cwd=str(RUN_DIR), stdout=logf, stderr=logf,
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

    def crash_tail(self, lines: int = 40) -> str:
        try:
            return "\n".join(self.log_path.read_text(
                errors="replace").splitlines()[-lines:])
        except OSError:
            return "(log unreadable)"


# ── the law, one creature ───────────────────────────────────────────────
def spine_pins(ylo: float, yhi: float, k: int, cx: float, cz: float):
    ys = ylo + (np.arange(k, dtype=np.float32) + 0.5) * (yhi - ylo) / k
    pins = np.empty((k, 3), dtype=np.float32)
    pins[:, 0], pins[:, 1], pins[:, 2] = cx, ys, cz
    return pins


def bring_alive(eng: Engine, obj: Path, k_joints: int, pose_deg: float) -> dict:
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
    topo = get_bytes(base, "/topology")
    n_tri = struct.unpack_from("<I", topo, 0)[0]
    idx = np.frombuffer(topo, dtype=np.uint32, count=n_tri * 3,
                        offset=4).reshape(n_tri, 3)
    vbuf = np.frombuffer(get_bytes(base, "/verts"), dtype=np.float32)
    nv = struct.unpack_from("<I", vbuf, 0)[0]
    pos = vbuf[1:].reshape(nv, 9)[:, 0:3]
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

    # 5. SEAL at mid-height
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

    # A2: pose flex holds conservation, then rest
    mid = k_joints // 2
    p1 = post(base, "/tick_pose", json.dumps({"joint_index": mid,
                                              "deg": pose_deg}))
    st2 = get_json(base, "/tick_state")
    p2 = post(base, "/tick_pose", json.dumps({"joint_index": mid, "deg": 0}))
    st3 = get_json(base, "/tick_state")
    a2 = bool(p1.get("ok") and p2.get("ok")
              and abs(st2.get("conserve_pct", 1e9)) <= 1.0
              and abs(st3.get("conserve_pct", 1e9)) <= 1.0)
    rec["a2"] = {"pose_ok": p1.get("ok"), "conserve_posed":
                 st2.get("conserve_pct"), "conserve_rest":
                 st3.get("conserve_pct"), "pass": bool(a2)}
    print(f"  A2 pose +{pose_deg:g} deg: conserve_posed="
          f"{st2.get('conserve_pct'):.4f}% conserve_rest="
          f"{st3.get('conserve_pct'):.4f}% -> {'PASS' if a2 else 'FAIL'}")

    # A3: the 10 kN touch answers (hit = topmost LIVE vertex, on skin)
    top_i = int(np.argmax(pos[:, 1]))
    hit = [float(x) for x in pos[top_i]]
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
    png = get_bytes(base, "/frame?w=900", timeout=120)
    if png[:8] == b"\x89PNG\r\n\x1a\n":
        out = GALLERY / f"{obj.stem}_alive.png"
        out.write_bytes(png)
        rec["frame"] = {"path": str(out), "bytes": len(png), "fit": fit.get("ok")}
        print(f"  frame: {out.name} ({len(png):,} B)")
    else:
        rec["frame"] = {"error": png[:120].decode(errors="replace")}
        print(f"  frame FAILED: {rec['frame']['error']}")

    rec["alive"] = bool(a1 and a2 and a3 and rec.get("frame", {})
                        .get("path"))
    return rec


# ── orchestration: one fresh throwaway per creature ─────────────────────
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18107)
    ap.add_argument("--pose-deg", type=float, default=25.0)
    ap.add_argument("--joints", type=int, default=9)
    args = ap.parse_args()
    objs = sorted(OBJ_DIR.glob("*.obj"))
    assert len(objs) == 5, f"expected 5 creatures in {OBJ_DIR}, found {objs}"
    GALLERY.mkdir(parents=True, exist_ok=True)

    results = []
    for obj in objs:
        print(f"\n=== {obj.stem} ===")
        eng = Engine(args.port)
        rec: dict = {"name": obj.stem}
        try:
            eng.start()
            rec = bring_alive(eng, obj, args.joints, args.pose_deg)
        except Exception as exc:                 # noqa: BLE001 -- a gallery
            rec["alive"] = False                 # row must survive anything
            rec["crash"] = {"exc": f"{type(exc).__name__}: {exc}",
                            "engine_alive_after": eng.alive(),
                            "log_tail": eng.crash_tail(15)}
            print(f"  CRASH/FAULT: {rec['crash']['exc']} "
                  f"(engine alive after: {rec['crash']['engine_alive_after']})")
        finally:
            eng.kill()
        results.append(rec)
        print(f"  VERDICT: {obj.stem} -> "
              f"{'ALIVE' if rec.get('alive') else 'NOT ALIVE'}")

    (GALLERY / "gallery_results.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")

    print("\n=== GALLERY TABLE ===")
    print(f"{'creature':9s} {'verts':>6s} {'tris':>6s} {'cells':>5s} "
          f"{'V_whole':>9s} {'cons%':>7s} {'dP_lower':>9s} {'dP_upper':>9s} "
          f"{'dimple':>8s}  verdict")
    for r in results:
        if "import" not in r or not r["import"].get("ok"):
            print(f"{r['name']:9s} REFUSED: {r.get('refusal', r.get('crash'))}")
            continue
        a1, a3 = r.get("a1", {}), r.get("a3", {})
        dP = a3.get("dP", [0, 0])
        print(f"{r['name']:9s} {r['import']['verts']:6d} "
              f"{r['import']['tris']:6d} {a1.get('n_cells', 0):5d} "
              f"{a1.get('V_whole', 0):9.4f} {a1.get('conserve_pct', 0):7.3f} "
              f"{dP[0]:9.1f} {dP[1]:9.1f} {a3.get('dimple_m', 0):8.4f}  "
              f"{'ALIVE' if r.get('alive') else 'NOT ALIVE'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
