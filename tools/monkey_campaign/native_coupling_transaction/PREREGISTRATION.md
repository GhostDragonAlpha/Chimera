# Native coupling transaction software correction

Owner: astra-native-coupling. Operator-authorized isolated engine work,
2026-10-03 America/Chicago. Source base: 771c812b7adca04d6f33cd3001a1376e337c86e8,
verified against remote master before preparing this file package.

## Problem and prediction

The native CombineScheduler is already consumed by MembraneTick::step. Its
run_window currently routes results into the live owner store before all later
results have passed output/ownership/duplicate checks. A late refusal can leave
the live store, apply counter, routed-writer bookkeeping and ledger partially
changed. Coupled modules require a whole-window transaction boundary.

Stage the complete window in private copies of the existing store and scheduler
bookkeeping. Commit by non-throwing swaps only after every output, ownership and
status operation has succeeded. Preserve the current contribution API, canonical
order, permitted output shapes, valid-window values, ledger ordering and serial
default. Callback purity remains a cooperative obligation; this change does not
sandbox callbacks that mutate external state.

## Software falsifiers fixed before implementation

- A late undeclared output, wrong owner, unknown state, duplicate writer, status
  refusal or callback exception changes live store bytes or its apply counter.
- A refused window poisons an identical repeated attempt on the same scheduler,
  or retains a ledger entry from an unsuccessful attempt; a new scheduler with
  new immutable valid inputs cannot recover against the unchanged store.
- Contribution-list order or execution with 1/2/4 workers changes accepted store
  bytes, routed records or ledger digest on the same compiler/backend.
- The unmodified baseline does not reproduce the late-refusal partial mutation,
  or the corrected core still reproduces it.
- The existing native MembraneTick gate loses its byte-identity across worker
  counts or parity against the original pre-wiring baseline.

Run these bounded CPU software checks only through the canonical sealed package
runner. Preserve the failing baseline discriminator and all run receipts. The
original membrane gate's preregistration, pins, scene and 180-tick criterion stay
unchanged. No scientific geometry, new body parameter or locomotion experiment is
introduced. This is repository software verification, not campaign admission or
a new physical qualification.

## Remaining architecture work

This repair establishes native whole-window refusal safety. Native implicit
coupling, typed physical ports and actual dynamically coupled game consumers
remain separate requirements. Passing this correction does not finish the engine
or the playable monkey goal. Shared integration/publication remains with GLM's
existing owner; this package changes no shared working file or Git ref.

## Pre-execution API clarification

Non-author source review identified that correcting a captured callback variable
would violate the declared frozen-input purity law. Before any run, narrow the
retry check to identical repeated refusals on the same immutable scheduler, then
successful recovery through a new scheduler with new immutable inputs. The API
provides no callback reconfiguration operation. No test result prompted this
clarification; the baseline discriminator and all rollback obligations remain.
