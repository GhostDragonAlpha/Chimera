"""WAVE-45 INSTRUMENT FENCE CHECK (declared instrument, P45_the_instrument).
Compares the instrumented trace stderr (.tmp/w45_receipt/instr_tr_stderr.txt)
against this lane's reproduction trace (.tmp/w45_receipt/base_tr_stderr.txt,
the 69e1273b wave-44 live-plumbing ship trace, [dvfa]+[dvfj]+[dvfk] counted
as base). The instrumented trace must equal the base trace PLUS inserted
[dvfl] lines ONLY: every non-instrument line byte-identical, in order, over
the WHOLE file (all runs). FALSIFIER: any non-instrument line moved, changed,
or missing.
"""
import sys

INSTR = ("[dvfl] ",)

base = open(".tmp/w45_receipt/base_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()
inst = open(".tmp/w45_receipt/instr_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()

i = j = 0
ins = 0
div = None
while i < len(base) and j < len(inst):
    if inst[j].startswith(INSTR):
        j += 1; ins += 1; continue
    if base[i] != inst[j]:
        div = (i, j, base[i][:100], inst[j][:100]); break
    i += 1; j += 1
if div is None and i < len(base):
    div = ("base tail unexplained", len(base) - i, base[i][:100], "")
if div is None and j < len(inst):
    tail = [l for l in inst[j:] if not l.startswith(INSTR)]
    if tail:
        div = ("instrument tail unexplained", len(tail), "", tail[0][:100])

if div is None:
    print("INSTRUMENT FENCE GREEN: every non-instrument line byte-identical, in order")
    print("base lines:", len(base), " instrument lines:", len(inst), " inserted [dvfl] lines:", ins)
else:
    print("INSTRUMENT FENCE FIRED:", div); sys.exit(1)
