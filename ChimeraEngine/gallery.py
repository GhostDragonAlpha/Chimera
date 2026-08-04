"""gallery.py — every proven term's end still + its RULE 0 one-liner in one browseable page.

STATEMENT: A gallery regenerated from the ledger (story/grow.py's output and each membrane's
story.md) is always correct because it reads the FILESYSTEM, not a hand-maintained index. Adding
a membrane adds its page automatically.

PREDICTION: Running gallery.py produces an HTML file where every proven term is listed with its
plain-words line, its derived numbers, and a link to its live view. Zero hand-editing.

FALSIFIER: A proven term is missing from the gallery — the regeneration missed a membrane.

Run: python ChimeraEngine/gallery.py
Output: ChimeraEngine/gallery.html

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OUT = _HERE / "gallery.html"
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE))

import splat_appearance as sa

_STORY = _HERE.parent / "story"

_PLAIN = "**In plain words —**"

_CSS = """/* gallery.css — the membrane index, one page */
:root{color-scheme:dark;--bg:#06070c;--card:#0b0e17;--line:#1e2740;--ink:#cfe0ff;--dim:#6b7899;
      --law:#7fd18a;--inst:#e8705c;--hot:#ffd98a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 system-ui,sans-serif}
h1{font-size:20px;margin:24px 24px 8px;font-weight:650}
p.sub{margin:0 24px 24px;color:var(--dim);font-size:13px;max-width:720px}
.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;padding:0 24px 40px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;
      transition:border-color .15s}
.card:hover{border-color:#41527d}
.card h2{margin:0 0 4px;font-size:15px}
.card h2 .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.card h2 .dot.law{background:var(--law)}
.card h2 .dot.inst{background:var(--inst)}
.card .plain{margin:4px 0 8px;color:#b9c8e6;font-size:13px;line-height:1.45}
.card .nums{font:11px ui-monospace,Menlo,monospace;color:var(--dim);margin:8px 0}
.card .nums i{color:var(--hot);font-style:normal}
.card .rule{font-size:11px;color:#4d587a;margin-top:6px;border-top:1px solid var(--line);padding-top:6px}
.card .rule b{color:#8ea3c8}
.card a{color:#8ea3c8;text-decoration:none;font-size:12px}
.card a:hover{color:#fff}
footer{padding:20px 24px;color:var(--dim);font-size:11px;border-top:1px solid var(--line);margin-top:20px}
"""


def _plain_of(folder: Path) -> str:
    s = folder / "story.md"
    if not s.exists():
        return ""
    for line in s.read_text(encoding="utf-8", errors="replace").splitlines():
        t = line.strip()
        if t.startswith(_PLAIN):
            return t[len(_PLAIN):].strip()
    return ""


def _rule0_of(folder: Path) -> str:
    """Extract the RULE 0 one-liner from story.md: the first line after the CHIMERA-LAW block
    that begins with 'STATEMENT:', 'THE LAW:', 'RULE 0:', or similar."""
    s = folder / "story.md"
    if not s.exists():
        return ""
    text = s.read_text(encoding="utf-8", errors="replace")
    for marker in ("STATEMENT:", "THE LAW:", "RULE 0:", "**Statement:**", "**STATEMENT:**"):
        idx = text.find(marker)
        if idx >= 0:
            line = text[idx:].split("\n")[0].strip()
            # Strip markdown bold
            line = line.replace("**", "").strip()
            if len(line) > 140:
                line = line[:140] + "…"
            return line
    return ""


def _is_instance(name: str) -> bool:
    return name[0] == 'a' and len(name) > 1 and name[1].isupper()


def build():
    """Regenerate the gallery from the live ledger."""
    terms = sa.scene_terms()
    membranes = set(sa.membrane_terms())

    cards: list[str] = []
    for term in terms:
        folder = sa._find_membrane(term)
        if folder is None:
            continue
        plain = _plain_of(folder)
        rule0 = _rule0_of(folder)
        nums = sa.term_numbers(term)
        is_inst = _is_instance(term)
        cls = "inst" if is_inst else "law"
        dot_cls = "inst" if is_inst else "law"

        num_str = " · ".join(
            f"<i>{k}</i>={_fmt(v)}" for k, v in list(nums.items())[:6]
        ) if nums else ""

        buf = sa.scene_buffer(term)
        n_grains = buf.shape[0] if buf is not None else 0

        cards.append(
            f'<div class="card">'
            f'<h2><span class="dot {dot_cls}"></span>{term}</h2>'
            f'<div class="plain">{plain}</div>'
            f'<div class="nums">{n_grains} grains' + (f" · {num_str}" if num_str else "") + '</div>'
            + (f'<div class="rule"><b>RULE 0:</b> {rule0}</div>' if rule0 else '')
            + f'<a href="/live.html" onclick="localStorage.setItem(\'chimera_scene\',\'{term}\')">view in gallery &rarr;</a>'
            f'</div>'
        )

    built_vs_total = f"{len(membranes)} built / {len(terms)} total"

    html = f"""<!doctype html><meta charset=utf-8><title>Chimera — Gallery</title>
<style>{_CSS}</style>
<h1>Chimera — Gallery of Proven Terms</h1>
<div class="gallery">
{chr(10).join(cards)}
</div>
<footer>Generated from the ledger · {built_vs_total} · never hand-edited</footer>
"""
    _OUT.write_text(html, encoding="utf-8")
    print(f"Gallery written to {_OUT} ({len(cards)} terms)")
    return _OUT


def _fmt(v):
    if isinstance(v, float):
        if abs(v) >= 1e5 or (v != 0 and abs(v) < 1e-3):
            return f"{v:.3g}"
        return f"{v:.4g}"
    return str(v)


if __name__ == "__main__":
    build()