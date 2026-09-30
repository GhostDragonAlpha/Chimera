# GPU queue protocol — repo-side banking amendment

Lane BANKING-ADOPTION, 2026-09-30. Tooling only: no card changes.

The operative GPU mailbox lives in coordination space
(`E:/ChimeraWork/gpu-queue/PROTOCOL.md`, Captain-ordered 2026-09-28): ONE
agent owns the GPU; every other lane submits bounded, non-interactive,
file-writing job JSONs to `incoming/` and never touches the GPU directly.
One job = ONE process; a job may not spawn further GPU processes; each job
writes its outputs to files and the queue records
`done/<id>.result.json` (exit code, stdout tail, sha256 per output,
duration) or `failed/<id>.result.json`. NEW job id per resubmit;
forward-slash JSONs.

This file lands the CERTIFIED BANKING MODES into the repo toolchain so card
lanes compose bank jobs against one documented law instead of re-deriving
it. Nothing above changes; this constrains how bank jobs are shaped.

## Banking modes (certified, M08 kernel set + this host/driver)

Source receipts: queue jobs `ta-batch-d/f/g/h/i-20260929` in
`E:/ChimeraWork/gpu-queue/done/`, fixture family + GREEN certificate in
`E:/ChimeraWork/monkey-coordination/test-acceleration-b/scratch/`
(`certify_disjoint_receipt.json`: C0-C3 and A1/A2 all true; the certificate
is never weakened). Three globally-disjoint clean fixtures, 6 ticks,
ambient GPU load recorded pre/post both arms (nvidia-smi preflight).

| arm | one job = | wall_s | speedup vs fresh-process | queue jobs |
|-----|-----------|--------|--------------------------|------------|
| baseline | 1 fresh process per fixture | 5.945 + 6.701 + 6.003 = 18.649 | 1.00x (status quo) | ta-batch-g/h/i-20260929 |
| sequential (DEFAULT) | 1 process, fixtures one after another | 7.475 | 2.50x | ta-batch-d-20260929 |
| batched (disjoint clean only) | 1 process, ONE world, all components concatenated | 5.924 | 3.15x | ta-batch-f-20260929 |

- Byte identity: per-fixture trace sha256 identical across the sequential
  and batched arms (`77b2b528c4774f6e`, `fa3a140771818af0`,
  `d660d27ce61b56c9`; 16-hex prefixes).
- Honest split: the CPU oracle backend gets NO banking speedup (sequential
  0.80x, batched 0.77x vs fresh-process; median of 3 order-deconfounded
  reps, `test-acceleration/scratch/cpu_speedup_table.json`) — there is no
  context/JIT warmup to amortize. Sequential banking is a GPU-BANK law, not
  a CPU-rehearsal one; the 2-tick single-fixture control (1.538x) confirms
  the fixed-cost-amortization model.
- Record numba JIT-cache state and ambient GPU load with every speedup
  claim (the queue receipts carry the preflight for both arms).

## Isolation law (the [700] lessons — designed, not hand-waved)

History (M08 card + `QUEUE_DRAINED.md`): a tamper teardown sticky-faulted
the NEXT world in the same process (`CUDA_ERROR [700]` at the clean
control's first memcpy); one poisoned context invalidates everything
scheduled after it, and memory unsafety can hide for whole runs as a
LATENT [700]. Therefore:

1. SEQUENTIAL is the default bank mode (2.50x, byte-identical traces,
   certified).
2. BATCHED (3.15x) only for GLOBALLY-DISJOINT clean fixtures, and only
   after the byte-equality job pair (seq + batched over the same fixture
   family) is GREEN for THIS kernel set + driver.
3. Tamper arms, sanitizer runs, and first-bank-of-new-kernel fixtures
   NEVER batch (sanitizer additionally never shares a process): the
   isolation boundary is the process. Submit them as separate
   `worker --spec ...` jobs.
4. Failure boundary = process boundary. Any exception in seq/batched:
   the per-fixture records completed so far are already on disk (each
   fixture writes its own result file the moment it completes — the exact
   completion boundary), and the process EXITS 3 immediately. Continuing
   would falsify later timings and risk a sticky card fault for the
   queue's next job.
5. Respawn = a NEW queue job containing only the REMAINING fixtures (fresh
   process = fresh context). No fixture is silently skipped or double-run.
6. Ordering law inside one process: clean fixtures first, tamper arms
   last; tamper arms preferably isolated entirely.

## Refusal guards (implemented in `tools/bank_runner.py`, exit 1)

- `far_field=True` fixtures: the direct-sum pass reads ALL states;
  concatenating fixtures changes every existing row (measured negative
  control: a shared subtrace sha changed when one disjoint component was
  added).
- Overlapping `x_offset` across the merged family: per-component
  decomposability is proven for globally distinct offsets only (the
  drained red ta-batch-b/c-20260929 had three components at 0.0 and two
  at 3.0 across fixtures).
- Mixed Maxwell elements across the merge: one world takes k_el/c_el from
  components[0].
- Non-clean arms (`tamper` / `sanitizer` / `first_bank`) in batched;
  sanitizer also refused in seq.

## Bank job shapes (mailbox-compliant)

Sequential bank job (same shape for batched, with `batched --specs ...`):
```json
{
  "id": "<lane>-bank-seq-<yyyymmdd>",
  "requester": "<lane> (Sergeant, <LANE>)",
  "command": "C:/Python314/python.exe -B <repo>/tools/bank_runner.py seq --specs <scratch>/f1.json,<scratch>/f2.json --out <scratch>/bank_seq.json --ticks 6",
  "workdir": "<scratch>",
  "expected_outputs": ["<scratch>/bank_seq.json",
                       "<scratch>/bank_seq.json.<fixture>.json", "..."],
  "timeout_seconds": 600
}
```
The requester aggregates the speedup table and byte-equality verdict from
the `done/*.result.json` receipts and the per-fixture files — the bank
stays the single source of recorded evidence. `tools/bank_runner.py
measure` (baseline-vs-sequential byte-equality certification + speedup)
spawns worker subprocesses and is a lane-host utility, NOT a queue job
shape; the certified GPU numbers above come from queue jobs only.

## Repo-side utility

`tools/bank_runner.py` (CPU modes; read-only against the card dir, default
`tools/monkey_campaign/contributions/MAT2-M08` + the M01/M03/M04/M06/M07
pin stack): `worker` (fresh-process baseline unit AND the process-isolated
arm), `seq`, `batched`, `measure`. Exit codes: 0 green (byte-equality
checks true), 1 refusal/red, 2 usage, 3 fault-containment stop. Run with
`python -B`. Outputs must stay outside the card dir (refused otherwise).
