# PUBLISHER_MANIFEST_R4 - G01-R4 deliverables for Big Pickle

Generated 2026-09-07T04:23:07Z by the G01 worker. Big Pickle is the SINGLE publisher; workers do not commit,
push, or publish. R4 supersedes R3 implementation for publication while
retaining R3 history (snapshot at docs/evidence/g01/r3_snapshot/, 11 files
+ this manifest; the snapshot was completed with the two files its first
cp list omitted -- both hash-verified identical to their R3-era values,
which is itself the untouched proof below).

## Repository-relative publication paths (unpacked owned-file list)

Copy each file to the SAME repo-relative path under
docs/evidence/g01/ on astra/gait-capture (i.e. docs/evidence/g01/<path>),
preserving subdirectories. The agent_logs/ files are gitignored at their
source and MUST be copied (not referenced) to the destination; hash-verify
every copied blob against this manifest and account for any line-ending
filter (compare `git hash-object` of the working file with the staged blob).

## Base commit

`e0ea5a5635ef4bac2d1a2b46a604c04d68e9c8d7` (packet base). No commits,
branches, or pushes were made by this worker during G01-R4.

## Environment (measured live)

- Python 3.14.3
- numpy 2.2.6
- float64 eps 2.220446049250313e-16

## Exact commands (cwd E:/Chimera_G01/tools)

```bash
python overdamped_descent_checks.py    # 13/13 PASS
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
| `tools/overdamped_descent.py` | `4e17aa3fd812fdec5f2202385735f01caaf070700532180b121769a5ace062d8` |
| `tools/overdamped_descent_checks.py` | `04bb18b97fc096f1bf0cd0ff142f798dc0e0af1b806227829fd9d1eeaf60eb1e` |
| `tools/evidence_output.py` | `ec2ce37a34b4b13d00553b3af093bbe927c2b96a0dfbda9719be32e258f007ed` |
| `docs/FOUNDATION_G01_REPORT.md` | `bb07e19bb2b51f6d244a6c134fd343507cdc950603f710a42b99c928f51f95a0` |
| `docs/FOUNDATION_G01_GPU_HANDOFF.md` | `a09a70c67d7a8f4e8c0700444af733511b7b6416ae07862a8924fc3200d57c08` |
| `docs/evidence/g01/r3_snapshot/SHA256SUMS.txt` | `8d107be1daab8db1004800e30bcf8d31060343427079572b0cf715eba7f0f39c` |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R3.md` | `d837ff0677ef1a436e19153e886264473ebd05eabe4d9930cf94b196518ae448` |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R4.md` | `e25be051d0edcb8e6719bec65e2c276be536c4bdd8a0ec149327a945fd02ef07` |
| `agent_logs/glm_foundation_g01/PUBLISHER_MANIFEST_R3.md` | `a1203e8d5cc2c028a662ff667caa2bc8efaf0c96f78b7df1c43484fa6cdf53dc` |
| `agent_logs/glm_foundation_g01/overdamped_descent_checks_results_20260907T041916.988123Z.json` | `02bb84d9a752c03dc27f2b8f2dcf8daee16fba1b69d8cb5ab2da7209a55f64a8` |
| `agent_logs/glm_foundation_g01/surface_energy_checks_results_20260907T041927.107608Z.json` | `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28` |
| `agent_logs/glm_foundation_g01/material_contract_checks_results_20260907T041927.354618Z.json` | `2f4409a677555be5e896251921f962974459f3a040fe074566af71bbafcc3799` |

## Untouched-file proof (vs the completed R3 snapshot baseline)

- `tools/surface_energy_reference.py`: **MATCH (untouched by R4)** (snapshot ca0a4500a11c19ee...)
- `tools/material_contract.py`: **MATCH (untouched by R4)** (snapshot 5704c2b858de3347...)
- `tools/evidence_output.py`: **MATCH (untouched by R4)** (snapshot ec2ce37a34b4b13d...)

Changed-in-R4 (expected): overdamped_descent.py (units rewrite),
overdamped_descent_checks.py (6 new R4 checks + dated vocabulary notes),
the two docs, and the new R4 records. surface_energy_checks.py and
material_contract_checks.py were NOT modified in R4 (their hashes are
unchanged from R3's manifest: 692cbd534a3d2b7f..., da86a57acad28ace...).

## Historical evidence preservation

- Original G01 results file after ALL R4 runs: `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28`
  (matches the original G01 manifest: cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28).