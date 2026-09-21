"""WAVE-43 INSTRUMENT FENCE CHECK (declared instrument, P43_the_instrument).
Compares the instrumented trace stderr (.tmp/w43_receipt/instr_tr_stderr.txt)
against this lane's reproduction trace (.tmp/w43_receipt/base_tr_stderr.txt,
the a307f7b0 wave-42 live-plumbing trace, [dvfa] counted as base).
The instrumented trace must equal the base trace PLUS inserted [dvfj] lines
ONLY: every non-instrument line byte-identical, in order, over the WHOLE file
(all runs). FALSIFIER: any non-instrument line moved, changed, or missing.
"""
import sys

INSTR = ("[dvfj] ",)

base = open(".tmp/w43_receipt/base_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()
inst = open(".tmp/w43_receipt/instr_tr_stderr.txt", encoding="utf-8", errors="replace").read().splitlines()

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
    print("base lines:", len(base), " instrument lines:", len(inst), " inserted [dvfj] lines:", ins)
else:
    print("INSTRUMENT FENCE FIRED:", div); sys.exit(1)
