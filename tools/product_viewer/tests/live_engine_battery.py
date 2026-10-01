"""Build the engine with the W2 lane's recipe, then run the viewer battery.

wk-play-live 2026-10-01. Run from a checkout/package root:

    python -B tools/product_viewer/tests/live_engine_battery.py

Steps:
1. cmake configure + Release build of ChimeraEngine/engine (exit-checked;
   the exact W2 lane build path, ENGINE_UP_RECEIPT.md).
2. Verify the sealed W2 payload pins on disk (tile ab76eec6..., body
   012b8b33...); a mismatch is a named BLOCKED, never a silent skip.
3. Run the tools.product_viewer.tests suite with CHIMERA_LIVE_ENGINE_EXE /
   CHIMERA_LIVE_TILE_PATH / CHIMERA_LIVE_BODY_PATH set, so the gated
   EngineUpIntegration class REALLY runs: engine up, proven payloads
   ingested, engine pixels served, kill-falsifier measured.
4. Write a receipt JSON (build tails, exe identity, payload identities,
   per-test outcomes incl. skips) to CHIMERA_OUTPUT_DIR (or CWD).

Exit codes: 0 build+battery green AND engine-up verified; 2 build or test
failure; 3 engine-up battery did not verify (missing marker). Skipped tests
are listed in the receipt and never silently dropped.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENGINE_SRC = ROOT / "ChimeraEngine" / "engine"
# The build lives OUTSIDE the runner scratch: cmake configure churns tens of
# thousands of probe files, and the runner's ~100 ms scratch-budget poller
# races exactly that churn (observed twice: WinError 3 on a test tempdir, then
# WinError 2 on a CompilerIdCXX .tlog mid-configure, jobs abefceecec25407998
# / 8139ae37469d4ba0bdd7a57307014030). A stable host-side build dir makes the
# scratch tree static for the poller; declared outputs are COPIED back into
# CHIMERA_OUTPUT_DIR.
BUILD_DIR = Path(os.environ.get("CHIMERA_LIVE_BUILD_DIR")
                 or (Path.home() / ".chimera-live-tmp" / "engine-build"))
EXE = BUILD_DIR / "Release" / "chimera_engine.exe"
SEALED_TILE = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike/tile_mesh_meshbin.bin")
SEALED_BODY = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike/body_tick10_skinbin.bin")
# These pins MUST match tools/product_viewer/server.py (checked below).
TILE_SHA = "ab76eec64b5cf608afb036f82bcd1a5cff500165a24ed8db87e7b2647b976ea3"
BODY_SHA = "012b8b330f4dda814fe3a4622a8cd0382b981492590ae5adcdd8ab182cc926eb"


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    sys.path.insert(0, str(ROOT))
    # The runner's scratch-budget poller walks scratch every ~100 ms while the
    # unittest tempdirs are created+deleted inside scratch/tmp (the runner sets
    # TMP there); a dir vanishing mid-walk kills the job (observed:
    # WinError 3 on scratch/tmp/viewer_cert_*, job abefceecec25407998b7e60ed38d078d).
    # Point the suite's tempdirs at a STABLE host dir OUTSIDE the runner
    # scratch; tests still clean up after themselves.
    tmpbase = Path(os.environ.get("CHIMERA_LIVE_TMPBASE")
                   or (Path.home() / ".chimera-live-tmp"))
    tmpbase.mkdir(parents=True, exist_ok=True)
    for var in ("TMP", "TEMP", "TMPDIR"):
        os.environ[var] = str(tmpbase)
    receipt: dict = {"schema": "chimera.viewer.live_battery.v1",
                     "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
                     "base_sha": os.environ.get("CHIMERA_BASE_SHA"),
                     "root": str(ROOT), "tmpbase": str(tmpbase)}

    # -- pin cross-check ----------------------------------------------------
    from tools.product_viewer import server as pv
    receipt["pin_crosscheck"] = {
        "tile": pv.LIVE_TILE_SHA256 == TILE_SHA,
        "body": pv.LIVE_BODY_SHA256 == BODY_SHA,
    }
    if not all(receipt["pin_crosscheck"].values()):
        print(json.dumps({"state": "BLOCKED",
                          "error": "payload pins disagree between battery and server.py"},
                         indent=2))
        return 2

    # -- payload identity on disk -------------------------------------------
    missing = [str(p) for p in (SEALED_TILE, SEALED_BODY) if not p.is_file()]
    if missing:
        print(json.dumps({"state": "BLOCKED",
                          "error": f"sealed W2 payload(s) missing: {missing}"}, indent=2))
        return 2
    tile_sha, body_sha = sha_file(SEALED_TILE), sha_file(SEALED_BODY)
    receipt["payloads"] = {
        "tile": {"path": str(SEALED_TILE), "sha256": tile_sha,
                 "bytes": SEALED_TILE.stat().st_size,
                 "matches_pin": tile_sha == TILE_SHA},
        "body": {"path": str(SEALED_BODY), "sha256": body_sha,
                 "bytes": SEALED_BODY.stat().st_size,
                 "matches_pin": body_sha == BODY_SHA},
    }
    if not (receipt["payloads"]["tile"]["matches_pin"]
            and receipt["payloads"]["body"]["matches_pin"]):
        print(json.dumps({"state": "BLOCKED",
                          "error": "sealed payload on disk does not match the pin",
                          "payloads": receipt["payloads"]}, indent=2))
        return 2

    # -- build the engine (the W2 lane's path) ------------------------------
    t0 = time.monotonic()
    conf = subprocess.run(["cmake", "-S", str(ENGINE_SRC), "-B", str(BUILD_DIR)],
                          capture_output=True, text=True, timeout=900)
    build = subprocess.run(["cmake", "--build", str(BUILD_DIR), "--config", "Release"],
                           capture_output=True, text=True, timeout=1800)
    receipt["build"] = {
        "configure_exit": conf.returncode,
        "build_exit": build.returncode,
        "seconds": round(time.monotonic() - t0, 1),
        "tail": (build.stdout[-2000:] + build.stderr[-1000:]),
    }
    print(receipt["build"]["tail"][-800:])
    if conf.returncode != 0 or build.returncode != 0 or not EXE.is_file():
        receipt["state"] = "BUILD_FAILED"
        _write(receipt)
        print(json.dumps({"state": "BUILD_FAILED",
                          "configure_exit": conf.returncode,
                          "build_exit": build.returncode,
                          "exe_present": EXE.is_file()}, indent=2))
        return 2
    receipt["engine_exe"] = {"path": str(EXE), "bytes": EXE.stat().st_size,
                             "sha256": sha_file(EXE)}
    out_dir = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or Path.cwd())
    try:
        (out_dir / "chimera_engine_battery.exe").write_bytes(EXE.read_bytes())
        receipt["engine_exe"]["copied_to_outputs"] = True
    except OSError as e:
        receipt["engine_exe"]["copied_to_outputs"] = f"copy failed: {e}"

    # -- run the suite with the gate set ------------------------------------
    os.environ["CHIMERA_LIVE_ENGINE_EXE"] = str(EXE)
    os.environ["CHIMERA_LIVE_TILE_PATH"] = str(SEALED_TILE)
    os.environ["CHIMERA_LIVE_BODY_PATH"] = str(SEALED_BODY)
    loader = unittest.defaultTestLoader
    suite = loader.discover(str(ROOT / "tools" / "product_viewer" / "tests"),
                            pattern="test_*.py")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    receipt["unittest"] = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": [{"test": str(test_id), "reason": reason}
                    for test_id, reason in result.skipped],
    }
    for case, _ in list(result.failures) + list(result.errors):
        print(f"FAILED: {case}", flush=True)

    # -- the engine-up marker must exist ------------------------------------
    marker = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or Path.cwd())
    receipt["engine_up_verified"] = (marker / "live_ingest_result.json").is_file() \
        and (marker / "live_kill_flip.json").is_file()
    green = (result.wasSuccessful() and receipt["engine_up_verified"]
             and not receipt["unittest"]["skipped"])
    receipt["state"] = ("PASSED" if green else
                        "PASSED_WITH_SKIPS" if result.wasSuccessful() else "FAILED")
    receipt["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _write(receipt)
    print(json.dumps({k: receipt[k] for k in
                      ("state", "unittest", "engine_up_verified", "engine_exe")},
                     indent=2))
    if not result.wasSuccessful():
        return 2
    if not receipt["engine_up_verified"]:
        return 3
    return 0


def _write(receipt: dict) -> None:
    out = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or Path.cwd())
    try:
        (out / "live_battery_receipt.json").write_text(
            json.dumps(receipt, indent=1), encoding="utf-8")
    except OSError as e:
        print(f"receipt write failed: {e}", flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
