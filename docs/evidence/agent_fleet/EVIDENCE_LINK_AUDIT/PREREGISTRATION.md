# PREREGISTRATION -- docs-evidence-link-audit-01 (wave 5)

Worker: subagent-worker-09 (instance-protocol enrollment, instance id
subagent-worker-09-a8960d274e14).
Base: bf9d532b361361137e8253c00d498a9326d38fe8. Slot 3 (E:\ChimeraWork\slot-03),
branch astra/tasks/docs-evidence-link-audit-01, PR base astra/gait-capture.
Written BEFORE any implementation or test code; refined verbatim from the
controller task packet (epoch 5, lead glm53-lead-02, claim generation 1).

AUDIT-ONLY LANE: this task never edits a doc. The only written paths are under
docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/ (this file, the audit script,
raw outputs as *.txt, the findings table, RESULT.md).

## The measured claim (packet, verbatim)

STATEMENT: every cross-reference from the fleet docs set
(docs/THE_AGENT_FLEET.md, docs/AGENT_START.md, the fleet sections of
docs/THE_MASTER_LIST.md, docs/evidence/agent_fleet/**/RESULT*+PREREG*) to
files, dirs, PR urls, and controller-record ids either resolves in-repo or is
explicitly labeled as controller-plane.

PREDICTION: a deterministic audit script (written in-lane, run from repo root)
enumerates all such references, checks each against the tree, and reports:
resolved count, dangling count, controller-labeled count; dangling references
beyond the known controller-id class are listed for lead disposition; NO doc is
edited in this lane (audit-only, findings retained).

FALSIFIER: the audit mutates any doc; references silently skipped (the script's
enumeration is itself tested against a fixture doc with known-good and
known-dangling refs); or findings not retained verbatim.

## Pinned deterministic procedure (fixed now, before any run)

The audit script docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/
evidence_link_audit.py is pure and oracle-injected: it takes (a) the source
doc set, (b) a tree-existence oracle, (c) a PR-merge map, and returns one
record per enumerated reference. `--self-test` runs the planted-fixture test
against synthetic oracles; a bare run (from the repo root) runs the real tree
and the real merge map. No network is contacted; PR resolution is against the
repo's own merge commits, not the GitHub API.

SOURCE SET (pinned):
  * docs/THE_AGENT_FLEET.md -- whole file;
  * docs/AGENT_START.md -- whole file;
  * docs/THE_MASTER_LIST.md -- "fleet sections" = the contiguous fleet record
    from the `## FLEET REGISTRY` heading to end-of-file, PLUS any level-2/3
    section outside that range whose heading matches (?i)\bfleet\b or
    (?i)\bslot\b (at this base: "Five-slot fleet adoption");
  * docs/evidence/agent_fleet/**/ -- every file whose basename starts with
    RESULT or PREREG (RESULT*.md/.txt, PREREGISTRATION*.md, PREREGISTER.md).

ENUMERATION (no silent skip; every extracted candidate is classified or
IGNORED with a recorded reason):
  1. markdown links in LINK(TARGET) form -- class MDLINK (anchor split off);
  2. inline code spans `...` and plain text, tokenized on whitespace and
     quote/paren characters, each token tested against the three classes
     below in order PATH, PR, TASKID;
  3. fenced code blocks are enumerated like any other text (the docs make
     references inside them; skipping them would be a silent-skip class).

TOKEN CLASSES:
  * PATH: token contains / or \ with path characters, or is a bare filename
    ending in a known extension (py md txt json jsonl cpp h hpp html git ps1
    bat cmd sh toml yml yaml cfg ini csv db sqlite png jpg mp4 bin exe spv
    log zip). `*` or `?` present -> IGNORED(glob). A `::` node suffix is
    split off and recorded (test_module::test_name -> the file part).
  * PR: `PR #N`, `PR N`, `PRN`, bare `#N`, `pull/N`, or a github.com URL with
    /pull/N. Normalized to the number N.
  * TASKID: controller-record id shape -- word-bounded, >= 3 segments
    separated by - or _, final segment exactly two digits 01-99
    (e.g. fleet-maintenance-amendment-01, SLOT02-PARALLEL-01). Deliberately
    excludes single-separator tokens (CUDA-12) and dates/shas.
  * Everything else a line contains is not a candidate and is not extracted
    (plain prose, bare branch names, commit shas >= 7 hex chars ->
    IGNORED(sha) only when they appear in a token position with a path-like
    or id shape, external non-PR http(s) URLs -> IGNORED(external-url),
    bare markdown anchors -> IGNORED(anchor), inline node-id suffixes are
    recorded on their parent PATH record).

RESOLUTION (pinned before the run):
  * PATH, repo-relative or doc-relative: normalize (strip trailing
    punctuation/quotes and trailing /), try repo root first, then the
    referencing file's own directory (evidence sibling refs like RESULT.md),
    then -- for bare filenames only -- a basename scan of `git ls-files`.
    RESOLVED iff an existing file OR directory is hit.
  * MDLINK: the file part resolves like PATH (doc dir, then repo root); if an
    #anchor is present it must match a GitHub-style heading slug of the
    target file, else DANGLING(anchor-missing).
  * Absolute drive-letter paths (E:\ChimeraWork\...) are outside the repo:
    CONTROLLER_LABELED iff their context line (plus the immediately preceding
    line, for wrapped prose/tables) carries an explicit controller-plane
    label from the pinned vocabulary below; else DANGLING(outside-repo).
  * PR: RESOLVED iff the repo history (git log --merges) contains a merge
    commit naming pull request N ("Merge pull request #N"). If the context
    line explicitly labels it open/unmerged/pending -> CONTROLLER_LABELED;
    else DANGLING(pr-not-in-history).
  * TASKID: controller-record ids never resolve in-repo; CONTROLLER_LABELED
    iff the context (line + preceding line) carries an explicit
    controller-plane label, else DANGLING(unlabeled-controller-id).
  * CONTROLLER-PLANE LABEL VOCABULARY (pinned now, case-insensitive):
    controller, control plane, control-plane, supervisor, task, task id,
    claim, generation, checkpoint, review, integration, integrated,
    dependency, registry, snapshot, packet, slot, worktree, deployment,
    deploy, repository, branch, recovery, epoch, requeue, open, unmerged,
    pending. This vocabulary is fixed by this prereg; if the real run shows
    it misclassifies, that is a FINDING, and any retune is a NEW generation
    with its own prereg amendment -- never a silent edit.

OUTPUTS (all retained verbatim under this directory):
  * RAW_SELFTEST.txt  -- fixture test run (falsifier teeth);
  * RAW_AUDIT.txt     -- full real-repo record, one line per reference;
  * FINDINGS.md       -- the findings table; every DANGLING reference listed
    with source file, line, class, reason, verbatim token -- for lead
    disposition;
  * RESULT.md         -- counts (resolved / dangling / controller-labeled /
    ignored-with-reason), prediction scorecard, falsifier status.
  * Worktree-mutation guard: the script records `git status --porcelain`
    before and after its run; the run is invalid if any tracked doc changes.
    The lane as a whole is audited at review time by `git diff <base>` showing
    only docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/ additions.

## PREDICTIONS (scorecard to be filled in RESULT.md, no counts pre-claimed)

P1 (fixture/teeth): --self-test plants known-good and known-dangling
    references of every class (PATH file, PATH dir, MDLINK, MDLINK with
    anchor, PR merged, PR unmerged, TASKID labeled, TASKID unlabeled) in a
    fixture doc plus a distractor line (a sha, an external URL, a glob) and
    asserts every planted candidate is enumerated and classified exactly as
    planted, and every distractor is IGNORED with its reason. Any planted
    reference absent from the record = silent skip = falsifier FIRED.
P2 (real run): the script completes over the real fleet docs set from the
    repo root, emitting >= 1 record for each of the classes PATH, MDLINK,
    PR, TASKID (the fleet docs demonstrably contain all four), with the
    three counts reported.
P3 (audit-only): before/after `git status --porcelain` are identical and no
    file outside docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/ is written
    by this lane (verified at review by `git diff --name-only <base>`).

FALSIFIER STATUS: any of P1-P3 failing, any planted reference silently
skipped, any doc outside the evidence scope mutated, or findings not retained
verbatim FIRES it.

## Method

Preregistration (this commit) -> script + self-test -> raw outputs (*.txt)
-> FINDINGS.md -> RESULT.md -> trailer `Agent: subagent-worker-09`, PR base
astra/gait-capture. Read-only against every doc; no engine, no GPU, no DYAD,
no controller mutation, no network.

## GEN-1 CLARIFICATION (appended before the implementation commit, same lane)

First enumeration pass over the real fleet docs (commit-time check) showed the
PATH shape `[\w.-]+/[\w.-]+` also matches PROSE slash-pairs ("CPU/GDI",
"task/generation", "9/9", "before/after"). These are plain prose under the
pinned "everything else ... is not a candidate" clause, and are now recorded as
IGNORED(prose-slash-pair) -- never silently skipped, never counted dangling.
Deterministic rule: a slash-token with no known extension, not starting with
./ or ../, whose FIRST segment is not an existing repo directory, is prose.
Git ref tokens (astra/..., origin/...) are IGNORED(git-ref), recorded. Nothing
else changed; the label vocabulary, context window, and resolution order are
exactly as pinned above. Fixture updated to plant both classes.
