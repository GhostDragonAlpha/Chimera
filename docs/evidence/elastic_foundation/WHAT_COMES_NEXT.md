# WHAT_COMES_NEXT.md — roadmap past the CPU-reference membrane law

Status: PROPOSAL. Written 2026-09-08, append-only.

This law's job was to be a REFERENCE: a deterministic, falsifiable, unit-carrying membrane
model with its own battery, a D1 material-response demo, and frozen GPU fixtures. That is
closed (MANIFEST.md). What follows are the candidate next moves, in dependency order. Start at
the top of each group; a group is not done until its acceptance run exists.

## 1. GPU acceptance (the handoff, do THIS first)

`GPU_HANDOFF.md` §5 is the contract. Nothing else is worth parallelizing before the kernel
exists. Deliverables: Stage A kernel, Stage B gather, Stage C acceptance scripts, and a
re-run of the CPU battery (`--suffix gpu_accept_<date>`). Expected spends: kernel + acceptance
~ 1–2 sessions of a focused GPU agent.

## 2. Extend the reference (additive membrane features)

Each item is a NEW law amendment (DERIVATION.md + a falsifier in the battery or a new one),
never a silent rewrite of this one:
- **per-vertex normals and a bending term** (discrete mean-curvature or STVK-plate); the sheet
  frame already exists but bending wants per-vertex data, so this is new geometry.
- **anisotropic fiber direction** (mapped onto `frame_t1/t2`), tested at D1 scale.
- **element quality hazard naming**: report per-face condition number of `B` so the user can
  pre-filter bad rest meshes even when total area is fine.
- **remeshing-friendly "rest-transfer"**: given two rest meshes and a map, transfer `A0`/`B`
  input (used by the renderer's adaptive subdivision).

## 3. GPU solve layer

- port `optimizers.py::gradient_descent` and `conjugate_gradient` to run per-frame on GPU
  using the Stage-C-accepted force kernel; keep the CPU identical for the battery.
- add a time-integration module (semi-implicit Euler) with its own energy-drift falsifier;
  the demo currently has NO time axis by design (phases are optimization steps).

## 4. Couplings (renderer-side)

- gravity + wind (time-dependent restoring), damping/viscosity; each gets a falsifier that
  runs against THIS law's static reference responses (the D1 reactions).
- two-way coupling with the renderer physics (the teddy); the contract for combining stages is
  already documented in AUDIT.md §7 (one strain convention per stage).
- collision contact forces, then the "movie, not still" judgement pipeline from AGENTS.md.

## 5. Calibration

- fit the scalar demo parameters (E, nu, gamma) to an LM-Station measure of "looks like the
  material intent" using the dyad-analysis loop (a number AND a term, aligned).

## Standing rules for anyone continuing

- Rule 0/1 gate before any sweep (`tools/training_gate.py`, `docs/THE_LAW.md`).
- No reference, no verdict: every new quantity that is "good enough" needs a named threshold a
  falsifier can kill.
- Delta checks are cheap: re-run `make_fixtures` + `verify_fixtures` and the battery after any
  change to geometry/law/materials; the docs point at the live store (`tools/orient.py`).