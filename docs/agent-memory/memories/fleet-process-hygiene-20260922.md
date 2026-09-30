---
name: fleet-process-hygiene-20260922
description: The operator's resource-footprint directive ("agents stacking up
  editors will crash my computer") + the shipped hygiene mechanisms (census,
  liveness-law orphan sweep, cron Duty 2, the supervisor lane) + the janitor
  multi-repo gap
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_4e19803a-d027-4ebb-bbb3-e07c9c521e7a
---

Operator directive 2026-09-22: "Your agents are stacking up open editors.
Eventually it will crash my computer. We need to find some way to manage the
engine BETTER." He suggested asking Astra (round 6 — see
[[astra-consultation-channel]]).

**Why:** the fleet shares HIS gaming machine; measured peak was 13 engine
processes + 15 lane servers + a 26-leaked-headless-browser incident class;
finished lanes historically left processes running (lanes sweep their own only
sometimes).

**How to apply (the mechanisms, all live):**
- `E:/ChimeraWork/tools/fleet_process_census.ps1` — per-class census (engines,
  lane servers, headless browsers, editors, user apps) with RAM; sweeps leaked
  headless browsers to the 2 newest.
- `E:/ChimeraWork/tools/orphan_process_sweep.ps1` — kills lane processes ONLY
  by the LIVENESS LAW: worktree gone or quiet >QuietMinutes (default 60) AND
  not in the janitor DENY set; reads DENY from worktree_janitor.py (single
  source of truth — but its parse regex captures only the FIRST quoted string
  per line, known limitation); never name/age/port alone (Astra R6's ownership
  law). To be SUPERSEDED to report-only once lanes launch through the
  supervisor's ownership registry.
- The janitor cron (automation-84d09653) now has DUTY 2 (process hygiene) via
  CronUpdate — every 2 h alongside cleanup + retrospective. First real catches:
  9 killed (landed-quiet pushchan servers), engines 13→1, RAM free 71.4 GB.
- `E:/ChimeraWork/lane-archive/MACHINE_FINDINGS.md` — host-level findings
  (chrome.exe loopback breakage triple-evidenced; read BEFORE diagnosing host
  weirdness; solved findings get appended).
- The SUPERVISOR lane (lane/fleet-supervisor-20260922, tip 248704d8) LANDED
  2026-09-22, 8/8 falsifiers PASS: Job-Object launcher (root SUSPENDED →
  AssignProcessToJobObject → resume; assignment failure = launch failure, no
  survivor), guaranteed tree-death (KILL_ON_JOB_CLOSE; no pid-kill path exists),
  100/100 cycles incl. 30 launcher-kills with 0 survivors >30 s, 202/202
  sentinel checks (one decoy dressed as the legacy sweep pattern — untouched),
  PID+creation-time registry, memory limits verified by effect (child gets its
  OWN MemoryError), real-shape smoke (slice server + engine as job member +
  bundled-chromium capture, all dead after). **HONEST FINDING F-CPURATE: CPU
  hard caps UNENFORCEABLE on Win11 26200 (silently no-op) — the launcher
  REFUSES cpu_pct rather than pretending.** Broker phase 1 (mode file
  Gaming/Fleet/Training + GPU reservation law: expired end = still occupied;
  lost heartbeat = OWNERSHIP UNCERTAIN, never auto-free) live at
  tools/fleet_supervisor/. BROKER2 (phase 2) in flight: the GPU queue with
  three separate timeout states (queue-deadline / model-load / inference —
  deferred is labeled deferred, never "failed"), judge batching with
  anti-starvation caps, the training keeper (survives broker restarts,
  reconnects never duplicates), OLLAMA_LOAD_TIMEOUT verification.
- KNOWN GAP (found by the 2026-09-22 janitor run): worktree_janitor.py scans
  only its home repo's worktree registry — the day's lane worktrees registered
  under pass3-integ/repo are INVISIBLE to it (0 deleted despite being out of
  DENY); one-line fix proposed (scan both `git worktree list`s), awaiting the
  lead's conversion. CONFIRMED REPEATED 2nd cycle; the lead reclaimed the 22
  landed pass3-integ worktrees manually (git worktree remove; ~240 GB freed,
  E: → 700.8 GB; engines hit 0 for the first time). 3rd cycle 2026-09-23:
  still bridged manually (broker2-agent reclaimed cleanly); BROKER2 LANDED
  (549ad5a4, 8/8 fault-injected PASS ×2 — killed keeper → UNCERTAIN + second
  owner refused + audited-release only, corrupted heartbeat SELF-HEALS; the
  three timeout states never cross-labeled; broker restart adopts-only; aging
  bound 59.05 s == analytic; batch 4×; OLLAMA_LOAD_TIMEOUT verified 5 m
  server-side; CPU disposition: caps refused → AFFINITY enforceable, 1.79 vs
  9.64 cores measured; the lane ran ZERO fleet GPU work while the operator
  gamed — the law held in the wild).
- **THE 2026-09-23 CYCLE = THE CLEANEST CENSUS OF THE CAMPAIGN: zero engines,
  zero lane servers, zero leaked browsers, 0 killed / 0 kept by the sweep —
  nothing to find; RAM free 76.5 GB, E: 712 GB.** The hygiene law is holding
  STRUCTURALLY (supervisor + landed lanes dying with their work).
- **THE SELF-SUSTAINING REMNANT CLASS (retrospective cycle 3, candidate rule
  R-G):** a LANDED lane's leftover server keeps writing logs into its worktree
  → the worktree looks "quiet <60 min" → the sweep spares it AND directory
  removal fails on open handles (evidence: integ7's server held its dir until
  killed; thincli's FOUR boot_slice.py servers defeated the sweep via their own
  .tmp log-writes — surgical lead reclamation required). R-G: a lane's
  processes are leftovers, not life, once its branch tip is an ANCESTOR OF
  MASTER (the landing record is the ownership verdict, not mtimes) — the sweep
  gains a `git merge-base --is-ancestor` check before the quiet-test; dies
  structurally once lanes launch through the supervisor.

The open operator decision surfaced per Astra R6: a separate training-capable
machine is justified NOW if training must run while gaming can start at any
moment (his money call, no rush; the supervisor's measurements will date it).

**THE QUOTA WALL ARRIVED (2026-09-23): the WEEKLY/MONTHLY LIMIT EXHAUSTED
mid-closeout-6** ("[1310] ... will reset at 2026-09-25 10:18:03") — the
operator's standing duty-cycle economics concern (since 2026-09-11) realized
as an actual mid-lane kill after two record days (~35 lanes). Consequences:
all implementer agents FROZEN until reset; the lead (own budget class)
completed the wrap-up alone (closeout-6 checkpointed 83110c19; INTEG8
executed directly, master 92d1ee5a; see [[astra-consultation-channel]] for
the resume plan). **Candidate rule R-H, THE BURN GAUGE (retrospective cycle
4):** every lane receipt records its token/spend count and a running total is
visible per cycle, so the weekly wall is seen coming ≥1 day out; falsifier =
an exhaustion landing mid-lane with no prior gauge reading above 70%; home =
THE_CHECKLIST §7 + the lane receipt schema. Pause cycles since (cron runs
2026-09-23): near-empty retrospectives, hygiene holding structurally (zero
engines/servers/leaks, RAM ~82 GB free, E: 712 GB).
