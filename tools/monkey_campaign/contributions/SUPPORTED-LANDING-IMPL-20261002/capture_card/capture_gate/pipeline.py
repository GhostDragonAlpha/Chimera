"""The card capture pipeline: prereg -> capture -> GATE -> receipts.

Schemas:
- gate receipt:     chimera.capture_gate.gate_receipt.v1
- pipeline receipt: chimera.capture_gate.pipeline_receipt.v1

Integration law (the reason this module exists): the object-ID / co-location
gate is PART OF the normal capture pipeline, not an optional add-on. The only
code path that can emit a pipeline receipt is run_pipeline, and it must run
the two-stage gate over every captured frame:

1. PREREG STAGE: load + verify the card prereg binding (prereg.py) BEFORE
   capture. Any mismatch refuses the run before a frame is rendered.
2. CAPTURE STAGE: capture every planned frame as a (beauty, mask) sidecar
   pair (sidecar.py), write capture_manifest.json, keep its sha256.
3. GATE STAGE (mandatory): stage-0 palette blank-check + stage-1 mask
   co-location for EVERY frame (mask_gate). assemble_pipeline_receipt
   REFUSES (GateNotRun) if it is not handed a gate receipt, so a pipeline
   pass without the gate running is structurally impossible.
4. RECEIPT STAGE: write gate_receipt.json then pipeline_receipt.json as
   canonical bytes carrying a hash chain
   prereg_file -> view_spec -> capture_manifest -> gate_receipt -> pipeline.
5. REVIEW STAGE: exception frames (declared occlusions) are exported as
   deterministic crops + review manifest for an independent visual pass.

Exit code semantics for the card's run_all: 0 iff every selected case's
pipeline verdict is GREEN; 1 on a RED (rejected) pipeline; 2 on a refused
run (prereg or capture contract). verify_pipeline_receipt re-checks the
chain from disk; the defect suite uses it so acceptance binds to receipts
from the actual flow, not isolated harness calls.

No wall-clock fields anywhere; receipts are byte-deterministic.
"""

import hashlib
import json
import os

from . import mask_gate, palette_stage, prereg as prereg_mod, review_export, sidecar, view_spec

GATE_SCHEMA = "chimera.capture_gate.gate_receipt.v1"
PIPELINE_SCHEMA = "chimera.capture_gate.pipeline_receipt.v1"

GATE_RECEIPT_FILENAME = "gate_receipt.json"
PIPELINE_RECEIPT_FILENAME = "pipeline_receipt.json"
REVIEW_DIRNAME = "review"

PIPELINE_LAW = (
    "The object-ID/co-location gate is part of the normal pipeline: capture "
    "runs are refused before rendering unless the card prereg pins the exact "
    "view-spec hash, and a pipeline receipt can only be assembled from an "
    "actual two-stage gate receipt (stage-0 palette blank-check + stage-1 "
    "mask co-location). Stage-0 totals are smoke census only; stage-1 owns "
    "acceptance. Exceptions pass only via preregistered declared occlusions "
    "with machine census rows and are exported for independent visual review.")


class PipelineRefused(RuntimeError):
    """The pipeline refused to run or to pass."""


class GateNotRun(PipelineRefused):
    """Raised when a pipeline receipt is requested without a gate receipt."""


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def write_canonical(path, obj):
    data = canonical_bytes(obj)
    with open(path, "wb") as handle:
        handle.write(data)
    return hashlib.sha256(data).hexdigest()


def gate_frames(spec, frames, capture_manifest_sha256, prereg_binding):
    """Two-stage gate over captured sidecar frames (the mandatory stage)."""
    frame_rows = []
    exception_rows = []
    for frame in frames:
        stage0 = palette_stage.evaluate_frame_palette(frame.beauty)
        stage1 = mask_gate.evaluate_frame(spec, frame.view_class,
                                          frame.beauty, frame.mask, frame.frame_id)
        verdict = (palette_stage.VERDICT_GREEN if
                   stage0["verdict"] == palette_stage.VERDICT_GREEN
                   and stage1["verdict"] == mask_gate.VERDICT_GREEN
                   else mask_gate.VERDICT_RED)
        frame_rows.append({
            "frame_id": frame.frame_id,
            "view_class": frame.view_class,
            "defect": frame.defect_label,
            "stage0": stage0,
            "stage1": stage1,
            "verdict": verdict,
        })
        exception_rows.extend(stage1["exceptions"])
    green = sum(1 for row in frame_rows if row["verdict"] == mask_gate.VERDICT_GREEN)
    return {
        "schema": GATE_SCHEMA,
        "pipeline_law": PIPELINE_LAW,
        "view_spec_schema": view_spec.SCHEMA,
        "spec_id": spec["spec_id"],
        "spec_version": spec["spec_version"],
        "prereg_sha256": view_spec.spec_prereg_sha256(spec),
        "card_prereg_file_sha256": prereg_binding["prereg_file_sha256"],
        "capture_manifest_sha256": capture_manifest_sha256,
        "frames": frame_rows,
        "frames_total": len(frame_rows),
        "frames_green": green,
        "frames_red": len(frame_rows) - green,
        "exception_rows": exception_rows,
        "verdict": mask_gate.VERDICT_GREEN
        if green == len(frame_rows) and frame_rows else mask_gate.VERDICT_RED,
    }


def assemble_pipeline_receipt(case_id, card_id, spec, prereg_binding,
                              capture_manifest_sha256, gate_receipt,
                              gate_file_sha256, review):
    """Build the pipeline receipt from an ACTUAL gate receipt.

    ``gate_file_sha256`` is the sha256 of the on-disk gate_receipt.json bytes
    just written by this run; verify_pipeline_receipt re-hashes the file and
    compares. Raises GateNotRun when gate_receipt is None: the normal
    pipeline cannot pass without the gate running.
    """
    if gate_receipt is None:
        raise GateNotRun("gate_not_run_pipeline_cannot_pass")
    if gate_receipt.get("schema") != GATE_SCHEMA:
        raise PipelineRefused("gate_receipt_schema_unrecognized")
    return {
        "schema": PIPELINE_SCHEMA,
        "pipeline_law": PIPELINE_LAW,
        "card_id": card_id,
        "case_id": case_id,
        "gate_ran": True,
        "gate": {
            "schema": gate_receipt["schema"],
            "verdict": gate_receipt["verdict"],
            "frames_total": gate_receipt["frames_total"],
            "frames_green": gate_receipt["frames_green"],
            "frames_red": gate_receipt["frames_red"],
            "receipt_sha256": gate_file_sha256,
        },
        "view_spec": {
            "spec_id": spec["spec_id"],
            "spec_version": spec["spec_version"],
            "prereg_sha256": view_spec.spec_prereg_sha256(spec),
            "prereg_pin_sha256": prereg_binding["prereg_sha256"],
            "prereg_file": prereg_binding["prereg_file"],
            "prereg_file_sha256": prereg_binding["prereg_file_sha256"],
        },
        "capture_manifest_sha256": capture_manifest_sha256,
        "review_export": review,
        "verdict": gate_receipt["verdict"],
    }


def verify_pipeline_receipt(out_dir):
    """Independently re-check one case's receipt chain from disk.

    Returns a list of machine problem codes; empty means the chain verifies:
    the on-disk gate receipt and capture manifest hash to the values the
    pipeline receipt pins, the gate verdict matches, and the gate ran.
    """
    problems = []
    pipeline_path = os.path.join(out_dir, PIPELINE_RECEIPT_FILENAME)
    gate_path = os.path.join(out_dir, GATE_RECEIPT_FILENAME)
    capture_path = os.path.join(out_dir, sidecar.CAPTURE_MANIFEST_FILENAME)
    for path, code in ((pipeline_path, "pipeline_receipt_missing"),
                       (gate_path, "gate_receipt_missing"),
                       (capture_path, "capture_manifest_missing")):
        if not os.path.isfile(path):
            problems.append(code)
    if problems:
        return problems
    with open(pipeline_path, "rb") as handle:
        receipt = json.loads(handle.read().decode("utf-8"))
    if receipt.get("schema") != PIPELINE_SCHEMA:
        problems.append("pipeline_receipt_schema_unrecognized")
    if receipt.get("gate_ran") is not True:
        problems.append("gate_ran_not_true")
    gate_file_sha = sha256_file(gate_path)
    if receipt.get("gate", {}).get("receipt_sha256") != gate_file_sha:
        problems.append("gate_receipt_sha256_mismatch")
    capture_file_sha = sha256_file(capture_path)
    if receipt.get("capture_manifest_sha256") != capture_file_sha:
        problems.append("capture_manifest_sha256_mismatch")
    with open(gate_path, "rb") as handle:
        gate_receipt = json.loads(handle.read().decode("utf-8"))
    if gate_receipt.get("schema") != GATE_SCHEMA:
        problems.append("gate_receipt_schema_unrecognized")
    if gate_receipt.get("verdict") != receipt.get("verdict"):
        problems.append("verdict_disagrees_with_gate_receipt")
    if gate_receipt.get("capture_manifest_sha256") != capture_file_sha:
        problems.append("gate_capture_binding_mismatch")
    return problems


def run_pipeline(card_root, out_dir, card_id, case_id, render_fn, frames_plan):
    """Run the full normal pipeline for one case; return (receipt, exit_code).

    Writes gate_receipt.json, capture_manifest.json, pipeline_receipt.json
    and (when exceptions fired) review/ artifacts under out_dir. Exit codes:
    0 GREEN, 1 RED (rejected), 2 refused (prereg/capture contract).
    """
    os.makedirs(out_dir, exist_ok=True)
    # 1. Prereg stage: refuse BEFORE any frame is rendered.
    try:
        prereg, spec, binding = prereg_mod.check_prereg_stage(card_root)
    except prereg_mod.PreregRefused as refused:
        return {"schema": PIPELINE_SCHEMA, "card_id": card_id, "case_id": case_id,
                "verdict": "REFUSED", "refusal": str(refused),
                "pipeline_law": PIPELINE_LAW}, 2
    # 2. Capture stage: sidecar pairs + channel-isolation audit.
    frames = []
    try:
        for entry in frames_plan:
            frames.append(sidecar.capture_frame(
                spec, entry["view_class"], render_fn,
                frame_id=entry["frame_id"], defect=entry.get("defect")))
    except sidecar.CaptureRefused as refused:
        return {"schema": PIPELINE_SCHEMA, "card_id": card_id, "case_id": case_id,
                "verdict": "REFUSED", "refusal": str(refused),
                "pipeline_law": PIPELINE_LAW}, 2
    _, capture_manifest_sha256 = sidecar.write_capture_manifest(
        out_dir, sidecar.build_capture_manifest(spec, binding, frames))
    # 3. GATE STAGE (mandatory) + 4. receipts with hash chain.
    gate_receipt = gate_frames(spec, frames, capture_manifest_sha256, binding)
    gate_file_sha256 = write_canonical(
        os.path.join(out_dir, GATE_RECEIPT_FILENAME), gate_receipt)
    review = None
    review_dir = os.path.join(out_dir, REVIEW_DIRNAME)
    frames_by_id = {frame.frame_id: frame for frame in frames}
    manifest = review_export.export_exception_crops(
        [row["stage1"] for row in gate_receipt["frames"]], frames_by_id, review_dir)
    if manifest["exception_count"]:
        review = {"exception_count": manifest["exception_count"],
                  "manifest_sha256": manifest["manifest_sha256"]}
    receipt = assemble_pipeline_receipt(case_id, card_id, spec, binding,
                                        capture_manifest_sha256, gate_receipt,
                                        gate_file_sha256, review)
    write_canonical(os.path.join(out_dir, PIPELINE_RECEIPT_FILENAME), receipt)
    exit_code = 0 if receipt["verdict"] == mask_gate.VERDICT_GREEN else 1
    return receipt, exit_code
