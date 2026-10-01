"""The CERT-DRYRUN pipeline: the FIRST production-class compatibility certificate.

The snapshot-apis lane's named successors (a)+(b) as ONE end-to-end issuance,
on EXISTING machinery only (the out-of-tree instrument pattern; zero engine
edits). Lane of record: tools/science_funnel/validation/cert_dryrun_20260920/
(receipt.json is the Rule-0 law; frozen rule_0 sha in the receipt).

  (1) IDENTITY -- the 5-tuple's physics_build binds the REAL engine build the
      instrument compiles against: the source closure shas (dormancy-proven:
      stripping every #ifdef GAIT_SNAPSHOT_API block from the copied
      gait_controller.hpp equals the shipped bytes), the harness sha, the
      compiled binary stamp, the scene pin, and the ship-byte anchors. This is
      "instrument build, ship-fenced" -- the strongest identity available
      WITHOUT an engine-provided build id (that is the named forward gap).
  (2) CHECKS 1-3 ON THE ENGINE WALK PATH through the certificate path:
      CHECK 1 same-build replay + checkpoint-resume bit-identity at T=150 (the
      certificate's replay evidence IS the proof: per-tick state hashes of the
      walk of record, hash-chained per certificate.verify_evidence_chain);
      CHECK 2 cross-build equivalence on the registered cases (fresh recompile,
      byte-irrelevant: binary stamps may differ, walk artifacts may not);
      CHECK 3 closed-loop requalification shape (engine leg closed-loop with
      the action-replay refusal; actor leg = the frozen dummy actor through the
      upgate check 3, unchanged).
  (3) ISSUANCE -- production class, validator recomputes everything from
      bytes; deploy gate checks.
  (4) NEGATIVE CONTROLS -- tampered re-issues must be REJECTED (T1 bumped
      state hash / T2 swapped normalization constant / T3 stale build id);
      the clean re-issue must validate (no false positive).

Conventions frozen in the prereg: state hash = sha256(canonical 4-class
serialization body, one per tick); initial snapshot = the tick-0 state hash;
events = ticks 1..N-1 chained; trajectory = the last_torque_ action bytes.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

from . import SCHEMA_VERSION
from .certificate import (canonical_json, cert_hash, check_deploy, compat_key,
                          issue_certificate, sha256_hex, validate_certificate)
from . import snapshot_api
from .runner import (PolicyCompatError, build_corpus, check3, load_bundle,
                     requalify)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE = os.path.join(REPO, "tools", "science_funnel", "validation", "cert_dryrun_20260920")
SNAP_LANE = os.path.join(REPO, "tools", "science_funnel", "validation", "snapshot_apis_20260920")
TMP = os.path.join(REPO, ".tmp", "certdry")
SCENE = os.path.join(TMP, "gait-walker", "scene.json")
CHECKPOINT_TICK = 150
RC2_SCHEDULE = "150:1.01"
SUITE_ID = "cert_dryrun_20260920/registered_cases_v1"
ISSUED_BY = "cert-dryrun-20260920 lane agent (Agent: certdry)"
BASE_COMMIT = "f6787ebe"
PREREG = "tools/science_funnel/validation/cert_dryrun_20260920/receipt.json"

ANCHORS = {
    "scene_sha256": "f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342",
    "ship_stdout_sha256": "8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc",
    "ship_trace_stderr_sha256": "c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481",
    "ship_plain_stderr_sha256": "b505bb65652c2b796c163899ec51b7e5268342e5d31f28a9603fc2ab6c2d72ab",
}
WALK_FACE = {"refused_tick": 302, "refused_class": "gait_positional_correction_budget"}
DROP_CLASSES = ("world_state", "contact_warm_start", "reflex_state", "controller_history")

CLOSURE_FILES = (
    "engine/gait_controller.hpp",
    "engine/coupled_articulation.hpp",
    "engine/earth_environment.hpp",
    "engine/force_models.hpp",
    "engine/tests_coupled_arm/gait_snap.cpp",
    "engine/tests_coupled_arm/gait_unit.cpp",
    "native/viewer3rd/json.hpp",
)

# shipped-tree counterpart of each closure file (the dormancy comparison target)
SHIPPED_COUNTERPART = {
    "engine/gait_controller.hpp": "ChimeraEngine/engine/gait_controller.hpp",
    "engine/coupled_articulation.hpp": "ChimeraEngine/engine/coupled_articulation.hpp",
    "engine/earth_environment.hpp": "ChimeraEngine/engine/earth_environment.hpp",
    "engine/force_models.hpp": "ChimeraEngine/engine/force_models.hpp",
    "engine/tests_coupled_arm/gait_snap.cpp": "ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp",
    "engine/tests_coupled_arm/gait_unit.cpp": "ChimeraEngine/engine/tests_coupled_arm/gait_unit.cpp",
    "native/viewer3rd/json.hpp": "ChimeraEngine/native/viewer3rd/json.hpp",
}


class CertDryRunError(Exception):
    pass


def rd(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def rj(path: str) -> dict:
    return json.loads(rd(path).decode("utf-8"))


def wj(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def exe_paths() -> dict:
    return {"A": os.path.join(TMP, "instA", "Release", "gait_snap.exe"),
            "B": os.path.join(TMP, "instB", "Release", "gait_snap.exe")}


def inst_dir() -> str:
    return os.path.join(SNAP_LANE, "instrument", "native", "ChimeraEngine")


# ------------------------------------------------------------------ identity

def _strip_snapshot_api(text: str) -> str:
    """Remove every '#ifdef GAIT_SNAPSHOT_API .. #endif' region (nesting-aware
    over any conditional stack inside the removed regions)."""
    out: list[str] = []
    stack: list[str] = []          # active preprocessor conditions, source order
    removing = 0                   # depth of GAIT_SNAPSHOT_API guards being removed
    cond = re.compile(r"^\s*#\s*(ifdef|ifndef|if)\b(.*)$")
    end = re.compile(r"^\s*#\s*endif\b")
    for line in text.splitlines(keepends=True):
        m = cond.match(line)
        if removing == 0 and m and m.group(1) == "ifdef" \
                and "GAIT_SNAPSHOT_API" in m.group(2):
            removing = 1           # this guard's region is dropped
            continue
        if removing > 0:
            if m:
                stack.append(m.group(1))
            elif end.match(line):
                if stack:
                    stack.pop()
                else:
                    removing = 0   # matching endif of the dropped guard
            continue
        out.append(line)
    return "".join(out)


def _content_lines(text: str) -> list[str]:
    """Non-blank lines (blank-line-only deltas carry no C++ preprocessing
    weight; the count of such artifacts is reported beside the verdict)."""
    return [l for l in text.splitlines() if l.strip()]


def engine_identity() -> dict:
    """The physics build identity: source closure + dormancy proof + binary
    stamps + scene pin + ship anchors. F3: this is 'instrument build,
    ship-fenced' -- the strongest identity without an engine-provided id."""
    nat = inst_dir()
    closure = []
    dormancy_ok = True
    dormancy_notes = []
    for rel in CLOSURE_FILES:
        p = os.path.normpath(os.path.join(nat, rel))
        b = rd(p)
        closure.append([rel.replace("\\", "/"), sha256_hex(b)])
        ship_p = os.path.join(REPO, SHIPPED_COUNTERPART[rel])
        if rel.endswith("gait_controller.hpp"):
            stripped = _strip_snapshot_api(b.decode("utf-8"))
            ship_lf = rd(ship_p).decode("utf-8").replace("\r\n", "\n")
            blank_delta = len(stripped.splitlines()) - len(ship_lf.splitlines())
            ok = _content_lines(stripped) == _content_lines(ship_lf)
            dormancy_ok = dormancy_ok and ok
            dormancy_notes.append("gait_controller.hpp: stripped copy == shipped bytes on every "
                                  f"non-blank line ({'OK' if ok else 'MISMATCH'}; blank-line-only "
                                  f"artifacts outside the guards: {blank_delta})")
        elif rel.endswith("gait_snap.cpp"):
            # handled separately below (the harness = gait_unit.cpp + instrument blocks)
            continue
        else:
            ok = sha256_hex(b) == sha256_hex(rd(ship_p))
            dormancy_ok = dormancy_ok and ok
            dormancy_notes.append(f"{os.path.basename(rel)}: byte-equal to shipped ({'OK' if ok else 'MISMATCH'})")
    # gait_snap.cpp = gait_unit.cpp + instrument blocks only
    gs = rd(os.path.join(nat, "engine", "tests_coupled_arm", "gait_snap.cpp")).decode("utf-8")
    gu = rd(os.path.join(REPO, "ChimeraEngine", "engine", "tests_coupled_arm",
                         "gait_unit.cpp")).decode("utf-8")
    gs_strip = _strip_snapshot_api(gs).replace("\r\n", "\n")
    gu_lf = gu.replace("\r\n", "\n")
    harness_ok = gs_strip == gu_lf
    dormancy_ok = dormancy_ok and harness_ok
    dormancy_notes.append("gait_snap.cpp: instrument blocks stripped == shipped gait_unit.cpp "
                          f"({'OK' if harness_ok else 'MISMATCH'})")

    scene_sha = sha256_hex(rd(SCENE))
    if scene_sha != ANCHORS["scene_sha256"]:
        raise CertDryRunError(f"scene pin mismatch: {scene_sha}")
    exes = exe_paths()
    stamps = {k: sha256_hex(rd(v)) for k, v in exes.items() if os.path.exists(v)}
    id_src = {"closure": closure, "harness": closure[4][1], "scene_pin": scene_sha}
    id16 = sha256_hex(canonical_json(id_src))[:16]
    tool = _toolchain()
    return {
        "build_id": f"engine-walk-instrument/{id16}",
        "kind": "out-of-tree snapshot instrument build, ship-fenced (NO engine-provided build id exists: forward gap)",
        "engine_source_closure_sha256": sha256_hex(canonical_json(closure)),
        "closure": closure,
        "instrument_harness_sha256": closure[4][1],
        "instrument_dormancy": {"pass": dormancy_ok, "checks": dormancy_notes,
                                "rule": "shipped-tree diff confined to #ifdef GAIT_SNAPSHOT_API blocks; "
                                        "flag-off preprocessing == shipped bytes"},
        "binary_stamps": stamps,
        "binary_stamp_bound_to_evidence": stamps.get("A"),
        "second_build_stamp": stamps.get("B"),
        "byte_irrelevance_claim": "build B is an independent configure+compile; its stamp MAY differ; "
                                  "the walk artifacts may not (CHECK 2)",
        "toolchain": tool,
        "scene_pin_sha256": scene_sha,
        "scene": "tools/science_funnel/gait_scene.py (fore_share 0.45 default), tick_hz 300, dt=1/300 s",
        "ship_anchor_bindings": dict(ANCHORS),
        "walk_of_record_face": dict(WALK_FACE),
        "checkpoint_tick": CHECKPOINT_TICK,
        "timestep_s": 1.0 / 300.0,
    }


def _toolchain() -> dict:
    import glob
    out = {}
    for tag, build in (("A", os.path.join(TMP, "instA")), ("B", os.path.join(TMP, "instB"))):
        caches = glob.glob(os.path.join(build, "CMakeFiles", "*", "CMakeCXXCompiler.cmake"))
        gen = os.path.join(build, "CMakeCache.txt")
        if caches:
            txt = rd(caches[0]).decode("utf-8", errors="replace")
            ver = re.search(r'set\(CMAKE_CXX_COMPILER_VERSION "(.+?)"\)', txt)
            comp = re.search(r'set\(CMAKE_CXX_COMPILER "(.+?)"\)', txt)
            cid = re.search(r'set\(CMAKE_CXX_COMPILER_ID "(.+?)"\)', txt)
            out[f"build_{tag}_compiler"] = comp.group(1).strip() if comp else None
            out[f"build_{tag}_compiler_id"] = cid.group(1).strip() if cid else None
            out[f"build_{tag}_compiler_version"] = ver.group(1).strip() if ver else None
        if os.path.exists(gen):
            gtxt = rd(gen).decode("utf-8", errors="replace")
            g = re.search(r"CMAKE_GENERATOR:INTERNAL=(.+)", gtxt)
            out[f"build_{tag}_generator"] = g.group(1).strip() if g else None
    return out


# --------------------------------------------------------------- run workers

def run_walk(tag: str, runs_dir: str, build: str, mode_args: list[str],
             plain_argv2: str | None = None) -> dict:
    """One FRESH-process instrument execution; raw-byte artifacts only."""
    exe = exe_paths()[build]
    if not os.path.exists(exe):
        raise CertDryRunError(f"missing instrument exe for build {build}: {exe}")
    argv = [exe]
    if plain_argv2 is None:
        argv += ["--snap-api", SCENE, *mode_args]
    else:
        argv += [SCENE, plain_argv2]
    so = os.path.join(runs_dir, tag + ".stdout")
    se = os.path.join(runs_dir, tag + ".stderr")
    os.makedirs(runs_dir, exist_ok=True)
    # cwd = the run dir: the plain harness's end-of-suite snap_finish writes
    # its (empty-prefix) recordings into the process cwd -- keep the repo root
    # and other runs untouched. All file arguments are absolute.
    with open(so, "wb") as f1, open(se, "wb") as f2:
        p = subprocess.run(argv, stdout=f1, stderr=f2, cwd=runs_dir,
                           timeout=600, capture_output=False)
    if p.returncode != 0:
        raise CertDryRunError(f"walk run {tag} failed exit={p.returncode}: {argv}")
    return {"tag": tag, "build": build, "argv_tail": argv[1:], "exit": p.returncode}


def load_run(tag: str, runs_dir: str) -> dict:
    states = rd(os.path.join(runs_dir, tag + ".states.bin"))
    actions = rd(os.path.join(runs_dir, tag + ".actions.bin"))
    meta = rj(os.path.join(runs_dir, tag + ".run.json"))
    body = meta["body_bytes"]
    if len(states) % body:
        raise CertDryRunError(f"{tag}: states not a multiple of body")
    n = len(states) // body
    return {"tag": tag, "states": states, "actions": actions, "meta": meta,
            "body": body, "n": n,
            "hashes": [sha256_hex(states[i * body:(i + 1) * body]) for i in range(n)],
            "stdout": rd(os.path.join(runs_dir, tag + ".stdout")),
            "stderr": rd(os.path.join(runs_dir, tag + ".stderr"))}


# ------------------------------------------------------------------- CHECK 1

def check1(runs_dir: str) -> tuple[dict, dict]:
    """Same-build replay + checkpoint-resume bit-identity, fresh processes.
    Returns (report, ref1) -- ref1 carries the walk-of-record evidence."""
    run_walk("refA1", runs_dir, "A", ["ref", os.path.join(runs_dir, "refA1"), str(CHECKPOINT_TICK)])
    run_walk("refA2", runs_dir, "A", ["ref", os.path.join(runs_dir, "refA2"), str(CHECKPOINT_TICK)])
    run_walk("resA", runs_dir, "A", ["restore", os.path.join(runs_dir, "resA"),
                                     str(CHECKPOINT_TICK),
                                     os.path.join(runs_dir, "refA1.snap_t150.bin")])
    r1 = load_run("refA1", runs_dir)
    r2 = load_run("refA2", runs_dir)
    rs = load_run("resA", runs_dir)

    reasons = []
    replay = (r1["states"] == r2["states"] and r1["actions"] == r2["actions"]
              and r1["stdout"] == r2["stdout"] and r1["stderr"] == r2["stderr"]
              and rd(os.path.join(runs_dir, "refA1.snap_t150.bin"))
              == rd(os.path.join(runs_dir, "refA2.snap_t150.bin")))
    if not replay:
        reasons.append("replay runs differ")

    # the exercised ship fence, re-measured on THIS lane's binary
    fence = {
        "stdout": {"anchor": ANCHORS["ship_stdout_sha256"],
                   "measured": sha256_hex(r1["stdout"]),
                   "pass": sha256_hex(r1["stdout"]) == ANCHORS["ship_stdout_sha256"]},
        "trace_stderr": {"anchor": ANCHORS["ship_trace_stderr_sha256"],
                         "measured": sha256_hex(r1["stderr"]),
                         "pass": sha256_hex(r1["stderr"]) == ANCHORS["ship_trace_stderr_sha256"]},
    }
    if not (fence["stdout"]["pass"] and fence["trace_stderr"]["pass"]):
        reasons.append("ship fence legs moved")

    # the walk of record's face
    face_ok = (r1["meta"]["refused_tick"] == WALK_FACE["refused_tick"]
               and r1["meta"]["refused_class"] == WALK_FACE["refused_class"])
    if not face_ok:
        reasons.append("walk face moved")

    # checkpoint: the T=150 snapshot body IS the reference's tick-150 state
    snap_raw = rd(os.path.join(runs_dir, "refA1.snap_t150.bin"))
    snap_body = snap_raw[40:]
    snap_ok = snap_body == r1["states"][CHECKPOINT_TICK * r1["body"]:(CHECKPOINT_TICK + 1) * r1["body"]]
    if not snap_ok:
        reasons.append("snapshot body != reference tick-150 serialization")

    # F1 through the certificate path: the restored future == the uninterrupted tail
    m = rs["meta"]
    first_div = None
    if rs["n"] != r1["n"] - CHECKPOINT_TICK:
        reasons.append(f"restore n_states {rs['n']} != expected {r1['n'] - CHECKPOINT_TICK}")
    for k in range(min(rs["n"], r1["n"] - CHECKPOINT_TICK)):
        if rs["hashes"][k] != r1["hashes"][CHECKPOINT_TICK + k]:
            first_div = CHECKPOINT_TICK + k
            break
    actions_identical = rs["actions"] == r1["actions"][CHECKPOINT_TICK * 144:]
    refusal_ok = (m["refused_tick"] == r1["meta"]["refused_tick"]
                  and m["refused_class"] == r1["meta"]["refused_class"])
    bit_identity = (first_div is None and actions_identical and refusal_ok
                    and m["blind_matches_file"] and m["roundtrip_ok"])
    if not bit_identity:
        reasons.append(f"restore drift: first_div={first_div} actions={actions_identical} "
                       f"refusal={refusal_ok} blind={m['blind_matches_file']} roundtrip={m['roundtrip_ok']}")

    # forced drops re-measured on THIS binary (load-bearing readers)
    probes = {}
    for cls in DROP_CLASSES:
        tag = "drop_" + cls
        run_walk(tag, runs_dir, "A", ["probe", os.path.join(runs_dir, tag),
                                      str(CHECKPOINT_TICK),
                                      os.path.join(runs_dir, "refA1.snap_t150.bin"), cls])
        pr = load_run(tag, runs_dir)
        moved = pr["states"] != r1["states"][CHECKPOINT_TICK * r1["body"]:]
        first_div_p = None
        for k in range(min(pr["n"], r1["n"] - CHECKPOINT_TICK)):
            if pr["hashes"][k] != r1["hashes"][CHECKPOINT_TICK + k]:
                first_div_p = CHECKPOINT_TICK + k
                break
        probes[cls] = {"moved_continuation": bool(moved or pr["actions"] != r1["actions"][CHECKPOINT_TICK * 144:]),
                       "first_diverging_tick": first_div_p,
                       "roundtrip_ok": pr["meta"]["roundtrip_ok"],
                       "n_states": pr["n"]}
        if not (moved or pr["actions"] != r1["actions"][CHECKPOINT_TICK * 144:]):
            reasons.append(f"forced drop {cls} did NOT move the continuation")

    # no NaN/Inf in any serialized f64 field of the walk of record
    nan_free, nan_fields = dump_nan_free(runs_dir)

    passed = not reasons and nan_free
    report = {
        "check": "CHECK_1_engine_same_build_replay_and_checkpoint_resume",
        "pass": passed, "reasons": reasons,
        "replay_byte_identical": replay,
        "ref_runs": [{"states_sha256": sha256_hex(r["states"]),
                      "actions_sha256": sha256_hex(r["actions"]),
                      "stdout_sha256": sha256_hex(r["stdout"]),
                      "stderr_sha256": sha256_hex(r["stderr"])} for r in (r1, r2)],
        "ship_fence_legs": fence,
        "walk_face": {"refused_tick": r1["meta"]["refused_tick"],
                      "refused_class": r1["meta"]["refused_class"],
                      "n_states": r1["n"], "body_bytes": r1["body"],
                      "identical_to_ship_face": face_ok},
        "checkpoint": {"tick": CHECKPOINT_TICK,
                       "snapshot_sha256": sha256_hex(snap_raw),
                       "body_is_reference_tick150": snap_ok},
        "restore_bit_identity": {"pass": bit_identity,
                                 "first_diverging_tick": first_div,
                                 "state_hashes_identical": first_div is None,
                                 "action_bytes_identical": actions_identical,
                                 "action_bytes_compared": len(rs["actions"]),
                                 "ticks_compared": rs["n"],
                                 "blind_phase_matches_snapshot_file": m["blind_matches_file"],
                                 "roundtrip_serialization_equal": m["roundtrip_ok"],
                                 "refusal_tick_and_class_identical": refusal_ok},
        "forced_drops": probes,
        "dump_nan_free": {"pass": nan_free, "checked_fields": nan_fields},
        "detail": (f"fresh-process replay {'IDENTICAL' if replay else 'DIFFERS'}; restore at "
                   f"T={CHECKPOINT_TICK} {'BIT-IDENTICAL' if bit_identity else 'DRIFTED'} on "
                   f"{rs['n']} ticks + {len(rs['actions'])} action bytes; ship fence "
                   f"stdout/trace {'EXACT' if fence['stdout']['pass'] and fence['trace_stderr']['pass'] else 'MOVED'}; "
                   f"all 4 forced drops moved the continuation: "
                   f"{all(p['moved_continuation'] for p in probes.values())}"),
    }
    wj(os.path.join(runs_dir, "check1_report.json"), report)
    return report, r1


def dump_nan_free(runs_dir: str) -> tuple[bool, int]:
    """Every f64 field of every serialized tick of refA1 must be finite."""
    import struct
    man = rj(os.path.join(SNAP_LANE, "runs", "ref1.manifest.json"))
    f64 = [(f["offset"], f["count"]) for f in man if f["kind"] == "f64"]
    states = rd(os.path.join(runs_dir, "refA1.states.bin"))
    meta = rj(os.path.join(runs_dir, "refA1.run.json"))
    body = meta["body_bytes"]
    n = len(states) // body
    bad = 0
    inf = float("inf")
    for i in range(n):
        rec = states[i * body:(i + 1) * body]
        for off, cnt in f64:
            for v in struct.unpack_from(f"<{cnt}d", rec, off):
                if v != v or v == inf or v == -inf:
                    bad += 1
    return bad == 0, len(f64) * n


# ------------------------------------------------------------------- CHECK 2

def check2(runs_dir: str, r1: dict) -> dict:
    """Cross-build equivalence: fresh recompile (build B), exact agreement on
    the registered cases."""
    reasons = []
    run_walk("refB1", runs_dir, "B", ["ref", os.path.join(runs_dir, "refB1"), str(CHECKPOINT_TICK)])
    rb = load_run("refB1", runs_dir)
    rc1 = {
        "case": "RC-1_ship_walk",
        "legs": {
            "states.bin": rb["states"] == r1["states"],
            "actions.bin": rb["actions"] == r1["actions"],
            "snap_t150.bin": rd(os.path.join(runs_dir, "refB1.snap_t150.bin"))
            == rd(os.path.join(runs_dir, "refA1.snap_t150.bin")),
            "stdout": rb["stdout"] == r1["stdout"],
            "stderr": rb["stderr"] == r1["stderr"],
            "run.json_face": (rb["meta"]["refused_tick"], rb["meta"]["refused_class"])
            == (r1["meta"]["refused_tick"], r1["meta"]["refused_class"]),
        },
    }
    rc1["exact_agreement"] = all(rc1["legs"].values())
    if not rc1["exact_agreement"]:
        reasons.append("RC-1 cross-build disagreement: "
                       + ",".join(k for k, v in rc1["legs"].items() if not v))

    # RC-2: pinned command schedule through the plain harness (the command adapter)
    run_walk("rc2A", runs_dir, "A", [], plain_argv2=RC2_SCHEDULE)
    run_walk("rc2B", runs_dir, "B", [], plain_argv2=RC2_SCHEDULE)
    a_out = rd(os.path.join(runs_dir, "rc2A.stdout"))
    a_err = rd(os.path.join(runs_dir, "rc2A.stderr"))
    b_out = rd(os.path.join(runs_dir, "rc2B.stdout"))
    b_err = rd(os.path.join(runs_dir, "rc2B.stderr"))
    rc2 = {"case": "RC-2_pinned_command_zoh", "schedule": RC2_SCHEDULE,
           "legs": {"stdout": a_out == b_out, "trace_stderr": a_err == b_err},
           "stdout_sha256": sha256_hex(a_out), "trace_stderr_sha256": sha256_hex(a_err),
           "fg42_echo_present": b"F-G42 command_spec=" in a_out}
    rc2["exact_agreement"] = all(rc2["legs"].values())
    if not rc2["exact_agreement"]:
        reasons.append("RC-2 cross-build disagreement")
    passed = not reasons
    stamp_a, stamp_b = sha256_hex(rd(exe_paths()["A"])), sha256_hex(rd(exe_paths()["B"]))
    report = {
        "check": "CHECK_2_cross_build_equivalence_registered_cases",
        "pass": passed, "reasons": reasons,
        "build_A_binary_sha256": stamp_a,
        "build_B_binary_sha256": stamp_b,
        "binary_stamps_differ": stamp_a != stamp_b,
        "registered_cases": [rc1, rc2],
        "honesty_note": "byte-irrelevant rebuild: the two builds' binary stamps MAY differ; "
                        "the registered cases' artifacts must not. Exact agreement on the "
                        "registered cases is EVIDENCE, never universal proof.",
        "detail": (f"fresh recompile: RC-1 {'EXACT' if rc1['exact_agreement'] else 'DIFFERS'}; "
                   f"RC-2 {'EXACT' if rc2['exact_agreement'] else 'DIFFERS'}; binary stamps "
                   f"{'differ as declared' if stamp_a != stamp_b else 'EQUAL'}"),
    }
    wj(os.path.join(runs_dir, "check2_report.json"), report)
    return report


# ------------------------------------------------------------------- CHECK 3

def check_engine(runs_dir: str, r1: dict) -> dict:
    """CHECK 3, engine leg: the walk is closed-loop (the engine controller is
    the in-loop actor; actions recomputed from the live trajectory -- the
    restore proof demonstrates exactly this), and NO channel accepts a
    pre-recorded action stream."""
    reasons = []
    # engine CLI action-replay probes: argv[2] is the ONLY foreign input shape
    # the plain harness can see, and it is parsed as a tick:vx COMMAND SCHEDULE
    # (a string), never as a file of pre-recorded actions.
    #   probe A: a relative path to the actions file (no drive colon) -- the
    #            parser must REFUSE it before any step.
    #   probe B: an absolute path to a NONEXISTENT actions file -- the Windows
    #            drive colon parses as a degenerate schedule {tick 0, vx 0.0}
    #            and the walk RUNS: the harness never opens the referenced
    #            file (a real action-replay channel would have to), which is
    #            the direct proof that no file/action channel exists.
    def _cli_probe(tag: str, spec: str) -> dict:
        argv = [exe_paths()["A"], SCENE, spec]
        so, se = os.path.join(runs_dir, f"replay_probe_{tag}.stdout"), \
            os.path.join(runs_dir, f"replay_probe_{tag}.stderr")
        with open(so, "wb") as f1, open(se, "wb") as f2:
            p = subprocess.run(argv, stdout=f1, stderr=f2, cwd=runs_dir, timeout=600)
        err = rd(se).decode("utf-8", errors="replace")
        out = rd(so).decode("utf-8", errors="replace")
        return {"probe": tag, "argv2": spec, "exit_code": p.returncode,
                "stderr_head": err.strip()[:160],
                "refused_before_any_step": p.returncode != 0
                and "bad command spec" in err,
                "fg42_schedule_echo": "F-G42 command_spec=" in out}

    # the spec is run-index-free (a canonical payload field): a colon-free
    # relative reference to the actions file, resolved against cwd=runs_dir
    probe_a = _cli_probe("A_relative_actions_path", "refA1.actions.bin")
    probe_b = _cli_probe("B_nonexistent_absolute_actions_path",
                         "Z:\\no_such\\pre_recorded_actions.bin")
    if not probe_a["refused_before_any_step"]:
        reasons.append(f"engine CLI did not refuse the actions file reference: {probe_a}")
    if not (probe_b["exit_code"] == 0 and probe_b["fg42_schedule_echo"]):
        reasons.append(f"engine CLI probe B behaved unexpectedly: {probe_b}")
    # the runner's refusals (the upgate machinery, unchanged)
    runner_refusals = []
    bundle = load_bundle()
    for kwargs in ({"precomputed_actions": [[0.0] * 8]}, {"mode": "action_replay"}):
        try:
            requalify(bundle, "engine-walk-scene", {}, 20260920, 900, **kwargs)
            runner_refusals.append(None)  # ACCEPTED: the refusal FAILED
        except PolicyCompatError as exc:
            runner_refusals.append(str(exc) if "ACTION_REPLAY_REFUSED" in str(exc) else None)
    refusals_ok = all(r is not None for r in runner_refusals)
    if not refusals_ok:
        reasons.append("runner requalify accepted a replay channel")
    # closed-loop statement: the restore proof IS the recomputation proof --
    # after restore, the controller RECOMPUTES actions from the restored live
    # trajectory and they match the uninterrupted walk bit-for-bit.
    passed = not reasons
    report = {
        "check": "CHECK_3_engine_closed_loop_requalification_shape",
        "pass": passed, "reasons": reasons,
        "closed_loop": ("the engine controller is the in-loop actor; per-tick actions "
                        "(last_torque_) are recomputed from the live trajectory at every "
                        "tick; the checkpoint-resume proof shows the recomputation "
                        "reproduces the uninterrupted actions bit-for-bit after a "
                        "fresh-process restore"),
        "action_replay_probes": {
            "engine_cli_relative_actions_path": probe_a,
            "engine_cli_nonexistent_absolute_path": probe_b,
            "runner_requalify": runner_refusals,
        },
        "refusal_rationale": ("no input channel accepts a pre-recorded action stream on the "
                              "engine walk path: the instrument's CLI takes a scene and (plain "
                              "form) a tick:vx command-schedule STRING only -- a file reference "
                              "is refused as 'bad command spec' before any step, and a "
                              "nonexistent path is 'consumed' as a schedule without ever being "
                              "opened (probe B: the walk runs on a nonexistent file -- no "
                              "action-file channel exists); the restore hook takes a STATE "
                              "snapshot and the controller recomputes the actions"),
        "detail": (f"engine CLI relative-path probe refused={probe_a['refused_before_any_step']}; "
                   f"nonexistent-path probe ran without opening the file (fg42 echo="
                   f"{probe_b['fg42_schedule_echo']}); "
                   f"runner refusals {sum(1 for r in runner_refusals if r is not None)}/2"),
    }
    wj(os.path.join(runs_dir, "check3_engine_report.json"), report)
    return report


def check_actor(runs_dir: str) -> tuple[dict, dict]:
    """CHECK 3, actor leg: the frozen dummy actor on the declared CPU walk
    scene -- the upgate check 3 machinery, unchanged, plus the corpus
    cross-check against the frozen P3 bytes."""
    rep, run = check3(runs_dir, 20260920, 900)
    bundle = load_bundle()
    corpus = build_corpus(bundle)
    p3 = os.path.join(REPO, "tools", "science_funnel", "validation",
                      "typeb_p3_20260921", "actions_run1.bin")
    corpus_matches = corpus["actions_sha256"] == sha256_hex(rd(p3))
    report = {"check": "CHECK_3_actor_leg_dummy_closed_loop",
              "pass": bool(rep["pass"] and corpus_matches),
              "upgate_check3": rep,
              "corpus_reproduces_p3_bytes": corpus_matches,
              "corpus_actions_sha256": corpus["actions_sha256"],
              "p3_recorded_actions_sha256": sha256_hex(rd(p3)),
              "detail": (f"actor-leg gates {'ALL GREEN' if rep['pass'] else 'RED'}; corpus "
                         f"{'reproduces' if corpus_matches else 'DRIFTS FROM'} the frozen P3 bytes")}
    wj(os.path.join(runs_dir, "check3_actor_report.json"), report)
    return report, run


# ----------------------------------------------------------------- relation

def registered_cases_sha() -> str:
    cases = [
        {"case": "RC-1_ship_walk", "schedule": None, "checkpoint_tick": CHECKPOINT_TICK,
         "horizon": "refusal-terminated walk life"},
        {"case": "RC-2_pinned_command_zoh", "schedule": RC2_SCHEDULE,
         "horizon": "refusal-terminated walk life"},
        {"case": "CL-ACTOR_cpu_scene", "seed": 20260920, "horizon_ticks": 900},
    ]
    return sha256_hex(canonical_json(cases))


def build_relation(identity: dict) -> dict:
    bundle = load_bundle()
    manifest = bundle["manifest"]
    env = bundle["pman"].build_env()
    runs_dir = os.path.join(TMP, "runs", "run1")
    return {
        "policy_bundle": {
            "manifest_hash": manifest["manifest_hash"],
            "weights_sha256": manifest["policy"]["weights_sha256"],
            "manifest_file_sha256": bundle["manifest_file_sha256"],
            "weights_file_sha256": bundle["weights_file_sha256"],
            "architecture": manifest["policy"]["architecture"],
            "activation": manifest["policy"]["activation"],
            "normalization_clip": manifest["normalization"].get("clip", 8.0),
            "normalization_dim": len(manifest["normalization"].get("std", [])),
            "training_backend": manifest["policy"]["training_backend"],
            "loader": "typeb_export.policy_manifest.load_manifest (frozen)",
        },
        "physics_build": identity,
        "runtime_profile": {
            **env,
            "policy_hz": manifest["action"]["clock"]["policy_hz"],
            "physics_hz": manifest["action"]["clock"]["physics_hz"],
            "hold_ticks": manifest["action"]["clock"]["hold_ticks"],
            "inference_recipe": manifest["inference"].get("recipe", "pinned-by-manifest-hash"),
            "engine_walk_tick_hz": 300,
            "evidence_event_stride": 1,
        },
        "body_domain": {
            "body_digest": "UNBOUND_dummy (P3 manifest body: status UNBOUND -- "
                           "binds automatically when the real actor exists)",
            "domain_tag": "gait-walker/14-coordinate (engine walk of record) + "
                          "cpu-walk-scene/hind-pad-surrogate (actor leg)",
        },
        "test_suite": {
            "id": SUITE_ID,
            "registered_cases_sha256": registered_cases_sha(),
            "event_stride": 1,
            "checkpoint_tick": CHECKPOINT_TICK,
            "snapshot_apis_proof_receipt_sha256": snapshot_api.sha256_hex(
                rd(os.path.join(SNAP_LANE, "receipt.json"))),
            "actor_leg_suite": "upgrade_gate_20260920/registered_cases_v1 (upgate check 3, unchanged)",
            "corpus": "frozen P3 900-tick/60-decision sequence",
        },
    }


def build_scope() -> dict:
    from .scene_cpu import derived_envelope
    env = derived_envelope()
    return {
        "bodies": ["UNBOUND_dummy (the P3 dummy actor; the certificate binds the bundle "
                   "hashes, so the real actor binds by reissuance with identical machinery)",
                   "gait-walker 14-coordinate walker (the engine walk of record's body)"],
        "skills": ["level-ground forward walk: the ship walk of record (engine leg, "
                   "refusal-terminated at the ship budget) + the CPU walk-scene surrogate "
                   "(actor leg)"],
        "transitions": ["entry from the measured gait state (engine leg; the ship harness's "
                        "own periodic-cycle entry) / entry from rest at the manifest center "
                        "commands (actor leg)"],
        "ranges": {"engine_walk_ticks": "[0, 302) recorded (refusal AT the tick-302 step "
                                        "boundary; the refusal state is never serialized)",
                   "checkpoint_tick": str(CHECKPOINT_TICK),
                   "rc2_command": "commanded_target_velocity_x = 1.01 m/s from tick 150 (ZOH)",
                   "phase": "[0,1) per leg", "com_speed_m_s": f"[0, {env['velocity_envelope_m_s']!r}] "
                   "(actor leg, the derived envelope V)"},
        "horizons": {"engine_walk_recorded_ticks": 302, "checkpoint_tick": CHECKPOINT_TICK,
                     "actor_leg_ticks": 900, "actor_leg_decisions": 60, "hold_ticks": 15},
        "bars": {
            "bounds_honored": "ACTOR LEG (measured): every applied command within the manifest "
                              "limiter bounds. ENGINE LEG: the command channel's declared domain "
                              "max(0,.) is enforced by the adapter (exercised in RC-2); the walk "
                              "of record carries the ship torque schedule byte-identically.",
            "no_nan_inf": "BOTH LEGS (measured): no NaN/Inf in any recorded state quantity "
                          "(actor leg: the 900-tick CPU loop; engine leg: every f64 field of "
                          "every serialized 184-field walk state, all 302 ticks).",
            "no_intervention": "ACTOR LEG (measured): intervention_reason == none at every tick. "
                               "ENGINE LEG: the walk of record carries EXACTLY the ship's own "
                               "declared refusal face -- one refusal at tick 302, class "
                               "gait_positional_correction_budget (the ship positional-correction "
                               "budget) -- and no other; the refusal IS the walk's declared "
                               "terminal face, not an intervention.",
            "contact_floor": "ACTOR LEG (measured): contact_count >= 2 at every tick. ENGINE LEG: "
                             "NOT CLAIMED as an independent green -- the walk of record's support "
                             "census is the SHIP FACE (the ship suite's own census reds ride the "
                             "fenced stdout), byte-bound bit-identically; the certificate claims "
                             "that face and nothing greener.",
            "availability_exact": "ACTOR LEG (measured): available_groups exactly the declared set "
                                  "at every tick. ENGINE LEG: the status surface is the ship "
                                  "status JSON, byte-fenced.",
            "velocity_envelope": "ACTOR LEG (measured): |v_t| <= V (the derived envelope). ENGINE "
                                 "LEG: the walk's velocity series is the ship walk of record's "
                                 "series -- bit-identity is the acceptance bound; any movement "
                                 "fires.",
        },
        "bars_scope_note": ("the six bars are the ACTOR leg's acceptance letter (all six measured "
                            "green by the upgate gates) plus the ENGINE leg's bit-identity "
                            "acceptance: the walk of record IS the ship face, byte-bound; no "
                            "greener walk is claimed anywhere"),
        "non_regression_margins": [
            {"name": "engine_walk_bit_identity", "quantity": "differing bytes vs the ship walk of "
                                                             "record across states/actions/stdout/trace",
             "bound": 0,
             "derivation": "the wave-47 ship anchor set is the human-authored reference (no "
                           "reference, no verdict); bit-identity is the tightest possible "
                           "non-regression bound and the fence proves it attainable at this base"},
            {"name": "restore_resume_diverging_ticks", "quantity": "first diverging tick of the "
                                                                   "restored continuation (state hashes or action bytes)",
             "bound": 0,
             "derivation": "the frozen-ref discipline: a restored future that diverges at ANY tick "
                           "fires F1 RESTORE-DRIFT; zero is the only passing value, derived from "
                           "the definition of bit-identity, not tuned"},
            {"name": "crossbuild_openloop_max_dv", "quantity": "max|v_N1 - v_N| over the registered "
                                                               "open-loop cases (actor leg)",
             "bound": env["openloop_crossbuild_margin_m_s"],
             "derivation": env["derivation"]},
        ],
        "universal_proof_disclaimer": "agreement on registered cases is evidence, never universal proof",
        "registration": {
            "claims": ("this exact engine walk build (source closure + binary stamp + scene pin + "
                       "ship anchors), this actor (the P3 dummy bundle hashes), this scene pair "
                       "(gait scene f6844ee... + the declared CPU walk scene), these bars; the four "
                       "restart-state gaps RESOLVED through the snapshot-apis readers (proof bound "
                       "by the receipt sha, live-verified at issuance); deployment class production"),
            "does_not_claim": ["no trained policy exists: the actor is the declared P3 dummy "
                               "(64->128->128->8, frozen seeded weights); body UNBOUND_dummy",
                               "no ship-tree build id: the identity is instrument-build-ship-fenced; "
                               "a first-class engine build id is a NAMED FORWARD GAP",
                               "the ship-tree HTTP snapshot route (GET/POST /gait_snapshot) is a "
                               "NAMED FORWARD GAP and is NOT implemented here",
                               "no actor-in-the-engine-loop coupling: the engine walk's in-loop "
                               "actor is the engine controller; the only actor->engine channel in "
                               "existence is the command adapter at schedule granularity (RC-2)",
                               "the engine walk of record is the ship face INCLUDING its refusal "
                               "(302) and its own census reds; nothing greener is claimed"],
        },
    }


# ------------------------------------------------------------- certificate

def build_evidence(r1: dict) -> dict:
    """The certificate's replay evidence, built from the walk of record's own
    per-tick state hashes: the evidence IS the restore-proof currency."""
    initial = r1["hashes"][0]
    chain = sha256_hex(f"chain0:{initial}".encode("utf-8"))
    events = []
    for t in range(1, r1["n"]):
        h = r1["hashes"][t]
        chain = sha256_hex(f"{chain}:{t}:state:{h}".encode("utf-8"))
        events.append({"tick": t, "kind": "state", "state_sha256": h, "chain_sha256": chain})
    return {
        "initial_snapshot_sha256": initial,
        "initial_snapshot_convention": "the tick-0 state hash: the first recorded state of the "
                                       "walk of record (post-step canonical 4-class body)",
        "events": events,
        "periodic_stride": 1,
        "final_state_sha256": r1["hashes"][-1],
        "trajectory_sha256": sha256_hex(r1["actions"]),
        "trajectory_convention": "last_torque_ 18 x f64 LE per tick (the engine controller's "
                                 "recomputed per-tick actions)",
    }


def issue(runs_dir: str, r1: dict, monitors: list[dict]) -> dict:
    identity = engine_identity()
    relation = build_relation(identity)
    receipt = rj(os.path.join(LANE, "receipt.json"))
    inventory = snapshot_api.production_inventory()
    ok, reasons = snapshot_api.verify_lane_proofs()
    if not ok:
        raise CertDryRunError("snapshot-apis proofs do not verify: " + "; ".join(reasons))
    comp_ok, comp_reasons = snapshot_api.check_registry_completeness()
    if not comp_ok:
        raise CertDryRunError("registry completeness: " + "; ".join(comp_reasons))
    # the T=150 checkpoint is bound in the relation (physics_build.checkpoint)
    snap_raw = rd(os.path.join(runs_dir, "refA1.snap_t150.bin"))
    relation["physics_build"]["checkpoint_snapshot"] = {
        "tick": CHECKPOINT_TICK, "file_sha256": sha256_hex(snap_raw),
        "body_bytes": r1["body"], "manifest_fields": len(rj(os.path.join(SNAP_LANE, "runs", "ref1.manifest.json"))),
        "restorable_proof": "CHECK 1's fresh-process restore continues BIT-IDENTICALLY to the "
                            "uninterrupted walk through the ship refusal",
    }
    evidence = build_evidence(r1)
    evidence["monitors"] = monitors
    cert = issue_certificate(relation, inventory, evidence, build_scope(),
                             {"issued_by": ISSUED_BY, "lane": "cert-dryrun-20260920",
                              "base_commit": BASE_COMMIT, "prereg_receipt": PREREG,
                              "prereg_rule0_sha": receipt["pre_registration"]["frozen_rule_0_sha"]})
    return cert


def assemble_monitors(c1: dict, c2: dict, c3e: dict, c3a: dict, corpus_ok: bool) -> list[dict]:
    inv = snapshot_api.production_inventory()
    mons = [
        {"name": "CHECK_1_engine_replay_resume_bit_identity", "pass": c1["pass"],
         "detail_sha256": sha256_hex(canonical_json(c1))},
        {"name": "CHECK_2_cross_build_exact_registered_cases", "pass": c2["pass"],
         "detail_sha256": sha256_hex(canonical_json(c2))},
        {"name": "CHECK_3_engine_closed_loop_and_replay_refusal", "pass": c3e["pass"],
         "detail_sha256": sha256_hex(canonical_json(c3e))},
        {"name": "CHECK_3_actor_leg_gates_and_refusal", "pass": c3a["pass"],
         "detail_sha256": sha256_hex(canonical_json(c3a))},
        {"name": "corpus_reproduces_p3_bytes", "pass": corpus_ok,
         "detail_sha256": sha256_hex(canonical_json({"p3": "typeb_p3_20260921/actions_run1.bin"}))},
        {"name": "snapshot_apis_gap_proofs_live_verified", "pass": True,
         "detail_sha256": sha256_hex(canonical_json(inv))},
    ]
    return mons


def tampers(cert: dict, runs_dir: str) -> dict:
    """The negative controls: the certificate must be able to FAIL."""
    import copy
    res = {}

    def verdict(tampered: dict, request_relation: dict | None):
        errs = validate_certificate(tampered)
        dep = check_deploy(request_relation if request_relation is not None
                           else {k: cert["relation"][k] for k in
                                 ("policy_bundle", "physics_build", "runtime_profile",
                                  "body_domain", "test_suite")}, tampered)
        return errs, dep

    # T1: bumped state hash, cert_hash recomputed (a self-consistent forgery)
    t1 = copy.deepcopy(cert)
    ev = t1["replay_evidence"]["events"][5]["state_sha256"]
    t1["replay_evidence"]["events"][5]["state_sha256"] = \
        ("0" if ev[0] != "0" else "1") + ev[1:]
    t1["cert_hash"] = cert_hash(t1)
    errs1, dep1 = verdict(t1, None)
    res["T1_bumped_state_hash"] = {
        "rejected": bool(errs1) and any("chain mismatch" in e for e in errs1),
        "layer": "validator: evidence chain mismatch",
        "violations": errs1, "deploy": dep1["decision"],
    }

    # T2: swapped normalization constant
    true_req = {k: cert["relation"][k] for k in
                ("policy_bundle", "physics_build", "runtime_profile", "body_domain", "test_suite")}
    t2a = copy.deepcopy(cert)
    t2a["relation"]["policy_bundle"]["normalization_clip"] = 8.5
    t2a["cert_hash"] = cert_hash(t2a)          # compat_key left stale
    errs2a, dep2a = verdict(t2a, None)
    t2b = copy.deepcopy(cert)
    t2b["relation"]["policy_bundle"]["normalization_clip"] = 8.5
    t2b["compat_key"] = compat_key(t2b["relation"])   # fully self-consistent forgery
    t2b["cert_hash"] = cert_hash(t2b)
    errs2b, dep2b = verdict(t2b, true_req)     # request built through the FROZEN P3 loader
    res["T2_swapped_normalization_constant"] = {
        "rejected": bool(errs2a) and dep2b["decision"] == "BLOCK",
        "layer_a": "validator: compat_key does not match the relation",
        "layer_b": "deploy gate: compatibility key mismatch vs the frozen-loader request",
        "violations_a": errs2a, "violations_b": errs2b,
        "deploy_a": dep2a["decision"], "deploy_b": dep2b["decision"],
    }

    # T3: stale build id
    stale = "engine-walk-instrument/0000000000000000-stale"
    t3a = copy.deepcopy(cert)
    t3a["relation"]["physics_build"]["build_id"] = stale
    t3a["cert_hash"] = cert_hash(t3a)
    errs3a, dep3a = verdict(t3a, None)
    t3b = copy.deepcopy(cert)
    t3b["relation"]["physics_build"]["build_id"] = stale
    t3b["compat_key"] = compat_key(t3b["relation"])
    t3b["cert_hash"] = cert_hash(t3b)
    errs3b, dep3b = verdict(t3b, true_req)
    res["T3_stale_build_id"] = {
        "rejected": bool(errs3a) and dep3b["decision"] == "BLOCK",
        "layer_a": "validator: compat_key does not match the relation",
        "layer_b": "deploy gate: compatibility key mismatch vs the true request",
        "violations_a": errs3a, "violations_b": errs3b,
        "deploy_a": dep3a["decision"], "deploy_b": dep3b["decision"],
    }

    # clean re-issue: no false positive
    errs_clean = validate_certificate(cert)
    dep_clean = check_deploy(true_req, cert)
    res["clean_reissue"] = {"valid": not errs_clean, "violations": errs_clean,
                            "deploy": dep_clean["decision"]}
    all_rejected = all(res[k]["rejected"] for k in
                       ("T1_bumped_state_hash", "T2_swapped_normalization_constant",
                        "T3_stale_build_id"))
    res["suite_pass"] = all_rejected and not errs_clean and dep_clean["decision"] == "ALLOW"
    wj(os.path.join(runs_dir, "tamper_report.json"), res)
    return res


# ----------------------------------------------------------------- pipeline

def pipeline(run_index: int) -> dict:
    runs_dir = os.path.join(TMP, "runs", f"run{run_index}")
    os.makedirs(runs_dir, exist_ok=True)
    identity = engine_identity()
    if not identity["instrument_dormancy"]["pass"]:
        raise CertDryRunError("instrument dormancy proof failed: "
                              + "; ".join(identity["instrument_dormancy"]["checks"]))
    c1, r1 = check1(runs_dir)
    c2 = check2(runs_dir, r1)
    c3e = check_engine(runs_dir, r1)
    c3a, _ = check_actor(runs_dir)
    p3 = os.path.join(REPO, "tools", "science_funnel", "validation",
                      "typeb_p3_20260921", "actions_run1.bin")
    corpus_ok = True  # recomputed inside check_actor; recompute here for the monitor
    bundle = load_bundle()
    corpus = build_corpus(bundle)
    corpus_ok = corpus["actions_sha256"] == sha256_hex(rd(p3))

    monitors = assemble_monitors(c1, c2, c3e, c3a, corpus_ok)
    if not all(m["pass"] for m in monitors):
        raise CertDryRunError("monitor red: "
                              + ",".join(m["name"] for m in monitors if not m["pass"]))
    cert = issue(runs_dir, r1, monitors)
    errs = validate_certificate(cert)
    if errs:
        raise CertDryRunError("F1 ISSUANCE-FAIL: the validator blocked the clean certificate: "
                              + "; ".join(errs))
    true_req = {k: cert["relation"][k] for k in
                ("policy_bundle", "physics_build", "runtime_profile", "body_domain", "test_suite")}
    allow = check_deploy(true_req, cert)
    foreign = dict(true_req)
    foreign["physics_build"] = dict(true_req["physics_build"])
    foreign["physics_build"]["build_id"] = "engine-walk-instrument/ffffffffffffffff-foreign"
    block_foreign = check_deploy(foreign, cert)
    block_missing = check_deploy(true_req, None)
    if not (allow["decision"] == "ALLOW" and block_foreign["decision"] == "BLOCK"
            and block_missing["decision"] == "BLOCK"):
        raise CertDryRunError("deploy gate sanity failed: "
                              f"{allow['decision']}/{block_foreign['decision']}/{block_missing['decision']}")
    tam = tampers(cert, runs_dir)
    if not tam["suite_pass"]:
        raise CertDryRunError("F2 TAMPER-PASS or clean-reissue false positive: "
                              + json.dumps({k: v for k, v in tam.items() if k != "suite_pass"})[:800])

    wj(os.path.join(runs_dir, "certificate.json"), cert)
    payload = {
        "suite": SUITE_ID,
        "schema_version": SCHEMA_VERSION,
        "identity_build_id": identity["build_id"],
        "identity_dormancy_pass": identity["instrument_dormancy"]["pass"],
        "check1": c1, "check2": c2, "check3_engine": c3e, "check3_actor": c3a,
        "evidence_events": len(cert["replay_evidence"]["events"]),
        "certificate": cert,
        "deploy_allow": allow,
        "deploy_block_foreign_build": block_foreign,
        "deploy_block_missing_certificate": block_missing,
        "tamper_suite": tam,
    }
    with open(os.path.join(TMP, f"payload_run{run_index}.json"), "wb") as f:
        f.write(canonical_json(payload))
    return payload


def main() -> None:
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    payload = pipeline(idx)
    print(json.dumps({"run": idx, "build_id": payload["identity_build_id"],
                      "compat_key": payload["certificate"]["compat_key"],
                      "deployment_class": payload["certificate"]["restart_state_inventory"]["deployment_class"],
                      "checks": {"c1": payload["check1"]["pass"], "c2": payload["check2"]["pass"],
                                 "c3e": payload["check3_engine"]["pass"],
                                 "c3a": payload["check3_actor"]["pass"]},
                      "tamper_suite_pass": payload["tamper_suite"]["suite_pass"],
                      "deploy_allow": payload["deploy_allow"]["decision"]}, indent=1))


if __name__ == "__main__":
    main()
