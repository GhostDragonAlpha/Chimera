# I-GOV-PR-HANDOFF-REPAIR — correction report: NO-CHANGE RECONCILIATION

**Verdict: PR #128 (head `8594a5fc`) must NOT be applied to the installed
workflow. Both of its target defects are already fixed by the current
astra-0017..0026 machinery — verified by a 12/12-green probe against the
current modules in isolated registries — and its automatic-displacement logic
would violate astra-0022. This is the lead-authorized "no-change
reconciliation receipt" (msg-a5dc3bf5).**

- Correction attempt `1ccb4bcdcddc4cf39c16a3fd1289e7c8`, agent
  `c95e1722350849bca846b237c1f60997`, criteria
  `71c0089538a563ea19173cd7e60604c150c51603e8538b3d1dad724fc92ecf9c`.
- Responds to: `msg-a5dc3bf59c41441c89676dced7a37dc0` (CHANGES REQUIRED on
  PR #128), which supersedes the original card steps' "deliver proposed.patch".
- Prior attempt `ad0b478d` (arrival `f4b9cb28`) authored PR #128's candidate;
  its files are preserved untouched in its attempt directory. This correction
  does not retract the prior work's quality against ITS pinned target (PR #116
  head `8730d384`) — it reconciles it against the CURRENT modules.

## Reconciliation analysis (each claim measured, code cited)

| PR #128 change | Current installed equivalent | Reconciled? |
|---|---|---|
| `request_publication` durable PR-request handoff (idempotent, exact identity, next-card transition, no credentials) | `continuous_cycle.py::request_publication` (astra-0017) + `worker_start.py --request-pr` — LIVE-PROVEN by this same agent TODAY: four requests (`publication-3c5e99f9…`, `publication-e371340a…`, `publication-da5f190d…`, `publication-32e57764…`), each recording `PUBLICATION_REQUESTED` and returning the next card | **SUPERSEDED** |
| `fulfil_publication` lead-side fulfilment | Lead publication + `github-recovery` recording + connected-lead merge service (astra-0024/0026: verified GitHub submission, accept-merge) | **SUPERSEDED** |
| Explicit selection resolving to the requested card | `continuous_cycle.join` filters candidates to `task_id`; while other WORKING work exists it REFUSES by name `checkpoint_active_work_before_switch` instead of returning a wrong card | **SUPERSEDED (stronger: refusal + park protocol)** |
| `displace_working` automatic parking of the worker's other attempts | DELIBERATELY ABSENT: astra-0022 — "No automatic parking or other worker takeover is permitted"; switching requires an explicit `--park` checkpoint | **MUST NOT INSTALL** |
| `--request-pr` wiring in worker_start | Present (used four times today) | **SUPERSEDED** |
| KANBAN.md bridge paragraph | Superseded by CONTINUOUS_CYCLE.md §2 | **SUPERSEDED** |

## Probe evidence (reconcile.py, current modules, isolated registries)

`python -B reconcile.py` → exit 0, **all 12 checks green**:

- **D1 (explicit routing)**: explicit request for T0 with T1 WORKING → named
  refusal `checkpoint_active_work_before_switch`, no card packet; T1's attempt
  remains WORKING (no auto-displacement); after parking, explicit request for
  T0 never returns T1; positive control: explicit request for T2 (no other
  active work) returns exactly T2 `ASSIGNED`.
- **D2 (PR-request bridge)**: `request_publication` records a durable request
  bound to attempt/criteria/artifacts (real files inside the attempt
  workspace, per the production law the probe itself exercises), flips the
  attempt to `PUBLICATION_REQUESTED`, is idempotent for identical artifacts
  (same request id), refuses a wrong criteria hash by name, and the next
  generic join returns a different card — all offline file operations.
- **Falsifier invariants**: board capacity stays 10; every card's
  `criteria_sha256` unchanged across join/request/park; no other agent's
  attempt is ever touched.

`python -B -m unittest test_reconcile -v` → 5/5 OK. Machine receipt:
`reconciliation_receipt.json` (schema `igov.pr116.reconciliation.probe.v1`,
`all_green: true`).

## Falsifier scorecard (from PREREGISTRATION.md)

- Any wrong-card return / trapped worker / masqueraded request / changed
  criteria or capacity: **NOT FIRED** (12/12).
- Live-session evidence fabricated: **NOT FIRED** — the four publication
  request ids above are real records from this session's own handoffs.
- Production edits: **NONE** — modules imported read-only from
  `E:/PythonChimera/tools/monkey_campaign`; registries in temp dirs.

## Disposition requested of the lead

Close PR #128 as superseded-by-reconciliation (do not merge), record this
receipt against the card, and mark the correction complete. If the lead
prefers to preserve PR #128's probe/test assets for history, they remain in
attempt `ad0b478d`'s directory, untouched.
