# THE PLAYABLE MONKEY IN THE FOREST — the standing goal + task board

Operator directive 2026-09-23 (the /goal text is authoritative; this file is its durable home
and the living task board). Executor: the fleet lead (execution coordinator). Architect: Astra.

## THE MILESTONE

One physically simulated monkey in a small forest clearing. The player steers it walking on all
fours, stops, approaches one tree, climbs, holds, descends, returns to the ground. All movement
from physical actuation — no teleportation, animated locomotion substitutes, invisible anchors,
or concealed resets. Execution order: (1) the two GPU parity residuals; (2) the unchanged walk
runbook at its gates; (3) connect the walk to the 20 Hz speed+heading interface, verify steering
and stopping; (4) the smallest forest clearing (uneven ground + one rigid climbable trunk);
(5) climbing feasibility from the actual animal's reach/contact/actuator limits — train climbing
only after those gates; (6) integrate + verify the ground–tree–ground loop. Climbing feasibility
may proceed alongside walking when resources permit. NOT advancing this goal: website work,
packaging polish, additional animals, large environments, unrelated improvements.

## THE TASK BOARD (durable; update on every verify/dispatch — priority, owner, dependency, status, receipt)

| # | Task | Pri | Owner | Depends | Status | Receipt |
|---|------|-----|-------|---------|--------|---------|
| T1 | closeout-7: the tick-66 discrete-flip drill (window 60→66) + the UCRT reconstruction (125/125 + dense-sweep bit gate, explicit-fma CUDA port) → the frozen bars re-run (freefall/stand/C1/C2, thresholds untouched) | P0 | fleet agent | quota reset 2026-09-25 10:18 | **BLOCKED (quota) — scouted by the lead (co7_LEAD_SCOUT.md on the port branch): drill clean at 68; fdlibm-port sign/quadrant bugs found; full brief ready** | validation/typeb_gpu_fullport_20260921/receipt.md (closeouts 1-6) |
| T2 | The walk training launch: the unchanged runbook at gates G1 parity / G2 anchors / G2.5 env obs field-21 / G3 identity (manifest c85ba5c4 + code rev + 3 seeds bound) / G4 reservation+keeper | P0 | lead (executor) | T1 | ARMED — operator-authorized, Astra Decision 1 | first_skill_prestage_20260922/RUNBOOK.md |
| T3 | Connect the trained walk to the 20 Hz speed+heading interface; verify steering + stopping (stopping gets its own bars per Astra r5) | P1 | fleet agent | T2 | pending | command_adapter_20260921 (the interface) |
| T4 | The forest clearing: minimal uneven ground + one rigid climbable trunk (engine scene; terrain lineage) | P1 | fleet agent | quota reset (parallel-eligible) | pending | gait_surface lineage |
| T5 | Climbing FEASIBILITY: reach / contact laws / actuator limits from the actual animal (the arm geometry + the landed muscle books); named gates BEFORE any climbing training | P1 | fleet agent | quota reset (parallel-eligible) | pending | k_fill_20260920 + hip_arms_20260920 (the books) |
| T6 | Climbing training | P2 | fleet agent | T2 + T5 gates | pending | — |
| T7 | The ground–tree–ground loop: integrate + verify end-to-end | P2 | lead | T3+T4+T6 | pending | — |
| — | Integration passes as tips land; supervisor/broker govern every dispatch; gaming mode = no fleet GPU | standing | lead | — | live | integration_pass4-8 receipts |

## RULES (binding, from the goal text)

Preregister before running; fired falsifiers are findings; never tune away failures or substitute
seeds; every integration re-proves the walk anchors (scene f6844ee, stdout 8c537cdb, 302 ticks,
30.970714 J); commit at milestones + concise recovery handoffs; owned-process launchers + the
resource broker; MACHINE_FINDINGS.md before host diagnosis; bundled Chromium; PowerShell .ps1;
quota pauses bind execution (planning ≠ authorization); completion requires evidence, never
"code exists" or "demo looks plausible". Decision boundary: routine choices inside approved
briefs only — physics/interfaces/training objectives/frozen bars/architecture changes return to
Astra with blocker + evidence + the smallest decision needed.
