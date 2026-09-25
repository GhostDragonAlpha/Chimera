"""verify_loading -- M-F08: the repeatable-loading verification suite.

Frozen prereg: agents/F08_loading/PREREGISTRATION.md (written BEFORE this file;
Amendments 1-2 appended before this suite existed). Consumes ONLY the live
integrated artifacts (F01 clearing, F02 terrain bundle + terrain_query, F03
trunk, F07 routes) and the declared data module
tools/monkey_campaign/data/monkey_forest/forest_loader.py.

The four preregistered falsifiers, and the checks that would fire them:

    (a) any recompile producing different bytes
        -> T1: in-process recompile x2 byte-identical; committed byte-identity
           for all four; >=3 fresh-process `receipt` runs byte-identical.
    (b) a missing/corrupted artifact loading silently
        -> T2: 4 omission cases, each a named f08_missing_artifact naming the
           exact sandbox path; T3: 13 corruption cases (body-edit / pin-edit /
           coherent re-forge per artifact + truncated JSON), every one a named
           refusal carrying the recipe's own code.
    (c) initial state varying across loads
        -> T4: initial_state_sha256 identical in-process x2 and across the 3
           fresh processes; every frozen field equals its declaring artifact.
    (d) teardown leaving declared resources live
        -> T5: headless test doubles -- a full load tears down 7/7 resources
           by name (engine slot first), second teardown is a named no-op, a
           failing release is a loud f08_teardown_leak, and a retry completes.

Real files are NEVER modified: the matrices run in sandbox copy trees, and the
suite re-hashes the four committed files before and after to prove it.

Stdlib only; CPU-only; headless; deterministic receipts (no wall clock).
Run from the repo root:
    python tools/monkey_campaign/agents/F08_loading/verify_loading.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, REPO)

from tools.monkey_campaign.data.monkey_forest import forest_loader as fl  # noqa: E402

RECEIPTS = os.path.join(HERE, "receipts")
ORDER = fl.ORDER
MOD_KEYS = {"clearing": "clearing_mod", "terrain": "terrain_mod",
            "trunk": "trunk_mod", "routes": "routes_mod"}

# --- frozen expectations (prereg) ----------------------------------------------
EXPECTED_FILE_SHA = {
    "clearing": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1",
    "terrain": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52",
    "trunk": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1",
    "routes": "28dff2b33e74fcc4103ac3699899b0937f6975323758d1fa142092704bf4496c",
}
EXPECTED_BYTES = {"clearing": 13112, "terrain": 877752,
                  "trunk": 16634, "routes": 8495}
DIGEST_CODE = {"clearing": "f01_digest_mismatch", "terrain": "f02_digest_mismatch",
               "trunk": "f03_digest_mismatch", "routes": "f07_digest_mismatch"}
JSON_CODE = {"clearing": "f01_invalid_json", "terrain": "f02_invalid_json",
             "trunk": "f03_invalid_json", "routes": "f07_invalid_json"}

CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append({"name": name, "pass": bool(cond), "detail": str(detail)})
    mark = "PASS" if cond else "FAIL"
    print("[%s] %s -- %s" % (mark, name, detail))
    return bool(cond)


# --- helpers ---------------------------------------------------------------------
def real_path(key):
    return os.path.join(REPO, *fl.ARTIFACTS[key]["path"].split("/"))


def sandbox_path(root, key):
    return os.path.join(root, *fl.ARTIFACTS[key]["path"].split("/"))


def make_sandbox(omit=None, tamper=None, tamper_key=None):
    """A sandbox copy tree holding the four artifacts (one optionally omitted;
    the file named by ``tamper_key`` optionally passed through
    ``tamper(key, raw, module) -> bytes``). Real files are only ever READ."""
    mods = fl.modules()
    root = tempfile.mkdtemp(prefix="f08_sandbox_")
    for key in ORDER:
        dst = sandbox_path(root, key)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if key == omit:
            continue
        with open(real_path(key), "rb") as handle:
            raw = handle.read()
        if tamper is not None and key == tamper_key:
            raw = tamper(key, raw, mods[MOD_KEYS[key]])
        with open(dst, "wb") as handle:
            handle.write(raw)
    return root


def _dump(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def expect_refusal(name, root, code, artifact, extra=None):
    """Load a sandbox root and require a named refusal. ``code=None`` defers
    the code question to the ``extra`` predicate (T3's per-case expectations);
    ``artifact`` must always name the exact offending input."""
    try:
        fl.load_forest(root=root)
    except fl.Refusal as exc:
        ok = ((code is None or exc.code == code)
              and exc.artifact == artifact
              and (extra is None or extra(exc)))
        return check(name, ok, "code=%s artifact=%s cause=%s"
                     % (exc.code, exc.artifact, exc.cause))
    except Exception as exc:                               # unnamed = falsifier (b)
        return check(name, False, "UNNAMED %r" % (exc,))
    return check(name, False, "LOADED SILENTLY")


# --- T1: recompile determinism ---------------------------------------------------
def t1_recompile_determinism(receipt_shas):
    mods = fl.modules()
    r1 = fl.recompile_all()
    r2 = fl.recompile_all()
    check("T1 in-process recompile x2 byte-identical",
          all(r1[k][1] == r2[k][1] for k in ORDER), "4/4 pairs equal")
    committed_ok = all(
        fl.sha(open(real_path(k), "rb").read()) == fl.sha(r1[k][1])
        for k in ORDER)
    check("T1 recompiled bytes == committed bytes (all four)", committed_ok,
          str({k: len(r1[k][1]) for k in ORDER}))
    pin_ok = True
    for k in ORDER:
        obj = r1[k][0]
        field = fl.ARTIFACTS[k]["pin_field"]
        body = {a: b for a, b in obj.items() if a != field}
        pin_ok = pin_ok and mods[MOD_KEYS[k]].sha(
            mods[MOD_KEYS[k]].canonical(body)) == obj[field]
    check("T1 recompiled self-pins verify (4/4)", pin_ok, "house digest law")
    sizes = {k: len(r1[k][1]) for k in ORDER}
    check("T1 byte counts == prereg frozen table", sizes == EXPECTED_BYTES,
          str(sizes))
    # >=3 fresh-process loads
    shas = set()
    outs = []
    for i in range(3):
        proc = subprocess.run(
            [sys.executable, os.path.join(REPO, "tools", "monkey_campaign",
                                          "data", "monkey_forest",
                                          "forest_loader.py"), "receipt"],
            cwd=REPO, capture_output=True)
        outs.append(proc.stdout)
        doc = json.loads(proc.stdout)
        shas.add(hashlib.sha256(proc.stdout).hexdigest())
        receipt_shas.append(hashlib.sha256(proc.stdout).hexdigest())
        check("T1 fresh-process run %d matches committed digests" % (i + 1),
              all(doc["artifacts"][k]["file_sha256"] == EXPECTED_FILE_SHA[k]
                  and doc["artifacts"][k]["bytes"] == EXPECTED_BYTES[k]
                  for k in ORDER),
              "initial_state_sha256=%s" % doc["initial_state_sha256"])
    check("T1 three fresh-process receipts byte-identical", len(shas) == 1,
          "stdout sha %s" % shas.pop())
    return json.loads(outs[0])


# --- T2: missing-asset matrix ----------------------------------------------------
def t2_missing_matrix():
    control = make_sandbox()
    try:
        scene = fl.load_forest(root=control)
        ok = scene.receipt["initial_state_sha256"] is not None
        scene.teardown()
        check("T2 sandbox happy-path control loads green", ok,
              "faithful 4-file copy")
    finally:
        shutil.rmtree(control, ignore_errors=True)
    for key in ORDER:
        root = make_sandbox(omit=key)
        try:
            expect_refusal(
                "T2 omit %s -> f08_missing_artifact" % key, root,
                "f08_missing_artifact", key,
                extra=lambda exc, k=key: (
                    exc.path is not None
                    and exc.path.startswith(root)
                    and exc.path.endswith(os.path.basename(fl.ARTIFACTS[k]["path"]))))
        finally:
            shutil.rmtree(root, ignore_errors=True)


# --- T3: corruption matrix --------------------------------------------------------
def _tamper_body(key, raw, module):
    obj = json.loads(raw)
    if key == "clearing":
        obj["spawn"]["required_clearance_m"] = 1.25
    elif key == "terrain":
        obj["terrain_surface"]["base_height_m"] = 0.25
    elif key == "trunk":
        obj["geometry"]["height_m"] = 1.2
    else:
        obj["bounds"]["max_slope_m_per_m"] = 0.06
    return _dump(obj)


def _tamper_pin(key, raw, module):
    obj = json.loads(raw)
    field = fl.ARTIFACTS[key]["pin_field"]
    first = obj[field][0]
    obj[field] = ("b" if first != "b" else "c") + obj[field][1:]
    return _dump(obj)


def _tamper_reforge(key, raw, module):
    """Edit a free-text field AND re-pin it with the module's own digest: the
    file lies coherently -- only the recompile can see it."""
    obj = json.loads(raw)
    field = fl.ARTIFACTS[key]["pin_field"]
    text_field = "derived_from" if key == "terrain" else "scope"
    obj[text_field] = obj[text_field] + " TAMPERED-FORGE"
    body = {a: b for a, b in obj.items() if a != field}
    obj[field] = module.digest(body)          # digest canonicalizes internally
    return module.canonical(obj)


def _tamper_garbage(key, raw, module):
    return raw[:len(raw) // 2]                    # truncated JSON bytes


def t3_corruption_matrix():
    cases = []
    for key in ORDER:
        cases.append(("body-edit", key, _tamper_body,
                      lambda exc, k=key: exc.cause == DIGEST_CODE[k]))
        cases.append(("pin-edit", key, _tamper_pin,
                      lambda exc, k=key: exc.cause == DIGEST_CODE[k]))
        cases.append(("re-forge", key, _tamper_reforge,
                      lambda exc, k=key: exc.code == "f08_recompile_drift"))
    cases.append(("truncated-json", "clearing", _tamper_garbage,
                  lambda exc: exc.cause == JSON_CODE["clearing"]))
    for label, key, tamper, extra in cases:
        root = make_sandbox(tamper=tamper, tamper_key=key)
        try:
            expect_refusal("T3 %s(%s) refuses by name" % (label, key),
                           root, None, key, extra=extra)
        finally:
            shutil.rmtree(root, ignore_errors=True)


# --- T4: initial-state determinism -------------------------------------------------
def t4_initial_state(fresh_doc):
    s1 = fl.load_forest()
    sha_a = s1.initial_state["initial_state_sha256"]
    st = s1.initial_state
    s1.teardown()
    s2 = fl.load_forest()
    sha_b = s2.initial_state["initial_state_sha256"]
    s2.teardown()
    check("T4 initial_state_sha256 identical in-process x2", sha_a == sha_b,
          sha_a)
    check("T4 initial_state_sha256 matches fresh processes", sha_a ==
          fresh_doc["initial_state_sha256"], fresh_doc["initial_state_sha256"])
    frozen = [
        ("scene_seed", st["scene_seed"], 4598321),
        ("spawn position", st["spawn"]["position_m"], [0.0, 0.0, 0.0]),
        ("spawn terrain height", st["spawn"]["terrain_height_m"], 0.0),
        ("spawn gradient", st["spawn"]["gradient_m_per_m"], [0.0, 0.0]),
        ("spawn envelope", st["spawn"]["body_radius_envelope_m"], 0.25),
        ("trunk site", st["trunk_site"]["base_centre_m"],
         [11.976783, 0.0, 2.471766]),
        ("trunk radius", st["trunk_site"]["radius_m"], 0.037),
        ("trunk height", st["trunk_site"]["height_m"], 1.158),
        ("route spawn", st["route_graph"]["spawn_m"], [0.0, 0.0, 0.0]),
        ("route axis", st["route_graph"]["trunk_axis_m"],
         [11.976783, 2.471766]),
        ("straight length", st["route_graph"]["straight"]["length_m"],
         12.229185),
        ("tangent count", len(st["route_graph"]["tangents"]), 10),
        ("tangent ids", [t["id"] for t in st["route_graph"]["tangents"]],
         ["R1L", "R1R", "R2L", "R2R", "R3L", "R3R", "R4L", "R4R", "R5L",
          "R5R"]),
        ("grid step", st["route_graph"]["route_grid"]["step_m"], 0.05),
        ("grid shape", (st["route_graph"]["route_grid"]["nx"],
                        st["route_graph"]["route_grid"]["nz"]), (801, 801)),
        ("blockers", st["route_graph"]["blockers"], ["B1", "B2"]),
        ("extent half width", st["extent"]["half_width_m"], 20.0),
        ("surfaces", st["surfaces"],
         ["trunk_01.lateral", "trunk_01.base_cap", "trunk_01.top_cap"]),
    ]
    for label, got, want in frozen:
        check("T4 %s == declared" % label, got == want, "%r" % (got,))
    derived = all(st["derived_from"][k]["file_sha256"] == EXPECTED_FILE_SHA[k]
                  for k in ORDER)
    check("T4 record carries the four proven digests", derived, "derived_from")


# --- T5: teardown (headless doubles; falsifier (d)) --------------------------------
class _ReleaseDouble:
    """Records every release; the headless proof double. Callable with the
    zero-arg shape of the declared referent World.shutdown_engine."""

    def __init__(self, log, name, boom=False):
        self.log, self.name, self.boom = log, name, boom
        self.releases = 0

    def release(self):
        self.releases += 1
        self.log.append(self.name)
        if self.boom:
            raise ValueError("boom")

    def __call__(self):
        self.release()


def t5_teardown():
    # full load with a recording engine double: 7/7 by name, engine first
    log = []
    engine = _ReleaseDouble(log, "engine_shutdown")
    scene = fl.load_forest(engine_shutdown=engine)
    receipt = scene.teardown()
    check("T5 teardown releases 7/7 by name, engine slot FIRST",
          receipt["released"] == ["engine_shutdown", "initial_state",
                                  "terrain_surface", "routes", "trunk",
                                  "terrain", "clearing"],
          str(receipt["released"]))
    check("T5 post-teardown audit names zero live resources",
          receipt["live_after"] == [] and scene.live_resources() == [],
          str(scene.live_resources()))
    check("T5 engine double released exactly once", engine.releases == 1,
          "releases=%d" % engine.releases)
    check("T5 direct handles dropped",
          scene.clearing is None and scene.terrain is None
          and scene.trunk is None and scene.routes is None
          and scene.terrain_surface is None and scene.initial_state is None,
          "all None")
    second = scene.teardown()
    check("T5 second teardown is a named no-op (never a second teardown)",
          second["already_torn_down"] is True and second["released"] == []
          and engine.releases == 1,
          "engine releases still %d" % engine.releases)
    # a failing release is LOUD, named, auditable, and retryable to clean
    boom = _ReleaseDouble([], "engine_shutdown", boom=True)
    bad = fl.load_forest(engine_shutdown=boom)
    try:
        bad.teardown()
        check("T5 failing release fires f08_teardown_leak", False,
              "no refusal raised")
    except fl.Refusal as exc:
        check("T5 failing release fires f08_teardown_leak",
              exc.code == "f08_teardown_leak"
              and exc.artifact == "engine_shutdown",
              "code=%s artifact=%s" % (exc.code, exc.artifact))
    check("T5 scene stays auditable after a leak",
          bad.live_resources() == ["clearing", "terrain", "trunk", "routes",
                                   "terrain_surface", "initial_state",
                                   "engine_shutdown"],
          str(bad.live_resources()))
    boom.boom = False                      # the operator fixes the engine
    receipt3 = bad.teardown()              # retry: failed slot re-releases
    check("T5 retry teardown completes clean",
          receipt3["live_after"] == [] and bad.live_resources() == []
          and boom.releases == 2,
          "engine releases=%d" % boom.releases)
    # pure double scene: every registered resource released exactly once
    log3 = []
    doubles = {k: _ReleaseDouble(log3, k) for k in ORDER}
    doubles["terrain_surface"] = _ReleaseDouble(log3, "terrain_surface")
    doubles["initial_state"] = _ReleaseDouble(log3, "initial_state")
    scene2 = fl.ForestScene(doubles, doubles["terrain_surface"],
                            doubles["initial_state"], {},
                            engine_shutdown=_ReleaseDouble(log3,
                                                           "engine_shutdown"))
    scene2.teardown()
    check("T5 double proof: every release issued exactly once, engine first",
          log3[0] == "engine_shutdown" and len(log3) == 7
          and len(set(log3)) == 7,
          str(log3))
    check("T5 double proof: no resource survives",
          scene2.live_resources() == [], str(scene2.live_resources()))


# --- T6: the loaded surface is the real physics surface ----------------------------
def t6_surface():
    scene = fl.load_forest()
    try:
        s = scene.terrain_surface
        check("T6 height_at(0,0) == 0.0 (spawn on flat base ground)",
              s.height_at(0.0, 0.0) == 0.0, repr(s.height_at(0.0, 0.0)))
        check("T6 gradient at spawn == (0,0)",
              s.gradient_at(0.0, 0.0) == (0.0, 0.0),
              repr(s.gradient_at(0.0, 0.0)))
        check("T6 gradient at trunk site == (0,0)",
              s.gradient_at(11.976783, 2.471766) == (0.0, 0.0),
              repr(s.gradient_at(11.976783, 2.471766)))
        worst, where = s.worst_triangle_slope()
        check("T6 worst_triangle_slope == F02 receipt 0.042522289331596436",
              worst == 0.042522289331596436 and where == (17.0, 7.0),
              "%r at %r" % (worst, where))
        check("T6 extent law strict > (20.0 in, 20.05 out)",
              s.classify(20.0, 0.0) == "inside"
              and s.classify(20.05, 0.0) == "outside",
              "%s/%s" % (s.classify(20.0, 0.0), s.classify(20.05, 0.0)))
        try:
            s.height_at(20.05, 0.0)
            check("T6 query past the extent refuses f02_outside_extent",
                  False, "no refusal")
        except fl.modules()["query_mod"].Refusal as exc:
            check("T6 query past the extent refuses f02_outside_extent",
                  exc.code == "f02_outside_extent", exc.code)
    finally:
        scene.teardown()
    # W10's consumption shape: context manager + surface, torn down on exit
    with fl.load_forest() as w10:
        inside = w10.terrain_surface.height_at(0.0, 0.0)
    check("T6 W10 context-manager consumption works and cleans up",
          inside == 0.0 and w10.live_resources() == [],
          "h=%r live=%r" % (inside, w10.live_resources()))


# --- integrity: real files untouched ------------------------------------------------
def real_file_hashes():
    return {k: fl.file_sha256(real_path(k)) for k in ORDER}


def main():
    os.makedirs(RECEIPTS, exist_ok=True)
    before = real_file_hashes()
    check("integrity: committed files match prereg table BEFORE the suite",
          before == EXPECTED_FILE_SHA, str(before))
    receipt_shas = []
    fresh = t1_recompile_determinism(receipt_shas)
    t2_missing_matrix()
    t3_corruption_matrix()
    t4_initial_state(fresh)
    t5_teardown()
    t6_surface()
    after = real_file_hashes()
    check("integrity: committed files unchanged AFTER the suite",
          after == before == EXPECTED_FILE_SHA, str(after))

    total = len(CHECKS)
    failed = [c for c in CHECKS if not c["pass"]]
    verdict = "GREEN" if not failed else "RED"
    falsifiers = {
        "a_recompile_bytes": "green" if all(
            c["pass"] for c in CHECKS if c["name"].startswith("T1"))
            else "RED",
        "b_missing_or_corrupt_silent": "green" if all(
            c["pass"] for c in CHECKS if c["name"].startswith(("T2", "T3")))
            else "RED",
        "c_initial_state_variance": "green" if all(
            c["pass"] for c in CHECKS if c["name"].startswith("T4"))
            else "RED",
        "d_teardown_leaves_live": "green" if all(
            c["pass"] for c in CHECKS if c["name"].startswith("T5"))
            else "RED",
    }
    doc = {
        "schema": "chimera.monkey_f08_verify.v1",
        "agent": "M-F08",
        "prereg": "agents/F08_loading/PREREGISTRATION.md (Amendments 1-2)",
        "loader": "tools/monkey_campaign/data/monkey_forest/forest_loader.py",
        "checks": CHECKS,
        "counts": {"total": total, "passed": total - len(failed),
                   "failed": len(failed)},
        "verdict": verdict,
        "falsifiers": falsifiers,
        "determinism": {"fresh_process_receipt_runs": 3,
                        "receipt_stdout_sha256": receipt_shas[0],
                        "all_identical": len(set(receipt_shas)) == 1,
                        "initial_state_sha256":
                            fresh["initial_state_sha256"]},
        "integrity": {"committed_unchanged": after == EXPECTED_FILE_SHA,
                      "file_sha256": after},
        "sandbox": {"missing_cases": 4, "corruption_cases": 13,
                    "real_files_deleted": False},
    }
    with open(os.path.join(RECEIPTS, "run.json"), "w") as handle:
        handle.write(_dump(doc).decode("utf-8"))
    lines = ["M-F08 verify_loading -- verdict %s (%d/%d checks pass)"
             % (verdict, total - len(failed), total), ""]
    lines += ["%s  %s  %s" % ("PASS" if c["pass"] else "FAIL", c["name"],
                              c["detail"]) for c in CHECKS]
    with open(os.path.join(RECEIPTS, "run.txt"), "w") as handle:
        handle.write("\n".join(lines) + "\n")
    print("\nVERDICT: %s (%d/%d) -- falsifiers %s"
          % (verdict, total - len(failed), total, falsifiers))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
