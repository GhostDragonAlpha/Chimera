# PREREGISTRATION — MAT2-F03 (Implement one rigid climbable trunk asset)

Card `MAT2-F03`, planning id F03, attempt
`865039032f8148f6ac0a5f6532a73984`, arrival
`arrival-6f97681152bd47bdbdfb943530771c32` (the arrival bound to the attempt in
the registry; the later same-session startup arrival
`arrival-15c5680efad1422a8c5a0a3e211375bb` found the attempt WORKING and
continued it), criteria sha256
`143a172d9531251d45952aa78c0e565b75c4409b3d7070b56109d6ef299f1ddd`
(= canonical spec digest, recipe-verified), scope sha256
`cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`.
Base revision `30cd0f75a2aac6cd8e16504ddfbabf6fa955f1e0` (sealed line: M02,
M03, M04, M06, B03, B04 merged; branch-2, attempt checkout prepared by
`worker_checkout.prepare`). Written and frozen BEFORE any candidate build or
verify run in this workspace; only read-only reconciliation (registry reads,
`git show` extraction, hashing) preceded this freeze. Frozen 2026-09-28.

done_when (verbatim): "Trunk geometry, surface IDs, material provenance and
collision representation are explicit. Material-first addition: The rigid trunk
is an explicitly reduced material object using the same contact interfaces.
Full wood growth/fracture or all tree rings are not prerequisites."
Verification profile (registry, read read-only from
`E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3`,
`state.payload -> kanban.cards[MAT2-F03].spec.ontology_qualification.task.
verification_profile`, canonical sha256
`d5b25ab9dcc5de7e15b1116f6f9c4da66b6c01d761a0913ef92443294c6bc5e7`):
id `forest`, kind `visible_static`, subject "Terrain/trunk geometry and actual
contact surfaces", views ["clearing overview", "terrain/trunk seam close-up",
"side and oblique depth checks"], diagnostic layers ["render mesh",
"collision surfaces", "normals/contact markers", "scene bounds",
"stable 3D labels"], clean_view_required true, numerical evidence required.
Falsifier (verbatim): "Rendered/collision mismatch, ghost support, missing
boundaries or off-frame probe subject fails; tags alone do not establish
contact."

## STATEMENT (frozen)

This card is a RECONCILIATION plus a material-first addition. The rigid
climbable trunk asset already exists as pinned data: `chimera.trunk_asset.v1`
(`trunk_01`, F01's pin, raw sha256 `94ff906ec5e8b8388e4de318aa3321bad9c791fbb
168e8234c371ed1d327e3f1`): exact analytic cylinder solid, radius 0.037 m,
height 1.158 m, base centre (11.976783, 0.0, 2.471766) m, axis +Y in F01's
right-handed Y-up world, 32-segment render/contact mesh (130 vertices, 128
triangles), surface ids `trunk_01.lateral` / `trunk_01.base_cap` /
`trunk_01.top_cap`, material `mat.bark.trunk_01` whose friction 0.6 is the
recorded UNEVIDENCED-PLACEHOLDER (acquisition is G04's debt, not this card's).
This attempt does NOT invent new geometry. It adds the missing material-first
layer, exactly as the card words it: the trunk becomes an explicitly reduced
material object —

1. a `chimera.material_state.v1` document (`trunk_01` as ONE closed `region`,
   single-owner matter `wood_trunk_01`, mass = declared density x measured mesh
   volume, ports carrying the same `material_contact` interface M02/M06 use);
2. a `chimera.passive_law.v1` rigid assignment (M04's `rigid` profile: "x = 0
   for any load in range; rest geometry is the only geometry") declaring the
   reduction RIGID explicitly;
3. an M06 (`chimera.local_contact.v1`) contact binding: the pinned triangle set
   (identity-mapped visual/physical mesh, per-triangle surface-id partition
   lateral 64 / base_cap 32 / top_cap 32) instantiated as pinned M06 bodies,
   thickness 0.0 m (solid region; no shell thickness invented), Coulomb mu
   s/k = 0.6/0.6 carried forward from the placeholder WITH its
   below-provisional provenance recorded, plus single-tick climb-relevant
   contact experiments (grip stick, understated-mu slip discriminator, cap
   rest) with balanced per-tick ledgers;
4. provenance that traces to real sources the way B03 did: the pinned matter
   library (`data/matter_library_1af0bbde.json`, sha256
   `de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed`)
   contains NO wood/bark entry — that absence is recorded, not papered over;
   declared density 760 kg/m3 (band 650-850) is cited from the on-disk source
   `docs/research/tree_architecture_reference.md` at base revision 30cd0f75
   (git blob `47583e73e50ffd599b674d383a89746195c2169c`, raw sha256
   `3cb871b0a1617f85d826608733add543e5d7f9b01c63e0e32770f69743880206`), which
   satisfies the library's own `researched` class definition ("cited external
   measurement with a cached source on disk") with the honesty note that the
   table states typical values with no moisture/conditions basis
   (under-specification recorded, not fabricated; proxy species white oak,
   consistent with the clearing's broadleaf-oak-like character);
5. visual evidence under the forest/visible_static profile with task_id `F03`
   (SHORT form), the REGISTRY profile object above, single gate-bound capture
   artifact, and numerical render/collision correspondence at frozen probes.

Frozen inputs (all materialized from git objects in THIS attempt checkout and
raw-hash-verified before the freeze; commits resolve in the attempt repo):

| key | commit | path | raw sha256 |
|---|---|---|---|
| trunk_declaration_json | dc7ea811 | tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |
| clearing_declaration_json | dc7ea811 | tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| clearing_recipe_py | dc7ea811 | tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py | `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc` |
| terrain_query_py | a2895755 | tools/monkey_campaign/data/monkey_clearing/terrain_query.py | `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1` |
| terrain_bundle_py | a2895755 | tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py | `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e` |
| terrain_bundle_json | a2895755 | tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| material_state_py (M01) | 30cd0f75 | tools/monkey_campaign/contributions/MAT2-M01/material_state.py | pinned at build time; recorded in checks |
| local_contact_py (M06) | 30cd0f75 | tools/monkey_campaign/contributions/MAT2-M06/local_contact.py | pinned at build time; recorded in checks |
| passive_law_py (M04) | 30cd0f75 | tools/monkey_campaign/contributions/MAT2-M04/passive_law.py | pinned at build time; recorded in checks |
| visual_capture_py | 30cd0f75 | tools/monkey_campaign/visual_capture.py | pinned at build time; recorded in checks |
| integrity_py | 30cd0f75 | tools/monkey_campaign/integrity.py | pinned at build time; recorded in checks |
| matter_library_json (B03 copy) | 30cd0f75 | tools/monkey_campaign/contributions/MAT2-B03/data/matter_library_1af0bbde.json | `de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed` |
| wood_source_md | 30cd0f75 | docs/research/tree_architecture_reference.md | `3cb871b0a1617f85d826608733add543e5d7f9b01c63e0e32770f69743880206` |

The three authority modules (M01/M06/M04) and the capture validator are used
UNMODIFIED (byte-pinned copies imported at run time). The F01 terrain/scene
load path (recipe + declaration + TerrainSurface bundle) is reused as pinned
bytes exactly as F01's PASS-reviewed receipt did.

## PREDICTIONS (frozen before the run; each with its pass bar)

- P1 geometry identity: the pinned mesh loads as 130 vertices / 128 triangles;
  per-triangle surface-id partition by the declared center-vertex rule
  (references vertex 128 -> `trunk_01.base_cap`, vertex 129 ->
  `trunk_01.top_cap`, else `trunk_01.lateral`) yields exactly 64 lateral /
  32 base_cap / 32 top_cap triangles; the mesh is closed (every edge shared by
  exactly 2 triangles) and outward-consistent (M06 `tri_area` accepts all 128;
  signed volume positive).
- P2 volume: divergence-theorem signed volume of the closed mesh V_mesh lies
  within [0.99355, 0.99362] x V_analytic where
  V_analytic = pi * R^2 * H = 0.0049803731169212051 m3 (R = 0.037,
  H = 1.158); prediction V_mesh / V_analytic = 32*sin(2*pi/32)/(2*pi)
  = 0.99358685114420575 within 1e-5 relative (inscribed 32-gon; the vertex
  rounding at 1e-6 m perturbs only at ~1e-9 relative).
- P3 mass provenance and arithmetic: m = 760 kg/m3 x V_mesh;
  3.7608092645 kg within the researched band [650, 850] kg/m3 ->
  [3.2164816078, 4.2061682564] kg; two independent summation orderings of the
  divergence integral agree within 1e-12 relative (B03 two-method pattern;
  the analytic solid volume is recorded alongside as the exact-solid
  reference, with the measured discretization difference).
- P4 material documents: `chimera.material_state.v1` document validates with
  the unmodified M01 validator (one region `trunk_01`, matter
  `wood_trunk_01` owned exactly once, port surface/material_contact);
  `chimera.passive_law.v1` document validates with the unmodified M04
  validator (profile `rigid`, assignment region `trunk_01`); bonds = [] and
  contacts = [] with the declared reasons (rigid and rooted; M06 owns
  contacts at runtime).
- P5 M06 contact binding: unmodified `local_contact.py` accepts the pinned
  triangle split as three pinned bodies (surface ids as above, matter
  `wood_trunk_01`, mu_s = mu_k = 0.6, thickness 0.0) plus the authored
  climb-grip probe (right tetrahedron, 0.1 m orthogonal edges, mass 1.0 kg,
  authored fixture) and returns balanced ledgers (|residual| <= 1e-12,
  reciprocity residual 0) for every experiment tick. Single-tick S1
  (press 0.30 m/s normal inward at `trunk_01.lateral`): mode `stick`,
  jn = 0.30 N*s within 1e-9, tangential speed arrested to <= 1e-12 m/s
  (gravity impulse 0.04905 N*s <= mu_s*jn = 0.18 N*s); measured grip capacity
  mu_s*jn/(g*dt) = 3.6697247706 kg recorded. S2 discriminator (declared
  counterfactual surface mu 0.15, clearly labeled counterfactual): mode
  `slip`, vt_post = 0.00405 m/s within 1e-9 (> 0). S3 (40 ticks resting on
  `trunk_01.top_cap`, gravity into the surface): cumulative probe
  displacement <= 2e-3 m, final tick mode `stick`/`still`, surface_b recorded
  as `trunk_01.top_cap` (surface ids flow through the M06 path).
- P6 collision/render correspondence: every lateral vertex lies within
  2e-4 m of the analytic cylinder (declared tolerance; predicted max
  = sagitta-derived 1.783e-4 m inward chord deficit rounded to the 1e-6 m
  vertex grid); all 128 triangles' vertices inside-or-on the analytic solid
  within 2e-4 m; frozen probes classified VISIBLE_EXACT / OCCLUDED /
  OFF_FRAME in every view with ZERO oracle breaches; every profile view
  contains at least one VISIBLE_EXACT trunk probe (the subject is on-frame in
  each declared view).
- P7 captures: 6 rows (3 registry profile views x diagnostic/clean), task_id
  `F03`, profile_id `forest`, tick_interval [0, 0], subject_sha256 = raw
  sha256 of `evidence/pins_materialized/trunk_declaration.json`,
  capture_sha256 = raw sha256 of the single gate-bound artifact
  `evidence/frame_V1_clearing_overview_clean.bmp`; manifest passes the
  unmodified `visual_capture.validate_manifest` against the REGISTRY profile
  object (read read-only from the sqlite registry at capture time, hash
  recorded), and `visual_gate.verify` passes on the committed bytes; all six
  committed BMPs listed under capture_layout.files with recomputed sha256s;
  clean rows carry no diagnostic layers; diagnostic rows carry all five
  profile layers and the tag bindings.
- P8 determinism: two full rebuilds in this workspace produce byte-identical
  artifact sets (checks.json, bites.json, 6 BMPs, capture_manifest.json,
  assets/*.json) — every recorded sha256 equal across runs.

## FALSIFIER BITES (fail-first; each must RAISE before the pinned pass)

- B1 ghost support: +1 cm outward radial perturbation of the collision mesh at
  a trunk probe -> the probe's oracle/collision classification must become a
  mismatch (bites the "ghost support" falsifier).
- B2 provenance fabrication: citing matter-library entry `materials.wood` ->
  refusal `unknown_matter_entry` (the pinned library has no wood entry).
- B3 missing boundary: delete the top-cap triangles -> closure refusal
  `f03_open_edges` (open surface cannot claim a volume region).
- B4 off-frame probe subject: probe displaced 155.7 degrees off-axis in V2 ->
  classification OFF_FRAME (bites "off-frame probe subject").
- B5 bad friction declaration: mu_k > mu_s into M06 `Body` -> refusal
  `bad_friction`.
- B6 ledger tamper: flip one recorded impulse sign -> `ledger_imbalance`
  refusal (per-tick ledger identity).
- B7 understated friction claimed as hold: S2's slip mode asserted as stick ->
  predicate failure (the S2/S1 discriminator must discriminate).

## PROBES AND VIEWS (frozen)

Views (F01's verified camera specs, reused byte-for-byte as camera books):
V1 clearing overview position [0, 46, -32] target [0, 0, 0] vfov 55 deg;
V2 terrain/trunk seam close-up position [10.15, 1.25, 1.35] target
[11.976783, 0.32, 2.471766] vfov 55 deg; V3 side/oblique depth position
[0, 12, -50] target [0, 0, 6] vfov 45 deg. Resolution 1280x720 (F01's), near
0.05 / far 500 (V1/V3) and 0.05 / 50 (V2), perspective, fixed_bookmark,
tick_interval [0, 0]. Every camera record carries the 16 profile-required
fields; orientation quaternions are derived from the look-at basis
(right, up, -fwd), round-trip error asserted < 1e-12.
Probes (counts frozen; positions computed from pinned inputs only):
ground grid 5x5 over (-16..16)^2 at pinned terrain height; spawn;
8 seam azimuths at radius 0.05 m around the trunk base on the pinned ground;
6 trunk lateral probes (2 azimuths facing V2 x 3 heights 0.15/0.6/1.0 m ON
the analytic surface); 1 base-cap rim probe; 1 top-cap centre probe;
4 boundary-post top probes; 1 climb-grip probe marker at the S1 contact pose.
Total 28 probes. Classification bar: zero oracle breaches (a probe's declared
surface must be the first surface hit by its view ray within the declared
tolerances); every view >= 1 VISIBLE_EXACT trunk probe; exact
VISIBLE/OCCLUDED/OFF_FRAME splits are measured and recorded, not predicted.

## CAPTURE BINDING (frozen)

task_id `F03` (SHORT form, campaign schema); run_id
`mat2-f03-trunk-20260928-86503903`; profile object = the registry's
`verification_profile` for MAT2-F03 read READ-ONLY from
`E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` (URI mode=ro), its
canonical sha256 recorded in the receipt; single gate-bound artifact =
`evidence/frame_V1_clearing_overview_clean.bmp`; subject =
`evidence/pins_materialized/trunk_declaration.json`. The registry read and
validator runs happen BEFORE renders are accepted; acceptance itself belongs
to the independent visual reviewer (this build claims structural validity and
binding, not visual acceptance).

## AMENDMENT A3 (disclosed contact-instantiation scoping; committed BEFORE the build)

Reconciliation also measured how the unmodified M06 law treats the SPLIT
asset: because the seam rings are EXACT duplicates (Amendment A2), lateral and
cap triangles from two DIFFERENT pinned bodies sit at gap-0 contact, and
`local_contact.solve_tick` refuses a both-pinned contact pair with
`nonfinite_state` (M06's denominator inv_ma + inv_mb = 0). Corrections:

1. P5's instantiation clause is scoped: each experiment instantiates exactly
   the declared parts it touches — S1/S2 the `trunk_01.lateral` body plus the
   probe, S3 both cap bodies plus the probe (the caps never touch each
   other). All three parts are still constructed through M06's `Body`
   validator in every experiment (areas, indices, friction eagerly checked),
   and the surface-id flow bars are unchanged (S1 surface_b
   `trunk_01.lateral`; S3 surface_b `trunk_01.top_cap`).
2. The full-split co-instantiation refusal is RECORDED as a measured property
   of the duplicated-ring mesh under the pinned contact law (outcome refused,
   code `nonfinite_state`), not silently avoided.
3. No friction, press, mass, bar or bite is changed.

Frozen 2026-09-28, before any build/verify run in this workspace.

## AMENDMENT A2 (disclosed measured-topology correction; committed BEFORE the build)

Reconciliation measured the pinned mesh's actual topology before the build:
the 130-vertex/128-triangle asset duplicates its two seam rings EXACTLY
(130 stored vertices, 66 distinct positions, worst duplicate distance 0.0 m),
so the RAW triangle set is topologically open (128 boundary edges) while the
WELDED surface (identical positions merged) is closed — 192 undirected edges,
every one shared by exactly 2 triangles — and outward-consistent. Corrections,
each strictly narrower or equally explicit versus the original text; no bar is
loosened:

1. P1 restated to the measured truth: raw open edges = 128 (exact seam
   duplicates); welded closure = 0 open edges; distinct positions = 66; the
   implementation asserts all three with named refusals.
2. Region kind corrected `region` -> `shell` per the M02 frozen closure rule
   ("zero open edges -> volume region; open edges -> shell that is never
   treated as sealed; volume claim refused"). volume_claim_m3 = null. The
   exact collision law remains the asset's declared analytic cylinder solid.
3. P3 mass formula corrected to m = rho x V_analytic
   (760 x 0.0049803731169212051 = 3.7850835688601157 kg; band
   [3.2372425259987834, 4.2333171493830246] kg at 650/850): the mass derives
   from the DECLARED exact solid, not from a claimed filled shell volume. The
   welded divergence-theorem volume 0.004948423828872138 m3 (ratio to analytic
   0.9935849609458944; relative deviation from the P2 inscribed-polygon
   prediction 1.902e-6, within P2's 1e-5 bar) is recorded as the
   discretization cross-check, with the two-ordering agreement bar unchanged.
4. B3 (missing boundary) evaluated on the welded graph: removing the top cap
   must leave the welded surface with open edges (refusing a volume claim).

P2's numeric bars are unchanged and hold for the measured value. Frozen
2026-09-28, before any build/verify run in this workspace.

## AMENDMENT A1 (disclosed arithmetic correction; committed BEFORE the build)

The PROBES paragraph's in-text total "Total 28 probes" is an arithmetic
slip: the enumerated set is 25 ground + 1 spawn + 8 seam + 6 trunk lateral +
1 base-cap rim + 1 top-cap centre + 4 boundary-post + 1 climb-grip marker
= 47 probes. No probe, view, bar, prediction, bite or capture binding is
changed; the implementation asserts `len(probes) == 47` with a named refusal
(`f03_probe_count`). Frozen 2026-09-28, before any build/verify run in this
workspace.

## HONEST LIMITS (frozen)

No engine run, no HTTP mesh route, no native collision change, no walk or
climb replay, no training, no GPU. The friction 0.6 stays the recorded
UNEVIDENCED-PLACEHOLDER (G04's debt); the density is a declared proxy-species
typical value with the source's missing conditions recorded. The climb
experiments demonstrate the contact interface's finite Coulomb support at
frozen single-tick and resting probes; they are NOT a climb controller and no
appendage anatomy is invented. Deformable branches, bark damage, growth
rings and fracture are out of scope per the card's own wording.
