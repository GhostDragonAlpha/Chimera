"""WAVE-35 FENCE CHECK (declared instrument).
Compares the amended trace stderr (.tmp/w35_receipt/w35_tr_stderr.txt) against
this lane's reproduction trace (.tmp/w35_receipt/base_tr_stderr.txt), FIRST walk
run of each, segmented by the t=0 restarts of the [dv] stream.
Letters: the [dv]-family lines byte-identical through tick 160 (the [0,65]
standing floor holds a fortiori); the named ticks 98/107/142/160 byte-exact;
the FIRST DIVERGENCE exactly tick 161.
"""
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

base = first_run(".tmp/w35_receipt/base_tr_stderr.txt")
w35 = first_run(".tmp/w35_receipt/w35_tr_stderr.txt")

def tick_of(line):
    m = re.search(r"t=(\d+)", line)
    return int(m.group(1)) if m else None

FAMS = ("[dv]", "[dvp]", "[dvj]", "[dvq]", "[dvf]", "[hindstep]", "[hindgate]")
def keep(line):
    return any(line.startswith(f) for f in FAMS)

b = [l for l in base if keep(l)]
w = [l for l in w35 if keep(l)]
print("base kept lines:", len(b), " amended kept lines:", len(w))

# byte-identity through 160 on the interleaved stream: compare prefix by prefix
# (the streams are tick-ordered; compare line i while both ticks <= 160)
i = 0
first_div = None
while i < min(len(b), len(w)):
    if b[i] != w[i]:
        first_div = (i, tick_of(b[i]), tick_of(w[i]), b[i].rstrip(), w[i].rstrip())
        break
    i += 1
print("first divergence index:", first_div[0] if first_div else None,
      " base tick:", first_div[1] if first_div else None,
      " amended tick:", first_div[2] if first_div else None)
if first_div:
    print("  base:", first_div[3].strip()[:160])
    print("  w35 :", first_div[4].strip()[:160])

pre160 = all(tick_of(l) is None or tick_of(l) <= 160 for l in b[: first_div[0]] if keep(l)) if first_div else None
print("all base lines up to the divergence are tick<=160:", pre160)

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
