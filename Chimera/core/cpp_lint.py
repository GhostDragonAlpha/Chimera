"""cpp_lint — literal-aware structural checks for the static-analysis gate.

The pipeline's Stage-4 pre-check counted raw '{' and '}' with str.count(),
which false-positives on any legitimate brace inside a string or char literal:
`FString A = TEXT("{");` is valid C++ but read as "1 open, 0 close" and
blocked the whole build (2026-07-12). The fix is a mini C++ lexer that skips
string literals, char literals, and comments before counting — so the gate
fails only on genuinely unbalanced STRUCTURE, never on characters inside
text. Real syntax errors still surface at UnrealBuildTool; this gate exists
only to catch obvious generator breakage cheaply, and it must not cry wolf.
"""

from __future__ import annotations


def count_structural(content: str, open_ch: str, close_ch: str) -> tuple[int, int]:
    """(opens, closes) for open_ch/close_ch OUTSIDE string/char literals and
    // and /* */ comments. A hand-rolled lexer — small, dependency-free, and
    correct where str.count() is not."""
    opens = closes = 0
    i, n = 0, len(content)
    state = None  # None | 'line' | 'block' | 'str' | 'char'
    while i < n:
        ch = content[i]
        nxt = content[i + 1] if i + 1 < n else ""
        if state is None:
            if ch == "/" and nxt == "/":
                state = "line"; i += 2; continue
            if ch == "/" and nxt == "*":
                state = "block"; i += 2; continue
            if ch == '"':
                state = "str"; i += 1; continue
            if ch == "'":
                state = "char"; i += 1; continue
            if ch == open_ch:
                opens += 1
            elif ch == close_ch:
                closes += 1
        elif state == "line":
            if ch == "\n":
                state = None
        elif state == "block":
            if ch == "*" and nxt == "/":
                state = None; i += 2; continue
        elif state == "str":
            if ch == "\\":
                i += 2; continue          # skip escaped char (incl. \" and \\)
            if ch == '"':
                state = None
        elif state == "char":
            if ch == "\\":
                i += 2; continue
            if ch == "'":
                state = None
        i += 1
    return opens, closes


def brace_paren_errors(file_label: str, content: str) -> list:
    """The two structural balance checks, literal-aware. Returns error strings
    (empty == balanced) in the same message format the old gate used, so
    downstream parsers are unaffected."""
    errors = []
    ob, cb = count_structural(content, "{", "}")
    if ob != cb:
        errors.append(f"Unbalanced braces in {file_label}: {ob} open, {cb} close")
    op, cp = count_structural(content, "(", ")")
    if op != cp:
        errors.append(f"Unbalanced parentheses in {file_label}: {op} open, {cp} close")
    return errors
