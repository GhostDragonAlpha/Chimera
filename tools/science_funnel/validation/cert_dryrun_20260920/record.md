# cert-dryrun-20260920 -- the FIRST full production-class compatibility certificate (dry run)

Rule-0 preregistration of record: `receipt.json` (frozen rule_0 sha printed in
the receipt; convention identical to the snapshot-apis lane's). This file is the
narrative; the receipt is the law. Committed BEFORE this lane's first build,
before any run of its own.

## The theory (Rule 0)

The snapshot-apis lane named its own successors in
`snapshot_apis_20260920/receipt.json` ("what_a_production_certificate_still_lacks"):
(a) bind the 5-tuple relation to the REAL engine build's identity, (b) run the
upgrade-gate checks 1-3 ON the engine walk path through the new readers. This
lane does both, as ONE end-to-end issuance: the FIRST full production-class
compatibility certificate, dry-run with the P3 dummy actor, on EXISTING
machinery only (the out-of-tree instrument pattern; zero engine edits).

**Statement:** the certificate issues clean (validator exit 0, production
class, deploy ALLOW for the matching 5-tuple) AND the validator rejects every
tampered re-issue (bumped state hash / swapped normalization constant / stale
build id: 3/3, clean re-issue validating -- no false positive).

**Prediction (pre-named):** check 1 reproduces the tick-150 bit-identity
THROUGH the certificate path (the certificate's replay evidence IS the proof:
per-tick state hashes of the engine walk of record, hash-chained per the
certificate's own convention); check 2 exact-agrees on a fresh recompile
(byte-irrelevant rebuild -- binary stamps may move, walk artifacts may not);
all 3 tamper probes rejected; the actor leg's six gates green on the declared
CPU scene (the upgate machinery, unchanged).

**Falsifiers (pre-named, full text in the receipt):**
- **F1 ISSUANCE-FAIL** -- the validator blocks the clean production
  certificate; the report names the blocking condition verbatim.
- **F2 TAMPER-PASS** -- any tampered re-issue validates or deploys; THE GATE
  IS BROKEN; report loudly, never tuned away.
- **F3 IDENTITY-WEAKNESS** -- the build identity cannot be bound tighter than
  "the instrument's own build" (no engine-provided build id exists); the lane
  then binds the strongest available identity (source closure + binary stamp +
  scene pin + ship-byte anchors), says exactly that in the certificate, and
  records the engine-service gap for a first-class build id.
- **F4 determinism** -- 3 independent full pipeline runs, byte-identical
  canonical payloads.
- **F5 scope** -- lane dir + tools/policy_compat (+ its tests) only; zero
  ChimeraEngine/ edits; builds under .tmp/ (untracked).

## The identity binding (Rule 1: derived, not chosen)

`physics_build.build_id = "engine-walk-instrument/" + id16` where
`id16` = first 16 hex of sha256 over the canonical JSON of
`{closure, harness, scene_pin}`: the sorted (relpath, sha256) of the compiled
source closure (the instrument's engine header copies + the harness sources +
json.hpp), the harness sha, and the scene pin sha. Bound alongside: the
compiled binary stamps of build A and build B (they MAY differ from each other
-- byte-irrelevance is check 2's claim), the compiler identity, and the ship
anchors. Dormancy is re-proven at issuance time from source: stripping every
`#ifdef GAIT_SNAPSHOT_API .. #endif` block from the copied gait_controller.hpp
must equal the shipped bytes; the rest of the closure byte-equals the shipped
tree at base f6787ebe.

Why this is the right identity for the engine walk path: the instrument's walk
leg is FENCED to the ship -- its stdout/trace bytes equal the wave-47 ship
anchors with recording active (the snapshot-apis F2 legs, re-measured by this
lane; the LEG-A/LEG-B fence live-verified from the bound proof receipt at
issuance). What the identity does NOT bind: a ship-tree binary (none exists in
this lane). The claim is exactly "instrument build, ship-fenced" -- never
"ship binary".

## Registered cases (declared a priori)

- **RC-1 ship-walk** -- the ship walk, no command schedule, horizon = the walk
  life (refusal-terminated; 302 recorded ticks, refusal face
  302/gait_positional_correction_budget). Instruments: states.bin /
  actions.bin / snap_t150.bin / manifest / stdout / trace stderr.
- **RC-2 pinned-command-zoh** -- schedule `150:1.01` (zero-order hold from the
  checkpoint tick; 1.01 m/s = the walk's own measured base speed) through the
  existing typea command adapter, plain harness mode. Instruments: stdout +
  trace byte-compare across builds.
- Checkpoint tick 150 (inherited derivation: the mid-hold tick of the shipped
  ride/hold era [107,152), frozen in the snapshot-apis receipt).

## Checks 1-3 through the certificate path

1. **Same-build replay + checkpoint-resume** -- ref runs x2 fresh-process
   byte-identical; snapshot at the end of tick 150; fresh-process restore;
   the restored continuation must equal the uninterrupted tail tick-for-tick
   on state hashes AND action bytes; refusal face identical. The certificate's
   replay evidence chain is built from THESE hashes (convention: state hash =
   sha256 of the canonical 4-class serialization body, 3089 B; chain_0 =
   sha256("chain0:" + initial snapshot sha); event chain =
   sha256(prev:tick:kind:state)). Plus the 4 forced-drop probes re-run on THIS
   lane's binary (each must move the continuation).
2. **Cross-build equivalence** -- the instrument recompiled fresh into an
   independent build tree (build B); RC-1 and RC-2 must agree EXACTLY across
   builds A and B.
3. **Closed-loop requalification shape** -- engine leg: the walk is closed loop
   (the engine controller is the in-loop actor; actions recomputed from the
   live trajectory every tick -- the restore proof demonstrates exactly this),
   and the action-replay refusal must hold: no channel accepts a pre-recorded
   action stream (CLI probe refused before any step; the runner's requalify
   refuses precomputed actions and action_replay mode). Actor leg: the frozen
   dummy actor on the declared CPU walk scene -- the upgate check 3, unchanged:
   six gates + refusal probes + the P3 corpus cross-check.

## The acceptance letter (part d)

The six required bars are measured on the ACTOR leg (all six, upgate gates) and
declared per-leg for the ENGINE leg: bit-identity with the ship walk of record
is the engine leg's acceptance bound. The engine walk of record is the SHIP
FACE -- including its own refusal (302, the ship positional-correction budget)
and its own census reds (support_census min_contacts=1, sub2_ticks=46 inside
the ship's judged window) -- byte-fenced; the certificate claims that face
bit-identically and claims NOTHING greener. Non-regression margins: engine-walk
bit-identity (bound 0, the wave-47 anchor reference), restore-resume diverging
ticks (bound 0, the frozen-ref discipline), and the upgate's derived
cross-build open-loop margin (the geometric-sum derivation).

## Registration (what the certificate claims / does not)

CLAIMS: this exact engine walk build (source closure + binary stamp + scene
pin f6844ee... + ship anchors), this actor (the P3 dummy bundle hashes),
this scene pair (the gait scene + the declared CPU walk scene for the actor
leg), these bars; the four restart-state gaps RESOLVED through the
snapshot-apis readers (proof bound by the receipt sha, live-verified at
issuance); deployment class production.

DOES NOT CLAIM: no trained policy exists (the actor is the declared dummy,
body UNBOUND_dummy); no ship-tree build id (the identity is instrument-build-
ship-fenced; a first-class engine build id is a NAMED FORWARD GAP); the
ship-tree HTTP snapshot route (GET/POST /gait_snapshot) is a NAMED FORWARD GAP
and is NOT implemented here; no actor-in-the-engine-loop coupling (the engine
walk's in-loop actor is the engine controller; the only actor->engine channel
in existence is the command adapter at schedule granularity -- RC-2).

## Negative controls

T1 bumped state hash (cert_hash recomputed -- a self-consistent forgery): the
evidence chain must mismatch. T2 swapped normalization constant: validator-level
(compat_key vs relation mismatch) AND deploy-level (the tampered 5-tuple cannot
be the certified bundle of a request built through the frozen P3 loader --
compatibility key mismatch, BLOCK). T3 stale build id: validator and deploy
rejections as in T2. Clean re-issue: zero violations, deploy ALLOW.

## Measured (append-only)

VERDICT: **ALL FIVE FALSIFIERS HELD** (per-falsifier numbers in receipt.json
`measured`; artifacts under `runs/`).

- **The certificate ISSUED:** production class, validator exit 0,
  `compat_key 091a3e5147f266706a342ab18255a21780ffd6dc03f3280a5db56ddf86bbad2a`,
  `cert_hash f3efd8c9...`, build_id
  `engine-walk-instrument/29bf00f0640c75c4`, all four engine gaps RESOLVED
  with proofs live-verified at issuance; deploy gate ALLOW for the matching
  5-tuple, BLOCK for a foreign build, BLOCK for a missing certificate.
- **F1 ISSUANCE-FAIL, not fired:** the clean production certificate validated
  with ZERO violations on the first issuance through the fixed pipeline.
- **CHECK 1:** fresh-process replay byte-identical; the tick-150 checkpoint
  (`0d6f65f9...` -- byte-exactly the snapshot-apis lane's committed snapshot)
  restored bit-identically in a fresh process: 152/152 tick state hashes,
  21888/21888 action bytes, refusal face 302/gait_positional_correction_budget
  identical; ship fence stdout/trace EXACT on this lane's binary; all 4
  forced drops moved the continuation; 16308 serialized f64 fields NaN/Inf-free.
- **CHECK 2:** fresh recompile (independent configure; binary stamps differ
  `64e81814...` vs `9fb65564...` as declared): RC-1 ship-walk EXACT on
  states/actions/snapshot/stdout/trace; RC-2 pinned-command-zoh `150:1.01`
  EXACT on stdout+trace with the F-G42 census echo present.
- **CHECK 3:** engine leg closed-loop with the refusal PROVEN: relative-path
  actions file REFUSED (`bad command spec (want tick:vx)`) before any step;
  the nonexistent-path probe RAN without opening the referenced file (no
  action-file channel exists); runner requalify refusals 2/2. Actor leg: the
  upgate gates ALL GREEN (six bars), corpus reproduces the frozen P3 bytes,
  action-replay refusals 2/2, max|v| 0.8699 <= envelope 2.9774 m/s.
- **F2 TAMPER-PASS, not fired -- 3/3 REJECTED:** T1 bumped state hash
  (cert_hash recomputed, a self-consistent forgery) -> evidence-chain
  mismatch; T2 swapped normalization constant -> validator key mismatch AND
  deploy BLOCK against the frozen-loader request; T3 stale build id -> both
  layers REJECT. Clean re-issue: zero violations, deploy ALLOW (no false
  positive).
- **F3 IDENTITY-WEAKNESS, resolved by binding + naming:** the identity binds
  the compiled source closure (dormancy-proven from source), both binary
  stamps, the scene pin, and the ship anchors; the certificate says exactly
  "instrument build, ship-fenced" and names the first-class engine build id
  as the engine-service forward gap.
- **F4 determinism, fired once then held:** the FIRST measurement FIRED (the
  three payloads differed) -- the cause was INSTRUMENTATION: the engine-CLI
  probe's recorded argv2 embedded the run-index path, while EVERY walk
  artifact sha across the three runs was byte-identical. The probe spec was
  made run-index-free and F4 re-measured CLEAN: three byte-identical
  canonical payloads, sha `cf036fc77bc59fe217193a94d3d045818d249d0670ec629ab244545419d989a8`.
  The falsifier did its job; nothing was tuned away.
- **F5 scope, not fired:** lane dir + tools/policy_compat (+ tests) only;
  zero ChimeraEngine/ edits; builds under .tmp/ (untracked).

The named forward gaps ride the certificate's registration verbatim: the
ship-tree `/gait_snapshot` route, the first-class engine build id, and
per-tick actor-engine coupling -- all NAMED, none implemented.
