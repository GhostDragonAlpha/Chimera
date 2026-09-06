# MANIFEST — G01 evidence packet (ASTRA independent review)

Packed 2026-09-06 by the G01 worker (GLM 5.3 Flash, Buffy/Freebuff). Per
ASTRA instruction: originals preserved in place (`agent_logs/` untouched,
still gitignored — nothing force-added); `docs/evidence/g01/` holds the
review copies ASTRA selected as the publication destination. The ZIP at
`E:/Chimera_G01/G01_EVIDENCE_PACKET.zip` contains exactly the eight files
below at their repo-relative paths (plus this manifest).

## Base commit

`e0ea5a5635ef4bac2d1a2b46a604c04d68e9c8d7` — isolated checkout
`E:\Chimera_G01` (shared clone of Alan's repo; Alan's `E:\PythonChimera`
checkout untouched). HEAD verified = base SHA at packing time; zero
commits, branches, or pushes made from this packet.

## Files and SHA-256

Measured with `sha256sum` on the working copy immediately before zipping.
The manifest itself is packaging metadata and carries no hash of its own.

| Repo-relative path | SHA-256 |
|---|---|
| `tools/surface_energy_reference.py` | `b37dd09d461adb5244e82091f5dcf079dfeadb178d0163c6be2fac056d2ec827` |
| `tools/surface_energy_checks.py` | `c8350804efdc8b02ba6ccce867c275f036e39e504db59619866e390897861ef8` |
| `tools/material_contract.py` | `700c4846ffff2128f53596c5d6b06d7c97f7084de1acab617e97168573c1ace7` |
| `tools/material_contract_checks.py` | `68867a42833e23e91b2942a2181e3e932efd5055406cd3a4a202b95a627ac5d6` |
| `docs/FOUNDATION_G01_REPORT.md` | `d21f489f4731cc09c4c7685bd17c1f6b3dd5fff53b2e8ec829d042f736c55824` |
| `docs/FOUNDATION_G01_GPU_HANDOFF.md` | `b27f627c921749f7242af9af86cd67f1367882d41438a496d334da143d081415` |
| `docs/evidence/g01/RUN_HISTORY.md` | `28e5928faa60dffde8158d9c3515bf255c220e4a1432f7f8b593e8fc2f2c34ad` |
| `docs/evidence/g01/surface_energy_checks_results.json` | `cfe48cb1024669bc9d1d6cdae495a65bf2004c760a2d4546a3d1ec8669e9ff28` |

Notes on the two evidence files:
- `RUN_HISTORY.md` — the narrative run record, INCLUDING the initial
  failed run (0/8) and its diagnosis.
- `surface_energy_checks_results.json` — raw machine results of the FIRST
  full battery run (the 0/8 failure, preserved per ASTRA instruction) plus
  the final green run.

The four code files were NOT modified by the G01-R correction pass (G01-R
touched only the two docs and created evidence copies), so these hashes are
the code the certified 8/8 + 10/10 runs executed.

## Exact test commands and working directories

```
cd /e/Chimera_G01/tools && python surface_energy_checks.py      # → 8/8 PASS
cd /e/Chimera_G01/tools && python material_contract_checks.py   # → 10/10 PASS
```

Working directory for both: `E:\Chimera_G01\tools` (the tests import their
subjects by module name from that directory). Re-runs by the reviewer must
use the same cwd; the tests write no files outside the process.

## Executing interpreter (reported by the interpreter itself, not from docs)

| Item | Value | Measured via |
|---|---|---|
| Python | 3.14.3 | `sys.version.split()[0]` |
| NumPy | 2.2.6 | `numpy.__version__` |
| float eps | 2.220446049250313e-16 | `sys.float_info.epsilon` (the P-1 limit's basis) |
| OS / shell | Windows 10, MSYS bash | — |

## Verification class of this packet

Numerical (CPU numpy) ONLY. No engine-window, no DYAD, no GPU verification
exists or is claimed. The GPU handoff in the packet is a proposal with
PROPOSED (unverified) tolerances; the window experiment is a design, not a
result.
