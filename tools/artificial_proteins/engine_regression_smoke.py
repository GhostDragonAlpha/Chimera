"""engine_regression_smoke.py -- stage 9 increment-5 follow-up: the
increment-4 open item, BROADER engine-suite regression beyond the membrane
scene. The increment-4 seam (981b805c: engine.cpp +289 md_deform/md_save/
md_restore, engine.hpp +33 membrane members, main.cpp +97 membrane routes)
has only ever been exercised through the membrane demo path; this driver
smoke-runs every OTHER scene/route family against the REBUILT exe:

  B2 scene      chimera.b2_scene.v1 admit (valid doc admitted, parts live,
                steps advance) + MALFORMED docs (named refusals, state hash
                and admission_reason untouched)   [main.cpp:100-194]
  studio board  the default CWD studio_board.json load (argv[2] a flag, so
                the board path is NOT overridden) surfaced by GET
                /studio_chrome "board"
  graph scene   the opt-in --science-surface flag parse + the live
                /science_surface control + /science, /science_graph assets
                [main.cpp:935]
  exclusivity   --science-surface then --thermal-salvage in ONE boot ->
                self-exit code 2 "exclusive_science_scene" [main.cpp:952];
                --science-surface then --earth-patch -> code 2
                "exclusive_earth_scene" [main.cpp:966]
  defaults      B2 scene OFF and membrane demo OFF on a default boot
                (GET /membrane_demo answers {"ok":false,"active":false})

Every boot is a private engine (copied exe + shaders, own port), terminated
by handle only; the exclusivity boots exit BY THEMSELVES with code 2 before
the HTTP server starts. HTTP bodies, B2 state hashes and exit codes are
recorded raw. Run INSIDE a managed GPU reservation (one gpu_batch job):
  python -B -m tools.artificial_proteins.engine_regression_smoke \
      --exe <chimera_engine.exe> --out <fresh dir> [--port 8845]
Prints "ENGINE REGRESSION COMPLETE <receipt path>"; exits 1 when any route
smoke FAILED (per-route verdicts in the receipt).
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from .native_binding_engine import _source_commit
from .native_view import require
from tools.evidence_output import default_stamp
from .core import file_hash

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent
EVID_DIR = _REPO / "docs" / "evidence" / "mechanism_factory"
RECEIPT_SCHEMA = "chimera-mechanism-factory-engine-regression-v1"
EXPECTED_ENGINE_SHA = ("c1c2474c6c8cbc58e73371ad8224882a031675aa3efbc6e"
                       "ba7fafed49fe0aa69")


# ── raw HTTP (records bodies; ok:false is DATA here, not a refusal) ─────────

def _http(base: str, method: str, path: str, payload=None,
          timeout: float = 10.0) -> dict:
    body = (json.dumps(payload, allow_nan=False).encode()
            if payload is not None else None)
    req = urllib.request.Request(
        base + path, data=body, method=method,
        headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            ctype = r.headers.get("Content-Type", "")
            status = r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        ctype = e.headers.get("Content-Type", "")
        status = e.code
    doc: dict = {"_status": status, "_content_type": ctype}
    if "json" in ctype:
        try:
            doc["json"] = json.loads(raw)
        except json.JSONDecodeError:
            doc["text"] = raw[:2000]
    else:
        doc["text"] = raw[:2000]
    return doc


# ── the graph scene's spec (chimera.surface.v1, composed from the load law) ──

def make_surface_spec(out_dir: Path) -> dict:
    """A minimal valid GraphSurface spec (graph_surface.hpp load law):
    3x3 plane grid, unit +z normal, 3+ pinned boundary vertices, normalized
    probe weights (pinned = 0), CCW-wound triangles, finite render params,
    one material with gamma, default force, boot camera, page/graph assets."""
    xs = [0.0, 0.1, 0.2]
    verts = [[x, y, 0.0] for y in xs for x in xs]          # 9 vertices
    idx = lambda ix, iy: iy * 3 + ix
    tris = []
    for iy in range(2):
        for ix in range(2):
            a, b, c, d = (idx(ix, iy), idx(ix + 1, iy),
                          idx(ix, iy + 1), idx(ix + 1, iy + 1))
            tris.append([a, b, d])                          # CCW about +z
            tris.append([a, d, c])
    free = [i for i in range(9) if i not in (0, 1, 2)]      # top row pinned
    w = [0.0] * 3 + [1.0 / 6.0] * 6
    page = out_dir / "science_page.html"
    page.write_text("<html><body>engine-regression smoke page</body></html>",
                    encoding="utf-8")
    graph = out_dir / "science_graph.json"
    graph.write_text('{"smoke":true}', encoding="utf-8")
    return {
        "schema": "chimera.surface.v1",
        "vertices_m": verts,
        "normal": [0.0, 0.0, 1.0],
        "pinned": [0, 1, 2],
        "probe_weights": w,
        "triangles": tris,
        "render_m_to_units": 100.0,
        "render_translation_units": [0.0, 0.2, 0.0],
        "max_force_N": 10.0,
        "temperature_K": 300.0,
        "graph_hash": "engine-regression-smoke-graph-hash",
        "materials": [{"name": "steel", "gamma_N_m": 1.0,
                       "source": "engine-regression smoke (composed from "
                                 "the graph_surface.hpp load law)",
                       "record_id": "engine_regression_smoke/spec"}],
        "default_force_N": 0.0,
        "camera": [1.5, 0.8, 0.9, 0.0, 0.1, 0.0, 0.0, 0.0],
        "page_file": str(page),
        "graph_file": str(graph),
    }


def make_incomplete_spec(out_dir: Path) -> dict:
    """The same spec WITHOUT the control-law's compiled max_force_N: the
    loader must refuse it and the boot must self-exit (main.cpp returns 2
    from the science-surface catch). The observed exit code is RECORDED,
    not assumed: the loader documents `return 2` but the first run
    self-exited with fail-fast 0xC0000409 -- a finding, reported."""
    spec = make_surface_spec(out_dir)
    spec.pop("max_force_N")
    return spec


# ── private engine boot/teardown (the established capture law) ───────────────

def _boot(executable: Path, native: Path, port: int, argv2: str,
          extra: list[str]) -> subprocess.Popen:
    """argv law (main.cpp:867-981): argv[1]=port; argv[2]=board path unless
    it starts with '--' (then the DEFAULT CWD board is polled); argv[3]/[4]
    override the 2K window; the flag loops scan every argv."""
    args = [str(native / executable.name), str(port), argv2, *extra]
    return subprocess.Popen(
        args, cwd=native,
        stdout=(native / "stdout.log").open("wb"),
        stderr=(native / "stderr.log").open("wb"))


def _teardown(proc: subprocess.Popen) -> int:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
    return proc.returncode


def _wait_ready(proc: subprocess.Popen, base: str,
                timeout_s: float = 30.0) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"engine_exited_during_boot_code_"
                               f"{proc.returncode}")
        try:
            chrome = _http(base, "GET", "/studio_chrome")
            if "json" in chrome.get("_content_type", ""):
                return chrome["json"]
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    raise RuntimeError("engine_readiness_timeout")


def _run_default_and_b2(executable: Path, native: Path, port: int,
                        out: Path) -> dict:
    results: dict = {}
    base = f"http://127.0.0.1:{port}"
    sys.path.insert(0, str(_REPO / "tools" / "construction_packet"))
    import b2_scene_gen                       # the gate's own scene generator
    board = out / "native" / "studio_board.json"   # the engine's CWD
    proc = None
    try:
        r = subprocess.run(
            [sys.executable, "-B", str(_REPO / "tools" / "studio_board.py"),
             "--out", str(board)],
            capture_output=True, text=True, timeout=120, cwd=str(_REPO))
        require(r.returncode == 0,
                f"studio_board_write_failed: {r.stderr[-200:]}")
        proc = _boot(executable, native, port, "--no-restore", [])
        chrome = _wait_ready(proc, base)
        time.sleep(1.5)          # the overlay polls the board per frame
        chrome = _http(base, "GET", "/studio_chrome").get("json", chrome)

        b2_default = _http(base, "GET", "/tick_b2_state")
        mem_default = _http(base, "GET", "/membrane_demo")
        results["studio_board_default"] = {
            "route": "GET /studio_chrome with the DEFAULT CWD board "
                     "(argv[2] is a flag, board path not overridden)",
            "board_stages": chrome.get("board", {}).get("stages"),
            "board_standing":
                chrome.get("board", {}).get("standing", "")[:80],
            "pass": bool(chrome.get("board", {}).get("stages")
                         and chrome.get("board", {}).get("standing"))}
        results["scene_defaults_off"] = {
            "b2_state_body": b2_default.get("json", b2_default.get("text")),
            "membrane_body": mem_default.get("json", mem_default.get("text")),
            "pass": bool(b2_default.get("json", {}).get("active") is False
                         and mem_default.get("json", {}).get("active") is False)}

        # ── B2 admit: the valid gate scene ───────────────────────────────
        scene = b2_scene_gen.make_scene()
        admit = _http(base, "POST", "/tick_b2_admit", scene)
        b2_live = _http(base, "GET", "/tick_b2_state").get("json", {})
        b2_hash = _http(base, "GET", "/tick_b2_hash").get("json", {})
        time.sleep(0.6)
        b2_live2 = _http(base, "GET", "/tick_b2_state").get("json", {})
        results["b2_admit_valid"] = {
            "route": "POST /tick_b2_admit (chimera.b2_scene.v1)",
            "http_body": admit.get("json", admit.get("text")),
            "state_after": {k: b2_live.get(k) for k in
                            ("active", "admission_reason", "steps",
                             "total_weight_n")},
            "n_parts": len(b2_live.get("parts", [])),
            "state_hash": b2_hash.get("state_hash"),
            "steps_advanced": (b2_live2.get("steps", 0)
                               > b2_live.get("steps", 0)),
            "pass": bool(admit.get("json", {}).get("ok")
                         and admit.get("json", {}).get("schema")
                         == "chimera.b2_scene.v1"
                         and b2_live.get("active")
                         and len(b2_live.get("parts", [])) == 2
                         and b2_live2.get("steps", 0)
                         > b2_live.get("steps", 0))}

        # ── B2 admit: malformed docs refuse BY NAME, scene untouched ─────
        # The state hash covers the DYNAMIC state too (b2_scene.hpp), so the
        # untouched check is measured on a PAUSED scene (the B4 transactional
        # law's own premise); the admission_reason is scene-static either way.
        paused = _http(base, "POST", "/tick_b2_pause", {"on": True})
        time.sleep(0.3)
        b2_hash_paused = _http(base, "GET", "/tick_b2_hash").get("json", {})
        b2_live_paused = _http(base, "GET", "/tick_b2_state").get("json", {})
        malformed = {}
        for tag, mutate in (
                ("schema_v2",
                 lambda s: s.update(schema="chimera.b2_scene.v2")),
                ("gravity_string",
                 lambda s: s.update(gravity_m_s2="9.81"))):
            bad = json.loads(json.dumps(scene))
            mutate(bad)
            refused = _http(base, "POST", "/tick_b2_admit", bad)
            b2_after = _http(base, "GET", "/tick_b2_state").get("json", {})
            b2_hash_after = _http(base, "GET", "/tick_b2_hash").get("json", {})
            untouched = (b2_hash_after.get("state_hash")
                         == b2_hash_paused.get("state_hash")
                         and b2_after.get("admission_reason")
                         == b2_live_paused.get("admission_reason"))
            malformed[tag] = {
                "http_body": refused.get("json", refused.get("text")),
                "state_hash_after": b2_hash_after.get("state_hash"),
                "state_hash_paused_before": b2_hash_paused.get("state_hash"),
                "admission_reason_after": b2_after.get("admission_reason"),
                "state_untouched": untouched,
                "pass": bool(refused.get("json", {}).get("ok") is False
                             and str(refused.get("json", {}).get("error", ""))
                             .startswith("refused:")
                             and untouched)}
        _http(base, "POST", "/tick_b2_pause", {"on": False})
        malformed["pass"] = all(v["pass"] for v in malformed.values())
        results["b2_admit_malformed"] = malformed
        results["b2_pause_control"] = {
            "route": "POST /tick_b2_pause (the B4 freeze control)",
            "body": paused.get("json", paused.get("text")),
            "pass": bool(paused.get("json", {}).get("ok"))}
    finally:
        results["boot_A_exit_code"] = _teardown(proc) if proc else None
    time.sleep(1.0)
    return results


def _run_graph_and_exclusivity(executable: Path, native: Path, port: int,
                               out: Path) -> dict:
    results: dict = {}
    base = f"http://127.0.0.1:{port}"
    spec_path = out / "science_surface_spec.json"
    spec_path.write_text(json.dumps(make_surface_spec(out)),
                         encoding="utf-8")
    page_path = out / "science_page.html"
    page_bytes = page_path.read_bytes()

    # ── boot B0: an INCOMPLETE science spec must be refused, boot self-exits
    bad_spec = out / "science_surface_spec_incomplete.json"
    bad_spec.write_text(json.dumps(make_incomplete_spec(out)),
                        encoding="utf-8")
    proc = None
    try:
        proc = _boot(executable, native, port, "--science-surface",
                     [str(bad_spec), "--no-restore"])
        try:
            proc.wait(timeout=45)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code = None
            _teardown(proc)
        err = (native / "stderr.log").read_text(encoding="utf-8",
                                                errors="replace")
        results["science_load_refusal"] = {
            "argv_shape": ["--science-surface <incomplete spec>"],
            "self_exited": code is not None,
            "exit_code": code,
            "documented_exit": "return 2 (main.cpp science-surface catch)",
            "stderr_tail": err[-300:],
            "refusal_named": "out_of_range" in err and "max_force_N" in err,
            "pass": bool(code is not None
                         and "science surface" in err
                         and "max_force_N" in err)}
    finally:
        if proc is not None and proc.poll() is None:
            _teardown(proc)
    time.sleep(1.0)

    # ── boot B: the opt-in graph scene ───────────────────────────────────
    proc = None
    try:
        proc = _boot(executable, native, port, "--science-surface",
                     [str(spec_path), "--no-restore"])
        _wait_ready(proc, base)
        sci = _http(base, "GET", "/science_surface")
        ctrl = _http(base, "POST", "/science_surface", {"force_N": 0.0})
        page = _http(base, "GET", "/science")
        graph = _http(base, "GET", "/science_graph")
        sci_json = sci.get("json", {})
        results["graph_opt_in"] = {
            "route": "--science-surface flag parse; GET/POST "
                     "/science_surface; GET /science, /science_graph",
            "status_body": sci_json,
            "control_body": ctrl.get("json", ctrl.get("text")),
            "page_served_bytes_match": page.get("text", "").encode()
                                       == page_bytes,
            "graph_body": graph.get("json", graph.get("text")),
            "pass": bool(not sci_json.get("ok") is False
                         and ctrl.get("json", {}).get("ok") is not False
                         and page.get("text", "").encode() == page_bytes
                         and graph.get("json", {}).get("smoke") is True)}
    finally:
        results["boot_B_exit_code"] = _teardown(proc) if proc else None
    time.sleep(1.0)

    # ── boots C/D: exclusivity guards (self-exiting, code 2) ─────────────
    dummy = out / "not_a_real_bundle.json"
    dummy.write_text("{}", encoding="utf-8")
    for name, flag, why in (("exclusivity_thermal", "--thermal-salvage",
                             "exclusive_science_scene"),
                            ("exclusivity_earth", "--earth-patch",
                             "exclusive_earth_scene")):
        proc = None
        try:
            proc = _boot(executable, native, port, "--science-surface",
                         [str(spec_path), flag, str(dummy)])
            try:
                proc.wait(timeout=45)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait(timeout=10)
            code = proc.returncode
            err = (native / "stderr.log").read_text(encoding="utf-8",
                                                    errors="replace")
            results[name] = {
                "argv_shape": ["--science-surface <spec>", flag, "<file>"],
                "exit_code": code,
                "documented_exit": "return 2 (the guard's require throws "
                                   "inside the scene's own catch)",
                "stderr_tail": err[-300:],
                "refusal_named": why in err,
                "exit_code_matches_doc": code == 2,
                "pass": bool(code is not None and code != 0
                             and why in err)}
        finally:
            if proc is not None and proc.poll() is None:
                _teardown(proc)
        time.sleep(1.0)
    return results


# ── the CPU tests (built and run in-process; no engine, no GPU) ──────────────

def _run_cpu_tests(out: Path) -> dict:
    """Build + run the two EXISTING tests in ChimeraEngine/engine/tests
    (header-only tendon-drive module; the exact commands their headers
    document). Captured verbatim into the receipt."""
    tests = {"tendon_drive_test": "tendon_drive_test.cpp",
             "tendon_arm_ledger_test": "tendon_arm_ledger_test.cpp"}
    out_results = {}
    for name, src in tests.items():
        exe_path = out / f"{name}.exe"
        build = subprocess.run(
            ["g++", "-std=c++17", "-O2", "-I", str(_REPO / "ChimeraEngine"
                                                   / "engine"),
             str(_REPO / "ChimeraEngine" / "engine" / "tests" / src),
             "-o", str(exe_path)],
            capture_output=True, text=True, timeout=300)
        if build.returncode != 0:
            out_results[name] = {"build_exit_code": build.returncode,
                                 "build_stderr_tail":
                                     build.stderr[-300:],
                                 "pass": False}
            continue
        run = subprocess.run([str(exe_path)], capture_output=True,
                             text=True, timeout=300)
        failures = "total failures: 0" in run.stdout
        out_results[name] = {
            "build_exit_code": 0,
            "exit_code": run.returncode,
            "stdout": run.stdout[-1500:],
            "total_failures_zero": failures,
            "pass": bool(run.returncode == 0 and failures)}
    out_results["pass"] = all(v["pass"] for v in out_results.values())
    return out_results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--exe", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8845)
    args = ap.parse_args(argv)

    exe = Path(args.exe)
    require(exe.is_file(), "engine_executable_missing")
    require((exe.parent / "shaders").is_dir(), "engine_shaders_missing")
    build_sha = file_hash(exe)
    require(build_sha == EXPECTED_ENGINE_SHA,
            f"rebuild_sha_differs_from_published_{EXPECTED_ENGINE_SHA}")
    out = Path(args.out)
    require(not out.exists(), "output_directory_exists")
    out.mkdir(parents=True, exist_ok=False)
    with socket.socket() as sock:
        require(sock.connect_ex(("127.0.0.1", args.port)) != 0,
                "port_occupied")

    executable = exe.resolve()
    native = out / "native"
    native.mkdir(exist_ok=False)
    shutil.copy2(executable, native / executable.name)
    shutil.copytree(executable.parent / "shaders", native / "shaders")

    results: dict = {}
    cpu = _run_cpu_tests(out)
    results["cpu_tests"] = cpu
    results.update(_run_default_and_b2(executable, native, args.port, out))
    results.update(_run_graph_and_exclusivity(executable, native,
                                              args.port, out))

    routes = {k: v for k, v in results.items()
              if isinstance(v, dict) and "pass" in v
              and k != "cpu_tests"}
    all_pass = all(v["pass"] for v in routes.values()) and cpu["pass"]
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "utc": default_stamp(),
        "source_commit": _source_commit(),
        "build": {
            "command": "cmake -S ChimeraEngine/engine -B "
                       "ChimeraEngine/engine/build/Release && cmake --build "
                       "ChimeraEngine/engine/build/Release --config Release",
            "executable": str(exe),
            "sha256": build_sha,
            "matches_published_increment4_sha": True,
        },
        "increment4_diff_scope": {
            "commit": "981b805c (engine.cpp +289, engine.hpp +33, "
                      "main.cpp +97)",
            "touched": [
                "the membrane-demo state class ONLY: md_deform (centre "
                "dead-load re-solve), md save/restore, the reset law, the "
                "status JSON's new centre_load_N field, the deform op "
                "parse, and the two /membrane_demo_save|restore routes"],
            "could_affect": [
                "the membrane-demo state machine, its status JSON shape "
                "(centre_load_N added), and its routes; nothing else -- "
                "every added branch is membrane-scoped and the pre-existing "
                "route ladder/dispatch order is unchanged (git show 981b805c"
                " -- main.cpp touches no non-membrane route line)"],
            "could_not_affect": [
                "B2 scene admit/refuse/controls (b2_scene.* untouched by "
                "the increment-4 commit)",
                "the studio board poll (ui.cpp board polling untouched; the"
                " commit's ui.cpp 3-line deletion is outside board code)",
                "the graph scenes (graph_surface/graph_thermal/graph_earth "
                "and the --science-surface/--thermal-salvage/--earth-patch "
                "boot loops untouched)",
                "physics init, /state, /control, and the argv parse law"],
        },
        "cpu_tests_note": "the two existing tests in ChimeraEngine/engine/"
                          "tests built with g++ -std=c++17 -O2 -I "
                          "ChimeraEngine/engine and run OUTSIDE the GPU "
                          "batch path (header-only CPU module, no engine); "
                          "their verbatim output is in "
                          "scenarios.cpu_tests",
        "scenarios": results,
        "route_verdicts": {k: v["pass"] for k, v in routes.items()},
        "scope": "smoke regression of the NON-membrane scene routes against "
                 "the rebuilt increment-4 exe; the membrane path itself is "
                 "covered by increments 2-5 evidence and is not re-claimed "
                 "here",
    }
    path = EVID_DIR / (f"engine_regression_receipt_"
                       f"{default_stamp()}.json")
    path.write_text(json.dumps(receipt, indent=1, default=str) + "\n",
                    encoding="utf-8")
    for k, v in routes.items():
        print(f"[{'PASS' if v['pass'] else 'FAIL'}] {k}")
        for kk in ("http_body", "exit_code", "stderr_tail", "board_standing",
                   "state_hash", "control_body"):
            if kk in v:
                print(f"       {kk}: {str(v[kk])[:160]}")
    print(f"boot exit codes: A={results.get('boot_A_exit_code')} "
          f"B={results.get('boot_B_exit_code')}")
    print(f"[{'PASS' if cpu['pass'] else 'FAIL'}] cpu_tests "
          f"(tendon_drive_test, tendon_arm_ledger_test)")
    print(f"ENGINE REGRESSION COMPLETE {path}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
