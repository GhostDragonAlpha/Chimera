"""Tests for the deterministic, versioned walking-anchor verifier.

Runnable two ways:

    python test_implementation.py        # no pytest needed; prints a summary and
                                         # exits non-zero on any failure
    pytest test_implementation.py         # standard discovery of test_* functions

Every test uses plain ``assert`` so it works under either runner. The standalone
runner collects every ``test_*`` callable in the module, runs them, and reports
pass/fail counts.
"""
import hashlib
import json

from implementation import (
    AnchorError,
    DeviceRecord,
    SUPPORTED_VERSIONS,
    verify_certificate,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Real byte material so the digests are computed from actual content, not guessed.
SOURCE_BYTES = b"source-material-v1\x00-qualified-by-device-alpha"
BINARY_BYTES = b"produced-binary-artifact\x00sha256-anchor"

TRUSTED_DEVICE = "device-alpha"
REVOKED_DEVICE = "device-beta"


def _registry():
    return {
        TRUSTED_DEVICE: DeviceRecord(TRUSTED_DEVICE),
        REVOKED_DEVICE: DeviceRecord(REVOKED_DEVICE, revoked_at="2026-09-01T00:00:00Z"),
    }


def _v2_cert(**overrides):
    cert = {
        "version": 2,
        "source_sha256": _sha256(SOURCE_BYTES),
        "binary_sha256": _sha256(BINARY_BYTES),
        "qualified_by_device": TRUSTED_DEVICE,
        "binding_scope": ["source", "binary", "device"],
    }
    cert.update(overrides)
    return cert


# --- Happy paths --------------------------------------------------------------

def test_source_binary_device_all_hops_hold():
    verdict = verify_certificate(_v2_cert(), SOURCE_BYTES, BINARY_BYTES, _registry())
    assert verdict.verified
    assert verdict.status == "VERIFIED"
    assert [b.hop for b in verdict.bindings] == ["source", "binary", "device"]
    assert all(b.ok for b in verdict.bindings)


def test_v1_default_scope_without_binding_scope():
    cert = {
        "version": 1,
        "source_sha256": _sha256(SOURCE_BYTES),
        "binary_sha256": _sha256(BINARY_BYTES),
        "qualified_by_device": TRUSTED_DEVICE,
    }
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert verdict.verified
    assert verdict.version == 1


def test_reconstructed_fixture_holds_with_matching_bytes():
    """The structured certificate fixture from the task context (SOURCE_SHA256 /
    BINARY_SHA256 / QUALIFIED_BY_DEVICE) does not exist on disk; reconstruct it as a
    case. With bytes matching its pinned digests and a trusted device, it verifies."""
    cert = {
        "version": 2,
        "source_sha256": _sha256(SOURCE_BYTES),
        "binary_sha256": _sha256(BINARY_BYTES),
        "qualified_by_device": TRUSTED_DEVICE,
        "binding_scope": ["source", "binary", "device"],
    }
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert verdict.verified


def test_devices_accepted_as_sequence_not_just_mapping():
    devices = [DeviceRecord(TRUSTED_DEVICE)]
    cert = {
        "version": 2,
        "source_sha256": _sha256(SOURCE_BYTES),
        "binary_sha256": _sha256(BINARY_BYTES),
        "qualified_by_device": TRUSTED_DEVICE,
        "binding_scope": ["source", "binary", "device"],
    }
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, devices)
    assert verdict.verified


# --- Rejections (binding failures stay REJECTED, never silently accepted) -----

def test_source_mismatch_rejected():
    cert = _v2_cert(source_sha256=_sha256(b"tampered-source"))
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert not verdict.verified
    assert verdict.status == "REJECTED"
    assert verdict.reason.startswith("source_binding_failed")


def test_binary_mismatch_rejected():
    cert = _v2_cert(binary_sha256=_sha256(b"tampered-binary"))
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert not verdict.verified
    assert verdict.reason.startswith("binary_binding_failed")


def test_unknown_device_rejected_missing_qualification_preserved():
    """A device absent from the trusted registry must NOT be treated as qualified."""
    cert = _v2_cert(qualified_by_device="device-ghost")
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert not verdict.verified
    dev = next(b for b in verdict.bindings if b.hop == "device")
    assert not dev.ok
    assert "unknown_or_untrusted" in (dev.reason or "")


def test_revoked_device_rejected():
    cert = _v2_cert(qualified_by_device=REVOKED_DEVICE)
    verdict = verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert not verdict.verified
    dev = next(b for b in verdict.bindings if b.hop == "device")
    assert not dev.ok
    assert "revoked" in (dev.reason or "")


def test_v2_revocation_horizon_before_and_after():
    # Revoked before the horizon -> invalid even though a record exists.
    cert_before = _v2_cert(
        qualified_by_device=REVOKED_DEVICE, device_revoke_after="2026-12-31T00:00:00Z"
    )
    verdict_before = verify_certificate(
        cert_before, SOURCE_BYTES, BINARY_BYTES, _registry()
    )
    assert not verdict_before.verified

    # Revoked after the horizon -> still valid at verification time.
    cert_after = _v2_cert(
        qualified_by_device=REVOKED_DEVICE, device_revoke_after="2026-01-01T00:00:00Z"
    )
    # Move the revoke timestamp to after that horizon.
    _registry()[REVOKED_DEVICE].revoked_at  # frozen record; rebuild registry instead
    reg = {
        TRUSTED_DEVICE: DeviceRecord(TRUSTED_DEVICE),
        REVOKED_DEVICE: DeviceRecord(REVOKED_DEVICE, revoked_at="2026-06-01T00:00:00Z"),
    }
    verdict_after = verify_certificate(cert_after, SOURCE_BYTES, BINARY_BYTES, reg)
    assert verdict_after.verified


# --- Structural errors (raised, not returned as REJECTED) ---------------------

def test_unsupported_version_raises():
    cert = _v2_cert(version=3)
    try:
        verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    except AnchorError as exc:
        assert exc.code == "UNSUPPORTED_ANCHOR_VERSION"
    else:
        raise AssertionError("expected AnchorError for unsupported version")


def test_missing_field_raises():
    cert = {
        "version": 1,
        "source_sha256": _sha256(SOURCE_BYTES),
        # binary_sha256 intentionally missing
        "qualified_by_device": TRUSTED_DEVICE,
    }
    try:
        verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    except AnchorError as exc:
        assert exc.code == "MISSING_CERTIFICATE_FIELD"
        assert "binary_sha256" in str(exc)
    else:
        raise AssertionError("expected AnchorError for missing field")


def test_invalid_digest_format_raises():
    cert = _v2_cert(source_sha256="not-a-hex-digest")
    try:
        verify_certificate(cert, SOURCE_BYTES, BINARY_BYTES, _registry())
    except AnchorError as exc:
        assert exc.code == "INVALID_BINDING_DIGEST"
    else:
        raise AssertionError("expected AnchorError for malformed digest")


# --- Determinism --------------------------------------------------------------

def test_determinism_identical_verdicts():
    a = verify_certificate(_v2_cert(), SOURCE_BYTES, BINARY_BYTES, _registry())
    b = verify_certificate(_v2_cert(), SOURCE_BYTES, BINARY_BYTES, _registry())
    assert a.canonical_json() == b.canonical_json()
    assert a.digest() == b.digest()


def test_canonical_output_independent_of_key_order():
    cert_ordered = {
        "version": 2,
        "source_sha256": _sha256(SOURCE_BYTES),
        "binary_sha256": _sha256(BINARY_BYTES),
        "qualified_by_device": TRUSTED_DEVICE,
        "binding_scope": ["source", "binary", "device"],
    }
    # Same data, keys inserted in a different order.
    cert_reordered = {
        "binding_scope": ["source", "binary", "device"],
        "qualified_by_device": TRUSTED_DEVICE,
        "binary_sha256": _sha256(BINARY_BYTES),
        "source_sha256": _sha256(SOURCE_BYTES),
        "version": 2,
    }
    va = verify_certificate(cert_ordered, SOURCE_BYTES, BINARY_BYTES, _registry())
    vb = verify_certificate(cert_reordered, SOURCE_BYTES, BINARY_BYTES, _registry())
    assert va.digest() == vb.digest()


def test_canonical_json_keys_are_sorted():
    verdict = verify_certificate(_v2_cert(), SOURCE_BYTES, BINARY_BYTES, _registry())
    payload = json.loads(verdict.canonical_json())
    keys = list(payload.keys())
    assert keys == sorted(keys)
    # bindings are emitted in hop-sorted order regardless of evaluation order
    hops = [b["hop"] for b in payload["bindings"]]
    assert hops == sorted(hops)


def test_supported_versions_are_one_and_two():
    assert SUPPORTED_VERSIONS == frozenset({1, 2})


# --- Standalone runner (no pytest required) -----------------------------------

def run():
    """Run every test_* function; return the number of failures."""
    tests = sorted(
        (name, obj)
        for name, obj in globals().items()
        if name.startswith("test_") and callable(obj)
    )
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - report all failures at once
            failed += 1
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        else:
            passed += 1
            print(f"ok   {name}")
    print(f"\n{passed} passed, {failed} failed, {len(tests)} total")
    return failed


if __name__ == "__main__":
    import sys

    raise SystemExit(run())
