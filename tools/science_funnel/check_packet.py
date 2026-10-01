"""Packet completeness gate for docs/packets (RULE 0 enforcement).

A packet that names no falsifier, no frozen bit-exact control, or no file
change list is not a packet -- this gate refuses it mechanically. Read-only
over the checkout: it never writes, so re-running it is always safe and its
verdict is reproducible byte-for-byte from the same tree.

Checks per docs/packets/*.md:
  1. required sections (Rule 0 admission, derivation, falsifiers, frozen
     control, performance budget, file change list, honest scope, and the
     Rule-0 admission-record pointer);
  2. the Rule-0 triple (STATEMENT / PREDICTION / FALSIFIER) inside the
     Rule-0 section;
  3. >= 3 named falsifiers, each carrying its own refusal criterion;
  4. the frozen-control section claims bit-exactness (bit-exact /
     bit-identical / ULP);
  5. the performance budget states a measured-unit budget;
  6. the file change list names >= 3 repo paths; every EXISTING path must
     exist on disk, every path marked (NEW) must at least have its parent
     directory (a stale file list is a lie about the work);
  7. the admission record names its work.* object id and admission script,
     the script exists, and the id is present in the authored program file
     (bank the record BEFORE the packet claims to exist -- RULE 0 order).

Exit codes: 0 all packets complete; 1 at least one packet incomplete;
2 environment/usage (no packets dir, no packets).
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("rule 0 admission", re.compile(r"^#{2,4}\s*.*(rule\s*0).*admission.*|"
                                    r"^#{2,4}\s*rule\s*0\b.*", re.IGNORECASE)),
    ("derivation", re.compile(r"^#{2,4}\s*.*derivation.*", re.IGNORECASE)),
    ("falsifiers", re.compile(r"^#{2,4}\s*.*falsifier.*", re.IGNORECASE)),
    ("frozen control", re.compile(r"^#{2,4}\s*.*frozen.*control.*", re.IGNORECASE)),
    ("performance budget", re.compile(r"^#{2,4}\s*.*performance\s+budget.*", re.IGNORECASE)),
    ("file change list", re.compile(r"^#{2,4}\s*.*(file-by-file|file\s+change\s+list|"
                                    r"staged\s+file\s+plan).*", re.IGNORECASE)),
    ("honest scope", re.compile(r"^#{2,4}\s*.*(non-claims|honest\s+scope).*", re.IGNORECASE)),
    ("admission record", re.compile(r"^#{2,4}\s*.*admission\s+record.*", re.IGNORECASE)),
]

RULE0_TRIPLE = [("STATEMENT", re.compile(r"\bstatement\b", re.IGNORECASE)),
                ("PREDICTION", re.compile(r"\bprediction\b", re.IGNORECASE)),
                ("FALSIFIER", re.compile(r"\bfalsifier\b", re.IGNORECASE))]

FALSIFIER_ENTRY = re.compile(r"^\s*[-*]\s*\*{0,2}F\d+\b", re.MULTILINE)
FALSIFIER_ID = re.compile(r"\bF\d+\b")
REFUSAL_WORD = re.compile(r"REFUS|REFUT", re.IGNORECASE)
BITEXACT_WORD = re.compile(r"bit-exact|bit-exactness|bit-identical|\bULP\b", re.IGNORECASE)
BUDGET_NUMBER = re.compile(r"\d+(?:\.\d+)?\s*(?:ms|s\b|x\b|\u00d7)", re.IGNORECASE)
REPO_PATH = re.compile(r"\b(?:ChimeraEngine|tools|docs|Chimera|core)/[A-Za-z0-9_./-]+")
RECORD_ID = re.compile(r"\bwork\.[a-z0-9_.]+")


def _sections(text):
    found = []
    for line in text.splitlines():
        if line.startswith("#"):
            found.append(line)
    return "\n".join(found)


def _section_body(text, heading_regex):
    """Text from a matching heading to the next same-or-higher heading."""
    lines = text.splitlines()
    start = None
    level = None
    for i, line in enumerate(lines):
        if heading_regex.match(line):
            start = i
            level = len(line) - len(line.lstrip("#"))
            break
    if start is None:
        return None
    body = []
    for line in lines[start + 1:]:
        lvl = len(line) - len(line.lstrip("#"))
        if line.startswith("#") and lvl <= level:
            break
        body.append(line)
    return "\n".join(body)


def _falsifier_entries(text):
    """List items starting with an F# id, each block up to the next entry."""
    lines = text.splitlines()
    entries = []
    current = None
    for line in lines:
        if FALSIFIER_ENTRY.match(line):
            if current is not None:
                entries.append(current)
            current = [line]
        elif current is not None:
            if line.startswith("#"):
                entries.append(current)
                current = None
            else:
                current.append(line)
    if current is not None:
        entries.append(current)
    return ["\n".join(block) for block in entries]


def check_path_list(text, repo):
    paths = []
    for match in REPO_PATH.finditer(text):
        p = match.group(0).rstrip(".")
        if p not in paths:
            paths.append(p)
    errors = []
    checked = 0
    for p in paths:
        if p.endswith("/"):
            continue  # directory mention (e.g. docs/packets/)
        absolute = repo / p
        line_start = max(0, text.find(p) - 120)
        context = text[line_start:text.find(p) + len(p) + 40]
        is_new = re.search(r"\(\s*NEW", context, re.IGNORECASE) is not None
        checked += 1
        if is_new:
            if not absolute.parent.is_dir():
                errors.append(f"  new path parent missing: {p} (parent {absolute.parent})")
        elif not absolute.exists():
            errors.append(f"  listed path does not exist on disk: {p}")
    return paths, checked, errors


def check_packet(path, repo, program_objects):
    text = path.read_text(encoding="utf-8-sig")
    errors = []
    headings = _sections(text)

    # 1. required sections
    for name, rx in REQUIRED_SECTIONS:
        if not any(rx.match(h) for h in headings.splitlines()):
            errors.append(f"  missing required section: {name}")

    # 2. rule-0 triple inside the rule-0 section
    rule0_body = None
    for line in headings.splitlines():
        if re.match(r"^#{2,4}\s*rule\s*0\b.*", line, re.IGNORECASE) and \
                "admission" in line.lower():
            rule0_body = _section_body(text, re.compile(
                r"^#{2,4}\s*rule\s*0\b.*admission.*", re.IGNORECASE))
            break
    if rule0_body is None:
        rule0_body = _section_body(text, re.compile(r"^#{2,4}\s*rule\s*0\b.*", re.IGNORECASE))
    if rule0_body is None:
        errors.append("  rule-0 section unreadable: cannot check STATEMENT/PREDICTION/FALSIFIER")
    else:
        for name, rx in RULE0_TRIPLE:
            if not rx.search(rule0_body):
                errors.append(f"  rule-0 section lacks {name} (a description survives "
                              "any result; a theory can lose -- all three required)")

    # 3. falsifiers with refusal criteria
    entries = _falsifier_entries(text)
    if len(entries) < 3:
        errors.append(f"  packet names {len(entries)} falsifiers; a packet needs >= 3 "
                      "(no falsifier, no build)")
    for entry in entries:
        fid = FALSIFIER_ID.search(entry)
        if fid and not REFUSAL_WORD.search(entry):
            errors.append(f"  falsifier {fid.group(0)} states no refusal criterion "
                          "(when does it fire?)")

    # 4. frozen control claims bit-exactness
    frozen = _section_body(text, re.compile(r"^#{2,4}\s*.*frozen.*control.*", re.IGNORECASE))
    if frozen is not None and not BITEXACT_WORD.search(frozen):
        errors.append("  frozen-control section does not claim bit-exactness "
                      "(bit-exact / bit-identical / ULP)")
    elif frozen is None and not BITEXACT_WORD.search(text):
        errors.append("  packet claims no frozen bit-exact control")

    # 5. performance budget states a number with a unit
    budget = _section_body(text, re.compile(r"^#{2,4}\s*.*performance\s+budget.*", re.IGNORECASE))
    if budget is not None and not BUDGET_NUMBER.search(budget):
        errors.append("  performance budget states no measurable budget (number + unit)")

    # 6. file list: paths exist (or NEW parents exist)
    paths, checked, path_errors = check_path_list(text, repo)
    if len({p for p in paths if not p.endswith("/")}) < 3:
        errors.append(f"  file change list names {len(paths)} repo paths; >= 3 required")
    errors.extend(path_errors)

    # 7. admission record: id + script + banked record
    record_ids = sorted(set(RECORD_ID.findall(text)))
    record_ids = [r for r in record_ids if r.startswith("work.dynamics.")]
    if not record_ids:
        errors.append("  admission record names no work.dynamics.* object id")
    script = repo / "tools/creature_graph/validation/admit_solver_packets_20260918.py"
    if not script.exists():
        errors.append("  admission script missing: "
                      "tools/creature_graph/validation/admit_solver_packets_20260918.py")
    if program_objects is not None:
        for rid in record_ids:
            if rid not in program_objects:
                errors.append(f"  admission record {rid} is NOT banked in the authored "
                              "program (bank it before the packet ships: RULE 0 order)")

    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--packets", type=Path, default=Path("docs/packets"),
                    help="directory of packet markdown files")
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2],
                    help="checkout root (paths in packets are relative to it)")
    ap.add_argument("--program", type=Path, default=None,
                    help="authored program JSON to verify banked records against "
                         "(default: <repo>/tools/creature_graph/data/authored/"
                         "project_program.json)")
    args = ap.parse_args(argv)
    repo = args.repo.resolve()
    packets_dir = (repo / args.packets).resolve() if not args.packets.is_absolute() else args.packets
    program_path = (repo / args.program) if args.program and not args.program.is_absolute() \
        else (args.program or repo / "tools/creature_graph/data/authored/project_program.json")
    program_objects = None
    try:
        if program_path.exists():
            with open(program_path, encoding="utf-8-sig") as stream:
                program_objects = {o.get("id") for o in json.load(stream).get("objects", [])}
        else:
            print(f"FAIL environment: authored program not found at {program_path} "
                  "(bank the Rule-0 records first)")
            return 2
    except (OSError, ValueError) as error:
        print(f"FAIL environment: program unreadable: {error}")
        return 2
    if not packets_dir.is_dir():
        print(f"FAIL environment: packets directory missing: {packets_dir}")
        return 2
    packets = sorted(packets_dir.glob("*.md"))
    if not packets:
        print(f"FAIL environment: no packets in {packets_dir}")
        return 2
    failed = 0
    for packet in packets:
        errors = check_packet(packet, repo, program_objects)
        if errors:
            failed += 1
            print(f"FAIL {packet.name}")
            for error in errors:
                print(error)
        else:
            print(f"PASS {packet.name}")
    if failed:
        print(f"PACKETS INCOMPLETE: {failed} of {len(packets)} refused "
              "(a packet naming no falsifier, no frozen control, or no file "
              "list is not a packet)")
        return 1
    print(f"ALL PACKETS COMPLETE ({len(packets)} packet(s): falsifier, frozen "
          "control, file list, admission record present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
