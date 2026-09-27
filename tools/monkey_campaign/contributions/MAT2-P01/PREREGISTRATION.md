# MAT2-P01 PREREGISTRATION — frozen before any build/verify run

Frozen: 2026-09-27T07:50Z (before test authoring and all runs below).

Task: Freeze the playable-monkey completion contract (MAT2-P01, criteria
sha256 e4521ad79a5bc263ba333b81ebe36599e1d6da5a13eed92c2ff5fa3a0e670c5e,
planning id P01, scope sha256 cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097).

## Frozen statement

The completion contract comprises (a) the carried core clause — "One monkey,
ground movement, one climbable trunk, return to ground, explicit success/failure
behavior; broader features excluded" — carried VERBATIM from the archived
ONT-P01 contract (archived scope sha256 01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6,
card state DONE at archive time), and (b) the material-first addition adopted
under astra-0031: reusable matter is the architecture; walking through woods is
the first product milestone, followed by the existing climb/return goal;
additional materials remain extensible, not universal-physics prerequisites.

## Frozen prediction

P1: The archived core clause equals the first sentence of MAT2-P01's done_when
byte-for-byte, and the material-first addition equals its remaining text
byte-for-byte (whitespace-normalized sentence compare).
P2: The active scope hash is cb5475f8... (recomputed from instruction_state's
canonical catalog by the test via the recorded tool contract, or accepted from
the startup-recorded scope_integrity block as an identity binding).
P3: All referenced authority files (MATERIAL_PLAN_ADOPTION.md, APPROVED_SCOPE.json,
MONKEY_RUN.md) hash to their recorded values.

## Frozen falsifiers (each must FAIL the test when its condition is injected)

F1 (missing identity): removing or altering any identity binding (criteria sha,
scope sha, archived scope sha, planning id) makes test_contract.py exit nonzero
with IDENTITY_MISMATCH.
F2 (unsupported pass): a completion-claim JSON citing a scope hash that is not
the bound active hash is refused with SCOPE_UNSUPPORTED; a claim without all
five core-clause elements (monkey, ground movement, climbable trunk, return to
ground, explicit success/failure) is refused with CORE_CLAUSE_INCOMPLETE.
F3 (record substitution): a screenshot or narrative path offered as contract
evidence is refused (only the bound authority hashes count).

## Frozen probes

test_contract.py (this contribution) implementing P1-P3 and F1-F3, CPU-only,
python -B, no network, no engine.

## Honest boundary

This is an offline records-kind contract card: no runtime, visual or native
claim is made or needed (verification_profile kind: offline). The contract
FREEZES the goal; it does not implement it.
