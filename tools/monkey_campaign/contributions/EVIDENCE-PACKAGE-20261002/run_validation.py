"""run_validation.py — VALIDATION-ONLY evidence-package build + falsifier probes.

Lane wk-evidence-package. This battery runs NO new physics: it replays the
SEALED MAT2-W08 commanded-walk store bytes (evidence-store/MAT2-W08) through
the chimera.evidence_package.v1 builder (build_package.py, same directory) to
prove the PACKAGE FORMAT + TOOLING for the GOAL's final deliverable:

  one evidence package binds the build and inputs to continuous video, player
  inputs, and time-aligned state, contact, force, and energy records.

Everything here is VALIDATION-ONLY (format proof; NOT the final demonstration).

Positive path:
  P0 store-pin assertion (drift = input_pin_drift refusal, never a warning)
  P1 build the VALIDATION-ONLY package over the sealed W08 run
  P2 verify it (freeze law: every binding re-hashed)
  P3 inspect it (content address re-checked)

Falsifier probes (each MUST refuse with its exact named code; a probe that
does not refuse FALSIFIES the format claim and fails this battery):
  A1 frame tick outside the records domain -> sync_frame_outside_tick_domain
  A2 duplicate frame tick                  -> sync_frame_ticks_not_unique_monotonic
  B1 post-freeze artifact modification     -> freeze_violation
  B2 package body edit                     -> package_tampered
  C1 injected wrong_script event           -> input_assertion_violation(wrong_script)
  C2 applied != requested, zero saturation -> input_assertion_violation(teleport)
  C3 injected teleport intervention row    -> input_assertion_violation(teleport)
  C4 event tick outside domain             -> input_event_outside_domain
  C5 deleted row (reset-class gap)         -> records_tick_domain_not_contiguous
  C6 duplicated tick (counter restart)     -> records_duplicate_tick
  D  decisions removed                     -> input_log_not_expressible

Outputs (declared keeps, CHIMERA_OUTPUT_DIR):
  outputs/validation_package.json
  outputs/validation_package.verification.json
  outputs/falsifier_probes.json
  outputs/VALIDATION_ONLY_REPORT.md
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import build_package  # noqa: E402  (the builder under test, same contribution dir)

STORE = Path("E:/ChimeraWork/monkey-coordination/evidence-store")
CARD = "MAT2-W08"
OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or (HERE / "_outputs"))

# Authoring-time identity pins for the identity-bearing artifacts (cross-checked
# against the store MANIFEST.json rows at run; any drift refuses).
AUTHORING_PINS = {
    "trace": "ee3413d19a812374121ccd73b6ecbfbc1bf1571ed8dbb2146da841b242b4209e",
    "video_media": "3d991a8b7a0af2769941c0077c7d7525afb511222974acbd73fc950fa2f09751",
    "preregistration": "00a04e08411ed079aee9e0ef43f9221c69abc84612f66311e4db4822f6c8412a",
    "capture_receipt": "32f56d59f164572a2ce0315c77012f8fd75f3212b09ca89e3ab2c232781d8d14",
}
STORE_FILES = {
    "trace": "numerical/trace_commanded.json",
    "trace_r1_determinism_twin": "numerical/trace_commanded_r1.json",
    "command_verification_receipt": "numerical/command_verification_receipt.json",
    "checks_receipt": "numerical/checks_receipt.json",
    "capture_manifest": "camera/capture_manifest.json",
    "capture_validation_receipt": "camera/capture_validation_receipt.json",
    "capture_receipt": "camera/capture_receipt.json",
    "video_media": "visual/capture_commanded.mkv",
    "preregistration": "source/PREREGISTRATION.md",
    "report": "verdict_ref/REPORT.md",
}

# The lineage lane's CURRENT authority, re-hashed from the owning lane's bytes
# at revision time (2026-10-03, post RC-2 correction) and again by this
# battery at run. It is BOUND as the `lineage_report` frozen binding so
# build/verify re-hash it — a citation-only sha escapes every re-hash gate by
# design (SGT review F1, durable lesson 1). Prior round 79aa4997... is
# SUPERSEDED (the owning lane's EVIDENCE line 94 names the supersession).
LINEAGE_REPORT = "E:/ChimeraWork/monkey-coordination/lineage-verify/REPORT.md"
LINEAGE_REPORT_SHA256 = "b7801ce08b53f9f16edbbf67607406e48cdd919d95b44fc6f7f5055e3fbe384f"

problems = []
probes = []


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fail(msg):
    problems.append(msg)
    print("FAIL: %s" % msg)


def store_pins():
    """P0: resolve every bound artifact from the store MANIFEST.json rows and
    hash-assert the file bytes (input_pin_drift law)."""
    manifest = json.loads((STORE / "MANIFEST.json").read_text(encoding="utf-8"))
    rows = {f["stored_rel_path"]: f for f in manifest["files"]}
    pins = {}
    for name, rel in STORE_FILES.items():
        key = "%s/%s" % (CARD, rel) if rel != "MANIFEST.json" else rel
        row = rows.get(key)
        if row is None:
            fail("store_manifest_row_missing: %s" % key)
            continue
        full = STORE / key
        if not full.is_file():
            fail("store_file_missing: %s" % key)
            continue
        observed = sha256_file(full)
        if observed != row["sha256"]:
            fail("input_pin_drift: %s manifest=%s observed=%s"
                 % (key, row["sha256"], observed))
            continue
        authoring = AUTHORING_PINS.get(name)
        if authoring and authoring != observed:
            fail("authoring_pin_drift: %s authoring=%s observed=%s"
                 % (name, authoring, observed))
            continue
        pins[name] = {"reference": str(full), "expected_sha256": observed,
                      "size_bytes": row["size_bytes"]}
        print("P0 ok: %-32s %s" % (name, observed[:16]))
    require_pins(pins)
    return pins


def require_pins(pins):
    missing = [n for n in STORE_FILES if n not in pins]
    if missing:
        fail("pins_incomplete: %s" % missing)
        finish()


def scratch_dir(name):
    path = OUT / "_probe_scratch" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_to(path, dest_dir, dest_name=None):
    dest = Path(dest_dir) / (dest_name or Path(path).name)
    shutil.copyfile(path, dest)
    return dest


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_package.canon(payload) + b"\n")
    return path


def run_tool(argv, expected_refusal=None, probe_name=None, ledger_dir=None):
    """Run the builder CLI in-process; read the refusal (if any) from the
    ledger next to the --out/--package target."""
    ledger = Path(ledger_dir) / "refusals.jsonl" if ledger_dir else None
    before = ledger.stat().st_size if ledger and ledger.exists() else 0
    code = build_package.main(argv)
    row = None
    if ledger and ledger.exists() and ledger.stat().st_size > before:
        with open(ledger, "rb") as stream:
            stream.seek(before)
            line = stream.readline().strip()
            if line:
                row = json.loads(line)
    refused = (row or {}).get("refused")
    if expected_refusal is None:
        if code != 0:
            fail("expected success, exit=%s refused=%s" % (code, refused))
        return code, row
    if probe_name is None:
        probe_name = expected_refusal
    entry = {"probe": probe_name, "expected_refusal": expected_refusal,
             "exit_code": code, "observed_refusal": refused,
             "observed_detail": (row or {}).get("detail")}
    if code != build_package.EXIT_REFUSED or refused != expected_refusal:
        entry["result"] = "FALSIFIED"
        fail("probe %s: expected refusal %s, got exit=%s refused=%s"
             % (probe_name, expected_refusal, code, refused))
    else:
        entry["result"] = "REFUSED_AS_EXPECTED"
        print("probe ok: %-42s -> %s" % (probe_name, refused))
    probes.append(entry)
    return code, row


def base_assembly(pins, trace_binding="trace", manifest_binding="capture_manifest",
                  receipt_binding="capture_validation_receipt",
                  media_binding="video_media", extra_labels=""):
    return {
        "package_class": "VALIDATION_ONLY",
        "label": "VALIDATION-ONLY format proof over the sealed MAT2-W08 "
                 "commanded walk (store-replay; NOT the final demonstration; "
                 "no new physics)" + extra_labels,
        "run_identity": {
            "run_id": "MAT2-W08-commanded-seam-R1 (sealed store card MAT2-W08)",
            "producer_card": CARD,
            "command": "python -B run_command_verification.py (W08 card; "
                       "store replay only in this validation)",
            "seed": 20260920,
            "tick_domain": [0, 10499],
            "dt_s": None,
            "dt_s_status": "NOT_PINNED_IN_VALIDATION (not needed for the "
                           "format proof; the FINAL package requires dt pinned)",
        },
        "bindings": dict(pins),
        "freeze_manifest": {
            "build": {
                "build_id": "cpu-walk-scene-build-N (from the bound trace)",
                "state_chain_sha256": "1145c26550f43382aa70172f0ae5ff0ab4bc972faab5a7428737d9c2e0bb06b3",
                "final_state_sha256": "2ade03d79d565ff9456e9e3a4cfa7325165d673e0dcab1eb129f861859f2f73e",
                "subject_sha256_source": "capture_validation_receipt (bound)",
                "pin_source": "command_verification_receipt.runs (bound)",
            },
            "scene": {
                "scene_line_reference": "the 10.038 kg W03 sealed walk scene-line "
                                        "(scene.json sha256 f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342 "
                                        "per ASSEMBLY_IDENTITY.md, wk-assembly-identity)",
                "status": "EXTERNAL_REFERENCE_PENDING",
                "why_pending": "validation binds the lineage REFERENCE; the "
                               "byte-level scene pin for the FINAL package comes "
                               "from the lineage-verify lane verdict",
            },
            "body_mass_ownership": {
                "reference": "E:/ChimeraWork/monkey-coordination/lineage-verify/"
                             "REPORT.md (LIFT verdict: SEALED-DYNAMICS-MASS; "
                             "cite, never re-derive) + ASSEMBLY_IDENTITY.md "
                             "(wk-assembly-identity)",
                "reference_binding": "lineage_report",
                "reference_sha256": LINEAGE_REPORT_SHA256,
                "supersession_note": "b7801ce0... is the OWNING lane's current "
                                     "authority (its EVIDENCE line 94); the "
                                     "prior round 79aa4997... is superseded "
                                     "and must never be cited",
                "table_digest_policy": "the FINAL package binds table_sha256; "
                                       "this VALIDATION-ONLY package references, "
                                       "never duplicates",
                "status": "EXTERNAL_REFERENCE_PENDING",
                "lv1_finding": "the home checkout's untracked stray "
                               "tools/science_funnel/gait_scene.py (blob "
                               "95c8b457) builds a DIFFERENT 10-body assembly; "
                               "live-runtime mass claims stay gated until the "
                               "build emits a frozen per-body mass table",
                "emission_status": "EMISSION_RECEIPT_PENDING",
                "emission_receipt_law": "at FINAL freeze the build itself emits "
                                        "its per-body mass table at launch "
                                        "(owner + mass + source-artifact sha per "
                                        "part), hashed into this manifest; the "
                                        "sealed scene bytes alone are not "
                                        "sufficient (LV-1)",
            },
            "control_interface": {
                "name": "u01_input_mapper commanded seam (sink_records source)",
                "command_vector_dim": 8,
                "command_names_source": "command_verification_receipt.command_table",
                "source_of_record": "trace decisions + sink_records",
            },
            "parameters": {
                "seed": 20260920,
                "tick_domain": [0, 10499],
                "pin_source": "command_verification_receipt (seed, horizons)",
            },
            "pass_criteria": {
                "preregistration_sha256": pins["preregistration"]["expected_sha256"],
                "criteria_source": "command_verification_receipt.criteria_sha256",
                "receipts": ["command_verification_receipt", "checks_receipt"],
            },
        },
        "video": {
            "media_binding": media_binding,
            "manifest_binding": manifest_binding,
            "receipt_binding": receipt_binding,
            "still_bytes": "MEDIA_EMBEDDED_PINNED (the W08 per-frame stills are "
                           "tick-keyed in the sealed sheet; loose PNGs are not "
                           "store-homed for this card - named gap, never silent)",
        },
        "inputs": {
            "events_from": "trace",
            "binding": trace_binding,
            "source_default": "u01_input_mapper",
            "intervention_field": "intervention_reason",
            "allowed_interventions": ["none"],
        },
        "records": {
            "binding": trace_binding,
            "tick_key": "tick",
            "tick_domain": [0, 10499],
            "classes": {
                "state": ["state_sha256", "com_x_m", "com_v_m_s", "phase_left",
                          "phase_right", "yaw_rate_rad_s", "trip_l", "trip_r"],
                "contact": ["contact_count", "foot_contacts", "pad_gaps"],
                "force": ["foot_forces", "applied_cmd", "saturation"],
            },
            "declared_absent": [{
                "class": "energy",
                "reason": "the W08 commanded-seam harness recorded no per-tick "
                          "energy ledger (K02 acct_rows class); com_v_m_s is "
                          "present but no mass ownership is bound in "
                          "validation, so no KE ledger is derived. The FINAL "
                          "package requires the energy class PRESENT.",
            }],
        },
        "phases": {"boundaries": []},  # filled from the command table at run
        "review_plan": {
            "per_phase_transition_evidence": "each declared command-table "
                                             "boundary resolves to records rows; "
                                             "the reviewer inspects rows+frames "
                                             "at the boundary ticks",
            "phase_continuity_law": "one uninterrupted run: a single contiguous "
                                    "tick domain, no reset between phases "
                                    "(mechanically proven by the no_reset check)",
            "frame_sample_law": "independent reviewer re-checks a bounded frame "
                                "sample (>= the standing >=20-frame picture "
                                "review sample) against the bound records rows "
                                "(state_sha256 + phase + contact census); "
                                "picture review routes through the Lieutenant "
                                "to the Flash Sergeant (this lane claims no "
                                "picture verification authority)",
            "physical_claims": "the reviewer verifies claims against the FROZEN "
                               "pass criteria (preregistration sha in the "
                               "freeze manifest), never against prose",
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    print("== wk-evidence-package VALIDATION-ONLY battery ==")
    print("   builder: %s (%s)" % (HERE / "build_package.py",
                                  build_package.TOOL_VERSION))

    pins = store_pins()
    if problems:
        finish()

    # Citation re-check AT RUN TIME (durable lesson 1, SGT review F1): the
    # lineage authority is re-hashed from the owning lane's bytes NOW, never
    # trusted from the authoring-time constant alone.
    observed_lineage = sha256_file(LINEAGE_REPORT)
    if observed_lineage != LINEAGE_REPORT_SHA256:
        fail("lineage_citation_drift: expected %s observed %s"
             % (LINEAGE_REPORT_SHA256, observed_lineage))
        finish()
    print("P0 ok: lineage_report (re-hashed at run)   %s"
          % observed_lineage[:16])

    cmd_receipt = json.loads(Path(pins["command_verification_receipt"]["reference"])
                             .read_text(encoding="utf-8"))
    table = cmd_receipt.get("command_table") or []
    boundaries = []
    for entry in table:
        ticks = entry.get("issued_ticks") or ([entry["issued_tick"]]
                                              if entry.get("issued_tick") is not None else [])
        for tick in ticks:
            boundaries.append({"phase": entry.get("command"), "tick": int(tick)})

    # ---------------- P1: the positive build ----------------
    # CHIMERA_OUTPUT_DIR is the keep root: keeps are declared as
    # outputs/<name> and resolve to OUT/<name>; write the package there.
    work = scratch_dir("positive")
    local = {}
    for name in STORE_FILES:
        local[name] = {"reference": pins[name]["reference"],
                       "expected_sha256": pins[name]["expected_sha256"]}
    # The lineage citation travels as a BOUND artifact (re-hashed at build and
    # verify), never as prose.
    local["lineage_report"] = {"reference": LINEAGE_REPORT,
                               "expected_sha256": LINEAGE_REPORT_SHA256}
    assembly = base_assembly(local)
    assembly["phases"]["boundaries"] = boundaries
    assembly_path = write_json(work / "assembly.json", assembly)
    package_path = OUT / "validation_package.json"
    run_tool(["build", "--assembly", str(assembly_path), "--out", str(package_path)],
             ledger_dir=str(OUT))
    if problems:
        finish()
    package = json.loads(package_path.read_text(encoding="utf-8"))
    print("P1 ok: package %s class=%s" % (package["package_sha256"][:16],
                                          package["package_class"]))

    # format assertions on the built package
    fb = package["video"]["frame_binding"]
    assert package["package_class"] == "VALIDATION_ONLY"
    assert "VALIDATION-ONLY" in package["label"].upper().replace("_", "-")
    assert package["records"]["tick_domain"] == [0, 10499]
    assert package["records"]["contiguous"] is True
    assert fb["frame_count"] == 60, "expected 60 bound frames, got %s" % fb["frame_count"]
    assert package["inputs"]["event_count"] == 403, package["inputs"]["event_count"]
    assert len(package["freeze_manifest"]["bindings"]) == 11
    assert package["inputs"]["session_sources"] == ["u01_input_mapper"]
    assert package["inputs"]["declared_source_default"] == "u01_input_mapper"
    assert [d["class"] for d in package["records"]["declared_absent"]] == ["energy"]
    assert package["inputs"]["assertions"] == {"no_teleport": "PASS",
                                               "no_hidden_anchor": "PASS",
                                               "no_reset": "PASS"}
    print("P1 ok: 60 frames resolved, 10500 contiguous ticks, 403 events, "
          "11 frozen bindings (incl. the bound lineage_report), energy named-absent")

    # ---------------- P2/P3: verify + inspect ----------------
    run_tool(["verify", "--package", str(package_path), "--allow-overwrite"],
             ledger_dir=str(OUT))
    run_tool(["inspect", "--package", str(package_path)])
    if problems:
        finish()

    # ---------------- Falsifier probes ----------------
    # A1: frame tick outside the records domain (desync class).
    a1 = scratch_dir("a1")
    tampered = json.loads(Path(pins["capture_manifest"]["reference"])
                          .read_text(encoding="utf-8"))
    key = sorted(tampered["sheet_layout"]["frame_files"], key=int)[0]
    tampered["sheet_layout"]["frame_files"]["99999999"] = \
        tampered["sheet_layout"]["frame_files"].pop(key)
    a1_manifest = write_json(a1 / "capture_manifest.json", tampered)
    a1_pins = dict(local)
    a1_pins["capture_manifest"] = {"reference": str(a1_manifest)}
    a1_assembly = base_assembly(a1_pins)
    a1_assembly["phases"]["boundaries"] = boundaries
    run_tool(["build", "--assembly",
              str(write_json(a1 / "assembly.json", a1_assembly)),
              "--out", str(a1 / "package.json")],
             expected_refusal="sync_frame_outside_tick_domain",
             probe_name="A1_frame_tick_outside_domain",
             ledger_dir=str(a1))

    # A2: duplicate frame tick via a zero-padded alias key — the keeper is
    # the FIRST NUMERICALLY-SORTED key (tick 300 in the W08 sheet), so the
    # alias '0300' parses to the same tick as '300' (F3: the earlier draft
    # wrongly exemplified this as '01310'/'1310'); the declared count is
    # bumped so the count law does not mask the uniqueness law.
    a2 = scratch_dir("a2")
    tampered = json.loads(Path(pins["capture_manifest"]["reference"])
                          .read_text(encoding="utf-8"))
    keys = sorted(tampered["sheet_layout"]["frame_files"], key=int)
    keeper = keys[0]
    tampered["sheet_layout"]["frame_files"]["0" + keeper] = \
        tampered["sheet_layout"]["frame_files"][keeper]
    tampered["sheet_layout"]["frame_count"] = \
        tampered["sheet_layout"]["frame_count"] + 1
    a2_manifest = write_json(a2 / "capture_manifest.json", tampered)
    a2_pins = dict(local)
    a2_pins["capture_manifest"] = {"reference": str(a2_manifest)}
    a2_assembly = base_assembly(a2_pins)
    a2_assembly["phases"]["boundaries"] = boundaries
    run_tool(["build", "--assembly",
              str(write_json(a2 / "assembly.json", a2_assembly)),
              "--out", str(a2 / "package.json")],
             expected_refusal="sync_frame_ticks_not_unique_monotonic",
             probe_name="A2_duplicate_frame_tick",
             ledger_dir=str(a2))

    # B1/B2: the freeze law over scratch-copied bindings.
    b = scratch_dir("b")
    b_pins = {}
    for name in STORE_FILES:
        copied = copy_to(pins[name]["reference"], b)
        observed = sha256_file(copied)
        b_pins[name] = {"reference": str(copied), "expected_sha256": observed}
    # distinct scratch name: both this report and the W08 verdict_ref/REPORT.md
    # are named REPORT.md; a naive copy overwrites the W08 binding's bytes and
    # the freeze law (correctly) refuses binding_hash_mismatch (dev4 lesson).
    b_lineage = copy_to(LINEAGE_REPORT, b, dest_name="lineage_REPORT.md")
    b_pins["lineage_report"] = {"reference": str(b_lineage),
                                "expected_sha256": sha256_file(b_lineage)}
    b_assembly = base_assembly(b_pins)
    b_assembly["phases"]["boundaries"] = boundaries
    b_package = b / "validation_package.json"
    run_tool(["build", "--assembly",
              str(write_json(b / "assembly.json", b_assembly)),
              "--out", str(b_package)],
             ledger_dir=str(b))
    if problems:
        finish()
    # B1: modify a bound artifact AFTER the freeze.
    victim_media = b / "capture_commanded.mkv"
    data = bytearray(victim_media.read_bytes())
    data[-1] ^= 0xFF
    victim_media.write_bytes(bytes(data))
    run_tool(["verify", "--package", str(b_package), "--allow-overwrite"],
             expected_refusal="freeze_violation",
             probe_name="B1_post_freeze_modification",
             ledger_dir=str(b))
    # B2: edit the package body itself.
    b2_package = b / "validation_package_tampered.json"
    pkg = json.loads(b_package.read_text(encoding="utf-8"))
    pkg["label"] = "tampered label"
    write_json(b2_package, pkg)
    run_tool(["verify", "--package", str(b2_package), "--allow-overwrite"],
             expected_refusal="package_tampered",
             probe_name="B2_package_body_edit",
             ledger_dir=str(b))

    # E1: a STALE CITATION (the superseded prior-round lineage sha) refuses —
    # the F1 regression probe. Citation-only references escape every re-hash
    # gate by design; a cited sha must equal its bound binding's observed sha.
    e1 = scratch_dir("e1")
    e1_pins = dict(local)
    e1_assembly = base_assembly(e1_pins)
    e1_assembly["phases"]["boundaries"] = boundaries
    e1_assembly["freeze_manifest"]["body_mass_ownership"]["reference_sha256"] = \
        "79aa499755eed5619969deaf8b69044dfb0d0a83662cdd9f850c892c58aab148"
    run_tool(["build", "--assembly",
              str(write_json(e1 / "assembly.json", e1_assembly)),
              "--out", str(e1 / "package.json")],
             expected_refusal="freeze_citation_stale",
             probe_name="E1_stale_lineage_citation",
             ledger_dir=str(e1))

    # E2: an UNBOUND citation refuses — the reference names a binding that is
    # not in the freeze bindings.
    e2 = scratch_dir("e2")
    e2_pins = dict(local)
    e2_assembly = base_assembly(e2_pins)
    e2_assembly["phases"]["boundaries"] = boundaries
    e2_assembly["freeze_manifest"]["body_mass_ownership"]["reference_binding"] = \
        "lineage_report_not_bound"
    del e2_assembly["freeze_manifest"]["body_mass_ownership"]["reference_sha256"]
    run_tool(["build", "--assembly",
              str(write_json(e2 / "assembly.json", e2_assembly)),
              "--out", str(e2 / "package.json")],
             expected_refusal="freeze_citation_unbound",
             probe_name="E2_unbound_lineage_citation",
             ledger_dir=str(e2))

    # C-probes: input assertions + reset-class desync over tampered traces.
    trace_path = Path(pins["trace"]["reference"])

    def c_probe(name, mutate, expected, detail_class=None):
        cdir = scratch_dir("c_" + name)
        tampered = json.loads(trace_path.read_text(encoding="utf-8"))
        mutate(tampered)
        tampered_path = write_json(cdir / "trace_commanded.json", tampered)
        c_pins = dict(local)
        c_pins["trace"] = {"reference": str(tampered_path)}
        # neutralize the video<->trace identity receipt for THIS probe
        # (the probe targets the input law in isolation)
        c_assembly = base_assembly(c_pins, trace_binding="trace",
                                   receipt_binding=None)
        c_assembly["phases"]["boundaries"] = boundaries
        code, row = run_tool(["build", "--assembly",
                              str(write_json(cdir / "assembly.json", c_assembly)),
                              "--out", str(cdir / "package.json")],
                             expected_refusal=expected,
                             probe_name="C_" + name,
                             ledger_dir=str(cdir))
        if detail_class is not None:
            observed_class = ((row or {}).get("detail") or {}).get("class")
            probes[-1]["expected_detail_class"] = detail_class
            probes[-1]["observed_detail_class"] = observed_class
            if observed_class != detail_class:
                fail("probe C_%s: expected detail class %s, got %s"
                     % (name, detail_class, observed_class))

    def mutate_wrong_script(t):
        t["decisions"][7]["wrong_script"] = True

    def first_zero_saturation(t):
        for index, decision in enumerate(t["decisions"]):
            if all(float(s) == 0.0 for s in (decision.get("saturation") or [0.0])):
                return index
        raise SystemExit("no zero-saturation decision found for the probe")

    def mutate_applied_rewrite(t):
        index = first_zero_saturation(t)
        t["decisions"][index]["applied"] = \
            [9.9] * len(t["decisions"][index]["applied"])

    def mutate_teleport_row(t):
        t["per_tick"][5000]["intervention_reason"] = "teleport"

    def mutate_event_outside(t):
        t["decisions"][3]["issued_tick"] = 99999999

    def mutate_delete_row(t):
        del t["per_tick"][7000]

    def mutate_duplicate_tick(t):
        t["per_tick"][9001]["tick"] = t["per_tick"][9000]["tick"]

    def mutate_drop_decisions(t):
        t["decisions"] = []

    c_probe("wrong_script_event", mutate_wrong_script,
            "input_assertion_violation", detail_class="wrong_script")
    c_probe("applied_rewrite_zero_saturation", mutate_applied_rewrite,
            "input_assertion_violation", detail_class="teleport")
    c_probe("teleport_intervention_row", mutate_teleport_row,
            "input_assertion_violation", detail_class="teleport")
    c_probe("event_outside_domain", mutate_event_outside,
            "input_event_outside_domain")
    c_probe("deleted_row_reset_gap", mutate_delete_row,
            "records_tick_domain_not_contiguous")
    c_probe("duplicated_tick_counter_restart", mutate_duplicate_tick,
            "records_duplicate_tick")
    c_probe("decisions_removed", mutate_drop_decisions,
            "input_log_not_expressible")

    falsified = [p for p in probes if p.get("result") == "FALSIFIED"]
    detail_bad = [p for p in probes
                  if p.get("expected_detail_class") is not None
                  and p.get("observed_detail_class") != p["expected_detail_class"]]
    if falsified or detail_bad:
        fail("falsified probes: %s detail-mismatched: %s"
             % ([p["probe"] for p in falsified],
                [p["probe"] for p in detail_bad]))
    finish()


def finish():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "falsifier_probes.json").write_bytes(
        build_package.canon({"schema": "chimera.evidence_package.probes.v1",
                             "battery": "VALIDATION-ONLY (format proof)",
                             "probes": probes,
                             "problems": problems}) + b"\n")
    write_report()
    if problems:
        print("BATTERY FAILED: %d problem(s)" % len(problems))
        for p in problems:
            print("  - %s" % p)
        sys.exit(1)
    print("BATTERY PASSED: %d probes refused as expected; positive build/"
          "verify/inspect green" % len(probes))
    sys.exit(0)


def write_report():
    ok = not problems
    lines = [
        "# VALIDATION-ONLY evidence-package report (format proof; NOT the final demonstration)",
        "",
        "- Builder: chimera.evidence_package.v1 / %s" % build_package.TOOL_VERSION,
        "- Validated over: the SEALED MAT2-W08 commanded-walk store card",
        "  (E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W08); replay of",
        "  existing sealed bytes only. NO new physics, NO engine run, NO capture.",
        "",
        "## Positive path",
        "",
        "- P0 store pins: 10 of 10 W08 artifacts + the store MANIFEST row for each,",
        "  hash-asserted fresh (input_pin_drift law); 4 authoring identity pins",
        "  (trace, mkv, prereg, capture receipt) cross-checked.",
        "- P1 build: package_class=VALIDATION_ONLY; 10500 contiguous ticks [0,10499];",
        "  60 frames tick-resolved (sheet_layout.frame_files, sorted key=int);",
        "  403 input events; 11 frozen bindings (lineage_report bound, not cited); video<->trace identity bound via",
        "  capture_validation_receipt (trace_sha256/video_sha256 match the bytes);",
        "  energy record class DECLARED-ABSENT with reason (the FINAL package",
        "  requires it present).",
        "- P2 verify: every frozen binding re-hashed; sync law + input assertions",
        "  re-proven over the frozen bytes; result VERIFIED.",
        "- P3 inspect: content address re-checked, INTACT.",
        "",
        "## Falsifier probes (each refused with its exact named code)",
        "",
    ]
    for probe in probes:
        lines.append("- %s -> %s (%s)" % (probe.get("probe"),
                                          probe.get("observed_refusal"),
                                          probe.get("result")))
    lines += [
        "",
        "## Result",
        "",
        ("- FORMAT FALSIFIERS ALL FIRED CORRECTLY: the builder refuses desync, "
         "post-freeze modification and prohibited-input injections. The package "
         "format is proven on the sealed W08 replay."
         if ok else
         "- BATTERY FAILED (see falsifier_probes.json problems[]); the format "
         "claim does NOT hold as stated."),
        "",
        "## Honest gaps (named, never silent)",
        "",
        "- energy record class: declared-absent for W08 (harness recorded none);",
        "  the FINAL demonstration package requires the per-tick energy ledger.",
        "- body/mass ownership: EXTERNAL_REFERENCE_PENDING + "
        "EMISSION_RECEIPT_PENDING (LV-1, lineage-verify/REPORT.md",
        "  b7801ce0... — the owning lane's CURRENT authority, bound as the",
        "  lineage_report frozen binding; the FINAL package requires the",
        "  build-emitted per-body mass table",
        "  — owner + mass + source-artifact sha per part — hashed into the",
        "  freeze manifest; sealed scene bytes alone are not sufficient).",
        "- scene byte-pin: the commanded run's scene identity is referenced via the",
        "  assembly-identity lineage record; the FINAL package requires the",
        "  byte-level scene pin.",
        "- W08 per-frame stills are MEDIA_EMBEDDED_PINNED (tick-keyed sheet); the",
        "  FINAL package requires stills or an extractable media inventory.",
        "- dt_s: not pinned by this validation; the FINAL package requires it.",
        "",
        "This report is an artifact of the wk-evidence-package lane; it claims no",
        "physics qualification, no acceptance authority and no merge authority.",
    ]
    (OUT / "VALIDATION_ONLY_REPORT.md").write_text("\n".join(lines) + "\n",
                                                   encoding="utf-8")


if __name__ == "__main__":
    main()
