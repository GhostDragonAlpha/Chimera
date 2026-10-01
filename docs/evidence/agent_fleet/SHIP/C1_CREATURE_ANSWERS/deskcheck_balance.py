"""deskcheck_balance.py -- C1r desk-check: brace/paren balance over the
edited engine sources via a small state machine (comments, strings, and
char literals respected). Desk-check grade only; not a compile."""

FILES = ["ChimeraEngine/engine/membrane_tick.cpp",
         "ChimeraEngine/engine/membrane_tick.hpp",
         "ChimeraEngine/engine/main.cpp"]

for f in FILES:
    src = open(f, encoding="utf-8", errors="replace").read()
    i, n = 0, len(src)
    depth_b = depth_p = 0
    state = 'code'
    while i < n:
        c = src[i]
        if state == 'code':
            if c == '/' and i + 1 < n and src[i + 1] == '/':
                state = 'line'; i += 2; continue
            if c == '/' and i + 1 < n and src[i + 1] == '*':
                state = 'block'; i += 2; continue
            if c == '"':
                state = 'str'; i += 1; continue
            if c == "'":
                state = 'chr'; i += 1; continue
            if c == '{':
                depth_b += 1
            elif c == '}':
                depth_b -= 1
            elif c == '(':
                depth_p += 1
            elif c == ')':
                depth_p -= 1
        elif state == 'line':
            if c == '\n':
                state = 'code'
        elif state == 'block':
            if c == '*' and i + 1 < n and src[i + 1] == '/':
                state = 'code'; i += 2; continue
        elif state == 'str':
            if c == '\\':
                i += 2; continue
            if c == '"':
                state = 'code'
        elif state == 'chr':
            if c == '\\':
                i += 2; continue
            if c == "'":
                state = 'code'
        i += 1
    print(f, "braces", depth_b, "parens", depth_p)
