# THE_DYAD_PROTOCOL.md — the standing eye loop

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
