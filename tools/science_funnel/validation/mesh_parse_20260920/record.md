# Rule 0 record — KILLING THE PARSE COST, lane mesh-parse-20260920

Lane: `lane/mesh-parse-20260920`, branched from `9a341b5c` (the landed
real-body tip, "RECEIPT: the slice's REAL BODY measured"). Setup path:
PRIMARY — `git worktree add` from `E:/ChimeraWork/realbody-agent/repo`
succeeded on the first try (the branch-from-commit needed no lazy fetch);
`ls-remote` verified `lane/slice-real-body-20260920` == `9a341b5c` pushed,
so the fallback fetch path was never needed. Git trailer on this lane's
commits: `Agent: meshparse`. The 4090 is shared: every run here is CPU-side
(the engine boots below are the slice's own modest render loads, the same
ones the landed lane ran).

## INHERITANCE — what this lane is the successor of

The landed lane's Amendment 3 (`slice_real_body_20260920/record.md`) records
F-SLICE-LAUNCH RED, STANDING: t_first_verts = **135.73 s** against the
slice's own 10 s bar. Its isolated breakdown (`import_timing.json`):
engine ready 0.71 s, ghost build 7.92 s, gravity arm 0.026 s, and the
engine's own `/mesh_import` parse of the pinned 499,976-tri payload
**237.67 s** (variable 130–240+ s across boots; one boot was killed by the
old 180 s POST timeout, since raised to 900 s). The cost is the ENGINE's
parse, "first exercised at this scale" — the 500,000-tri cap had never been
filled before. The landed lane named this lane: engine importer performance
at cap scale. The pins this lane inherits and must not move:

- payload pin: `standing_body.obj` sha256 `bc9033bf…9111`, 249,743 verts,
  499,976 tris (`meshes_body_20260922/body_manifest.json`);
- import anchors: `/mesh_import` ok, verts 249743, tris 499976,
  volume 0.000973470353, ymin −0.134641007, ymax +0.134641007,
  winding_flipped false;
- the slice's falsifier bank (F-BODY-CLOSURE/CAP, RESTART, FALL, …) stays
  owned by the slice's scripts; this lane changes NO bar of theirs.

## THE THEORY

**STATEMENT** (someone could disagree): the 237.67 s `/mesh_import` cost is
ATTRIBUTABLE (a named phase owns it) and REMOVABLE to the slice's own launch
bar — import in the seconds class, t_first_verts <= 10 s per the fired
clause — by an ADMISSION-TIME PREPROCESSED CACHE in a format the engine's
import contract ALREADY accepts: the `'G'` glTF/GLB binary route beside the
`'O'` OBJ text route (both named in `importer.hpp`'s own contract), derived
once from the pinned payload, byte-pinned, loaded fast — with import
semantics preserved EXACTLY: the engine's closure law (`finish()`) still
audits every import, and the resident mesh state is bit-identical. The same
fix class covers the boot's second term, the ghost's 7.92 s text build: the
derived ghost bytes, serialized once and pinned, load in their place.

**PREDICTIONS** (none measured yet by anyone):

- P-COST: the 237.67 s is dominated by `parse_obj`'s text conversion
  (per-line `sscanf` over 249,743 `v` lines + 499,976 `f` lines of an
  18.5 MB text payload) — NOT by `finish()`'s linear geometry passes (the
  edge closure map, the divergence volume, the normals) and NOT by the HTTP
  layer. Numbers when measured: parse_obj is predicted > 90% of
  import_mesh's total; finish() < 5 s at 500k tris; loopback upload of
  18.5 MB < 1 s.
- P-CACHE: posting the SAME mesh as a pinned derived GLB (byte-exact f32
  POSITIONs + u32 indices, same order) through the SAME `finish()` lands
  the isolated import in the seconds class (< 10 s) and is BIT-IDENTICAL
  engine-side: /verts bytes, /topology bytes, import_stats JSON text, and
  the settled start-state sha all equal to the `'O'` route's.
- P-GHOST: the ghost's 7.92 s is compose + `np.savetxt` text formatting;
  the exact derived bytes cached and pinned load in < 1 s and are
  byte-identical (sha equality vs a fresh in-process compose, 3x).
- P-BOOT: with both caches, full-boot t_first_verts <= 10 s (the fired
  clause's bar). If the parse dies but the clause still runs red, the
  residue is the ghost's own number plus server startup, and the record
  says so — nothing tuned.

**FALSIFIERS** (named before the run; any one failing = the theory loses,
the RED is recorded and reported, not tuned):

| id | class | pass condition |
|----|-------|----------------|
| F1-PARITY | byte-identical engine-side state, cache vs slow path | the strongest comparable surface, named: same engine build, fresh `--no-restore` boot per run — (a) /verts payload sha256 equal across `'O'` and `'G'` routes; (b) /topology payload sha256 equal; (c) import_stats JSON text equal (verts/tris/volume/ymin/ymax/winding_flipped, all digits); (d) settled start-state /verts sha equal across the pair, re-measured here (the landed bank's `8c040418…` is corroborating, not assumed); ghost cache bytes sha == fresh `build_ghost_obj()` bytes sha, 3 fresh composes; scene sha == the body_manifest payload pin (unchanged). NOT weaker than the landed lane's own checks: the importer's closure refusal still runs on every import, so a poisoned cache is refused BY NAME (F-BODY-CLOSURE's classes stay enforced). |
| F2-BAR | the fired clause's bar | isolated `/mesh_import` (the landed lane's own time_import pattern, engine-in-the-loop) with the fix: t_mesh_import < 10 s; AND full-boot t_first_verts measured with the fix and reported against the 10 s bar. |
| F3-SCOPE | the frozen engine | ZERO edits under ChimeraEngine/ (git diff of the engine tree empty vs 9a341b5c); shipped-tree edits limited to tools/playable_slice/ (scene_boot.py cache loads + the pinned cache artifacts + their pin manifest) and this lane dir. Anything that cannot be held to provable zero-byte-semantics inside that boundary is RECORDED as the engine-service gap instead of built. |
| F4-DETERMINISM | byte-stable everywhere | the GLB derivation byte-stable x3 (same sha); the ghost derivation byte-stable x3; the fixed import path byte-stable x3 boots (same /verts sha, same stats text). |
| F5-CONTAINMENT | lane discipline | measurement artifacts only in tools/science_funnel/validation/mesh_parse_20260920/; caches only in tools/playable_slice/; no gait_controller.hpp, no gait_* validation, no first_skill_prestage_20260922_, no master, no shared tooling; no 4090-heavy work. |

## DERIVED, NOT TUNED (Rule 1)

- The 10 s bar is the slice's OWN launch clause (the landed lane's
  F-SLICE-LAUNCH pass condition), not this lane's chosen number.
- The GLB route is NOT a new engine surface and this lane expects to record
  NO engine-service gap: `importer.hpp`'s contract already names kind `'G'`
  (glTF 2.0 / GLB container, embedded buffers) as the second front door,
  and `finish()` — the closure law, the cap, the by-name refusals — runs
  UNCHANGED on whatever bytes arrive. The cache only precomputes the
  text→raw half. If profiling attributes the 237 s to `finish()` itself
  instead of the text parse (P-COST RED), the GLB cache alone cannot clear
  the bar and the honest outcome is the gap record plus the best OUT-OF-
  TREE proof (the instrument demonstrates the speedup class; the gap names
  the route the engine lacks). The profiling decides — before the fix is
  built.
- The ghost cache is in-scope by derivation, not appetite: the fired clause
  is the BOOT's bar, and the boot's second-largest term is the ghost build
  (7.92 s, the landed lane's own import_timing.json). Killing only the
  parse would leave the clause red by the ghost's own number — the cache
  class is the same (deterministic derived bytes, serialized once, pinned,
  loaded fast).
- Parity is measured on the engine's OWN output surfaces (/verts,
  /topology, stats JSON text, settled start sha) because the resident
  g_mesh_req state is not dumpable without engine edits, which F3 forbids.
  This is the strongest comparable surface that exists.
- The caches refuse on drift, by name, exactly like the payload pin does:
  a missing or sha-drifting cache is a boot refusal, never a silent
  re-derivation inside the timed path (that would move the cost, not kill
  it) and never a stale-body boot.

## RUN PLAN

Prereg (this file, committed) -> instrument: a lane-dir copy of
importer.cpp with phase timers, compiled standalone (out-of-tree; the
shipped tree untouched) -> cost derivation with numbers (P-COST) -> derive
the caches from the pinned payload (lane tooling) -> fences: F1 parity pair
on the engine, F4 x3 -> re-measure: isolated import + full boot
(t_first_verts) -> receipt.json with per-falsifier verdicts in THIS
directory -> tests -> commits ("Agent: meshparse") -> push ONLY
lane/mesh-parse-20260920.

Receipt: tools/science_funnel/validation/mesh_parse_20260920/receipt.json.

Agent: meshparse
