#!/usr/bin/env python3
"""MAT2-A03 adoption probe — executes the FROZEN predictions MR-0..MR-8 from
PREREGISTRATION.md (freeze commit 5019ceea9d0a23e5c41be27a8cfd73c08290a414,
frozen before this script existed).

Binds the merged, lead-approved ONT-A03 staged ulna mapping/supersession into the
MAT2 identity by full re-verification at base cb4af613 (PR #214 merge). Read-only
against the repository, the registry and the play checkout; all writes go to the
attempt workspace's probe_tmp/ (outside this checkout) and to this contribution's
evidence/ directory. ONT-A03 bytes are never modified. CPU-only, offline,
python -B.

Exit code 0 iff every frozen prediction passes. Any falsifier firing prints
FALSIFIER FIRED and exits nonzero: the adoption then STOPS, nothing is repaired
here.
"""
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

# --- frozen constants (PREREGISTRATION.md incl. Amendment 1) ----------------
FREEZE_COMMIT = "a0c1e5549d9ed9db59438450a812ba00a1cd22a3"       # Amendment 1
ORIGINAL_FREEZE = "5019ceea9d0a23e5c41be27a8cfd73c08290a414"     # original freeze
BASE = "cb4af613aac6841925535624405b3f630a787c3c"        # PR #214 merge (MAT2-A02)
APPROVED_HEAD = "051d341da2c0786fe9706d169fe16b8127cb8772"  # PR #187 head (ONT-A03)
MERGE_187 = "4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf"      # PR #187 merge
PREFIX = "tools/monkey_campaign/contributions/ONT-A03"
MY_DIR = "tools/monkey_campaign/contributions/MAT2-A03"
EXPECTED_FILES = 37
ATTEMPT_ID = "7ac643af941548f39ad251b024eda976"
ARRIVAL_ID = "arrival-c2a69acdef164e47b9b59d751a25d6a6"
CRITERIA = "a4d6c38cbc07587a261fbde90425e5f0afa5dbd2d8edb4f40713f277e93c3aa8"
ONT_CRITERIA = "d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d"
SCOPE_MAT2 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
SCOPE_ONT = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
DEFINITION_RAW = "57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1"
TASK_DIGEST = "944e19ee697cf953046f73501dc2669f3a0611789abcb7ae356a944b303324a9"
ENVELOPE_DIFF = {"id", "depends_on[0]", "ontology_qualification.scope_sha256"}
MERGE_187_AT = "2026-09-27T06:44:32Z"
PIN = {  # committed-byte pins at the base (MR-3)
    "transforms/radius_supersession_record.json":
        "e98c3c772e8088311278be13078a8cada43af59d1a81d962a634390c49514526",
    "PREREGISTRATION.md":
        "1b1ca64adc42d77839c0bdfe1c9422768378504b78a69a3577031c089cd7a2df",
    "evidence/numerical_receipt.json":
        "6862817bfdfd62ac42048f348063b2e8bd7f696f09387319a2cdd34d4840a9f8",
    "evidence/state_snapshot.json":
        "f9cae65f43da70a3244752a1d67bee501b8c1b80aed6392ca4179c554d68b1a8",
    "evidence/capture_manifest.json":
        "d11ac1409e403c193439e915fea662418099f1bd8402bd0f4b269a9a48e88dfb",
    "evidence/capture_context.json":
        "c0797687119f5328361310848f13d9a4eff83ded04b5274385a5448194eb838b",
    "evidence/capture_sheet.png":
        "7ee98625ecddf74083872131dba8736e4642128943e73cca4751a295354028f1",
    "evidence/visual_provenance.json":
        "1266921aaff08ef83a1a490049067b496c4a04e9f5820338f33d9a55b5e167d6",
    "evidence/qualification_receipt.json":
        "27331aad6b2f1fa8b6a58a51b35100fcbf6e076da73ec6f531eb5e91103f21a8",
    "reference/EXTRACTION.json":
        "4fe87ba7f63eff429f62d19fb2a962173cfbe708a25b0665f97af06c0b0c66af",
}
ONT_PREREG_SHA = PIN["PREREGISTRATION.md"]
EXPECTED_PROBE_LINE = "checks 75/75 PASS  outcome=STAGED_AND_QUALIFIED"
PRISTINE_SUITE_LINE = "137/138 tests PASS"
PRISTINE_SUITE_FAIL_LINES = ["recomputed state equals the committed state snapshot"]
REGSUITE_LINE = "137/138 tests PASS"
REGSUITE_FAIL_LINES = ["subject hash matches the state snapshot"]
PLAY_CHECKOUT = Path(r"E:/PythonChimera/tools/monkey_campaign")
STATE_DIFF_KEYS = ["staged_record_path"]
RECEIPT_DIFF_KEYS = ["state_snapshot_sha256"]
RECORD_ENVELOPE = {
    "schema": "chimera.ont_a03_radius_supersession_record.v1",
    "task_id": "A03", "card_id": "ONT-A03",
    "attempt_id": "9435c49896af49d18c70a08ce20138d2",
    "arrival_id": "arrival-bb1ef1a6a3994ca9bb660ad90af78d6d",
    "criteria_sha256": ONT_CRITERIA, "scope_sha256": SCOPE_ONT,
    "status": "STAGED_FOR_ARCHITECT_APPROVAL", "ok": True,
    "preregistration_sha256": ONT_PREREG_SHA,
}
RECEIPT_ENVELOPE = {
    "schema": "chimera.ont_a03_numerical_receipt.v1",
    "task_id": "A03", "card_id": "ONT-A03",
    "attempt_id": "9435c49896af49d18c70a08ce20138d2",
    "preregistration_sha256": ONT_PREREG_SHA,
    "state_snapshot_sha256": PIN["evidence/state_snapshot.json"],
    "summary": {"fail": 0, "pass": 75, "total": 75},
    "outcome": "STAGED_AND_QUALIFIED",
}
MANIFEST_ENVELOPE = {
    "schema": "chimera.visual_capture_manifest.v1",
    "task_id": "A03", "card_id": "ONT-A03",
    "attempt_id": "9435c49896af49d18c70a08ce20138d2",
    "subject_sha256": PIN["evidence/state_snapshot.json"],
    "capture_sha256": PIN["evidence/capture_sheet.png"],
    "profile_id": "anatomy", "tick_interval": [0, 3],
}
CONTEXT_ENVELOPE = {
    "task_id": "A03",
    "subject_sha256": PIN["evidence/state_snapshot.json"],
    "capture_sha256": PIN["evidence/capture_sheet.png"],
    "tick_interval": [0, 3],
}
QUAL_ENVELOPE = {
    "schema": "chimera.ont_a03_qualification.v1",
    "task_id": "A03", "card_id": "ONT-A03",
    "criteria_sha256": ONT_CRITERIA, "head_sha": None,
}
RECORD_VALUES = {  # exact record pins (MR-3)
    "sides.radius.before.scale": 0.22170679566544982,
    "sides.radius.before.span_m": 0.06474489854186721,
    "sides.radius.after.scale": 0.20418868001006546,
    "sides.radius.after.span_m": 0.05962909405176015,
    "sides.radius_l.before.scale": 0.22170679566544982,
    "sides.radius_l.after.scale": 0.20418868001006546,
}
CAMERA_REQUIRED = [
    "frame_id", "coordinate_unit", "position",
    "orientation_convention_and_values", "target", "distance_to_target",
    "projection", "vertical_fov_or_orthographic_span", "near_far_planes",
    "aspect_ratio", "viewport_resolution", "camera_motion_or_bookmark_sequence",
    "visibility_layers", "label_ids", "occlusion_or_xray_mode",
    "state_or_tick_interval",
]
PROFILE = {  # byte-identical to the MAT2-A03 / archived ONT-A03 task profile
    "id": "anatomy",
    "kind": "visible_static",
    "views": ["whole-creature overview", "local attachment close-up",
              "orthogonal side and oblique views"],
    "clean_view_required": True,
    "diagnostic_layers": ["outer envelope", "selected bones/joints",
                          "muscle/tendon paths", "attachment sites",
                          "frame axes", "stable 3D labels"],
}
MY_CONTRACT = {"task_id": "A03", "task": {"verification_profile": PROFILE}}

REPO = Path(__file__).resolve()
while not (REPO / ".git").exists():
    REPO = REPO.parent
ATTEMPT_ROOT = REPO.parent
TMP = ATTEMPT_ROOT / "probe_tmp"
COORD = ATTEMPT_ROOT.parent.parent.parent / "agent_slots.sqlite3"

RESULTS = []


def git(*args):
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("git failed: " + " ".join(args) + "\n" + out.stderr)
    return out.stdout


def git_bytes(*args):
    out = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True)
    if out.returncode != 0:
        raise RuntimeError("git failed: " + " ".join(args) + "\n" + out.stderr.decode(errors="replace"))
    return out.stdout


def record(pid, ok, details):
    RESULTS.append({"id": pid, "pass": bool(ok), "details": details})
    print(("PASS " if ok else "FAIL ") + pid + ": " + details)
    return ok


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def load_jsonb(b: bytes):
    return json.loads(b.decode("utf-8"))


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def registry_state():
    con = sqlite3.connect("file:%s?mode=ro" % COORD.as_posix(), uri=True)
    try:
        payload = con.execute("SELECT payload FROM state WHERE id=1").fetchone()[0]
        if isinstance(payload, (bytes, bytearray)):
            payload = payload.decode("utf-8")
        return json.loads(payload)
    finally:
        con.close()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def spec_diff_paths(a, b, path=""):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            base = path + "." + k if path else k
            if k not in a:
                out.append(base + " (only MAT2)")
            elif k not in b:
                out.append(base + " (only ONT)")
            else:
                out += spec_diff_paths(a[k], b[k], base)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            out += spec_diff_paths(x, y, path + "[%d]" % i)
    elif a != b:
        out.append(path)
    return out


def extract(rev, sub, dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = git_bytes("archive", rev, sub)
    import tarfile, io
    with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            rel = Path(m.name).relative_to(sub)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tf.extractfile(m).read())
    return dest


def run_py(script: Path, cwd: Path, timeout=1800):
    return subprocess.run([sys.executable, "-B", script.name], cwd=str(cwd),
                          capture_output=True, text=True, timeout=timeout)


# --- MR-0 freeze chronology (Amendment 1 chain) ------------------------------
def find_freeze_commit():
    """(amendment_sha, original_sha, original_parent) or Nones."""
    parents = {}
    for line in git("log", "--format=%H %P %s", "--max-count=64").splitlines():
        parts = line.split(" ", 2)
        if len(parts) >= 2:
            parents[parts[0]] = parts[1]
    amend = FREEZE_COMMIT if FREEZE_COMMIT in parents else None
    orig = parents.get(FREEZE_COMMIT, "")
    return amend, (orig or None), (parents.get(orig) if orig else None)


def mr0():
    sha, orig, orig_parent = find_freeze_commit()
    files = [f for f in git("show", "--name-only", "--format=", FREEZE_COMMIT).split() if f]
    ofiles = [f for f in git("show", "--name-only", "--format=", ORIGINAL_FREEZE).split() if f]
    only_prereg = files == [MY_DIR + "/PREREGISTRATION.md"] and \
        ofiles == [MY_DIR + "/PREREGISTRATION.md"]
    anc = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor",
                          FREEZE_COMMIT, "HEAD"], capture_output=True)
    anc0 = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor",
                           ORIGINAL_FREEZE, "HEAD"], capture_output=True)
    head_files = [f for f in git("diff", "--name-only", BASE, "HEAD").split() if f]
    scoped = all(f.startswith(MY_DIR + "/") for f in head_files) and bool(head_files)
    ok = (sha == FREEZE_COMMIT and orig == ORIGINAL_FREEZE
          and orig_parent == BASE and only_prereg
          and anc.returncode == 0 and anc0.returncode == 0 and scoped)
    detail = ("freeze chain HEAD<-%s(parent %s=original %s, parent %s=base); both commits "
              "touch only PREREGISTRATION.md; ancestors-of-HEAD=%s/%s; HEAD-vs-base diff "
              "%d file(s) all under %s/"
              % (sha[:8], (orig or "?")[:8], ORIGINAL_FREEZE[:8], (orig_parent or "?")[:8],
                 anc.returncode == 0, anc0.returncode == 0, len(head_files),
                 MY_DIR.rsplit('/', 1)[-1]))
    return record("MR-0", ok, detail + ("" if ok else " MISMATCH"))


# --- MR-1 clause identity (registry read-only) ------------------------------
def check_clause_identity(state):
    errs = []
    mat = state["kanban"]["cards"]["MAT2-A03"]
    ont = state["scope_archives"][SCOPE_ONT]["board"]["cards"]["ONT-A03"]
    if digest(mat["spec"]) != mat["criteria_sha256"] or mat["criteria_sha256"] != CRITERIA:
        errs.append("MAT2 spec digest %s" % digest(mat["spec"])[:12])
    if digest(ont["spec"]) != ont["criteria_sha256"] or ont["criteria_sha256"] != ONT_CRITERIA:
        errs.append("ONT spec digest %s" % digest(ont["spec"])[:12])
    ot = ont["spec"]["ontology_qualification"]
    mt = mat["spec"]["ontology_qualification"]
    if ot["definition_raw_sha256"] != mt["definition_raw_sha256"] or \
            mt["definition_raw_sha256"] != DEFINITION_RAW:
        errs.append("definition_raw mismatch")
    if digest(ot["task"]) != digest(mt["task"]) or digest(ot["task"]) != TASK_DIGEST:
        errs.append("task digest mismatch")
    diff = set(spec_diff_paths(ont["spec"], mat["spec"]))
    if diff != ENVELOPE_DIFF:
        errs.append("spec diff %s" % sorted(diff))
    att = (mat.get("attempts") or {}).get(ATTEMPT_ID) or {}
    if att.get("agent_id") != ARRIVAL_ID or att.get("state") != "WORKING" or \
            att.get("criteria_sha256") != CRITERIA:
        errs.append("attempt %s" % {k: att.get(k) for k in ("agent_id", "state", "criteria_sha256")})
    return (len(errs) == 0, "; ".join(errs) if errs else
            "digest(spec)==criteria both cards (ONT %s… / MAT2 %s…); definition_raw %s… equal; "
            "projected task digest %s… equal; spec diff exactly %s; attempt %s WORKING"
            % (ONT_CRITERIA[:8], CRITERIA[:8], DEFINITION_RAW[:8], TASK_DIGEST[:8],
               sorted(ENVELOPE_DIFF), ATTEMPT_ID[:8]))


# --- MR-3 committed-byte pins + envelope checks -----------------------------
def check_pins(replica: Path):
    errs = []
    for rel, want in PIN.items():
        raw = git_bytes("show", "%s:%s/%s" % (BASE, PREFIX, rel))
        got = sha256_bytes(raw)
        if got != want:
            errs.append("%s=%s" % (rel, got))
    rec = load_json(replica / "transforms" / "radius_supersession_record.json")
    for k, want in RECORD_ENVELOPE.items():
        if rec.get(k) != want:
            errs.append("record %s=%r" % (k, rec.get(k)))
    if "merge of this exact head" not in (rec.get("approval_semantics") or ""):
        errs.append("approval_semantics")
    b = rec.get("bounds") or {}
    for k in ("no_grasp_claim", "no_utility_selection", "not_anatomical", "staged_only"):
        if not b.get(k):
            errs.append("bounds %s missing" % k)
    dec = rec.get("decision") or {}
    if not (dec.get("basis") or "").startswith("SOURCE-KINEMATIC CONVENTION FIDELITY"):
        errs.append("decision.basis")
    if not dec.get("r1_verdict_sentence_verbatim") or \
            not (dec.get("r1_verdict_extraction") or {}).get("all_key_phrases_present"):
        errs.append("r1 verdict")
    if "NO moment-arm, utility" not in (dec.get("selection_rule") or ""):
        errs.append("selection_rule")
    if len(rec.get("superseded_set_enumerated_as_history") or []) != 4:
        errs.append("superseded set")
    for path, want in RECORD_VALUES.items():
        node = rec
        for part in path.split("."):
            node = (node or {}).get(part) if isinstance(node, dict) else None
        if node != want:
            errs.append("%s=%r" % (path, node))
    nr = load_json(replica / "evidence" / "numerical_receipt.json")
    for k, want in RECEIPT_ENVELOPE.items():
        if nr.get(k) != want:
            errs.append("receipt %s=%r" % (k, nr.get(k)))
    fb = nr.get("falsifier_bookkeeping") or {}
    if fb.get("F1_identity") != "no identity mismatch" or fb.get("F2_value") != "none":
        errs.append("falsifier_bookkeeping=%r" % (fb,))
    mani = load_json(replica / "evidence" / "capture_manifest.json")
    for k, want in MANIFEST_ENVELOPE.items():
        if mani.get(k) != want:
            errs.append("manifest %s=%r" % (k, mani.get(k)))
    ctx = load_json(replica / "evidence" / "capture_context.json")
    for k, want in CONTEXT_ENVELOPE.items():
        if ctx.get(k) != want:
            errs.append("context %s=%r" % (k, ctx.get(k)))
    qual = load_json(replica / "evidence" / "qualification_receipt.json")
    for k, want in QUAL_ENVELOPE.items():
        if qual.get(k) != want:
            errs.append("qual %s=%r" % (k, qual.get(k)))
    ir = (qual.get("evidence") or {}).get("independent_review") or {}
    if ir.get("pending") is not True:
        errs.append("qual independent_review.pending")
    return (len(errs) == 0, "; ".join(errs[:8]) if errs else
            "all %d file pins + record/receipt/manifest/context/qualification envelopes "
            "reproduce at the base" % len(PIN))


# --- MR-4 approval act + dependency (registry read-only) --------------------
def check_approval(state):
    errs = []
    ont = state["scope_archives"][SCOPE_ONT]["board"]["cards"]["ONT-A03"]
    w = ont.get("winner") or {}
    oq = w.get("ontology_qualification") or {}
    if not (w.get("pr_url") or "").endswith("/187"):
        errs.append("pr_url=%r" % (w.get("pr_url"),))
    if w.get("head_sha") != APPROVED_HEAD or w.get("merge_commit_sha") != MERGE_187:
        errs.append("winner head/merge")
    if w.get("merged_at") != MERGE_187_AT:
        errs.append("merged_at=%r" % (w.get("merged_at"),))
    review = None
    for u, p in (ont.get("prs") or {}).items():
        if isinstance(p, dict) and p.get("review"):
            review = p["review"]
    if not review or review.get("verdict") != "ACCEPTED" or \
            review.get("head_sha") != APPROVED_HEAD or \
            review.get("criteria_sha256") != ONT_CRITERIA:
        errs.append("review=%r" % (None if not review else review.get("verdict"),))
    if oq.get("task_id") != "A03" or oq.get("done_when_verified") is not True or \
            oq.get("profile_verified") is not True:
        errs.append("winner oq")
    ev = oq.get("evidence") or {}
    for kind, want in (("numerical", PIN["evidence/numerical_receipt.json"]),
                       ("visual", PIN["evidence/capture_sheet.png"]),
                       ("camera", PIN["evidence/capture_manifest.json"])):
        if (ev.get(kind) or {}).get("raw_sha256") != want:
            errs.append("winner evidence %s" % kind)
    anc = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor",
                          MERGE_187, BASE], capture_output=True)
    if anc.returncode != 0:
        errs.append("merge_187 not ancestor of base")
    a2 = state["kanban"]["cards"]["MAT2-A02"]
    w2 = a2.get("winner") or {}
    if a2.get("state") != "DONE" or w2.get("merge_commit_sha") != BASE or \
            not (w2.get("pr_url") or "").endswith("/214"):
        errs.append("MAT2-A02 dependency")
    return (len(errs) == 0, "; ".join(errs) if errs else
            "ONT-A03 winner PR #187 head %s… merged %s at %s, review ACCEPTED at that "
            "head, oq done_when_verified; merge is ancestor of base; MAT2-A02 DONE via "
            "PR #214 merge == base" % (APPROVED_HEAD[:8], MERGE_187[:8], MERGE_187_AT))


# --- MR-5 probe regeneration diffs -------------------------------------------
def diff_keys(committed: dict, regenerated: dict):
    def flat(o, pre=""):
        out = {}
        if isinstance(o, dict):
            for k in sorted(o):
                out.update(flat(o[k], pre + "." + k if pre else k))
            if not o:
                out[pre] = {}
        elif isinstance(o, list):
            for i, v in enumerate(o):
                out.update(flat(v, "%s[%d]" % (pre, i)))
            if not o:
                out[pre] = []
        else:
            out[pre] = o
        return out
    f1, f2 = flat(committed), flat(regenerated)
    diff = sorted(set(f1) ^ set(f2)) + sorted(k for k in set(f1) & set(f2) if f1[k] != f2[k])
    tops = sorted({k.split(".")[0].split("[")[0] for k in diff})
    return tops, diff


# --- MR-7 capture class -------------------------------------------------------
def camera_field_locator(cam, vis, manifest):
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
    missing = [k for k, (_, v) in mapping.items() if v is None]
    return missing, mapping


def mr7(replica: Path):
    errs = []
    manifest = load_json(replica / "evidence" / "capture_manifest.json")
    context = load_json(replica / "evidence" / "capture_context.json")
    vc_src = git_bytes("show", BASE + ":tools/monkey_campaign/visual_capture.py")
    ig_src = git_bytes("show", BASE + ":tools/monkey_campaign/integrity.py")
    (TMP / "visual_capture.py").write_bytes(vc_src)
    (TMP / "integrity.py").write_bytes(ig_src)
    play_vc = PLAY_CHECKOUT / "visual_capture.py"
    vc_identical = play_vc.read_bytes() == vc_src
    if not vc_identical:
        errs.append("play checkout visual_capture.py differs from base blob")
    play_vg_sha = sha256_file(PLAY_CHECKOUT / "visual_gate.py")
    play_ig_sha = sha256_file(PLAY_CHECKOUT / "integrity.py")
    if play_ig_sha != sha256_bytes(ig_src):
        errs.append("play checkout integrity.py differs from base blob")
    canonical = gate = "not run"
    sys.path.insert(0, str(TMP))
    sys.path.insert(1, str(PLAY_CHECKOUT))
    try:
        import visual_capture as vc
        structural = vc.validate_manifest(manifest, context, PROFILE)
        if structural.get("structurally_valid") is not True or structural.get("view_count") != 6:
            errs.append("canonical validator=%r" % (structural,))
        else:
            canonical = ("validate_manifest (base blob, play-copy byte-identical): "
                         "structurally_valid=%s view_count=%s"
                         % (structural["structurally_valid"], structural["view_count"]))
    except Exception as exc:  # noqa: BLE001 - falsifier path
        errs.append("canonical validator raised: %r" % (exc,))
    rows = manifest.get("views", [])
    pairs = {}
    for row in rows:
        pairs.setdefault(row.get("pair_id"), set()).add(row.get("mode"))
        cam, vis = row.get("camera", {}), row.get("visibility", {})
        miss, _ = camera_field_locator(cam, vis, manifest)
        if miss:
            errs.append("missing camera fields %s:%s=%s" % (row.get("pair_id"), row.get("mode"), miss))
        if row.get("mode") == "diagnostic" and vis.get("occlusion_mode") != "mixed":
            errs.append("diagnostic occlusion %s" % row.get("pair_id"))
        if row.get("mode") == "clean" and (vis.get("occlusion_mode") != "depth_tested"
                                           or vis.get("layers") != [] or vis.get("label_ids") != []):
            errs.append("clean row semantics %s" % row.get("pair_id"))
    if len(rows) != 6 or sorted(pairs) != ["V1", "V2", "V3"] or \
            any(v != {"diagnostic", "clean"} for v in pairs.values()):
        errs.append("rows/pairs=%r" % {k: sorted(v) for k, v in pairs.items()})
    by_pair = {}
    for row in rows:
        by_pair.setdefault(row["pair_id"], {})[row["mode"]] = row
    for pid, pair in by_pair.items():
        if pair.get("diagnostic", {}).get("camera") != pair.get("clean", {}).get("camera") or \
                pair.get("diagnostic", {}).get("state_binding") != pair.get("clean", {}).get("state_binding"):
            errs.append("pair %s camera/state mismatch" % pid)
    try:
        import visual_gate as vg
        mirror = {
            "evidence": {
                "camera": {"reference": str((replica / "evidence" / "capture_manifest.json").resolve()),
                           "raw_sha256": PIN["evidence/capture_manifest.json"]},
                "visual": {"reference": str((replica / "evidence" / "capture_sheet.png").resolve()),
                           "raw_sha256": PIN["evidence/capture_sheet.png"]},
            },
            "capture_context": context,
        }
        gate_receipt = vg.verify(mirror, MY_CONTRACT)
        if gate_receipt.get("structurally_valid") is not True or gate_receipt.get("view_count") != 6:
            errs.append("visual_gate.verify=%r" % (gate_receipt,))
        else:
            gate = ("visual_gate.verify(task_id A03 contract): structurally_valid=%s "
                    "view_count=%s" % (gate_receipt["structurally_valid"],
                                       gate_receipt["view_count"]))
    except Exception as exc:  # noqa: BLE001 - falsifier path
        errs.append("visual_gate.verify raised: %r" % (exc,))
    if sha256_file(replica / "evidence" / "capture_sheet.png") != PIN["evidence/capture_sheet.png"]:
        errs.append("replica PNG bytes differ from pin")
    detail = ("task_id A03 envelope, 6 rows V1/V2/V3 x diagnostic/clean, all 16 contract "
              "camera fields on every row, pairs share camera+state, PNG bound %s…; %s; %s; "
              "visual_capture+integrity imported as base blobs (play copies byte-identical), "
              "visual_gate from the play checkout (not in the base tree; A02 precedent), "
              "sha %s…; limits: CPU software-raster component capture, "
              "CAMERA_METADATA_STRUCTURE_ONLY, no native frames, no new human acceptance "
              "claimed" % (PIN["evidence/capture_sheet.png"][:8], canonical, gate,
                           play_vg_sha[:8]))
    if errs:
        detail = "; ".join(errs[:10])
    return record("MR-7", not errs, detail)


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    replica = extract(BASE, PREFIX, TMP / "replica_ont_a03")
    state = registry_state()

    mr0()
    ok, detail = check_clause_identity(state)
    record("MR-1", ok, detail)
    # MR-2 byte stability
    trees = {}
    for rev in (APPROVED_HEAD, MERGE_187, BASE):
        trees[rev] = {}
        for line in git("ls-tree", "-r", rev, "--", PREFIX).splitlines():
            meta, path = line.split("\t", 1)
            trees[rev][path] = meta.split()[2]
    same = all(trees[r] == trees[APPROVED_HEAD] for r in trees) and \
        len(trees[APPROVED_HEAD]) == EXPECTED_FILES
    record("MR-2", same, "files=%d (frozen %d) blob-identical across %s… -> %s… -> %s…"
           % (len(trees[APPROVED_HEAD]), EXPECTED_FILES, APPROVED_HEAD[:8],
              MERGE_187[:8], BASE[:8]) + ("" if same else " DRIFT"))
    ok, detail = check_pins(replica)
    record("MR-3", ok, detail)
    ok, detail = check_approval(state)
    record("MR-4", ok, detail)

    # MR-6 FIRST (pristine replica, committed evidence intact)
    suite = run_py(replica / "test_ota03_ulna_correspondence.py", replica)
    out_lines = [ln.strip() for ln in (suite.stdout + suite.stderr).splitlines() if ln.strip()]
    fail_lines = [ln for ln in out_lines if ln.startswith("FAIL ")]
    final = out_lines[-1] if out_lines else "<absent>"
    ok = (suite.returncode == 1 and final == PRISTINE_SUITE_LINE
          and fail_lines == ["FAIL " + PRISTINE_SUITE_FAIL_LINES[0]])
    record("MR-6", ok, "pristine suite exit=%d; final=%r; FAIL lines=%s (frozen exactly %r)"
           % (suite.returncode, final, fail_lines, PRISTINE_SUITE_FAIL_LINES))

    # MR-5 probe re-execution (regenerates staged record + receipts in replica)
    probe = run_py(replica / "ota03_ulna_correspondence.py", replica)
    p_lines = [ln.strip() for ln in (probe.stdout + probe.stderr).splitlines() if ln.strip()]
    p_final = p_lines[0] if p_lines else "<absent>"
    reg_rec_sha = sha256_file(replica / "transforms" / "radius_supersession_record.json")
    committed_state = load_jsonb(git_bytes("show", "%s:%s/evidence/state_snapshot.json"
                                           % (BASE, PREFIX)))
    committed_receipt = load_jsonb(git_bytes("show", "%s:%s/evidence/numerical_receipt.json"
                                             % (BASE, PREFIX)))
    reg_state = load_json(replica / "evidence" / "state_snapshot.json")
    reg_receipt = load_json(replica / "evidence" / "numerical_receipt.json")
    st_tops, _ = diff_keys(committed_state, reg_state)
    rc_tops, _ = diff_keys(committed_receipt, reg_receipt)
    bound = reg_receipt.get("state_snapshot_sha256") == sha256_file(
        replica / "evidence" / "state_snapshot.json")
    ok = (probe.returncode == 0 and p_final == EXPECTED_PROBE_LINE
          and reg_rec_sha == PIN["transforms/radius_supersession_record.json"]
          and st_tops == STATE_DIFF_KEYS and rc_tops == RECEIPT_DIFF_KEYS and bound)
    record("MR-5", ok, "probe exit=%d; final=%r; regenerated staged record sha %s…; "
           "state diff keys=%s (frozen %s); receipt diff keys=%s (frozen %s); "
           "regenerated receipt re-binds regenerated state=%s"
           % (probe.returncode, p_final, reg_rec_sha[:8], st_tops, STATE_DIFF_KEYS,
              rc_tops, RECEIPT_DIFF_KEYS, bound))

    # MR-5b suite re-run AFTER regeneration (Amendment 1 expectation)
    suite2 = run_py(replica / "test_ota03_ulna_correspondence.py", replica)
    out2 = [ln.strip() for ln in (suite2.stdout + suite2.stderr).splitlines() if ln.strip()]
    fails2 = [ln for ln in out2 if ln.startswith("FAIL ")]
    final2 = out2[-1] if out2 else "<absent>"
    ok = (suite2.returncode == 1 and final2 == REGSUITE_LINE
          and fails2 == ["FAIL " + REGSUITE_FAIL_LINES[0]])
    record("MR-5b", ok, "post-regeneration suite exit=%d; final=%r; FAIL lines=%s "
           "(frozen exactly %r: the committed manifest binds the committed state hash;"
           " regenerating the state snapshot in a path-changed replica breaks exactly that"
           " binding)" % (suite2.returncode, final2, fails2, REGSUITE_FAIL_LINES))

    mr7(replica)

    # MR-8 failing-first
    # (a) staged-record tamper on a FRESH PRISTINE extraction (committed evidence)
    tam = extract(BASE, PREFIX, TMP / "tamper_record")
    srp = tam / "transforms" / "radius_supersession_record.json"
    raw = srp.read_text(encoding="utf-8")
    assert raw.count("STAGED_FOR_ARCHITECT_APPROVAL") >= 1
    srp.write_text(raw.replace("STAGED_FOR_ARCHITECT_APPROVAL", "TAMPERED_RECORD", 1),
                   encoding="utf-8")
    ok_a, why_a = check_pins(tam)
    fired_a = not ok_a and "status" in why_a
    # (b) registry head tamper (in-memory)
    state_b = deepcopy(state)
    ob = state_b["scope_archives"][SCOPE_ONT]["board"]["cards"]["ONT-A03"]
    ob["winner"]["head_sha"] = "0" * 39 + "1"
    ok_b, why_b = check_approval(state_b)
    fired_b = not ok_b
    record("MR-8ab", fired_a and fired_b,
           "(a) record tamper (1 token status->TAMPERED_RECORD) check_pins fails with %r; "
           "(b) winner head tamper check_approval fails (%s)"
           % (why_a[:80], "fired" if fired_b else "NOT FIRED: " + why_b[:80]))
    # (c) one-ulp receipt-08 tamper -> probe DISCREPANCY_RECORDED
    tam2_dir = TMP / "tamper_receipt"
    extract(BASE, PREFIX, tam2_dir)
    r08 = tam2_dir / "reference" / "receipts" / "I7_08_radius_before_after.json"
    raw8 = r08.read_text(encoding="utf-8")
    needle = "0.22170679566544982"
    assert needle in raw8, "frozen tamper needle absent from receipt 08"
    r08.write_text(raw8.replace(needle, "0.22170679566544983", 1), encoding="utf-8")
    probe2 = run_py(tam2_dir / "ota03_ulna_correspondence.py", tam2_dir)
    t_lines = [ln.strip() for ln in (probe2.stdout + probe2.stderr).splitlines() if ln.strip()]
    t_final = t_lines[0] if t_lines else "<absent>"
    import re
    m = re.search(r"checks (\d+)/(\d+) PASS  outcome=(\S+)", t_final)
    got_pass = int(m.group(1)) if m else -1
    outcome2 = m.group(3) if m else "?"
    fired_c = (m is not None and outcome2 == "DISCREPANCY_RECORDED" and got_pass < 75)
    record("MR-8c", fired_c,
           "one-ulp tamper of pinned receipt 08 (radius before scale) -> probe final=%r "
           "(outcome=%s, pass=%d<75, M0 identity/provenance checks fail as recorded by the "
           "merged review)" % (t_final, outcome2, got_pass))

    failures = [r for r in RESULTS if not r["pass"]]
    receipt = {
        "schema": "chimera.mat2_a03_adoption_receipt.v1",
        "task_id": "A03",
        "card_id": "MAT2-A03",
        "attempt_id": ATTEMPT_ID,
        "criteria_sha256": CRITERIA,
        "preregistration_freeze_commit": FREEZE_COMMIT,
        "original_freeze_commit": ORIGINAL_FREEZE,
        "candidate_base": BASE,
        "anchors": {"approved_head": APPROVED_HEAD, "merge_187": MERGE_187,
                    "base": BASE,
                    "ont_card_criteria": ONT_CRITERIA,
                    "ont_scope": SCOPE_ONT,
                    "definition_raw_sha256": DEFINITION_RAW,
                    "projected_task_digest": TASK_DIGEST},
        "adopted_record": {
            "path": PREFIX + "/transforms/radius_supersession_record.json",
            "sha256": PIN["transforms/radius_supersession_record.json"],
            "status": "STAGED_FOR_ARCHITECT_APPROVAL",
            "approval_act": "lead merge of exact head 051d341da2c0786fe9706d169fe16b8127cb8772"
                            " as PR #187 merge 4aecbc9ee98cb115ec9a690f5c0df173d9f3efbf"
                            " (registry ACCEPTED, 2026-09-27T06:44:32Z); record status kept"
                            " exactly as merged",
        },
        "probes": RESULTS,
        "outcome": "ADOPTED_AND_REVERIFIED" if not failures else "FALSIFIER_FIRED",
        "checks_pass": sum(1 for r in RESULTS if r["pass"]),
        "checks_total": len(RESULTS),
        "probe_corrections": [
            "Amendment 1 (commit a0c1e5549d9ed9db59438450a812ba00a1cd22a3, child of the"
            " original freeze 5019ceea9d0a23e5c41be27a8cfd73c08290a414, both touching only"
            " PREREGISTRATION.md): corrected the mis-derived MR-5b prediction before the"
            " confirmatory run; full disclosure in PREREGISTRATION.md Amendment 1 section.",
            "Instrument shakeout (first probe run, receipts discarded, observations"
            " preserved in REPORT.md): (1) spec-diff path formatting fixed to match the"
            " frozen 'depends_on[0]' wording; (2) removed a wrongly-assumed"
            " criteria_sha256 field from the receipt envelope pins (the merged receipt has"
            " none; the frozen MR-3 text never pinned one); (3) visual_gate import moved to"
            " the play checkout because visual_gate.py is not part of the base tree (the"
            " A02 merged precedent imported it the same way); its sha256 is recorded in"
            " the MR-7 detail.",
        ],
        "environmental_notes": [
            "MR-6 reproduces the merged independent review's recorded environmental"
            " behavior on a path-changed replica: the committed state snapshot embeds"
            " the original ONT-A03 attempt checkout's absolute staged_record_path, so"
            " exactly that one check fails on the pristine replica; the key-level diff"
            " (MR-5) shows staged_record_path is the ONLY differing state key and"
            " state_snapshot_sha256 the ONLY differing receipt key.",
            "MR-5b (Amendment 1) reproduces the same family on the regenerated replica:"
            " the committed capture manifest pins the committed state snapshot's hash,"
            " so regenerating the state snapshot breaks exactly that one binding;"
            " suite 138/138 requires the original attempt checkout path, as the merged"
            " review recorded. Both committed pairs (state<->receipt,"
            " manifest->state) are verified intact at the base by MR-3/MR-7.",
        ],
        "bounds_carried": {
            "no_grasp_claim": "this adoption does NOT authorize mechanically qualified"
                              " grasp (G-chain work remains)",
            "no_utility_selection": "no moment-arm/utility evidence entered the selection",
            "not_anatomical": "basis is kinematic-convention fidelity; R1's refutation"
                              " retained verbatim and never relabeled",
            "staged_only": "nothing outside the merged ONT-A03 contribution was executed"
                           " or written; no production source, model store, fit or training"
                           " body is touched by this card",
        },
        "honesty": {"cpu_only": True, "gpu_used": False, "native_engine_run": False,
                    "network_used": False,
                    "note": "read-only probe over committed bytes + registry read-only;"
                            " temp replicas under attempt workspace probe_tmp/;"
                            " ONT-A03 contribution bytes never modified"},
    }
    ev = Path(__file__).resolve().parent / "evidence"
    ev.mkdir(exist_ok=True)
    rec_path = ev / "reconciliation_receipt.json"
    rec_path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    qual = {
        "schema": "chimera.mat2_a03_qualification.v1",
        "task_id": "A03",
        "card_id": "MAT2-A03",
        "attempt_id": ATTEMPT_ID,
        "arrival_id": ARRIVAL_ID,
        "criteria_sha256": CRITERIA,
        "scope_sha256": SCOPE_MAT2,
        "preregistration_freeze_commit": FREEZE_COMMIT,
        "original_freeze_commit": ORIGINAL_FREEZE,
        "candidate_base": BASE,
        "kind": "decision+implementation",
        "done_when": "Architect approves mapping/supersession, historical radius"
                     " preserved, new transforms and regressions qualified",
        "done_when_verified": not failures,
        "profile_verified": not failures,
        "reconciliation_receipt_sha256": sha256_file(rec_path),
        "evidence": {
            "adopted_supersession_record": {
                "reference": PREFIX + "/transforms/radius_supersession_record.json",
                "raw_sha256": PIN["transforms/radius_supersession_record.json"],
                "base": BASE,
            },
            "merged_numerical_receipt": {
                "reference": PREFIX + "/evidence/numerical_receipt.json",
                "raw_sha256": PIN["evidence/numerical_receipt.json"],
            },
            "merged_capture_sheet": {
                "reference": PREFIX + "/evidence/capture_sheet.png",
                "raw_sha256": PIN["evidence/capture_sheet.png"],
            },
            "merged_capture_manifest": {
                "reference": PREFIX + "/evidence/capture_manifest.json",
                "raw_sha256": PIN["evidence/capture_manifest.json"],
            },
            "approval_act": {
                "reference": "registry scope_archives/%s/board/cards/ONT-A03 winner" % SCOPE_ONT,
                "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/187",
                "head_sha": APPROVED_HEAD,
                "merge_commit_sha": MERGE_187,
                "review_verdict": "ACCEPTED",
            },
        },
        "visual_applicability": {
            "class": "visible_static anatomy (anatomy profile)",
            "delivered": "the merged ONT-A03 capture (6 rows V1/V2/V3 x diagnostic/clean,"
                         " all 16 contract camera fields, campaign schema"
                         " chimera.visual_capture_manifest.v1, CONTRACT task_id A03"
                         " envelope) is bound byte-exact and revalidated structurally at"
                         " this base (MR-7)",
            "limits": "CPU software-raster component capture; CAMERA_METADATA_STRUCTURE_ONLY;"
                      " visual_acceptance=false declared; not native engine frames; no new"
                      " human acceptance claimed by this card",
        },
        "head_sha": None,
        "independent_review": {
            "pending": True,
            "note": "only the independently assigned reviewer fills reference+raw_sha256;"
                    " zero digests and head_sha None are honest placeholders exactly as in"
                    " the accepted A01/A02 receipts",
        },
        "bounds": receipt["bounds_carried"],
    }
    (ev / "qualification_receipt.json").write_text(
        json.dumps(qual, indent=2, sort_keys=True), encoding="utf-8")
    print("outcome:", receipt["outcome"], "(%d/%d probes pass)" %
          (receipt["checks_pass"], receipt["checks_total"]))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
