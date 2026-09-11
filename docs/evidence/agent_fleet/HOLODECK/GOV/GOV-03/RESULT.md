# RESULT — holodeck-gov-03 "Law and decision records" (gen 1)

Agent: subagent-worker-09 (instance subagent-worker-09-a8960d274e14) · slot 4 ·
worktree E:\ChimeraWork\slot-04 · branch astra/tasks/holodeck-gov-03 · base
62b8e35757c71e31d621c26b32a7c52558905b02 (HEAD at claim, provision verified
HEAD==base, clean). CPU only; no GPU/model/engine process; no controller
resources; the live service at 127.0.0.1:8099 was NEVER contacted.

## SOURCE IDENTITY (the deployed contract, read-only reference text)

- tools/verdict.py, 241 lines, sha256
  0d13502dcda098c822355b38bad209df3a9367a9106cd49836e02f7cf2b8b68d
- tools/port_registry.py, 151 lines, sha256
  a061d42e7315a135517a40cf564c5963f3998646a68ba5519d457dce0d33923c
- tools/agent_fleet/control.py, 839 lines, sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30
- tools/agent_fleet/review_handoff.py, 228 lines, sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811
- All at git base 62b8e357. control.py and review_handoff.py hashes are
  byte-identical to GOV-01's measurements at d59518b9 (the files did not move
  between the two bases).

## DELIVERABLES

- `reference/gov03_reference_model.py` — independent, stdlib-only reference
  model of the INTENDED law/decision record contract: typed law records (the
  card's six kinds energy/force/flux/boundary/domain/parameter), admission
  gates with NAMED refusals (missing_falsifier, missing_constant_origin,
  missing_domain, missing_oracle, missing_limitations,
  oracle_not_independent, duplicate_law, bad_kind, dimension_mismatch),
  a no-eval/exec recursive-descent formula parser with a dimensional algebra
  over {M, L, T, Theta} (sums constrained to equal operand dimensions),
  versioned assumptions (append-only, version bumps), supersession, and a
  monotone decision ledger citing admitted ACTIVE laws with an evidence
  pointer and a fixed outcome vocabulary {ADOPT, REJECT, REVISE}.
- `controls/run_controls.py` — executes the preregistered R1-R4 in one
  process (bytecode writing disabled; no __pycache__ in the evidence tree).
- `controls/run_source_checks.py` — read-only R5/R6 measurements of the
  deployed text (quotes + occurrence counts; no service contact).
- `checks/r1_positive.txt` — R1 HOLDS 10/10 (8 core rows: six admissions, one
  per card kind, each with falsifier/domain/independent oracle/limitations/
  constants-with-origins/dimension-consistent formula, plus two legal
  decisions; 2 post-state rows: exactly 6 laws, exactly 2 decisions).
- `checks/r2_falsifier_lacking.txt` — R2 HOLDS 5/5: admission without
  falsifier and with whitespace-only falsifier both refused
  missing_falsifier; decision citing a never-admitted law refused
  law_not_admitted; decision without evidence refused missing_evidence;
  decision with out-of-vocabulary outcome refused bad_outcome — every refusal
  verbatim, every post-state byte-identical.
- `checks/r3_constant_origin.txt` — R3 HOLDS 6/6: constant with absent origin
  and with blank origin both refused missing_constant_origin; declared output
  dimension != composed dimension refused dimension_mismatch; self-oracle
  refused oracle_not_independent; duplicate name refused duplicate_law; kind
  outside the card's six refused bad_kind — verbatim, post-state identical.
- `checks/r4_law_fields_versioning.txt` — R4 HOLDS 36/36 (threshold 36): each
  of the six admitted laws names its domain, independent oracle, limitations,
  falsifier, and constants-each-with-origin (30 rows — the card prediction,
  field by field); amend bumps v1->v2 and preserves the v1 assumption
  verbatim (2); supersede marks the old law SUPERSEDED, still readable, with
  successor recorded, successor ACTIVE (2); a decision citing the superseded
  law is refused law_superseded with the ledger unchanged (1); decision
  numbering monotone (1).
- `checks/r5_source_trace.txt` — the card semantics traced into the DEPLOYED
  text: 5/5 present with exact quoted lines — statement+falsifier required at
  admission (port_registry.py:32-39, 61-62, 97-101); verdict close requires a
  nonempty evidence pointer (verdict.py:104-115); fixed result vocabulary
  (verdict.py:34, refusal :107-109); a missing record is a REFUSAL, not a
  smaller number (port_registry.py:140-151); a composition may only name
  already-registered parts (port_registry.py:50-78).
- `checks/r6_deployed_deltas.txt` — 14/14 measured counts equal the
  preregistered predictions (below).
- `PREREG.md` — committed FIRST (21452520), untouched since.

## PREDICTION SCOREBOARD (card prediction / prereg rows)

| row | prediction (fixed in PREREG before any run) | verdict |
|-----|---------------------------------------------|---------|
| R1 | model accepts 6 legal admissions + 2 legal decisions | HOLDS 10/10 (8 core + 2 post-state) |
| R2 | model refuses all 5 falsifier-lacking / unbacked decision paths | HOLDS 5/5 |
| R3 | model refuses all 6 constant-origin / integrity violation paths | HOLDS 6/6 |
| R4 | every admitted law names all 5 card parts; versioning + supersede + monotone decisions | HOLDS 36/36 |
| R5 | all 5 intended semantics present in the deployed text with quoted lines | HOLDS 5/5 |
| R6 | 12 marker counts == 0; owner_instance rh == 0, control == 9 | HOLDS 14/14 |

## CARD VERDICT (GOV-03 at catalogue digest b9d32319)

- CARD PREDICTION "Each admitted law names its domain, independent oracle and
  limitations": SUPPORTED by the intended contract — the reference model makes
  those fields REQUIRED at admission and R4 shows all six admitted laws expose
  all five named parts. The DEPLOYED registries enforce the RULE-0 pair
  (statement+falsifier) and the evidence-backed close, but carry NO domain,
  oracle, or limitations fields anywhere (R6: 0 occurrences of each marker in
  both port_registry.py and verdict.py) — the card's prediction describes the
  intended contract, and the deployed text realizes only its Rule-0 subset.
- CARD FALSIFIER "A physical claim lacks a falsifier or a constant lacks an
  origin": NOT reproduced by the intended contract — both admission paths are
  refused by name with byte-identical post-state (R2 5/5, R3 6/6). In the
  DEPLOYED text the falsifier half is enforced (port_registry.py:34-36 refuses
  a test with no falsifier; verdict.py:76-78 refuses a membrane with missing
  parts), while the constant-origin half has NO deployed enforcement (R6:
  \borigin\b occurs 0 times in both registries — a constant's origin is
  nowhere a required field).
- CARD MATHEMATICS "dimensional analysis; contracts; versioned assumptions":
  realized in the model (executed dimension algebra incl. same-dimension
  constraint on sums; named-refusal contracts; append-only assumption
  versions) and ABSENT in the deployed registries (R6: \bdimension\b 0,
  \bassumption\b 0 in both files).

## MEASURED DEVIATION (recorded finding, timestamped at 62b8e357)

The known live-claim regression (dispatch note; GOV-01 measured it at
d59518b9): the interceptor claim path binds {owner, slot, state, generation}
without owner_instance, so the intended per-instance fencing is inert on the
live claim path while instance_fencing=='compat'. Measured at THIS base:
owner_instance occurs 0 times in review_handoff.py and 9 times in
control.py — byte-identical files to GOV-01's base, so the deviation is still
present at 62b8e357; the fix (PR #80) is in review, not integrated. Per the
prereg, the reference model deliberately models the INTENDED contract and
this deviation is recorded, not adopted.

## PRE-VERDICT RUNNER/MODEL DEFECTS (disclosed; the fired runs were the
controls working as designed)

Method-note deviation, disclosed: the prereg's METHOD section aimed the model
at <300 lines; the delivered model is 358 lines. The R1-R6 rows are the
preregistered thresholds and all hold; the line budget was a method note, not
a verdict row, and the artifact was not churned after its controls ran to
cosmetically meet it.

The first execution of the controls FIRED (10/10 R1 failures, retained at the
time in checks/ before the re-run): the model's dimension tokenizer accepted
neither the caret power syntax nor negative exponents ("bad dimension
character '^'/'-'"), the formula tokenizer omitted the division slash and
rejected numeric literals, and decide() returned a bare string instead of the
named-refusal dict on missing evidence. Fixing the tokenizers surfaced a real
grammar defect — '*' and '+' shared one precedence level, so k*x + c*v_n
mis-parsed — fixed with the standard add/mul/pow tiering, which makes '+'/'-'
correctly require equal operand dimensions. After the fixes the whole suite
was re-run end-to-end in one process; the committed check files are exactly
that final run (R1 10/10, R2 5/5, R3 6/6, R4 36/36, R5 5/5, R6 14/14). Two
runner-side defects were also fixed before verdicts: the R4 supersede case
referenced a law not admitted in its fixture registry, and the R5(i)
presence assertion demanded two substrings on one line where the deployed
refusal spans two lines. No control output was edited after the fact; the
model's admission gates never changed semantics — the fired run failed on
tokenization, not on any gate the prereg pinned.

## DYAD RECORD

NOT_APPLICABLE — reference-only/source-only scope: no executed runtime
behavior of the deployed system was produced or altered; the deliverables are
a reference model, its in-process controls, and static source measurements.
Per the card's DYAD policy, reference-only scope records NOT_APPLICABLE with
this reason.

## REPRODUCTION

```
git -C <checkout> rev-parse 62b8e357            # base identity
cd docs/evidence/agent_fleet/HOLODECK/GOV/GOV-03
python controls/run_controls.py .               # rewrites checks/r1-r4
python controls/run_source_checks.py            # rewrites checks/r5, r6
python -c "import hashlib,sys; [print(f, hashlib.sha256(open(f,'rb').read()).hexdigest()) for f in ['tools/verdict.py','tools/port_registry.py','tools/agent_fleet/control.py','tools/agent_fleet/review_handoff.py']]"
```
R5 quotes can be re-derived with `sed -n '<line>p'` at the recorded line
numbers. Both runners set sys.dont_write_bytecode; no __pycache__ is produced.

## LIMITATIONS

- The reference model covers law/decision record semantics only (the card's
  statement scope); it does not model claims, resources, elections, or the
  catalogue plane.
- The dimension algebra covers multiplication, division, integer powers,
  sums with a same-dimension constraint, and dimensionless numeric literals;
  transcendental functions and non-integer powers are out of scope (refused
  as malformed, which is the conservative direction).
- R6 is a static textual measurement of one base revision; it does not
  observe the live service and makes no claim about the in-flight fix's
  content.
- Concurrency, persistence-to-disk, and multi-registry composition are out of
  the modeled scope; the GOV-01 lane holds the claim/CAS/persistence model.

## SHIP RECORD

- Commit chain: 21452520 (PREREG, first) -> artifact commit(s) -> pushed HEAD
  recorded in the controller submit_review event; PR into astra/gait-capture;
  pushed no-force.
- Files changed: docs/evidence/agent_fleet/HOLODECK/GOV/GOV-03/** only.
