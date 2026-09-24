# Tool home proposal — permanent home for the promoted consumption validator

## Proposal

Install the promoted validator as **the proposed home: tools/ + `rigid_body_mass_consumption_validator.py` (created at promotion)**
(single flat module, beside its four dependencies, following the existing
`tools/` conventions: snake_case module name = CLI entry point, module docstring
carrying scope + CLI + exit contract, `main(argv)` returning the exit class,
`raise SystemExit(main())` under `__main__`).

The file to install is the W6 promotion candidate:
`material_volume_campaign/impl/W6_validator/rigid_body_mass_consumption_validator.py`
(sha256 recorded in `receipts/final_hashes.txt`). Nothing else changes: the four
pinned dependencies already live in `tools/` (see `DEPENDENCY_MANIFEST.md`), so
the tool's `_tools_dir()` resolution (`Path(__file__).resolve().parents[1] / "tools"`
once installed at repo-root depth `tools/`) and its `sys.dont_write_bytecode`
guard work unchanged.

Conventions check against the existing `tools/` inventory (2026-09-24):
`tools/` already hosts the sibling single-file CLIs of this contract family —
`material_volume_body_export.py`, `material_volume_body_export_reader.py`,
`material_volume_admission.py` — each a flat module with a docstring header and
an argparse CLI. The proposed name follows the same
`material_volume_<subject>.py` family shape: it is the consumption-side
counterpart of `material_volume_body_export_reader.py`.

## Why promotion (operator items 2+4+6, Astra decisions)

- M10 contract spots: "Reconcile with already-decided v1.0 D1-D5; they are not
  pending again. Keep static-only use, partial-assembly rejection,
  source-effective exclusion and flat v1 frames. Separate read-only verification
  aggregation is allowed under CON-16 with explicit frames and disjoint
  ownership. It does not authorize collapsed export bodies, inferred joints, or
  runtime regrouping." — reconciled (see `../PREREGISTRATION.md`, frozen table;
  all five spots applied; D1/D4/D5 NO-CHANGE).
- Promotions: "Authorize isolated promotion preparation for the diagnostic and
  validator into their permanent tool home, including exact dependency pinning,
  current-contract reconciliation and review." — this directory is that isolated
  preparation; `agents/M10_validator/` remains the untouched campaign artifact.
- M06-H04 exit classes 0/2/1 — implemented (`docs/USAGE.md`).
- MV-O1 hash-scope documentation + separate full-report identity — implemented.
- MV-B3-1 raw-report-only consumption, summary refused by name — implemented.

## Installation steps (for the operator; NOT executed by W6 — `tools/` is
## read-only during the campaign)

1. Re-verify dependency OIDs per `DEPENDENCY_MANIFEST.md` § Promotion-time
   re-verification.
2. Copy `impl/W6_validator/rigid_body_mass_consumption_validator.py` to
   the proposed home: tools/ + `rigid_body_mass_consumption_validator.py` (created at promotion) (blob OID of the installed
   file to be recorded in the promotion receipt; §6 Git blob identity).
3. Copy `docs/USAGE.md` to `docs/` (or link it) as the tool's manual.
4. Run the frozen suite against the installed location
   (`_tools_dir()` resolves relative to the module, so the suite needs its
   `AGENT_DIR` repointed — the suite is part of the promoted artifact).
5. Record the promotion receipt (installed blob OID, suite verdict, `--version`
   output) in the campaign ledger.

## Explicitly NOT authorized by this promotion

- No runtime wiring (D1: runtime binding requires the separate Astra-approved
  qualification gate); the tool never imports physics, never mutates state,
  never assembles.
- No v2 lineage schema (D4: deferred), no source-effective transport (D5: no
  fallback path), no subset-binding exception (D2: none yet).
