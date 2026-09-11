# fleet-slot-expansion-03 preregistration (2026-09-11, lead lane)

Successor of fleet-slot-expansion-03 with corrected scopes (+ layout.py,
+ inventory.py — both hardcode the 1-5 bound; -01/-02 records retire via
task_abandon once deployed). Operator directives: HUMAN feedback 4e55c08a
(grow until an empirical limit; I/O hypothesis) + dbd97562 (slots spin up
like worktrees) + the standing mandate: work until yes.

- **STATEMENT**: slots are materialized on demand like worktrees — the
  registry dict IS the state (no count lives in code beyond a safety
  fuse); a supervisor `slot_spawn` creates the next slot with the standard
  layout, `slot_retire` retires a free unprovisioned one (slot 1 immortal);
  a claim with no free slot of its kind auto-spawns one instead of
  refusing, WITHOUT masking stale-provision refusals; fresh registries
  still initialize 5 (migration is a no-op); a SLOT_MAX=64 fuse makes
  unbounded growth degrade by named refusal instead of corruption.
- **PREDICTION**: (1) reopening an existing registry changes nothing
  (byte-equal slots); (2) slot_spawn 6..N creates slots with correct
  kind/path/port-family; retire round-trips; refusals by name
  (busy/provisioned/slot-1/unknown kind/non-supervisor/guard); (3) with
  all worker slots busy, an eligible claim auto-spawns and completes
  claim→checkpoint end-to-end; a free-but-stale-provisioned slot still
  yields `stale_provision_requires_recovery` (not masked); (4) scale
  probe: ≥8 threads × ≥20 s mixed ops on one registry → zero
  `database is locked`, recorded p50/p95/p99 op latency + per-slot spawn
  cost (first I/O-hypothesis data); (5) inventory count parameter
  default-5 keeps existing callers byte-identical; (6) full fleet suite
  green.
- **FALSIFIER**: existing slots mutated/removed; lost claims/audit; lock
  errors in the probe; auto-spawn masking a stale provision; latency or
  spawn cost unmeasured; path/port collisions with protected paths;
  kind semantics changed (slot 1 integration); or live deployment outside
  the documented controlled transition.

Deployment + live spin-up by the lead after review; operator's 10-parallel
deployment is the acceptance exercise.
