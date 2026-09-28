# PREREGISTRATION — MAT2-A04 reconciliation of the merged hand-assembly identity and palm-orientation evidence (anatomy profile)

Card `MAT2-A04` (planning `A04`, verification profile `anatomy`, kind **visible_static**),
attempt `31c8beb654664b6d8e28280e38f7c0d6`, agent `arrival-73c48ff5c55146f1ad7ff5231213ec6c`,
criteria `b6a4bb30f1bfe207c76969f2eebfd736d33360546d1d0522bae8e29860a1bf3d`, scope
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`, candidate base
`8ec90f13` (`origin/astra/gait-capture`, work branch `work-a04-reconcile`, isolated
attempt checkout). Written and frozen **before** any re-verification run of this
attempt. Every predicted identity below is cited from already-merged, lead-accepted
receipts (reconcile phase read them; nothing was re-measured before this freeze).

## RECONCILE — what exists and is reused (never re-implemented)

- **Clause identity:** the MAT2-A04 `done_when` — "Source and target assembly
  correspondence is evidenced, including palm sign and geometry coverage" — is the
  same clause, with the same definition (`57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`),
  the same calculation contracts (`C01`, `C16`) and the same profile (`anatomy`,
  `visible_static`) that the merged **ONT-A04** winner qualified. The only changed
  inputs are campaign-era bookkeeping fields (scope `01ea5cdd…` → `cb5475f8…`,
  card criteria `bf8583ae…` → `b6a4bb30…`).
- **Merged evidence (accepted):** PR #177 head `020c0a5c216a4182d0bed9c4ade59cb0beb585ad`,
  merged as `56d0116a` into `astra/gait-capture`; lead ACCEPTED review
  `6e27829fa06c44cc92907bb5fa0273c8` with `done_when_verified: true`,
  `profile_verified: true`. In-tree at this base under
  `tools/monkey_campaign/contributions/ONT-A04/`.
- **Dependency:** `P02` DONE — MAT2-P02 merged (PR #196, tip parent of this base);
  its lineage map inherits the ONT-P02 authority (`8c7ed8c2`).
- **Honest gates carried by the merged work (still open, still named):**
  target palm sign UNRESOLVED (the human A/B labeling verdict of the ±T_R face
  instrument; operator decision artifact prepared and hash-verified at
  `E:/ChimeraWork/monkey-coordination/review-workspaces/labeling_gate_ER/gate_artifact/`);
  H-LEN/H-ASP UNRESOLVED; H-BODY REJECTED circular; 14 phalanges NOT covered;
  no scale promoted; no runtime/native claim.

## What this attempt builds (and the only work it builds)

A **reconciliation deliverable** under `tools/monkey_campaign/contributions/MAT2-A04/`:
(i) clause-to-evidence map binding each part of the done_when clause to the merged
artifacts by hash; (ii) scoped CPU-only re-verification of the merged numerical leg,
test suite and capture determinism at this base; (iii) the campaign-schema manifests
for this card — a `chimera.qualification_receipt.v1` (kind `reconcile`) and a
planning-envelope `card_task.json` with `task_id: "A04"` under the current scope,
carrying the `C01`/`C16` calculation contracts; (iv) a recorded **decision request**
for the genuinely missing operator decision (target palm face A/B), addressed to the
lead/operator — **never answered here**. No new anatomy, no new measurement code, no
constants authored, no edits to the merged ONT-A04 tree.

## FROZEN PREDICTIONS (each cited from the merged receipts; any miss is recorded FIRED)

- **P1 pin integrity:** the in-tree ONT-A04 files byte-match the accepted head pins —
  `a04_correspondence_probe.py` `8e36aa2fb2c8ebda791d97ef6b91fd23b619d48392da12cdfa156cdae7365669`;
  `evidence/capture_a04.png` `878eb3de68123bb6b82fc0c25b172b18be6346773d24ede8b4f5f24edc3685b2`;
  `evidence/capture_manifest.json` `4447058a4627d74779a5a8410408149d22077c93a4b213854cca32f062501224`;
  `evidence/capture_receipt.json` `7473143820d6e185fb2f3d68cfc98f7c6792021fe551df79c82aa8180cd118e8`;
  `evidence/numerical_receipt.json` `e3864b161c865a404b0b2d0e73cce2a76e479bcf3c29c42c86c54d84c5db5fa1`;
  `evidence/state_snapshot.json` `33d3219cc66071a7a5957b24f40f172accbada2ac8ec69c9de5e060de74b1164`;
  `qualification_receipt.json` `726efaf8a7630c7df7fd108064dd1daf2386e1bfa82f5286ddb591126601d9c4`.
- **P2 numerical probe rerun (scratch copy, CPU-only `python -B`):**
  `a04_correspondence_probe.py` exits 0 with `all_green=True`, exactly **2** FIRED
  deviations (the two merged-record deviations: C4 s2 site-metric convention within
  the 3.5 mm anchor class; C5 far-end 18.04 vs printed 18.1 mm), and regenerates
  `numerical_receipt.json` / `state_snapshot.json` **byte-identical** to
  `e3864b16…` / `33d3219c…`.
- **P3 test suite rerun:** `python -B -m unittest test_ont_a04` → **19/19 OK**.
- **P4 capture determinism rerun (scratch copy):** `capture_build.py` regenerates
  `capture_a04.png` byte-identical to `878eb3de…` and `capture_manifest.json`
  byte-identical to `4447058a…` (capture_receipt may differ only in absolute-path
  strings, per the merged record); manifest `structurally_valid=True`, `fired=0`.
- **P5 manifest revalidation against the current-era envelope:** feeding the merged
  `capture_manifest.json` plus `visual_capture.validate_manifest` with context
  `task_id "A04"`, `subject_sha256 33d3219c…`, `capture_sha256 878eb3de…`,
  `tick_interval [0,0]` and the current `anatomy`/`visible_static` profile →
  `structurally_valid` True.
- **P6 operator gate state:** no human A/B palm-face verdict exists anywhere in the
  merged record (verified by the reconcile phase in-tree and in the labeling-gate
  workspace, whose own verification log shows 34/34 PASS for the *instrument*, with
  the ANSWER block unfilled) → the deliverable records a decision REQUEST; any
  recorded verdict claim without an operator receipt FAILS this card.

## FALSIFIERS (frozen; any firing is recorded, never retried into passing)

- **G-A (pin drift):** any P1 hash mismatch between the in-tree merged work and the
  accepted head → the reconciliation FAILS (the cited evidence is not what was accepted).
- **G-B (probe regression):** probe not `all_green=True`, a new deviation beyond the
  two recorded ones, or nonzero exit → FAILS.
- **G-C (numerical determinism):** regenerated `numerical_receipt.json` or
  `state_snapshot.json` not byte-identical → FAILS.
- **G-D (capture regression):** PNG/manifest not byte-identical, or
  `structurally_valid` not True → FAILS.
- **G-E (honesty inheritance, from card falsifier F-D):** any claim that the target
  palm face is decided, any scale number promoted, any digit-coverage overclaim, or
  any label ambiguity presented as resolved → FAILS.
- **G-F (gate forgery):** any A/B verdict recorded without an operator-authored
  receipt → FAILS; the decision request is the only lawful output of this attempt
  for that gate.

## SCOPE DISCIPLINE

CPU-only (`python -B`; no GPU/OpenGL/Vulkan/CUDA). All reads outside the attempt
workspace are read-only; ALL writes stay inside this attempt workspace. The merged
ONT-A04 tree is referenced read-only and not modified. Static inspection only — no
runtime/native claim; the runtime render and training bodies remain P02-kept-separate
lineages. Checkpoint-free per the profile's applicability boundary (offline
visible_static subject).
