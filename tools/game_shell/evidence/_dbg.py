import sys, re
src = open(sys.argv[1], encoding='utf-8').read()

i, n = 0, len(src); line_no = 1; state = None
stack = []; in_lc = False; in_bc = False; prev_sig = ''
min_paren = 0; first_bad_close=None
def bal(c):
    global min_paren, first_bad_close
    if c in '[{(': stack.append((c, line_no))
    elif c in ')]}':
        m = {')':'(', ']':'[', '}':'{'}
        if stack and stack[-1][0]==m[c]:
            stack.pop()
            min_paren = min(min_paren, sum(1 for s in stack if s[0]=='('))
        else:
            if first_bad_close is None:
                first_bad_close=(line_no,c)

while i < n:
    c = src[i]
    if c == '\n':
        line_no+=1; prev_sig='\n'; i+=1; continue
    if in_lc:
        if c=='\n': in_lc=False; prev_sig='\n'
        i+=1; continue
    if in_bc:
        if c=='*' and i+1<n and src[i+1]=='/': in_bc=False; i+=2; prev_sig='*/'
        else: i+=1
        continue
    if state is None:
        if c=='/' and i+1<n and src[i+1]=='/': in_lc=True; i+=2; continue
        if c=='/' and i+1<n and src[i+1]=='*': in_bc=True; i+=2; continue
        low=prev_sig.lower(); kw=('return','typeof','instanceof','in','of','delete','void','do','new','throw','case','await')
        if c=='/':
            can=(prev_sig=='' or prev_sig in '([{:;,&|?+-*/%!~^=\t\n\r'); notkw=low not in kw; notval=prev_sig not in ')]' and not prev_sig.isalnum()
            if can and notkw and notval: state='regex'; i+=1; continue
        if c=="'" or c=='"' or c=='`':
            state = 'double' if c=='"' else ('single' if c=="'" else 'template')
            i+=1; continue
        bal(c); i+=1; continue
    if state=='regex':
        if c=='\\': i+=2; continue
        if c=='[':
            j=i+1
            while j<n and src[j]!=']':
                if src[j]=='\\': j+=2
                else: j+=1
            i=max(j+1,i+1); prev_sig=']'; continue
        if c=='/':
            state=None; i+=1
            while i<n and src[i].isalpha(): i+=1
            prev_sig='/'; continue
        prev_sig=c; i+=1; continue
    if state in ('single','double'):
        if c=='\\': i+=2; continue
        if (state=='single' and c=="'") or (state=='double' and c=='"'):
            state=None; prev_sig=c; i+=1; continue
        bal(c); i+=1; continue
    if state=='template':
        if c=='\\': i+=2; continue
        if c=='`': state=None; prev_sig=c; i+=1; continue
        bal(c); i+=1; continue

print("first unmatched close (line,char):", first_bad_close)
print("min paren depth seen:", min_paren)
print("final state:", state)
print("remaining stack:", stack)
