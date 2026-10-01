"""WAVE-44 INSTRUMENT FENCE CHECK (declared instrument, P44_the_instrument).
Compares the instrumented trace stderr (.tmp/w44_receipt/instr_tr_stderr.txt)
against this lane's reproduction trace (.tmp/w44_receipt/base_tr_stderr.txt,
the 5f170542 wave-43 live-plumbing trace, [dvfa]+[dvfj] counted as base).
The instrumented trace must equal the base trace PLUS inserted [dvfk] lines
ONLY: every non-instrument line byte-identical, in order, over the WHOLE file
(all runs). FALSIFIER: any non-instrument line moved, changed, or missing.
"""
import sys

INSTR = ("[dvfk] ",)

base = open(".tmp/w44_receipt/base_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()
inst = open(".tmp/w44_receipt/instr_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()

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
    print("base lines:", len(base), " instrument lines:", len(inst), " inserted [dvfk] lines:", ins)
else:
    print("INSTRUMENT FENCE FIRED:", div); sys.exit(1)
