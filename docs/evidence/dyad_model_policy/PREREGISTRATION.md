# Permanent DYAD model — 2026-09-10

Task `dyad-permanent-model-01`, root claim generation 1, provision revision 337.
Base: `accd15b61d7ac3805edfc36535ef99de121baf65`.

Alan explicitly selects permanently:
`C:\Users\allen\.lmstudio\models\esatapedico\Qwen3.8-27B-NVFP4-MTP-GGUF\Qwen3.8-27B-NVFP4-MTP-VERY-LOW.gguf`.
This current instruction supersedes older DYAD auto-follow instructions.

STATEMENT: a persistent project policy selects this exact DYAD artifact and
model identity; neither a stale Saved override nor gateway resident adoption
may silently send a DYAD request to another model. Text clients retain their
existing routing. Policy selection is not proof of the served model.

PREDICTION: LM Studio's local model index maps that exact relative filename to
`qwen3.8-27b-nvfp4-mtp`. Missing/contradictory policy, missing required loaded
identity, and missing/wrong response identity fail explicitly. A matching
response records its own identity. Policy persists without Saved files in a
fresh worktree. No model load, eviction or context change occurs in CPU tests.

FALSIFIERS, before implementation/tests: any request retargeted to another
resident model; an on-disk-only identity called resident; stale response
identity carried into a new failure; an override bypassing permanent policy;
text gateway state mutated; actual inference or model mutation in CPU tests;
actual selected filename/key not matching the index; a visual report without
image hashes, raw response, served identity and finish reason.

Targeted CPU command after implementation:
`python -m unittest tools.test_dyad_model_policy -v`.
Tests mock metadata and inference transport and exercise actual senses/CLI
paths, including wrong and missing identities and private gateway routing.
Normal commit hooks and `git diff --check` must pass before publication.

The local index and API are read-only observations. The operator has now
loaded the selected key with context 30208; preserve that configuration.
Actual can_see and one-image watch calls require controller GPU/eye admission.
Inference waits follow the current DYAD protocol; no replacement model,
reload, performance claim or fabricated acceptance is permitted.

The loaded-model API and local-index commands are documented by LM Studio:
https://lmstudio.ai/docs/developer/rest/list and
https://lmstudio.ai/docs/cli/local-models/load . File identity, configured key,
loaded instance and inference response remain separately recorded evidence.
