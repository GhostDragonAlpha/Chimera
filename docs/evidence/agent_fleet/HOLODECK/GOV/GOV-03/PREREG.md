# PREREG — holodeck-gov-03 "Law and decision records" (gen 1)

- Agent: subagent-worker-09 (instance subagent-worker-09-a8960d274e14). Slot 4,
  worktree E:\ChimeraWork\slot-04, branch astra/tasks/holodeck-gov-03, base
  62b8e35757c71e31d621c26b32a7c52558905b02 (HEAD==base verified, clean, before
  any work). Admitted from DRAFT-holodeck-gov-03.md (catalogue card GOV-03,
  digest b9d32319, content_sha256 2a29d31b...); dependency holodeck-gov-01
  INTEGRATED (pattern precedent PR #77, studied at this base).
- SOURCE-ONLY lane: the DEPLOYED contract is studied from source text at base
  (tools/verdict.py 241 lines, tools/port_registry.py 151 lines,
  tools/agent_fleet/control.py 839 lines sha 7cee259b...,
  tools/agent_fleet/review_handoff.py 228 lines sha ad3674bd...; full sha256
  table recorded in RESULT.md). The live service at 127.0.0.1:8099 is NEVER
  contacted. DYAD: NOT_APPLICABLE — reference-only/source-only scope produces
  no executed runtime behavior; reason recorded in RESULT.md per the card's
  DYAD policy.
- This commit contains the prereg ONLY. No reference model, no controls, no
  results.

## CARD MEMBRANE (quoted from the card / task packet)

- CARD STATEMENT: Energy, force, flux, boundary, domain and parameter records
- CARD PREDICTION: Each admitted law names its domain, independent oracle and
  limitations
- CARD FALSIFIER (named BEFORE the run, both for the reference model and the
  source trace): **A physical claim lacks a falsifier or a constant lacks an
  origin**
- CARD MATHEMATICS: dimensional analysis; contracts; versioned assumptions
- CARD THRESHOLD POLICY: derive the fixture-specific bound before
  implementation tests; preserve existing frozen gates; a catalogue prediction
  is not a preregistered numeric certificate. (The concrete thresholds are the
  R1-R6 rows below, fixed here before any implementation test.)

## REFERENCE MODEL CONTRACT (fixed before implementation)

A self-contained stdlib-only python module (`reference/gov03_reference_model.py`,
inside this evidence scope) implementing the INTENDED law/decision record
contract the card describes, NOT any deployed subset or deviation:

- LAW RECORD, typed by the card's six kinds: `kind` in
  {energy, force, flux, boundary, domain, parameter}. Required at admission:
  name (unique), kind, statement, falsifier (Rule 0), domain, oracle,
  limitations, constants (each {name, value, origin}), input dimensions, a
  formula over those inputs, and the declared output dimension. Versioned
  assumptions start at v1. Status starts ACTIVE.
- ADMISSION GATES (each refusal NAMED, none silent):
  missing_falsifier (absent or blank), missing_domain, missing_oracle,
  missing_limitations, missing_constant_origin (absent or blank origin on any
  constant), oracle_not_independent (oracle may not be the law's own name or
  statement — a law is not its own independent oracle), duplicate_law,
  bad_kind, dimension_mismatch (see the algebra below). A refused admission
  leaves the registry byte-identical (count, keys, versions).
- DIMENSIONAL ANALYSIS (card mathematics): a tiny dimension algebra over base
  dims {M, L, T, Theta} plus dimensionless. Dimensions compose by
  mul=add-exponents, div=subtract, integer powers only. The declared formula
  is parsed over the declared input dimensions with a small recursive-descent
  parser (tokens: symbols, `*`, `/`, `**`, parentheses; NO eval, NO exec);
  the composed dimension must equal the declared output dimension exactly,
  else the admission is refused `dimension_mismatch`.
- VERSIONED ASSUMPTIONS (card mathematics): `amend_law` appends an assumption
  and bumps the version (v1 -> v2 ...); prior assumptions are preserved
  immutably; no in-place mutation of history. `supersede_law(new, old)` marks
  old SUPERSEDED (still readable, pointer to successor retained) and admits
  new under the full admission gates.
- DECISION RECORDS: a monotone-numbered ledger (next = highest + 1; duplicate
  or backward numbers refused, mirroring verdict.py:81-85 semantics).
  `decide(law, outcome, evidence, rationale)` requires the cited law to be an
  ADMITTED, ACTIVE law (`law_not_admitted` / `law_superseded` otherwise), a
  nonempty evidence pointer (`missing_evidence`, the verdict.py close()
  semantics), and an outcome in {ADOPT, REJECT, REVISE} (`bad_outcome`, the
  verdict.py VALID_RESULTS vocabulary shape). Decisions are immutable once
  recorded.

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: each R row must reach its full N/N; any miss = the card
falsifier (or the row's prediction) FIRED for that row and the miss is
REPORTED verbatim, never patched around. If a fired row exposes a defect in
the MODEL or in my reading of the semantics, the model is fixed and the
correction is disclosed in RESULT.md with the fired run retained; the
DEPLOYED-source findings are never edited to match.

- R1 positive controls (model must ACCEPT) — N=8/8: six legal admissions, one
  per card kind (energy: E=m*v^2 -> M L^2 T^-2; force: F=m*a -> M L T^-2;
  flux: power per area P/(L^2) with P ~ M L^2 T^-3 -> M T^-3; boundary:
  pressure balance p=F/L^2 -> M L^-1 T^-2; domain: a length-scale law
  lambda = L^1; parameter: a dimensionless ratio, e.g. restitution with input
  dims cancelling), each with falsifier, domain, independent oracle,
  limitations, >=1 constant WITH origin, dimension-consistent formula; plus
  two legal decisions citing admitted active laws with evidence and valid
  outcomes.
- R2 the card falsifier clause 1 ("a physical claim lacks a falsifier") and
  its decision-side (model must REJECT) — N=5/5 named refusals with verbatim
  records and byte-identical post-state: (a) law admission without falsifier;
  (b) law admission with whitespace-only falsifier; (c) decision citing a law
  that was never admitted; (d) decision with empty evidence; (e) decision with
  an outcome outside the fixed vocabulary.
- R3 the card falsifier clause 2 ("a constant lacks an origin") plus
  integrity gates (model must REJECT) — N=6/6 named refusals with
  byte-identical post-state: (a) constant with absent origin; (b) constant
  with blank origin; (c) dimension_mismatch (declared output != composed);
  (d) oracle_not_independent; (e) duplicate_law; (f) bad_kind.
- R4 the card prediction ("each admitted law names its domain, independent
  oracle and limitations") plus versioning — N=36/36: for EACH of the six
  admitted laws, the stored record exposes all five named parts (domain,
  oracle, limitations, falsifier, constants-each-with-origin) = 30 assertions;
  plus versioned assumptions: after one amend, version==2 AND v1 assumption
  text byte-preserved (2); after supersede, old law still readable with status
  SUPERSEDED (2); decision citing the superseded law refused law_superseded
  with the decision ledger unchanged (1); decision numbering monotone across
  the R1/R4 decisions (1).
- R5 deployed-source trace (the card semantics judged against the DEPLOYED
  text at 62b8e357, quoted with exact file:line) — N=5/5 semantics present:
  (i) statement+falsifier admission refusal — port_registry.py:32-36 (and
  primitive copy :61-62; action three-part :97-101); (ii) close requires an
  evidence pointer — verdict.py:110-112; (iii) fixed outcome vocabulary —
  verdict.py:34 + refusal :109; (iv) count-assertion refusal (a missing
  record is a REFUSAL, not a smaller number) — port_registry.py:146-151;
  (v) composition requires already-registered parts — port_registry.py:66-70.
- R6 measured deltas (predicted BEFORE the retained measurement; any miss is
  a disclosed surprise, never reconciled) — N=14/14 rows match:
  - The deployed registries lack the card's law-record fields. Predicted
    word-boundary, casefold occurrence counts in BOTH tools/port_registry.py
    and tools/verdict.py, each == 0: "domain", "oracle", "limitation",
    "origin", "dimension", "assumption" (12 rows). Reading basis: full read of
    port_registry.py (151 lines) and verdict.py:1-180 (the remainder is the
    argparse tail); a nonzero anywhere in either file is a MISSED prediction
    and is reported.
  - Known-regression timestamp at THIS base (dispatch: live claim path drops
    owner_instance; fix PR #80 in review — model the INTENDED, record the
    deviation): predicted word-count owner_instance in
    tools/agent_fleet/review_handoff.py == 0 and in
    tools/agent_fleet/control.py == 9 (2 rows; GOV-01 measured the same
    0/9 at d59518b9; control.py sha is unchanged between the bases, so any
    difference is a surprise finding).

## METHOD

1. Write the reference model (evidence-scoped, stdlib-only, <300 lines, no
   eval/exec; bytecode writing disabled in the runner so no __pycache__ is
   committed).
2. `controls/run_controls.py` executes R1-R4 against the model in one process
   and writes `checks/r1_positive.txt`, `checks/r2_falsifier_lacking.txt`,
   `checks/r3_constant_origin.txt`, `checks/r4_law_fields_versioning.txt`
   (every refusal verbatim, every post-state assertion listed).
3. R5/R6 measured from the source text at base by a read-only check:
   `checks/r5_source_trace.txt` (quoted lines), `checks/r6_deployed_deltas.txt`
   (occurrence counts with the exact regex stated).
4. RESULT.md: scoreboard, card verdict, reproduction commands, source identity
   (git base sha + per-file sha256), limitations, DYAD NOT_APPLICABLE record.
5. Commit chain on astra/tasks/holodeck-gov-03 (trailer
   `Agent: subagent-worker-09`), push no-force, PR into astra/gait-capture,
   submit_review with exact HEAD.
