# DYAD_JUDGE — the blind judge merged into the dyad system (D1, 2026-09-14)

Operator directive: *"Integrate the blind judge system in with the dyad
system."* Shipped: `tools/dyad_judge/` — one command
(`python tools/dyad_judge/run_judge.py --name <judge>`) runs the R8/R4
playbook session headless, records it, watches it with the standing dyad
machinery, takes the blind verdict, and registers the dyadAnalysis in
`tools/verdict_registry.json` through `tools/verdict.py`'s own ledger law.
Full architecture: `tools/dyad_judge/README.md`.

## THE DRY RUN (what actually happened)

Three runs against the live demo on 8206. The first two are honest pipeline
defects, registered as MARGINAL membranes (a defect that voids a measurement
is recorded, not spun); the third is the clean end-to-end run.

| run | session | membrane | outcome |
|---|---|---|---|
| 1 | `sessions/D1-dryrun_20260914_223515` | V63 MARGINAL | `Session.send` matched response lines with BYTE offsets sliced from DECODED text; the landing text carries an em-dash, byte size > char length, the reader went blind at the first click. Fixed (bytes sliced from bytes). |
| 2 | `sessions/D1-dryrun_20260914_223911` | V64 MARGINAL | Session played clean (56 frames, 11 eye reads, recording) but (a) lesson/free-play presses clobbered the S4 press window and (b) T_capture spammed the closed driver 6 min because its stop latch matched only the literal word TIMEOUT. Both fixed (witnessed-press windows; stop after 2 consecutive failures). |
| 3 | `sessions/D1-dryrun_20260914_225117` | **V65 FALSIFIED** | Clean end-to-end: PLAY -> register in one command. |

## RUN 3 = V65, the dry run of record

- **Membrane** (opened BEFORE the run, Rule 0): statement "blind-judge dyad
  [D1-dryrun]: a buyer-judge ... witnesses an answered press -- a visible dent
  on held frames and calm recovery after release -- and delivers buyer
  pay-intent"; prediction "novelty >= 8/10 AND dent_visible_frames >= 2 AND
  recovery-to-calm <= 10000 ms AND pay25 == True"; falsifier names every clause.
- **Session**: landing -> PLAY as camera `D1-dryrun-225126` (fresh progress
  namespace) -> lessons 1-3 (L1 PASSED, L2 stalled — the hand-strength slider
  is inoperable headless, the page's own known defect, reproduced; L3 PASSED)
  -> S4 press-hold-release-recover (cell 1 reached 0.479 MPa mid-hold) ->
  free play -> quit. 56 timed capture frames, 19 named evidence shots.
- **Measured half (pixel read, per press)**: best press shows dent-visible on
  2/2 held frames, recovery 4370 ms, peak frame-delta 0.0106; the per-press
  table (5 presses) is in the registry entry. The witnessed S4 press measured
  0/2 — the box-wide metric is dominated by pose motion; known limitation,
  recorded honestly.
- **Eye**: senses eye DARK (permanent DYAD model `qwen3.8-27b-nvfp4-mtp` not
  loaded in LM Studio — recorded with reason); the clearly-labeled
  `ollama-fallback` lane (qwen3.8:latest, one image per call, think:false)
  served 8 reads inside the session, one dent-yes ("the creature's torso is
  visibly squashed/compressed" on the frame the pixel read also flags).
  Eye-vs-pixel alignment 0.375 — low, honestly recorded: the eye misreads the
  small HUD digits and the pixel box counts pose motion as signal.
- **Verdict** (D1 as judge-of-record; honesty note in `verdict.json`: NOT
  blind — fleet agent; proves the PIPELINE, not the market): novelty 8/10,
  pay no, pay25 no, term **"honest hydraulic touch"**.
- **Close**: clauses novelty 8>=8 PASS, dent 2>=2 PASS, recovery 4370<=10000
  PASS, pay25 false != True FAIL -> **FALSIFIED**, mechanically derived, no
  spin. Consistent with R8 STRANGER (both judges NO) and R8/R4 judges 1-2.
- **Overlap (measured, one shared wall-clock epoch)**: session span 190.7s;
  encode 4/4 segments INSIDE the session (0.9s of ffmpeg work — libx264 is
  simply fast at 16-frame segments); watch 8/8 reads INSIDE the session
  (24.7s of eye time). `timeline.jsonl` + `encode_log.jsonl` +
  `watch_log.jsonl` carry every interval.
- **Recording**: `recording.mp4` (1.5 MB, real-time 0.83 fps from the timed
  captures) — the dyad watched a MOVIE, not a still.

## REGISTRY + GATE

- `tools/verdict_registry.json` gained V63/V64/V65 (lane `blind-judge`), every
  write through `registry.py` -> `tools/verdict.py`'s `VerdictLedger`.
  Pre-integration backup: `verdict_registry.pre_dyad_judge.json` (created by
  the tool before its first write, never overwritten).
- `python tools/verdict.py status` shows all three WITHOUT modification.
- The $25 gate is now machine-readable:
  `python tools/dyad_judge/run_judge.py --gate-report` →
  `GATE: OPEN (latest CLOSED blind-judge verdict must carry metrics.pay25 ==
  true)` — currently V65, pay25=False. The gate reads from the registry, not
  from prose.

## HOW THE NEXT LANE USES IT

```bash
python tools/game_shell/server.py 8206            # front door (was down; started for the dry run, left serving)
python tools/dyad_judge/run_judge.py --name <judge> --wait-verdict 900
# spawn the judge agent on the session's judge_task.md, or pass --verdict-file
python tools/dyad_judge/run_judge.py --gate-report
```
