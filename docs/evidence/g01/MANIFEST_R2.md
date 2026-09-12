# MANIFEST_R2 — G01-R2 corrected packet
Packed 2026-09-06 after the G01-R2 correction pass. Base of the work: e0ea5a5635ef4bac2d1a2b46a604c04d68e9c8d7; first packet published on branch g01-evidence (a530b514) BEFORE this pass — this packet is the post-correction state, delivered as a ZIP per the no-commit constraint.

## Results

```
cd /e/Chimera_G01/tools && python surface_energy_checks.py     -> 8/8 PASS
cd /e/Chimera_G01/tools && python material_contract_checks.py  -> 16/16 PASS (P8a..j + R2k..p)
```

## SHA-256 (all packed entries except this manifest itself)

| Repo-relative path | SHA-256 |
|---|---|
| `tools/surface_energy_reference.py` | `ca0a4500a11c19eedd50e0fafb1cf6c34b6df6d03082427dbe8f8588a31ab844` |
| `tools/surface_energy_checks.py` | `c8350804efdc8b02ba6ccce867c275f036e39e504db59619866e390897861ef8` |
| `tools/material_contract.py` | `5704c2b858de33479b11962980808bfac270a0dda61285521cc50deec992efb1` |
| `tools/material_contract_checks.py` | `9f901f7172bcb1c68b061e21191078c5c021e902d000df6ef8c37f49e6c80c3d` |
| `docs/FOUNDATION_G01_REPORT.md` | `e686154b5f535d2bb7c53bbd1f4f7a819122072f4993ac03bb961c593574eb92` |
| `docs/FOUNDATION_G01_GPU_HANDOFF.md` | `a7fbb321ebad8302d9551710e7e60ceb38314d4e33e207619f29486c207ca0b4` |
| `docs/evidence/g01/MANIFEST.md` | `cb9cd02e2f7189775d1f064b40e8b90fa4bca1443ecdb01db698189ab6833aac` |
| `agent_logs/glm_foundation_g01/RUN_HISTORY_R2.md` | `17b433465a2c402b2fc9b249ea6a95a552783e82df5c543b61168d17c519679d` |
| `agent_logs/glm_foundation_g01/surface_energy_checks_results_R2.json` | `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28` |
| `agent_logs/glm_foundation_g01/surface_energy_checks_R2_run.txt` | `1692521eff4c6f13acde26515bd6a3a359ac29facb247557c09cad2ebd548808` |
| `agent_logs/glm_foundation_g01/material_contract_checks_R2_run.txt` | `e27122bae71b6eb13e9c8d7b197585e489175489fa83f983c88f146038f15cd9` |

Interpreter: Python 3.14.3, NumPy 2.2.6 (unchanged). Verification class: numerical (CPU numpy) only; no window/DYAD/GPU claims. Original G01 evidence preserved byte-exact (asserted at pack time: RUN_HISTORY.md, surface_energy_checks_results.json, surface_energy_checks.py). The manifest itself carries no self-hash; its working-copy hash is verified against the archived copy at pack time.
