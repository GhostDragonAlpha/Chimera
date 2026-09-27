#!/usr/bin/env python3
"""MAT2-A02 reconciliation probe — executes the FROZEN predictions PR-1..PR-6
from PREREGISTRATION.md (commit dc2906816b0d435042010b38fb1a9db6f7407810, frozen
before this script existed).

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
APPROVED_HEAD = "dadfda280d7c4abcc403b78f5c5b6ecd8332a402"  # PR #181 head (ONT-A02)
MERGE_181 = "970ffe1a34eb8a895956c6cb92ce66d01dc74961"      # PR #181 merge
MERGE_ERA = "4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf"      # PR #187 merge (ONT-A03)
CURRENT_TIP = "6af853ad3be90e2f9564cb7f908fd4a202f9241c"    # PR #211 merge (MAT2-A01) = base
PREFIX = "tools/monkey_campaign/contributions/ONT-A02"
FREEZE_PARENT = CURRENT_TIP
FREEZE_MSG_PREFIX = "MAT2-A02: PREREGISTRATION frozen before probes"
FREEZE_FILE = "tools/monkey_campaign/contributions/MAT2-A02/PREREGISTRATION.md"
EXPECTED_FILES = 35
EXPECTED_SUITE_LINE = "106/106 tests PASS"
PLAY_CHECKOUT = Path(r"E:/PythonChimera/tools/monkey_campaign")
CAMERA_REQUIRED = [
    "frame_id", "coordinate_unit", "position",
    "orientation_convention_and_values", "target", "distance_to_target",
    "projection", "vertical_fov_or_orthographic_span", "near_far_planes",
    "aspect_ratio", "viewport_resolution", "camera_motion_or_bookmark_sequence",
    "visibility_layers", "label_ids", "occlusion_or_xray_mode",
    "state_or_tick_interval",
]
PROFILE = {  # byte-identical to the MAT2-A02 / archived ONT-A02 task profile
    "id": "anatomy",
    "kind": "visible_static",
    "views": ["whole-creature overview", "local attachment close-up",
              "orthogonal side and oblique views"],
    "clean_view_required": True,
    "diagnostic_layers": ["outer envelope", "selected bones/joints",
                          "muscle/tendon paths", "attachment sites",
                          "frame axes", "stable 3D labels"],
}
MY_CONTRACT = {"task_id": "A02", "task": {"verification_profile": PROFILE}}
# frozen numerical receipt pins (exact JSON float/text equality)
ENVELOPE_PINS = {
    "outcome": "PRESENTED_AND_VERIFIED",
    "task_id": "A02",
    "card_id": "ONT-A02",
    "schema": "chimera.ont_a02_numerical_receipt.v1",
    "preregistration_sha256": "c624401da34c14ed0b71bae33ec85825187d4a6d8e93cbb1acba78faacf4150b",
    "state_snapshot_sha256": "9e770ea52f8172e3b004df58ac2feb534a0cedfb106d82d775c008931eedcb58",
}
SUMMARY_PIN = {"fail": 0, "pass": 57, "total": 57}
GROUP_CENSUS = {"N0": 4, "N1": 12, "N2": 30, "N3": 4, "N4": 7}
CHECK_PINS = {
    "N1.u2r_mm": 23.07463997552291,
    "N1.r2h_mm": 292.0293820833787,
    "N1.e2h_mm": 305.79223569279844,
    "N1.axial_mm": 14.323729312735956,
    "N1.lateral_mm": 18.088103293382634,
    "N1.posterior_mm": 0.3005126010484894,
    "N1.angle_deg": 51.62861170617259,
    "N1.source_fraction_pct": 7.545855414950395,
    "N2.radius.s_old": 0.22170679566544982,
    "N2.radius.s_new": 0.20418868001006546,
    "N2.radius.span_old_m": 0.06474489854186721,
    "N2.radius.span_new_m": 0.05962909405176015,
    "N2.radius.gap_m": 0.005115804490107064,
    "N2.radius.det_new": 0.008513242115903161,
    "N2.radius.G_unchanged": 2.220446049250313e-16,
    "N2.radius.max_delta_m": 0.004950983466166482,
    "N2.radius_l.max_delta_m": 0.004948423135921825,
    "N2.scale_change_pct": -7.901478889180636,
    "N4.o1_ECU-P2": 63.61229795664599,
    "N4.o1_ANC-P2": 17.552772577400333,
    "N4.o1_TRIlat-P5": 0.15353092426937565,
    "N4.band_margin": 3.0,
}
# merged qualification receipt evidence digests (byte bindings)
QUAL_PINS = {
    "numerical": "2aa382a15c0f005ef421fb0fa967b912486e03bdac2f75b9a50529d3ab90cce1",
    "source": "60241502ebe8f7679f4dd42f69a498a547417aa0c2342cf7571940e53f121089",
    "visual": "a728b16a6c0fb87170c3ce2dd6c1824bf7a9a353e4c304a5cf41966b5d4462fa",
    "camera": "6a7957d3d4c9aa4d0493f2ad984768bce182232f77a7909067926f7a0e8c0f6d",
}
PNG_SHA = "a728b16a6c0fb87170c3ce2dd6c1824bf7a9a353e4c304a5cf41966b5d4462fa"

REPO = Path(__file__).resolve()
while not (REPO / ".git").exists():
    REPO = REPO.parent
ATTEMPT_ROOT = REPO.parent  # ...\kanban-attempts\MAT2-A02\<attempt>
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
    revs = [APPROVED_HEAD, MERGE_181, MERGE_ERA, CURRENT_TIP]
    trees = {}
    for rev in revs:
        raw = git("ls-tree", "-r", rev, "--", PREFIX)
        trees[rev] = {}
        for line in raw.splitlines():
            meta, path = line.split("\t", 1)
            blob = meta.split()[2]
            trees[rev][path] = blob
    counts = {r: len(trees[r]) for r in revs}
    same_all = (all(trees[r] == trees[APPROVED_HEAD] for r in revs)
                and counts[APPROVED_HEAD] == EXPECTED_FILES)
    diffs = []
    if not same_all:
        paths = set().union(*[set(t) for t in trees.values()])
        for p in sorted(paths):
            vals = [trees[r].get(p) for r in revs]
            if len(set(vals)) > 1:
                diffs.append({"path": p, "blobs": dict(zip(revs, vals))})
    detail = ("files=%d (frozen %d) identical blob sha256 across %s -> %s -> %s -> %s"
              % (counts[APPROVED_HEAD], EXPECTED_FILES, APPROVED_HEAD[:8],
                 MERGE_181[:8], MERGE_ERA[:8], CURRENT_TIP[:8]))
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


def pr2(replica: Path):
    run = subprocess.run([sys.executable, "-B", "test_ota02_radioulnar.py"],
                         cwd=str(replica), capture_output=True, text=True, timeout=1800)
    out = run.stdout + run.stderr
    final_line = [ln for ln in out.splitlines() if "tests PASS" in ln]
    count_line = final_line[-1].strip() if final_line else "<absent>"
    hard_fails = len(re.findall(r"(?:^|\n)FAIL ", out))
    ok = (run.returncode == 0 and count_line == EXPECTED_SUITE_LINE and hard_fails == 0)
    detail = ("suite exit=%d; final count line=%r (frozen %r); FAIL lines=%d; "
              "cpu-only python -B"
              % (run.returncode, count_line, EXPECTED_SUITE_LINE, hard_fails))
    return record("PR-2", ok, detail)


# --- PR-3 numerical identity ------------------------------------------------
def check_numerical(replica: Path):
    r = json.loads((replica / "evidence" / "numerical_receipt.json").read_text(
        encoding="utf-8"))
    errs = []
    for key, want in ENVELOPE_PINS.items():
        if r.get(key) != want:
            errs.append("%s=%r" % (key, r.get(key)))
    if r.get("summary") != SUMMARY_PIN:
        errs.append("summary=%r" % (r.get("summary"),))
    fb = r.get("falsifier_bookkeeping", {})
    if fb.get("F1_identity") != "no identity mismatch" or fb.get("F2_value") != "none":
        errs.append("falsifier_bookkeeping=%r" % (fb,))
    checks = r.get("checks", [])
    census = {}
    for c in checks:
        census[c["id"].split(".")[0]] = census.get(c["id"].split(".")[0], 0) + 1
        if c.get("verdict") != "PASS":
            errs.append("verdict %s=%r" % (c.get("id"), c.get("verdict")))
    if census != GROUP_CENSUS or len(checks) != SUMMARY_PIN["total"]:
        errs.append("census=%r total=%d" % (census, len(checks)))
    by_id = {c["id"]: c for c in checks}
    for cid, want in CHECK_PINS.items():
        got = by_id.get(cid, {}).get("measured")
        if got != want:
            errs.append("pin %s measured=%r want=%r" % (cid, got, want))
    extras = {
        "N2.radius.worst_site": "BICshort-P6",
        "N2.radius_l.worst_site": "BIClong_l-P9",
        "N2.radius.n_sites": 16,
        "N3.gate_cells": "10 PASS",
        "N3.receipt_08_ok": True,
        "N3.coverage_ok": True,
        "N4.o1_unanimous": True,
        "N4.c1_10of10": True,
    }
    for cid, want in extras.items():
        got = by_id.get(cid, {}).get("measured")
        if got != want:
            errs.append("pin %s measured=%r want=%r" % (cid, got, want))
    t6 = by_id.get("N3.t6", {}).get("measured", {})
    if t6.get("verdict") != "PASS" or t6.get("banned_evidence_occurrences") != 0:
        errs.append("N3.t6=%r" % (t6,))
    return (len(errs) == 0, "; ".join(errs[:8]) if errs else
            "outcome PRESENTED_AND_VERIFIED, 57/57 PASS (census %s), all %d exact value "
            "pins + %d structural pins reproduced, task_id A02 envelope"
            % (json.dumps(census, sort_keys=True), len(CHECK_PINS), len(extras) + 1))


# --- PR-4 manifest class (visible_static, task_id A02, committed bytes) ------
def camera_field_locator(cam, vis, manifest):
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


def pr4(replica: Path):
    manifest = json.loads((replica / "evidence" / "capture_manifest.json").read_text(encoding="utf-8"))
    context = json.loads((replica / "evidence" / "capture_context.json").read_text(encoding="utf-8"))
    qual = json.loads((replica / "evidence" / "qualification_receipt.json").read_text(encoding="utf-8"))
    errs = []
    if manifest.get("task_id") != "A02":
        errs.append("manifest task_id=%r" % manifest.get("task_id"))
    if context.get("task_id") != "A02":
        errs.append("context task_id=%r" % context.get("task_id"))
    if manifest.get("profile_id") != "anatomy":
        errs.append("profile_id=%r" % manifest.get("profile_id"))
    if manifest.get("schema") != "chimera.visual_capture_manifest.v1":
        errs.append("schema=%r" % manifest.get("schema"))
    if context.get("tick_interval") != [0, 3]:
        errs.append("context tick_interval=%r" % (context.get("tick_interval"),))
    rows = manifest.get("views", [])
    pairs = {}
    for row in rows:
        pairs.setdefault(row.get("pair_id"), set()).add(row.get("mode"))
        if row.get("mode") == "diagnostic" and \
                (row.get("visibility") or {}).get("occlusion_mode") != "mixed":
            errs.append("diagnostic occlusion=%r" % row.get("pair_id"))
        if row.get("mode") == "clean":
            vis = row.get("visibility") or {}
            if vis.get("occlusion_mode") != "depth_tested" or vis.get("layers") != [] \
                    or vis.get("label_ids") != []:
                errs.append("clean row semantics=%r" % row.get("pair_id"))
    if len(rows) != 6 or sorted(pairs) != ["V1", "V2", "V3"] or \
            any(v != {"diagnostic", "clean"} for v in pairs.values()):
        errs.append("rows/pairs=%r" % {k: sorted(v) for k, v in pairs.items()})
    missing_fields = {}
    for row in rows:
        miss, _ = camera_field_locator(row.get("camera", {}), row.get("visibility", {}),
                                       manifest)
        if miss:
            missing_fields[row.get("pair_id") + ":" + row.get("mode")] = miss
    if missing_fields:
        errs.append("missing camera fields=" + json.dumps(missing_fields))
    # byte binding: committed capture_sheet.png == context/manifest/qualification-receipt
    png = replica / "evidence" / "capture_sheet.png"
    png_sha = sha256_file(png)
    if png_sha != PNG_SHA:
        errs.append("capture_sheet.png sha=%r" % png_sha)
    if png_sha != context.get("capture_sha256") or png_sha != manifest.get("capture_sha256"):
        errs.append("png not bound to manifest/context")
    ev = qual.get("evidence", {})
    if qual.get("schema") != "chimera.ont_a02_qualification.v1" or \
            qual.get("task_id") != "A02" or qual.get("done_when_verified") is not True or \
            qual.get("profile_verified") is not True:
        errs.append("qualification envelope=%r" % qual.get("schema"))
    if ev.get("visual", {}).get("raw_sha256") != PNG_SHA:
        errs.append("qualification visual pin=%r" % ev.get("visual", {}).get("raw_sha256"))
    replica_files = {
        "numerical": replica / "evidence" / "numerical_receipt.json",
        "source": replica / "reference" / "EXTRACTION.json",
        "camera": replica / "evidence" / "capture_manifest.json",
    }
    for kind, path in replica_files.items():
        want = QUAL_PINS[kind]
        got = sha256_file(path)
        if got != want:
            errs.append("%s bytes=%r want=%r" % (kind, got, want))
        if ev.get(kind, {}).get("raw_sha256") != want:
            errs.append("qualification %s pin=%r" % (kind, ev.get(kind, {}).get("raw_sha256")))
    # canonical structural validation from THIS BASE's own bytes; assert the play
    # checkout copy (the one the lead pipeline imports) is byte-identical first
    vc_src = git("show", CURRENT_TIP + ":tools/monkey_campaign/visual_capture.py")
    vc_path = TMP / "visual_capture_probe.py"
    vc_path.write_text(vc_src, encoding="utf-8")
    play_vc = PLAY_CHECKOUT / "visual_capture.py"
    vc_identical = play_vc.read_bytes() == vc_src.encode("utf-8")
    if not vc_identical:
        errs.append("play checkout visual_capture.py differs from base blob")
    canonical = "validator identity not checked"
    sys.path.insert(0, str(TMP))
    try:
        import visual_capture_probe as vc
        structural = vc.validate_manifest(manifest, context, PROFILE)
        if structural.get("structurally_valid") is not True or structural.get("view_count") != 6:
            errs.append("canonical validator=%r" % structural)
        else:
            canonical = ("canonical validate_manifest (base blob, play-checkout copy "
                         "byte-identical): structurally_valid=%s view_count=%s"
                         % (structural["structurally_valid"], structural["view_count"]))
    except Exception as exc:  # noqa: BLE001 - falsifier path
        errs.append("canonical validator raised: %r" % (exc,))
    # visual_gate.verify against replica-resolved absolute paths, THIS card's contract
    gate = "gate not run"
    try:
        sys.path.insert(0, str(PLAY_CHECKOUT))
        import visual_gate
        mirror = {
            "evidence": {
                "camera": {"reference": str(replica_files["camera"].resolve()),
                           "raw_sha256": QUAL_PINS["camera"]},
                "visual": {"reference": str(png.resolve()), "raw_sha256": PNG_SHA},
            },
            "capture_context": context,
        }
        gate_receipt = visual_gate.verify(mirror, MY_CONTRACT)
        if gate_receipt.get("structurally_valid") is not True or gate_receipt.get("view_count") != 6:
            errs.append("visual_gate.verify=%r" % gate_receipt)
        else:
            gate = ("visual_gate.verify(task_id A02 contract): structurally_valid=%s "
                    "view_count=%s" % (gate_receipt["structurally_valid"],
                                       gate_receipt["view_count"]))
    except Exception as exc:  # noqa: BLE001 - falsifier path
        errs.append("visual_gate.verify raised: %r" % (exc,))
    detail = ("task_id=A02 envelope, 6 rows = V1/V2/V3 x diagnostic/clean, all 16 "
              "contract camera fields located on every row, PNG bytes bound (sha %s…), "
              "qualification receipt binds all 4 evidence digests, %s; %s"
              % (png_sha[:8], canonical, gate))
    if errs:
        detail = "; ".join(errs[:10])
    return record("PR-4", not errs, detail)


# --- PR-5 dependency merged at this base + freeze chronology -----------------
def find_freeze_commit():
    """(sha, parent) of the freeze commit, HEAD-position-independent."""
    for line in git("log", "--format=%H %P %s", "--max-count=64").splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[2].startswith(FREEZE_MSG_PREFIX):
            return parts[0], parts[1]
    return None, None


def pr5():
    con = sqlite3.connect("file:%s?mode=ro" % COORD.as_posix(), uri=True)
    try:
        state = json.loads(con.execute(
            "SELECT payload FROM state WHERE id=1").fetchone()[0])
    finally:
        con.close()
    card = state["kanban"]["cards"]["MAT2-A01"]
    winner = card.get("winner") or {}
    oq = winner.get("ontology_qualification") or {}
    dep_ok = (card.get("state") == "DONE"
              and winner.get("merge_commit_sha") == CURRENT_TIP
              and winner.get("pr_url", "").endswith("/211")
              and oq.get("task_id") == "A01"
              and oq.get("scope_sha256") == "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097")
    freeze_sha, freeze_parent = find_freeze_commit()
    chron = freeze_sha is not None and freeze_parent == CURRENT_TIP
    anc = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor",
                          freeze_sha or "HEAD", "HEAD"], capture_output=True)
    files = [f for f in git("show", "--name-only", "--format=",
                            freeze_sha or "HEAD").split() if f]
    only_prereg = files == [FREEZE_FILE]
    has_dir = bool(git("ls-tree", "HEAD", "--name-only", "--",
                       "tools/monkey_campaign/contributions/MAT2-A02/").strip())
    ok = (dep_ok and chron and anc.returncode == 0 and only_prereg and has_dir)
    detail = ("MAT2-A01 state=%s merged via PR #211 merge_commit=%s == candidate base "
              "%s (winner ontology_qualification task_id=%s); freeze commit %s "
              "(parent %s, ancestor-of-HEAD=%s, files=%s); HEAD carries contribution "
              "dir=%s" % (card.get("state"), (winner.get("merge_commit_sha") or "?")[:8],
                          CURRENT_TIP[:8], oq.get("task_id"), (freeze_sha or "?")[:8],
                          (freeze_parent or "?")[:8], anc.returncode == 0,
                          [f.rsplit('/', 1)[-1] for f in files], has_dir))
    return record("PR-5", ok, detail + ("" if ok else " MISMATCH"))


# --- PR-6 failing-first: probe has teeth ------------------------------------
def pr6(replica: Path):
    tam = TMP / "replica_tampered"
    if tam.exists():
        shutil.rmtree(tam)
    shutil.copytree(replica, tam)
    nr = tam / "evidence" / "numerical_receipt.json"
    raw = nr.read_text(encoding="utf-8")
    assert "PRESENTED_AND_VERIFIED" in raw
    nr.write_text(raw.replace("PRESENTED_AND_VERIFIED", "TAMPERED_RECORD", 1),
                  encoding="utf-8")
    ok_pristine, _ = check_numerical(replica)
    ok_tampered, why = check_numerical(tam)
    fired = ok_pristine and not ok_tampered
    detail = ("pristine passes=%s; tampered (1 token: outcome->TAMPERED_RECORD) "
              "passes=%s (%s)" % (ok_pristine, ok_tampered, why[:120]))
    return record("PR-6", fired, detail)


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    replica = TMP / "replica_ont_a02"
    extract(CURRENT_TIP, PREFIX, replica)
    freeze_sha, _ = find_freeze_commit()
    pr1()
    pr2(replica)
    pr3_ok, pr3_detail = check_numerical(replica)
    record("PR-3", pr3_ok, pr3_detail)
    pr4(replica)
    pr5()
    pr6(replica)
    failures = [r for r in RESULTS if not r["pass"]]
    receipt = {
        "schema": "chimera.mat2_a02_reconciliation_receipt.v1",
        "task_id": "A02",
        "card_id": "MAT2-A02",
        "attempt_id": "ce71ec9ca3d74978bd62f99a5c0fcdfe",
        "criteria_sha256": "c5d0e02ef376f01afcab78ee81e087f3b28dd9c7f29aef1bd0375c9ac2dd7bdf",
        "preregistration_freeze_commit": freeze_sha,
        "candidate_base": CURRENT_TIP,
        "anchors": {"approved_head": APPROVED_HEAD, "merge_181": MERGE_181,
                    "merge_era": MERGE_ERA, "current_tip": CURRENT_TIP},
        "probes": RESULTS,
        "outcome": "RECONCILED" if not failures else "FALSIFIER_FIRED",
        "checks_pass": sum(1 for r in RESULTS if r["pass"]),
        "checks_total": len(RESULTS),
        "probe_corrections": [],
        "applicability_notes": [
            "replica suite re-execution READ two pinned external inputs from the "
            "read-only play checkout (E:/PythonChimera/Saved/meshes/monkey_birth.bin, "
            "661076 bytes and monkey_joints.bin, 296589 bytes; hash-pinned inside the "
            "receipt under test) and imported visual_capture/visual_gate support "
            "modules from the play checkout (visual_capture byte-identical to the "
            "base blob; read-only imports, python -B, no bytecode writes, no network).",
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
