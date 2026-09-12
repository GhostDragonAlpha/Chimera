# Ownership review preregistration

Snapshot: cf275281. Offline only, standard library, disposable temporary SQLite databases; original implementation and fixtures remain unchanged. No live service, network, Git writes, engine or Windows actions.

1. STATEMENT: enrollment-issued sessions cannot exercise supervisor authority. PREDICTION: registering the reserved-looking ID SUPERVISOR is accepted and its issued token can qualify itself and forge HUMAN feedback. FALSIFIER: enrollment is refused or supervisor operations reject this token. Negative control: ordinary enrolled ID is refused.
2. STATEMENT: election considers current spare task capacity. PREDICTION: a standby at max_tasks is elected over an eligible free standby. FALSIFIER: full standby is excluded and free standby elected. Rank ordering is policy; ranks distinguish choices, not a parameter sweep.
3. STATEMENT: recovery invalidates provisioning identity for reusable slots. PREDICTION: recover releases a provisioned slot without clearing its old head/attestation, then a different task inherits them and provision_slot refuses re-provisioning. FALSIFIER: successor has unprovisioned engine plan and accepts its own provisioning.
4. STATEMENT: recovery attestations are bound to the failed generation. PREDICTION: delayed first-generation recover payload is accepted on a second failure of the same task, clearing its newer hold. FALSIFIER: mismatched generation/owner is refused without mutation. No process-drain truth is simulated; test checks binding of the supplied stale attestation only.
5. STATEMENT: worker generation and revoked-session fences survive real transitions. PREDICTION: old worker generation after review_requeue is refused; failed session remains refused after controller restart. FALSIFIER: either old credential/context succeeds.

Prerecorded before creating/executing reproducer. Scope: control-plane behavior; no claim of filesystem or external publication containment.
