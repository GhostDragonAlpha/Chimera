# MANIFEST_R5 — G01-A1 hardening pass (BP-A1), 2026-09-07

Worker: Big Pickle (BP-A1). Base commit: `e3d53cf7` (held by `astra/gait-capture`
at the start of the pass; fetched and verified before publishing).
Environment measured live: Python 3.14.3, numpy 2.2.6, float64 eps
2.220446049250313e-16. Preregistration: `docs/FOUNDATION_G01_REPORT.md`
section 9-A1 (written before the A1 source edits). Results: 62/62 PASS
(material 32, surface 12, overdamped 18); all 37 pre-A1 verdicts identical.

## Changed / added this pass

| Repo-relative path | Status | SHA-256 |
|---|---|---|
| `tools/material_contract.py` | MODIFIED (A1-1..5: surface_energy/fracture_toughness types, finite/provenance/derivation gates, record boundary, orthotropic law, density_from_sg conditions) | `7765a23a462f1a9eb9433b924038b748a8424ab4759b540053bd1ccd898c2d6f` |
| `tools/material_contract_checks.py` | MODIFIED (+A1_1a..A1_5c, 16 checks; EXPECTED_CHECKS 32) | `c3a3c28f43a55c20422b970622e4d71ed8b0fdb28038ec6618a317baa9a5283d` |
| `tools/overdamped_descent.py` | MODIFIED (A1-6: mean-edge tolerance basis; A1-7: fractional-pin + optimizer-argument validation) | `61bdf79a1bdd71f8df67c691b1a810fd3a99df96228b774fc6eaa31775694a50` |
| `tools/overdamped_descent_checks.py` | MODIFIED (+A1_6a..A1_7c, `_mean_edge` helper; r4b/r4d tolerance basis amended; 18 checks) | `73fc1b7c85fcafe6c9bd2018c1a25e9482d75dff2a5ea71ca2e69674cb857c06` |
| `tools/surface_energy_reference.py` | MODIFIED (A1-8: NONFINITE_RESULT gates on evaluate_surface + metric path; A1-9: `_as_gamma` copies) | `73b0f7a56c794dd9b5bca8721dc5ba820ff02fe763dca376b54bfe34bfd40809` |
| `tools/surface_energy_checks.py` | MODIFIED (+A1_8a..A1_9, 12 checks) | `f0184ee191ea1e34b774b4944baf059bca6242af37a356969e3a3d19dfa94890` |
| `docs/FOUNDATION_G01_REPORT.md` | EXTENDED (section 9-A1 prereg before code; section 10 A1 RESULTS after) | `a99acffc37b979b4fb32cb9672b54a3865e42e1fb0c2661e6bbb9a328035b621` |
| `docs/evidence/g01/RUN_HISTORY_R5.md` | NEW | `31bd90ff17567857b8e8e3c4381643e7f39a4ba8b7d435c40313e9156f92ceea` |
| `docs/evidence/g01/MANIFEST_R5.md` | NEW (this file; packaging metadata, carries no hash of itself) | — |
| `docs/evidence/g01/PUBLISHER_MANIFEST_R5.md` | NEW (publication manifest; also packaging metadata, tables the hashes; carries no hash in this table) | — |

## Fresh run records (R5, unique stamped, mirrored into this directory)

| Repo-relative path | SHA-256 |
|---|---|
| `docs/evidence/g01/overdamped_descent_checks_results_20260907T201557.766911Z.json` | `4bfa2e8735d82c2498f9ef84ccf4ea9f46ecb592e8ba46bf8859860e34e83c71` |
| `docs/evidence/g01/surface_energy_checks_results_20260907T201559.721656Z.json` | `3c753046f368e581a7fdd7cd441caabddfa928d11b19c162d82752d66d2e0fe2` |
| `docs/evidence/g01/material_contract_checks_results_20260907T201559.989357Z.json` | `a3bd4e617828c7b48a997c13b03d46da5a52927a25358b9170ca7cafd81bf2e2` |

## Untouched (unchanged) this pass

- `tools/evidence_output.py` — `ec2ce37a34b4b13d00553b3af093bbe927c2b96a0dfbda9719be32e258f007ed`
  (identical to the R4 manifest value; the evidence law was not modified).
- `docs/FOUNDATION_G01_GPU_HANDOFF.md` — unchanged (no engine-side change;
  this pass is foundation-tools-only).

## Verification class

Numerical (CPU numpy) only. No engine, no GPU, no DYAD verification
exists or is claimed. Re-runs must use cwd `tools/` (the tests import
their subjects by module name).