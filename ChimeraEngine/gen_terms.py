"""Generate ChimeraEngine/THE_TERMS.md from engine_state._DECL -- the single source.

The declaration (`_DECL`) is the story decomposed into the game; this renders it as the readable
term list. Run after editing the declaration (or the story):
    python ChimeraEngine/gen_terms.py
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import engine_state as ES


def _main() -> int:
    decl = ES._DECL
    note_of = {n: (t, note) for n, p, t, note in decl}
    children = {}
    for n, p, *_ in decl:
        children.setdefault(p, []).append(n)

    eng = ES.Engine()                       # live status from the ledger (read-only)
    status = eng.state["hierarchy"]

    def mark(n):
        s = status.get(n, {}).get("status", "open")
        return {"proven": "[x]", "decided": "[H]"}.get(s, "[~]" if n in ES.BUILT else "[ ]")

    def render(n, depth, out):
        t, note = note_of[n]
        out.append(f"{'  ' * depth}- {mark(n)} **{n}**" + (f" `[{t}]`" if t else "") + f" — {note}")
        for c in children.get(n, []):
            render(c, depth + 1, out)

    L = ["# THE TERMS — the game, decomposed from the primary timeline", "",
         "> **GENERATED from `engine_state._DECL` by `gen_terms.py` — do not hand-edit.** The single",
         "> source is the declaration in the engine; edit that (or the story `Chimera/docs/THE_STORY.md`),",
         "> then re-run `python ChimeraEngine/gen_terms.py`. Each term is a membrane proven through the",
         "> engine (`MCP_ENGINE.md`): `[P]` physics (measured) · `[H]` the human (decided).",
         ">",
         "> Status: `[x]` proven through the engine · `[H]` decided · `[~]` built substrate, not yet",
         "> proven through it · `[ ]` open. The tree below IS the decomposition of the story into the game.",
         ""]

    root = eng.state["seed"]
    _, rnote = note_of[root]
    L.append(f"**{mark(root)} `{root}`** — {rnote}  *(decided; the outermost membrane)*")
    L.append("")
    for pillar in children.get(root, []):
        title, quote = ES.MOVEMENTS.get(pillar, (pillar, ""))
        L.append(f"## {title}" + (f" — *\"{quote}\"*" if quote else ""))
        out = []
        render(pillar, 0, out)
        L.extend(out)
        L.append("")

    n_terms = len(decl)
    n_phys = sum(1 for n, p, t, _ in decl if t == "P")
    n_human = sum(1 for n, p, t, _ in decl if t == "H")
    n_proven = sum(1 for n in status if status[n]["status"] == "proven")
    n_built = sum(1 for n, *_ in decl if n in ES.BUILT)
    L += ["## Counts",
          f"- **{n_terms} terms** · {n_phys} physics · {n_human} the-human · "
          f"{n_proven} proven through the engine · {n_built} with built substrate (`~`).", "",
          "*The declaration is the assignment; the engine and this doc both fall out of it. "
          "Change the story to change the game.*"]

    out_path = HERE / "THE_TERMS.md"
    out_path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out_path} ({n_terms} terms; {n_proven} proven)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
