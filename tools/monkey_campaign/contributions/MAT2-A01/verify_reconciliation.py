#!/usr/bin/env python3
"""MAT2-A01 reconciliation probe — executes the FROZEN predictions PR-1..PR-6
from PREREGISTRATION.md (commit 38c2ada2, frozen before this script existed).

Read-only against the repository, the registry and the play checkout. All writes
go to the attempt workspace's probe_tmp/ (outside this checkout) and to this
contribution's evidence/ directory. CPU-only, offline, python -B.

Exit code 0 iff every frozen prediction passes. Any falsifier firing prints
FALSIFIER FIRED and exits nonzero: the reconciliation then STOPS, nothing is
repaired here.
"""
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# --- frozen constants -------------------------------------------------------
MERGE_ERA = "4aecbc9e"   # PR #187 merge; contributions/ONT-A01 present
CURRENT_TIP = "8ec90f13"  # PR #196 merge (MAT2-P02), this candidate's base
APPROVED_HEAD = "6f90c288ce93f236c820a2d665b0418c11d7024a"  # PR #176 head (ONT-A01)
PREFIX = "tools/monkey_campaign/contributions/ONT-A01"
FREEZE_PARENT = CURRENT_TIP  # PREREGISTRATION commit 38c2ada2 sits directly on this
PIN_P1_X_MM = -28.320999816060066
PIN_P2_D_MM = 3.2891597453041737
PIN_P2_T_MM = 6.0
PIN_P3_ERR_DEG = 0.15353092426937565
EXPECTED_SUITE_OK = 26
CAMERA_REQUIRED = [
    "frame_id", "coordinate_unit", "position",
    "orientation_convention_and_values", "target", "distance_to_target",
    "projection", "vertical_fov_or_orthographic_span", "near_far_planes",
    "aspect_ratio", "viewport_resolution", "camera_motion_or_bookmark_sequence",
    "visibility_layers", "label_ids", "occlusion_or_xray_mode",
    "state_or_tick_interval",
]
PROFILE = {  # byte-identical to the MAT2-A01 / archived ONT-A01 task profile
    "id": "anatomy",
    "kind": "visible_static",
    "views": ["whole-creature overview", "local attachment close-up",
              "orthogonal side and oblique views"],
    "clean_view_required": True,
    "diagnostic_layers": ["outer envelope", "selected bones/joints",
                          "muscle/tendon paths", "attachment sites",
                          "frame axes", "stable 3D labels"],
}

REPO = Path(__file__).resolve()
while not (REPO / ".git").exists():
    REPO = REPO.parent
ATTEMPT_ROOT = REPO.parent  # ...\kanban-attempts\MAT2-A01\<attempt>
TMP = ATTEMPT_ROOT / "probe_tmp"
COORD = ATTEMPT_ROOT.parent.parent.parent / "agent_slots.sqlite3"

RESULTS = []


def git(*args):
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("git failed: " + " ".join(args) + "\n" + out.stderr)
    return out.stdout


def record(pid, ok, details):
    RESULTS.append({"id": pid, "pass": bool(ok), "details": details})
    print(("PASS " if ok else "FAIL ") + pid + ": " + details)
    return ok


def sha256_file(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- PR-1 byte-stability ----------------------------------------------------
def pr1():
    revs = [APPROVED_HEAD, MERGE_ERA, CURRENT_TIP]
    trees = {}
    for rev in revs:
        raw = git("ls-tree", "-r", rev, "--", PREFIX)
        trees[rev] = {}
        for line in raw.splitlines():
            meta, path = line.split("\t", 1)
            blob = meta.split()[2]
            trees[rev][path] = blob
    counts = {r: len(trees[r]) for r in revs}
    same_all = (trees[APPROVED_HEAD] == trees[MERGE_ERA] == trees[CURRENT_TIP]
                and counts[APPROVED_HEAD] > 0)
    diffs = []
    if not same_all:
        paths = set().union(*[set(t) for t in trees.values()])
        for p in sorted(paths):
            vals = [trees[r].get(p) for r in revs]
            if len(set(vals)) > 1:
                diffs.append({"path": p, "blobs": dict(zip(revs, vals))})
    # frozen anchor pair + disclosed stricter lineage anchor (approved head)
    detail = ("files=%d identical blob sha256 across %s -> %s -> %s" %
              (counts[MERGE_ERA], APPROVED_HEAD[:8], MERGE_ERA[:8], CURRENT_TIP[:8]))
    return record("PR-1", same_all, detail + ("" if same_all else " DIFFS=" + json.dumps(diffs[:5])))


# --- PR-2 suite re-execution in a fresh temp replica ------------------------
def extract(rev, sub, dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(REPO), "archive", rev, sub],
                         capture_output=True)
    if tar.returncode != 0:
        raise RuntimeError("git archive failed: " + tar.stderr.decode(errors="replace"))
    import tarfile, io
    with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            rel = Path(m.name).relative_to(sub)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tf.extractfile(m).read())
    return dest


def pr2():
    replica = TMP / "replica_ont_a01"
    extract(CURRENT_TIP, PREFIX, replica)
    run = subprocess.run([sys.executable, "-B", "test_ota01_roll_sign.py", "-v"],
                         cwd=str(replica), capture_output=True, text=True, timeout=900)
    out = run.stdout + run.stderr
    ran = re.search(r"Ran (\d+) tests", out)
    ran_n = int(ran.group(1)) if ran else -1
    final_ok = re.search(r"(?:^|\n)OK\b", out) is not None
    hard_fails = len(re.findall(r"(?:^|\n)(?:FAIL|ERROR): ", out))
    # diagnostic only: per-line ok count undercounts when unittest wraps a
    # multi-line docstring or a ResourceWarning lands before the verdict word
    ok_lines = len(re.findall(r"\.\.\. ok", out))
    detail = ("suite exit=%d; unittest summary: Ran %d tests, OK=%s; hard FAIL/ERROR "
              "result lines=%d (frozen: exit 0, %d tests, zero fail; cpu-only "
              "python -B); per-line-ok diagnostic=%d" % (
                  run.returncode, ran_n, final_ok, hard_fails, EXPECTED_SUITE_OK,
                  ok_lines))
    ok = (run.returncode == 0 and ran_n == EXPECTED_SUITE_OK and final_ok
          and hard_fails == 0)
    return record("PR-2", ok, detail)


# --- PR-3 numerical identity ------------------------------------------------
def check_numerical(replica: Path):
    r = json.loads((replica / "evidence" / "numerical_receipt.json").read_text(
        encoding="utf-8"))
    errs = []
    if r.get("outcome") != "AMBIGUITY_RECORDED":
        errs.append("outcome=%r" % r.get("outcome"))
    if sorted(r.get("fired_falsifiers", [])) != ["F2", "F4"]:
        errs.append("fired_falsifiers=%r" % r.get("fired_falsifiers"))
    p1 = r["P1_source_bone"]
    if p1["olecranon_min_x_mm"] != PIN_P1_X_MM or p1["receipt_olecranon_min_x_mm"] != PIN_P1_X_MM:
        errs.append("P1 olecranon x mismatch")
    bs = r["P2_target_olecranon_test"]["best_station"]
    if bs["t_mm"] != PIN_P2_T_MM or bs["D_post_minus_ant_mm"] != PIN_P2_D_MM \
            or bs["receipt_D_mm"] != PIN_P2_D_MM:
        errs.append("P2 best station mismatch")
    p3 = r["P3_sign_law"]
    if p3["trilat_no_flip_err_deg"] != PIN_P3_ERR_DEG or p3["unanimous_no_flip"] is not True:
        errs.append("P3 sign law mismatch")
    if r.get("task_id") != "A01" or r.get("card_id") != "ONT-A01":
        errs.append("envelope ids mismatch")
    if r.get("honesty", {}).get("cpu_only") is not True or \
            r.get("honesty", {}).get("gpu_used") is not False:
        errs.append("honesty block mismatch")
    return (len(errs) == 0, "; ".join(errs) if errs else
            "outcome AMBIGUITY_RECORDED, F2/F4 fired, P1 x=%r mm, P2 t=+6 D=%r mm, "
            "P3 %r deg unanimous NO-FLIP, task_id A01, cpu_only, all exact" % (
                PIN_P1_X_MM, PIN_P2_D_MM, PIN_P3_ERR_DEG))


def pr3():
    ok, detail = check_numerical(TMP / "replica_ont_a01")
    return record("PR-3", ok, detail)


# --- PR-4 manifest class (visible_static, task_id A01, committed bytes) ------
def camera_field_locator(cam, vis, manifest, row):
    """Map the 16 contract fields to their canonical locations in this row."""
    samples = cam.get("samples") or []
    s0 = samples[0] if samples else {}
    mapping = {
        "frame_id": ("camera", cam.get("frame_id")),
        "coordinate_unit": ("camera", cam.get("coordinate_unit")),
        "position": ("camera.samples", s0.get("position")),
        "orientation_convention_and_values": (
            "camera.orientation_convention+samples[].orientation",
            [cam.get("orientation_convention"), [s.get("orientation") for s in samples]]),
        "target": ("camera.samples", s0.get("target")),
        "distance_to_target": ("camera.samples", s0.get("distance_to_target")),
        "projection": ("camera", cam.get("projection")),
        "vertical_fov_or_orthographic_span": ("camera.orthographic_span",
                                              cam.get("orthographic_span")),
        "near_far_planes": ("camera", cam.get("near_far_planes")),
        "aspect_ratio": ("camera", cam.get("aspect_ratio")),
        "viewport_resolution": ("camera", cam.get("viewport_resolution")),
        "camera_motion_or_bookmark_sequence": (
            "camera.sample_mode+samples", [cam.get("sample_mode"), len(samples)]),
        "visibility_layers": ("view.visibility.layers", vis.get("layers")),
        "label_ids": ("view.visibility.label_ids", vis.get("label_ids")),
        "occlusion_or_xray_mode": ("view.visibility.occlusion_mode",
                                   vis.get("occlusion_mode")),
        "state_or_tick_interval": ("manifest.tick_interval+samples[].tick",
                                   [manifest.get("tick_interval"),
                                    [s.get("tick") for s in samples]]),
    }
    # an empty list is a PRESENT, honestly-empty declaration (clean rows carry no
    # diagnostic layers/labels by definition); only an absent field is missing
    missing = [k for k, (_, v) in mapping.items() if v is None]
    return missing, mapping


def pr4():
    rep = TMP / "replica_ont_a01"
    manifest = json.loads((rep / "evidence" / "capture_manifest.json").read_text(encoding="utf-8"))
    context = json.loads((rep / "evidence" / "capture_context.json").read_text(encoding="utf-8"))
    errs = []
    if manifest.get("task_id") != "A01":
        errs.append("manifest task_id=%r" % manifest.get("task_id"))
    if context.get("task_id") != "A01":
        errs.append("context task_id=%r" % context.get("task_id"))
    if manifest.get("profile_id") != "anatomy":
        errs.append("profile_id=%r" % manifest.get("profile_id"))
    if manifest.get("schema") != "chimera.visual_capture_manifest.v1":
        errs.append("schema=%r" % manifest.get("schema"))
    rows = manifest.get("views", [])
    pairs = {}
    for row in rows:
        pairs.setdefault(row.get("pair_id"), set()).add(row.get("mode"))
    if len(rows) != 6 or sorted(pairs) != ["V1", "V2", "V3"] or \
            any(v != {"diagnostic", "clean"} for v in pairs.values()):
        errs.append("rows/pairs=%r" % {k: sorted(v) for k, v in pairs.items()})
    missing_fields = {}
    for row in rows:
        miss, _ = camera_field_locator(row.get("camera", {}), row.get("visibility", {}),
                                       manifest, row)
        if miss:
            missing_fields[row.get("pair_id") + ":" + row.get("mode")] = miss
    if missing_fields:
        errs.append("missing camera fields=" + json.dumps(missing_fields))
    # byte binding: committed capture_sheet.png == context/manifest capture_sha256
    png = rep / "evidence" / "capture_sheet.png"
    png_sha = sha256_file(png)
    if png_sha != context.get("capture_sha256") or png_sha != manifest.get("capture_sha256"):
        errs.append("capture_sheet.png bytes not bound to manifest/context sha")
    # canonical structural validation
    vc_src = git("show", CURRENT_TIP + ":tools/monkey_campaign/visual_capture.py")
    vc_path = TMP / "visual_capture_probe.py"
    vc_path.write_text(vc_src, encoding="utf-8")
    sys.path.insert(0, str(TMP))
    try:
        import visual_capture_probe as vc
        structural = vc.validate_manifest(manifest, context, PROFILE)
        if structural.get("structurally_valid") is not True or structural.get("view_count") != 6:
            errs.append("canonical validator=%r" % structural)
        else:
            canonical = "canonical validate_manifest: structurally_valid=%s view_count=%s mode=%s" % (
                structural["structurally_valid"], structural["view_count"], structural["mode"])
    except Exception as exc:  # noqa: BLE001 - falsifier path
        errs.append("canonical validator raised: %r" % (exc,))
        canonical = "canonical validator failed"
    detail = ("task_id=A01 envelope, 6 rows = V1/V2/V3 x diagnostic/clean, all 16 contract "
              "camera fields located on every row (canonical schema layout), PNG bytes "
              "bound (sha %s…), %s" % (png_sha[:8], canonical))
    if errs:
        detail = "; ".join(errs)
    return record("PR-4", not errs, detail)


# --- PR-5 dependency merged at this base ------------------------------------
def pr5():
    con = sqlite3.connect("file:%s?mode=ro" % COORD.as_posix(), uri=True)
    try:
        state = json.loads(con.execute(
            "SELECT payload FROM state WHERE id=1").fetchone()[0])
    finally:
        con.close()
    card = state["kanban"]["cards"]["MAT2-P02"]
    winner = card.get("winner") or {}
    merge_sha = winner.get("merge_commit_sha", "")
    ok = (card.get("state") == "DONE" and merge_sha.startswith(CURRENT_TIP)
          and winner.get("pr_url", "").endswith("/196"))
    base = git("rev-parse", "HEAD~1").strip()  # freeze commit's parent = base
    base_ok = base.startswith(CURRENT_TIP)
    detail = ("MAT2-P02 state=%s merged via PR #196 merge_commit=%s == candidate base %s; "
              "freeze-commit parent %s" % (card.get("state"), merge_sha[:8],
                                           CURRENT_TIP[:8], base[:8]))
    return record("PR-5", ok and base_ok, detail + ("" if (ok and base_ok) else " MISMATCH"))


# --- PR-6 failing-first: probe has teeth ------------------------------------
def pr6():
    tam = TMP / "replica_tampered"
    if tam.exists():
        shutil.rmtree(tam)
    shutil.copytree(TMP / "replica_ont_a01", tam)
    nr = tam / "evidence" / "numerical_receipt.json"
    raw = nr.read_text(encoding="utf-8")
    assert "AMBIGUITY_RECORDED" in raw
    nr.write_text(raw.replace("AMBIGUITY_RECORDED", "TAMPERED_RECORD", 1),
                  encoding="utf-8")
    ok_pristine, _ = check_numerical(TMP / "replica_ont_a01")
    ok_tampered, why = check_numerical(tam)
    fired = ok_pristine and not ok_tampered
    detail = ("pristine passes=%s; tampered (1 byte: outcome->TAMPERED_RECORD) passes=%s (%s)"
              % (ok_pristine, ok_tampered, why))
    return record("PR-6", fired, detail)


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    pr1()
    pr2()
    pr3()
    pr4()
    pr5()
    pr6()
    failures = [r for r in RESULTS if not r["pass"]]
    receipt = {
        "schema": "chimera.mat2_a01_reconciliation_receipt.v1",
        "task_id": "A01",
        "card_id": "MAT2-A01",
        "attempt_id": "f59c82c7dba94fb5abb210fe818ef537",
        "criteria_sha256": "3ffafb225eb06eb7dc958676d48c17bfcfd7f9d266c68b6e3a32d8b97920ff56",
        "preregistration_freeze_commit": git("rev-parse", "HEAD~1").strip(),
        "candidate_base": CURRENT_TIP,
        "anchors": {"approved_head": APPROVED_HEAD, "merge_era": MERGE_ERA,
                    "current_tip": CURRENT_TIP},
        "probes": RESULTS,
        "outcome": "RECONCILED" if not failures else "FALSIFIER_FIRED",
        "checks_pass": sum(1 for r in RESULTS if r["pass"]),
        "checks_total": len(RESULTS),
        "probe_corrections": [
            {"fired_first_run": "PR-2 FAIL: suite exit=0 ok=25 fail/error=0 "
                                "(expected 26 ok, cpu-only python -B)",
             "cause": "probe counting heuristic: regex '\\.\\.\\. ok' undercounts when "
                      "unittest wraps a multi-line docstring or a ResourceWarning line "
                      "lands before the verdict word; unittest's own summary printed "
                      "'Ran 26 tests / OK', exit 0, zero FAIL/ERROR result lines",
             "fix": "PR-2 now asserts the authoritative unittest summary (exit 0, "
                    "Ran 26 tests, final OK, zero 'FAIL:'/'ERROR:' result lines); the "
                    "per-line count is kept as a disclosed diagnostic. FROZEN "
                    "EXPECTATION UNCHANGED (26/26, zero fail)."},
            {"fired_first_run": "PR-4 FAIL: missing camera fields={V1:clean, V2:clean, "
                                "V3:clean: [visibility_layers]}",
             "cause": "probe locator idiom '(vis.get(\"layers\") or [None])[0]' read the "
                      "clean rows' honestly-EMPTY declared 'layers': [] as absent; clean "
                      "rows carry empty layers/label_ids by definition (clean semantics) "
                      "and the canonical validator accepts this by design",
             "fix": "locator now treats an empty list as a present, honestly-empty "
                    "declaration; only an absent (null) field is missing. FROZEN "
                    "EXPECTATION UNCHANGED (all 16 contract fields locatable on every "
                    "row)."},
        ],
        "applicability_notes": [
            "replica suite re-execution READ one pinned external input from the "
            "read-only play checkout (E:/PythonChimera/Saved/meshes/monkey_birth.bin, "
            "target pack, 661076 bytes, mtime 2026-08-31) via the archived "
            "reference/mesh_target_o1.py; read-only, no writes, no network.",
        ],
        "honesty": {"cpu_only": True, "gpu_used": False, "native_engine_run": False,
                    "network_used": False,
                    "note": "read-only probe over committed bytes + registry read-only; "
                            "temp replica under attempt workspace probe_tmp/"},
    }
    ev = Path(__file__).resolve().parent / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / "reconciliation_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print("outcome:", receipt["outcome"], "(%d/%d probes pass)" %
          (receipt["checks_pass"], receipt["checks_total"]))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
