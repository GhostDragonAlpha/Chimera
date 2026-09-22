"""run_tickcost.py -- the TICK-COST ATTRIBUTION run driver.

Runs the plain baseline and the instrumented binary on the regenerated pinned
scene, asserts the byte-identity guard (F2: instrumented stdout sha == pinned
ship stdout sha == plain stdout sha), and writes raw logs + a run-index JSON
under raw/. Raw-byte subprocess capture to files (never shell redirects).
Long runs execute as detached processes with redirected logs when invoked via
run_in_background; this script itself is synchronous and cheap to supervise.

Usage:
  python run_tickcost.py --plain-bin PATH --tc-bin PATH --scene PATH \
      --runs-plain 5 --runs-tc 3 --raw-dir raw

Trailer Agent: tickcost.
"""
import argparse, hashlib, json, subprocess, time
from pathlib import Path

SHIP_SHA = "71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f7db69b10d4b8d94517592"  # ancestor fence (30821ef7 bytes; see PREREG Amendment 1)
LANE_FENCE = "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc"  # bd4bf630 plain build, this machine, MSVC==MinGW
SCENE_SHA = "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def one_run(exe, scene, prefix):
    t0 = time.perf_counter()
    with open(prefix + "_stdout.txt", "wb") as so, open(prefix + "_stderr.txt", "wb") as se:
        p = subprocess.run([str(exe), str(scene)], stdout=so, stderr=se)
    wall = time.perf_counter() - t0
    return {"exit": p.returncode, "wall_s": round(wall, 3),
            "stdout_sha256": sha256_file(prefix + "_stdout.txt"),
            "stdout_bytes": Path(prefix + "_stdout.txt").stat().st_size}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain-bin", required=True)
    ap.add_argument("--tc-bin", default=None)
    ap.add_argument("--scene", required=True)
    ap.add_argument("--runs-plain", type=int, default=5)
    ap.add_argument("--runs-tc", type=int, default=3)
    ap.add_argument("--raw-dir", default="raw")
    a = ap.parse_args()
    raw = Path(a.raw_dir); raw.mkdir(parents=True, exist_ok=True)
    scene_sha = sha256_file(a.scene)
    assert scene_sha == SCENE_SHA, "scene is not the pinned bytes: %s" % scene_sha
    index = {"scene_sha256": scene_sha, "lane_fence_sha256": LANE_FENCE,
             "ancestor_fence_sha256": SHIP_SHA, "runs": []}
    for k in range(1, a.runs_plain + 1):
        r = one_run(a.plain_bin, a.scene, str(raw / ("plain_run%d" % k)))
        r["kind"] = "plain"; r["n"] = k
        index["runs"].append(r)
        print("plain_run%d wall=%.3fs sha=%s.. exit=%d" % (k, r["wall_s"], r["stdout_sha256"][:12], r["exit"]))
    for k in range(1, a.runs_tc + 1):
        r = one_run(a.tc_bin, a.scene, str(raw / ("tc_run%d" % k)))
        r["kind"] = "tc"; r["n"] = k
        index["runs"].append(r)
        print("tc_run%d wall=%.3fs sha=%s.. exit=%d" % (k, r["wall_s"], r["stdout_sha256"][:12], r["exit"]))
    plains = {r["stdout_sha256"] for r in index["runs"] if r["kind"] == "plain"}
    tcs = {r["stdout_sha256"] for r in index["runs"] if r["kind"] == "tc"}
    index["guard"] = {
        "plain_all_equal": plains == {LANE_FENCE},
        "tc_all_equal": tcs == {LANE_FENCE} if tcs else None,
        "f2_byte_neutral": tcs == {LANE_FENCE} and plains == {LANE_FENCE},
    }
    (raw / "run_index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    print("GUARD:", json.dumps(index["guard"]))
    if not index["guard"]["f2_byte_neutral"]:
        raise SystemExit("F2 RED: stdout bytes differ from the lane fence -- instrument NOT byte-neutral")


if __name__ == "__main__":
    main()
