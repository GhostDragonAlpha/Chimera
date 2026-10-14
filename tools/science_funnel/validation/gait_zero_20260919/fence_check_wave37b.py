"""WAVE-37 FENCE CHECK B: the composed walk vs the RECONSTRUCTED wave-36 amended
walk (the trajectory the composition rides until the re-lock's engagement).
Letters: [161,192] byte-identical (the composed walk rides the parent law's
trajectory exactly); at tick 193 the composed walk inserts the unloadgate
L@193 (the re-lock's engagement) where the amended walk has NO fire attempt."""
import re

def first_run(path):
    run = 0
    order = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[dv\] t=(\d+) ", line)
        if m:
            if int(m.group(1)) == 0:
                run += 1
            if run == 2:
                break
        if run == 1:
            order.append(line)
    return order

amd = first_run(".tmp/w37_receipt/w36instr_tr_stderr.txt")
w37 = first_run(".tmp/w37_receipt/w37_tr_stderr.txt")

FAMS = ("[dv]", "[dvp]", "[dvj]", "[dvq]", "[dvf]", "[hindstep]", "[hindgate]")
def keep(l):
    return any(l.startswith(f) for f in FAMS)
def tick_of(l):
    m = re.search(r"\bt=(\d+)", l) or re.search(r"tick=(\d+)", l)
    return int(m.group(1)) if m else None

a = [l for l in amd if keep(l)]
w = [l for l in w37 if keep(l)]
print("amended kept:", len(a), " composed kept:", len(w))

i = 0
first_div = None
while i < min(len(a), len(w)):
    if a[i] != w[i]:
        first_div = (i, tick_of(a[i]), tick_of(w[i]), a[i].rstrip(), w[i].rstrip())
        break
    i += 1
print("FIRST DIVERGENCE vs the amended walk: index", first_div[0],
      " amended tick:", first_div[1], " composed tick:", first_div[2])
print("  amended:", first_div[3].strip()[:150])
print("  composed:", first_div[4].strip()[:150])
# all amended lines strictly before the divergence are tick<=192?
pre = all((tick_of(l) is None or tick_of(l) <= 192) for l in a[: first_div[0]])
print("all amended lines up to the divergence are tick<=192:", pre)

# the composed line at the divergence should be the unloadgate L@193
print("composed line is the unloadgate L@193:",
      "unloadgate leg=0" in first_div[4] and "tick=193" in first_div[4])
