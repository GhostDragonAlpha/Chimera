# AMENDMENT-4 — lane det-mpm (prereg 32e485e0; amendments a7dc1f1a, bb81ce60, 09dd5a8b)

Status: DRAFT for Lieutenant commit; the r2r contention cell is gated on this
commit. Submitted by wk-det-mpm, 2026-10-02.

## Second library-boundary finding (preserved failures)

Both r2r-cont2 arms (v4, N=125049, 24 frames) FAILED at the first contention
launch, exit 1, job walls 3.5/3.1 s, receipts preserved under
runs/r2r-cont2-a/ and runs/r2r-cont2-b/:

    RuntimeError: Deterministic scatter buffer overflow in kernel
    'contention_kernel'. Increase 'deterministic_max_records' or reduce ...

Mechanism (from the installed warp 1.17.0 sources, warp/config.py:476 and
warp/native/deterministic.cu): under RUN_TO_RUN, atomic scatters are recorded
as (key, value) records in a bounded buffer, then ordered by destination and
accumulated in order (record -> sort -> segmented reduction). The buffer bound
is PER-THREAD (`deterministic_max_records`, default 0 = static codegen lower
bound). The v4 kernel's dynamic `iters` loop cannot be statically bounded, so
the launch overflows. The MPM integrands' per-thread record counts ARE
statically bounded (a fixed number of atomic sites per quadrature-point
visit), which is why every R2R clean arm and all four CPU runs completed and
were bit-exact. The two failures are themselves evidence about the boundary:
warp's R2R determinism composes only with workloads whose per-thread scatter
counts fit the record budget.

Fix validated CPU-side with CUDA hidden: setting
`wp.config.deterministic_max_records = 8192` before module creation makes the
IDENTICAL v4 kernel launch under RUN_TO_RUN and land exactly 268,435,456 adds
(array sum exact). NG mode ignores the setting.

## Changes

C10. Harness v5: run_mpm_arm_v5.py
     sha256 a983d5c466d984e2f55ed0b4cfaff4c2c55971e69d1d6ce65050d4f6f7770331
     (diff vs v4: `wp.config.deterministic_max_records = 8192` set before
     newton import with an assert + receipt field; NOTHING else changes — the
     kernel, workload, per-frame share design and hash protocol are
     byte-identical to v4).

C11. Calibration cal3: cont_cal.py
     sha256 ac80571b5e0119248dd4fe15c3d292e014f3473d4e9f712a7a85bddfe5f8d5c2
     (NON-EVIDENCE; imports v5 twice — once per mode — and reports BOTH
     T_ng_solo_ms_median and T_r2r_solo_ms_median. The R2R launch cost
     includes recording + ordering of 268M records and is expected to be much
     larger than the NG cost, so per-mode calibration is required; using the
     NG time would undersize the r2r stream.)

C12. Sizing (formula unchanged, mode-specific inputs):
     scene_ng_s    = 120 * mean(0.105388, 0.076297) = 10.901 s   (measured)
     scene_r2r24_s = 24 * mean(4.170550, 4.320911)  = 101.898 s  (measured)
     N_ng_cell  = clamp(ceil(3.0 * scene_ng_s    / T_ng_solo_s),  800, 2000000)
     N_r2r_cell = clamp(ceil(3.0 * scene_r2r24_s / T_r2r_solo_s), 800, 2000000)
     Budget guard: job = 60 + max(scene, N*T_mode_solo) + 30 <= 570 s; else
     N = floor((570 - 90 - scene) / T_mode_solo), floor 800. The ng-cont2 pair
     (v4, N=13378, completed exit 0, bit-exact) REMAINS the ng contention cell
     of record: v5 changes nothing for NG mode (the record bound is ignored),
     so re-running the ng pair under v5 is not required; the r2r cell runs
     under v5 as det-mpm-r2r-cont3-a/b (24 frames). If any future ng re-run is
     ordered, it uses v5 for a single current identity.

C13. Validity rule C5 unchanged (drain_wait_s >= 1.0 s, else WEAK, no
     re-runs). The declared C5-vs-per-frame-share operationalization gap for
     NG cells stands as recorded in EVIDENCE.md; for the r2r cell the
     contention backlog is expected to outlast the scene, so C5 is expected to
     be satisfiable as written. Memory note, pre-declared: an R2R contention
     launch holds up to threads x iters records (32768 x 8192 x ~16 B ~ 4.3 GB)
     on the 24 GB card alongside the MPM scene; if the r2r-cont3 job fails on
     device memory, the failure is preserved and the Captain/Lieutenant decide
     between a reduced-iters variant (iters=1024, same record-bound mechanism,
     N scaled x8 by the same formula) and accepting the boundary finding as
     the r2r cell result. No other prereg term changes.

## Execution order after this commit

det-mpm-cont-cal3 -> derive N_r2r (formula above, both medians recorded) ->
submit det-mpm-r2r-cont3-a/b -> pair comparison + C5 validity -> final report.

## Requested commit

Add to tools/monkey_campaign/contributions/WK-DET-MPM-20261001/ as ONE commit:
1. AMENDMENT-4.md (this file as staged)
2. run_mpm_arm_v5.py (as staged)
3. cont_cal.py (as staged)
