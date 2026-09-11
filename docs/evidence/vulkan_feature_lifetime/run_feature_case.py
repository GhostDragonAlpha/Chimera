"""Owned-engine per-feature lifetime runner for engine-feature-resource-lifetime-02.

Adapted from the engine-vulkan-cleanup-02 lane's run_case.py (same owned-window
discipline: only test-owned HWNDs are queried, moved, closed, or captured).
One engine process per --case; each case loads a declared feature family from
EXISTING sourced fixtures, exercises its load/replacement/clear paths, reads
its live state gate, then closes in order. stderr is retained verbatim —
validation errors in it are the decisive measurement, never filtered here.

Fixture recipes are the ones the prior evidence lanes recorded verbatim:
mesh/hinge/joints = the C1 D1 driver sequence (scratch/_joints_verify.py),
water = the H4 lane (scratch/_chrome_verify.py), frost = the H9/H12 blob.
"""
from __future__ import annotations

import argparse
import ctypes as c
from ctypes import wintypes as w
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import time
import urllib.request
from datetime import datetime, timezone

_PARENT = Path(__file__).resolve().parent.parent / "engine_shutdown_order" / "parent_runtime" / "owned_visual"
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("owned_backdrop", _PARENT / "owned_backdrop.py")
ob = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(ob)
OwnedBackdrop, capture_client = ob.OwnedBackdrop, ob.capture_client
hwnd_owner, post_owned_close = ob.hwnd_owner, ob.post_owned_close
require_owned_hwnd, window_rect, sha256_file = ob.require_owned_hwnd, ob.window_rect, ob.sha256_file

LAYOUT = (64, 64, 1280, 720)  # single static window: resize generations were PR #58's scope
SHUTDOWN_MARKERS = [
    "shutdown: admission_closed",
    "shutdown: boot_joined",
    "shutdown: http_stopped",
    "shutdown: engine_shutdown",
]
WATCHDOG_SECONDS = 10
user = c.WinDLL("user32", use_last_error=True)
user.SetProcessDPIAware()
user.IsWindowVisible.argtypes = [w.HWND]
user.IsWindow.argtypes = [w.HWND]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.SetWindowPos.argtypes = [w.HWND, w.HWND, c.c_int, c.c_int, c.c_int, c.c_int, w.UINT]
user.ShowWindow.argtypes = [w.HWND, c.c_int]
WM_CLOSE = 0x0010
callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

CASES = ("F1_JOINTS", "F2_WATER", "F3_FROST")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def windows(pid: int) -> list[tuple[int, tuple[int, int, int, int]]]:
    found = []

    @callback_type
    def visit(hwnd, _):
        if hwnd_owner(int(hwnd)) == pid and user.IsWindowVisible(hwnd):
            rect = window_rect(int(hwnd))
            if rect[2] > rect[0] and rect[3] > rect[1]:
                found.append((int(hwnd), rect))
        return True

    user.EnumWindows(visit, 0)
    return sorted(found, key=lambda item: ((item[1][2] - item[1][0]) *
                                           (item[1][3] - item[1][1])), reverse=True)


def http_json(port: int, method: str, path: str, body=None, timeout: float = 35.0):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def http_bytes(port: int, method: str, path: str, data=None, ct: str | None = None,
               timeout: float = 35.0) -> bytes:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method)
    if data is not None and ct:
        req.add_header("Content-Type", ct)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


# ── fixture payload builders: the prior lanes' recipes, byte for byte ────────
def build_mesh_and_hinge(fixtures: Path) -> tuple[bytes, bytes, dict]:
    import numpy as np
    import trimesh
    mesh = trimesh.load(fixtures / "monkey_assets/recon/8955fb5b9c9b4e169456ccbae7c465f7_birth.glb",
                        force="mesh")
    eg = np.load(fixtures / "eye_build/eye_geom.npz")
    nb = len(mesh.vertices)
    verts = np.vstack([np.asarray(mesh.vertices, np.float32), eg["verts"].astype(np.float32)])
    tris = np.vstack([np.asarray(mesh.faces, np.int64),
                      eg["tris"].astype(np.int64) + nb]).astype(np.uint32)
    norms = np.vstack([np.asarray(mesh.vertex_normals, np.float32), eg["norms"].astype(np.float32)])
    cols = np.vstack([np.tile(np.array([[0.80, 0.55, 0.35]], np.float32), (nb, 1)),
                      np.tile(np.array([[0.10, 0.10, 0.12]], np.float32),
                              (len(eg["verts"]), 1))])
    verts9 = np.hstack([verts, norms, cols]).astype(np.float32)
    extent = float(np.linalg.norm(verts, axis=1).max()) or 1.0
    hdr = struct.pack("<II4f", len(verts), int(tris.size), 2.7 * extent, 0.6, 0.12, 0.0)
    mesh_body = hdr + verts9.tobytes() + tris.tobytes()

    npz = np.load(fixtures / "skeleton/joints_pack.npz", allow_pickle=True)
    names_l = list(npz["names"])
    kl, kr = names_l.index("knee_L"), names_l.index("knee_R")
    hinge_hdr = struct.pack("<I13f", len(verts),
                            *npz["J"][kl].tolist(), *npz["J"][kr].tolist(),
                            *npz["axis"][kl].tolist(),
                            float(npz["rom"][kl][1]), float(npz["rom"][kr][1]), 4.0, 0.0)
    zeros = np.zeros(len(verts), dtype=np.float32).tobytes()
    hinge_body = hinge_hdr + zeros + zeros
    provenance = {"mesh_verts": int(len(verts)), "mesh_tris": int(len(tris))}
    return mesh_body, hinge_body, provenance


def build_water(fixtures: Path) -> bytes:
    import numpy as np
    p = np.load(fixtures / "water_gpu/water_payload.npz")
    n, ne, nc = int(p["n_cells"]), int(p["n_edges"]), int(p["n_colors"])
    inj = p["inj"].astype(np.uint32)
    hdr = struct.pack("<4I3d", n, ne, nc, inj.shape[0],
                      float(p["Q"]), float(p["G"]), float(p["c_local"]))
    return (hdr
            + p["areas"].astype(np.float64).tobytes()
            + p["bed"].astype(np.float64).tobytes()
            + p["V0"].astype(np.int32).tobytes()
            + p["occ_mask"].astype(np.uint32).tobytes()
            + p["edge_ij"].astype(np.int32).tobytes()
            + p["k_e"].astype(np.float64).tobytes()
            + p["l_ij"].astype(np.float64).tobytes()
            + p["edge_active"].astype(np.uint32).tobytes()
            + p["color_start"].astype(np.uint32).tobytes()
            + inj.tobytes())


def ordered_shutdown(log: str) -> tuple[bool, list[int]]:
    positions = [log.find(marker) for marker in SHUTDOWN_MARKERS]
    return all(position >= 0 for position in positions) and positions == sorted(positions), positions


def post_bin(port: int, path: str, body: bytes) -> tuple[int, bytes]:
    return 200, http_bytes(port, "POST", path, body, "application/octet-stream")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime-name", required=True)
    parser.add_argument("--fixtures", type=Path, required=True,
                        help="absolute path of the sourced fixture root (.tmp)")
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--port", type=int, default=8105)
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    exe = args.exe.resolve()
    output = args.output.resolve()
    fixtures = args.fixtures.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing evidence directory: {output}")
    if not exe.is_file() or not (exe.parent / "shaders").is_dir():
        raise FileNotFoundError("supplied executable or adjacent shaders are missing")
    for needed in ("skeleton/joints_pack.bin", "skeleton/joints_pack.npz",
                   "water_gpu/water_payload.npz", "frost_gt/frost_engine.bin",
                   "monkey_assets/recon/8955fb5b9c9b4e169456ccbae7c465f7_birth.glb",
                   "eye_build/eye_geom.npz"):
        if not (fixtures / needed).is_file():
            raise FileNotFoundError(f"sourced fixture missing: {fixtures / needed}")
    if Path(args.runtime_name).name != args.runtime_name:
        raise ValueError("runtime-name must be one path component")
    output.mkdir(parents=True)
    runtime = repo / ".tmp" / "engine_runtime" / args.runtime_name
    runtime.mkdir(parents=True, exist_ok=False)
    staged = runtime / exe.name
    shutil.copy2(exe, staged)
    shutil.copytree(exe.parent / "shaders", runtime / "shaders")

    fixture_hashes = {name: sha256_file(fixtures / name) for name in (
        "skeleton/joints_pack.bin", "skeleton/joints_pack.npz",
        "water_gpu/water_payload.npz", "frost_gt/frost_engine.bin",
        "monkey_assets/recon/8955fb5b9c9b4e169456ccbae7c465f7_birth.glb",
        "eye_build/eye_geom.npz")}
    shader_hashes = {
        str(path.relative_to(runtime)): sha256_file(path)
        for path in sorted((runtime / "shaders").glob("*.spv"))
    }
    source = {
        "main_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/main.cpp"),
        "engine_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/engine.cpp"),
        "engine_hpp_sha256": sha256_file(repo / "ChimeraEngine/engine/engine.hpp"),
        "ui_cpp_sha256": sha256_file(repo / "ChimeraEngine/engine/ui.cpp"),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "fixture_root": str(fixtures),
        "fixture_sha256": fixture_hashes,
        "shader_manifest_sha256": hashlib.sha256(
            json.dumps(shader_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    result = {
        "schema": "chimera-vulkan-feature-lifetime-case-v1",
        "case": args.case,
        "declared_layout_xywh": list(LAYOUT),
        "watchdog_seconds": WATCHDOG_SECONDS,
        "source": source,
        "command": [str(staged), str(args.port), "--no-restore"],
        "validation": {
            "layer": "VK_LAYER_KHRONOS_validation (engine-enabled when present, engine.cpp:474-500)",
            "stderr_is_verbatim": True,
            "suppression": "none",
        },
        "steps": [],
    }
    backdrop = None
    proc = None
    try:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(("127.0.0.1", args.port))

        backdrop = OwnedBackdrop(LAYOUT).start()
        result["backdrop_reference"] = capture_client(
            backdrop.hwnd, backdrop.pid, output / "backdrop_reference.png", "backdrop reference")

        env = os.environ.copy()
        env.pop("CHIMERA_SHUTDOWN_TEST_HOLD", None)
        stdout_path = output / "engine.stdout.log"
        stderr_path = output / "engine.stderr.log"
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            proc = subprocess.Popen(result["command"], cwd=runtime, env=env,
                                    stdout=stdout, stderr=stderr,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        engine = {"pid": proc.pid, "exe_sha256": sha256_file(staged), "staged_exe": str(staged)}
        result["engine"] = engine

        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError("native process exited during startup")
            visible = windows(proc.pid)
            if visible:
                try:
                    http_json(args.port, "GET", "/state", timeout=1.0)
                    break
                except Exception:
                    pass
            time.sleep(0.05)
        else:
            raise AssertionError("startup did not produce an owned window and HTTP readiness")
        result["cases_V0_startup"] = {"passed": True}

        hwnd = visible[0][0]
        engine["hwnd"] = hwnd
        require_owned_hwnd(hwnd, proc.pid, "engine")
        with socket.socket() as probe2:
            probe2.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                probe2.bind(("127.0.0.1", args.port))
                raise AssertionError("listener is not the engine process")
            except OSError:
                pass  # bind refused because the engine owns the port
        user.ShowWindow(w.HWND(hwnd), 9)
        if not user.SetWindowPos(w.HWND(hwnd), w.HWND(-1), *LAYOUT, 0x0040):
            raise c.WinError(c.get_last_error(), "SetWindowPos(owned engine)")
        time.sleep(1.2)

        def step(name, ok, detail):
            result["steps"].append({"step": name, "ok": bool(ok), "detail": detail})
            if not ok:
                raise AssertionError(f"{name} failed: {detail}")

        # ── the per-case feature paths ───────────────────────────────────────
        if args.case == "F1_JOINTS":
            mesh_body, hinge_body, prov = build_mesh_and_hinge(fixtures)
            pack = (fixtures / "skeleton/joints_pack.bin").read_bytes()
            st, body = post_bin(args.port, "/mesh_bin", mesh_body)
            step("mesh_load", st == 200 and b'"ok":true' in body, body[:60])
            st, body = post_bin(args.port, "/hinge_bin", hinge_body)
            step("hinge_scaffold", st == 200 and b'"ok":true' in body, body[:60])
            st, body = post_bin(args.port, "/joints_bin", pack)
            step("joints_load", st == 200 and b'"ok":true' in body, body[:80])
            http_json(args.port, "POST", "/joints", body={"on": True})
            time.sleep(0.5)
            doc = http_json(args.port, "GET", "/joints")
            step("joints_gate", bool(doc.get("loaded")) and doc.get("n_joints") == 19,
                 {"loaded": doc.get("loaded"), "n_joints": doc.get("n_joints")})
            st, body = post_bin(args.port, "/joints_bin", pack)   # replacement path
            step("joints_reload", st == 200 and b'"ok":true' in body, body[:80])
            time.sleep(0.5)
            doc = http_json(args.port, "GET", "/joints")
            step("joints_gate_after_reload",
                 bool(doc.get("loaded")) and doc.get("n_joints") == 19,
                 {"loaded": doc.get("loaded"), "n_joints": doc.get("n_joints")})
            # the B3 clear path: a VALID header carrying N=0/idxCount=0
            # (a zero-byte body is rejected as "short header" by the parser)
            clear_hdr = struct.pack("<II4f", 0, 0, 2.7, 0.6, 0.12, 0.0)
            st, body = post_bin(args.port, "/mesh_bin", clear_hdr)
            step("mesh_clear", st == 200 and b'"ok":true' in body, body[:60])
            st, body = post_bin(args.port, "/mesh_bin", mesh_body)
            step("mesh_reupload", st == 200 and b'"ok":true' in body, body[:60])
            http_json(args.port, "POST", "/joints", body={"on": True})
            time.sleep(0.5)
            http_json(args.port, "POST", "/strain", body={"on": True})
            time.sleep(0.5)
            strain = http_json(args.port, "GET", "/strain")
            step("strain_gate", strain.get("on") is True and strain.get("hinge") is True, strain)
            doc = http_json(args.port, "GET", "/joints")
            step("joints_gate_after_clear_cycle",
                 bool(doc.get("loaded")) and doc.get("n_joints") == 19,
                 {"loaded": doc.get("loaded"), "n_joints": doc.get("n_joints")})
            result["fixture_provenance"] = prov

        elif args.case == "F2_WATER":
            water_body = build_water(fixtures)
            st, body = post_bin(args.port, "/water_bin", water_body)
            step("water_load", st == 200 and b'"ok":true' in body, body[:60])
            st, body = post_bin(args.port, "/water_bin", water_body)  # replacement path
            step("water_reload", st == 200 and b'"ok":true' in body, body[:60])
            time.sleep(0.5)
            states = http_bytes(args.port, "GET", "/water_state")
            ns, nc = struct.unpack("<II", states[:8]) if len(states) >= 8 else (0, 0)
            step("water_state_gate", ns >= 1, {"bytes": len(states), "ns": ns, "nc": nc})

        elif args.case == "F3_FROST":
            blob = (fixtures / "frost_gt/frost_engine.bin").read_bytes()
            st, body = post_bin(args.port, "/frost_bin", blob)
            step("frost_load", st == 200 and b'"ok":true' in body, body[:60])
            http_json(args.port, "POST", "/frost", body={"on": True})
            time.sleep(0.5)
            st, body = post_bin(args.port, "/frost_bin", blob)   # replacement path
            step("frost_reload", st == 200 and b'"ok":true' in body, body[:60])
            http_json(args.port, "POST", "/frost", body={"on": True})
            time.sleep(0.5)
            doc = http_json(args.port, "GET", "/frost")
            step("frost_gate", bool(doc.get("loaded")) and doc.get("on") is True,
                 {"loaded": doc.get("loaded"), "on": doc.get("on"),
                  "n_tris": doc.get("n_tris")})

        # a presented frame proves the loaded state is live in the render loop
        deadline = time.monotonic() + 10
        glass = b""
        while time.monotonic() < deadline:
            try:
                glass = http_bytes(args.port, "GET", "/glass")
                if glass.startswith(b"\x89PNG\r\n\x1a\n"):
                    break
            except Exception:
                pass
            time.sleep(0.1)
        if not glass.startswith(b"\x89PNG\r\n\x1a\n"):
            raise AssertionError("owned engine did not produce a presented /glass PNG")
        (output / "engine_loaded_glass.png").write_bytes(glass)
        result["loaded_glass"] = {"png_bytes": len(glass),
                                  "sha256": hashlib.sha256(glass).hexdigest()}

        result["window_before_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        if not result["window_before_close"]:
            raise AssertionError("engine HWND disappeared before WM_CLOSE")
        post_owned_close(hwnd, proc.pid, "engine")
        try:
            result["exit_code"] = proc.wait(timeout=WATCHDOG_SECONDS)
        except subprocess.TimeoutExpired:
            result["watchdog"] = True
            proc.kill()  # exact owned process handle only; retained as a failure
            result["exit_code"] = proc.wait()
        result["window_after_close"] = bool(user.IsWindow(w.HWND(hwnd)))
        log = stdout_path.read_text(encoding="utf-8", errors="replace")
        result["ordered_markers"], result["marker_positions"] = ordered_shutdown(log)
        close = {"passed": result["exit_code"] == 0 and not result.get("watchdog")
                 and not result["window_after_close"] and result["ordered_markers"],
                 "exit_code": result["exit_code"], "watchdog": bool(result.get("watchdog")),
                 "window_after_close": result["window_after_close"],
                 "ordered_markers": result["ordered_markers"],
                 "marker_positions": result["marker_positions"]}
        result["cases_V4_ordered_shutdown"] = close

        require_owned_hwnd(backdrop.hwnd, backdrop.pid, "backdrop after close")
        after_raw = capture_client(backdrop.hwnd, backdrop.pid,
                                   output / "backdrop_after.png", "backdrop after close")
        result["backdrop_unchanged"] = after_raw["sha256"] == result["backdrop_reference"]["sha256"]
        if not result["backdrop_unchanged"]:
            raise AssertionError("owned backdrop changed between reference and post-close capture")

        err = stderr_path.read_text(encoding="utf-8", errors="replace")
        result["validation_error_lines"] = sum(1 for line in err.splitlines() if "[VK ERROR]" in line)
        result["vuid_vkDestroyDevice_05137_count"] = err.count("VUID-vkDestroyDevice-device-05137")
        result["vuid_vkFreeMemory_memory_00677_count"] = err.count("VUID-vkFreeMemory-memory-00677")
        result["passed"] = (all(s["ok"] for s in result["steps"])
                            and result["cases_V4_ordered_shutdown"]["passed"]
                            and result["validation_error_lines"] == 0)
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["passed"] = False
    finally:
        if proc is not None and proc.poll() is None:
            for hwnd, _ in windows(proc.pid):
                try:
                    post_owned_close(hwnd, proc.pid, "engine cleanup")
                except Exception:
                    pass
            try:
                proc.wait(timeout=WATCHDOG_SECONDS)
            except subprocess.TimeoutExpired:
                result["cleanup_watchdog"] = True
                proc.kill()
                proc.wait()
        if backdrop is not None:
            try:
                backdrop.close()
            except Exception as exc:
                result["backdrop_cleanup_error"] = f"{type(exc).__name__}: {exc}"
                result["passed"] = False
        (output / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps({k: v for k, v in result.items() if k != "source"}, indent=2))
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
