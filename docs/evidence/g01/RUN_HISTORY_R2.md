# RUN_HISTORY_R2 — G01-R2 (correction pass), 2026-09-06

Scope: the six refusal gaps ASTRA's independent review exposed + three GPU
handoff physics corrections. Original G01 evidence UNCHANGED (verified by
hash at the end of this pass). No commits, branches, pushes; no engine
control; no GPU integration. Work confined to the isolated copy
`E:\Chimera_G01`.

## Order of work (ASTRA's terms: record before pivot)

1. Read all three touched files; named the ROOT CAUSE of each gap before
   editing:
   - E=-1 accepted: `n in ("E", "K_IC")` compared against `name.lower()` —
     `"e" != "E"`, a case bug inside a name-substring law.
   - density unit "m" accepted: sign was gated, unit family never was —
     no law tied a property's meaning to its unit family.
   - blank source/conditions: no hygiene gate existed at all.
   - convert("bogus","bogus") → 1: the `u == v` identity shortcut returned
     BEFORE the registry lookup.
   - NaN frame/matrix accepted: `dev > 1e-9` and `eig.min() <= 0` are both
     silently False for NaN — the NaN-comparison trap.
   - triangle_metric NaN: `_frame` divided by `area2` and `|e1|` before any
     validation; the det guard was also NaN-blind.
2. Registered predictions P-8k..P-8p + the R2 ledger in the report
   (section 9-R2) BEFORE any code change.
3. Implemented: property-type decision table (type → value gate + unit
   families), blank-provenance gate, convert order fix, NaN-safe
   validate_orthotropic, geometry-before-normalization in triangle_metric
   (floor = the reference's own DEGENERACY_FLOOR law — no new constant).
4. PRE-RUN REGRESSION CATCH: the first type table's modulus hint `g_`
   shadowed `GLR_EL` (a dimensionless ratio in the real white_oak record);
   the family gate would have refused it and broken the record build.
   Fixed before running anything: ratio names declared exactly
   (`et_el`, `er_el`, `glr_el`) ahead of the modulus hints.
5. Self-caught fixture error while writing R2p: the first "current
   collinear" fixture did not collapse anything (face area 3.0). Rewrote
   fixtures so each case genuinely collapses a distinct face or side.
6. Ran both batteries. First R2 run: 16/16 contract, 8/8 surface — all
   PASS, no tolerance touched, P8a..j and F1..F8 behavior unchanged.
7. COMPLIANCE CATCH: the surface battery overwrote
   `agent_logs/glm_foundation_g01/surface_energy_checks_results.json`
   (the preserved original). Restored it byte-exact from the evidence
   copy (sha256 cfe48cb1… verified both sides) and re-captured the R2 run
   under its own names: `surface_energy_checks_results_R2.json`,
   `surface_energy_checks_R2_run.txt`, `material_contract_checks_R2_run.txt`.
8. GPU handoff §6.0 written: no-rest-shape, planar-patch assumptions,
   declared quasi-static scheme + timestep gate; A2/2/3 rewritten to match.
9. Manifest clarified: the "zero commits/branches/pushes" line describes
   PACKAGING TIME of the first packet, not current publication history
   (the packet itself was later published on branch `g01-evidence` at
   ASTRA's direction).

## Exact commands and results

```
cd /e/Chimera_G01/tools && python surface_energy_checks.py     → 8/8 PASS
cd /e/Chimera_G01/tools && python material_contract_checks.py  → 16/16 PASS
```

Interpreter: Python 3.14.3, NumPy 2.2.6 (unchanged from the manifest).

## Verification class

Numerical (CPU numpy) only. No window/DYAD/GPU verification exists or is
claimed.

## Hashes at end of pass (G01-R2)

- tools/surface_energy_reference.py: MODIFIED (geometry-before-normalization)
- tools/material_contract.py: MODIFIED (type table + gates + convert order)
- tools/surface_energy_checks.py: UNCHANGED — c8350804efdc8b02ba6ccce867c275f036e39e504db59619866e390897861ef8 (matches the original manifest)
- tools/material_contract_checks.py: MODIFIED (six R2 regression checks appended)
- Original results JSON: UNCHANGED — cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28 (verified after the overwrite incident)
