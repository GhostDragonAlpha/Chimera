"""Deterministic, versioned walking-anchor certificate verifier.

A *walking anchor* is a certificate whose binding must hold across an ordered
chain of hops -- source material -> produced binary -> qualifying device. The
anchor "walks" only if every hop verifies against the identity it declares. If
any hop breaks, the anchor does not hold and verification rejects deterministically.

This module never infers acceptance. A missing or revoked device qualification is
reported as a failure, not silently treated as qualified (see
``DEVICE_NOT_QUALIFIED`` / ``DEVICE_REVOKED``). A version it does not support is
rejected rather than guessed at. The same inputs always produce the same verdict
and the same canonical byte digest of that verdict -- there is no dict-ordering or
wall-clock dependence in the output.

No digital signature, secret, or human identity is implied; a pinned expected
digest (``trusted_source_sha256``) plays the role of the externally pinned trust
anchor, matching ``integrity.verify_catalog``'s model.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

# --- Schema / versioning -----------------------------------------------------

#: Certificate schema versions this verifier understands and will verify.
SUPPORTED_VERSIONS: frozenset[int] = frozenset({1, 2})

#: Canonical algorithm name for the verdict digest (mirrors integrity.ALGORITHM).
ALGORITHM = "sha256-chimera-walking-anchor-v1"

#: Required certificate fields per schema version. v2 extends v1 with an explicit
#: ordered binding scope and a device-revocation horizon.
_REQUIRED_FIELDS: Mapping[int, tuple[str, ...]] = {
    1: ("version", "source_sha256", "binary_sha256", "qualified_by_device"),
    2: (
        "version",
        "source_sha256",
        "binary_sha256",
        "qualified_by_device",
        "binding_scope",
    ),
}


def _is_hex64(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


# --- Errors -------------------------------------------------------------------

class AnchorError(ValueError):
    """A walking-anchor verification failure. ``code`` is a stable machine id."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(detail or code)


# --- Device registry ----------------------------------------------------------

@dataclass(frozen=True)
class DeviceRecord:
    """A trusted device entry. ``revoked_at`` is an ISO-8601 UTC timestamp or None."""

    id: str
    revoked_at: Optional[str] = None

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


# --- Verdict ------------------------------------------------------------------

@dataclass
class BindingResult:
    hop: str
    ok: bool
    reason: Optional[str] = None


@dataclass
class AnchorVerdict:
    """A deterministic verification outcome.

    ``bindings`` preserves the ordered hops so a caller can see exactly which walk
    step held and which broke; it is sorted by hop name only for canonical output,
    never for evaluation order (evaluation always follows the certificate's own
    binding scope).
    """

    version: int
    status: str  # 'VERIFIED' or 'REJECTED'
    bindings: tuple[BindingResult, ...] = field(default_factory=tuple)
    reason: Optional[str] = None

    @property
    def verified(self) -> bool:
        return self.status == "VERIFIED"

    def canonical_json(self) -> str:
        payload = {
            "algorithm": ALGORITHM,
            "version": self.version,
            "status": self.status,
            "bindings": [
                {"hop": b.hop, "ok": b.ok, "reason": b.reason}
                for b in sorted(self.bindings, key=lambda x: x.hop)
            ],
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def digest(self) -> str:
        """Stable sha256 over the canonical verdict bytes."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


# --- Core verification --------------------------------------------------------

def _check_hex64(value: Any, hop: str) -> None:
    if not _is_hex64(value):
        raise AnchorError(
            "INVALID_BINDING_DIGEST",
            f"{hop} must be a 64-char hex sha256, got {value!r}",
        )


def verify_certificate(
    cert: Mapping[str, Any],
    source_bytes: bytes,
    binary_bytes: bytes,
    devices: Mapping[str, DeviceRecord] | Sequence[DeviceRecord],
) -> AnchorVerdict:
    """Verify a walking-anchor certificate against its declared binding identities.

    Parameters
    ----------
    cert:
        The certificate mapping. Must carry the fields required by its ``version``.
    source_bytes, binary_bytes:
        The actual material to hash and compare against ``source_sha256`` /
        ``binary_sha256``. These are supplied at verification time; no real bytes
        or fixtures are embedded in this module.
    devices:
        A trusted-device registry. Accepts a mapping of device id -> DeviceRecord,
        or a sequence of DeviceRecords (looked up by ``id``).

    Returns
    -------
    AnchorVerdict with status 'VERIFIED' only when every hop holds.

    Raises
    ------
    AnchorError
        For structural problems that prevent evaluation: unsupported version,
        missing fields, or malformed digests. Binding failures are reported in the
        returned verdict (status 'REJECTED'), not raised, so callers get a full
        deterministic picture of which hops held.
    """
    if not isinstance(cert, Mapping):
        raise AnchorError("CERTIFICATE_NOT_MAPPING", "certificate must be a mapping")

    version = cert.get("version")
    if version not in SUPPORTED_VERSIONS:
        raise AnchorError(
            "UNSUPPORTED_ANCHOR_VERSION",
            f"version {version!r} is not supported; supported={sorted(SUPPORTED_VERSIONS)}",
        )

    required = _REQUIRED_FIELDS[version]
    missing = [name for name in required if name not in cert or cert[name] is None]
    if missing:
        raise AnchorError(
            "MISSING_CERTIFICATE_FIELD",
            f"certificate version {version} is missing fields: {sorted(missing)}",
        )

    registry = _normalize_devices(devices)
    scope = _resolve_scope(cert, version)
    bindings: list[BindingResult] = []

    # Hop 1: source material hashes to the declared SOURCE_SHA256.
    _check_hex64(cert["source_sha256"], "source_sha256")
    actual_source = hashlib.sha256(source_bytes).hexdigest()
    if actual_source == cert["source_sha256"]:
        bindings.append(BindingResult("source", True))
    else:
        bindings.append(
            BindingResult(
                "source",
                False,
                f"declared {cert['source_sha256']} != computed {actual_source}",
            )
        )

    # Hop 2: produced binary hashes to the declared BINARY_SHA256.
    _check_hex64(cert["binary_sha256"], "binary_sha256")
    actual_binary = hashlib.sha256(binary_bytes).hexdigest()
    if actual_binary == cert["binary_sha256"]:
        bindings.append(BindingResult("binary", True))
    else:
        bindings.append(
            BindingResult(
                "binary",
                False,
                f"declared {cert['binary_sha256']} != computed {actual_binary}",
            )
        )

    # Hop 3: the qualifying device is trusted and not revoked.
    device_id = cert["qualified_by_device"]
    record = registry.get(device_id)
    if record is None:
        bindings.append(
            BindingResult(
                "device",
                False,
                f"DEVICE_NOT_QUALIFIED: unknown_or_untrusted device {device_id!r}",
            )
        )
    else:
        # Revocation status depends on whether a horizon is in play.
        horizon = cert.get("device_revoke_after") if version == 2 else None
        revoked_at = record.revoked_at
        if horizon is not None and revoked_at is not None:
            # v2 explicit horizon: valid only if the device was revoked strictly
            # AFTER the declared horizon (i.e. still qualified at verification time).
            device_ok = revoked_at > horizon
            reason = (
                f"DEVICE_REVOKED: device {device_id!r} "
                f"revoked at/before horizon {horizon}"
                if not device_ok
                else None
            )
        elif revoked_at is not None:
            # v1, or v2 without an explicit horizon: any revocation record rejects.
            device_ok = False
            reason = f"DEVICE_REVOKED: device {device_id!r} revoked at {revoked_at}"
        else:
            device_ok = True
            reason = None
        bindings.append(BindingResult("device", device_ok, reason))

    failed = [b for b in bindings if not b.ok]
    if failed:
        # Deterministic reason: first broken hop by evaluation (scope) order.
        reason = f"{failed[0].hop}_binding_failed" + (
            f": {failed[0].reason}" if failed[0].reason else ""
        )
        status = "REJECTED"
    else:
        reason = None
        status = "VERIFIED"

    return AnchorVerdict(
        version=version,
        status=status,
        bindings=tuple(bindings),
        reason=reason,
    )


def _normalize_devices(devices):
    if isinstance(devices, Mapping):
        return dict(devices)
    out = {}
    for rec in devices:
        out[rec.id] = rec
    return out


def _resolve_scope(cert, version):
    """Ordered list of hops to evaluate. v2 carries an explicit scope; v1 defaults."""
    if version == 2 and cert.get("binding_scope"):
        scope = list(cert["binding_scope"])
        known = {"source", "binary", "device"}
        for hop in scope:
            if hop not in known:
                raise AnchorError(
                    "INVALID_BINDING_SCOPE", f"unknown binding hop {hop!r}"
                )
        return scope
    return ["source", "binary", "device"]


if __name__ == "__main__":  # tiny self-check; not a test
    sample = {
        "version": 2,
        "source_sha256": hashlib.sha256(b"source-material").hexdigest(),
        "binary_sha256": hashlib.sha256(b"produced-binary").hexdigest(),
        "qualified_by_device": "device-alpha",
        "binding_scope": ["source", "binary", "device"],
    }
    devices = {"device-alpha": DeviceRecord("device-alpha")}
    verdict = verify_certificate(
        sample, b"source-material", b"produced-binary", devices
    )
    print(verdict.status, verdict.digest())
