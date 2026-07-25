"""Generate the declaration from the STORY -- the true single source.

Parses the ```chimera-terms``` block inside Chimera/docs/THE_STORY.md (indentation = parent
nesting; each line: `name [P|H] note`) and writes ChimeraEngine/terms_data.py, which the engine
loads as _DECL. The story is the program; this is its compile step.

    python ChimeraEngine/gen_decl.py     (re-run after editing the story's decomposition block)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORY = HERE.parent / "Chimera" / "docs" / "THE_STORY.md"


def parse(md: str):
    m = re.search(r"```chimera-terms\n(.*?)```", md, re.S)
    if not m:
        sys.exit("no ```chimera-terms``` block found in THE_STORY.md")
    decl, stack = [], []                      # stack of (level, name)
    for raw in m.group(1).splitlines():
        if not raw.strip():
            continue
        level = (len(raw) - len(raw.lstrip(" "))) // 2
        body = raw.strip()
        name, _, rest = body.partition(" ")
        tm = re.match(r"\[([PH])\]\s*(.*)", rest)
        terminal, note = (tm.group(1), tm.group(2)) if tm else ("", rest)
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else None
        decl.append((name, parent, terminal, note.strip()))
        stack.append((level, name))
    return decl


def _main() -> int:
    decl = parse(STORY.read_text(encoding="utf-8"))
    out = ['"""GENERATED from Chimera/docs/THE_STORY.md by gen_decl.py -- DO NOT EDIT.',
           '',
           'The story is the source; its ```chimera-terms``` block is the decomposition of the',
           'timeline into the game. Re-run `python ChimeraEngine/gen_decl.py` after changing it."""',
           '', 'TERMS = [']
    for n, p, t, note in decl:
        out.append(f"    ({n!r}, {None if p is None else repr(p)}, {t!r}, {note!r}),".replace("None", "None"))
    out.append("]")
    (HERE / "terms_data.py").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote terms_data.py ({len(decl)} terms) from THE_STORY.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
