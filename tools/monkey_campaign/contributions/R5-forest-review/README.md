# R5-forest-review — corrected forest-front verdict (contribution)

Kanban card `R5-forest-review`, attempt `92f723834c64405aae3e8debabc65418`,
criteria `6198e40ba1cfe37059275bc908e55e1e4fa804d58d418bcc21ea8520e4753ae6`.
Responds to lead finding `msg-183cad37dbef420ea1122e84d6720cf6`.

## Contents

- `corrected_review.md` — the corrected verdict: F02/F03/F04 verified static only
  (native heightfield/trunk contact NOT established); F05/F06 explicitly NOT complete
  (never started, blocked on the walking chain); W10 NOT ready; original R5 findings
  preserved as static verification, none retracted; full source/receipt identities.
- `tools/measure_evidence.py` — reproduces every identity cited (13/13 checks).
- `evidence/identities.json` — machine-readable measured evidence
  (schema `r5.correction.evidence.v1`).

## Reproduce

```
python -B tools/monkey_campaign/contributions/R5-forest-review/tools/measure_evidence.py \
    E:/ChimeraWork/monkey-play-20260924 \
    tools/monkey_campaign/contributions/R5-forest-review/evidence
```

Read-only over the play worktree; CPU-only; no engine launch, no GPU, no threshold
changes. Re-runs re-measure hashes/counts; the original 70/70 R5 measurements are
preserved as authored, not re-executed.
