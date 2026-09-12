# Review slot handoff validation

Task: `fleet-review-slot-handoff-01`, slot 1, generation 1. Base integration
revision: `17403eddaa4dcecee0b41a26da451da096d6e2cb`.

The controller previously held slots until integration and counted all REVIEW
tasks against worker capacity. The service now uses an additive controller
subclass. A trusted, preserved PR handoff releases its slot while retaining REVIEW;
detached reviews no longer consume execution capacity. Scope barriers remain.
Corrections return to READY, then an ordinary claim and exact-head provisioning
allow the same or a replacement worker to resume.

No live registry, credentials or worker slot was changed by these tests. All
controller/HTTP tests used temporary registries and owned loopback servers.
Source identities are in `FINAL_SOURCE.json`.

## Executed validation

- Final installed focused suite: 13/13 PASS, 1.478 seconds. The parent command,
  exit status and complete stdout/stderr are retained in the `parent_final`
  records. No control-root override was set.
- Final candidate against current deployed controller source: 13/13 PASS.
- Final candidate against integrated controller source: 13/13 PASS.
- Existing controller suites with their fixture Control globals rebound to the
  exact service subclass: integrated 74/74 PASS; current deployed source's
  available suites 62/62 PASS. The runner and final raw logs are retained here.
- Before the final acknowledgement-response correction, the parent full fleet
  suite ran 100 tests: 99 PASS, one SKIP because symlink creation was unavailable.
  The exact earlier source is retained under `superseded_before_ack_response`;
  its full run is `parent_full`. This is not a claim that the full 100-test suite
  ran against the final source. The final change adjusts only the response after
  successful inherited integration and adds tests for detached/slotted responses.
- Before implementation, the fleet baseline ran 88 tests: 87 PASS and the same
  symlink SKIP. Its tool output remains in the lead session.

The focused suite exercises authenticated refusal and rollback, exact head and
slot identity, preservation of another task under the same agent identity, two
detached reviews freeing capacity, scope protection, resources retained on
refusal, integration without a slot, correction/replacement claims, exact
correction provisioning, stale generation refusals, recovery and restart.

The claim override was compared with the base implementation: qualifications,
capabilities, dependencies, integration/Master ownership, slot kinds and scope
conflicts remain enforced. Independent review of the pre-response-correction
source found no lifecycle blocker. Its queue-history observation is retained as
a boundary below; the parent reviewed the final response-only delta.

## Boundaries and deployment

Frozen REVIEW means its submitted artifact and review fields remain frozen. An
inherited resource request can still append a refused/stale queue receipt; tests
verify it receives no runtime resource. The system is not a hostile-shell
sandbox: filesystem preservation, stopped writers and remote PR verification
are trusted broker observations, not effects of changing controller metadata.

The new operation is supervisor-only. Workers keep using their own session and
the existing client envelope. No worker receives supervisor credentials.

The current live service uses an older base controller than the integrated
reference. A bounded transition must stage the reviewed service/extension over
that exact old controller and layout, preserve persistent identity/state, and
verify assignments after restart. The already reviewed resource patch and the
pending catalogue PR are separate deployment work. No live deployment is
claimed by this predeployment report.
