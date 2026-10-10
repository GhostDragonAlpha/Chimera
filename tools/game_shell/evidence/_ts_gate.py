import sys
from tree_sitter import Parser, Language
from tree_sitter_javascript import language as _lang_capsule

path = sys.argv[1]
src = open(path, encoding='utf-8').read()

capsule = _lang_capsule()
lang = Language(capsule)
parser = Parser(lang)
tree = parser.parse(bytes(src, 'utf-8'))

def walk(node):
    # node type names via .type in newer API; fall back to .label if present
    t = getattr(node, 'type', None)
    if t is None and hasattr(node, 'label'):
        t = node.label()
    yield t, node
    for child in node.children or []:
        yield from walk(child)

error_nodes = []
source_roots = 0
for t, node in walk(tree.root_node):
    if t == 'source_file' or t == 'program':
        source_roots += 1
    elif t and ('ERROR' in t.upper() or 'MISSING' in t.upper()):
        row = node.start_point[0] + 1
        col = node.start_point[1] + 1
        error_nodes.append((row, col, t))

print(f"root nodes parsed: {source_roots}")
if error_nodes:
    print("PARSE_FAIL: %d error/missing node(s)" % len(error_nodes))
    for row, col, t in error_nodes[:40]:
        print(f"  L{row} C{col}: {t}")
    sys.exit(1)
print("PARSE_OK: tree-sitter parsed with zero ERROR/MISSING nodes")
