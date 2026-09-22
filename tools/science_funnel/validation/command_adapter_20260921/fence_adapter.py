"""FENCE CHECK for the typea-command-adapter lane (declared instrument).

1. UNEXERCISED: the adapter build (no argv[2]) vs the pristine 30821ef7 ship
   build -- stdout sha byte-equality (71065ac5...), plain==trace stdout, the
   FULL trace stderr byte-equality (which subsumes the [0,65] line-identity
   and the named ticks 98/107/142/160 byte-exactness, the wave-38 fence
   convention; reported explicitly anyway).
2. COMMANDED runs: vs the ship trace, BY TICK, with the command run's own
   [cmd] instrument lines excluded -- the first diverging tick must be the
   first command-affected fire (>= the issue tick, nothing before it), and
   the [0,65] window plus the named ticks must be byte-exact.
"""
import hashlib, re, sys

def lines(p): return open(p, encoding="utf-8", errors="replace").read().splitlines()
def tick_of(l, prev=-1):
    # 'tick[ =]N' (the global tick) takes precedence over 't=N' (a sub-clock's own t)
    m = (re.search(r"\btick[ =](\d+)", l) or re.search(r"\bt=(\d+)", l))
    return int(m.group(1)) if m else prev

def by_tick(ls, drop_prefix=None):
    d = {}
    cur = -1
    for l in ls:
        if drop_prefix and l.startswith(drop_prefix): continue
        cur = tick_of(l, cur)  # lines without their own tick (e.g. [pawcap]) belong to the current tick
        d.setdefault(cur, []).append(l)
    return d

def first_diff_tick(a, b, la, lb, drop=None):
    da, db = by_tick(a, drop), by_tick(b, drop)
    for t in sorted(set(da) | set(db)):
        if da.get(t) != db.get(t):
            print(f"  {la} vs {lb}: FIRST DIVERGING TICK {t}")
            for x, y in zip(da.get(t, []), db.get(t, [])):
                if x != y:
                    print("    ship:", x[:130]); print("    run :", y[:130]); break
            else:
                print("    lines only in one side: ship", len(da.get(t, [])), "run", len(db.get(t, [])))
            return t
    print(f"  {la} vs {lb}: identical")
    return -1

def named(a, b, la, lb, ticks=(98, 107, 142, 160), drop=None):
    da, db = by_tick(a, drop), by_tick(b, drop)
    for t in ticks:
        ok = da.get(t) == db.get(t)
        print(f"  named tick {t}: lines={len(da.get(t,[]))}/{len(db.get(t,[]))} byte-exact={ok}")
    bad = sum(1 for t in set(by_tick(a).keys()) | set(by_tick(b).keys()) if t <= 65 and da.get(t) != db.get(t))
    print(f"  [0,65] ticks differing: {bad}")

SHIP_TR = lines(sys.argv[1])
print("== UNEXERCISED fence ==")
p = sys.argv[2]  # adpt_tr
AD = lines(p + "_stderr.txt")
h = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
print("  stdout sha:", h(p + "_stdout.txt"), "expected 71065ac54fa988704ce29cd79cfb5cdbe0d4e2eab3f7db69b10d4b8d94517592")
print("  trace stderr byte-identical to ship:", AD == SHIP_TR)
named(SHIP_TR, AD, "SHIP", "ADPT")

print("== COMMANDED runs (ship vs run, [cmd] instrument excluded) ==")
for name, issue in (("r1_t150_v050", 150), ("r2_t150_v060", 150), ("r3_t150_v070", 150),
                    ("r4_t000_seed", 0), ("r5_t150_v130", 150), ("r6_zoh_v060", 150)):
    ls = lines(sys.argv[3] % name + "_stderr.txt")
    print(f" {name} (issue {issue}):")
    t = first_diff_tick(SHIP_TR, ls, "SHIP", name, drop="[cmd]")
    ok = t >= issue
    print(f"  first divergence >= issue tick: {ok}")
    named(SHIP_TR, ls, "SHIP", name, drop="[cmd]")
