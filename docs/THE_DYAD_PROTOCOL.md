# THE_DYAD_PROTOCOL.md — the standing eye loop

> **Current operator selection (2026-09-10):** DYAD permanently uses
> `qwen3.8-27b-nvfp4-mtp`, bound to
> `C:\Users\allen\.lmstudio\models\esatapedico\Qwen3.8-27B-NVFP4-MTP-GGUF\Qwen3.8-27B-NVFP4-MTP-VERY-LOW.gguf`.
> This supersedes the historical auto-follow model instructions below for
> DYAD. The persistent policy lives in `ChimeraEngine/dyad_model_policy.json`.
> Selection, local artifact identity, loaded instance, and response-reported
> identity are separate facts. Missing or different response identity is a
> failed observation, never permission to silently substitute another model.
> Preserve resource admission, the fair inference queue, one image per call,
> UTF-8 logging, and the operator's existing load/context settings. This
> selection does not change non-DYAD text-client routing. Recorded identity
> and verification evidence: `docs/evidence/dyad_model_policy/`.

<!-- THE LOOP, CODIFIED 2026-09-03 after four verified rounds (see
     docs/THE_ENGINE_STUDIO.md, "the loaded review" chain). The dyad is the
     resident vision model (Qwen3 32B NVFP-MTP, LM Studio, ~23.3 GB VRAM).
     It sees ONLY what this protocol hands it: one screenshot per call plus
     the briefing in the prompt. It has no file access, no repo access, no
     memory between calls. -->

## THE TWO LENSES — neither alone is sufficient

- **The dyad (meaning):** reads screenshots and returns prose verdicts. Catches
  what pixel math cannot: "reads as broken", "the header lies", "unfinished".
- **Measurement (arithmetic):** pixel band scans, region fractions, endpoint
  parity. Twice in round one this REVERSED the dyad's diagnosis: its "dead
  black zones" were panel background (content drought), not layout geometry.
  Fix the thing measurement says is real; use the dyad to find it and to
  confirm the fix reads.

## THE LOOP

1. **ORIENT** — capture evidence: `/glass` (window restored; minimized windows
   have no present), `/frame`, endpoint state JSONs, under `Saved/dyad/<ts>/`.
2. **BRIEF-ME-FIRST** — every round's prompt carries the accumulated defect
   list and what was already fixed. The loop got sharper each round once the
   dyad judged against its own history. Never send a cold prompt.
3. **ASK STRUCTURED, NEVER LEADING** — numbered questions, demand numbered
   answers, name the single worst item. Vague prompts get vague critique. But
   do NOT name the defect strings you expect (r6: I primed it with
   `JOIN _` / `repo_` and it obligingly "found" them in pure-ASCII source —
   the report was contamination, not observation). Ask what it sees, not
   whether it sees what you expect.
4. **MEASURE BEFORE FIXING** — turn each critique into a number (band count,
   content fraction, parity check). If measurement contradicts the prose,
   believe the arithmetic and re-diagnose.
5. **FIX SMALLEST** — one defect per edit, Rule-0 statement/prediction/
   falsifier stated before the edit, build, measure.
6. **RE-JUDGE** — fresh `/glass`, dyad answers against the SAME questions.
   A fix is not a fix until the eye says it reads right AND the numbers agree.
7. **RECORD + PUSH** — verdict lines into `docs/THE_ENGINE_STUDIO.md` + master
   list, commit, push. The critique history accumulates; sessions inherit it.

## PARALLEL OPERATION (2026-09-03, operator decree)

Two agents work the repo at once; the operator runs a Bionic harness beside
them. Engine churn is a FACT OF LIFE, not an incident. The standing rules:

- **Never trust engine state — verify it.** Before any capture or judgment:
  `GET /state` + `GET /studio` (state object? mesh loaded?) + which port.
  A vanished creature mid-session is a PEER AT WORK (restart for a build),
  not a bug: reload `Saved/meshes/monkey_birth.bin` via `/mesh_bin` and move on.
- **Kill discipline.** Kill only PIDs you spawned, or verify ownership first
  (port + exe path + start time). Ports: 8090 operator/live, 8092 the dev
  loop, 8093 reserved for the local agent's isolated instances.
- **Binary identity.** Pin every verdict to an exe hash + spv hash (the
  stale-spv incident proves a clean build is not proof the right code runs).
- **Cooldown, not lock contention:** if a port is down, wait and re-probe;
  assume a peer is mid-swap. Never "fix" a down port by spawning a duplicate
  on the same port.

## MECHANICS (hard-won, do not relitigate)

- **ONE image per `senses.watch` call** (CHIMERA_SENSES_MAX_IMAGES=1; the
  resident model's context truncates silently otherwise). Loop, then aggregate.
- **`PYTHONIOENCODING=utf-8`** on every bridge/dyad invocation — the dyad
  emits typographic characters (‑, —) that kill cp1252 mid-print and lose the
  whole verdict.
- **The engine window must be shown** before `/glass` will serve a present;
  a minimized window answers `{"ok":false,"error":"no present"}`.
- **Test instance discipline:** Debug engine on port 8092 for the loop; the
  operator's live Release on 8090 is swapped only after a round is fully
  verified, and the creature (`Saved/meshes/monkey_birth.bin` via `/mesh_bin`)
  is reloaded immediately after every restart. The lane guard holds: never
  `/membrane_bin` over the creature.
- **Timeouts are disabled by operator decree** — the dyad is slow and the
  answer is worth the wait. Do not add timeouts to "fix" this.

## SCORECARD (running)

| Date | Round | Defects found | Fixed | Verified by |
|------|-------|---------------|-------|-------------|
| 2026-08-31 | empty-viewport review | 6 | 1,5,6 (by 09-03) | dyad + glass |
| 2026-09-03 | loaded review r1 | right dock 77% void | scene summary | bands 13→25, /scene parity, dyad |
| 2026-09-03 | r2 | faint scaffold, missing container lines | both | dyad r3 |
| 2026-09-03 | r3 | reel header [0/12] vs 6 slots | all 12 slots | dyad r4: "none reads as broken" |
| 2026-09-03 | r5–r8 | +cam ink, title margins (16→30, derived from the strip's vertical inset), timeline label overlap, scene-header clip, dope sheet drawing without a clock | all five | r7 caught my primed report (protocol hardened); r8: "layout is clean" |
| 2026-09-03 | render lane | GSQ RCO as eye (30.3s, sharp read): lighting now soft/symmetric; shadow detached from contact point; floor barely visible | lighting fix landed (mean 69.9→94.0, dim-band 0.290→0.085); floor/shadow membrane OPEN | pixel stats + GSQ read, same camera both sides |

**r7 lesson (law now):** a leading question manufactures findings. I named
`JOIN _` / `repo_` and the dyad obligingly "found" them in pure-ASCII source.
Ask what it sees; never ask whether it sees what you expect.

## OPEN (as of 2026-09-03, post r8)

- Render lane: one-sided lighting / near-black shadow side, shadow-direction
  mismatch vs ground plane, no visible floor (3D pass, not chrome)
- Viewport strut: a thin vertical line hangs from the creature's centre to the
  grid (r7) — helper axis or missing lower mesh; needs the 3D lane to identify
- Stage-strip ordering optics: B9 "done" after B8 "partial" (r7) — either the
  board's statuses are stale or "done" downstream of "partial" is legal; an
  operator call, not an editor one
- Empty-state spacing taste (the ONE OPEN TENSION above, still open)

## PROVIDER INTERFACE (2026-09-11, dyad-provider-interface-01)

A dedicated DYAD reviewer no longer assumes the local vision server is the only
executor. `tools/dyad_provider.py` declares the review contract separately from
the provider: a request carries task/attempt identity, physical/programming
context, the claim under examination, NON-LEADING questions, ordered capture
references with sha256 hashes, camera/runtime metadata, a review type
(`still` | `ordered_frames` | `movie`) and explicit evidence limits. Every
response retains the served provider/model identity where available (missing
identity is a named uncertainty, never a substitution), input capture
identities, the EXACT prompt, the raw response, finish status, observations
with uncertainty, and a structured verdict in which model agreement is
`INCONCLUSIVE` — never acceptance — and numeric mentions are tagged
`unverified_numeric_mention`, never manufactured into facts.

Providers declare capability (`no_vision` refuses everything; temporal ladder
`none` < `frames` < `movie`; a still-only provider refuses temporal claims by
name). Captures are hash-verified fail-closed (`capture_missing`,
`capture_hash_mismatch`). Adapter kinds — subagent callback (lead-delegated
reviewer), remote HTTPS service (auth via environment variable name, token
never stored), and the LOCAL SENSES/LM STUDIO EYE (retained, lazily imported,
one image per call remains the law; ordered frames are a call sequence) — are
selected by configuration with no silent fallback. CPU contract tests:
`tools/test_dyad_provider.py` (11 synthetic tests). ACTUAL VISUAL ACCEPTANCE
STAYS NOT_CLAIMED until a live provider run with retained evidence; a protocol
unit test alone is not visual acceptance.

## SUBAGENT PROVIDER TEMPLATE (2026-09-11, dyad-subagent-template-01)

Operator direction (HUMAN feedback `d015187c`, 2026-09-11): the DYAD reviewer
can be *another agent asked the dyad questions and given the picture or
movie* — the subagent fleet runs GLM 5.3 Flash (vision), faster than the
local eye; the local eye remains a legal provider class and is unchanged.

Easy creation lives in
[THE_DYAD_SUBAGENT_TEMPLATE.md](THE_DYAD_SUBAGENT_TEMPLATE.md): a request
spec, `tools/dyad_subagent_template.py plan` (validates the reviewed
contract, verifies capture sha256, retains the exact prompt), a copy-paste
spawn template for the reviewer subagent, and `assemble` which parses the
structured report through `SubagentDyadProvider` so the reviewed refusals,
verdict ceiling (agreement is INCONCLUSIVE, never acceptance) and
numeric-mention tagging execute on the real path. Served identity for this
class is the harness declaration (operator-asserted), never the model's
self-report. The subagent class consumes no local GPU/model; the
`dyad_eye` → `rtx4090` chain governs the local-senses class only.

First live run (retained): a still review of the EDGE-01 raised capture
through this template — request spec, exact prompt (sha256 retained), the
reviewer's verbatim report, the assembled response JSON and the dyad log are
in `docs/evidence/agent_fleet/DYAD_SUBAGENT_TEMPLATE/`. One fail-closed
refusal (`subagent_callback_malformed`, report-parse contract) fired on the
way and is retained there as correction history. The run certifies the
provider path only; content-level visual acceptance stays with each owning
lane's gates.
