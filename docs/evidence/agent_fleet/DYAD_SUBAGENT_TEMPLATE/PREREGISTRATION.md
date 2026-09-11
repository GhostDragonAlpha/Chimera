# dyad-subagent-template-01 preregistration (2026-09-11, lead lane)

Task: `dyad-subagent-template-01` generation 1, slot 5, worktree
`E:\ChimeraWork\slot-05`, base `7e7d8466bb3ec88e5979168bcecea1fa50cb07a8`
(current integration tip). Operator direction recorded as HUMAN feedback
`d015187c` (2026-09-11): the DYAD reviewer is another agent asked the dyad
questions and given the picture/movie; subagents run GLM 5.3 Flash (vision);
the local eye remains optional; build a template for easy creation.

- **STATEMENT**: a lead-delegated vision subagent, given ONLY the reviewed
  `DyadReviewRequest` exact prompt and hash-verified captures, serves as the
  DYAD reviewer through `SubagentDyadProvider` (`tools/dyad_provider.py`) with
  fully retained evidence, without touching the local model, the `dyad_eye`
  resource chain, or any GPU resource.
- **PREDICTION**: the template driver validates a `still` request (exactly one
  capture, sha256 verified before the spawn); a subagent spawned from the
  copy-paste template reads the capture file and returns a structured report
  that parses into the callback 6-tuple (raw response, served-or-None, finish,
  observations, uncertainty, conclusion); the provider assembles a
  `DyadResponse` whose verdict status is at most INCONCLUSIVE with numeric
  mentions tagged `unverified_numeric_mention`; the exact prompt, raw
  response, capture identities and served-identity note are retained verbatim
  as evidence JSON plus a dyad log append.
- **FALSIFIER**: capture unreadable or hash-mismatched (named refusal fires);
  the report cannot be parsed into the callback contract
  (`subagent_callback_malformed`); any expected-defect string leaks into the
  questions (leading-question contamination); served identity fabricated from
  the model's self-report instead of the harness declaration; or evidence not
  retained verbatim.

Demonstration run plan (declared before any run): review type `still`, one
retained capture from the already-integrated EDGE-01 evidence
(`docs/evidence/membrane_gpu_demo_runtime/20260909T143821.177952Z/raised_gamma0.png`),
non-leading numbered questions about the visible fan/spoke structure with
explicit uncertainty demanded. The run certifies the PROVIDER PATH only; any
content-level physics/visual acceptance stays NOT_CLAIMED. No local model
load, no GPU claim, no engine process.
