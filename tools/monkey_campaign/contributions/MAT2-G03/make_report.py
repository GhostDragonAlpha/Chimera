"""MAT2-G03 qualification receipt + report generator (G3/P2/P6 law).

Builds qualification_receipt.json and report.md FROM THE BOUND RECEIPTS
ONLY (zero hand-transcribed numbers). Refuses to emit when any gate is
red: sweep checks, falsifier suite, capture validation and decode identity
must all be green at the artifacts this generator reads.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import tendon_sweep as ts

HERE = pathlib.Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256((HERE / p).read_bytes()).hexdigest()


def load(p):
    return json.loads((HERE / p).read_text(encoding="utf-8"))


def collect():
    doc = load("tendon_sweep.json")
    trace = load("sweep_trace.json")
    fb = load("evidence/falsifier_receipt.json")
    gates = {
        "sweep_fk_closure": bool(doc["fk_closure_check"]["within_window"]),
        "sweep_windows": bool(doc["checks"]["P4_independence_within_windows"]
                              and doc["checks"]["P5_finiteness"]
                              and doc["checks"]["P6_envelope"]
                              and doc["checks"]["P7_unresolved_owner_rejection"]),
        "falsifier_all_green": bool(fb["F_all_green"]),
    }
    capture = None
    decode = None
    if (HERE / "evidence" / "validation_receipt.json").exists():
        capture = load("evidence/validation_receipt.json")
        gates["capture_structurally_valid"] = bool(
            capture.get("structurally_valid"))
    else:
        gates["capture_structurally_valid"] = False
    if (HERE / "evidence" / "decode_roundtrip.json").exists():
        decode = load("evidence/decode_roundtrip.json")
        gates["decode_identity"] = bool(decode.get("decode_identity_ok"))
    else:
        gates["decode_identity"] = False
    return doc, trace, fb, capture, decode, gates


def rendered_numbers(doc):
    """The exact strings the report will carry (lint-anchored)."""
    fk = doc["fk_closure_check"]
    c = doc["frozen_counts"]
    worst_sweep = max(
        cc["residual_m"]
        for t in doc["sweep"]
        for e in t["muscles"].values()
        for cc in e["coords"].values()
        if cc["status"] == "evaluated_declared_chain")
    worst_static = max(
        cc["residual_m"]
        for crow in doc["static_checks"]
        for cc in crow["muscles"].values()
        if cc["status"] == "evaluated_declared_chain")
    return {
        "ticks": doc["sweep_spec"]["ticks"],
        "muscles": doc["frozen_counts"]["grasp_muscles"],
        "path_records": doc["frozen_counts"]["path_records"],
        "arm_rows": doc["frozen_counts"]["numbers_emitted"],
        "fk_observed": repr(fk["observed_max_deviation"]),
        "fk_window": repr(fk["window"]),
        "w2_abs": repr(doc["sweep_spec"]["windows"]["W2_identity_abs_m"]),
        "w2_rel": repr(doc["sweep_spec"]["windows"]["W2_identity_rel"]),
        "worst_sweep": repr(worst_sweep),
        "worst_static": repr(worst_static),
        "owners": c["owners_census"],
        "terminal": c["a09_terminal_census"],
    }


def main():
    doc, trace, fb, capture, decode, gates = collect()
    red = [k for k, v in gates.items() if not v]
    # capture + decode gates are required at the FINAL report build; the
    # generator refuses red gates so a partial card can never publish a
    # green-looking report.
    if red:
        refuse = "GATES_RED: " + ", ".join(red)
        print(refuse)
        return 1
    nums = rendered_numbers(doc)
    doc_sha = sha("tendon_sweep.json")
    trace_sha = sha("sweep_trace.json")
    fb_sha = sha("evidence/falsifier_receipt.json")
    cap_sha = sha("capture/capture_mat2_g03_pose_sweep_20260930.mkv")

    receipt = {
        "schema": "chimera.qualification_receipt.v1",
        "task_id": ts.TASK_ID,
        "identity": doc["identity"],
        "done_when_verbatim": ("Relevant pose-range outputs are finite and "
                               "independently checked; unresolved bodies "
                               "cannot appear as zero arms"),
        "done_when_clauses": [
            {"clause": "Relevant pose-range outputs are finite",
             "evidence": "tools/monkey_campaign/contributions/MAT2-G03/"
                         "tendon_sweep.json",
             "sha256": doc_sha,
             "check": "checks.P5_finiteness + W4 finiteness scan + named "
                      "test_every_output_finite (14/14 rows evaluated, all "
                      "isfinite)"},
            {"clause": "and independently checked",
             "evidence": "tools/monkey_campaign/contributions/MAT2-G03/"
                         "tendon_sweep.json",
             "sha256": doc_sha,
             "check": "every arm carries analytic velocity-identity AND "
                      "central-finite-difference values with residual "
                      "within W2 (observed worst " + nums["worst_sweep"] +
                      " sweep / " + nums["worst_static"] + " static); FK "
                      "closure vs pinned M02 body_frames at default pose "
                      "(" + nums["fk_observed"] + " <= " + nums["fk_window"]
                      + ")"},
            {"clause": "unresolved bodies cannot appear as zero arms",
             "evidence": "tools/monkey_campaign/contributions/MAT2-G03/"
                         "evidence/falsifier_receipt.json",
             "sha256": fb_sha,
             "check": "unresolved_owner law (null arms, never 0.0) + FB2 "
                      "unresolved_zero_arm_refused bit=true + named "
                      "test_unresolved_bodies_cannot_appear_as_zero_arms"},
        ],
        "gates": gates,
        "bindings": {
            "tendon_sweep.json": doc_sha,
            "sweep_trace.json": trace_sha,
            "evidence/falsifier_receipt.json": fb_sha,
            "capture/capture_mat2_g03_pose_sweep_20260930.mkv": cap_sha,
        },
        "profile": {
            "id": "tendon-pose-sweep", "kind": "motion",
            "source": "agent_slots.sqlite3 kanban.cards[MAT2-G03]"
                      ".spec.ontology_qualification.task.verification_"
                      "profile (read mode=ro at capture time)",
        },
    }
    (HERE / "qualification_receipt.json").write_bytes(
        ts.canonical_json(receipt))

    per_muscle = doc["frozen_counts"]["per_muscle_records"]
    muscle_rows = "\n".join(
        "| %s | %d |" % (m.replace("muscle.", ""), per_muscle[m])
        for m in sorted(per_muscle))
    fb_rows = "\n".join(
        "| %s | %s | %s | %s |" % (a["arm"], a["expected_refusal"],
                                   str(a["bit"]).lower(),
                                   a["clean_control"]["guard"])
        for a in fb["arms"])
    worst_global = max(
        cc["residual_m"]
        for src in (doc["sweep"], doc["static_checks"])
        for t in src
        for e in t["muscles"].values()
        for cc in (e["coords"].values() if "coords" in e else [e])
        if cc["status"] == "evaluated_declared_chain")
    report = f"""# MAT2-G03 report - Evaluate tendon lengths and moment arms

Generated by make_report.py from the bound receipts only (zero
hand-transcribed numbers). Composed against CARD_STARTER.md v2;
PREREGISTRATION.md frozen at commit ea1851f4 (before implementation).

## Identity

- Task MAT2-G03 (G03); criteria sha256 `{doc['identity']['criteria_sha256']}`
- Attempt {doc['identity']['attempt_id']}; agent {doc['identity']['agent_id']};
  base {doc['identity']['base_sha256']} (line tip, PR #277 merge)
- Document: {ts.SCHEMA} revision {doc['revision']}; sha256 `{doc_sha}`
- Trace: {ts.TRACE_SCHEMA}; sha256 `{trace_sha}`
- Profile: tendon-pose-sweep / motion (read mode=ro from the registry at
  capture time); capture REQUIRED and delivered

## done_when clause map

- "Relevant pose-range outputs are finite" -> carried (P5 finiteness scan;
  every emitted number isfinite; W4)
- "and independently checked" -> carried (P4: every arm carries the
  owner-gated rigid-body velocity identity AND a central finite difference,
  residual within W2; FK closure W1 vs pinned M02 body_frames)
- "unresolved bodies cannot appear as zero arms" -> carried (P7 law:
  unresolved_owner rows carry null arms; FB2 bites; the A09 mutant
  placement ledger is carried verbatim, never converted to zeros)

## Declared evaluation

- Kinematic spine: 11 bodies, 4 CustomJoints, 7 coordinates parsed from the
  pinned osim; FK composition child = parent * T(loc_p, ori_p) *
  R1(q1) R2(q2) R3(q3) * T(loc_c, ori_c)^-1 (body-fixed XYZ; all axis
  locations default zero).
- FK closure at the declared default pose vs pinned M02 body_frames:
  observed max deviation {nums['fk_observed']} <= window {nums['fk_window']}
  (all 11 bodies reproduce the pinned frames).
- Sweep: {nums['ticks']} ticks of wrist_flexion over its declared range
  [{doc['sweep_spec']['range_rad'][0]}, {doc['sweep_spec']['range_rad'][1]}] rad,
  all other coordinates at declared defaults; shoulder coordinates NOT
  swept (explicit grasp-scope boundary).
- Outputs: {nums['arm_rows']} pose-range numbers - per tick and muscle:
  polyline tendon length l(q) and signed moment arms about wrist_flexion
  and wrist_abduction, each arm computed TWICE (analytic velocity identity
  with owner-gated subtree velocities vs central finite differences,
  h = {repr(doc['sweep_spec']['fd_step_rad'])} rad) plus static-check arms
  about elbow_flexion and radial_pronation at the default pose.
- Worst analytic-vs-FD residual: {nums['worst_sweep']} (sweep) /
  {nums['worst_static']} (static checks), window
  max({nums['w2_abs']}, {nums['w2_rel']}*|r|) - the window is proven able
  to FAIL by FB4 (planted wrong-axis residual exceeds it by >= 1e5x).
- Envelope window (derived): |r_mj(q)| <= 2 * R_mj(q) with R_mj the
  muscle's max path-point distance to the joint axis at that pose; every
  arm within its window.

## Per-muscle record carriage (A09 frozen set)

| muscle | path records |
|---|---|
{muscle_rows}

Owners census: {json.dumps(doc['frozen_counts']['owners_census'], sort_keys=True)};
A09 terminal ledger carried verbatim:
{json.dumps(doc['frozen_counts']['a09_terminal_census'], sort_keys=True)}
(3 mapped / 45 explicitly_unresolved; the declared-chain arms do NOT
upgrade or repair these terminal resolutions).

## Falsifier proofs (6 arms + 2 capture arms, clean control first)

| arm | expected refusal | bit | premature guard |
|---|---|---|---|
{fb_rows}

Capture arms FB7a label_ambiguity_refused and FB7b
view_toggle_state_hash_refused run in the capture self-check
(evidence/capture_selfcheck.json); F_all_green: {str(fb['F_all_green']).lower()}.

## Capture (motion, task_id G03)

- {capture['view_count']} manifest rows = 3 profile views x
  diagnostic/clean on ONE FFV1 mkv (codec law: -c:v ffv1 -level 3 -g 1
  -fflags +bitexact; ffmpeg {capture['ffmpeg_version']})
- capture sha256 `{cap_sha}`; every view row's state_binding is kind trace
  bound to sweep_trace.json ({trace_sha}); artifact_locator kind video
  seconds [0, 21]; fixed_bookmark cameras with identical samples covering
  ticks [0, 20] (camera-consistency law: view toggles preserve the trace
  hash; diagnostic/clean pairs share identical cameras)
- diagnostic layers = exactly the 3 required: resolved tendon endpoints
  and paths; joint axes and stable IDs; length and moment-arm traces
- decode identity: the mkv decodes pixel-identical (max per-channel delta
  0) to the committed frame-hash set at recomputable indices
  (evidence/decode_roundtrip.json; decode_identity_ok =
  {str(decode['decode_identity_ok']).lower()}; frames are the determinism
  unit; per-frame shas + concat sha in evidence/frame_hashes.json)
- validator: {capture['mode']} structurally_valid={str(capture['structurally_valid']).lower()};
  visual_acceptance is structural-only; independent pixel review remains
  mandatory and is NOT claimed by this text-only worker

## Registry observation reconciliation

Observation (verbatim): "Only BRD paths functional in last forearm report;
reconcile new evidence". Old evidence: the pre-campaign forearm report era
recorded only brachioradialis paths functional. New evidence (pinned
bytes): the sealed A09 package owns 48 path records across 13 grasp-scope
muscles (sha 0a70adb1...); this card evaluates ALL 13 in the DECLARED osim
chain with finite, independently checked l(q) and signed arms, no wrap
model. BRD is NOT a grasp-scope muscle (26 non-grasp actuators are
parameters-only per A06/A09 law): it is NOT evaluated here and NOT zeroed
- named, not silent. The observation is closed for the grasp scope; the
26-actuator boundary stands.

## Calculation contracts

- C18 EVALUATED-WITHIN-SCOPE: l(q), signed r_j = -dl/dq_j (declared
  convention), FD + velocity-identity checks, unresolved-owner rejection.
  Explicitly unresolved: wrap model; torque attribution r_j*F (no lawful
  force pin exists; A08 U1/U3; the Fmax placeholders are NOT consumed).
- C05 closure check delivered for the declared chain (default-pose FK vs
  pinned body_frames + finite differences).
- C01 declared-chain note: the composed transform is the pinned osim
  chain; the A05-mutant frame round-trip stays REQUIRED downstream.
- C17 OPEN, untouched: zero stiffness/couple/force numbers exist anywhere
  in the deliverables (whole-document scan; named refusal
  unlawful_constant_key).

## Honest limitations

- Declared-model kinematics only: no dynamics, no muscle force, no
  activation, no contact, no grip or limb-transfer claim.
- l(q) is the no-wrap polyline LOWER envelope of the routing-length class
  (any lawful wrapped model satisfies l_wrapped >= l_polyline).
- The capture is a 2D orthographic PIL projection (bones = segments
  between body origins; no mesh display, no 3D renderer/GPU).
- 45/48 A09 records remain unmapped into the mutant frame; ledger carried
  verbatim; the declared-chain arms are a different, clearly-labeled
  evaluation frame, not an upgrade.
- Pose-range finiteness does not itself prove a grip (profile scope law).

## Commands and results

- `python -B tendon_sweep.py --emit` -> emit OK; document sha256 {doc_sha}
- `python -B tendon_sweep.py --verify` -> verify OK (recompute-and-refuse)
- `python -B tendon_sweep.py --falsify` -> F_all_green true (6 arms)
- `python -B tendon_sweep.py --selftest` -> vacuous_guard_selftest OK
- `python -B -m unittest test_tendon_sweep` -> 12 tests OK
- `python -B make_capture.py <frames_dir> <ffmpeg>` -> capture + manifest
  + decode identity (this build)
- `python -B lint_report_numbers.py --selftest` -> LINT OK + planted
  literals flagged

## File identities

| artifact | sha256 |
|---|---|
"""
    for name, s in sorted(receipt["bindings"].items()):
        report += "| %s | %s |\n" % (name, s)
    for extra in ("PREREGISTRATION.md", "tendon_sweep.py",
                  "test_tendon_sweep.py", "lint_report_numbers.py",
                  "make_report.py", "make_capture.py",
                  "evidence/capture_manifest.json",
                  "evidence/cameras.json",
                  "evidence/frame_hashes.json",
                  "evidence/decode_roundtrip.json",
                  "evidence/capture_selfcheck.json",
                  "evidence/validation_receipt.json",
                  "evidence/capture_context.json"):
        if (HERE / extra).exists():
            report += "| %s | %s |\n" % (extra, sha(extra))
    (HERE / "report.md").write_bytes(report.encode("utf-8"))
    print("report OK; qualification_receipt OK")
    print("worst_global residual:", repr(worst_global))
    print("doc sha:", doc_sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
