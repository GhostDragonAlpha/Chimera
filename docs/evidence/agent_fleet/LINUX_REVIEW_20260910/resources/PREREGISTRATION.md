# Resource review preregistration — cf275281

Scope: offline public Control API against newly created TemporaryDirectory SQLite databases. No existing service, process, credentials, database, Git mutation, or production fix. Read AGENTS.md, docs/AGENT_START.md, docs/THE_AGENT_FLEET.md, tools/agent_fleet/README.md, control.py and test_resources.py. Referenced law/manual/onboarding documents are absent from supplied snapshot.

STATEMENT: Grouped admission and promotion preserve existing physical holders, strict same-resource FIFO, truthful memory totals, and progress for valid resource demand; benchmark isolation cannot be removed by a new request without drainage.

PREDICTIONS (source-derived, not yet executed):
1. A queued GPU+engine_demo request overwrites an existing engine_demo holder acquired via the supported legacy API.
2. With RAM budget B=1024 held by A, B's earlier GPU+RAM(B) request stalls but C's later GPU-only request grants, violating FIFO.
3. Releasing a sole RAM(B) hold with no pending requests leaves admitted_mb=B although sum(held.memory_mb)=0.
4. With A holding GPU and B holding all RAM, A requesting RAM and B requesting GPU leaves both pending; repeated promotion changes nothing. This disproves unconditional deadlock-free claims, though explicit release/revoke can recover.
5. A task with GPU benchmark can request functionality on the same GPU, replacing the reservation class without release evidence.
6. Positive control: RAM(B)+RAM(1) never admits above B, and releasing RAM(B) auto-promotes RAM(1).

FALSIFIERS: any predicted overwrite is refused or retains original ownership; later overlapping request remains queued; released total equals sum of holds; split cycle is rejected or independently resolved; benchmark upgrade/downgrade requires release. Positive control fails if sum exceeds B or pending request is not promoted.

Bounds/derivation: budget uses API minimum B=1024, exact capacity and B+1 boundary; 3 tasks suffice for FIFO, 2 for ownership/cycle, 1 for accounting/downgrade. Two explicit promotion-triggering no-op revocations test the stable cycle; no arbitrary sweeps or timing thresholds. Tests assert observed defects and identify themselves as reproduction tests, not desired regression semantics.

Pre-run strengthening after the six-case run: ownership case will start with a grouped GPU+engine_demo grant, then release GPU through its ordinary owner API, then request the same group for a second task. Prediction: release lacks an engine_demo dependency guard, retains engine_demo, and promotion overwrites it. Falsifier: release is refused or the second group remains queued. This removes reliance on legacy unchained acquisition. The original case and observations are retained in results.txt; strengthened run goes to results_stronger.txt.
