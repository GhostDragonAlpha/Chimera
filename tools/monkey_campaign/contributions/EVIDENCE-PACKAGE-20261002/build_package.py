"""build_package.py — the chimera.evidence_package.v1 builder/verifier.

Lane evidence-package (wk-evidence-package, 2026-10-02). Format contract:
PACKAGE_SPEC.md next to this file. Serves the GOAL's final-deliverable law:
one evidence package binds the build and inputs to continuous video, player
inputs, and time-aligned state, contact, force, and energy records; the build,
scene, body/mass ownership, control interface, parameters and pass criteria
are FROZEN (hashed) before the final run; an independent reviewer verifies the
physical claims and confirms visible behavior matches the trace.

Design conventions cited from acceptance-chain/acceptance_packet.py (never
imported; that lane owns its bytes): canonical-JSON content addressing, named
refusals with a refusals.jsonl ledger, fresh re-hash of every bound artifact,
and an immutable package after build.

Subcommands:
  build   --assembly ASSEMBLY_JSON --out PACKAGE_JSON
          Assembles the package from an assembly spec (the caller-authored
          description of the run's artifacts, classes, phases, assertions).
          Refuses on ANY missing binding; no package is written on refusal.
  verify  --package PACKAGE_JSON [--expect-class CLASS]
          Re-hashes every frozen binding (post-freeze changes refuse),
          re-proves the sync law and the input assertions, and emits a
          verification receipt next to the package.
  inspect --package PACKAGE_JSON
          Prints the human summary.

Exit codes: 0 success, 2 named refusal, 3 usage error.
Every refusal is a named reason, emitted as JSON on stderr and appended to
refusals.jsonl next to the output/package. THE SYNC LAW: any desync or
unbound row is a package FAILURE -- the build refuses loudly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "chimera.evidence_package.v1"
TOOL_VERSION = "evidence-package-v1"
EXIT_REFUSED = 2
EXIT_USAGE = 3

# Prohibited intervention/event classes (the no-teleport / no-hidden-anchor /
# no-reset law; PACKAGE_SPEC.md section (c)).
PROHIBITED_INTERVENTIONS = {
    "teleport": "teleport",
    "position_snap": "teleport",
    "animation_only": "teleport",
    "anchor": "hidden_anchor",
    "hidden_anchor": "hidden_anchor",
    "weld": "hidden_anchor",
    "sticky_weld": "hidden_anchor",
    "reset": "reset",
    "restart": "reset",
    "respawn": "reset",
}

# Command-name tokens that carry a prohibited class in an input EVENT
# (the no_hidden_anchor / no_reset log halves; matched on word-boundary
# tokens of the command name, so e.g. 'start_ceiling_hold' is clean but
# 'weld_release' or 'reset_pose' refuse).
PROHIBITED_COMMAND_TOKENS = {
    "anchor": "hidden_anchor",
    "weld": "hidden_anchor",
    "teleport": "teleport",
    "snap": "teleport",
    "animation": "teleport",
    "reset": "reset",
    "respawn": "reset",
    "restart": "reset",
}

FREEZE_SECTIONS = ("build", "scene", "body_mass_ownership", "control_interface",
                   "parameters", "pass_criteria")
RECORD_CLASSES = ("state", "contact", "force", "energy")


# ------------------------------------------------------------- helpers ----

def now_utc():
    return datetime.now(timezone.utc).isoformat()


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            digest.update(chunk)
    return digest.hexdigest(), size


def write_bytes_lf_free(path, data):
    """Byte-exact write; no newline conversion anywhere in this tool."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as stream:
        stream.write(data)


def load_json(path):
    return json.loads(Path(path).read_bytes().decode("utf-8"))


def tick_int(value):
    """The M09 lesson: tick keys may arrive as strings ('0','10','21',...).
    Everything numeric here resolves through int(); never sort tick keys
    lexically."""
    return int(value)


def sorted_ticks(keys):
    return sorted((tick_int(k) for k in keys))


class Refusal(Exception):
    """A named refusal carrying a stable reason token and detail."""

    def __init__(self, reason, detail=None):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail or {}


def require(ok, message, detail=None):
    if not ok:
        raise Refusal(message, detail)


def record_refusal(out_dir, command, refusal, extra=None):
    entry = {"at_utc": now_utc(), "tool": TOOL_VERSION, "command": command,
             "refused": refusal.reason, "detail": refusal.detail}
    if extra:
        entry.update(extra)
    if out_dir is not None:
        path = Path(out_dir) / "refusals.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "ab") as stream:
            stream.write(canon(entry) + b"\n")
    print(json.dumps(entry, sort_keys=True), file=sys.stderr)


# ---------------------------------------------------------- bindings ----

def resolve_bindings(assembly, checks):
    """Fresh-hash every declared binding; enforce expected sha when declared
    (the input-pin-drift law: drift at build is a refusal, never a warning)."""
    bindings = {}
    for name, spec in sorted((assembly.get("bindings") or {}).items()):
        reference = spec.get("reference")
        require(bool(reference), "binding_missing",
                {"binding": name, "why": "no reference declared"})
        path = Path(reference)
        require(path.is_file(), "binding_missing",
                {"binding": name, "reference": str(reference)})
        observed, size = sha256_file(path)
        expected = spec.get("expected_sha256")
        require(expected is None or expected == observed, "binding_hash_mismatch",
                {"binding": name, "reference": str(reference),
                 "expected_sha256": expected, "observed_sha256": observed,
                 "why": "declared pin drift; the frozen input identity moved"})
        bindings[name] = {"reference": str(reference), "sha256": observed,
                          "size_bytes": size}
        if expected is not None:
            checks.append({"check": "binding_pin." + name, "result": "PASS",
                           "detail": {"sha256": observed}})
    return bindings


def bind_json(bindings, name):
    require(name in bindings, "binding_missing",
            {"binding": name, "why": "required JSON artifact not bound"})
    return load_json(bindings[name]["reference"])


# ------------------------------------------------------------ freeze ----

def build_freeze(assembly, bindings, checks):
    freeze = assembly.get("freeze_manifest") or {}
    for section in FREEZE_SECTIONS:
        require(isinstance(freeze.get(section), dict), "freeze_manifest_incomplete",
                {"section": section, "why": "required freeze section absent"})
    own = freeze.get("body_mass_ownership") or {}
    status = own.get("status")
    require(status in ("BOUND", "EXTERNAL_REFERENCE_PENDING"),
            "freeze_manifest_incomplete",
            {"section": "body_mass_ownership",
             "why": "status must be BOUND or EXTERNAL_REFERENCE_PENDING",
             "found": status})
    require(bool(own.get("reference")), "freeze_manifest_incomplete",
            {"section": "body_mass_ownership",
             "why": "lineage table reference required (the lineage-verify lane's "
                    "table feeds this; reference, never duplicate)"})
    # The citation-rehash law (SGT review F1, durable lesson): a sha CITED in
    # a freeze section escapes every re-hash gate unless it is BOUND. When the
    # ownership reference names a sha, it must name the binding that carries
    # it; the builder refuses a stale citation and records the OBSERVED sha.
    ref_binding = own.get("reference_binding")
    ref_sha = own.get("reference_sha256")
    if ref_binding is not None or ref_sha is not None:
        require(ref_binding in bindings, "freeze_citation_unbound",
                {"section": "body_mass_ownership",
                 "reference_binding": ref_binding,
                 "why": "a cited lineage sha must be carried by a frozen "
                        "binding so build/verify re-hash it (citation-only "
                        "references escape every re-hash gate by design)"})
        require(ref_sha is None or ref_sha == bindings[ref_binding]["sha256"],
                "freeze_citation_stale",
                {"section": "body_mass_ownership",
                 "declared_sha256": ref_sha,
                 "observed_sha256": bindings[ref_binding]["sha256"],
                 "why": "the cited lineage authority moved; re-check the "
                        "owning lane's CURRENT bytes and rebuild"})
        own["reference_sha256"] = bindings[ref_binding]["sha256"]
    package_class = assembly.get("package_class")
    require(status == "BOUND" or package_class == "VALIDATION_ONLY",
            "freeze_body_ownership_unbound",
            {"why": "the FINAL_DEMONSTRATION package requires a BOUND "
                    "body/mass-ownership digest; EXTERNAL_REFERENCE_PENDING is "
                    "lawful only for VALIDATION_ONLY packages"})
    # LV-1 emission-receipt law (lineage-verify/REPORT.md — the OWNING lane's
    # current authority; the sha is BOUND as the lineage_report binding and
    # re-hashed at build/verify, never trusted as a prose citation):
    # the build must EMIT its per-body mass table at launch; the sealed scene
    # bytes alone are not evidence of what the running build loads.
    emission = own.get("emission_receipt")
    if package_class == "FINAL_DEMONSTRATION":
        require(isinstance(emission, dict) and emission.get("reference")
                and emission.get("sha256"), "freeze_emission_receipt_missing",
                {"why": "FINAL requires the per-body EMISSION RECEIPT the build "
                        "emits at launch (owner + mass value + source-artifact "
                        "sha per part; LV-1, the bound lineage_report "
                        "binding); sealed scene bytes alone are insufficient"})
        bound = bindings.get("emission_receipt")
        require(bound is not None and bound["sha256"] == emission.get("sha256"),
                "freeze_emission_receipt_unbound",
                {"why": "the emission receipt must be a frozen binding so "
                        "verify re-hashes it (emitted_by == the frozen build)"})
    else:
        require(emission is not None
                or own.get("emission_status") == "EMISSION_RECEIPT_PENDING",
                "freeze_emission_receipt_missing",
                {"why": "a VALIDATION package without the emission receipt must "
                        "carry emission_status: EMISSION_RECEIPT_PENDING "
                        "(LV-1 named gap, never silent)"})
    criteria = freeze.get("pass_criteria") or {}
    require(criteria.get("preregistration_sha256") or criteria.get("criteria_sha256"),
            "freeze_manifest_incomplete",
            {"section": "pass_criteria",
             "why": "the frozen prereg/criteria sha is the pass-criteria freeze"})
    interface = freeze.get("control_interface") or {}
    require(interface.get("name") and isinstance(interface.get("command_vector_dim"), int),
            "freeze_manifest_incomplete",
            {"section": "control_interface",
             "why": "interface name + command vector dimension required"})
    checks.append({"check": "freeze_sections_complete", "result": "PASS",
                   "detail": {"sections": list(FREEZE_SECTIONS),
                              "lv1_emission_receipt":
                                  "BOUND" if emission else "EMISSION_RECEIPT_PENDING"}})
    return freeze


# ----------------------------------------------------------- records ----

def find_tick_key(row, declared):
    if declared:
        require(declared in row, "records_tick_key_missing",
                {"tick_key": declared, "row_keys": sorted(row.keys())[:24]})
        return declared
    for candidate in ("tick", "t_tick"):
        if candidate in row:
            return candidate
    raise Refusal("records_tick_key_missing",
                  {"row_keys": sorted(row.keys())[:24],
                   "why": "no tick field found; the join law needs one"})


def build_records(assembly, bindings, checks):
    trace_spec = assembly.get("records") or {}
    trace = bind_json(bindings, trace_spec.get("binding", "trace"))
    schema = trace.get("schema")
    require(bool(schema), "records_schema_missing", {"why": "trace schema absent"})
    rows = trace.get("per_tick")
    if rows is None:
        rows = trace.get("rows")
    require(isinstance(rows, list) and rows, "records_rows_missing",
            {"schema": schema})

    tick_key = find_tick_key(rows[0], trace_spec.get("tick_key"))
    index = {}
    for position, row in enumerate(rows):
        tick = tick_int(row[tick_key])
        require(tick not in index, "records_duplicate_tick",
                {"tick": tick, "row_positions": [index.get(tick), position]})
        index[tick] = row

    domain_declared = trace_spec.get("tick_domain")
    ticks = sorted(index)
    t0, t1 = ticks[0], ticks[-1]
    contiguous = (len(ticks) == (t1 - t0 + 1)) and all(
        b - a == 1 for a, b in zip(ticks, ticks[1:]))
    require(contiguous, "records_tick_domain_not_contiguous",
            {"t0": t0, "t1": t1, "n_rows": len(ticks),
             "why": "a gap/duplicate in the tick sequence is the no-reset "
                    "evidence surface; the run is not one uninterrupted sequence"})
    if domain_declared is not None:
        require([tick_int(v) for v in domain_declared] == [t0, t1],
                "records_tick_domain_mismatch",
                {"declared": domain_declared, "observed": [t0, t1]})

    declared_absent = trace_spec.get("declared_absent") or []
    absent_names = set()
    for item in declared_absent:
        require(isinstance(item, dict) and item.get("class") in RECORD_CLASSES
                and str(item.get("reason", "")).strip(),
                "record_class_absent_unnamed",
                {"item": item,
                 "why": "a declared-absent record class needs a named reason"})
        absent_names.add(item["class"])
    present = {}
    for klass in RECORD_CLASSES:
        if klass in absent_names:
            continue
        fields = (trace_spec.get("classes") or {}).get(klass)
        require(isinstance(fields, list) and fields, "record_class_absent_unnamed",
                {"class": klass,
                 "why": "class neither bound with fields nor declared_absent "
                        "with a reason"})
        missing = [f for f in fields if f not in rows[0]]
        require(not missing, "record_class_fields_missing",
                {"class": klass, "missing": missing})
        present[klass] = fields
    checks.append({"check": "records_tick_domain_contiguous", "result": "PASS",
                   "detail": {"t0": t0, "t1": t1, "rows": len(ticks),
                              "tick_key": tick_key, "schema": schema}})
    checks.append({"check": "record_classes", "result": "PASS",
                   "detail": {"present": sorted(present),
                              "declared_absent": sorted(absent_names)}})
    return {"trace": trace, "schema": schema, "tick_key": tick_key,
            "index": index, "t0": t0, "t1": t1,
            "present": present, "declared_absent": declared_absent,
            "binding": trace_spec.get("binding", "trace")}


# ------------------------------------------------------------- video ----

def build_video(assembly, bindings, records, checks):
    video_spec = assembly.get("video") or {}
    require(video_spec, "video_section_missing", {"why": "no video section"})
    media = bindings.get(video_spec.get("media_binding", "video_media"))
    require(media is not None, "binding_missing", {"binding": "video_media"})
    manifest = bind_json(bindings, video_spec.get("manifest_binding",
                                                  "capture_manifest"))

    require(manifest.get("schema") in
            ("chimera.visual_capture_manifest.v1",
             "chimera.capture_gate.capture_manifest.v1",
             "chimera.walkfilm_manifest.v1"),
            "video_manifest_schema_invalid", {"schema": manifest.get("schema")})

    capture_sha = manifest.get("capture_sha256")
    require(capture_sha == media["sha256"], "video_media_identity_mismatch",
            {"capture_manifest_sha256": capture_sha,
             "media_sha256": media["sha256"],
             "why": "the media identity declared by the capture manifest must "
                    "equal the bound media bytes"})

    sheet = manifest.get("sheet_layout") or {}
    frame_files = sheet.get("frame_files")
    frames = []
    if isinstance(frame_files, dict) and frame_files:
        # The M09 law: sheet keys are TICKS; resolve numerically.
        for key, sha in frame_files.items():
            frames.append({"frame_id": "tick_%d" % tick_int(key),
                           "tick": tick_int(key), "sha256": sha})
        source = "sheet_layout.frame_files"
    else:
        raw = manifest.get("frame_manifest") or []
        require(isinstance(raw, list) and raw, "frame_binding_source_missing",
                {"why": "neither sheet_layout.frame_files nor frame_manifest "
                        "present in the capture manifest"})
        for entry in raw:
            require(isinstance(entry.get("tick"), int), "frame_binding_source_missing",
                    {"entry": entry, "why": "frame entry without an integer tick"})
            frames.append({"frame_id": entry.get("frame", "frame_%d" % entry["tick"]),
                           "tick": entry["tick"],
                           "sha256": entry.get("sha256"),
                           "state_hash": entry.get("state_hash")})
        source = "frame_manifest"

    # The M09 law, both halves: keys resolve NUMERICALLY and are processed in
    # NUMERIC order — dict/JSON iteration is lexicographic ('10464' < '1111')
    # and naive ordering reports inversions that do not exist.
    frames.sort(key=lambda f: f["tick"])

    declared_count = sheet.get("frame_count", len(frames))
    require(len(frames) == declared_count, "sync_frame_count_mismatch",
            {"declared": declared_count, "resolved": len(frames)})

    unresolved, outside, unsorted_pairs = [], [], []
    last = None
    for frame in frames:
        tick = frame["tick"]
        if tick not in records["index"]:
            if records["t0"] <= tick <= records["t1"]:
                unresolved.append(tick)
            else:
                outside.append(tick)
        if last is not None and tick <= last:
            unsorted_pairs.append([last, tick])
        last = tick
    require(not outside, "sync_frame_outside_tick_domain",
            {"frames": outside[:8], "domain": [records["t0"], records["t1"]],
             "why": "THE SYNC LAW: a frame whose tick is outside the records "
                    "domain is an unbindable row = package FAILURE"})
    require(not unresolved, "sync_frame_tick_unresolved",
            {"frames": unresolved[:8],
             "why": "THE SYNC LAW: a frame whose tick has no records row is an "
                    "unbound row = package FAILURE"})
    require(not unsorted_pairs, "sync_frame_ticks_not_unique_monotonic",
            {"pairs": unsorted_pairs[:8],
             "why": "duplicate or non-increasing frame ticks cannot join"})

    receipt_binding = video_spec.get("receipt_binding")
    receipt = None
    if receipt_binding:
        receipt = bind_json(bindings, receipt_binding)
        trace_sha = bindings[records["binding"]]["sha256"]
        media_sha = media["sha256"]
        rt = receipt.get("trace_sha256")
        rv = receipt.get("video_sha256")
        require(rt is None or rt == trace_sha, "video_trace_identity_mismatch",
                {"receipt_trace_sha256": rt, "bound_trace_sha256": trace_sha})
        require(rv is None or rv == media_sha, "video_trace_identity_mismatch",
                {"receipt_video_sha256": rv, "bound_media_sha256": media_sha})

    ticks = [f["tick"] for f in frames]
    gaps = [b - a for a, b in zip(ticks, ticks[1:])] or [0]
    checks.append({"check": "sync_frames_resolved", "result": "PASS",
                   "detail": {"source": source, "frames": len(frames),
                              "tick_range": [ticks[0], ticks[-1]],
                              "max_gap_ticks": max(gaps),
                              "media_sha256": media["sha256"]}})
    return {"media": media, "manifest_binding": video_spec.get(
        "manifest_binding", "capture_manifest"), "frames": frames,
        "source": source, "tick_interval": manifest.get("tick_interval"),
        "receipt_binding": receipt_binding, "still_bytes": video_spec.get(
            "still_bytes", "PRESENT")}


# ------------------------------------------------------------ inputs ----

def build_inputs(assembly, bindings, records, checks):
    inputs_spec = assembly.get("inputs") or {}
    trace = records["trace"]
    events = []
    log_schema = None
    if inputs_spec.get("events_from") == "trace" or "decisions" in trace:
        log_schema = trace.get("schema")
        decisions = trace.get("decisions") or []
        require(decisions, "input_log_not_expressible",
                {"why": "no decisions events in the bound trace"})
        sink = trace.get("sink_records") or []
        # The session census is BYTE-DERIVED ONLY: identities recorded in the
        # bound trace (sink_records + decisions' own source fields). The
        # assembly's source_default is SELF-DECLARED — it labels events that
        # carry no source and is attested separately, never counted.
        byte_sources = sorted({str(s.get("source")) for s in sink if s.get("source")}
                              | {str(d["source"]) for d in decisions
                                 if d.get("source")})
        require(byte_sources, "input_log_not_expressible",
                {"why": "no source identity in the bound bytes; the session "
                        "law (no_reset) cannot be evaluated"})
        for position, decision in enumerate(decisions):
            require("issued_tick" in decision, "input_log_not_expressible",
                    {"event_index": position,
                     "why": "event without issued_tick cannot join on tick"})
            events.append({
                "event_index": position,
                "command": decision.get("command", inputs_spec.get(
                    "command_default", "commanded_segment")),
                "issued_tick": tick_int(decision["issued_tick"]),
                "issued_ms": decision.get("issued_ms"),
                "source": decision.get("source",
                                       inputs_spec.get("source_default",
                                                       "trace")),
                "requested": decision.get("requested"),
                "applied": decision.get("applied"),
                "saturation": decision.get("saturation"),
                "wrong_script": decision.get("wrong_script"),
            })
    else:
        raise Refusal("input_log_not_expressible",
                      {"why": "no recognized event source in the assembly"})

    t0, t1 = records["t0"], records["t1"]
    outside = [e["issued_tick"] for e in events if not (t0 <= e["issued_tick"] <= t1)]
    require(not outside, "input_event_outside_domain",
            {"events": outside[:8], "domain": [t0, t1]})

    # Session law (no_reset, mechanical half): exactly ONE byte-derived
    # source identity, unless the assembly declares the allowed set.
    allowed_sources = inputs_spec.get("allowed_sources")
    if allowed_sources is not None:
        undeclared = [s for s in byte_sources if s not in set(allowed_sources)]
        require(not undeclared, "input_assertion_violation",
                {"class": "multi_source_session", "sources": undeclared[:8],
                 "allowed_sources": sorted(allowed_sources),
                 "why": "a byte-derived input source outside the declared "
                        "allowed set is an undeclared control path"})
    else:
        require(len(byte_sources) == 1, "input_assertion_violation",
                {"class": "multi_source_session", "sources": byte_sources[:8],
                 "why": "the no_reset law requires exactly ONE run session/"
                        "source identity produced the records; declare "
                        "allowed_sources in the assembly to widen this "
                        "(the widening is then a frozen, reviewed decision)"})

    # Command-name scan (no_hidden_anchor / no_reset log halves, mechanical):
    # an event whose COMMAND name carries a prohibited class token refuses.
    command_violations = {}
    for event in events:
        tokens = [t for t in re.split(r"[^a-z0-9]+",
                                      str(event.get("command", "")).lower()) if t]
        for token in tokens:
            klass = PROHIBITED_COMMAND_TOKENS.get(token)
            if klass:
                command_violations.setdefault(klass, []).append(
                    event["event_index"])
    for klass in ("teleport", "hidden_anchor", "reset"):
        require(not command_violations.get(klass), "input_assertion_violation",
                {"class": klass,
                 "event_indices": command_violations.get(klass, [])[:8],
                 "why": "an input-event command name carries a prohibited "
                        "anchor/weld/teleport/reset class token; the "
                        "prohibition is a check over the bound log"})

    wrong = [e["event_index"] for e in events if e.get("wrong_script")]
    require(not wrong, "input_assertion_violation",
            {"class": "wrong_script", "event_indices": wrong[:8],
             "why": "an event flagged wrong_script is an undeclared input"})

    # Teleport-class check on commanded application: with an all-zero
    # saturation vector the applied vector must equal requested exactly;
    # a silent re-write of the command is a teleport-class violation.
    rewritten, clamped = [], 0
    for event in events:
        requested, applied = event.get("requested"), event.get("applied")
        saturation = event.get("saturation") or []
        if requested is None or applied is None:
            continue
        if all(float(s) == 0.0 for s in saturation):
            if requested != applied:
                rewritten.append(event["event_index"])
        else:
            clamped += 1
    require(not rewritten, "input_assertion_violation",
            {"class": "teleport", "event_indices": rewritten[:8],
             "why": "applied != requested with zero declared saturation: the "
                    "input path re-wrote a command outside the declared mapping"})

    # Per-tick intervention surface (teleport / hidden_anchor / reset).
    tick_key = records["tick_key"]
    intervention_field = (assembly.get("inputs") or {}).get(
        "intervention_field", "intervention_reason")
    violations = {}
    scanned = 0
    for tick, row in records["index"].items():
        # K02-class injection registers, when present, are checked directly.
        injections = row.get("injections")
        if isinstance(injections, dict):
            for key, prohibited in (("hidden_anchor", "hidden_anchor"),
                                    ("teleport_at_tick", "teleport"),
                                    ("sticky_release_weld", "hidden_anchor")):
                if key in injections and injections[key] not in (None, False):
                    violations.setdefault(prohibited, []).append(tick)
        reason = row.get(intervention_field)
        if reason is None:
            continue
        scanned += 1
        text_reason = str(reason)
        if text_reason in PROHIBITED_INTERVENTIONS:
            violations.setdefault(PROHIBITED_INTERVENTIONS[text_reason],
                                  []).append(tick)
        elif text_reason not in (assembly.get("inputs") or {}).get(
                "allowed_interventions", ["none"]):
            violations.setdefault("undeclared_intervention",
                                  []).append(tick)
    for klass in ("teleport", "hidden_anchor", "reset"):
        require(not violations.get(klass), "input_assertion_violation",
                {"class": klass, "ticks": violations.get(klass, [])[:8],
                 "count": len(violations.get(klass, [])),
                 "why": "the records carry a prohibited intervention; the "
                        "prohibition is a check over the bound log+records"})
    require(not violations.get("undeclared_intervention"),
            "input_assertion_violation",
            {"class": "undeclared_intervention",
             "ticks": violations.get("undeclared_intervention", [])[:8],
             "why": "an intervention class outside the declared allowed set "
                    "is itself undeclared authority; declare it in "
                    "allowed_interventions or remove it"})

    reset_evidence = {"contiguous_domain": True,
                      "duplicate_ticks": 0,
                      "byte_derived_sessions": len(byte_sources),
                      "allowed_sources_declared": allowed_sources is not None}
    checks.append({"check": "input_assertions", "result": "PASS",
                   "detail": {"events": len(events),
                              "intervention_rows_scanned": scanned,
                              "clamped_events": clamped,
                              "byte_derived_sources": byte_sources,
                              "declared_source_default":
                                  inputs_spec.get("source_default"),
                              "command_tokens_scanned": True,
                              "no_reset": reset_evidence}})
    return {"events": events, "log_schema": log_schema, "sources": byte_sources,
            "declared_source_default": inputs_spec.get("source_default"),
            "intervention_field": intervention_field,
            "intervention_rows_scanned": scanned,
            "binding": inputs_spec.get("binding", records["binding"])}


# ------------------------------------------------------------ phases ----

def build_phases(assembly, records, checks):
    phases = (assembly.get("phases") or {}).get("boundaries") or []
    unresolved = []
    for phase in phases:
        tick = phase.get("tick")
        require(tick is not None, "phase_boundary_unresolved",
                {"phase": phase, "why": "boundary without a tick"})
        if tick_int(tick) not in records["index"]:
            unresolved.append(phase)
    require(not unresolved, "phase_boundary_unresolved",
            {"phases": unresolved[:8],
             "why": "every declared phase boundary must resolve to a records "
                    "row (per-phase transition evidence)"})
    checks.append({"check": "phase_boundaries_resolved", "result": "PASS",
                   "detail": {"boundaries": [tick_int(p["tick"]) for p in phases],
                              "law": "phase transitions occur inside ONE tick "
                                     "sequence; no reset between phases"}})
    return phases


# -------------------------------------------------------------- build ----

def package_body(assembly):
    checks = []
    bindings = resolve_bindings(assembly, checks)
    freeze = build_freeze(assembly, bindings, checks)
    records = build_records(assembly, bindings, checks)
    video = build_video(assembly, bindings, records, checks)
    inputs = build_inputs(assembly, bindings, records, checks)
    phases = build_phases(assembly, records, checks)

    package_class = assembly.get("package_class")
    label = assembly.get("label", "")
    require(package_class in ("FINAL_DEMONSTRATION", "VALIDATION_ONLY"),
            "package_class_invalid", {"package_class": package_class})
    if package_class == "VALIDATION_ONLY":
        require("VALIDATION-ONLY" in label.upper().replace("_", "-").replace(" ", "-"),
                "validation_label_missing",
                {"label": label, "why": "a validation package must be labeled "
                                        "VALIDATION-ONLY; it is never the final "
                                        "deliverable"})

    body = {
        "schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "created_at_utc": now_utc(),
        "package_class": package_class,
        "label": label,
        "run_identity": assembly.get("run_identity") or {},
        "freeze_manifest": {
            "frozen_at_utc": now_utc(),
            "freeze_law": "post-freeze changes refuse: verify re-hashes every "
                          "binding and refuses freeze_violation on any mismatch",
            "build": freeze.get("build") or {},
            "scene": freeze.get("scene") or {},
            "body_mass_ownership": freeze.get("body_mass_ownership") or {},
            "control_interface": freeze.get("control_interface") or {},
            "parameters": freeze.get("parameters") or {},
            "pass_criteria": freeze.get("pass_criteria") or {},
            "bindings": bindings,
        },
        "video": {
            "artifact": assembly_video_media(assembly, bindings),
            "capture_manifest": {
                "reference": bindings[video["manifest_binding"]]["reference"],
                "sha256": bindings[video["manifest_binding"]]["sha256"]},
            "frame_binding": {"source": video["source"], "frames": video["frames"],
                              "frame_count": len(video["frames"]),
                              "tick_interval": video["tick_interval"],
                              "still_bytes": video["still_bytes"]},
            "binding_receipt": ({"reference": bindings[video["receipt_binding"]]["reference"],
                                 "sha256": bindings[video["receipt_binding"]]["sha256"]}
                                if video["receipt_binding"] else None),
        },
        "inputs": {
            "log": {"reference": bindings[inputs["binding"]]["reference"],
                    "sha256": bindings[inputs["binding"]]["sha256"],
                    "schema": inputs["log_schema"]},
            "event_count": len(inputs["events"]),
            "events": inputs["events"],
            "session_sources": inputs["sources"],
            "declared_source_default": inputs["declared_source_default"],
            "intervention_field": inputs["intervention_field"],
            "intervention_rows_scanned": inputs["intervention_rows_scanned"],
            "assertions": {"no_teleport": "PASS", "no_hidden_anchor": "PASS",
                           "no_reset": "PASS"},
        },
        "records": {
            "trace": {"reference": bindings[records["binding"]]["reference"],
                      "sha256": bindings[records["binding"]]["sha256"],
                      "schema": records["schema"]},
            "tick_key": records["tick_key"],
            "tick_domain": [records["t0"], records["t1"]],
            "contiguous": True,
            "classes_present": records["present"],
            "declared_absent": records["declared_absent"],
        },
        "phases": {"boundaries": phases,
                   "continuity_law": "one uninterrupted run: a single tick "
                                     "domain, no reset between phases"},
        "review_plan": assembly.get("review_plan") or {},
        "verification": {"checks": checks},
    }
    body["package_sha256"] = sha256_bytes(canon(body))
    return body


def assembly_video_media(assembly, bindings):
    name = (assembly.get("video") or {}).get("media_binding", "video_media")
    return dict(bindings[name], binding=name)


def cmd_build(a):
    assembly = load_json(a.assembly)
    require(isinstance(assembly, dict), "assembly_invalid", {})
    body = package_body(assembly)
    out = Path(a.out)
    require(not out.exists(), "output_exists",
            {"path": str(out), "why": "packages are immutable; choose a new path"})
    write_bytes_lf_free(out, canon(body) + b"\n")
    print("EVIDENCE PACKAGE BUILT (%s)" % body["package_class"])
    print("  package sha256 : %s" % body["package_sha256"])
    print("  package file   : %s" % out)
    print("  run            : %s" % body["run_identity"].get("run_id"))
    print("  tick domain    : %s" % body["records"]["tick_domain"])
    print("  frames bound   : %d (%s)" % (body["video"]["frame_binding"]["frame_count"],
                                         body["video"]["frame_binding"]["source"]))
    print("  input events   : %d" % body["inputs"]["event_count"])
    print("  record classes : %s / declared_absent %s"
          % (sorted(body["records"]["classes_present"]),
             [d["class"] for d in body["records"]["declared_absent"]]))
    print("  checks         : %d PASS" % len(body["verification"]["checks"]))
    print(json.dumps({"package_sha256": body["package_sha256"],
                      "package_class": body["package_class"],
                      "path": str(out)}, sort_keys=True))
    return 0


# ------------------------------------------------------------- verify ----

def cmd_verify(a):
    package_path = Path(a.package)
    raw = package_path.read_bytes()
    package = json.loads(raw.decode("utf-8"))
    require(package.get("schema") == SCHEMA, "package_schema_invalid",
            {"schema": package.get("schema")})
    stored = package.get("package_sha256")
    body = {k: v for k, v in package.items() if k != "package_sha256"}
    require(stored == sha256_bytes(canon(body)), "package_tampered",
            {"path": str(package_path),
             "why": "the package body no longer matches its content address"})

    checks = []
    bindings = (package.get("freeze_manifest") or {}).get("bindings") or {}
    require(bindings, "freeze_manifest_incomplete", {"section": "bindings"})
    for name, item in sorted(bindings.items()):
        path = Path(item["reference"])
        require(path.is_file(), "freeze_violation",
                {"binding": name, "reference": item["reference"],
                 "why": "the frozen artifact is missing"})
        observed, _size = sha256_file(path)
        require(observed == item["sha256"], "freeze_violation",
                {"binding": name, "reference": item["reference"],
                 "expected_sha256": item["sha256"], "observed_sha256": observed,
                 "why": "POST-FREEZE MODIFICATION: a bound byte changed after "
                        "the freeze; the package refuses"})

    # Re-prove the sync law over the frozen bytes.
    assembly_shape = {
        "records": {"binding": _binding_name_for(bindings, package["records"]["trace"]),
                    "tick_key": package["records"]["tick_key"],
                    "tick_domain": package["records"]["tick_domain"],
                    "classes": package["records"]["classes_present"],
                    "declared_absent": package["records"]["declared_absent"]},
        "video": {"media_binding": package["video"]["artifact"].get("binding",
                                                                   "video_media"),
                  "manifest_binding": _binding_name_for(
                      bindings, package["video"]["capture_manifest"]),
                  "receipt_binding": (_binding_name_for(
                      bindings, package["video"]["binding_receipt"])
                      if package["video"].get("binding_receipt") else None),
                  "still_bytes": package["video"]["frame_binding"].get("still_bytes")},
        "inputs": {"events_from": "trace",
                   "binding": _binding_name_for(bindings, package["inputs"]["log"]),
                   "intervention_field": package["inputs"]["intervention_field"],
                   "allowed_interventions": ["none"]},
    }
    frozen = dict(package["freeze_manifest"])
    reassembly = dict(package=package)
    reassembly["bindings"] = bindings
    reassembly["package_class"] = package["package_class"]
    reassembly["label"] = package["label"]
    reassembly["freeze_manifest"] = frozen
    reassembly.update(assembly_shape)
    reassembly["phases"] = package.get("phases") or {}

    checks.extend(package.get("verification", {}).get("checks", []))
    records = build_records(reassembly, bindings, checks)
    build_video(reassembly, bindings, records, checks)
    build_inputs(reassembly, bindings, records, checks)
    build_phases(reassembly, records, checks)

    receipt = {"schema": "chimera.evidence_package.verification.v1",
               "tool_version": TOOL_VERSION,
               "verified_at_utc": now_utc(),
               "package": str(package_path),
               "package_sha256": stored,
               "package_class": package["package_class"],
               "bindings_reverified": len(bindings),
               "checks": checks,
               "result": "VERIFIED"}
    receipt_path = package_path.with_name(
        package_path.stem + ".verification.json")
    require(not receipt_path.exists() or a.allow_overwrite,
            "output_exists", {"path": str(receipt_path)})
    write_bytes_lf_free(receipt_path, canon(receipt) + b"\n")
    print("EVIDENCE PACKAGE VERIFIED (%s)" % stored)
    print("  bindings re-hashed : %d (freeze law holds)" % len(bindings))
    print("  sync law           : frames resolved, events in domain")
    print("  assertions         : no_teleport / no_hidden_anchor / no_reset PASS")
    print("  verification       : %s" % receipt_path)
    print(json.dumps({"package_sha256": stored, "result": "VERIFIED",
                      "receipt": str(receipt_path)}, sort_keys=True))
    return 0


def _binding_name_for(bindings, target):
    ref = (target or {}).get("reference")
    for name, item in bindings.items():
        if item.get("reference") == ref:
            return name
    raise Refusal("binding_missing",
                  {"binding": ref, "why": "package section references an "
                                          "artifact outside the freeze bindings"})


def cmd_inspect(a):
    package = load_json(a.package)
    stored = package.get("package_sha256")
    body = {k: v for k, v in package.items() if k != "package_sha256"}
    ok = stored == sha256_bytes(canon(body))
    print("PACKAGE %s (%s)" % (a.package, "INTACT" if ok else "TAMPERED"))
    print("  class/label : %s / %s" % (package.get("package_class"),
                                       package.get("label")))
    print("  run         : %s" % package.get("run_identity", {}).get("run_id"))
    print("  ticks       : %s contiguous=%s"
          % (package.get("records", {}).get("tick_domain"),
             package.get("records", {}).get("contiguous")))
    print("  frames      : %s" % package.get("video", {})
          .get("frame_binding", {}).get("frame_count"))
    print("  events      : %s" % package.get("inputs", {}).get("event_count"))
    print("  bindings    : %d" % len((package.get("freeze_manifest") or {})
                                     .get("bindings") or {}))
    return 0 if ok else EXIT_REFUSED


# --------------------------------------------------------------- main ----

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("build")
    p.add_argument("--assembly", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("verify")
    p.add_argument("--package", required=True)
    p.add_argument("--allow-overwrite", action="store_true")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("inspect")
    p.add_argument("--package", required=True)
    p.set_defaults(func=cmd_inspect)

    a = parser.parse_args(argv)
    out_dir = None
    if a.cmd == "build":
        out_dir = str(Path(a.out).parent)
    elif a.cmd == "verify":
        out_dir = str(Path(a.package).parent)
    try:
        return a.func(a)
    except Refusal as refusal:
        record_refusal(out_dir, a.cmd, refusal)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
