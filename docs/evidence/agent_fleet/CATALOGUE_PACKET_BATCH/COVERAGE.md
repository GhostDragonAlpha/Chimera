# COVERAGE — catalogue-packet-batch-01

Catalogue digest: `b9d32319b43a03bbb713f1a4e6120f24065839f15383b0729fb587ba04f9000a` (imported_revision 651, epoch 5). Derivation: deterministic sorted-frontier expansion (catalogue_next semantics: PROPOSED, not realized live, all depends_on INTEGRATED), first 12 pops; replay retained at `checks/p1_batch_replay.txt`.

Eligibility truth at drafting time: `catalogue_next` returned exactly ["GOV-01"]; every other card below is BLOCKED-ON until its card dependencies are INTEGRATED live tasks. Drafts are PLANNING DATA — NOT ADMITTED.

| # | card id | draft file | proposed task id | card depends_on | live deps (draft ids) | eligibility at drafting time |
|---|---------|-----------|------------------|-----------------|----------------------|------------------------------|
| 1 | GOV-01 | drafts/DRAFT-holodeck-gov-01.md | `holodeck-gov-01` | [] | none | ELIGIBLE NOW |
| 2 | GOV-02 | drafts/DRAFT-holodeck-gov-02.md | `holodeck-gov-02` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 3 | GOV-03 | drafts/DRAFT-holodeck-gov-03.md | `holodeck-gov-03` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 4 | GOV-04 | drafts/DRAFT-holodeck-gov-04.md | `holodeck-gov-04` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 5 | GOV-05 | drafts/DRAFT-holodeck-gov-05.md | `holodeck-gov-05` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 6 | GOV-06 | drafts/DRAFT-holodeck-gov-06.md | `holodeck-gov-06` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 7 | MATH-01 | drafts/DRAFT-holodeck-math-01.md | `holodeck-math-01` | ["GOV-01"] | `holodeck-gov-01` | BLOCKED-ON: GOV-01 |
| 8 | MAT-01 | drafts/DRAFT-holodeck-mat-01.md | `holodeck-mat-01` | ["MATH-01", "GOV-03"] | `holodeck-math-01`, `holodeck-gov-03` | BLOCKED-ON: MATH-01, GOV-03 |
| 9 | MAT-02 | drafts/DRAFT-holodeck-mat-02.md | `holodeck-mat-02` | ["MATH-01", "GOV-03", "MAT-01"] | `holodeck-math-01`, `holodeck-gov-03`, `holodeck-mat-01` | BLOCKED-ON: MATH-01, GOV-03, MAT-01 |
| 10 | MAT-03 | drafts/DRAFT-holodeck-mat-03.md | `holodeck-mat-03` | ["MATH-01", "GOV-03", "MAT-01"] | `holodeck-math-01`, `holodeck-gov-03`, `holodeck-mat-01` | BLOCKED-ON: MATH-01, GOV-03, MAT-01 |
| 11 | MAT-04 | drafts/DRAFT-holodeck-mat-04.md | `holodeck-mat-04` | ["MATH-01", "GOV-03", "MAT-01"] | `holodeck-math-01`, `holodeck-gov-03`, `holodeck-mat-01` | BLOCKED-ON: MATH-01, GOV-03, MAT-01 |
| 12 | MAT-05 | drafts/DRAFT-holodeck-mat-05.md | `holodeck-mat-05` | ["MATH-01", "GOV-03", "MAT-01"] | `holodeck-math-01`, `holodeck-gov-03`, `holodeck-mat-01` | BLOCKED-ON: MATH-01, GOV-03, MAT-01 |

Chain note for the lead: create_task refuses dependencies that do not exist yet. The batch is a chain: admit `holodeck-gov-01` first; GOV-02..GOV-06 and MATH-01 depend on it; MAT-01 depends on MATH-01 + GOV-03; MAT-02..MAT-05 additionally depend on `holodeck-mat-01`. Each admitted task runs its own prereg/measurement lifecycle; these drafts pre-authorize nothing.

P1 disclosure (falsifier fired, membrane lost, kept honestly): PREREG.md predicted the batch to be GOV-01..06 + MATH-01..06. The preregistered deterministic expansion instead yields GOV-01..06, MATH-01, then MAT-01..MAT-05 — MAT-01 (deps MATH-01+GOV-03) unlocks at pop 8 and sorts before MATH-02. This batch therefore drafts the procedure's ACTUAL output; MATH-02..06 raw reads are retained as orientation extras and are natural candidates for a later batch.

