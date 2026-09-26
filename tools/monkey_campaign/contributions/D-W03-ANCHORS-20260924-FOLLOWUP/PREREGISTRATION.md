# D-W03-ANCHORS-20260924-FOLLOWUP — retrospective verification record (executed 2026-09-25)

Owner: bounded_implementation worker for planning id W03. Depends on the base
diagnostic `D-W03-ANCHORS-20260924` (which prepared the versioned anchor adoption
evidence and isolated the remaining C++/host/device gap). Task kind:
`bounded_implementation`; source_edit_allowed; production_edit_allowed=false;
gpu_allowed=false. Owned files: `implementation.py`, `test_implementation.py`,
`proposed.patch`, `report.md`, `PREREGISTRATION.md`. Required artifact: `report.md`.

STATUS — this is a **retrospective verification record**, not a preregistration. The
statement, predictions and falsifiers below were written after the module was implemented
and executed on 2026-09-25 against the frozen module; several predictions carry
post-execution specifics (the pinned self-check digest `04d759cdf9d13be58ea23966c1bce7f7ea7116058b77a56db72c9509dc25069f` and exact test names) that could only be recorded
once results existed. No earlier, dated preregistration exists for this task: the parent
diagnostic `D-W03-ANCHORS-20260924` is a separate bounded task and holds no
preregistration of these predictions. The statement and falsifiers are still stated as
theories that could be falsified; each prediction below is marked CONFIRMED by the checks
recorded in `report.md`. No anchor hash was changed, no GPU workload ran, and no
physics/threshold constant was tuned — every quantity below is derived from identity
comparison and a trusted-device registry lookup.

---

## STATEMENT

A *walking anchor* is a certificate whose binding must hold across an ordered chain
of hops — source material -> produced binary -> qualifying device. The anchor walks
only if every hop verifies against the identity it declares; if any hop breaks,
verification rejects deterministically. This module implements `verify_certificate`
in `implementation.py`:

- It understands schema versions 1 and 2 only (`SUPPORTED_VERSIONS = {1, 2}`) and
  rejects any other version rather than guessing.
- Hop 1 hashes the supplied source bytes and compares to `source_sha256`.
- Hop 2 hashes the supplied binary bytes and compares to `binary_sha256`.
- Hop 3 requires the declaring device to be present in the trusted registry and not
  revoked (v2 adds an explicit revocation horizon, `device_revoke_after`).
- A missing or revoked device is reported as a failure (`DEVICE_NOT_QUALIFIED` /
  `DEVICE_REVOKED`); it is never silently treated as qualified.
- The same inputs always produce the same verdict and the same canonical byte digest
  of that verdict — there is no dict-ordering or wall-clock dependence in the output.

No digital signature, secret, or human identity is implied; a pinned expected digest
(`trusted_source_sha256` at call sites) plays the role of the externally pinned trust
anchor, matching `integrity.verify_catalog`'s model.

## PREDICTION (named before results; each CONFIRMED in report.md)

Every test uses plain `assert`, so it runs under both `python test_implementation.py`
and `pytest`. The reconstructed fixture (`SOURCE_BYTES` / `BINARY_BYTES`) does not
exist on disk; it is built from real bytes whose sha256 equals the pinned digests.

1. **All-hops hold (v2).** `verify_certificate(v2_cert, SOURCE_BYTES, BINARY_BYTES, registry)` ->
   status `VERIFIED`, all three bindings ok, bindings in scope order
   `[source, binary, device]`. Digest of this verdict ==
   `04d759cdf9d13be58ea23966c1bce7f7ea7116058b77a56db72c9509dc25069f` (self-check).
   CONFIRMED — `test_source_binary_device_all_hops_hold`, standalone self-check.
2. **v1 default scope.** A v1 certificate with no `binding_scope` verifies and reports
   `version == 1`. CONFIRMED — `test_v1_default_scope_without_binding_scope`.
3. **Source tamper.** Declared `source_sha256` != computed -> `REJECTED`,
   `reason.startswith("source_binding_failed")`. CONFIRMED — `test_source_mismatch_rejected`.
4. **Binary tamper.** Declared `binary_sha256` != computed -> `REJECTED`,
   `reason.startswith("binary_binding_failed")`. CONFIRMED — `test_binary_mismatch_rejected`.
5. **Unknown device (missing qualification preserved).** `qualified_by_device` absent
   from registry -> device hop not ok, reason contains `unknown_or_untrusted`; never
   accepted as qualified. CONFIRMED — `test_unknown_device_rejected_missing_qualification_preserved`.
6. **Revoked device.** Device with a `revoked_at` record -> device hop not ok, reason
   contains `revoked`. CONFIRMED — `test_revoked_device_rejected`.
7. **v2 revocation horizon.** Revoked *at/before* the declared horizon -> REJECTED;
   revoked *strictly after* the horizon -> still qualified at verification time -> VERIFIED.
   CONFIRMED — `test_v2_revocation_horizon_before_and_after`.
8. **Unsupported version raises.** `version == 3` -> `AnchorError.code == "UNSUPPORTED_ANCHOR_VERSION"`.
   CONFIRMED — `test_unsupported_version_raises`.
9. **Missing field raises.** v1 cert without `binary_sha256` ->
   `AnchorError.code == "MISSING_CERTIFICATE_FIELD"` naming `binary_sha256`.
   CONFIRMED — `test_missing_field_raises`.
10. **Malformed digest raises.** Non-hex `source_sha256` ->
    `AnchorError.code == "INVALID_BINDING_DIGEST"`. CONFIRMED — `test_invalid_digest_format_raises`.
11. **Determinism.** Two identical verifications produce identical `canonical_json()`
    and `digest()`. CONFIRMED — `test_determinism_identical_verdicts`.
12. **Key-order independence.** Same data with keys inserted in different order -> same
    `digest()`. CONFIRMED — `test_canonical_output_independent_of_key_order`.
13. **Sorted canonical output.** `canonical_json()` top-level keys are sorted and the
    emitted bindings are hop-sorted regardless of evaluation order. CONFIRMED —
    `test_canonical_json_keys_are_sorted`.
14. **Registry accepts a sequence.** A list of `DeviceRecord` (not only a mapping) is
    accepted and verifies. CONFIRMED — `test_devices_accepted_as_sequence_not_just_mapping`.
15. **Supported versions are one and two.** `SUPPORTED_VERSIONS == frozenset({1, 2})`.
    CONFIRMED — `test_supported_versions_are_one_and_two`.
16. **Reconstructed fixture holds.** The structured certificate whose pinned digests
    match the reconstructed bytes verifies with a trusted device. CONFIRMED —
    `test_reconstructed_fixture_holds_with_matching_bytes`.

Recorded check: standalone runner `16 passed, 0 failed, 16 total`; `pytest`
`16 passed in 0.01s`. Both runners green on the frozen module.

## FALSIFIERS (any one fails the claim)

- A missing predecessor fact is fabricated (e.g. claiming a real device qualification
  or a real v1/v2 anchor hash that was never obtained).
- A fixture is labeled native acceptance when it is actually reconstructed from bytes.
- The patch changes unscoped physics/thresholds, or tunes any numerical constant to
  force a pass.
- A CPU result is labeled as new device qualification (the host/device gap stays open).
- Old anchors are changed; an unexplained out-of-band change appears in the module.
- The digest depends on dict ordering, wall-clock time, or input key order.
- A missing/revoked device is silently accepted instead of reported REJECTED.
- Empty directory and logs without verdicts fail for lack of evidence.

## DERIVATION (no tuned constants)

A hop holds iff its computed identity equals its declared identity:

```
source_ok   = sha256(source_bytes)   == cert["source_sha256"]
binary_ok   = sha256(binary_bytes)   == cert["binary_sha256"]
device_ok   = device_id in registry  AND revocation_status(device_id, version, cert) <= qualified
```

where for the device hop:

```
v1 (or v2 without horizon):  device_ok = revoked_at is None
v2 with horizon h:           device_ok = revoked_at is None OR revoked_at > h
```

The verdict status is `VERIFIED` iff every hop in the certificate's own evaluation
scope holds; otherwise `REJECTED` and `reason` names the first broken hop by scope
order. The digest is `sha256(canonical_json().encode("utf-8"))`, where
`canonical_json()` emits sorted keys and hop-sorted bindings with compact separators,
so it is invariant to insertion order. Structural problems (bad mapping, unsupported
version, missing field, malformed digest) raise `AnchorError`; binding failures are
returned in the verdict so a caller sees every hop that held and every hop that broke.

## TESTS / HOW VERIFIED

- `python test_implementation.py` (standalone runner, no pytest required): 16 passed.
- `pytest test_implementation.py -q`: 16 passed.
- `python implementation.py` self-check prints `VERIFIED <digest>` with the pinned
  digest unchanged.
- Representative REJECTED sample (revoked device) canonical_json recorded in report.md.

## SCOPE LIMITS

Own attempt workspace only. No GPU, training, process termination, live checkout
edits, model/mesh copying, or unapproved threshold changes. The C++/host/device gap
isolated by the base diagnostic is deliberately left open: this module reports missing
device qualification as missing and does not substitute CPU evidence for it.

## NEXT IMPLEMENTATION STEP

Hand off these hash-bound artifacts to lead review (`worker_start.py --request-pr`),
then take the next assigned card. The downstream lead/operator action — a lead-reviewed
merged PR to `astra/gait-capture` pinned to this card's criteria hash — is not performed
by this worker. Whether GitHub network/infra is available for that merge is checked at
handoff; if it is not, the blocker is recorded here rather than claimed as a live PR.

