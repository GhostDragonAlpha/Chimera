"""Doc audit — does the documentation line up with the code? (Groundskeeping tool.)

Checks, mechanically:
  1. Every `python -m core.<module>` mentioned in the docs -> module file exists.
  2. Every `--flag` on those same lines -> the flag string appears in that module's source.
  3. Every auto-promoted heuristic (PENDING_HEURISTICS status `promoted (auto`) ->
     its draft_rule text is actually present in an organ (CLAUDE.md / MCP_PATHWAYS.md).
  4. Scheduled tasks referenced as armed -> schtasks actually knows them.

Exit 0 always — findings are work items, not crashes. Run via Groundskeeping_floor.
Usage: python -m core.doc_audit
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT.parent
DOCS = [WS / "CLAUDE.md", WS / "CYCLE_PROMPT.md", WS / "SUCCESSOR_RUNBOOK.md",
        WS / "AGENTS.md", WS / "README.md",
        ROOT / "docs" / "GENERATION_PROTOCOL.md", ROOT / "docs" / "SLEEPWALKER_DESIGN.md",
        ROOT / "docs" / "DEMO_ARCHITECTURE.md", ROOT / "docs" / "MCP_PATHWAYS.md",
        WS / ".roo" / "rules" / "01-chimera.md", WS / ".roo" / "rules" / "02-traps.md",
        WS / ".roo" / "rules" / "03-circadian.md"]


def main():
    findings = []

    # 1+2: module + flag references
    mod_flags = {}
    for doc in DOCS:
        if not doc.exists():
            findings.append(f"MISSING DOC: {doc}")
            continue
        for line in doc.read_text(encoding="utf-8", errors="replace").splitlines():
            # attribute flags ONLY to the command span they belong to: from this
            # `python -m core.X` up to the next `python -m` / backtick / arrow on the line
            for m in re.finditer(r"python -m core\.([a-z_]+)", line):
                mod = m.group(1)
                rest = line[m.end():]
                cut = len(rest)
                for stop in ("python -m", "`", "→", "->", ";"):
                    i = rest.find(stop)
                    if i != -1:
                        cut = min(cut, i)
                flags = set(re.findall(r"--[a-z][a-z-]+", rest[:cut]))
                mod_flags.setdefault(mod, {"docs": set(), "flags": set()})
                mod_flags[mod]["docs"].add(doc.name)
                mod_flags[mod]["flags"] |= flags
    for mod, info in sorted(mod_flags.items()):
        src = ROOT / "core" / f"{mod}.py"
        if not src.exists():
            findings.append(f"DOC->CODE: `core.{mod}` referenced in {sorted(info['docs'])} but core/{mod}.py DOES NOT EXIST")
            continue
        code = src.read_text(encoding="utf-8", errors="replace")
        for flag in sorted(info["flags"]):
            if flag not in code:
                findings.append(f"DOC->CODE: core/{mod}.py has no `{flag}` (referenced in {sorted(info['docs'])})")

    # 3: promoted rules present in organs
    pending = ROOT / "docs" / "PENDING_HEURISTICS.md"
    organs = (WS / "CLAUDE.md").read_text(encoding="utf-8", errors="replace") + \
             (ROOT / "docs" / "MCP_PATHWAYS.md").read_text(encoding="utf-8", errors="replace")
    if pending.exists():
        text = pending.read_text(encoding="utf-8", errors="replace")
        for block in re.split(r"(?m)^## ", text)[1:]:
            hid = block.split(":")[0]
            if re.search(r"(?m)^- status: promoted \(auto", block):
                m = re.search(r"(?m)^- draft_rule:\s*(.+)$", block)
                if m and m.group(1).strip() not in organs:
                    findings.append(f"PROMOTION DRIFT: {hid} marked promoted but its rule is not in any organ")

    # 4: scheduled tasks
    for task in ("ChimeraUnblock", "ChimeraSleepwalk", "ChimeraDream"):
        r = subprocess.run(["schtasks", "/Query", "/TN", task], capture_output=True, text=True)
        if r.returncode != 0:
            findings.append(f"RHYTHM DRIFT: scheduled task {task} not found (docs say armed)")

    if findings:
        print(f"[doc_audit] {len(findings)} finding(s):")
        for f in findings:
            print(f"  - {f}")
    else:
        print("[doc_audit] CLEAN — documentation lines up with the code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
