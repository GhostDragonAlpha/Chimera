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

_REQUIRED_TOP = [
    "manifest_version", "kind", "claim", "named_falsifiers", "cpu_reference",
    "horizon_and_ticks", "scene_and_receipts", "body", "reflex_set", "physics_version",
    "observation", "normalization", "action", "policy", "inference", "reset",
    "evaluation", "receipts",
]

_REQUIRED_POLICY = ["architecture", "activation", "weights_format", "weights_sha256",
                    "param_count", "mac_count", "seed", "training_backend"]


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
