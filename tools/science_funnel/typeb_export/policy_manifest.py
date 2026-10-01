"""TypeB-P3 policy manifest: Astra's missing piece #2 -- the complete frozen contract.

A weight file is insufficient. The manifest binds (per the shared registration
envelope, lane-archive astra-typeb-pilots-20260921.md): claim + named falsifiers, CPU
reference commit / record-set digest / build environment, horizon and tick conventions,
baseline scene and receipts, body digests (UNBOUND for the dummy), reflex set version +
initialization/reset semantics, observation schema (units, frames, availability),
action schema (units, bounds, mapping, command clock and hold semantics), training
backend (NONE: dummy), policy architecture + weights + preprocessing digests, CPU
export implementation and deterministic inference recipe, evaluation distribution.

The manifest hash: canonical JSON (sorted keys, no whitespace, UTF-8) over the manifest
with the "manifest_hash" field itself removed -- sha256 hex. Because every component
lives inside the manifest (weights enter via weights_sha256; the record set via
record_set_digest; the environment via build_env), ANY field change moves the hash.
That is F-CPU-POLICY-BYTES clause (b).
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys

MANIFEST_VERSION = "typeb-policy-manifest/1.0.0"

# THE DEPLOYMENT-INFERENCE FREEZE (ADDED by lane/policy-interface-freeze-20260920;
# purely additive and BACKWARD-COMPATIBLE: an optional `inference_freeze` block,
# validated ONLY when present -- existing manifests (without the block) validate
# exactly as before and their canonical manifest_hash is byte-identical (pinned:
# the P3 manifest's 9ca7e976...). A NEW manifest that will feed skill #1 training
# MUST carry the block: it pins the deployment-side facts the training side is
# entitled to assume -- deterministic action selection, the compute precision,
# the exported-graph pinning, and the normalization constants' digest -- so a
# deployment runtime cannot drift from the trained contract without moving the
# manifest hash (F-CPU-POLICY-BYTES discipline, extended to the runtime).
DEPLOYMENT_INFERENCE_VERSION = "deployment-inference/1.0.0"
_PRECISION_STORAGE = "float32"

_REQUIRED_TOP = [
    "manifest_version", "kind", "claim", "named_falsifiers", "cpu_reference",
    "horizon_and_ticks", "scene_and_receipts", "body", "reflex_set", "physics_version",
    "observation", "normalization", "action", "policy", "inference", "reset",
    "evaluation", "receipts",
]

_REQUIRED_POLICY = ["architecture", "activation", "weights_format", "weights_sha256",
                    "param_count", "mac_count", "seed", "training_backend"]

_REQUIRED_INFERENCE_FREEZE = [
    "deployment_inference_version", "deterministic_action_selection", "precision",
    "exported_graph", "normalization_constants", "action_selection",
]


def inference_freeze_block(weights_bytes: bytes, norm_mean, norm_std, clip: float,
                           clock: dict) -> dict:
    """Assemble the optional block deterministically (for future manifests).
    digest laws: graph_sha256 = sha256(weights_bytes); normalization digest =
    sha256 over canonical JSON of {mean, std, clip} -- the SAME law
    build_policy_manifest.py's normalization.digest uses."""
    import numpy as np
    return {
        "deployment_inference_version": DEPLOYMENT_INFERENCE_VERSION,
        "deterministic_action_selection": True,
        "precision": {"storage": _PRECISION_STORAGE, "compute": _PRECISION_STORAGE,
                      "accumulate": _PRECISION_STORAGE, "batch": 1},
        "exported_graph": {
            "format": "numpy-npz/float32/c-contiguous",
            "graph_sha256": hashlib.sha256(weights_bytes).hexdigest(),
            "op_set": ["matvec", "tanh", "add", "mul", "clip"],
            "graph_pinned": True,
        },
        "normalization_constants": {
            "source": "manifest.normalization (mean/std/clip)",
            "digest_sha256": hashlib.sha256(json.dumps(
                {"mean": [float(v) for v in np.asarray(norm_mean, dtype=np.float32)],
                 "std": [float(v) for v in np.asarray(norm_std, dtype=np.float32)],
                 "clip": float(clip)}, sort_keys=True).encode("utf-8")).hexdigest(),
            "mean_fill_semantics": "unavailable channel -> mean fill (exactly 0.0 "
                                   "in normalized space); the mask is observed",
            "clip": float(clip),
        },
        "action_selection": {
            "rule": "raw deterministic map; no sampling, no argmax",
            "mapping": "applied = clip(center + scale * raw_activation, bounds_lo, bounds_hi)",
            "sampling": "none",
        },
        "clock": {"policy_hz": int(clock["policy_hz"]),
                  "physics_hz": int(clock["physics_hz"]),
                  "hold_ticks": int(clock["hold_ticks"]),
                  "zero_order_hold": True},
    }


def _validate_inference_freeze(manifest: dict, weights_bytes: bytes | None) -> list[str]:
    """The freeze-block validator (called only when the block is present)."""
    errs = []
    blk = manifest["inference_freeze"]
    for k in _REQUIRED_INFERENCE_FREEZE:
        if k not in blk:
            errs.append(f"inference_freeze missing: {k}")
    if errs:
        return errs
    if blk["deployment_inference_version"] != DEPLOYMENT_INFERENCE_VERSION:
        errs.append(f"inference_freeze.deployment_inference_version != "
                    f"{DEPLOYMENT_INFERENCE_VERSION}")
    if blk["deterministic_action_selection"] is not True:
        errs.append("inference_freeze.deterministic_action_selection must be true "
                    "(the deployment freeze exists to pin determinism)")
    prec = blk["precision"]
    if not isinstance(prec, dict) or prec.get("storage") != _PRECISION_STORAGE:
        errs.append(f"inference_freeze.precision.storage must be {_PRECISION_STORAGE}")
    g = blk["exported_graph"]
    if not isinstance(g, dict) or not g.get("graph_pinned"):
        errs.append("inference_freeze.exported_graph.graph_pinned must be true")
    if isinstance(g, dict):
        sha = g.get("graph_sha256")
        if not isinstance(sha, str) or len(sha) != 64:
            errs.append("inference_freeze.exported_graph.graph_sha256 must be a "
                        "sha256 hex digest")
        elif weights_bytes is not None and \
                hashlib.sha256(weights_bytes).hexdigest() != sha:
            errs.append("inference_freeze.exported_graph.graph_sha256 does not "
                        "match the weights bytes")
    nc = blk["normalization_constants"]
    norm = manifest["normalization"]
    if isinstance(nc, dict):
        want = hashlib.sha256(json.dumps(
            {"mean": [float(v) for v in norm.get("mean", [])],
             "std": [float(v) for v in norm.get("std", [])],
             "clip": float(nc.get("clip", norm.get("clip", 8.0)))},
            sort_keys=True).encode("utf-8")).hexdigest()
        if nc.get("digest_sha256") != want:
            errs.append("inference_freeze.normalization_constants.digest_sha256 "
                        "does not match manifest.normalization")
    clk = blk.get("clock", {})
    act_clk = manifest["action"].get("clock", {})
    for k in ("policy_hz", "physics_hz", "hold_ticks"):
        if k in clk and act_clk.get(k) is not None and clk[k] != act_clk[k]:
            errs.append(f"inference_freeze.clock.{k} != action.clock.{k}")
    return errs


def canonical_json(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def manifest_hash(manifest: dict) -> str:
    """sha256 over canonical JSON with manifest_hash itself excluded."""
    m = copy.deepcopy(manifest)
    m.pop("manifest_hash", None)
    return hashlib.sha256(canonical_json(m)).hexdigest()


def validate_manifest(manifest: dict, weights_bytes: bytes | None = None) -> list[str]:
    """Return a list of violations (empty == valid)."""
    errs = []
    for k in _REQUIRED_TOP:
        if k not in manifest:
            errs.append(f"missing top-level key: {k}")
    if errs:
        return errs
    if manifest["manifest_version"] != MANIFEST_VERSION:
        errs.append(f"manifest_version != {MANIFEST_VERSION}")
    if manifest["kind"] != "typeb_policy_manifest":
        errs.append("kind != typeb_policy_manifest")
    for f in ("F-CPU-POLICY-BYTES", "F-INFERENCE-BUDGET"):
        if f not in manifest["named_falsifiers"]:
            errs.append(f"named_falsifiers must include {f}")

    pol = manifest["policy"]
    for k in _REQUIRED_POLICY:
        if k not in pol:
            errs.append(f"policy missing: {k}")
    obs_dim = manifest["observation"].get("dim")
    arch = pol.get("architecture", [])
    if not (isinstance(arch, list) and len(arch) >= 2 and arch[0] == obs_dim):
        errs.append("policy.architecture[0] must equal observation.dim")
    if manifest["action"].get("dim") != arch[-1]:
        errs.append("action.dim must equal policy.architecture[-1]")

    # parameter / MAC accounting must close
    pc = sum(arch[i] * arch[i + 1] + arch[i + 1] for i in range(len(arch) - 1))
    mc = sum(arch[i] * arch[i + 1] for i in range(len(arch) - 1))
    if pol.get("param_count") != pc:
        errs.append(f"policy.param_count {pol.get('param_count')} != derived {pc}")
    if pol.get("mac_count") != mc:
        errs.append(f"policy.mac_count {pol.get('mac_count')} != derived {mc}")

    obs = manifest["observation"]
    order = obs.get("order", [])
    if len(order) != obs_dim:
        errs.append("observation.order length != observation.dim")
    if len(set(order)) != len(order):
        errs.append("observation.order has duplicate field names")
    per_field = obs.get("per_field", {})
    for name in order:
        pf = per_field.get(name)
        if pf is None:
            errs.append(f"per_field missing for {name}")
        elif pf.get("privileged") is not False:
            errs.append(f"privileged field {name} forbidden in deployed observation")
    if obs.get("privileged_forbidden") is not True:
        errs.append("observation.privileged_forbidden must be true")

    norm = manifest["normalization"]
    if set(norm.get("mean", [])) and len(norm["mean"]) != obs_dim:
        errs.append("normalization.mean length != observation.dim")
    if len(norm.get("std", [])) != obs_dim:
        errs.append("normalization.std length != observation.dim")

    act = manifest["action"]
    clk = act.get("clock", {})
    if clk.get("policy_hz") * clk.get("hold_ticks") != clk.get("physics_hz"):
        errs.append("clock: policy_hz * hold_ticks must equal physics_hz")
    for k in ("bounds_lo", "bounds_hi", "scale", "center"):
        if len(act.get(k, [])) != act.get("dim"):
            errs.append(f"action.{k} length != action.dim")

    if weights_bytes is not None:
        got = hashlib.sha256(weights_bytes).hexdigest()
        if got != pol["weights_sha256"]:
            errs.append(f"weights sha256 mismatch: manifest {pol['weights_sha256']} vs file {got}")

    # THE DEPLOYMENT-INFERENCE FREEZE (additive, optional): validated ONLY when
    # the block is present; manifests without it behave exactly as before.
    if "inference_freeze" in manifest:
        errs += _validate_inference_freeze(manifest, weights_bytes)
    return errs


def load_manifest(path: str, weights_path: str | None = None) -> dict:
    """Validated loader. Raises ValueError on any violation. Fills manifest_hash."""
    with open(path, "rb") as f:
        manifest = json.loads(f.read().decode("utf-8"))
    wbytes = None
    if weights_path is not None:
        with open(weights_path, "rb") as f:
            wbytes = f.read()
    errs = validate_manifest(manifest, wbytes)
    if errs:
        raise ValueError("invalid manifest: " + "; ".join(errs))
    manifest["manifest_hash"] = manifest_hash(manifest)
    return manifest


def build_env() -> dict:
    import platform
    return {
        "python": sys.version.split()[0],
        "numpy": __import__("numpy").__version__,
        "os": platform.platform(),
        "machine": platform.machine(),
    }
