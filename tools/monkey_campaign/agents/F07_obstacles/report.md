# F07 Report — the route/blocking layer: traversable routes, no invisible walls

Author: M-F07. Date: 2026-09-24. Checkout `E:/ChimeraWork/monkey-play-20260924`,
branch `monkey-play-20260924` (HEAD at start `ebc00096`). Item F07, verbatim:
"The clearing offers traversable routes; no invisible walls masquerade as
physical obstacles. Player steering needs no general autonomous pathfinding."
Contracts C14 (terrain/traversability) + C23 noted (the blocker geometry set
for camera cases). Depends on F01 + F02 + F03 + F04 (all read first; all three
data artifacts re-validated live at load).

## What was done

1. **Read the four artifacts** (F01 report/prereg, F02 report, F03
   report/HANDOFFS, F04 report/HANDOFFS) and re-proved all three data
   artifacts live (digests `aa2607df…` / `8c7d60c8…` / `b7089e78…`; file
   hashes pinned in the prereg and re-checked at every load).
2. **Froze the prereg BEFORE implementation** (`PREREGISTRATION.md`): the
   obstacle inventory (5 mounds NOT obstacles; the trunk THE rigid blocker;
   the boundary the extent rule with its visible posts; the spawn disk
   headroom), the blocking-causes table skeleton (two YES rows, two NO rows,
   zero unexplained), the corridor envelope DERIVED (W_env = 4·r_body = 1.0 m
   — F01's own frozen passing-room quantum, not a new number), three
   falsifiers (a/b/c), and the declared new scene-data paths.
3. **Implemented** (pure Python, stdlib-only):
   - `tools/monkey_campaign/data/monkey_routes/route_recipe.py` — frozen
     constants, strict intake of the three live artifacts (byte-drift
     refusal), deterministic tangent/straight route constructions,
     canonical compile, self-pinned digest, full validator.
   - `tools/monkey_campaign/data/monkey_routes/route_declaration.json` —
     the compiled route/blocking layer as data (schema
     `chimera.monkey_routes.v1`, 8,495 canonical bytes, self-pin
     `7c3ad6e86039b63324e4695abe5e5525e2693a98f9a0ef91355b804da8b8e211`).
   - `agents/F07_obstacles/verify_routes.py` — the suite: the traversal
     predicate (the ONLY route model; refuse sites are exactly the frozen
     table rows), the 801×801 @ 0.05 m grid sweep, BFS reachability +
     corridor, straight-heading R0, 10 tangent routes, edge rays, the
     blocking-causes enumeration, the Agg route map, receipts.
4. **Ran it** — 9/9 verdicts GREEN, receipts deterministic (two fresh runs
   byte-identical `run.json`, sha256 `7baaf018…48832`); declaration
   byte-identical across in-process + fresh-subprocess compiles.
5. **Recorded one honest RED→amendment cycle** (see below): the first run
   fired the frozen tangent-route construction invariant on 8/10 routes.
   The RED receipts are preserved (`receipts/run_attempt1_RED.json/.txt`),
   the construction was re-derived (falsifiers unchanged), the second run is
   green. Sibling suites re-run: F01+F02+F03 = 121/121 OK.

## Measured numbers

| Quantity | Value | Frozen bound |
|---|---|---|
| Route declaration bytes | 8,495 canonical, self-pinned | byte-identical per compile (in-process + subprocess) |
| `route_declaration_sha256` | `7c3ad6e86039b63324e4695abe5e5525e2693a98f9a0ef91355b804da8b8e211` | validator-checked |
| Committed-file sha256 | `28dff2b33e74fcc4103ac3699899b0937f6975323758d1fa142092704bf4496c` | — |
| Route grid | 801×801 @ 0.05 m (Δ = r_body/5), 8-connected, closed extent | 641,601 cells |
| Free cells / blocked | 641,494 free; 107 blocked (ALL cause B2 trunk disk); 0 B1 (closed grid); 0 N1 | counts sum exactly |
| **Reachability** | **641,494 / 641,494 free cells reachable from spawn; 0 unreachable; 0 unexplained causes** | falsifier (a) |
| Worst slope (grid sweep, physical `gradient_at`) | 0.042522 m/m at (17.0, 7.0) — == F02's worst mesh triangle | ≤ 0.05 |
| F01 grid central differences (re-derived) | 0.034606 m/m — == F01's receipt exactly | ≤ 0.05 |
| Analytic max A·π/(2R) | 0.037956 (mound 2: 0.104618·π/(2·4.329635)) | ≤ 0.05 |
| **Spawn→trunk corridor (BFS)** | min clearance 0.538 m → width 1.076 m at (11.3, 2.0) | ≥ 1.0 m (W_env) |
| **Spawn→trunk straight (R0, one heading)** | 12.229 m, 0 blocked samples, min clearance outside approach zone 0.502 m | ≥ 0.5 m |
| Corridor envelope | W_env = 4·r_body = 1.0 m; stance floor 2·r_body = 0.5 m; approach zone r_block + 2·r_body = 0.787 m | derivation in prereg |
| Tangent routes (5 mounds × L/R) | 10/10 construct; 6 PASS outright + 4 PASS-AS-DECLARED (B1-terminated on the visible edge); 0 FAIL; every mound has an outright PASS side | amended rule (below) |
| Tangent own-margin (measured min dist to mound centre) | e.g. 5.712239 vs envelope 5.712244 (deficit ≤ derived rounding tol 2.0e-5 m) | ≥ R + r_body − tol |
| Edge rays (4) | stop-short ≤ 0.05 m of the post line; nearest post ≤ 1.0 m; first refusal beyond = `f02_outside_extent` | falsifier (a) leg |
| Posts (N2) | 80; worst off-edge 0.0; ring extent 20.0; all 80 inward probes FREE (no post term in the predicate) | F04 VIS-03 NO-CLAIM |

## The blocking-causes table (zero unexplained — measured, not prose)

| id | predicate | declared physical cause | visible cause | blocks? | measured |
|---|---|---|---|---|---|
| B1 | \|x\| > 20 or \|z\| > 20 (strict >) | F01 `boundary.physical` extent rule = engine `out_of_patch` (`earth_environment.hpp:118`) | 80 ochre posts ON the edge (worst off-edge 0.0 m, ring extent 20.0, gap ≤ 1.0 m) | YES | 0 on-grid cells; edge rays stop AT the post line; beyond-query refuses `f02_outside_extent` |
| B2 | dist to trunk axis < 0.287 m | F03 analytic cylinder solid (r 0.037) + F01 body envelope (r 0.25); F04 INT-01 tangency 7.0e-16 | trunk render mesh 130v/128tri, rep. error 1.783e-4 ≤ 2e-4 | YES | 107 grid cells, all annotated |
| N1 | slope > 0.05 would be a NEW blocker | F01 `terrain.max_slope_bound` | the terrain surface itself (C14: render IS collision) | NO | 0 cells; worst 0.042522 ≤ 0.05 |
| N2 | boundary posts | none declared (F04 VIS-03 PASS-AS-DECLARED, NO-CLAIM) | the posts themselves | NO | predicate has NO post term; 80/80 inward probes free |

Unexplained causes: **0**. Every refusal in 641,601 grid cells + all route
samples maps to B1/B2; N1 never fires; N2 is structurally absent.

## Prereg misses and the amendment (recorded, not tuned away)

1. **First run: falsifier-free but V5 RED — the construction, not the scene.**
   The frozen tangent rule "extend past the mound centre plane by R + 2·r_body"
   overshoots the declared extent for boundary-adjacent mounds (mound 0 centre
   is 1.69 m from the west edge): 8/10 routes then hit B1 refusals or
   sub-envelope endpoints. The RED run is preserved
   (`receipts/run_attempt1_RED.json/.txt`). Diagnosis: the waypoint rule told
   the walker to leave the world; reachability V3 passed in the SAME run
   (routes exist), so the defect was in my construction, not the clearing.
2. **Amendment 1 (falsifiers (a)–(c) unchanged):** endpoints end at
   min(enlarged-disk exit {C, R+2·r_body} (exact half-chord
   sqrt(r·(2R+3r))), extent exit (analytic wall times)); centre-plane
   required only where the world allows it (measured: mound 3 R side is cut
   by the wall at t = 21.68 m before t_pass = 22.22 m — its far side lies
   outside the world; PASS-AS-DECLARED, other side PASS); trunk clearance
   ≥ 0.5 m at EVERY sample; wall clearance < 0.5 m only as a contiguous
   suffix terminating ON the visible edge (a slanted approach spans more
   than 0.5 m of arc length — the first "final 0.5 m of segment" wording was
   geometrically wrong and was corrected BEFORE the re-run, from the same
   measurements).
3. **Prediction scorecard (honesty rows):** "10/10 construct and verify" →
   corrected to 6 PASS + 4 PASS-AS-DECLARED (the four boundary-hugging R
   sides; declared causes). Blocked cells "≈ 104" → measured 107 (grid
   quantization, as expected). Corridor bottleneck "exactly 0.5 at the gate"
   → measured 0.502 (R0, sample step) and 0.538 (BFS grid cell) — the gate
   bound met with a small positive margin from discretization. Worst
   analytic slope "≤ 0.0471" → measured 0.037956 (the seed drew no
   extreme combination; F01's continuous bound was worst-CASE). F01/F02
   receipt numbers reproduced EXACTLY (0.034606; 0.042522 at (17, 7)).

## Falsifier verdicts (frozen set a/b/c)

- **(a) Invisible wall / unexplained blocker: NOT OBSERVED.** 641,494/641,494
  free cells reachable from the spawn (BFS, 0.05 m grid); 0 slope-refused
  cells; all 4 edge rays walk to the visible post line (stop-short ≤ one grid
  step, nearest post ≤ 1.0 m) and the first query beyond refuses
  `f02_outside_extent` — the blocking edge IS the visible edge.
- **(b) Corridor narrower than the derived envelope: NOT OBSERVED.** BFS
  corridor width 1.076 m ≥ 1.0 m (min clearance 0.538 m at (11.3, 2.0)); the
  straight R0 heading needs no pathfinding and holds ≥ 0.502 m clearance
  outside the declared approach zone; 6 tangent routes PASS outright, 4 are
  B1-terminated on the visible edge (declared cause), 0 FAIL; every mound has
  an outright around-route on at least one side.
- **(c) Any mound steeper than the 0.05 law: NOT OBSERVED.** Worst slope
  0.042522 m/m (physical gradient AND mesh triangles agree, at (17.0, 7.0));
  F01's grid law re-derives 0.034606 exactly; analytic bound 0.037956; all
  ≤ 0.05 with margin.

Supporting verdicts: V1 declaration determinism (byte-identical in-process +
subprocess; validator green); V7 posts render-only (80/80 inward probes
free — the predicate has no post term); V8 blocking-causes table closed with
zero unexplained; V9 route map (`receipts/route_map.png`: terrain, mounds,
posts, the two blockers, R0 + BFS + 10 tangent routes, clearance profiles vs
the frozen envelope).

## Honest boundaries

- **L1 only, same as F04:** everything here verifies the DECLARED scene model
  in Python. The frozen engine has no heightfield or prop contact (F04's L2
  gap statement applies unchanged); in-vivo route/walking demonstration is
  W10/G04 territory and recorded as owed.
- **The route/blocking layer is CONSUMED geometry, not new geometry:** every
  number traces to F01/F02/F03 (the suite refuses on any upstream byte
  drift). F07 owns the derivations: the envelope, the predicate, the routes,
  the table.
- **Design, not evidence:** 0.05 slope law and 4·r_body envelope are design
  derivations; F05/G04 own the evidence-based replacements (amendment path
  declared in HANDOFFS).
- **Post collision remains unclaimed** (F04 VIS-03 NO-CLAIM); a new blocker
  row would be a prereg change, never a silent collider.

## Integrity paste (git status --porcelain -uall at completion, F07 lines)

```
?? tools/monkey_campaign/agents/F07_obstacles/PREREGISTRATION.md
?? tools/monkey_campaign/agents/F07_obstacles/brief.md
?? tools/monkey_campaign/agents/F07_obstacles/HANDOFFS.md
?? tools/monkey_campaign/agents/F07_obstacles/report.md
?? tools/monkey_campaign/agents/F07_obstacles/receipts/determinism.txt
?? tools/monkey_campaign/agents/F07_obstacles/receipts/route_map.png
?? tools/monkey_campaign/agents/F07_obstacles/receipts/run.json
?? tools/monkey_campaign/agents/F07_obstacles/receipts/run.txt
?? tools/monkey_campaign/agents/F07_obstacles/receipts/run_attempt1_RED.json
?? tools/monkey_campaign/agents/F07_obstacles/receipts/run_attempt1_RED.txt
?? tools/monkey_campaign/agents/F07_obstacles/verify_routes.py
?? tools/monkey_campaign/data/monkey_routes/route_declaration.json
?? tools/monkey_campaign/data/monkey_routes/route_recipe.py
```

M-F07's footprint is EXACTLY `tools/monkey_campaign/agents/F07_obstacles/`
(11 files) plus the two declared data paths
(`data/monkey_routes/route_recipe.py`, `route_declaration.json` — declared in
the frozen prereg BEFORE implementation). No existing file was modified; no
engine C++ edits; no GPU; no servers launched; CPU-only, headless. The other
untracked paths in the full status belong to parallel sessions (TIE2, U05b,
U02's receipt) — untouched by M-F07.

Not committed (coordinator commits agent files, per campaign pattern).
