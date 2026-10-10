import sys

path = sys.argv[1]
src = open(path, encoding='utf-8').read()

i, n = 0, len(src)
errors = []
line_no = 1
state = None            # 'single','double','template','regex', or None
stack = []              # (char, line) for [ { (
str_start = {}          # state -> line where current open string/template started
in_line_comment = False
in_block_comment = False
prev_sig = ''           # last significant char (whitespace/comments ignored)

def handle_balanced(c):
    """Return True if c was consumed as a structural delimiter."""
    global prev_sig
    if c in '[{(':
        stack.append((c, line_no))
    elif c in ')]}':
        mapping = {')':'(', ']':'[', '}':'{'}
        if not stack or stack[-1][0] != mapping[c]:
            errors.append(f"L{line_no}: unbalanced closing '{c}'")
        else:
            stack.pop()
    prev_sig = c

while i < n:
    c = src[i]
    if c == '\n':
        line_no += 1; prev_sig = '\n'; i += 1; continue
    # line comment
    if in_line_comment:
        if c == '\n':
            in_line_comment = False; prev_sig = '\n'
        i += 1; continue
    # block comment
    if in_block_comment:
        if c == '*' and i+1 < n and src[i+1] == '/':
            in_block_comment = False; i += 2; prev_sig = '*/'
        else:
            i += 1
        continue
    # not inside a string/regex/comment
    if state is None:
        if c == '/' and i+1 < n and src[i+1] == '/':
            in_line_comment = True; i += 2; continue
        if c == '/' and i+1 < n and src[i+1] == '*':
            in_block_comment = True; i += 2; continue
        # regex detection: `/` starts a regex when preceded by an operator,
        # opening bracket, comma, semicolon, or keyword-op (not a value-end).
        low = prev_sig.lower()
        kw_end = ('return','typeof','instanceof','in','of','delete','void',
                  'do','new','throw','case','await')
        prev_word = prev_sig  # identifiers handled as single chars below; approximate
        if c == '/':
            can_regex = (prev_sig == '' or prev_sig in '([{:;,&|?+-*/%!~^= \t\n\r')
            not_kw = low not in kw_end
            not_valend = prev_sig not in ')]' and not prev_sig.isalnum()
            if can_regex and not_kw and not_valend:
                state = 'regex'; i += 1; continue
        if c == "'" or c == '"' or c == '`':
            state = 'single' if c == "'" else ('double' if c == '"' else 'template')
            str_start[state] = line_no; prev_sig = c; i += 1; continue
        handle_balanced(c)
        i += 1; continue
    # inside a string / template / regex: only terminators + escapes are special.
    if state == 'regex':
        if c == '\\':
            i += 2; continue
        if c == '[':  # char class: '/' inside is literal until ']'
            j = i + 1
            while j < n and src[j] != ']':
                if src[j] == '\\': j += 2
                else: j += 1
            i = max(j+1, i+1); prev_sig = ']'; continue
        if c == '/':
            state = None; i += 1
            while i < n and src[i].isalpha(): i += 1  # flags g,i,m,s,y,u
            prev_sig = '/'; continue
        prev_sig = c; i += 1; continue
    # string or template: pass everything else to balance handler so ${ } etc. count
    if state == 'single':
        if c == '\\':
            i += 2; continue
        if c == "'":
            state = None; prev_sig = "'"; i += 1; continue
        handle_balanced(c); i += 1; continue
    if state == 'double':
        if c == '\\':
            i += 2; continue
        if c == '"':
            state = None; prev_sig = '"'; i += 1; continue
        handle_balanced(c); i += 1; continue
    if state == 'template':
        if c == '\\':
            i += 2; continue
        if c == '`':
            state = None; prev_sig = '`'; i += 1; continue
        handle_balanced(c); i += 1; continue

if state == 'single' and str_start.get('single'):
    errors.append(f"Unterminated single-quote string opened at L{str_start['single']}")
elif state == 'double' and str_start.get('double'):
    errors.append(f"Unterminated double-quote string opened at L{str_start['double']}")
elif state == 'template' and str_start.get('template'):
    errors.append(f"Unterminated template string opened at L{str_start['template']}")
for ch, ln_ in reversed(stack):
    errors.append(f"Unbalanced opening '{ch}' never closed (L{ln_})")

print(f"chars scanned: {n}  lines: {line_no}")
if errors:
    print("PARSE_FAIL:")
    for e in errors[:60]:
        print("  " + e)
    sys.exit(1)
print("PARSE_OK: no unterminated strings, balanced delimiters/braces")
