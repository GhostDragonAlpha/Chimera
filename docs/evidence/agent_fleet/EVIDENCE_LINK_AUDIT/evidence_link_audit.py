#!/usr/bin/env python3
"""evidence_link_audit.py -- deterministic cross-reference audit of the fleet docs set.

Task: docs-evidence-link-audit-01 (wave 5). AUDIT-ONLY: this script reads the
fleet docs set and writes nothing outside its own evidence directory. It never
edits a doc. Prereg: PREREGISTRATION.md in this directory (rules pinned there
BEFORE this script was written; this file implements exactly those rules).

Fleet docs set (pinned):
  * docs/THE_AGENT_FLEET.md              (whole file)
  * docs/AGENT_START.md                  (whole file)
  * docs/THE_MASTER_LIST.md              (fleet sections only: the contiguous
    record from `## FLEET REGISTRY` to EOF, plus level-2/3 sections outside
    that range whose heading matches \\bfleet\\b or \\bslot\\b)
  * docs/evidence/agent_fleet/**/RESULT*, docs/evidence/agent_fleet/**/PREREG*

Reference classes enumerated (no silent skip: every extracted candidate is
classified RESOLVED / DANGLING / CONTROLLER_LABELED or IGNORED-with-reason):
  PATH     file/dir references (backticked or plain, repo-relative,
           doc-relative, or bare filenames; drive-letter paths are
           controller-plane candidates, never in-repo).
  MDLINK   markdown LINK(TARGET) references; a #anchor must match a
           GitHub-style heading slug of the resolved target file.
  PR       `PR #N`, `PR N`, bare `#N`, `pull/N`, github PR urls; resolved
           against the repo's own merge commits (no network).
  TASKID   controller-record ids: >= 3 separator-separated segments, final
           segment exactly two digits (fleet-maintenance-amendment-01);
           labeled controller-plane by the pinned vocabulary or dangling.
  Label checks run on the context line + preceding line with the matched
  token itself removed, so an id containing the word "task" cannot
  label itself.

IGNORED classes (recorded, never silent): glob/angle tokens, commit shas,
external non-PR urls, bare anchor-link targets, git branch refs (astra/...).
Plain prose is not a candidate.

Modes:
  python docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/evidence_link_audit.py --self-test
      Planted-fixture test (the falsifier's teeth): known-good AND
      known-dangling references of every class must each be enumerated and
      classified exactly as planted; distractors must be IGNORED with reasons.
      Writes RAW_SELFTEST.txt next to this script. Exit 1 on any failure.
  python docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/evidence_link_audit.py
      Real audit; MUST run from the repo root. Writes RAW_AUDIT.txt (every
      record, verbatim) and FINDINGS.md (the dangling table for lead
      disposition). Records `git status --porcelain` before/after and fails
      if the run mutated the worktree. Exit 1 if the run was invalid.
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- pinned rules

MAIN_DOCS = ["docs/THE_AGENT_FLEET.md", "docs/AGENT_START.md"]
MASTER_LIST = "docs/THE_MASTER_LIST.md"
EVIDENCE_ROOT = "docs/evidence/agent_fleet"
EVIDENCE_PREFIXES = ("RESULT", "PREREG")

EXTS = ("py", "md", "txt", "json", "jsonl", "cpp", "h", "hpp", "html", "git",
        "ps1", "bat", "cmd", "sh", "toml", "yml", "yaml", "cfg", "ini", "csv",
        "db", "sqlite", "png", "jpg", "jpeg", "mp4", "bin", "exe", "spv",
        "log", "zip")

LABEL_VOCAB = [  # pinned in PREREGISTRATION.md; controller-plane labels
    "controller", "control plane", "control-plane", "supervisor", "task",
    "claim", "generation", "checkpoint", "review", "integration",
    "integrated", "dependency", "registry", "snapshot", "packet", "slot",
    "worktree", "deployment", "deploy", "repository", "recovery", "epoch",
    "requeue", "open", "unmerged", "pending", "branch",
]
PR_OPEN_LABELS = ["open", "unmerged", "pending"]

MDLINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)\)")
CODESPAN_RE = re.compile(r"`([^`]+)`")
PR_PLAIN_RE = re.compile(r"(?i)\bPR\s*#?\s*(\d{1,4})\b")
PR_ADJACENT_RE = re.compile(r"(?i)\bPR(\d{2,4})\b")
PR_BARE_RE = re.compile(r"(?<![\w#])#(\d{1,4})\b")
URL_PULL_RE = re.compile(r"https?://\S+?/pull/(\d{1,4})(?![0-9])", re.I)
DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
REL_PATH_RE = re.compile(r"^[\w.\-]+(?:[/\\][\w.\-]+)+$")
BARE_FILE_RE = re.compile(r"^[\w.\-]+\.(?:" + "|".join(EXTS) + r")$", re.I)
TASKID_RE = re.compile(
    r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)+"
    r"[-_](?:0[1-9]|[1-9][0-9]))(?![0-9])")
HEX_RE = re.compile(r"^(?:[0-9a-fA-F]{7,64})(?:\u2026|\.+)?$")
NODE_SPLIT_RE = re.compile(r"^(.+?[^:])::(\S+)$")

TRAIL_PUNCT = ".,;:)]}>\"'"


# ------------------------------------------------------------------ records

class Rec:
    __slots__ = ("disp", "cls", "source", "line", "token", "reason", "node",
                 "anchor", "context")

    def __init__(self, disp, cls, source, line, token, reason="", node="",
                 anchor="", context=""):
        self.disp, self.cls, self.source, self.line = disp, cls, source, line
        self.token, self.reason, self.node, self.anchor = token, reason, node, anchor
        self.context = context

    def key(self):
        return (self.source, self.line, self.cls, self.token, self.anchor,
                self.node)


def norm_token(tok: str) -> str:
    tok = tok.strip()
    tok = re.sub(r"'s$", "", tok)          # possessive: THE_X.md's
    tok = tok.strip("\"'`([{<")
    tok = tok.rstrip(TRAIL_PUNCT)
    tok = tok.rstrip("/\\")
    return tok


def tokenize(text: str):
    for part in re.split(r"[\s|,;\(\)\[\]{}'\"]+", text):
        if part:
            yield part


def label_hit(context: str, vocab) -> bool:
    low = context.lower()
    return any(w in low for w in vocab)


def ctx_without(full_ctx: str, token: str) -> str:
    """Context with the matched token itself removed (no self-labeling)."""
    return full_ctx.replace(token, " ")


# -------------------------------------------------------------- enumeration

def classify_token(tok_raw, source, lineno, full_ctx, out):
    """Test one whitespace/punct-split token against the pinned classes."""
    tok = norm_token(tok_raw)
    if not tok:
        return
    node = ""
    m = NODE_SPLIT_RE.match(tok)
    if m and (BARE_FILE_RE.match(m.group(1)) or REL_PATH_RE.match(m.group(1))
              or DRIVE_RE.match(m.group(1))):
        tok, node = m.group(1), m.group(2)
    if tok.startswith(("http://", "https://")):
        pm = URL_PULL_RE.match(tok)
        if pm:
            out.append(Rec("CAND", "PR", source, lineno, tok, context=full_ctx))
        else:
            out.append(Rec("IGNORED", "URL", source, lineno, tok,
                           reason="external-url", context=full_ctx))
        return
    if tok.startswith(("astra/", "origin/")):
        out.append(Rec("IGNORED", "GITREF", source, lineno, tok,
                       reason="git-ref", context=full_ctx))
        return
    if DRIVE_RE.match(tok):
        out.append(Rec("CAND", "PATH", source, lineno, tok, node=node,
                       context=full_ctx))
        return
    if any(c in tok for c in "*?<>"):
        out.append(Rec("IGNORED", "GLOB", source, lineno, tok, reason="glob",
                       context=full_ctx))
        return
    if HEX_RE.match(tok) and not BARE_FILE_RE.match(tok):
        out.append(Rec("IGNORED", "SHA", source, lineno, tok, reason="sha",
                       context=full_ctx))
        return
    if REL_PATH_RE.match(tok) or BARE_FILE_RE.match(tok):
        out.append(Rec("CAND", "PATH", source, lineno, tok, node=node,
                       context=full_ctx))
        return
    tm = TASKID_RE.match(tok)
    if tm:
        out.append(Rec("CAND", "TASKID", source, lineno, tm.group(1),
                       context=full_ctx))
        return
    # anything else is plain prose: not a candidate, not extracted.


def extract(source: str, numbered_lines):
    """Enumerate every candidate reference in one source file. No silent skip.

    numbered_lines: iterable of (lineno, text) with ORIGINAL line numbers.
    """
    lines = [t for _, t in numbered_lines]
    out = []
    for idx, raw in enumerate(lines):
        lineno = numbered_lines[idx][0]
        prev = lines[idx - 1] if idx > 0 else ""
        full_ctx = prev + " " + raw

        # 1. markdown links
        def link_repl(m):
            target = m.group(2)
            um = URL_PULL_RE.match(target)
            if target.startswith(("http://", "https://")):
                if um:
                    out.append(Rec("CAND", "PR", source, lineno, target,
                                   context=full_ctx))
                else:
                    out.append(Rec("IGNORED", "URL", source, lineno, target,
                                   reason="external-url", context=full_ctx))
                return " "
            if target.startswith("#"):
                out.append(Rec("IGNORED", "ANCHOR", source, lineno, target,
                               reason="anchor", context=full_ctx))
                return " "
            anchor = ""
            if "#" in target:
                target, anchor = target.split("#", 1)
            tok = norm_token(target)
            if tok:
                out.append(Rec("CAND", "MDLINK", source, lineno, tok,
                               anchor=anchor, context=full_ctx))
            return " "

        residue = MDLINK_RE.sub(link_repl, raw)

        # 2. PR patterns on the residue (code spans still present on purpose)
        def pr_repl(m):
            out.append(Rec("CAND", "PR", source, lineno, m.group(0).strip(),
                           context=full_ctx))
            return " "
        residue = PR_PLAIN_RE.sub(pr_repl, residue)
        residue = PR_ADJACENT_RE.sub(pr_repl, residue)
        residue = PR_BARE_RE.sub(pr_repl, residue)

        # 3. inline code spans -> tokenized like plain text
        spans = CODESPAN_RE.findall(residue)
        residue = CODESPAN_RE.sub(" ", residue)

        # 4. plain text + code-span contents through the same token classifier
        for tok in tokenize(residue):
            classify_token(tok, source, lineno, full_ctx, out)
        for span in spans:
            for tok in tokenize(span):
                classify_token(tok, source, lineno, full_ctx, out)

    # dedupe identical (source, line, class, token, anchor, node) records
    seen, uniq = set(), []
    for r in out:
        k = r.key()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    return uniq


# --------------------------------------------------------------- resolution

def resolve(rec: Rec, oracles):
    if rec.disp != "CAND":
        return rec
    ctx = ctx_without(rec.context, rec.token)
    if rec.cls == "PATH":
        if DRIVE_RE.match(rec.token):
            if label_hit(ctx, LABEL_VOCAB):
                rec.disp, rec.reason = "CONTROLLER_LABELED", "outside-repo:labeled"
            else:
                rec.disp, rec.reason = "DANGLING", "outside-repo:unlabeled"
            return rec
        tok = rec.token.replace("\\", "/")
        i = tok.find("#")
        if i != -1:
            tok = tok[:i]
        docdir = os.path.dirname(rec.source).replace("\\", "/")
        hits = [oracles.tree_exists(tok), oracles.doc_exists(docdir, tok)]
        if "/" not in rec.token and "\\" not in rec.token:
            hits.append(oracles.basename_exists(tok))
        if any(hits):
            rec.disp = "RESOLVED"
        else:
            # pinned prose clause: plain prose is not a reference. A
            # slash-pair with no known extension whose first segment is not
            # an existing repo dir (CPU/GDI, task/generation, 9/9, ...) is
            # prose, IGNORED with a reason -- never silently skipped and
            # never counted as a dangling path.
            has_ext = re.search(r"\.(?:" + "|".join(EXTS) + r")$", tok, re.I)
            first = tok.split("/")[0] if "/" in tok else ""
            if (not has_ext and not tok.startswith(("./", "../"))
                    and first and not oracles.tree_exists(first)):
                rec.disp = "IGNORED"
                rec.cls = "PROSE"
                rec.reason = "prose-slash-pair"
            else:
                rec.disp, rec.reason = "DANGLING", "path-not-in-tree"
        return rec
    if rec.cls == "MDLINK":
        tok = rec.token.replace("\\", "/")
        docdir = os.path.dirname(rec.source).replace("\\", "/")
        found = None
        if oracles.doc_exists(docdir, tok):
            found = os.path.normpath(os.path.join(docdir, tok)).replace("\\", "/")
        elif oracles.tree_exists(tok):
            found = os.path.normpath(tok).replace("\\", "/")
        if found is None:
            rec.disp, rec.reason = "DANGLING", "target-missing"
            return rec
        if rec.anchor:
            if rec.anchor.lower() in oracles.slugs(found):
                rec.disp = "RESOLVED"
            else:
                rec.disp, rec.reason = "DANGLING", "anchor-missing"
        else:
            rec.disp = "RESOLVED"
        return rec
    if rec.cls == "PR":
        nm = re.search(r"(\d{1,4})", rec.token)
        n = nm.group(1) if nm else ""
        if n and oracles.pr_merged(n):
            rec.disp = "RESOLVED"
        elif label_hit(ctx, PR_OPEN_LABELS):
            rec.disp, rec.reason = "CONTROLLER_LABELED", "pr-labeled-open"
        else:
            rec.disp, rec.reason = "DANGLING", "pr-not-in-history"
        return rec
    if rec.cls == "TASKID":
        if label_hit(ctx, LABEL_VOCAB):
            rec.disp, rec.reason = "CONTROLLER_LABELED", "controller-id:labeled"
        else:
            rec.disp, rec.reason = "DANGLING", "unlabeled-controller-id"
        return rec
    return rec


def run_over(sources, oracles):
    """sources: list of (source_path, [(lineno, text)]). Returns record list."""
    records = []
    for src, numbered in sources:
        for rec in extract(src, numbered):
            records.append(resolve(rec, oracles))
    return records


# ----------------------------------------------------------------- oracles

class RealOracles:
    def __init__(self, root: Path):
        self.root = root
        ls = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                            text=True, encoding="utf-8",
                            errors="replace").stdout
        self.basenames = {p.replace("\\", "/").rsplit("/", 1)[-1]
                          for p in ls.splitlines() if p}
        subj = subprocess.run(["git", "log", "--merges", "--format=%s"], cwd=root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").stdout
        self.merged = set(re.findall(r"Merge pull request #(\d{1,4})", subj))
        self._slugs = {}

    def tree_exists(self, rel):
        p = self.root / rel
        return p.is_file() or p.is_dir()

    def doc_exists(self, docdir, rel):
        p = self.root / docdir / rel
        return p.is_file() or p.is_dir()

    def basename_exists(self, name):
        return name in self.basenames

    def pr_merged(self, n):
        return n in self.merged

    def slugs(self, path):
        if path not in self._slugs:
            try:
                text = (self.root / path).read_text(encoding="utf-8",
                                                    errors="replace")
            except OSError:
                text = ""
            sl = set()
            for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", text, re.M):
                s = m.group(1).lower()
                s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
                s = re.sub(r"\s", "-", s.strip())
                sl.add(s)
            self._slugs[path] = sl
        return self._slugs[path]

    def git_status(self):
        return subprocess.run(["git", "status", "--porcelain"], cwd=self.root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace").stdout


def numbered(rel: str, root: Path):
    lines = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
    return (rel, list(enumerate(lines, start=1)))


def master_list_fleet_lines(root: Path):
    """Pinned fleet-section extraction for THE_MASTER_LIST.md (original numbers)."""
    path = root / MASTER_LIST
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    heads = []
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{2,3})\s+(.*)$", ln)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    fleet_start = None
    for i, lev, txt in heads:
        if re.search(r"FLEET REGISTRY", txt, re.I):
            fleet_start = i
            break
    in_scope = [False] * len(lines)
    if fleet_start is not None:
        for i in range(fleet_start, len(lines)):
            in_scope[i] = True
    for j, (i, lev, txt) in enumerate(heads):
        if fleet_start is not None and i >= fleet_start:
            continue
        end = heads[j + 1][0] - 1 if j + 1 < len(heads) else len(lines) - 1
        if re.search(r"\bfleet\b|\bslot\b", txt, re.I):
            for k in range(i, end + 1):
                in_scope[k] = True
    return (MASTER_LIST,
            [(k + 1, ln) for k, ln in enumerate(lines) if in_scope[k]])


def collect_sources(root: Path):
    sources = []
    for rel in MAIN_DOCS:
        sources.append(numbered(rel, root))
    sources.append(master_list_fleet_lines(root))
    ev = root / EVIDENCE_ROOT
    for p in sorted(ev.rglob("*")):
        if p.is_file() and p.name.startswith(EVIDENCE_PREFIXES):
            sources.append(numbered(p.relative_to(root).as_posix(), root))
    return sources


# --------------------------------------------------------------- self-test

FIXTURE_PATH = "docs/fixture/FIXTURE.md"

FIXTURE_TEXT = """# Fixture doc for the enumeration teeth

Known-good files: `docs/AGENT_START.md` and `tools/agent_fleet/control.py`.
Known-good dir: `tools/agent_fleet` plus bare name `control.py`.
Known-dangling: `docs/DOES_NOT_EXIST_XYZ.md` and `tools/no_such_dir_zz/file.py`.
Links: [AGENT_START](AGENT_START.md) and [PR workflow](THE_AGENT_FLEET.md#pull-request-workflow) work.
Bad anchor: [PR workflow](THE_AGENT_FLEET.md#no-such-anchor) must dangle.
Anchor-only link: [skip](#section-anchor) is ignored with a reason.
Merged PRs: PR #64, bare #51, and https://github.com/x/y/pull/62 all merged.
Also unlabeled: PR #98.
Unmerged but labeled open in this line: PR #99.
Labeled id: the controller task fleet-maintenance-amendment-01 is recorded.
Unlabeled id follows:
some-worker-task-01
Distractors: be615277 plus https://git-scm.com/docs/git-worktree plus `test_*.py` plus `astra/gait-capture`.
Prose pairs: CPU/GDI and before/after and 9/9 are not references.
Git ref: origin/astra/tasks/fleet-orient-continuation-01 merged here.
Node ref: `test_capture_window.py::test_exists` points at a real file.
"""

TREE = {
    "docs/fixture/FIXTURE.md": True,
    "docs/fixture/AGENT_START.md": True,
    "docs/AGENT_START.md": True,
    "tools/agent_fleet": True,
    "tools/agent_fleet/control.py": True,
    "THE_AGENT_FLEET.md": True,
    "test_capture_window.py": True,
}
MERGED = {"51", "62", "64"}
SLUGS = {"THE_AGENT_FLEET.md": {"pull-request-workflow"}}


class FixtureOracles:
    def tree_exists(self, rel):
        return TREE.get(rel.replace("\\", "/"), False)

    def doc_exists(self, docdir, rel):
        return TREE.get((docdir + "/" + rel).replace("\\", "/"), False)

    def basename_exists(self, name):
        return name == "control.py"

    def pr_merged(self, n):
        return n in MERGED

    def slugs(self, path):
        return SLUGS.get(path, set())


def self_test():
    lines = FIXTURE_TEXT.splitlines()
    records = run_over([(FIXTURE_PATH, list(enumerate(lines, start=1)))],
                       FixtureOracles())
    got = {(r.cls, r.token, r.anchor, r.disp, r.reason) for r in records}
    expect = [
        # (cls, token, anchor, disp, reason) -- every planted candidate
        ("PATH", "docs/AGENT_START.md", "", "RESOLVED", ""),
        ("PATH", "tools/agent_fleet/control.py", "", "RESOLVED", ""),
        ("PATH", "tools/agent_fleet", "", "RESOLVED", ""),
        ("PATH", "control.py", "", "RESOLVED", ""),
        ("PATH", "docs/DOES_NOT_EXIST_XYZ.md", "", "DANGLING", "path-not-in-tree"),
        ("PATH", "tools/no_such_dir_zz/file.py", "", "DANGLING", "path-not-in-tree"),
        ("PATH", "test_capture_window.py", "", "RESOLVED", ""),
        ("MDLINK", "AGENT_START.md", "", "RESOLVED", ""),
        ("MDLINK", "THE_AGENT_FLEET.md", "pull-request-workflow", "RESOLVED", ""),
        ("MDLINK", "THE_AGENT_FLEET.md", "no-such-anchor", "DANGLING", "anchor-missing"),
        ("PR", "PR #64", "", "RESOLVED", ""),
        ("PR", "#51", "", "RESOLVED", ""),
        ("PR", "https://github.com/x/y/pull/62", "", "RESOLVED", ""),
        ("PR", "PR #99", "", "CONTROLLER_LABELED", "pr-labeled-open"),
        ("PR", "PR #98", "", "DANGLING", "pr-not-in-history"),
        ("TASKID", "fleet-maintenance-amendment-01", "", "CONTROLLER_LABELED",
         "controller-id:labeled"),
        ("TASKID", "some-worker-task-01", "", "DANGLING", "unlabeled-controller-id"),
    ]
    failures = []
    for e in expect:
        if e not in got:
            failures.append("MISSING planted ref: %r" % (e,))
    ignores = {(r.cls, r.token, r.reason) for r in records if r.disp == "IGNORED"}
    for e in (("URL", "https://git-scm.com/docs/git-worktree", "external-url"),
              ("GLOB", "test_*.py", "glob"),
              ("ANCHOR", "#section-anchor", "anchor"),
              ("GITREF", "astra/gait-capture", "git-ref"),
              ("GITREF", "origin/astra/tasks/fleet-orient-continuation-01", "git-ref"),
              ("PROSE", "CPU/GDI", "prose-slash-pair"),
              ("PROSE", "before/after", "prose-slash-pair"),
              ("PROSE", "9/9", "prose-slash-pair")):
        if e not in ignores:
            failures.append("MISSING distractor ignore: %r" % (e,))
    if not any(r.cls == "SHA" and r.token == "be615277" and r.reason == "sha"
               for r in records):
        failures.append("MISSING sha distractor ignore: be615277")
    if not any(r.cls == "PATH" and r.node == "test_exists" for r in records):
        failures.append("MISSING node suffix on the node-ref record")
    for r in records:
        if r.disp == "CAND":
            failures.append("UNCANDIDATED record left: %r" % (r.key(),))
    found_planted = sum(1 for e in expect if e in got)
    report = []
    report.append("SELF-TEST -- docs-evidence-link-audit-01 enumeration teeth")
    report.append("fixture: %s (%d planted refs, 9 distractors)"
                  % (FIXTURE_PATH, len(expect)))
    report.append("planted found: %d/%d" % (found_planted, len(expect)))
    report.append("")
    report.append("ALL RECORDS (%d):" % len(records))
    for r in sorted(records, key=lambda r: (r.line, r.cls, r.token)):
        report.append("  L%02d %-17s %-6s %-42s anchor=%-20s node=%-11s %s" % (
            r.line, r.disp, r.cls, r.token[:42], r.anchor[:20], r.node[:11],
            r.reason))
    report.append("")
    counts = {}
    for r in records:
        counts[r.disp] = counts.get(r.disp, 0) + 1
    report.append("COUNTS: " + ", ".join("%s=%d" % kv
                                         for kv in sorted(counts.items())))
    report.append("")
    if failures:
        report.append("FAILURES (%d):" % len(failures))
        for f in failures:
            report.append("  " + f)
        report.append("FALSIFIER STATUS: FIRED (silent skip or misclassification)")
    else:
        report.append("FAILURES: 0")
        report.append("FALSIFIER STATUS: NOT TRIGGERED (every planted ref "
                      "enumerated and classified exactly; distractors ignored "
                      "with reasons)")
    return failures, "\n".join(report), records


# ---------------------------------------------------------------- real run

def real_run(root: Path):
    if not (root / "docs" / "THE_AGENT_FLEET.md").is_file():
        print("REFUSED: run from the repo root (docs/THE_AGENT_FLEET.md not found)")
        return 2
    o = RealOracles(root)
    status_before = o.git_status()
    sources = collect_sources(root)
    records = run_over(sources, o)
    status_after = o.git_status()
    mutated = status_before != status_after

    counts = {}
    for r in records:
        counts[r.disp] = counts.get(r.disp, 0) + 1
    dangling = [r for r in records if r.disp == "DANGLING"]
    beyond = [r for r in dangling if r.cls != "TASKID"]

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout.strip()
    out = []
    out.append("RAW AUDIT -- docs-evidence-link-audit-01")
    out.append("cwd: %s" % root)
    out.append("head: %s" % head)
    out.append("date: %s" % datetime.datetime.now().replace(microsecond=0).isoformat())
    out.append("sources (%d):" % len(sources))
    n_lines = 0
    for src, numbered_lines in sources:
        n_lines += len(numbered_lines)
        out.append("  %-72s lines=%d" % (src, len(numbered_lines)))
    out.append("  total in-scope lines: %d" % n_lines)
    out.append("")
    out.append("git status --porcelain BEFORE: %s"
               % (status_before.strip() or "(clean)"))
    out.append("git status --porcelain AFTER:  %s"
               % (status_after.strip() or "(clean)"))
    out.append("WORKTREE MUTATION DURING RUN: %s"
               % ("YES -- RUN INVALID (falsifier)" if mutated else "no"))
    out.append("")
    out.append("COUNTS: resolved=%d dangling=%d controller_labeled=%d ignored=%d "
               "total_records=%d"
               % (counts.get("RESOLVED", 0), counts.get("DANGLING", 0),
                  counts.get("CONTROLLER_LABELED", 0), counts.get("IGNORED", 0),
                  len(records)))
    out.append("dangling beyond the known controller-id class: %d" % len(beyond))
    out.append("")
    out.append("PR merge map (from git log --merges): %s"
               % ",".join(sorted(o.merged, key=int)))
    out.append("")
    out.append("ALL RECORDS (one line per enumerated reference; nothing skipped):")
    for r in sorted(records, key=lambda r: (r.source, r.line, r.cls, r.token)):
        out.append("[%s] class=%-6s %s:%d token=%s%s%s%s" % (
            r.disp, r.cls, r.source, r.line, r.token,
            (" anchor=" + r.anchor) if r.anchor else "",
            (" node=" + r.node) if r.node else "",
            (" reason=" + r.reason) if r.reason else ""))
    raw_path = SCRIPT_DIR / "RAW_AUDIT.txt"
    raw_path.write_text("\n".join(out) + "\n", encoding="utf-8")

    # FINDINGS.md -- the dangling table for lead disposition
    fnd = []
    fnd.append("# FINDINGS -- docs-evidence-link-audit-01 (dangling references)")
    fnd.append("")
    fnd.append("Every DANGLING reference from the fleet docs set, verbatim, for")
    fnd.append("lead disposition. `beyond-id-class` = yes for references whose")
    fnd.append("class is not the known controller-record-id class")
    fnd.append("(PATH/MDLINK/PR). Counts: resolved=%d dangling=%d"
               % (counts.get("RESOLVED", 0), counts.get("DANGLING", 0)))
    fnd.append("controller-labeled=%d ignored=%d."
               % (counts.get("CONTROLLER_LABELED", 0), counts.get("IGNORED", 0)))
    fnd.append("")
    fnd.append("| # | class | source | line | token | reason | beyond-id-class |")
    fnd.append("|---|-------|--------|------|-------|--------|-----------------|")
    for i, r in enumerate(sorted(dangling, key=lambda r: (r.source, r.line)), 1):
        fnd.append("| %d | %s | %s | %d | `%s` | %s | %s |" % (
            i, r.cls, r.source, r.line, r.token.replace("|", "\\|"),
            r.reason or "-", "no" if r.cls == "TASKID" else "yes"))
    fnd.append("")
    (SCRIPT_DIR / "FINDINGS.md").write_text("\n".join(fnd) + "\n", encoding="utf-8")

    print("counts: resolved=%d dangling=%d controller_labeled=%d ignored=%d"
          % (counts.get("RESOLVED", 0), counts.get("DANGLING", 0),
             counts.get("CONTROLLER_LABELED", 0), counts.get("IGNORED", 0)))
    print("dangling beyond controller-id class: %d" % len(beyond))
    print("raw: %s" % raw_path)
    print("findings: %s" % (SCRIPT_DIR / "FINDINGS.md"))
    if mutated:
        print("REFUSED: worktree mutated during run (see RAW_AUDIT.txt)")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="run the planted-fixture enumeration test")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.self_test:
        failures, report, _ = self_test()
        (SCRIPT_DIR / "RAW_SELFTEST.txt").write_text(report + "\n",
                                                     encoding="utf-8")
        print(report)
        return 1 if failures else 0
    return real_run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
