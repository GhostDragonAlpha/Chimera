# RESULT -- docs-evidence-link-audit-01 (wave 5)

Worker: subagent-worker-09 (instance id subagent-worker-09-a8960d274e14).
Branch astra/tasks/docs-evidence-link-audit-01; base bf9d532b; slot 3
(E:\ChimeraWork\slot-03). Preregistration: PREREGISTRATION.md, own commit
e26105f2 (before code; GEN-1 CLARIFICATION appended before the implementation
commit, documented below). AUDIT-ONLY: `git diff --name-only <base>` shows
additions under docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/ and nothing
else; no doc was edited.

## Retained run (the verbatim record)

Command (from the repo root, slot 3):

    python docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/evidence_link_audit.py

Run order (deterministic): lane files staged (index) first so bare sibling
names resolve against `git ls-files` exactly as they will in the committed
tree; RAW_AUDIT.txt and FINDINGS.md below were then written by that run;
this RESULT.md was finalized after the run, so its own lines are the only
fleet-set content not covered by the retained snapshot (a re-run at the PR
head reproduces it; the enumeration is deterministic given the tree).

The script's worktree-mutation guard compared `git status --porcelain`
immediately before and after enumeration: identical (RAW_AUDIT.txt header).
No tracked doc changed at any point in this lane.

## Prediction scorecard

P1 (fixture/teeth) -- VERIFIED.
  `--self-test` plants 17 references of every class in a fixture doc plus 9
  distractors (sha, external URL, glob, anchor-only link, two git refs, three
  prose slash-pairs). Result: planted found 17/17, each with EXACTLY the
  planted disposition; distractors 9/9 IGNORED with recorded reasons; zero
  records left CAND; FAILURES: 0. RAW_SELFTEST.txt retained verbatim.
  Note: the falsifier FIRED once during development -- the fixture first put
  the unlabeled PR directly under the labeled-PR line, and the pinned
  context window (line + preceding line) legitimately labeled it. The fixture
  was corrected to test the pinned semantics; the rules were NOT retuned to
  make the test pass.

P2 (real run) -- VERIFIED.
  All four classes present in the real fleet docs set; every class produced
  records; the three counts are reported below. RAW_AUDIT.txt retains one
  line per enumerated reference (1,692 records), verbatim.

P3 (audit-only) -- VERIFIED (see above; review-verifiable via
  `git diff --name-only bf9d532b` == this directory only).

Falsifier status: NOT TRIGGERED (no doc mutated; no reference silently
skipped -- enumeration teeth proven by P1; findings retained verbatim).

## Counts (the prediction's three numbers)

    resolved           459
    dangling            85   (17 beyond the known controller-id class)
    controller-labeled 178
    ignored-with-reason 970  (prose-slash-pair 378, glob 315, sha 227,
                                git-ref 46, external-url 4)
    total records     1,692

Class detail: PATH 383 resolved / 16 dangling / 33 controller-labeled;
MDLINK 21 resolved / 0 dangling; PR 55 resolved / 1 dangling / 2
controller-labeled; TASKID 143 controller-labeled / 68 dangling.

## Findings for lead disposition (full table in FINDINGS.md)

Dangling beyond the controller-id class: 17.

Genuinely unresolved relative refs (the defect class this audit exists for):
  * CONTROLLER_TRANSITION/RESULT.md:67  `SLOT_BINDING/RESULT.md` -- the file
    exists at docs/evidence/agent_fleet/SLOT_BINDING/RESULT.md, but the
    reference is written from inside CONTROLLER_TRANSITION/ and resolves
    nowhere (doc-relative and repo-root both miss).
  * CONTROLLER_TRANSITION/RESULT.md:90  `FLEET_OPERATIONS_RECORD/RECORD.md` --
    same wrong-prefix pattern; target exists under docs/evidence/agent_fleet/.
  * REVIEW_FOLLOWUPS_02/RESULT.md:15  `TRANSPORT_BODY_LIMIT/MEASUREMENT.json`
    -- same wrong-prefix pattern; target exists under docs/evidence/agent_fleet/.
  * CATALOGUE_REPIN/PREREGISTRATION.md:55  `evidence/MEASUREMENT.json` --
    actual sibling is MEASUREMENT.json one level up (docs/evidence/agent_fleet/
    CATALOGUE_REPIN/MEASUREMENT.json); the written path resolves nowhere.
  * THE_MASTER_LIST.md:2407  `.git/config` -- true from a worktree (no
    .git/config there; hooks/config live in the commondir), as is
    `.git/hooks` (EVIDENCE_HYGIENE/RESULT.txt:12) and `.git/hooks/pre-commit`
    (EVIDENCE_HYGIENE/PREREGISTRATION.txt:24) -- worktree-host-specific paths,
    resolvable only from a full checkout.

PR not in history:
  * THE_MASTER_LIST.md:2449  `PR19` (also `PR24` on the same line, which DOES
    resolve -- merge b8bb5de5). No "Merge pull request #19" exists; pre-history
    or unmerged reference. Lead disposition.

Controller-plane references whose immediate window carries no pinned label:
  * THE_AGENT_FLEET.md:38  `E:\PythonChimera` (operator checkout);
  * EVIDENCE_HYGIENE/PREREGISTRATION.txt:19  `E:\PythonChimera\.gitignore`
    (operator checkout file; "repo-wide" does not match the pinned word
    "repository");
  * CATALOGUE_REPIN/PREREGISTRATION.md:42  `E:\ChimeraWork\slot-03` and
    CATALOGUE_REPIN_02/PREREGISTRATION.md:48  `E:\ChimeraWork\slot-04`
    (command lines whose window lacks a pinned label word);
  * EVIDENCE_LINK_AUDIT/PREREGISTRATION.md:89  `E:\ChimeraWork` -- this
    lane's own prereg example path (self-referential; expected);
  * THE_MASTER_LIST.md:2212  `ChimeraEngine/engine_state.json` -- gitignored
    operator-checkout store (the doc says so in prose; the path itself does
    not resolve in-repo);
  * EVIDENCE_HYGIENE/RESULT.txt:69  `python.exe` and :71 `state.sqlite`,
    SLOT_BINDING/PREREGISTRATION.md:8  `state.sqlite` -- controller/runtime
    binaries named as bare filenames, no in-repo resolution.

Dangling within the known controller-id class (68, not beyond it): 55
task-shaped ids + 12 agent ids (subagent-worker-NN) + 1 session id whose
context window (line + preceding line, token removed) carries no pinned
vocabulary word. Dominant families: agent ids in "Worker:" header lines
(pinned vocabulary has "task" but not "worker"), and ids inside tables/lists
whose labels sit further than one line away. THE_AGENT_FLEET.md:697-698 is
the largest single cluster (retired-task list). Bulk disposition candidate:
extend the pinned vocabulary with worker/agent-id labeling (e.g. "worker",
"agent", "enrollment", "owner", "assignment") in a gen-2 -- a LEAD decision;
this lane did not retune the pinned rules post-run.

## What the audit does NOT claim

  * No network: PR resolution is against this repo's own merge commits only;
    an unmerged-but-open PR reads as pr-not-in-history unless labeled open in
    its context window (pinned).
  * MASTER_LIST coverage is the pinned fleet sections (FLEET REGISTRY to EOF
    plus "Five-slot fleet adoption"), not the whole 2,692-line list.
  * IGNORED classes are recorded, not resolved: a prose slash-pair or a sha is
    not a reference and was never counted in any of the three numbers.
  * determinism: same tree + same index -> same records; the one free variable
    is the run date in the RAW_AUDIT.txt header.

## Method

Preregistration (commit 1, e26105f2) -> implementation + fixture self-test ->
retained run from the repo root (RAW_AUDIT.txt, FINDINGS.md written by the
script) -> RESULT.md (this file). Trailer `Agent: subagent-worker-09`, PR
base astra/gait-capture. Read-only against every doc; no engine, no GPU, no
DYAD, no controller mutation, no network.

## Hook note (owned, targeted, disclosed)

The evidence commit cannot pass `tools/doc_lint.py --staged` unskipped: the
retained outputs QUOTE unresolved paths verbatim (the planted fixture refs
`docs/fixture/FIXTURE.md`, `tools/no_such_dir_zz/file.py`, and the real
finding `ChimeraEngine/engine_state.json`) -- quoting them is the
deliverable, not drift. The sanctioned targeted valve the hook itself
provides (`CHIMERA_SKIP_DOCLINT=1`, .githooks/pre-commit line 108) is used
for this one commit; every other gate (bind_guard, library-guard, shazam
delegation, commit-msg attribution) still ran. Blanket `--no-verify` was
rejected as too broad, and `.doclint.allow` is outside this lane's write
scope and would wrongly hide these refs from future lint runs. Ownership:
the quoted pointers are exactly FINDINGS.md's rows, disposition owned by the
lead, not by any doc that "points" at the files.
