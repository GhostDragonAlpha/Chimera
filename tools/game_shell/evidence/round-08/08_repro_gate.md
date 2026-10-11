# Round-08 fix — Step 0 REPRODUCIBILITY GATE: FAILED as literally specified → STOP

Date: 2026-10-10 · Worker: Tiel · Status: **STOPPED at the gate per assignment
contract** ("If the output hash != 74b3ab04… STOP immediately… Do not
proceed"; "repro gate fails" is the contract's first named unexpected wall).
Cause fully diagnosed, unblock proven bit-exact, decision returned to Qwen.
**Nothing outside `tools/game_shell/evidence/round-08/` was touched.**

## Gate result

| run | pack sha256 |
|---|---|
| shipped `Saved/meshes/monkey_joints.bin` (= graph pin) | `74b3ab04…c1662` |
| unmodified `tools/rig_factory_fit.py`, tree inputs, scratch out | `ef0114167fefe5f74ad216f3f585300676d04c86bdbc6d0b77c62e74959a3c05` — **MISMATCH** |
| unmodified generator + reconstructed referee input (below) | `74b3ab04…c1662` — **BIT-EXACT** |

## Field-level diff (shipped vs unmodified-tree regeneration)

`_scratch_gen/_diff_packs.py`: `owner`, `w`, `J`, `AX`, `parents`, `joint2`,
`w2` are **bit-identical**. The ONLY difference: 8 `ROM` rows —

| joint (L and R) | shipped (referee) | factory fallback |
|---|---|---|
| shoulder | (−149, 60) | (−30, 60) |
| elbow | (−145, 125) | (−30, 125) |
| hip | (−159, 119) | (−150.23, 60) |
| knee | (−131, 147) | (−147.89, 140.15) |

## Cause

`rig_factory_fit.py:412` overlays referee ROM verdicts from
`.tmp/skeleton/rom_referee_r2.json` (written by `tools/rom_referee_r2.py`,
B5 round 2). That file is **gone**: `.tmp/` is gitignored scratch
(`.gitignore:230`), never tracked (`git log` empty), and the generator treats
absence as "loud warning, never silent" — it falls back to `ROM_L` values.
So the generator ALONE (tree state) is not the sole authority; the generator
**plus that input** is, and the input is recoverable bit-exactly: the shipped
pack's own ROM rows ARE the referee overlay (the overlay is the last writer
of those rows).

## Why I did not proceed

1. Gate wording: hash mismatch → STOP, do not proceed.
2. To regenerate the REAL pack with the REAL generator, the referee file must
   exist at `.tmp/skeleton/rom_referee_r2.json` — writing there is outside my
   allowed touch list, and running a path-redirected generator instead would
   leave the real generator permanently unable to reproduce the asset (the
   exact silent-authority problem the gate exists to catch).
3. Real regression hazard the ownership diff would NOT catch: regenerating
   without the overlay silently rewrites 8 ROM rows (elbow ext −145→−30, hip
   flex 119→60, knee flex 147→140.15, shoulder ext −149→−30) — gameplay
   clamps change while every vertex binding stays identical.

## Proven unblock (one decision for Qwen)

`_scratch_gen/rom_referee_r2.reconstructed.json` holds the four pair entries
read bit-exact from the pack; with `_ref_path` pointed at it, the UNMODIFIED
generator reproduces the pin `74b3ab04…c1662` exactly (log:
`_scratch_gen/gen_with_referee.log`). Options for Qwen:

- **A (minimal):** approve restoring `.tmp/skeleton/rom_referee_r2.json`
  (exact contents = reconstructed file) and re-run the gate → passes
  bit-exact → steps 1–7 proceed exactly as assigned.
- **B (durable):** additionally re-run `tools/rom_referee_r2.py` (regenerates
  the verdict from mesh+pack; needs scipy) and/or embed the referee ROMs in
  the generator so a scratch-dir cleanup can never silently regress the pack
  again.

## State preserved

- `Saved/meshes/monkey_joints.bin` untouched, re-verified `74b3ab04…c1662`.
- Backup taken: `tools/game_shell/evidence/round-08/monkey_joints.bin.bak-74b3ab04` (Step 1 done early, hash-verified).
- No generator edit, no re-pin, no engine/browser work started.
- Scratch artifacts: `_scratch_gen/` (patched-path generator copies, diff
  tool, reconstructed referee JSON, repro packs, logs).
