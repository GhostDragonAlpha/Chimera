# PUBLISHER_MANIFEST_R5 — G01-A1 deliverables for Big Pickle

Generated 2026-09-07 by the BP-A1 worker (Big Pickle). Big Pickle is the
SINGLE publisher: this pass's evidence was verified then published by the
model itself from the isolated checkout
`C:\Users\allen\AppData\Local\Temp\opencode\chimera_pub` (NOT
`E:\PythonChimera`, which was read-only). Base commit held at start:
`e3d53cf7` on `astra/gait-capture`. Preregistration for every finding:
`docs/FOUNDATION_G01_REPORT.md` section 9-A1, written BEFORE the A1 source
edits (this is a Rule-0-compliant pass: each regression check names its
falsifier; `port_test` refuses a test with no falsifier).

## Environment (measured live)

- Python 3.14.3
- numpy 2.2.6
- float64 eps 2.220446049250313e-16

## Exact commands (cwd = tools/ at the published layout)

```bash
python material_contract_checks.py       # 32/32 PASS, exit 0
python surface_energy_checks.py          # 12/12 PASS, exit 0
python overdamped_descent_checks.py      # 18/18 PASS, exit 0
```

Run JSONs were written to `agent_logs/glm_foundation_g01/` (unique stamped,
gitignored at source) and mirrored bit-identical into `docs/evidence/g01/`.

## Files and SHA-256

| Repo-relative path | SHA-256 |
|---|---|
| `tools/material_contract.py` | `7765a23a462f1a9eb9433b924038b748a8424ab4759b540053bd1ccd898c2d6f` |
| `tools/material_contract_checks.py` | `c3a3c28f43a55c20422b970622e4d71ed8b0fdb28038ec6618a317baa9a5283d` |
| `tools/overdamped_descent.py` | `61bdf79a1bdd71f8df67c691b1a810fd3a99df96228b774fc6eaa31775694a50` |
| `tools/overdamped_descent_checks.py` | `73fc1b7c85fcafe6c9bd2018c1a25e9482d75dff2a5ea71ca2e69674cb857c06` |
| `tools/surface_energy_reference.py` | `73b0f7a56c794dd9b5bca8721dc5ba820ff02fe763dca376b54bfe34bfd40809` |
| `tools/surface_energy_checks.py` | `f0184ee191ea1e34b774b4944baf059bca6242af37a356969e3a3d19dfa94890` |
| `tools/evidence_output.py` | `ec2ce37a34b4b13d00553b3af093bbe927c2b96a0dfbda9719be32e258f007ed` (UNCHANGED this pass) |
| `docs/FOUNDATION_G01_REPORT.md` | `a99acffc37b979b4fb32cb9672b54a3865e42e1fb0c2661e6bbb9a328035b621` |
| `docs/evidence/g01/RUN_HISTORY_R5.md` | `31bd90ff17567857b8e8e3c4381643e7f39a4ba8b7d435c40313e9156f92ceea` |
| `docs/evidence/g01/overdamped_descent_checks_results_20260907T201557.766911Z.json` | `4bfa2e8735d82c2498f9ef84ccf4ea9f46ecb592e8ba46bf8859860e34e83c71` |
| `docs/evidence/g01/surface_energy_checks_results_20260907T201559.721656Z.json` | `3c753046f368e581a7fdd7cd441caabddfa928d11b19c162d82752d66d2e0fe2` |
| `docs/evidence/g01/material_contract_checks_results_20260907T201559.989357Z.json` | `a3bd4e617828c7b48a997c13b03d46da5a52927a25358b9170ca7cafd81bf2e2` |
| `docs/evidence/g01/PUBLISHER_MANIFEST_R5.md` | (this file; packaging metadata, carries no hash of itself) |

## Untouched-file proof (vs base e3d53cf7)

- `tools/evidence_output.py`: UNCHANGED (hash equals the R4 manifest value)
- `docs/FOUNDATION_G01_GPU_HANDOFF.md`: UNCHANGED (no engine-side change)
- All historical evidence under `docs/evidence/g01/` (R2..R4 manifests,
  run histories, r3_snapshot, R4-era results): UNCHANGED; the R5 run
  records are ADDITIVE.

## Verdict identity of the 37 prior checks

Field-wise comparison of each battery's newest run JSON against the
R4-era run JSONs (`docs/evidence/g01/*_results_20260907T04*.json`):
all 16 material + 8 surface + 13 overdamped pre-A1 check names are
verdict-identical (all PASS in both); the A1 checks are additive. No
pre-A1 tolerance was changed.

## Historical evidence preservation

The three R5 run JSONs were written to UNIQUE stamped paths (collision on
an existing path exits 2 without writing — the evidence law); historical
files were byte-identical after all runs. This manifest is appended by the
publisher; the worker made no premature commit.