# PUBLISHER_MANIFEST_R3 - G01-R3 deliverables for Big Pickle

Generated 2026-09-07T03:46:37Z by the G01 worker. Big Pickle is the SINGLE publisher (handoff change: workers do
not commit, push, or publish). Suggested destination per ASTRA's standing
decision: docs/evidence/g01/ on astra/gait-capture. NOTE: agent_logs/ is
gitignored - the raw results files must be COPIED to the destination;
hash-verify the copies against this manifest.

## Base commit

`e0ea5a5635ef4bac2d1a2b46a604c04d68e9c8d7` (packet base, verified = HEAD of
the isolated copy at R3 start). No commits, branches, or pushes were made
by this worker during G01-R3.

## Environment (measured live from the executing interpreter)

- Python 3.14.3
- numpy 2.2.6
- float64 eps 2.220446049250313e-16

## Exact commands (cwd E:/Chimera_G01/tools)

```bash
python overdamped_descent_checks.py    # 7/7 PASS
python surface_energy_checks.py        # 8/8 PASS
python material_contract_checks.py     # 16/16 PASS
```

## Files and SHA-256

| Repo-relative path | SHA-256 |
|---|---|
| `tools/surface_energy_reference.py` | `ca0a4500a11c19eedd50e0fafb1cf6c34b6df6d03082427dbe8f8588a31ab844` |
| `tools/surface_energy_checks.py` | `692cbd534a3d2b7fdb28977773708d4bb2d3c8455350fb63bea95f7aba203acb` |
| `tools/material_contract.py` | `5704c2b858de33479b11962980808bfac270a0dda61285521cc50deec992efb1` |
| `tools/material_contract_checks.py` | `da86a57acad28ace8a30d1c987e84e5da46091083f1b6d884321dea25c1c7fe3` |
| `tools/overdamped_descent.py` | `19a5f186cf5de64be51c8d8ee1e472bd1e8c95a11323413001b9aa75c91285f5` |
| `tools/overdamped_descent_checks.py` | `09ac80666b12d461b2b114d40fd30af6b74f8eae12891ec9510ec23d8ee3df88` |
| `tools/evidence_output.py` | `ec2ce37a34b4b13d00553b3af093bbe927c2b96a0dfbda9719be32e258f007ed` |
| `docs/FOUNDATION_G01_REPORT.md` | `0a4f7fc38e9cec38938905b5476eaf5b5e94d5ed984acee4b831dd197a807594` |
| `docs/FOUNDATION_G01_GPU_HANDOFF.md` | `b1a72eab4d00df37699c37286cbf3a2998ad751b590377d6079197b76b43b401` |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R3.md` | `d837ff0677ef1a436e19153e886264473ebd05eabe4d9930cf94b196518ae448` |
| `agent_logs/glm_foundation_g01/overdamped_descent_checks_results_20260907T034058.619182Z.json` | `79640273457c5f37d3bf8483f8eefd1da81cb4f2cb93b0d6486ec4594a797949` |
| `agent_logs/glm_foundation_g01/surface_energy_checks_results_20260907T034115.679194Z.json` | `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28` |
| `agent_logs/glm_foundation_g01/material_contract_checks_results_20260907T034115.921497Z.json` | `2f4409a677555be5e896251921f962974459f3a040fe074566af71bbafcc3799` |

## Untouched-file proof (R3 claim, verified against the TRUE R2 baseline)

Baseline: MANIFEST_R2.md inside G01_R2_CORRECTED_PACKET.zip (the R2 packet
ASTRA received). An earlier draft of THIS manifest compared against the
ORIGINAL G01 hashes by mistake and reported MISMATCH; that draft was
discarded and never returned to any publisher.

- `tools/surface_energy_reference.py` vs R2 `ca0a4500a11c19ee...`: **MATCH (untouched by R3)**
- `tools/material_contract.py` vs R2 `5704c2b858de3347...`: **MATCH (untouched by R3)**

Changed-in-R3 (expected, evidence law + new modules only):
`surface_energy_checks.py`, `material_contract_checks.py` (runner I/O only
- no check, tolerance, or measured value changed), the two docs, plus the
three NEW files (overdamped_descent.py, overdamped_descent_checks.py,
evidence_output.py).

## Historical evidence preservation

- Original G01 results file after ALL R3 runs: `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28`
  (matches the original G01 manifest: cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28).