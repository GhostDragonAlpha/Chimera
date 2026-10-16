# mechanism_factory — §11.18 P1 reference layer

The boundary/load equilibrium solve required by
`docs/GAME_PLAN_ACTION_RPG.md` §11.18 "First deliverable": *"Reuse the
constant-gamma law; qualify its boundary/load solve before producing
targets. If that solve is absent, implement and validate it first."*
The solve was absent (no applied-load term existed anywhere in
`tools/membrane_scale_lab/`); this directory is that P1 reference, pure
numpy, CPU only, no engine, no GPU, no network.

## What exists here

| File | Role |
|---|---|
| `patch_equilibrium.py` | `solve_equilibrium(positions, faces, gamma, fixed_vertices, loads)` — monotone backtracking projected descent on `U(x) = Σ γ_t A_t(x) − Σ f_i·x_i`; named pre-iteration refusals; pin reactions; `free_residual`; receipt writer (schema `chimera-mechanism-factory-patch-equilibrium-v1`). All check tolerances are frozen in `PREREGISTERED_ALLOWANCES`. |
| `patch_equilibrium_checks.py` | The registered falsifier battery C1–C6 on the house `tools/port_registry.py` harness. Exit 0 all-pass, 1 a check failed, 2 evidence-path refusal. |
| `README.md` | This file. |

## The law reused (imported, never edited)

`tools/membrane_scale_lab/surface_energy_reference.py` — the law of record:
`U_surface = Σ γ_t A_t` on CURRENT geometry, exact geometric derivative
(`grad_a A = cross(b−c, n)/2`), named refusals (`InvalidSurface`). The
descent discipline (preconditioner `P = 1/γ_max`, Armijo `c1 = 1e-4`,
geometry gate = the reference's own refusals, the five terminal states
`stationary|stagnated|step_limit|no_descent_step|invalid_surface`, pin
reactions `R_i = −F_total_i`) is imported from
`tools/membrane_scale_lab/overdamped_descent.py` and mirrored, not
re-declared. Fixtures come from `tools/membrane_scale_lab/fixture_generator.py`;
evidence paths from `evidence_output.resolve_evidence_path`.

## The load term added

Dead external loads at named vertices: `U(x) = Σ γ_t A_t(x) − Σ f_i·x_i`,
so `F_total = F_surface + f` (the load potential is linear, gradient −f).
A load on a pinned vertex is a contradiction and is refused before any
iteration (`load_on_fixed_vertex`); zero tension with loads is refused
(`load_zero_tension`). At stationarity the reactions satisfy the balance
theorems `Σ R + Σ f = 0` and `Σ x × (R + f) = 0` (exact: translational and
rotational invariance of the surface law).

## How to run

```
python tools/mechanism_factory/patch_equilibrium_checks.py            # exit 0 = green
python tools/mechanism_factory/patch_equilibrium_checks.py --json     # + dump
python tools/mechanism_factory/patch_equilibrium_checks.py --out PATH # explicit evidence path
```

Each green run writes a stamped receipt
`docs/evidence/mechanism_factory/patch_equilibrium_receipt_<stamp>.json`
containing: schema, UTC, `source_commit` (`git rev-parse HEAD`),
sha256 of every imported law/solver/fixture file plus both files here,
the frozen allowances, and per-case records (fixture params, pin set,
load vectors, status, steps, free residual, reactions, force/moment
balance residuals). Existing evidence is never overwritten (exit 2).

## The checks (all green, 2026-10-15)

- **C1 analytic anchor** — one triangle, two pins, loaded vertex with
  `|f| = γL/2` exactly. Closed form: `f = γ·grad_a A` with
  `|grad_a A| = |b−c|/2` forces `f ⊥ bc`, `|f| = γL/2`, the final normal
  `n·f = 0`, and the equilibrium set is the flat ray along `f` (U ≡ 0 on
  it). Reactions verified against independent Heron finite differences
  (`R = +γ·grad A`, the pin cancelling the surface force) and the sum
  identity `R_b + R_c + f = 0`. Measured: residual 2.4e-9, identities
  ≤ 4.8e-9.
- **C2 zero-load equivalence** — `loads=[]` reproduces `run_descent`
  bit-exactly (ΔE = 0.0, same status, same residual) on flat and bumped
  disks.
- **C3 balance identity** — asymmetric composite (three apex patches,
  6/5/8 rims, three point loads): force balance 3.5e-7, moment balance
  3.2e-7, both ≤ 1e-6.
- **C4 asymmetry real** — per-block reaction norms 0.87/0.67/0.61,
  margin 0.30 > 0.10.
- **C5 refusals** — all 13 named refusals fire under their exact names;
  the valid control is accepted.
- **C6 convergence honesty** — overload (`|f| > γL/2`) → `step_limit`
  (residual 0.105); partial-rim pins → `step_limit` (residual 0.13);
  the solvable control converges — no fake stationary.

## Physics findings (reported, not tuned away)

1. **Partial-rim pins have no equilibrium under this law.** A free
   boundary vertex of a constant-γ current-area film carries line tension
   γ (measured |F| = γ·spacing on a straight free rim): the film contracts
   its free edge forever. The task's literal C3 prescription
   ("irregular_patch, partial-rim pins") is therefore unsolvable by
   construction; C3 uses an asymmetric multi-load composite and the
   partial-rim case is kept as a C6 honesty witness.
2. **Loaded irregular meshes are ill-conditioned for the lab's fixed
   preconditioner.** Tangential (reparametrization) modes of the area law
   have Hessian eigenvalues ~1e-6 vs ~7 normal ones (measured κ ≈ 7e6);
   the lab's own `run_descent` stagnates/step-limits on the same fixtures
   (verified). The C3 fixture keeps free vertices at apex-like positions
   where the soft modes are unforced by symmetry.
3. **The stagnation floor caps asymptotic stationarity.** The lab's own
   law (accepted decrease ≤ 8·ε·max(|U|,1)) floors the reachable residual
   at ~√ε ≈ 4e-8 when the equilibrium energy is ≈ 0; `stagnated` with
   residual ≤ 1e-6 is the honest converged label there (C1, C3).

## §11.18 stage covered

This is the **P1: reference** stage for the response *"boundary
displacement + point loads → equilibrium port reactions of an asymmetric
constant-tension patch"*: analytical anchor + native correctness
falsifiers + receipts at pinned inputs, qualifying the boundary/load
solve before any P2 characterization sweep produces labels. P0 packet
fields (owner scope: only `tools/mechanism_factory/` and
`docs/evidence/mechanism_factory/` are written; the lab is imported
read-only) and the failure-response law (refuse before simulation;
convergence failure stays FAILED/stagnated, never rewritten) are honored.

## Receipt adapter (seam 2b) — `receipt_adapter.py`

Independent, versioned verifier (`ADAPTER_VERSION = receipt-adapter-v1`,
accepted schema `chimera-mechanism-factory-qualification-receipt-v2`; v1
receipts are refused explicitly as `receipt_schema_unsupported`).
`verify_receipt(receipt, packet) -> Verdict(passed, refusals)` trusts nothing
it can recompute: packet digest, solver/law/fixture file hashes, units,
finiteness, the convergence acceptance law (`unconverged_label`: stationary,
or stagnated with the case residual within the PACKET threshold), the v2
balance residuals recomputed against the packet's force/moment thresholds,
domain and split integrity, declared-verdict forgery (tolerances read ONLY
from the packet; thresholds carried in the receipt are inert), and `gpu_job`
reservation unless a clean-resume block matches a checkpoint hash on disk.
Run: `python tools/mechanism_factory/receipt_adapter.py RECEIPT PACKET`
(exit 0 pass / 1 refused / 2 usage-or-unreadable).

Acceptance suite — `receipt_adapter_faults.py` (exit 0 only if all green):
builds a genuine pair fresh, then injects F1 receipt deleted; F2 receipt
hash byte flipped; F3 units `cm`; F4 holdout family duplicated under train;
F5 NaN output; F6 `step_limit` and over-threshold `stagnated`; F7 foreign
family `twisted_torus`; F8 packet threshold widened post hoc; F9 PASS
claimed over an over-threshold number; F10 gpu_job reserved vs. clean
resume with a real checkpoint; F11 absurd receipt thresholds proven inert;
F12 a v2 receipt recording a balance residual above the packet threshold
under a declared PASS (`verdict_forgery`).
Results are stamped as `chimera-mechanism-factory-adapter-faults-v1` into
`docs/evidence/mechanism_factory/` via `resolve_evidence_path`.

## P3 bounded fit, learned candidate and GPU batch — `bounded_fit.py`, `fit_job.py`

`bounded_fit.py` builds the bounded PCHIP table from adapter-PASSed
receipts only (out-of-domain refused by name; holdout structurally unread;
`no_final_test_access` recorded), evaluates against direct reference
solves, and refuses or justifies the learned candidate by gate
consistency. `fit_job.py` is the device-agnostic learned-candidate fit
(seed 1729, fit-job-v1 receipt, `physically_qualified` flag vs the packet
gate, budgets enforced). `gpu_fit_manifest.py` + `gpu_fit_dryrun.py`
preregister the one-reservation GPU batch (no LLM calls, release in
cleanup) and validate it without reserving; see `GPU_LIVE_BATCH.md`.
## Executable checklist (seam 3) — `test_workflow_checklist.py`

Work object `work.mechanism-factory-patch-equilibrium` in
`tools/creature_graph/data/creature_graph.json` binds the 11.18 first
deliverable (smallest receipt adapter + executable checklist): four pinned
checks (p1-battery, qualification-receipt, adapter-faults,
adapter-verify-committed) run by the trusted `graph_workflow_runner` on a
clean committed candidate, with `verifier_inputs` sha256 pins over the five
mechanism_factory modules, `port_registry.py`, the packet, the committed
receipt and the four imported lab files. Checks write evidence OUTSIDE the
tracked candidate via `--out ../mechanism_<name>.json --force-out`, so
`candidate()` stays clean before and after.
Read-first graph documents: this README and `example_packet.json`
(losslessly absorbed, immutable by oid).
Run: `python tools/mechanism_factory/test_workflow_checklist.py`
(builds the control plane on a temp service over the real graph and runs
claim -> prepare -> pinned checks -> attest -> submit_review to REVIEW).
