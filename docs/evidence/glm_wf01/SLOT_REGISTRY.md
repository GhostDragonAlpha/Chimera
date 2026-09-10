# GLM-WF-01 — SLOT REGISTRY RECORD + ORIENT.PY RECONCILIATION (2026-09-09)

Worker: GLM 5.3 Flash (the Master List's ACTIVE GPU-material lane).
Inspected revision: `d7c47446b94acc75d1d32505de1665feb0fa0133`
(`astra/gait-capture` remote head, fetch-verified twice during the session).
Task worktree: `E:/ChimeraWork/slot-glm-wf01`, branch `astra/tasks/glm-wf-01`.
Session status: **BOOTSTRAP_NOT_CONFIGURED** (see §6) — this task proceeds under
the audit's own "next choice-independent task" designation
(`docs/THE_WORKFLOW_BOOTSTRAP_AUDIT.md`, recorded at `60b77671`) and the Master
List's CURRENT CONTROL assignment of GLM 5.3. The fleet control plane is not
deployed; no controller claim, generation or lease exists for this work, and
none is invented here.

## 0 · PREREGISTRATION (RULE 0)

The audit named the task but not its falsifiers. Named here, BEFORE the
measurements (the store-presence facts below were established first, during
entry diagnosis; every BEHAVIORAL prediction was written down before the run
that could fire it — the run order is preserved in the session log).

- **Statement:** a written per-checkout registry of the five observed worker
  lanes plus a source-verified reconciliation of `tools/orient.py` removes the
  bootstrap audit's named ambiguity ("which store is authoritative, and what
  does a fresh worktree actually see") without deploying the fleet, without
  code changes, and without touching any live store.
- **Predictions and falsifiers (all named before measurement):**
  - **F1** — PREDICTION: `orient.py` fails or degrades loudly in a fresh
    worktree that has no local `engine_state.json`. FALSIFIER: it exits 0 with
    a plausible term tree.
  - **F2** — PREDICTION: `engine_state.json` is tracked and identical across
    checkouts of the same commit (like `verdict_registry.json`). FALSIFIER:
    it is absent from `git ls-files` at any inspected head.
  - **F3** — PREDICTION: the five review checkouts hold divergent live copies
    of the two stores. FALSIFIER: no review checkout carries either store
    (they carry neither).
  - **F4** — PREDICTION: `orient.py` writes state as a side effect (the
    readiness doc demanded constructor side-effect checks). FALSIFIER: a
    read-only run leaves `git status --porcelain` empty in a fresh worktree
    AND source inspection finds no write path.
  - **F5** — PREDICTION: the GLM freeze checkout's four untracked leftovers
    are unpublished work. FALSIFIER: all four paths exist on the integration
    branch.
  - **F6** — PREDICTION: the operator checkout is on `master` for the whole
    session. FALSIFIER: it is on `astra/gait-capture` when re-read before the
    record is written.

## 1 · MEASURED RESULTS (each falsifier resolved)

| # | Prediction | Result | Evidence |
|---|---|---|---|
| F1 | loud failure without a store | **FALSIFIED — exits 0, plausible default tree, no marker** | fresh worktree run printed `CURRENT TERM: theSeed`, all six gates `[ ]`, exit 0; worktree stayed clean |
| F2 | store tracked like the verdict lane | **FALSIFIED — `engine_state.json` is NOT tracked at `cf2a0ae2` or `d7c47446`; gitignored at `.gitignore:174`** | `git cat-file -e` refused at both heads; `git check-ignore -v` → `.gitignore:174:ChimeraEngine/engine_state.json` |
| F3 | divergent copies in review checkouts | **FALSIFIED — the four review checkouts carry NEITHER store** | no `engine_state.json` on disk and not tracked at `900b1297` / `7aba0ee7` / `cf2a0ae2` / `bf0a6216` |
| F4 | hidden write path | **HELD — read-only confirmed twice** | source: only `--json` argparse flag, no save call; measured: `git status --porcelain` empty after the run in the fresh worktree |
| F5 | unpublished predecessor leftovers | **HELD — all four paths already on the branch** | `docs/evidence/gpu_fixtures/`, `tools/gpu_fixtures_generate.py`, `tools/gpu_fixtures_recovered/`, `tools/gpu_fixtures_verify.py` all resolve at `d7c47446` |
| F6 | operator checkout on master | **FALSIFIED — observed on `astra/gait-capture` @ `d7c47446` mid-session** (was `master` @ `51cd7212` at session start; not moved by this worker — this worker only fetched and added a worktree) | `git -C E:/PythonChimera branch --show-current` → `astra/gait-capture` |

Net: three falsifiers FIRED. The audit's suspicion about orient.py ("Its
output describes that checkout's stores. It does not identify the currently
displayed engine or prove shared fleet authority") is confirmed and now
measured precisely: the real hazard is the **silent default** — an agent that
orients in a store-less checkout gets exit 0 and a plausible hierarchy, which
is worse than an error because nothing marks the output as empty.

## 2 · THE SLOT REGISTRY (the RECORD the audit asked for)

Ten lanes were observed. Port column: taken/needed per the fleet plan
(candidates 8101–8105); no lane's port was probed beyond a loopback
availability check and none was opened or bound by this worker.

| Lane (path) | Role / owner | HEAD (observed) | Dirty state | `engine_state.json` (live term store) | `verdict_registry.json` | Port |
|---|---|---|---|---|---|---|
| `E:/PythonChimera` | operator checkout + canonical stores | moved `51cd7212`→`d7c47446` during session (not by this worker) | 124 entries (docs, evidence, launch logs) | PRESENT, 24,869 B, sha256 `2bc21ed757351f5b…` | tracked, 2,981 B, blob `cfba404b` | n/a |
| `E:/Chimera_GLM_freeze` | GLM lane (this worker's predecessor) | `cf2a0ae2` (detached) | 4 untracked (all published upstream, F5) | ABSENT | tracked @ that commit | none taken |
| `E:/PythonChimera/gpu-demo-recovery-01/isolated-checkout` | BP recovery lane | `900b1297` (branch `gpu-demo-recovery-01`) | clean | ABSENT | tracked @ that commit | none taken |
| `E:/PythonChimera/review-mutations-01/isolated-checkout` | mutation-review lane | `7aba0ee7` (detached) | clean | ABSENT | tracked @ that commit | none taken |
| `E:/PythonChimera/robustness-01/isolated-checkout` | Muse robustness lane | `cf2a0ae2` (detached) | 2 modified | ABSENT | tracked @ that commit | none taken |
| `E:/PythonChimera/state-integrity-01/isolated-checkout` | DS state-integrity lane | `bf0a6216` (detached) | 2 modified | ABSENT | tracked @ that commit | none taken |
| `E:/Chimera_G01` | G01 evidence lane | `a530b514` (branch `g01-evidence`) | 17 entries (not entered) | not inspected (out of scope) | not inspected | none taken |
| `E:/Chimera`, `E:/ChimeraSpace` | legacy/adjacent copies | `24ab3291` / `74f25a7f` on master, heavy dirt | — | not inspected (out of scope) | — | none taken |
| `E:/ChimeraWork/slot-glm-wf01` | THIS task worktree | `d7c47446` (branch `astra/tasks/glm-wf-01`) | only this record | ABSENT (by design — see R2) | tracked @ `d7c47446` (blob `cfba404b`) | none taken |
| `E:/ChimeraWork` (planned slots 01–05) | fleet plan targets | **DO NOT EXIST** — `E:/ChimeraWork` was empty before this task created its directory | — | — | — | 8101–8105 free |

Registry facts that matter for the fleet decision:

- Only the operator checkout holds a live term store. The term lane is
  effectively **single-store, single-owner** today.
- The verdict lane is **commit-identified and reproducible** — every checkout
  of the same commit byte-matches (blob `cfba404b`); its authority question is
  about WRITES, not reads (AGENTS.md already assigns the serialized owner).
- The four review checkouts are pure evidence snapshots: no stores, nothing to
  reconcile, safe to preserve as-is (the fleet's "never delete a legacy
  checkout" law is already satisfied).
- The freeze checkout is fully drained: every artifact it held is on the
  integration branch. It is safe to retire whenever the operator chooses; this
  worker did not remove it.

## 3 · ORIENT.PY RECONCILIATION — WHAT IS TRUE AFTER SOURCE + RUNS

`tools/orient.py` @ `d7c47446`, verified by source inspection and two live
runs (operator checkout; fresh worktree):

1. It is a genuine READ: no write/save path exists in the tool (F4 held).
2. Its "git HEAD" line prints **the checkout's own HEAD**. Output therefore
   differs per checkout by construction; it is a per-checkout read, never a
   fleet-wide authority probe. The readiness doc's row is confirmed.
3. Its term-lane half reads `ChimeraEngine/engine_state.json` from
   `ROOT = <checkout>/`, i.e. the ONE live copy in the operator checkout —
   and, where the file is absent, **silently default-initializes an empty
   Engine in memory** and prints it (F1 fired). No error, no marker, exit 0,
   nothing written back.
4. Its verdict-lane half reads the TRACKED `tools/verdict_registry.json` and
   works identically in any checkout of the same commit (closed=2, next=63
   measured in the fresh worktree).
5. `Engine._load()`'s memory reconciliation of saved state with generated
   terms (readiness doc row) is NOT re-verified here; the recorded caution
   ("not a byte-for-byte snapshot of the original file") stands as written.

## 4 · THE RECONCILED RULES (binding on fleet integration; proposal, not code)

- **R1 — No authoritative orient without a store.** Any adapter that honors
  orient output MUST first verify `ChimeraEngine/engine_state.json` EXISTS in
  that checkout and record its byte length + sha256 with the revision. Exit 0
  alone proves nothing (F1).
- **R2 — The term store is per-checkout, gitignored, untracked.** It is NOT a
  shared store and cannot become one by copying. Until an adapter exists, the
  operator checkout's store is the only authoritative term state; fresh slots
  start EMPTY and must say so, not print a default tree as if it were state.
- **R3 — orient.py is approved as a read for agent sessions** (F4), but every
  recorded orientation must carry: store presence, store hash, checkout HEAD,
  and (for the verdict lane) the commit identity. An orientation record
  without these is NOT_TESTED, not oriented.
- **R4 — Verdict-lane reads are commit-safe; writes stay serialized.** The
  tracked ledger reproduces per commit (measured), so READS from any checkout
  of the recorded commit are sound. WRITES remain the serialized owner's
  (AGENTS.md law); five worktrees writing five copies is exactly the
  divergence the readiness doc warns about, and the registry shows the term
  lane would diverge immediately (untracked), the verdict lane only on write.
- **R5 — A `--strict` flag is the named minimal fix** (refuse, or mark
  output UNORIENTED, when the term store is absent). NOT implemented in this
  task — the audit scoped this as a record, `orient.py` sits in the operator
  lane's tool surface, and a shared-tool change deserves its own preregistered
  change with the operator's sign-off. Recorded as the follow-up.

This registry also hands the operator the measured baseline for the audit's
ONE blocking choice (per-slot private session stores vs a shared namespaced
store): the term lane ALREADY behaves per-slot (gitignored, single live copy,
silent defaults in fresh copies) — a per-slot design formalizes what exists; a
shared design must first give `engine_state.json` an owner, a format contract
and a writer. Either way R1–R3 are prerequisites, because the silent default
defeats both designs.

## 5 · ENVIRONMENT SNAPSHOT (read-only, at record time)

- GPU: NVIDIA GeForce RTX 4090, 21,309 / 24,564 MiB resident (consistent with
  the resident 27B eye per the Master List contention note). No training or
  engine run was started; no reservation taken.
- Ports probed (loopback, availability only): 8765, 8088, 8091, 8101–8105 —
  all FREE. No control service, no eye service, no slot engine is running.
- Protected paths: nothing written under `ChimeraEngine/engine/build/` or any
  build directory; no engine launched; no other lane's files modified; no
  push of any kind (master untouched; this branch is local-only).

## 6 · SESSION STATUS — BOOTSTRAP_NOT_CONFIGURED (exact prerequisites)

The universal entry's runtime requirements are absent; per `AGENT_START.md`
this is reported, not worked around:

1. **No control service** — `tools/agent_fleet/service.py` is not running
   (ports free), no `state.sqlite` exists outside the per-run temp demos
   (`C:/Users/allen/AppData/Local/Temp/opencode/fleet-demo-*/`), and
   `E:/ChimeraWork` (the planned root) was empty. Smallest operator action:
   start the service per THE_AGENT_FLEET.md with an explicitly assigned free
   port and its supervisor/enrollment tokens, or delegate that to the trusted
   launcher.
2. **No provisioned session file for this worker** — enrollment is
   launcher-only by design (`client.py` refuses `enroll` so credentials never
   enter agent logs). Smallest operator action: run the trusted-launcher
   enrollment for this lane and provision the private session JSON.
3. **Universal dispatch itself is on HOLD** (`docs/AGENT_BOOTSTRAP_READINESS.md`,
   `AGENT_START.md` banner) pending documentation reconciliation — which is
   exactly the work this record feeds. Existing explicit assignments continue;
   this task is one of them.

## 7 · CHECKPOINT (resume without this conversation)

- Task: GLM-WF-01 (self-assigned under the audit's named follow-up; no
  controller generation exists).
- Branch: `astra/tasks/glm-wf-01` (local only) at `d7c47446` + this record.
- Completed: entry verification; coordination diagnosis (§6); lane inventory
  (§2); orient.py source+run verification (§3); falsifier set resolved (§1);
  this record + master-list row.
- Next executable step: lead/operator review; then EITHER integrate this
  record and implement R5 (`--strict`, preregistered separately) OR hand the
  §4 rules to the fleet adapter work. No verification gate remains open on
  this record itself — it contains no physical or perceptual claim; its
  verdicts are source-inspection and filesystem measurements, reproducible
  from the commands quoted above.
- Not done, named: no engine runtime, no DYAD, no GPU work (none was in
  scope); orient.py `--strict` NOT implemented (R5); Master List row rides
  with this branch and is PENDING INTEGRATION, not self-published.

## 8 · EARNED EN ROUTE — the gates caught pre-existing pointers (2026-09-09)

The repo's own doc-lint gate (`tools/doc_lint.py --staged`, wired via
`.githooks/pre-commit`) refused the first commit attempt because this record
references `ChimeraEngine/engine_state.json` — which does not exist in a fresh
checkout. That refusal is the linter working correctly on my own finding: the
reference is intentional (the file is gitignored BY POLICY, see F2), so the
record was admitted through the documented mechanism (`.doclint.allow`, reason
comment in-file) — no bypass, no tolerance widened.

The same gate then surfaced TWO PRE-EXISTING broken-in-checkout pointers in
`docs/THE_MASTER_LIST.md` (§4 LANDED FOUNDATIONS, the T2 membrane record):
`models/cad_bear/ca_run.json` and `models/cad_bear/frost_binding.json`.
Measured: `/models/` is wholly gitignored (`.gitignore:249`, zero tracked
files at `d7c47446`); both files exist ONLY in the operator checkout as
untracked run artifacts. Same class as the term store: per-checkout local
artifacts referenced by tracked prose. They were allowlisted with a reason
comment in the same commit — but the continuity risk is now on record: the
T2 run evidence cited by the Master List is not reproducible from a fresh
checkout. Follow-up (NOT done here, out of scope): either track a copy under
`docs/evidence/` (the repo's evidence convention) or have the evidence-policy
owner record the retention decision.
