# THE WORKFLOW BOOTSTRAP AUDIT — universal-agent workflow bootstrap (2026-09-09)

Review record, not a ledger: THE_MASTER_LIST.md stays the only task ledger.
Scope: the five-source-worktree "fleet" system (per operator assignment), what
already exists vs what is only proposed, and the exact blocking choice.

## 1 · Inventory at source revisions

Audited at: repo `https://github.com/GhostDragonAlpha/Chimera`, branch
`astra/gait-capture`, HEAD `60b77671` (local; pushed). Cross-checked master
`51cd7212` and history (`git log --all`) for earlier fleet records.

**EXISTS (reusable — do not recreate):**

- `docs/THE_MASTER_LIST.md` — the sole authoritative task ledger; entries
  carry owner, task, evidence path, status. This is the "shared authoritative
  state" the fleet needs; it already works (this session claims/records
  through it).
- `ChimeraEngine/AGENT_PROTOCOL.md` — the session contract (green baseline,
  done-is-a-log, docs-last append-only, handoff on context exhaustion, scratch
  quarantine). STALE: its "CURRENT TASK" slot still describes the retired
  SPIACE/teddy pipeline (pre-2026-08-23 session shape), but its RULES are the
  live law AGENTS.md cites for SPIACE agents.
- `docs/THE_DYAD_PROTOCOL.md` — the standing eye loop with parallel-operation
  rules: verify engine state, kill only PIDs you spawned, ports 8090/8092/8093,
  binary identity (exe + spv hash per verdict), cooldown-not-contention.
  This is the fleet's per-agent runtime-safety law, already codified.
- `Chimera/core/membrane.py` (master; described in CLAUDE.md L-law) — seals a
  git worktree of the current tree plus a copy of gitignored `docs/world/`,
  measures containment. This is the PROVEN isolation primitive: a fleet slot
  is a membrane with a port.
- The five physical review checkouts on `E:` (observed this session):
  `opencode\gpu-demo-recovery-01\isolated-checkout`,
  `robustness-01\isolated-checkout`, `review-mutations-01\isolated-checkout`,
  `state-integrity-01\isolated-checkout`, `membrane_scale_lab_checkout` —
  each an independent clone of this repo at the same engine source. These
  demonstrate the slot pattern in practice (Astra's lanes), but no committed
  document defines them.
- Evidence discipline (law, in force): unique run dirs, raw logs, summary
  JSON, state IDs, hashes — demonstrated across
  `docs/evidence/membrane_gpu_demo_runtime/`.

**PROPOSED ONLY (no committed artifact):**

- The five-slot fleet itself: no committed document names the slots, their
  ports, their build dirs, or their session stores. (AGENTS.md's retired
  task-board shape was REMOVED 2026-08-03 deliberately; nothing replaced it.)
- Slot-scoped engine build/runtime/session storage: build dirs exist per
  checkout in practice, but are unrecorded; session storage (Saved/, dyad
  logs, evidence) currently lives per-checkout with no cross-slot registry.
- The universal prompt: no committed artifact. Closest existing pieces:
  AGENT_PROTOCOL.md's contract + THE_DYAD_PROTOCOL.md's parallel rules +
  THE_MASTER_LIST.md as claim/record surface.
- Task claiming/leasing: none. The master list has no claim semantics, no
  dependency field, no integration-ownership field — one agent writes it
  today, so none was needed before.

## 2 · Gap list (what a universal prompt needs that does not exist)

1. **Slot registry** — a committed file naming the five slots: worktree path,
   branch/base, port (8090 operator / 8092 dev / 8093 isolated + free range),
   build dir (OUTSIDE `ChimeraEngine/engine/build/` and outside the user
   Temp dir — the GLM-GPU-DEMO-02 stale-TU finding is the reason), session
   store path, and current owner.
2. **Claim/lease semantics for master-list entries** — without it, two slots
   can take one task. Minimal form: an entry gains `claimed: <slot-id> /
   <timestamp>` written under the slot's identity; restart recovery = a
   claim older than a bound is stealable, with the steal recorded.
3. **Integration ownership** — who merges a slot's published branch commits
   into `astra/gait-capture` (today: each lane pushes its own lane branch;
   integration to the authorized branch is the publisher's act). Needs one
   recorded rule, not machinery.
4. **Cross-slot evidence pointer convention** — each slot's evidence must be
   reachable from the master list (a path or a published commit SHA).
5. **Stale-context recovery text** — the universal prompt's "recover
   context" step = `python tools/orient.py` + master list + AGENT_PROTOCOL
   rules + last own evidence dir. `tools/orient.py` exists (master-era);
   verify it still runs in this checkout or point at its replacement.
6. **Conflicting-instruction resolution** — AGENTS.md's research-agent and
   subagent-delegation sections predate the sole-agent amendments; the
   universal prompt must state precedence: operator instruction > master
   list entry > AGENT_PROTOCOL rules > AGENTS.md background sections.

## 3 · The EDGE-01 workflow example (claimed setting → contradiction → source → correction → rerun)

This session produced a clean, complete instance of the loop the fleet
should make routine (source revisions: EDGE-01 implementation `60b77671`;
contradiction evidence `20260909T142006.842279Z/dyad_gpu_demo_review.json`;
correction + rerun same branch):

1. **Claimed setting** (recorded in the run facts): "render mode = fill +
   1px GPU wireframe (slotmode 2)" — imported from the CPU-demo `/mesh_bin`
   law.
2. **Observed contradiction** (independent observer, DYAD protocol): the
   reviewer reports "I do not see distinct wireframe strokes" in both
   captures — the claim is not what the pixels show.
3. **Measurement + source inspection**: PNGs byte-differ between the
   fill-only and "wire" runs (something drew), and engine source shows the
   wire pass requires `mesh_mode_ >= 1`, which the demo path never sets;
   the contrast pipeline additionally needs its own latch. The claim was
   FALSE for this render path: the pass fell back to the fill-colored wire.
4. **Correction**: the runner's recorded render mode was corrected (not the
   observation), and the smallest opt-in (`CHIMERA_MD_EDGE` ->
   `md_edge_contrast_`, demo-scoped, `mesh_mode_` untouched) made the claim
   TRUE by construction; the contrast instrument joined the same latch.
5. **Rerun with identity**: numerical gate green in every configuration
   (20 PASS + 1 INFO) and `accepted_state_id` bit-identical across all
   presentation runs — the correction is proven presentation-only, and the
   new dyad reads (spokes visible; apex above centroid vs relaxed centroid)
   closed the loop.

Law this instance already demonstrates: neither model consensus (the dyad's
first two reports agreed with the fill-only scene) nor a passing screenshot
substitutes for the state-identity gate (bit-identical accepted_state_id)
and the numerical gate (20-PASS rerun) — those are what made the correction
admissible.

## 4 · The blocking architectural choice (named, not invented around)

**Who owns a slot's session store and how independent stores reconcile —
per-slot private stores (isolation, but cross-slot context must be
republished through the master list) vs a shared store with per-slot
namespacing (context is automatically visible to all, but the store becomes
a shared writable resource and every peer's crash-recovery story must handle
partial writes by others).**

This choice determines the claim/lease mechanism (file locks + convention on
a shared file vs atomic rename in a private store), whether `Saved/dyad` and
evidence land per-slot or in one namespaced tree, and what the universal
prompt's recovery step reads. It is an operator call because it trades
isolation (the membrane law's own direction: `core/membrane.py` exists
because shared stores caused real incidents — the 2026-07-14 phantom-task
write through the shared live graph) against fleet visibility (the operator's
five-slot design assumes slots share authoritative state). Existing evidence
on both sides: the membrane incident says shared-writable stores are the
historical failure mode; the master list and dyad log are shared stores that
worked, but with exactly one writer at a time.

Everything else in the gap list can be built without this choice being made
first; the universal prompt cannot honestly be announced ready until it is,
because "recover context" differs materially under each answer.

## 5 · What was implemented now (smallest increment, offline-tested)

None of the machinery: per the operator's own rule, the blocking choice above
gates the bootstrap design, and inventing a parallel controller would repeat
the retired task-board mistake. What this session contributed instead:
- this audit (inventory, gaps, example, choice) at a named revision;
- the EDGE-01 workflow instance it documents, end to end;
- the master-list update recording the fleet proposal's status and this
  record's location.

Next executable task (smallest, choice-independent): write the slot registry
for the five observed lanes as they exist today (paths, ports, build dirs,
owners) — a record, not a controller — and reconcile `tools/orient.py` with
this checkout's live state so the universal prompt's first step exists.
