"""WAVE-37 FENCE CHECK (declared instrument).
Compares the composed trace stderr (.tmp/w37_receipt/w37_tr_stderr.txt) against
this lane's reproduction trace (.tmp/w37_receipt/base_tr_stderr.txt), FIRST walk
run of each. Letters: the [0,160] trace byte-identical (the [0,65] floor holds
a fortiori); the named ticks 98/107/142/160 byte-exact; THE FIRST DIVERGENCE
EXACTLY TICK 161 (the waivefire); THE SECOND DIVERGENCE EXACTLY TICK 193 (the
unloadgate -- the re-lock's engagement)."""
import re

def first_run(path):
    run = 0
    lines = {}
    order = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[dv\] t=(\d+) ", line)
        if m:
            if int(m.group(1)) == 0:
                run += 1
            if run == 2:
                break
        if run == 1:
            lines.setdefault(line[: line.rfind("t=") + 2], []).append((len(order), line))
            order.append(line)
    return order

base = first_run(".tmp/w37_receipt/base_tr_stderr.txt")
w37 = first_run(".tmp/w37_receipt/w37_tr_stderr.txt")

def tick_of(line):
    m = re.search(r"t=(\d+)", line)
    return int(m.group(1)) if m else None

FAMS = ("[dv]", "[dvp]", "[dvj]", "[dvq]", "[dvf]", "[hindstep]", "[hindgate]")
def keep(line):
    return any(line.startswith(f) for f in FAMS)

b = [l for l in base if keep(l)]
w = [l for l in w37 if keep(l)]
print("base kept lines:", len(b), " composed kept lines:", len(w))

divs = []
i = 0
while i < min(len(b), len(w)):
    if b[i] != w[i]:
        divs.append((i, tick_of(b[i]), tick_of(w[i]), b[i].rstrip(), w[i].rstrip()))
        if len(divs) >= 3:
            break
    i += 1
for k, (idx, tb, tw, lb, lw) in enumerate(divs, 1):
    print("divergence #%d at index %d: base tick=%s composed tick=%s" % (k, idx, tb, tw))
    print("  base:", lb.strip()[:170])
    print("  w37 :", lw.strip()[:170])

if divs:
    print("FIRST DIVERGENCE TICK:", divs[0][1], "(predicted exactly 161:",
          divs[0][1] == 161, ")")
    print("  the inserted line is the waivefire:", "waivefire" in divs[0][4])
    later = [(idx, tb, tw) for (idx, tb, tw, _, _) in divs if idx > divs[0][0]]
    if later:
        print("SECOND DIVERGENCE TICK:", later[0][1], "(predicted exactly 193:",
              later[0][1] == 193, ")")
    # the base lines between the divergences must be tick<=192 (identity through 192
    # on the base side except the inserted waivefire)
else:
    print("NO DIVERGENCE FOUND in the common prefix")

named = {}
for l in b:
    if l.startswith("[dv] "):
        t = tick_of(l)
        if t in (98, 107, 142, 160):
            named[t] = l
ok = True
for t, bl in named.items():
    wmatch = [l for l in w if l.startswith("[dv] ") and tick_of(l) == t]
    good = len(wmatch) == 1 and wmatch[0] == bl
    ok = ok and good
    print("named tick", t, "byte-exact:", good)
print("NAMED TICKS ALL EXACT:", ok)
