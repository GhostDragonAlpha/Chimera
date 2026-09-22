"""The ENGINE snapshot-API registry: the four registered restart-state gaps.

The upgrade gate's restart-state inventory (runner.inventory_block) carries four
REGISTERED GAPS against the production path -- gap_engine_contact_warm_start,
gap_engine_reflex_state, gap_engine_controller_history, gap_engine_world_state
-- which validator-BLOCK every production-class certificate while unresolved.

This module is the registry that CLOSES them for builds carrying the
OUT-OF-TREE GAIT_SNAPSHOT_API instrument (the wave/ifreeze read-only-build-flag
precedent: a lane-dir copy of the engine headers with a dormant flag; zero
shipped bytes; ship-invariance fenced against the base's own anchors). Each gap
names its reader, the proof artifacts, and the verdicts. The certificate
validator (certificate._validate_inventory) enforces that a RESOLVED gap
CARRIES verifiable proof fields -- a RESOLVED gap without proof is a violation,
so only PROVEN readers un-block the production class.

Lane of record:
tools/science_funnel/validation/snapshot_apis_20260920/ (receipt.json is the
Rule-0 law; proof_compare.json + fence.json hold the measured verdicts).
"""
from __future__ import annotations

import hashlib
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LANE_DIR = os.path.join(REPO, "tools", "science_funnel", "validation",
                        "snapshot_apis_20260920")

# The four production restart-state gaps, in the inventory's own vocabulary.
ENGINE_GAPS = (
    {"name": "gap_engine_contact_warm_start", "item": "contact_warm_start_cache",
     "reader_class": "contact_warm_start"},
    {"name": "gap_engine_reflex_state", "item": "reflex_state",
     "reader_class": "reflex_state"},
    {"name": "gap_engine_controller_history", "item": "controller_history",
     "reader_class": "controller_history"},
    {"name": "gap_engine_world_state", "item": "world_state",
     "reader_class": "world_state"},
)

# The engine-side inventory items that carry the four classes (the surrogate
# scene's eight-item inventory is runner.inventory_block's; this is the
# production-path counterpart for an instrumented engine build).
ENGINE_INVENTORY_ITEMS = (
    {"name": "body_state", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.world_state",
     "contents": "base q/v + joint q/v/speeds (the walker's dynamical state, "
                 "GaitWalker::gait_snap_serialize class 0)"},
    {"name": "contact_warm_start_cache", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.contact_warm_start",
     "contents": "touch-hysteresis state + persistent/per-tick contact books "
                 "(class 1)"},
    {"name": "reflex_state", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.reflex_state",
     "contents": "hind-step/height/capture reflex state + censuses (class 2)"},
    {"name": "held_command", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.controller_history",
     "contents": "command hold (cmd_vx_live_/cmd_vx_/cmd_vx_tick_) in class 3"},
    {"name": "decision_phase", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.controller_history",
     "contents": "the hybrid contact-reset clock phi_[2] + ticks_ (class 3)"},
    {"name": "controller_history", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.controller_history",
     "contents": "fore/hind calendars, actuator stores, last_torque_, pin "
                 "census, settle/e_ref (class 3)"},
    {"name": "rng_stream", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.none",
     "contents": "the engine walk carries NO random stream: the scene pin "
                 "(gait_scene.json sha) plus the deterministic solver close "
                 "the trajectory; no RNG state exists to serialize"},
    {"name": "world_state", "snapshotable": True,
     "snapshot_key": "engine.gait_snapshot.world_state",
     "contents": "the walker's full dynamical + ledger state s_ (class 0)"},
)

READER_ID = "gait_snapshot_api/out-of-tree@snapshot_apis_20260920"


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read(path: str) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def load_snapshot_manifest(lane_dir: str = LANE_DIR) -> dict | None:
    """The C++-emitted field manifest of the dump (class, field, kind, count,
    offset per field) -- the reader's own completeness record."""
    raw = _read(os.path.join(lane_dir, "instrument", "runs", "ref1.manifest.json"))
    if raw is None:
        raw = _read(os.path.join(lane_dir, "runs", "ref1.manifest.json"))
    if raw is None:
        return None
    return json.loads(raw.decode("utf-8"))


def _proof_artifacts(lane_dir: str) -> dict[str, bytes | None]:
    runs = os.path.join(lane_dir, "runs")
    out = {}
    for name in ("proof_compare.json", "fence.json", "receipt.json"):
        out[name] = _read(os.path.join(lane_dir if name == "receipt.json" else runs, name))
    return out


def verify_lane_proofs(lane_dir: str = LANE_DIR) -> tuple[bool, list[str]]:
    """Recompute the lane's proof verdicts from its artifacts (issuance-time
    authority). Returns (all_green, reasons). Fail-safe: any missing or red
    artifact leaves the gaps UNRESOLVED."""
    reasons: list[str] = []
    arts = _proof_artifacts(lane_dir)
    for name, raw in arts.items():
        if raw is None:
            reasons.append(f"missing artifact: {name}")
    if reasons:
        return False, reasons
    pc = json.loads(arts["proof_compare.json"].decode("utf-8"))
    fe = json.loads(arts["fence.json"].decode("utf-8"))
    rec = json.loads(arts["receipt.json"].decode("utf-8"))
    if not pc.get("pass"):
        reasons.append("proof_compare.json verdict not green: " + str(pc.get("reasons")))
    out = pc.get("out") or pc
    # the receipt's frozen Rule-0 sha must still verify (append-only integrity)
    rule0 = rec.get("pre_registration", {}).get("rule_0")
    want = rec.get("pre_registration", {}).get("frozen_rule_0_sha")
    got = sha256_hex(json.dumps(rule0, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True).encode("utf-8"))
    if got != want:
        reasons.append(f"receipt rule_0 sha drift: {got[:16]} != {want[:16]}")
    # F1: the restore must be bit-identical on BOTH instruments
    f1 = out.get("f1_restore_bit_identity", {})
    if not f1.get("pass"):
        reasons.append("F1 restore bit-identity not green: " + str(f1.get("detail", "")))
    # F4: determinism
    f4 = out.get("f4_determinism", {})
    if not f4.get("pass"):
        reasons.append("F4 determinism not green: " + str(f4.get("detail", "")))
    # F3: every class load-bearing under the forced-drop probe
    f3 = out.get("f3_forced_drop_load_bearing", {})
    for gap in ENGINE_GAPS:
        cls = gap["reader_class"]
        probe = (f3.get("classes") or {}).get(cls, {})
        if not probe.get("load_bearing"):
            reasons.append(f"F3 forced-drop probe: {cls} not load-bearing")
    # F2: the ship-invariance fence
    if not fe.get("pass"):
        reasons.append("F2 ship-invariance fence not green: " + str(fe.get("detail", "")))
    return not reasons, reasons


def gap_proof_block(lane_dir: str = LANE_DIR) -> dict:
    """The proof block embedded in every RESOLVED gap (the validator consumes
    these fields; certificate._validate_inventory enforces their presence)."""
    arts = _proof_artifacts(lane_dir)
    receipt_sha = sha256_hex(arts["receipt.json"]) if arts["receipt.json"] else None
    return {
        "reader": READER_ID,
        "kind": "out-of-tree read-only build flag (GAIT_SNAPSHOT_API); "
                "zero shipped bytes; ship-invariance fenced",
        "proof_receipt_sha256": receipt_sha,
        "restore_bit_identity": True,
        "ship_invariance": "PASS",
        "load_bearing_forced_drops": True,
        "proof_lane": "tools/science_funnel/validation/snapshot_apis_20260920",
    }


def engine_gap_registry(lane_dir: str = LANE_DIR) -> tuple[list[dict], list[str]]:
    """The registered_gaps list for an INSTRUMENTED engine build. Returns
    (gaps, verify_reasons): RESOLVED + proof when the lane's proofs verify,
    the original REGISTERED GAP statuses otherwise (fail-safe)."""
    ok, reasons = verify_lane_proofs(lane_dir)
    if not ok:
        return [dict(g, status="REGISTERED GAP (pending engine binding)",
                     cause="no verified snapshot-api proof for this build",
                     clears_when="the snapshot-apis lane's readers + proofs verify")
                for g in ENGINE_GAPS], reasons
    proof = gap_proof_block(lane_dir)
    gaps = []
    for g in ENGINE_GAPS:
        entry = dict(g)
        entry["status"] = ("RESOLVED (snapshot-api reader + restore bit-identity "
                           "proof, ship-invariance fenced)")
        entry["cause"] = ("closed by the out-of-tree GAIT_SNAPSHOT_API instrument: "
                          "class serialized per tick, restored in a fresh process, "
                          "future bit-identical on tick hashes AND action bytes")
        entry["clears_when"] = "n/a (resolved; the proof lane is bound by sha)"
        entry["proof"] = proof
        gaps.append(entry)
    return gaps, reasons


def production_inventory(lane_dir: str = LANE_DIR) -> dict:
    """The restart-state inventory for a PRODUCTION-class certificate on an
    instrumented engine build. The validator un-blocks the production class
    only when every gap here is RESOLVED with verifiable proof."""
    gaps, _ = engine_gap_registry(lane_dir)
    return {"deployment_class": "production",
            "items": [dict(it) for it in ENGINE_INVENTORY_ITEMS],
            "registered_gaps": gaps,
            "gap_rule": "PRODUCTION certificates REQUIRE zero unresolved gaps "
                        "AND verifiable proof on every RESOLVED gap "
                        "(validator-enforced BLOCK); this inventory closes the "
                        "four engine gaps through the snapshot-apis readers."}


def check_registry_completeness(lane_dir: str = LANE_DIR) -> tuple[bool, list[str]]:
    """The reader's serialized classes must cover the prereg's named fields
    (the C++ manifest is checked against the receipt's class inventories)."""
    reasons: list[str] = []
    man = load_snapshot_manifest(lane_dir)
    if man is None:
        return False, ["snapshot manifest not found (instrument not run)"]
    rec = json.loads(_read(os.path.join(lane_dir, "receipt.json")).decode("utf-8"))
    classes = rec["pre_registration"]["rule_0"]["instrument"]["classes_serialized"]

    def norm(name: str) -> str:
        # the prereg declares C++ member notation (s_.q[18], hind_step_mode_[2],
        # fore_hold_off_[2]x3); the manifest records the serializer's field
        # names (q, hind_step_mode[leg0], fore_hold_off[leg0]) -- normalize
        n = name.strip()
        if n.startswith("s_."):
            n = n[3:]
        n = n.split("[")[0]
        if n.endswith("x3"):
            n = n[:-2]
        return n.rstrip("_")

    by_class: dict[str, list[str]] = {}
    for fld in man:
        by_class.setdefault(fld["class"], []).append(fld["field"].split("[")[0])
    for cls, declared in classes.items():
        got = by_class.get(cls, [])
        if not got:
            reasons.append(f"class {cls}: no fields in the manifest")
            continue
        for token in declared.replace(",", " ").split():
            want = norm(token)
            if want and not any(f == want or f.startswith(want) or want.startswith(f)
                                for f in got):
                reasons.append(f"class {cls}: prereg field {token} not in manifest")
    return not reasons, reasons
