import sys
from tree_sitter import Parser, Language
lang = Language(__import__('tree_sitter_javascript', fromlist=['language']).language())
p = Parser(lang)

def check(label, code):
    wrapped = "function f(){" + code + "}\n"
    t = p.parse(bytes(wrapped, 'utf-8'))
    errs = []
    def walk(n):
        ty = getattr(n, 'type', None)
        if ty and ('ERROR' in ty.upper() or 'MISSING' in ty.upper()):
            errs.append((n.start_point[0]+1, n.start_point[1]+1, ty))
        for c in (n.children or []): walk(c)
    walk(t.root_node)
    print(f"[{'OK' if not errs else 'FAIL'}] {label}")
    for r,c,ty in errs[:6]:
        print("   L%d C%d: %s" % (r,c,ty))

BS = chr(92)   # backslash
AP = chr(39)   # apostrophe
# Build the third literal exactly as bytes.
# displayed text after playerName: 's saved ... press 'save progress' afterwards.
content = BS+AP + "s saved lesson progress on this device. You can still press " + BS+AP + "save progress" + BS+AP + "afterwards."
third_open = AP
third_close = AP
third = third_open + content + third_close
fixed_line = "if (!confirm('Start over? This erases ' + playerName + " + third + ")) return;"
broken_line = "if (!confirm('Start over? This erases ' + playerName + " + third_open + content + BS+AP + ")) return;"

print("FIXED  line bytes:", repr(fixed_line))
check("CANDIDATE A: final apostrophe UNESCAPED (closing delim)", fixed_line)
print("BROKEN line bytes:", repr(broken_line))
check("CURRENT file: final apostrophe ESCAPED (unterminated)", broken_line)
