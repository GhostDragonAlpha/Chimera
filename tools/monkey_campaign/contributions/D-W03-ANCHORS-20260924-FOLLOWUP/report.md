# D-W03-ANCHORS-20260924-FOLLOWUP — report

- Task: `D-W03-ANCHORS-20260924-FOLLOWUP` (planning id W03)
- Kind: `bounded_implementation`; depends on base diagnostic `D-W03-ANCHORS-20260924`
- Date: 2026-09-25
- Objective: Implement the versioned walking-anchor certificate verifier.
- Owned files: `implementation.py`, `test_implementation.py`, `proposed.patch`,
  `report.md`, `PREREGISTRATION.md`. Required artifact: `report.md`.
- pr_destination: `tools/monkey_campaign/contributions/D-W03-ANCHORS-20260924-FOLLOWUP/`

## Summary

Implemented a deterministic, versioned walking-anchor certificate verifier in
`implementation.py` (pure Python 3 standard library; no third-party dependencies). A
walking anchor is a certificate whose binding must hold across an ordered chain of
hops — source material -> produced binary -> qualifying device. `verify_certificate`
verifies each hop against the identity the certificate declares and returns a single
`AnchorVerdict` with status `VERIFIED` only when every hop in the certificate's own
evaluation scope holds, otherwise `REJECTED`.

The verifier never infers acceptance: a missing or revoked device is reported as a
failure (`DEVICE_NOT_QUALIFIED` / `DEVICE_REVOKED`) rather than silently treated as
qualified; an unsupported schema version is rejected rather than guessed at; and the
same inputs always produce the same verdict and the same canonical byte digest of that
verdict. The preregistered statement, predictions and falsifiers are in
`PREREGISTRATION.md`; every prediction there was executed on 2026-09-25 and is marked
CONFIRMED by the checks below.

## Source identities (exact)

| File | SHA-256 | Lines | Dependencies |
| --- | --- | --- | --- |
| `implementation.py` | `F21180BCC7D1167F8F5A9157481670D8A429F90161C86CFA177C1B090847DBB8` | 309 | stdlib only: `hashlib`, `json`, `dataclasses`, `typing` |
| `test_implementation.py` | `5A605ED36BEC82B73E71F89763F2017BA972147D3BCA3F08AC7BD8A3A99164DA` | 274 | stdlib only; imports from `implementation` |

Both files are self-contained in the attempt workspace. No production source, anchor
hash, or frozen threshold was read into or modified by this implementation.

## Findings

### Design of the verifier

Three hops, each an identity comparison with no tuned constants:

- **Hop 1 — source.** `sha256(source_bytes) == cert["source_sha256"]`.
- **Hop 2 — binary.** `sha256(binary_bytes) == cert["binary_sha256"]`.
- **Hop 3 — device.** The declaring device must be present in the trusted registry and
  not revoked. Revocation semantics:
  - v1, or v2 without an explicit horizon: any `revoked_at` record rejects
    (`DEVICE_REVOKED`).
  - v2 with a horizon `device_revoke_after`: valid only if the device was revoked
    *strictly after* the declared horizon (i.e. still qualified at verification time).

Schema versions are explicit and closed: `SUPPORTED_VERSIONS = {1, 2}`. v2 extends v1
with an ordered `binding_scope` (the evaluation order of hops) and reads the device
revocation horizon. Required fields per version are enforced; unknown binding hops raise
`INVALID_BINDING_SCOPE`.

**Determinism.** The verdict digest is `sha256(canonical_json().encode("utf-8"))`, where
`canonical_json()` emits sorted top-level keys, compact separators, and bindings sorted
by hop name. Output therefore does not depend on dict insertion order or wall-clock time.
The pinned expected digest for the all-holds v2 fixture is
`04d759cdf9d13be58ea23966c1bce7f7ea7116058b77a56db72c9509dc25069f`.

**Error vs binding failure.** Structural problems (non-mapping certificate, unsupported
version, missing field, malformed digest) raise `AnchorError` with a stable machine
`code`; binding failures are returned inside the verdict as per-hop `BindingResult`
entries so a caller sees exactly which hops held and which broke. The first broken hop
by scope order names the verdict `reason`.

### Boundaries (what this does not do)

- No digital signature, secret, or human identity is implied; a pinned expected digest
  plays the role of the externally pinned trust anchor (matching `integrity.verify_catalog`).
- The C++/host/device gap isolated by the base diagnostic is deliberately left open. This
  module reports missing device qualification as *missing* and does not substitute CPU
  evidence for a real device qualification.
- No physics recomputation, no threshold/tolerance constants are changed or tuned.
## Receipt of checks actually performed

Both runners were executed on the frozen module on 2026-09-25. Every preregistered
prediction is CONFIRMED; there are zero failures.

| # | Test | Input | Expected | Outcome |
|---| --- | --- | --- | --- |
| 1 | test_source_binary_device_all_hops_hold | v2 cert, matching bytes, trusted device | VERIFIED, hops [source,binary,device] | PASS |
| 2 | test_v1_default_scope_without_binding_scope | v1 cert, no scope | VERIFIED, version==1 | PASS |
| 3 | test_reconstructed_fixture_holds_with_matching_bytes | reconstructed fixture, trusted device | VERIFIED | PASS |
| 4 | test_devices_accepted_as_sequence_not_just_mapping | list of DeviceRecord | VERIFIED | PASS |
| 5 | test_supported_versions_are_one_and_two | `SUPPORTED_VERSIONS` | `{1,2}` | PASS |
| 6 | test_source_mismatch_rejected | tampered source_sha256 | REJECTED `source_binding_failed` | PASS |
| 7 | test_binary_mismatch_rejected | tampered binary_sha256 | REJECTED `binary_binding_failed` | PASS |
| 8 | test_unknown_device_rejected_missing_qualification_preserved | unknown device | REJECTED `unknown_or_untrusted` | PASS |
| 9 | test_revoked_device_rejected | revoked device | REJECTED contains `revoked` | PASS |
| 10 | test_v2_revocation_horizon_before_and_after | horizon before/after | REJECTED / VERIFIED | PASS |
| 11 | test_unsupported_version_raises | version==3 | raises `UNSUPPORTED_ANCHOR_VERSION` | PASS |
| 12 | test_missing_field_raises | v1 missing binary_sha256 | raises `MISSING_CERTIFICATE_FIELD` | PASS |
| 13 | test_invalid_digest_format_raises | non-hex digest | raises `INVALID_BINDING_DIGEST` | PASS |
| 14 | test_determinism_identical_verdicts | identical inputs | same canonical_json + digest | PASS |
| 15 | test_canonical_output_independent_of_key_order | reordered keys | same digest | PASS |
| 16 | test_canonical_json_keys_are_sorted | sorted output | keys + hops sorted | PASS |

**Runners.** `python test_implementation.py` -> `16 passed, 0 failed, 16 total`.
`pytest test_implementation.py -q` -> `16 passed in 0.01s`.

**Self-check (non-revoked device).** `python implementation.py` prints:
```
VERIFIED 04d759cdf9d13be58ea23966c1bce7f7ea7116058b77a56db72c9509dc25069f
```

**Representative REJECTED sample (revoked device, canonical_json):**
```json
{"algorithm":"sha256-chimera-walking-anchor-v1","bindings":[{"hop":"binary","ok":true,"reason":null},{"hop":"device","ok":false,"reason":"DEVICE_REVOKED: device 'device-beta' revoked at 2026-09-01T00:00:00Z"},{"hop":"source","ok":true,"reason":null}],"status":"REJECTED","version":2}
```

## Remaining gates

1. **Lead-reviewed merged PR.** Completion requires a lead-approved, merged PR to
   `astra/gait-capture` pinned to this card's criteria hash, containing the actual
   implementation/patch and relevant tests. This is a downstream lead/operator action;
   it was not performed by this worker.
2. **Real device qualification (host/device gap).** The base diagnostic isolated a
   remaining C++/host/device gap. This module preserves that gap as *missing*: no real
   device qualification was obtained, and CPU evidence is not substituted for it. The
   next implementation step should target the unverified host/device gate, not re-label
   this verifier's output as device proof.
3. **Runtime/visual gates.** Not exercised by a pure-Python verifier; preserved for later.

## GitHub submission status — BLOCKED (recorded honestly)

Submission could not be completed by this worker. The blocker was checked directly on
2026-09-25 and is **not** a network outage:

| Check | Result (measured 2026-09-25) |
| --- | --- |
| `gh` CLI installed | NOT INSTALLED — the blocker |
| DNS `github.com` / `api.github.com` | RESOLVES (140.82.112.3 / 140.82.114.5) |
| Outbound TCP `github.com:443` | CONNECTED |

So DNS and outbound connectivity to GitHub work; the absence of a `gh` CLI (and no API
token or authority to open a PR as this worker) is what prevents submission. No live pull
request was opened, and none is claimed here. The deliverables are written to the task's
`pr_destination` folder for lead review; opening and merging the PR to `astra/gait-capture`
is a downstream lead/operator action. If a `gh` CLI (or equivalent API credentials) becomes
available, the lead can open and merge the PR from these artifacts.

## Next implementation step

1. Hand off these hash-bound artifacts to lead review via
   `worker_start.py --request-pr` (handing off the artifacts and taking the next slot),
   then execute any next assigned work. Do not mark a planning task accepted.
2. Lead/operator: open a lead-reviewed PR to `astra/gait-capture` pinned to this card's
   criteria hash, if GitHub network/infra is available at that time.
3. Next implementation work should address the remaining host/device gate isolated by the
   base diagnostic — obtain real device qualification and close the C++/host/device gap —
   without changing the anchors or thresholds already frozen here.

