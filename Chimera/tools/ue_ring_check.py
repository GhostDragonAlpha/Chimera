"""Trace the UE C++ generation RING and its import boundary with current infra."""
import glob, re, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))  # repo-relative
def norm(p): return p.replace('\\', '/')

# candidate generation-ring modules (by role: generate / build / fix UE C++)
RING = ['game_code_generator', 'game_generation_orchestrator', 'code_generation_orchestrator',
        'incremental_generator', 'dsl_game_parser', 'build_validator', 'build_orchestrator',
        'generator_guard', 'auto_fixer']

paths = {norm(f): os.path.splitext(os.path.basename(f))[0] for f in glob.glob('core/**/*.py', recursive=True)}
stem2path = {}
for p, st in paths.items(): stem2path.setdefault(st, p)
ring_paths = {stem2path[s] for s in RING if s in stem2path}
loc = {}
for p in paths:
    try: loc[p] = open(p, encoding='utf-8', errors='replace').read().count('\n') + 1
    except Exception: loc[p] = 0

print('  === THE GENERATION RING ===')
for s in RING:
    p = stem2path.get(s)
    print(f"  {'FOUND' if p else 'absent':6}  {s:32} {loc.get(p,0):>6} LOC" if p else f"  absent  {s}")
print(f"  ring LOC total: {sum(loc[p] for p in ring_paths):,}")

# who imports the ring, and are they ring or current?
print('\n  === IMPORT BOUNDARY: who imports each ring module ===')
current_importers = set()
for rp in sorted(ring_paths):
    rs = paths[rp]
    users = []
    for p in paths:
        if p == rp: continue
        try: s = open(p, encoding='utf-8', errors='replace').read()
        except Exception: continue
        if re.search(rf'(?:from|import)\s+core[.\w]*\.{rs}\b|from\s+\.{rs}\s+import|import\s+.*\b{rs}\b', s):
            tag = 'ring' if p in ring_paths else 'CURRENT'
            users.append((tag, norm(p)))
            if tag == 'CURRENT': current_importers.add(norm(p))
    cur = [u for t, u in users if t == 'CURRENT']
    print(f"  {rs:32} <- {len(users):2} importers; {'CURRENT: '+str(cur) if cur else 'ring-only (severable)'}")

print(f"\n  === THE CUT POINTS (current modules that reach INTO the ring) ===")
for c in sorted(current_importers):
    print(f"    {c}")
print(f"  {len(current_importers)} current modules import the ring -- these are the edges to sever.")
