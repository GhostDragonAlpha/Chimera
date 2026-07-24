"""library_guard — enforce the one-writer rule for recovered_genomes.json.

THE_ORDER #4: the genome library had SEVEN writers, each with its own non-atomic
load-merge-dump, racing each other. The fix routed them through the single atomic owner
Construction/export_genome.py::save_library. This keeps it that way: a commit that adds a
NEW direct writer of recovered_genomes.json is refused, the same discipline as bind_guard
(network) and objective_lint (objectives). A doc can be ignored; a gate cannot.

TARGETED, not keyword-crude: a file that merely READS the library, or writes its OWN
results file, is fine. Only a WRITE whose target is recovered_genomes.json is flagged --
detected by tracing a path variable assigned the library path to a write on that variable,
plus direct `Path('...recovered_genomes...').write_text(...)`. That precision is why it
does not false-positive on phase3 (reads the library, writes phase3_recombination_results)
or train_splat_compositions (writes matter_library.json, a different file).

    python -m core.library_guard            # scan the whole tree
    python -m core.library_guard --staged   # pre-commit: only staged files
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LIBRARY = 'recovered_genomes.json'

# The sole sanctioned writer. A path, matched against the repo-relative file.
OWNER = 'Construction/export_genome.py'
SELF = 'core/library_guard.py'

SKIP_PARTS = {'node_modules', '.git', 'site-packages', 'dist', 'build', '__pycache__',
              '.venv', 'venv'}


def _writes_library(text: str) -> list:
    """Lines where this file WRITES recovered_genomes.json (not merely references it)."""
    lines = text.splitlines()
    hits = []

    # 1. a path variable assigned the library path, then written in 'w' mode or dumped to.
    lib_vars = set()
    for i, line in enumerate(lines, 1):
        m = re.match(r'\s*(\w+)\s*=\s*.*recovered_genomes\.json', line)
        if m:
            lib_vars.add(m.group(1))
    if lib_vars:
        varpat = '|'.join(re.escape(v) for v in lib_vars)
        for i, line in enumerate(lines, 1):
            # open(<libvar>, 'w') / .open('w') on the var, or a handle from it
            if re.search(rf'open\(\s*(?:{varpat})\s*,\s*["\']w', line) or \
               re.search(rf'(?:{varpat})\.(?:write_text|write_bytes|open\(["\']w)', line):
                hits.append((i, line.strip()[:100]))

    # 2. direct Path('...recovered_genomes...').write_text(...) with no intermediate var.
    for i, line in enumerate(lines, 1):
        if 'recovered_genomes' in line and re.search(r'\.write_text\(|\.write_bytes\(', line):
            hits.append((i, line.strip()[:100]))

    # de-dupe by line number
    seen, out = set(), []
    for ln, txt in hits:
        if ln not in seen:
            seen.add(ln); out.append((ln, txt))
    return out


def _skip(path: str) -> bool:
    p = path.replace('\\', '/')
    return (p.endswith(OWNER) or p.endswith(SELF) or not p.endswith('.py')
            or any(part in p for part in SKIP_PARTS))


def _staged_py() -> list:
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                          capture_output=True, text=True).stdout.strip()
    out = subprocess.run(['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'],
                         capture_output=True, text=True).stdout.splitlines()
    return [Path(root) / f for f in out if f.endswith('.py')]


def _tracked_py() -> list:
    root = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                          capture_output=True, text=True).stdout.strip()
    out = subprocess.run(['git', 'ls-files', '*.py'], capture_output=True, text=True).stdout.splitlines()
    return [Path(root) / f for f in out]


def check(paths) -> list:
    violations = []
    for p in paths:
        rel = str(p).replace('\\', '/')
        if _skip(rel):
            continue
        try:
            hits = _writes_library(Path(p).read_text(encoding='utf-8', errors='replace'))
        except (OSError, UnicodeError):
            continue
        for ln, txt in hits:
            violations.append({'file': rel, 'line': ln, 'text': txt})
    return violations


def main() -> int:
    staged = '--staged' in sys.argv
    paths = _staged_py() if staged else _tracked_py()
    v = check(paths)
    if not v:
        print(f'  [library-guard] PASS: {OWNER} is the only writer of {LIBRARY} '
              f'({len(paths)} file(s) considered)')
        return 0
    print('')
    print(f'  [library-guard] REFUSED: a file other than the owner writes {LIBRARY} directly.')
    print(f'  The library has ONE writer so competing read-modify-write races cannot corrupt')
    print(f'  it or silently drop a genome (THE_ORDER #4).')
    print('')
    for x in v:
        print(f"    {x['file']}:{x['line']}")
        print(f"        {x['text']}")
    print('')
    print(f'  Write through the owner instead:')
    print(f'      from Construction.export_genome import save_library')
    print(f'      save_library({{material_name: genome}})   # atomic, merging, locked')
    print(f'  See docs/OBJECTIVE_DESIGN.md siblings and Construction/export_genome.py.')
    print('')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
