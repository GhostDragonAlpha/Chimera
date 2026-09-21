# THE LAW-DOC 5C APPEND PREREGISTRATION — the five-class taxonomy promoted into the law itself

Lane `agent/law-5c-append-20260921`, base `4ea008cb` (`agent/standing-pose-20260921`, whose base
is `52f101c1` — the class records). This is THE NAMED SUCCESSOR WORK: commit `52f101c1`'s message
records that "a law-doc section 5C append is successor work that must re-bank the stage hashes in
its own lane", and its lane's preregistration records why the law doc could not move then (the
committed p6_contrast hard-banks the stage-5B hash via `law_amendment_b_bank_matches_file`). This
lane moves the law doc and re-banks the stage hashes HERE, in its own lane, before any battery
runs. Banked BEFORE the append and BEFORE the battery re-runs. Bank file:
`preregistration.sha256`.

## 1. RULE 0 MEMBRANE

**STATEMENT.** The five-class joint taxonomy shipped at `52f101c1` as committed metadata with
teeth — ball_and_socket (2 hips, 3 DOF each), hinge_revolute (8 bonds, 1 DOF), condyled_gliding
(7 tarsal bonds, 1 DOF), syndesmosis_nodof (2, 0 DOF by cited absence), positional_contact (4,
0 DOF, flagged for anatomical review) — is LAW, not annotation, and the law document is its
missing canonical home: the law doc's own §3 wrote the joints-are-materials law and its §1.4
held the citations, but the class record that binds DOFs by citation lives only in the
definition's metadata and the class-records lane's documents. This lane appends §5C to
`docs/THE_ARTICULATION_LAW.md` stating the taxonomy, the DOF census (3×2 + 1×15 + 0×6), the
registered/prescribed pivot forms (sphere_fit REGISTERED on the hips; pin_axis PRESCRIBED per
the engine's 8-float hinge record and the held PinJoint records; none where no joint exists),
the cycle-B thin margin 0.040529146675 mm with its lawful consequence (band narrowing, never cut
widening), the positional_contact anatomical-review flag, and the falsifier-register addition
(the class-band admission law). The append is metadata-with-teeth prose: it changes ZERO
measurements, zero kernel/engine/definition bytes. Someone can disagree: the taxonomy could be
premature to promote before a second specimen or a driven pose exercises it — the answer is that
the standing-pose lane ALREADY enforced it (its falsifier F1 walked all 23 bonds' recorded bands
and fired the A5 refusal BY NAME past every moved band), so the records have teeth that bit
before this prose exists; the prose follows the enforcement, it does not outrun it.

**PREDICTIONS** (not yet measured at banking time).

- **P1 (byte scope).** The law doc's post-append bytes differ from the banked pre-append bytes
  (sha256 `97585c4e7b5781d3e776d7cdaa7b4d19ce8b33772f239178cbd60be7f6410e4c`) by EXACTLY one
  contiguous inserted block — the §5C section and its separator, inserted immediately before the
  committed `## 6.` heading — so `post == pre[:i] + INSERT + pre[i:]` for one i; every
  pre-existing byte preserved, every line of §5/§5A/§5B byte-identical, everything after the
  insertion point byte-identical.
- **P2 (the three batteries re-run green, verdicts identical, echo-only diffs).** Per the
  `52f101c1` precedent: hip_pivot_proof (A1–A6), p6_contrast (P6′ v2, real PASS / null FAIL both
  hips), tarsal_cycle_battery (all six bonds discriminate; the loop closes on both cycles) each
  exit 0 with `hard_checks_pass` TRUE and every verdict/measurement leaf BYTE-IDENTICAL to its
  committed `battery.json`; the ONLY differing leaves are sha256-ECHO leaves whose values copy a
  watched or banked file's bytes: (a) the law-doc sha256 in p6's and tarsal's untouched
  before/after watch maps and in p6's `banks.law_doc_sha256_this_stage` (old
  `97585c4e…` → post-append value); (b) p6's watch entry for its re-banked
  `law_amendment_b.sha256` stage bank; (c) the definition-sha256 echoes carried since the class
  records amended the definition (`95ddd280…` → `db412e0c…` in watch maps and runtime-computed
  input leaves); (d) tarsal's watch entries for the re-banked hip and p6 `battery.json` files.
  Any leaf that is NOT a copy of a watched/banked file's hash and differs → falsifier F1, STOP.
- **P3 (determinism).** Each regenerated `battery.json` is byte-identical on an immediate
  second run (the tarsal and class-records lanes' twice-byte-identical precedent).
- **P4 (gates).** test_definition 9/9 OK; test_glue 8/8 OK; training_gate PASS.

**FALSIFIERS** (named before the run; any one voids the append as written).

- **F1** any battery's verdict or measurement leaf differs from the committed file beyond the
  P2 echo set (any verdict flip, any number moved, `hard_checks_pass` FALSE, any non-zero
  exit) → the prose append changed a measurement → VOID; the lane STOPS and reports the fired
  falsifier.
- **F2** any pre-existing law-doc byte changes (P1 fails: a 5/5A/5B line edited, a reflow, a
  re-wrap) → the append is not an append → VOID.
- **F3** any watched byte drifts WITHIN a battery run (`untouched.equal` FALSE anywhere) → VOID.
- **F4** any kernel gate red (test_definition, test_glue, training_gate) → VOID.
- **F5** a regenerated `battery.json` differs between its two runs → VOID.

## 2. THE RE-BANK PLAN (declared before the runs; this is the 52f101c1-named work)

1. Append §5C to `docs/THE_ARTICULATION_LAW.md` (P1's single inserted block).
2. Re-bank `p6_repreregistration_20260921/law_amendment_b.sha256` — the STAGE-HASH bank — from
   the stage-5B value `97585c4e…` to the post-append law hash, so the committed tree keeps
   `law_amendment_b_bank_matches_file` TRUE. The stage-5A bank (`law_amendment.sha256`,
   `e18d46ca…`) is historical and hard-pinned against run-1's stage in the committed script; it
   does not move. The superseded stage-5B value remains in the record: git history at `4ea008cb`,
   and this lane's `receipt.json`.
3. RUN ORDER p6 → hip → tarsal, forced by p6's committed parent pin
   (`PRIOB_BATTERY_SHA = 18f0ef06…`): p6 must observe the hip battery's committed bytes, so p6
   runs before the hip battery is re-banked. Tarsal watches hip's and p6's battery files
   within-run only (no pinned constant), so it runs last. Each battery runs twice (P3).
4. The three regenerated `battery.json` files are RE-BANKED — committed with their new echo
   hashes. (The `52f101c1` lane restored the committed bytes; its message names THIS lane as the
   one that re-banks in its own right.) The historical bytes remain at `4ea008cb` in git
   history. Recorded consequence, in the open: after this lane, p6's committed parent pin
   `18f0ef06…` refers to the hip battery bytes AT THE BASE, not at HEAD — a future p6 re-run
   against HEAD's re-banked hip battery must manage that pin in its own lane, exactly as this
   lane managed the stage-hash re-bank in its own.
5. This lane's `receipt.json` (schema `chimera.rule0_receipt.v1`) records: law-doc pre/post
   sha256, stage-bank old/new, per-battery leaf-level diffs with the echo classification, the
   determinism results, and the gate lines. The committed `receipt.json` files of every prior
   lane are read, never written; the batteries' own `receipt.json` files are untouched — only
   the three `battery.json` files and the one stage-hash bank are re-banked.

## 3. SCOPE AND DISCIPLINE

This lane writes ONLY: `docs/THE_ARTICULATION_LAW.md` (one appended section),
`p6_repreregistration_20260921/law_amendment_b.sha256` (the stage-hash re-bank),
`p6_repreregistration_20260921/battery.json`, `hip_pivot_proof_20260921/battery.json`,
`tarsal_cycle_pivots_20260921/battery.json` (the three re-banked batteries), and its own
directory under `tools/science_funnel/validation/law_doc_5c_append_20260921/`. The kernel, the
engine, the definition, the tris bins, every prior lane's receipts/preregistrations/scripts, the
three osim records: READ-ONLY, ZERO bytes changed.

Banked by: lane `agent/law-5c-append-20260921`. Trailer: `Agent: GLM 5.3`.
