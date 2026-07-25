"""Doc audit — does the documentation line up with the code? (Groundskeeping tool.)

Checks, mechanically:
  1. Every `python -m core.<module>` mentioned in the docs -> module file exists.
  2. Every `--flag` on those same lines -> the flag string appears in that module's source.
  3. Every auto-promoted heuristic (PENDING_HEURISTICS status `promoted (auto`) ->
     its draft_rule text is actually present in an organ (CLAUDE.md / MCP_PATHWAYS.md).
  4. Scheduled tasks referenced as armed -> schtasks actually knows them.
  5. CODE->DOC: every gate postflight ENFORCES is named in at least one doc.

CHECKS 1-4 ALL RUN DOC->CODE, AND THAT IS WHY THE DOCS ROT (5 added 2026-07-16).
They catch a doc that OVER-claims — it names `core.ds`, no such module, an agent runs
it, gets an error, someone fixes it. Nothing could catch a doc that UNDER-claims: a
gate that EXISTS and no doc mentions. Nothing breaks. Nobody notices. The failure is
invisible by construction.

Measured the day check 5 was written, with 1-4 reporting only two trivial findings:

    MASTER_ONBOARDING.md                        13 gate refs   (the only current one)
    CLAUDE.md                                    6
    SUCCESSOR_RUNBOOK.md                         1
    AGENTS.md                                    0   <- a 408-line onboarding doc
    THE_COMPLETE_CHIMERA_DEVELOPMENT_CYCLE.md    0   <- this one is called "the Contract"
    GENERATION_PROTOCOL.md                       0
    RESULT_GRADING_RUBRIC.md                     0

Ten gates had shipped. Four of seven docs knew about none of them, including the
Contract. MASTER_ONBOARDING was current for exactly one reason: THE HUMAN RE-TESTED IT
every revision — the only doc that got EXECUTED, and the only one that stayed true. The
others are prose nothing runs, and prose nothing runs drifts to zero.
(Consolidated 2026-07-25: the ONE onboarding is now `ChimeraEngine/ONBOARDING.md`, which this
audit checks in MASTER_ONBOARDING's place — the human re-tests THAT one now.)

THE GATE LIST IS DERIVED FROM postflight, NEVER HAND-LISTED (beat_lint's lesson, and
this file's own check 3 exists because a hand-maintained list drifted). postflight is
where a gate becomes real — if it is imported and enforced there, an agent will meet
it, so a doc that never names it is a doc that will surprise someone at closure.

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
        # The ONBOARDING is the single most important doc in the repo — the prompt handed to every
        # agent — and NOTHING had ever checked that the commands/flags it orders an agent to run
        # actually exist (the doc most likely to be OBEYED was the doc least likely to be AUDITED).
        # Consolidated to ONE onboarding 2026-07-25: ChimeraEngine/ONBOARDING.md (was MASTER_ONBOARDING).
        WS / "ChimeraEngine" / "ONBOARDING.md", ROOT / "docs" / "THREAT_MODEL.md",
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
            # [a-z_0-9]+ — DIGITS INCLUDED (fixed 2026-07-16). It was [a-z_]+, which
            # stops dead at the `4` in `core.ds4_brain` and captures `core.ds`, so this
            # audit reported "core/ds.py DOES NOT EXIST" every night since ds4 landed.
            # Its own regex under-read its own source — the same bug as beat_lint's
            # dispatch scanner, found the same afternoon. An instrument that cries wolf
            # nightly trains everyone to ignore it, which is worse than not running.
            for m in re.finditer(r"python -m core\.([a-z_0-9]+)", line):
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
                # BY ID, not by verbatim text (fixed 2026-07-16). The exact-string match
                # reported H-2 as drifted every night — and H-2 IS in CLAUDE.md. It was
                # `amended 2026-07-13`, so the promoted text no longer matches the
                # original draft_rule word for word. The check was asking "is this exact
                # SENTENCE present?" when the honest question is "is this HEURISTIC
                # present?" — an amended rule is still a promoted rule, and a check that
                # cries wolf whenever someone IMPROVES a rule punishes the improving.
                # The id is the identity; the wording is allowed to get better.
                present = re.search(rf"\[{re.escape(hid)}[,\]]", organs)
                if m and not present and m.group(1).strip() not in organs:
                    findings.append(f"PROMOTION DRIFT: {hid} marked promoted but its rule is not in any organ")

    # 5: CODE->DOC — every gate postflight ENFORCES must be named in some doc.
    # The mirror of 1-4, and the only one that can catch a doc which UNDER-claims.
    # Derived from postflight's imports: that is where a gate becomes real, so a gate
    # named there and in no doc is a gate that will surprise an agent at closure.
    pf = ROOT / "core" / "postflight.py"
    if pf.exists():
        pf_src = pf.read_text(encoding="utf-8", errors="replace")
        enforced = set(re.findall(r"from core\.([a-z_]+) import.*\bcheck\b", pf_src))
        enforced |= set(re.findall(r"from core\.([a-z_]+) import.*\benforced\b", pf_src))
        # Where a gate must be findable. Not every doc — the ones an agent is told to
        # read. A gate absent from ALL of them is undiscoverable.
        gate_docs = [WS / "CLAUDE.md", WS / "AGENTS.md", WS / "SUCCESSOR_RUNBOOK.md",
                     ROOT / "docs" / "THE_WORKFLOW.md"]
        # WHITESPACE-NORMALIZED: markdown wraps, and "Generator\n   Guard" is the same
        # gate as "Generator Guard". My first cut matched raw text and reported
        # generator_guard as undocumented because of a LINE BREAK.
        blob = {}
        for d in gate_docs:
            if d.exists():
                blob[d.name] = re.sub(
                    r"\s+", " ", d.read_text(encoding="utf-8", errors="replace").lower())
        for gate in sorted(enforced):
            pretty = gate.replace("_", " ")            # why_gate -> "why gate"
            # The STEM too: the postflight stack in the workflow docs names gates by
            # their short name ("-> Witness (sim/telemetry node; --witnessed)"), never
            # "witness gate". That IS documentation — an agent reading it learns the
            # gate exists and what it wants — and my first cut called it undocumented.
            #
            # This over-matches (`why`, `generator` appear everywhere), so the check
            # UNDER-REPORTS. Deliberate: when an instrument must be wrong, be wrong in
            # the cheap direction. A missed doc gap costs a later notice; a false
            # "UNDOCUMENTED GATE" costs an agent an afternoon chasing noise — and this
            # audit's whole purpose is to REMOVE noise from the docs, not add it.
            stem = re.sub(r"_(gate|guard|verifier)$", "", gate)
            where = [n for n, t in blob.items()
                     if gate in t or pretty in t or re.search(rf"\b{re.escape(stem)}\b", t)]
            if not where:
                findings.append(
                    f"UNDOCUMENTED GATE: postflight enforces core.{gate} but NO doc "
                    f"names it — an agent will meet it for the first time as a refusal")
            elif len(where) == 1:
                findings.append(
                    f"THIN DOC: core.{gate} is enforced but named ONLY in {where[0]} — "
                    f"an agent reading any other doc will not know it exists")

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
