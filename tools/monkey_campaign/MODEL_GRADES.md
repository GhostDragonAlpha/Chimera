# Shared model quality grades

Captain-authorized 2026-09-27. Rubric version 1. This is a project-local evaluation
of demonstrated work, not a universal intelligence ranking. Reuse normal review
evidence; do not create extra reviews or benchmarks just to obtain a grade.

## Where to look

Read `MODEL_SCORECARD.json` for current published grades and limitations, and
`MODEL_EVIDENCE.json` for the append-only case ledger. Every worker, Sergeant and
replacement Lieutenant uses these same records. When the Captain asks "model
grades", give the role/task-specific grade, sample size, confidence, limitations
and recommended use. Say UNRATED where attribution or evidence is insufficient.

The Captain reports a useful worker capability floor around models called
"Quinn 3.8 flash" and "GLM 5.3 flash". Those are operator-supplied labels, not
verified provider/model identifiers. This observation is recorded separately from
scored outcomes. Do not guess exact model IDs or assign historical attempts to them.

## Attribution before comparison

At dispatch, the Sergeant records the exact provider/model ID when available,
model revision, quantization for local models, reasoning configuration, harness,
context/compression mode and any model switch, alongside arrival, task, attempt and
role. An attested harness record is stronger than a model's self-description.
Unknown values remain null. Configuration changes form a separate cohort. Never
collect credentials, private prompts or unrelated operator data for this purpose.

Score one bounded work unit per task/attempt lineage and role. Revisions, tests,
reruns and review comments are not additional samples. Attribute reviewer work to
the reviewer and implementation to its author. Mark mixed-model work explicitly;
do not award the entire result to the model that wrote the final summary.

Compare cohorts within role AND work class (for example implementation/numerical,
implementation/UI, review/numerical, coordination, architecture). Do not collapse
different task difficulty or support levels into an unqualified global ranking.

## Fixed scoring anchors

An independent reviewer proposes scores using exact artifacts. The designated
Lieutenant adjudicates and publishes them, with their own identity recorded.
The same person need not remain Lieutenant: the rubric and evidence survive them.
No agent grades its own work as independent evidence. Captain overrides are recorded
as overrides with reasons, never disguised as measurements.

Each dimension is 0, 1 or 2. Attach a factual reason and evidence for each score.

| Dimension | Weight | 2 | 1 | 0 |
| --- | ---: | --- | --- | --- |
| Correctness | 35 | Meets assigned criteria on independent verification without substantive correction | Meets them after a substantive correction | Failed criteria, abandonment from attributable inability, or required replacement |
| Evidence accuracy | 25 | Claims, identities and limitations accurately match artifacts | Material reporting error caught and corrected before acceptance | Unsupported success, false identity/provenance or omitted material failure |
| Workflow completion | 20 | Correct ownership, checkpoint and required handoff | Recoverable workflow error requiring intervention | Ownership violation, lost work, or avoidably missing handoff despite capability |
| Recovery | 10 | Follows feedback correctly, or no avoidable correction needed | Needs repeated explanation of the same actionable finding | Repeats the failure or cannot recover within the authorized attempt |
| Rework burden | 10 | No avoidable corrective work by another agent/human | Bounded outside correction needed | Another agent must substantially replace the work |

Case score = sum(weight * dimension / 2). Score only terminal, attributable units.
A legitimate external blocker is not a model failure. If a unit cannot yet be
fairly scored, record it as pending or excluded with the reason; do not fill unknown
dimensions with zero. Difficult honest negative findings can score fully.

## Grade, confidence and trend

For each cohort, average its latest 20 eligible terminal units, or all if fewer.
Use the unrounded mean for thresholds: A >= 90, B >= 80, C >= 65, D >= 50, F < 50.
Always display the exact sample count and contributing case IDs/date range.

- No eligible units: UNRATED.
- 1-9 units: PROVISIONAL letter, low confidence.
- At least 10 units across 3 distinct tasks: established local grade, moderate
  confidence. Otherwise retain provisional status even if sample count is larger.
- Never label a project-local convenience sample universal or statistically certain.

With at least 10 units, compare the newest five against the preceding five within
the same cohort; show the numeric change. A drop of 10 points or two attributable
repeats of the same failure in the latest five triggers a lead review of placement.
Do not infer degradation merely because later tasks are harder; show task mix and
changes in context, tools and support before recommending a model change.

An evidence-integrity or destructive ownership incident gets an immediate visible
flag and scoped suitability review even if the average is high. An honest numerical
failure or correctly refused assignment is not an integrity incident. Restrictions
are lead decisions with evidence and scope, not automatic bans from a low score.

## Practical value and limitations

Alongside grades, report observed first-pass rate, accepted handoff rate, corrective
rounds and attributable intervention effort. Record active effort separately from
queue, GPU, credential or dependency waiting. Cost/tokens are null unless measured
from attributable usage. Use accepted work per dollar only for comparable work with
known costs; do not reward token consumption, verbosity or number of agents launched.

Each published cohort has suitable_work, limitations, recommended_supervision,
integrity_flags and unresolved_questions. Limitations describe demonstrated behavior
and scope, not a claim that a model can never learn or handle other work.

## Durable publication and correction

Ledger entries contain: case_id, cohort metadata and attribution evidence, task_id,
attempt/review identity, role, work_class, difficulty/support context, exact source
head and criteria hash, review/verdict references and artifact hashes, outcome,
blocker attribution, five scores with reasons, corrective rounds, measured effort/
cost if available, evaluator identity/date and rubric version. Corrections append a
new record with supersedes_case_id; preserve the original. Exclude superseded records
from rollups and explain changed grades. Never silently edit a bad result away.

Publish scorecard updates through normal reviewed repository changes to master;
keep raw private telemetry out of the public repo. Record a version/commit and
as_of timestamp. Workers may challenge a grade through the mailbox with task IDs
and counterevidence. Only the lead/Captain adjudicates; task gates still govern
acceptance regardless of a model's grade. Hashes detect changes, not secure identity
on a shared Windows account. Model grades grant no architectural or merge authority.

The lead checks new attributable outcomes during operator-triggered queue checks.
There is no background scoring loop. Missing model metadata should be requested
from the Sergeant in normal dispatch records; it must not block useful work or
become a reason to fabricate an identity.
