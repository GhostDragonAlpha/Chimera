# THE_DYAD_SUBAGENT_TEMPLATE.md — easy DYAD reviewer subagents

**Operator direction (2026-09-11, HUMAN feedback `d015187c`):** the DYAD
reviewer is *another agent asked the dyad questions and given the picture or
movie*. The subagent fleet runs GLM 5.3 Flash (vision) — operator-asserted —
and a subagent call is much faster than the local eye. The local
senses/LM Studio eye remains a legal provider class; nothing here removes it.

This template realizes the **SUBAGENT class** of the reviewed provider
interface (`tools/dyad_provider.py`, PR #44): every run goes through
`SubagentDyadProvider`, so the contract's named refusals, verdict building
(agreement is INCONCLUSIVE, never acceptance) and numeric-mention tagging
execute on the real path. A protocol run alone is never visual acceptance;
each lane's content-level acceptance is separately earned.

## The recipe (three commands + one spawn)

1. **Write the request spec** (JSON, non-leading questions, no
   expected-defect strings — the r7 law):
   ```json
   {
     "task": "<task-id>", "attempt": "<run-id>",
     "physical_context": "<what the image physically shows, camera, presentation>",
     "claim_under_exam": "<neutral statement of the claim being examined>",
     "questions": ["<numbered-neutral-question-1>", "..."],
     "captures": [{"index": 1, "path": "<absolute path to image>", "sha256": "<optional declared sha256; verified fail-closed when present>"}],
     "runtime_metadata": {"camera": "...", "state": "..."},
     "review_type": "still",
     "evidence_limits": "<single still; numbers are observations, not measurements>"
   }
   ```
   `still` = exactly ONE capture (the one-image law). `ordered_frames` = 2+
   captures the reviewer reads in order (declared temporal capability);
   `movie` additionally requires `runtime_metadata.movie_artifact`.
2. **Plan** (validates the request, records each capture's sha256 and — when
   the spec declares one — VERIFIES the file against that declaration,
   failing closed `capture_hash_mismatch` on any tamper; retains the exact
   prompt):
   ```bash
   python tools/dyad_subagent_template.py plan --spec <spec.json> \
       --evidence-root docs/evidence/agent_fleet/DYAD_SUBAGENT_TEMPLATE
   ```
3. **Spawn the DYAD subagent** with the template below; paste the exact
   prompt from `exact_prompt_<attempt>.txt` into the marked slot and list the
   capture path(s). Save the subagent's FINAL message verbatim to
   `subagent_report_<attempt>.txt` in the evidence root.
4. **Assemble** (parses the report through the reviewed provider; refuses by
   name on any malformation; retains the response JSON + dyad log append):
   ```bash
   python tools/dyad_subagent_template.py assemble --spec <spec.json> \
       --report <subagent_report_<attempt>.txt> \
       --evidence-root docs/evidence/agent_fleet/DYAD_SUBAGENT_TEMPLATE \
       --served "GLM 5.3 Flash (vision) [harness-declared, operator-asserted 2026-09-11]"
   ```

## The spawn template (copy-paste)

```text
You are a dedicated DYAD visual reviewer. Your only job: LOOK at the image
file(s) listed below with your Read tool, then answer the numbered questions
in the embedded DYAD request. You are not implementing, not merging, not
certifying anything. You have no stake in the work.

Rules:
- Read ONLY the listed image file(s); do not open the repository, code, or
  any other file. The images are the entire evidence.
- Report only what you can observe in the image(s). State uncertainty
  explicitly wherever it exists. Do not guess.
- Any number you mention is an observation to verify, never a measurement.
- Answer EVERY question with its number.
- If an image file cannot be read, say so as your RAW_RESPONSE and set
  CONCLUSION: unclear and FINISH: failed.

Image file(s) (in order):
<absolute-path-or-paths>

--- DYAD request (verbatim) ---
<exact contents of exact_prompt_<attempt>.txt>
--- end DYAD request ---

Your FINAL message must end with exactly this block, nothing after it:

===DYAD_REPORT===
RAW_RESPONSE:
<your full numbered answers, prose>
OBSERVATIONS:
- <one-line observation>
- <one-line observation>
UNCERTAINTY:
<what you could not resolve and why>
CONCLUSION: <supports | contradicts | unclear>
FINISH: <complete | truncated | failed>
===END===
```

## Laws carried by this template

- **Served identity is the harness declaration, never the model self-report.**
  `--served` records what the operator/lead asserted about the subagent fleet
  (currently GLM 5.3 Flash, vision); omitted → `None` + named uncertainty in
  the response. A model's claim about itself is not identity evidence.
- **Non-leading questions only.** The request builder refuses nothing here
  that prose smuggles in — the DISCIPLINE is yours: ask what it sees, never
  whether it sees what you expect (r7 contamination lesson, now law).
- **Resource accounting:** the subagent provider consumes no local GPU and no
  local model. The `dyad_eye` → `rtx4090` chained admission governs the LOCAL
  senses class only; using the subagent class neither bypasses nor widens it.
- **Evidence retention:** exact prompt (retained by `plan` before the spawn),
  the subagent's final message verbatim, the assembled `DyadResponse` JSON
  (exact prompt, raw response, capture identities + sha256, served-identity
  note, finish status, tagged numeric mentions, verdict), and the dyad log
  append. Verdict ceiling: INCONCLUSIVE. Acceptance is earned by the owning
  lane's gates, never by this review.

## Live demonstration

The lane's own evidence directory records the first live run through this
template (a retained EDGE-01 still): `docs/evidence/agent_fleet/
DYAD_SUBAGENT_TEMPLATE/` — request spec, exact prompt with sha256, verbatim
subagent report, assembled response JSON, dyad log. That run certifies the
provider path only.
