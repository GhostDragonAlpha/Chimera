# dyad_judge -- the blind judge and the dyad, ONE standing system

Operator directive 2026-09-14: *"Integrate the blind judge system in with the
dyad system."* Before this lane, blind judges were ad-hoc subagents following
`docs/evidence/agent_fleet/SHIP/R8_R4_PLAYBOOK/PLAYBOOK.md` by hand, and the
dyad machinery (senses eye, encode_movie, the verdict registry) ran separately.
This directory is the merge: **any lane can request a blind-judge dyad run with
one command**, the recording and verdicts flow into `tools/verdict_registry.json`
through `tools/verdict.py`'s own ledger law, and the $25 go-live gate reads
from the registry instead of from prose.

## THE ONE COMMAND

```bash
python tools/dyad_judge/run_judge.py --name <judge-name> [--base http://127.0.0.1:8206]
```

Phases, as a PIPELINE (never serialized -- see THE STANDING RULE below):

1. **PREPARE** -- fresh session dir under
   `docs/evidence/agent_fleet/SHIP/DYAD_JUDGE/sessions/<name>_<ts>/`, env probe
   (demo reachable, ffmpeg, node), playwright staged into the session dir
   (copied from the repo's prior judge install; `npm i` only as fallback),
   registry backed up once, and the Rule-0 membrane **OPENED**:
   statement + prediction + falsifier, before anything runs. A membrane without
   all three is refused by `tools/verdict.py`'s own `new()`.
2. **SESSION** -- the playbook's headless Playwright driver (`judge_drive.js`,
   Appendix A verbatim + the rule-8 `keydown`/`keyup` extension) plays the
   page blind: landing -> self-taught entry -> >=3 lessons -> the press test
   (SPACE down, HOLD, keyup) -> free play -> quit. Every screen read and every
   click is in `resp.jsonl`; the buyer's truth is only ever what the page
   showed. The judge plays under a FRESH progress name (`<name>-<HHMMSS>`) so
   no earlier player's state is resumed or overwritten.
3. **DYAD WATCH** (overlapped) -- `eye.py` probes the standing senses eye
   (`senses.available()`; the permanent policy model must be loaded in LM
   Studio). If the eye is dark it tries the local Ollama server as a
   **clearly-labeled fallback lane** (`ollama-fallback`, not the permanent DYAD
   eye -- every report and registry entry names the lane that served), one
   image per call, `think:false`, num_ctx sized per frame exactly like senses'
   own ollama branch. If both are dark the lane is recorded `dark` and the
   semantic read is honestly skipped; the pixel read still measures.
4. **ENCODE** (overlapped) -- capture frames are ffmpeg-segmented as they land
   (`ChimeraEngine/cpp_bridge.py::encode_movie`, 16 frames per segment) and
   concatenated into `recording.mp4` -- the MOVIE the dyad watches, not a still.
5. **MEASURE** -- `eye.pixel_read`: mean |frame - baseline| in the creature box
   per capture frame; threshold derived from the pre-press baseline noise
   (mean + 6 sigma), giving dent-visible held frames and recovery time per
   recorded press. Not an eye -- the measured half of the dyadAnalysis.
6. **VERDICT** -- the blind judge's buyer verdict. The tool cannot spawn a
   fresh agent session from inside the pipeline, so the shipped shape is a
   **task-file handoff**: the tool writes `judge_task.md` (the exact briefing:
   read `resp.jsonl`'s screen reads and the shots AS A BUYER, write both
   `verdict.md` and machine-readable `verdict.json`), then waits
   (`--wait-verdict N`) for `verdict.json` to appear in the session dir. A lane
   that already holds a verdict passes `--verdict-file`; a verdict that arrives
   after the run ended is finished with `--late-register --session-dir <dir>`,
   which reads the OPEN membrane number from `run_state.json`.
7. **ALIGN + REGISTER** -- the dyadAnalysis: the NUMBER (judge novelty + the
   pixel metrics: dent-visible held frames, recovery ms, per-press table) and
   the TERM (the buyer term from the verdict quotes), plus the eye-vs-pixel
   alignment rate. The entry is written through `registry.py`, which calls
   `tools/verdict.py`'s `VerdictLedger.new/close/link` -- the SAME load,
   validate, number and save path the biomechanics lane uses. `close()` then
   checks every prediction clause mechanically: PASS / FALSIFIED / MARGINAL
   (MARGINAL reserved for "subjective clauses held but the measured half
   failed"). `python tools/verdict.py status` shows blind-judge verdicts
   WITHOUT any modification to verdict.py.
8. **REPORT** -- one-page `report.md` in the session dir + the registry entry
   path + the gate line.

## THE STANDING RULE: OVERLAP, NEVER SERIALIZE

Operator directive 2026-09-14: no serial single-threaded Python. Four workers
run concurrently, all logging intervals against ONE shared wall-clock epoch so
the overlap is MEASURED, not asserted (`timeline.jsonl`, `encode_log.jsonl`,
`watch_log.jsonl`; `overlap_report()` sums the pairwise intersections):

- **T_capture** (thread): timed screenshots every ~1.2 s through the playbook
  driver -- the recording accumulates WHILE the judge plays. Stops after two
  consecutive unanswered shots (a wedged or dead driver never answers again).
- **T_watch** (thread): reads key frames ONE IMAGE PER CALL while they are
  produced -- a drip early, then the live press window (hold + recovery) with
  priority. I/O-bound: belongs in a thread.
- **P_encode** (multiprocessing process): CPU-bound libx264 segments must not
  steal the GIL from the I/O threads, so the encode runs in its own process.
- **T_session** (main thread): the play script itself.

## HOW A LANE REQUESTS A RUN

```bash
python tools/dyad_judge/run_judge.py --name <judge-name> --wait-verdict 900
```

and spawn the judge agent pointed at the session's `judge_task.md` (or hand
the session dir to a human judge). The demo front door must be up:

```bash
python tools/game_shell/server.py 8206     # proxies to the engine; the tool
                                            # never starts or restarts servers
```

Gate check, any time:

```bash
python tools/dyad_judge/run_judge.py --gate-report
```

## THE $25 GATE

`docs/THE_SHIP_GOAL.md`: *"does this look worth paying for? The judge's
verdict is the gate."* That gate is now machine-readable:
`registry.gate25()` passes iff the **latest CLOSED lane=="blind-judge" verdict
carries `metrics.pay25 == true`**. The verdict that opens it must be a real
blind-judge run -- session dir, recording, eye lane and measured metrics ride
in the entry as provenance, so the gate's evidence is auditable.

## REGISTRY SCHEMA ADDITION (additive)

A blind-judge entry is a normal `tools/verdict_registry.json` verdict PLUS:
`lane`, `judge`, `judge_kind`, `session_dir`, `recording`, `eye`, `eye_reason`,
`metrics` {novelty, pay, pay25, dent_visible_frames, hold_frames, recovery_ms,
per_press, eye_reports, eye_dent_yes, eye_lane, lessons_completed, stalls},
`quotes`, `dyad_analysis` {number, term, alignment}, `date`.
`tools/verdict.py` reads a fixed key set and ignores the rest -- the ledger's
own law is untouched, and Rule 0 (no statement/prediction/falsifier, no
verdict) now governs judges exactly as it governs probes.

## FILES

- `run_judge.py` -- the pipeline CLI (phases, threads, process, align, report)
- `session_script.py` -- the blind-compliant play script (proven coordinates)
- `eye.py` -- the watch ladder: senses -> labeled ollama fallback -> dark;
  plus the pixel measure
- `registry.py` -- the live-state writer: backup, open/close through
  `tools/verdict.py`, `gate25()`
- `judge_drive.js` -- the playbook driver, verbatim + marked extension
