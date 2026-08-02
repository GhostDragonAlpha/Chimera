"""stamp_law.py -- put RULE 1 on every authored document, and prove none was missed.

WHY THIS EXISTS. The derivation rule was written on 2026-07-28, lived in CLAUDE.md, and was
violated on 2026-08-02 by a four-variant parameter sweep. The post-mortem found the mechanism:
the rule was in ONE paragraph of ONE long file, and the document a new context reads FIRST --
`story/README.md` -- did not carry it at all. Documentation that is not where you are looking is
documentation that does not exist.

So the fix is not "write it better". It is: every authored document in this repository carries the
same eight-line banner, and a checker can list the ones that do not.

    python tools/stamp_law.py              # report only
    python tools/stamp_law.py --apply
    python tools/stamp_law.py --check      # exit 1 if any authored doc lacks the banner

GENERATED FILES ARE DELIBERATELY SKIPPED and named in the report. A banner in a nightly-rebuilt
file is gone by morning, which is worse than absent: it reads as covered.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = "<!-- CHIMERA-LAW -->"

BANNER = f"""{MARK}
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](../docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
{MARK}
"""

# authored doc roots -- everything else is generated, vendored, or agent scratch
ROOTS = ["docs", "Chimera/docs", "ChimeraEngine", "story", "Construction", "WorldModel",
         "research_references", "core", "tools"]

# generated or regenerated: stamping them is a lie that lasts until the next build.
# `contents.md` is the sharp case -- `grow.py` rewrites it every run from the children's
# plain-words lines, so a banner in one survives until the next `python story/grow.py`.
GENERATED = {
    "DREAM_REPORT.md", "HERALD.md", "HISTORY_BOOK.md", "TASK_BOARD.md", "PENDING_HEURISTICS.md",
    "EXPECTATION_VIOLATIONS.md", "MASTER_DEVELOPMENT_DASHBOARD.md", "THE_BACKLOG.md",
    "OPERATOR_INBOX.md", "CHANNEL.md", "element_catalog.md", "contents.md", "THE_TERMS.md",
}
SKIP_DIRS = {".git", "node_modules", "vendor", "external", "Saved", "Intermediate", "Binaries",
             ".pytest_cache", ".roo", "fork_reports", "patterns", "gauntlet", "haiku_verdicts",
             "artifacts", "lm_queue", "world", "objectives", "beats", "reference_scans",
             "__pycache__", ".venv", "site-packages"}


def rel_link(p: Path) -> str:
    """docs/THE_LAW.md relative to p's directory -- a broken link is a rule nobody follows."""
    try:
        return (Path("../" * len(p.relative_to(ROOT).parent.parts)) / "docs/THE_LAW.md").as_posix()
    except ValueError:
        return "docs/THE_LAW.md"


def targets():
    seen, out = set(), []
    for m in sorted(ROOT.glob("*.md")):
        out.append(m)
        seen.add(m)
    for r in ROOTS:
        base = ROOT / r
        if not base.exists():
            continue
        for m in sorted(base.rglob("*.md")):
            if any(part in SKIP_DIRS for part in m.relative_to(ROOT).parts):
                continue
            if m not in seen:
                out.append(m)
                seen.add(m)
    return out


def stamp(p: Path, apply: bool) -> str:
    txt = p.read_text(encoding="utf8", errors="replace")
    if p.name in GENERATED:
        return "generated"
    if MARK in txt:
        return "already"
    if p.resolve() == (ROOT / "docs/THE_LAW.md").resolve():
        return "the law itself"

    # A membrane's story.md is the PRODUCT, not documentation about the product. Six lines of
    # methodology repeated 42 times through the narrative is the thing this project exists to
    # avoid. It carries the same marker in one line, so --check still sees it.
    if p.name in ("story.md", "contents.md") and "story" in p.relative_to(ROOT).parts:
        banner = (f"{MARK}\n> *Derive before you train — [THE LAW]({rel_link(p)}). "
                  f"Every number below is derived from the parent's or measured; "
                  f"none is chosen.*\n{MARK}\n")
    else:
        banner = BANNER.replace("../docs/THE_LAW.md", rel_link(p))

    lines = txt.split("\n")
    # after the H1 if there is one, otherwise at the very top
    ins = 0
    for i, ln in enumerate(lines[:5]):
        if ln.startswith("# "):
            ins = i + 1
            break
    new = "\n".join(lines[:ins] + ["", banner.rstrip()] + lines[ins:])
    if apply:
        p.write_text(new, encoding="utf8")
    return "stamped"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    counts, missing = {}, []
    for p in targets():
        r = stamp(p, a.apply and not a.check)
        counts[r] = counts.get(r, 0) + 1
        if r == "stamped" and a.check:
            missing.append(p.relative_to(ROOT).as_posix())

    for k in sorted(counts):
        print(f"  {counts[k]:>4}  {k}")
    if a.check and missing:
        print(f"\nMISSING RULE 1 -- {len(missing)} authored documents:")
        for m in missing[:40]:
            print(f"    {m}")
        return 1
    if a.check:
        print("\nevery authored document carries RULE 1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
