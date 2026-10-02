# PREREGISTRATION (DRAFT) — GP1 CANDIDATE-POSTURE FEASIBILITY: the 22-joint aperture witness treated as a CANDIDATE grasp posture (self-collision, trunk penetration, opposing contacts, actuator forces, load support)

Status: DRAFT authored by `wk-grasp-posture` for the Lieutenant. Per the publication
law this file is committed ALONE FIRST (separate-first; the M03/P04 law; the K01
precedent commit `cdfaa8cc1535dbe723097aa1277385aeb2aa79d3`) BY THE LIEUTENANT;
the committed bytes are the freeze and every emitted receipt must embed
`preregistration_sha256` of exactly those bytes and refuse any mismatch. No
implementation file, harness run, measurement or capture frame of this card exists
at draft time. Write scope of the draft: the NEW lane dir
`E:/ChimeraWork/monkey-coordination/grasp-posture/` (NO_WORKTREES law honored: no
worktree, no clone; all CPU verification through
`python -B E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`).

- Card MAT2-GP1-POSTURE-FEASIBILITY (Lieutenant-owned mapping), agent-author
  `wk-grasp-posture`, lane `E:/ChimeraWork/monkey-coordination/grasp-posture/`.
- DISPATCH PROVENANCE: this card IS the follow-up lane declared by
  `x-aperture/GRASP_MECHANISMS.md` section 7.2 ("Per the Captain's disposition
  received with this flag, the follow-up lane for those demonstrations is
  DISPATCHED; this lane performs none of them and claims none of them"). The
  Captain's order (binding, verbatim intent): treat the 22-joint witness as a
  CANDIDATE grasp posture, with aperture clearance demonstrated and physical grasp
  still open; place the actual hand geometry around the trunk, check self-collision
  and trunk penetration, establish opposing contacts, and calculate actuator forces
  and load support; distinguish feasibility of the final posture from feasibility of
  REACHING it; preserve all friction assumptions.
- CRITERIA consumed: C16 (`MONKEY_COMPLETION_MAP.md` sha256
  `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae`, re-hashed
  2026-10-02) — "Grasp reach and anatomical correspondence ... FK/Jacobians plus
  independent anatomical correspondence; geometry feasibility precedes skill
  training". This card closes NO registry row; it is a bounded feasibility chain
  stop feeding the Captain's grasp docket.
- EXPERIMENT CLASS: deterministic, sealed, stdlib-only derivation battery
  (x-aperture class) — forward kinematics, mesh-statistic proxies, placement
  enumeration and static arithmetic at a FROZEN configuration. NO physics-engine
  run, NO dynamics claim, NO GPU work, NO friction measurement, NO training.

## 0. The baseline law and the objective law (binding, carried verbatim-in-substance)

THE PROVISIONAL BASELINE LAW (carried from the K01 frozen prereg / K02 section 0,
binding wording): the 10.037998 kg certified line is the PROVISIONAL baseline for
every K/GP-tier card, PROVIDED its receipt binds the actual body composition, mass
ownership and runtime configuration. A hash establishes identity; it does not by
itself establish correct mass accounting. LINEAGE BASIS (Captain criterion):
"select body mass and ownership from authoritative assembly evidence, never to
obtain a passing result"; ONLY the 10.037998 kg line is a body any sealed receipt
hashes (`assembly-identity/ASSEMBLY_IDENTITY.md` sha256
`2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035`). LINEAGE
APPLIED PER THE CAPTAIN'S EVIDENCE CRITERION; SUBJECT TO HIS ONE-WORD VETO; THE
RESERVED DECISION STAYS OPEN in every document:
KEEP-10.038-AS-DYNAMICS | ORDER-BAND-MASS-ASSEMBLY | ROUTE-TO-WALK-TIER-CARD.
Open items OI-1..OI-5 (ASSEMBLY_IDENTITY section 8 scoping; carried in K02
section 0.2) stay open; none is closed here. Binding receipts (hash-verified
2026-10-02, pins in section 7): `mass_register.json` (builder_order_sum_kg
10.037998000000004), `RUNTIME_CONTRACT.md` (`assembly_mass_kg
10.037998000000004`, `weight_N 98.43913308670002`, 18 coordinates),
`w04_certificate.json`, `w04_freeze_manifest.json`, `adoption_record.json`
(TC-8 ports 0/8).

THE OBJECTIVE LAW (verbatim, binding on every outcome reading): "DEMONSTRATED
IMPOSSIBILITY CAN CLOSE AN INVESTIGATION, BUT IT CANNOT COMPLETE THE
PLAYABLE-MONKEY GOAL." Applied to THIS card (the Captain's law, candidate scope):
A CANDIDATE FAILURE CLOSES THE INVESTIGATION OF THAT CANDIDATE — NEVER THE
APERTURE RESULT, NEVER THE OBJECTIVE. A self-collision or penetration finding at
the PRIMARY candidate invalidates THIS candidate configuration only; the declared
fallback ladder (section 4 CC1) and the Captain's docket options (friction bench,
x_aperture geometry admission, resolved parameters, n=4 declaration) follow. No
outcome of this card closes the playable objective or any other candidate.

## 1. Scope — the declared split: FINAL-POSTURE feasibility (this card) vs REACHING feasibility (fenced neighbor)

THE CAPTAIN'S SPLIT, DECLARED AS CARD LAW: feasibility of the FINAL posture
(the candidate configuration itself admits the trunk with opposing contacts, no
self-collision, no penetration, and a static contact set that supports the
declared load at the declared parameters) is THE declared scope of GP1.
Feasibility of REACHING it (the path from any approach posture to the candidate —
preshape, approach, insertion, closing path, x_reach / C01 round-trip) is OUT OF
SCOPE and is THE FENCED NEIGHBOR: a separate future card (working name GP2
REACH/PATH; C01 round-trip debt class). Nothing in GP1's constructions (least of
all the declared trunk placement of CC3, which is derived FROM the candidate
contacts, not reached TO them) may be read as placement, reach or path evidence.

IN SCOPE (four checks at the candidate, per the Captain's order):
1. SELF-COLLISION (CC2): the hand's own certified segments must not interpenetrate
   at the candidate configuration — measured by the DECLARED conservative
   mesh-derived proxy (certified collision geometry is ABSENT; the proxy verdict
   is the declared instrument, labeled DERIVED-PROXY, NECESSARY-condition class).
2. TRUNK PENETRATION (CC3): no hand segment penetrates the declared 74 mm cylinder
   surface at the declared trunk placement family — same proxy law, with the
   declared contact-segment exemption recorded (section 4 CC3).
3. OPPOSING CONTACTS (CC4): identify which digit pairs achieve the antipodal /
   pincer opposition at the candidate — contact points (certified tip origins;
   pads ABSENT), surface normals (declared radial construction), the chord (vs the
   certified WRAP-2 window).
4. ACTUATOR FORCES + LOAD SUPPORT (CC5): at the candidate posture, the joint
   torques required for the opposition press via the DECLARED certified-kinematics
   static map (moment arms of the contact force about the certified joint axes —
   C18 tendon moment arms stay ABSENT; this is the declared geometry-derived
   static map, not a tendon model), and whether the resulting contact set supports
   the declared load (the 10.038 kg PROVISIONAL line) — the K01/G04 static
   arithmetic EXTENDED to the reconfigured contacts at the placeholder frictions,
   with the MP-cap comparison recorded (x_press debt evidence).

OUT OF SCOPE (fenced, not smuggled in):
- REACHING / placement / preshape / closing PATH (GP2, x_reach, C01) — fenced by
  construction: CC3's trunk placement is a declared placement FAMILY derived from
  the candidate contacts (a final-posture construct), never a reach.
- THE RECORDED CONFIGURATION: K01 closed it (P3 SUPPORTED_REFUSAL_OBSERVED: wrap
  margin -0.01733690019744087 m mu-independent; pincer mu_crit 0.8399663223427114
  > 0.6). GP1 re-runs NO recorded-config arm; the recorded numbers appear only as
  docket context.
- FINGER-FINGER WRAP: CLOSED, mu-independently, at every lawful configuration
  (GRASP_MECHANISMS section 7.1 semantics: "closed" = RULED OUT for the six
  finger-finger pairs; their PINCH closure at mu >= 0.3678851621658376..
  0.7265561648676228 is a different mechanism). GP1 tests NO finger-finger wrap;
  finger-finger contacts may enter only as additional same-side contacts of a
  thumb-opposition candidate (CC1 secondary sets).
- PALM OPPOSITION: NON-ANALYZABLE (`grasp.palm_anchor` is role
  `grasp_palm_reference` at the wrist body origin; the palm contact patch record
  is MISSING). No palm contact is counted in any contact set.
- FRICTION MEASUREMENT (NB-01/02 GAP stands; never tuned, never promoted), n=4
  (activates ONLY on a Captain declaration), transfer/ascent (B5 fences),
  descent metering, impact/landing dynamics, training-spec items, reset scenarios,
  mass-line reserved decision, muscle force capacity (A08-U1..U5 absent — no
  anatomical strength comparison is claimed or approximated).
- x_press: the declared 60 N press is the DECLARED fixture operating point
  (jn/DT; K01/G04/F03 line), NEVER an actuator qualification (TC-8 ports 0/8).
  GP1 computes required torques and records the MP-cap comparison as x_press DEBT
  evidence; it does not qualify any actuator.

## 2. The claim-by-claim table (SEPARATE CLAIMS: final-posture feasibility != reaching != physical grasp != measured friction)

LAW (Captain correction #2 class, binding): aperture clearance, final-posture
feasibility, reaching, grasp establishment, static hold and climbing transfer are
SEPARATE claims. The sealed aperture result (x_aperture
0.09508268161006561 m, pair digit3-thumb, margin +0.021082681610065615 m vs the
declared D = 0.074 m; runner job `2b32a723030646f6920191702fa8e21a`) is
NECESSARY-CONDITION admittance evidence ONLY. Any GP1 success is feasibility
evidence of the FINAL posture under the declared assumption set — NEVER a
physical grasp claim (static closure at placeholder mu is necessary-condition
class; sufficiency needs x_reach, certified contact geometry, x_press and measured
mu, each NAMED ABSENT). Labels: every threshold below is a CONDITIONAL-CALCULATION
of the declared models under assumption set A1-A8 (section 4 header). No number
below is a measured monkey-bark value.

| # | bound (verbatim value, source) | constrains ONLY | does NOT touch |
|---|---|---|---|
| B-G1 | aperture admittance: x_aperture `0.09508268161006561` m (digit3-thumb), margin vs D `0.074` m = `+0.021082681610065615` m; ALL FOUR thumb-opposition envelopes >= D; ALL SIX finger-finger envelopes < D (sealed aperture_result.json sha256 `bbfc2bbb2e23da906f6392da04481d8da304808758a5316732e1c1426f59e663`) | the ADMITTANCE (open-around) necessary condition of the certified hand on the declared 74 mm trunk | placement (x_reach ABSENT); collision/penetration (THIS card measures, proxy-class); press (x_press ABSENT); measured mu (GAP); the pincer force-closure threshold below |
| B-G2 | pincer chord window at placeholder mu_s = 0.6: chord >= `0.06345447650272827` m = D*cos(atan 0.6) (RECORDED grasp-geometry, re-derived delta 0.0 in the sealed aperture run); window upper end = antipodal D; recorded-config mu_crit `0.8399663223427114` = tan(acos(0.056663099802559125/0.074)) | the two-surface FRICTIONAL force closure of a candidate pincer chord IN the window, at the declared placeholder | load support (different law, B-G4); wrap/encirclement (B-G1 admittance only); any claim at other mu |
| B-G3 | declared press operating point: jn = `0.30` N*s per contact tick, DT = `0.005` s -> jn/DT = `60.0` N per contact (GRASP_BENCHMARK.md lines 93-98; sealed FRICTION_SOURCES section 1.3; K01 run-confirmed press deviation worst `1.012356865004449e-12` N*s) | the DECLARED normal-force scale of every static map in GP1 (A3 label) | actuator qualification (x_press ABSENT, ports 0/8); muscle capacity (A08-U1..U5 absent) |
| B-G4 | static load-support law (K01/G04 arithmetic, corrected 2026-10-01 static law, DERIVATION.md): P_req = W/(n*mu); n=3 scene line CLOSES at placeholder: P_req `54.68840727038889` N std-g (`54.70708910000001` rec-g) <= 60 N; threshold mu >= `0.5468840727038888` std-g (`0.5470708910000001` rec-g), inside the F-A band [0.3, 1.0]. DERIVED-PREDICTION extension to n=2 (formula + pinned W, re-derived at run): P_req = 98.43913308670002/(2*0.6) = `82.03261090558335` N std-g > 60 N -> NON-CLOSE; threshold mu >= 98.43913308670002/(2*60) = `0.8203261090558336` std-g (rec-g 10.037998*9.81/120 = `0.8206063365000001`), inside the F-A band, ABOVE the 0.6 placeholder | the LOAD-SUPPORT verdict of the declared contact set at the declared parameters ONLY | pincer force closure (B-G2); any claim about the physical grasp, transfer, or other n/mu |
| B-G5 | the declared scenario parameter mu = 0.41 (labeled on EVERY use: single-coefficient reading of the human-analogue Gerhardt-2008 transfer; NOT monkey-bark, UNMEASURED): K01 run-confirmed n=3 NON-CLOSE with slip recursion dv `0.012289681856880237` m/s per tick as the named failure discriminator. DERIVED-PREDICTION at n=2: 0.41 < `0.8203261090558336` -> NON-CLOSE | diagnostic verdicts AT 0.41 only | the placeholder-0.6 verdicts; geometry (B-G1 mu-independent); never a measurement claim |
| B-G6 | hand-body problem (K01 derivation): `m_eff = 0.048761970806378674` kg certified hand body; static support THROUGH the anatomical hand body in the solver line UNDECIDABLE until TC-3/TC-8 (B6 of the K02 table) | nothing in GP1 — GP1 computes REQUIRED torques and contact-set arithmetic, never solver support through the hand body | the load-support arithmetic of B-G4 (contact-capacity law, not hand-body dynamics) |
| B-G7 | declared MP actuator cap `0.8875` N*m (RUNTIME_CONTRACT; K02 B9 row); NO derivation exists from caps to the 60 N grip normal (gap 6; TC-8 ports 0/8) | the RECORDED comparison "computed digit-joint torque vs declared cap" = x_press DEBT evidence | no pass/fail of this card hinges on the cap comparison (P6 records it; it can only RECORD a debt finding) |
| B-G8 | friction placeholders mu_s = `0.6` / mu_k = `0.4` (NAMED PLACEHOLDERS, FRICTION_SOURCES verdict GAP; REPIN ORDER 2; NB-01/02); F-A band [0.3, 1.0] a DECLARED screening band | every friction-dependent verdict above at exactly these labels | measured reality (no measured macaque volar-on-bark mu exists anywhere in the corpus) |

## 3. Friction provenance and the mu label (binding on every use)

- mu_s = 0.6 / mu_k = 0.4 are NAMED PLACEHOLDERS (sealed FRICTION_SOURCES
  `evidence-store/MAT2-F05/source/FRICTION_SOURCES.md` sha256
  `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b`; verdict
  GAP; NB-01/02 stands). Monkey-bark friction (macaque volar skin on bark at the
  20-60 N operating load) is UNMEASURED — never tuned, never promoted, never
  inferred from geometry.
- THE 0.41 VALUE IS A DECLARED SCENARIO PARAMETER, labeled on every use: the
  human-analogue transfer (Gerhardt et al. 2008, HUMAN volar forearm on textile at
  14.8+/-1.3 N, natural-dry 0.41-0.42), carried at K01's single-coefficient
  reading for comparability. NOT monkey-bark, NOT a measurement of the target
  interface.
- THE PLACEHOLDER-MU LAW: no re-pin of mu mid-run; every GP1 verdict is emitted at
  exactly the declared parameters; parameter changes are new preregged runs.
- Every Coulomb/cone form used is the certified WRAP-2 class (sealed
  grasp-geometry forms; Sergeant-verified 3 derivations;
  SGT_GEOMETRY_REVIEW sha256
  `30a2d6aeb6ed1059c1e416a7aa39ab3285cd3fa12013e8141dab20288a3ebc3b`): two-contact
  force closure iff the contact chord subtends theta >= pi - 2*atan(mu),
  equivalently c >= D*cos(atan(mu)).

## 4. The declared experiment design (deterministic sealed derivation battery)

Assumption set (binding labels): A1 declared mass line (PROVISIONAL, section 0);
A2 contact points are the certified A09 fingertip ORIGINS — POINTS, pads ABSENT;
A3 declared press operating point 60.0 N per contact (B-G3; never actuator-
qualified); A4 declared trunk: the F01/G01/G04 asset class — exact analytic
cylinder, radius `0.037` m, diameter `0.074` m, height `1.158` m, 32-segment
contact mesh, surface `trunk_01.lateral`; A5 friction placeholders 0.6/0.4 with
0.41 a declared scenario parameter (section 3); A6 law forms: WRAP-2 cone/chord,
static P_req = W/(n*mu), torque map tau = J(q)^T f on the certified chain, record-g
9.81 vs standard-g 9.80665 labeled per convention; A7 F-A band [0.3, 1.0] a
declared screening band; A8 collision/penetration instruments are the DECLARED
conservative mesh-derived proxies of CC2/CC3 (certified collision geometry ABSENT;
proxy verdicts are NECESSARY-condition class, labeled DERIVED-PROXY).

- CC0 INPUT GATE: hash-verify every pinned input (section 7) at run; re-parse all
  quoted constants from the pinned bytes (no prose trusted); value-match every
  quoted number (mismatch = refusal `threshold_pin_mismatch`); re-verify the
  GRASP_MECHANISMS prefix identity (pre-amendment sha256 `855c1a9f...` per its
  section 7 APPEND-ONLY record) against the current lane bytes; verify all 19 A05
  stl_sha256 pins against the on-disk vendor meshes and the anchor VTP pin against
  its recorded sha (drift = refusal `input_pin_mismatch`).
- CC1 CANDIDATE CONTACT CONFIGURATIONS (the declared candidate set and fallback
  ladder): the aperture witness q* (chord 0.09508268161006561 m) is ADMITTANCE
  evidence, not a contact configuration (chord > D cannot sit on one 74 mm
  cross-section). The candidate contact configuration for a thumb-opposition pair
  (T, k) is a configuration q_c inside the DECLARED 22-joint box with the pair's
  tip-separation equal to a declared target chord in the placeholder window
  [0.06345447650272827, 0.074] m; NOMINAL target c_t = D = `0.074` m (antipodal,
  window upper end, strongest closure); declared solve tolerance |chord(q_c) -
  c_t| <= 1e-6 m; achieved chord recorded exactly. Declared solve restriction (for
  determinism, honest as a restriction): only the pair's 6 chord-moving joints
  vary (cmc_abduction, cmc_flexion, mp_flexion, mcp{k}_abduction, mcp{k}_flexion,
  pm{k}_flexion); all other 16 joints held at 0 (the q=0 pose and the aperture
  witness both live in this closure of the subbox; attainment of interior chords
  is checked CONSTRUCTIVELY by the solve, never assumed by continuity prose).
  PRIMARY candidate = (thumb, digit3) — the certified aperture argmax pair.
  FALLBACK LADDER (declared order, each an independent candidate with its own
  four-check verdict): F1 = (thumb, digit4), F2 = (thumb, digit5),
  F3 = (thumb, digit2). SECONDARY contact sets within a candidate (for B-G4
  load support at n=3): declared surface-fit solve for each further digit tip d
  (same-side): minimize |radial_dist(tip_d(q), trunk axis) - R| over d's 3-joint
  subbox about q_c; a third contact counts ONLY if the fit <= 1e-4 m (declared
  tolerance) with the digit tip on the SAME lateral surface, all other checks
  (CC2-CC4) re-run for the enlarged set; not-achieved is recorded honestly.
  Solver discipline: the sealed aperture derivation's deterministic class
  (grid + zoom + coordinate polish), stdlib-only, no physics engine.
- CC2 SELF-COLLISION (declared instrument): per certified segment (anchor body +
  19 mutation bodies): bounding sphere from the segment's certified mesh bytes —
  19 STL bodies: parse pinned STL, scale vertices by the declared mutation scale
  `0.5384048132470733`, sphere center = scaled-AABB midpoint, radius = max vertex
  distance to that center (conservative); anchor body: the certified
  `hand_vtp_bounds_m` AABB (A05 envelope_check) with the same construction.
  FK all body frames at q_c (certified parentage, offsets, joint axes; the
  parser discipline that reproduced the recorded endpoints to
  1.3877787807814457e-17 m). Predicate: for each of the 190 segment pairs minus
  the 19 certified parent-child pairs (declared adjacency exemption: segments
  connected by a certified hinge may share the joint origin), a PROXY OVERLAP is
  dist(c_i, c_j) < r_i + r_j. VERDICT per candidate: SELF-COLLISION-FREE
  (necessary-condition, DERIVED-PROXY) iff zero non-adjacent proxy overlaps;
  else the overlapping pair list, margins, and q_c are RECORDED as the
  candidate-invalidating finding (Captain's law, section 0). All 190 raw
  separations are recorded either way.
- CC3 TRUNK PENETRATION (declared placement family): given the candidate's two
  contact points a, b on the trunk surface (chord c <= D): the declared family =
  all placements of the A4 cylinder admitting BOTH points on the lateral surface
  with antiparallel radial normals — parametrized by the axis direction u with
  u ⟂ (b-a) (1 DOF, deterministic sweep of 720 angles over [0, 2*pi)), axis
  through m + h*w where m = (a+b)/2, h = sqrt(R^2 - (c/2)^2), w the in-plane unit
  normal to the chord (BOTH mirror sides, 2 per u); axial extent centered at m
  (both contacts within the 1.158 m extent; axial coordinates recorded). For each
  placement: per-segment sphere-vs-cylinder-interior test — NON-CONTACT segment
  FAIL if its sphere intersects the cylinder interior (radial distance of sphere
  center < R + r_s and axial overlap); CONTACT segments (the two touching tips):
  the contact point lies ON the certified segment envelope, so a narrow
  sphere/surface intersection is EXPECTED and is recorded as contact-class
  intersection (declared exemption with the intersection depth reported; the
  absent pad geometry makes finer resolution untestable — named proxy
  limitation); a contact segment FAILS only if its bounding-sphere CENTER lies
  strictly inside the interior (gross intrusion). VERDICT per candidate:
  PENETRATION-FREE (necessary-condition, DERIVED-PROXY) iff at least one
  placement in the family has zero FAIL segments (feasibility = existential over
  the declared family) AND the min-clearance and max-penetration placements are
  both recorded (full map recorded: per placement per segment worst margin).
- CC4 OPPOSING CONTACTS (identification): at each candidate record: contact
  points (the two certified tip origins, 3D), surface normals (unit radial
  directions of the declared construction — antiparallel by construction),
  the chord c and its window membership (B-G2), the friction-cone overlap verdict
  at placeholder mu (2-contact closure iff c >= 0.06345447650272827 m), and for
  every secondary set the additional point/normal and the n-contact closure
  reading. Finger-finger-only sets are FENCED (section 1). All labels
  DERIVED-GEOMETRY.
- CC5 ACTUATOR FORCES + LOAD SUPPORT (statics at q_c, no dynamics):
  (i) TORQUE MAP: per contact i, contact force on the HAND = +F*n_i (trunk
  reaction to the declared press, F = 60.0 N, line of action along the declared
  radial normal); per joint j on the loaded chain: moment arm r_j,i =
  |(p_i - o_j) x u_j| (o_j = joint origin = certified child-body frame origin;
  u_j = certified joint axis in the certified frame; the axis-frame convention is
  declared as parsed and cross-checked against the A05 XML at run); joint torque
  tau_j = sum_i ((p_i - o_j) x F*n_i) . u_j, plus the segment-weight torques from
  the certified mass priors (gravity torque at q_c recorded separately). Segment
  weights use the A05 mass priors (firstmc-class bodies; anchor 0.049 kg effective
  — the declared alternative-allocation views are recorded, never summed twice).
  (ii) CAP COMPARISON (RECORDED, never decisive): computed digit-joint torques vs
  the declared MP cap `0.8875` N*m (B-G7) — a torque exceeding the cap is
  RECORDED as an x_press DEBT finding at that joint (the declared press is beyond
  the declared cap there), never a silent pass and never a card failure.
  (iii) LOAD SUPPORT (the K01/G04 arithmetic extended): per declared contact set
  (n = 2 primary, n = 3 secondary if achieved): P_req = W/(n*mu) vs the 60 N
  declared ceiling; thresholds vs placeholder 0.6, scenario 0.41, and the F-A
  band; per-contact capacity 36.0 N rec-g / 35.98770642201834 N std-g at
  placeholder; verdicts labeled per B-G4/B-G5. NO solver dynamics run; NO
  hand-body support claim (B-G6 fences).
- CC6 DETERMINISM: every construction is closed-form or deterministic-enumerative;
  a repeat run is bit-identical (the x-aperture precedent); the implementation
  lane records a rerun-determinism receipt.

## 5. Frozen predictions and tolerances (the honest mixed outcome is predicted)

Honest predicted outcome first, per discipline: UNDER THE CURRENT DECLARED
PARAMETERS the honest predicted verdict of this card is CONFIRMING-MIXED — the
candidate solves exist (P2), the PRIMARY two-contact pincer achieves frictional
force closure at placeholder mu (P5, chord in window) but DOES NOT support the
declared 10.038 kg line at the declared 60 N ceiling (P7: predicted NON-CLOSE at
n=2, B-G4) — OBSERVING THAT NON-CLOSE SUPPORTS the prediction and RECORDED it as
the candidate's load-support boundary — while self-collision (P3) and penetration
(P4) are GENUINELY OPEN (no sealed record predicts either way; the proxy
instruments are new; whichever way they land is the measurement). A prereg that
predicts its own honest failure mode where the parameters say so is correct
discipline, NOT pessimism; per section 0 a NON-CLOSE closes THIS candidate's
load-support leg at n=2, never the aperture result and never the objective.

- P1 INPUT GATE `input_pins_verified_values_matched`: every section-7 pin
  hash-verified; every quoted constant value-matched against pinned bytes at run;
  the 19+1 mesh pins match on-disk bytes; GRASP_MECHANISMS prefix identity
  re-verified. TOLERANCE: sha256 equality; value-match exact. FALSIFIER: any
  mismatch -> refusal `threshold_pin_mismatch` / `input_pin_mismatch` /
  `input_pin_missing`, run stops, nothing is normalized.
- P2 CANDIDATE SOLVE `candidate_contact_config_exists`: for the PRIMARY pair the
  declared solve returns q_c in the declared subbox with chord within
  [0.06345447650272827, 0.074] m and |chord - 0.074| <= 1e-6 m. HONEST FAILURE
  MODE: the nominal chord may be unreachable in the 6-joint subbox at 1e-6 m —
  then the solver reports the best chord; if the best chord still lies in the
  window the candidate PROCEEDS at the achieved chord (recorded); if not, the
  candidate is CLOSED at solve level (recorded; F1 next). FALSIFIER: a solve
  claiming success with chord outside the window or with any joint outside its
  certified range.
- P3 SELF-COLLISION `candidate_self_collision_proxy`: zero non-adjacent proxy
  overlaps at q_c (DERIVED-PROXY necessary-condition). NO corpus number predicts
  this — it is a new measurement of the certified geometry. HONEST FAILURE MODE:
  proxy overlaps at the candidate = RECORDED finding that invalidates THIS
  candidate (per section 0: the next fallback candidate follows; the aperture
  result and the objective are untouched). FALSIFIER: none can be named in
  advance beyond the predicate itself — a verdict computed from anything other
  than the declared CC2 instrument on the pinned bytes is the only contradiction
  class (instrument-falsifier).
- P4 TRUNK PENETRATION `candidate_trunk_penetration_proxy`: EXISTS a placement in
  the declared family with zero FAIL segments at q_c (DERIVED-PROXY
  necessary-condition), full map recorded. Same honest framing as P3.
  FALSIFIER: instrument-falsifier only (as P3).
- P5 OPPOSITION `opposing_contacts_identified_window_cleared`: the candidate's
  contact points, antiparallel normals and chord are recorded; the chord lies in
  the placeholder window (B-G2) -> the two-contact frictional closure holds at
  placeholder mu_s = 0.6 (predicted; the window law is certified). FALSIFIER: a
  chord recorded in-window whose window re-derivation at run mismatches the
  recorded form (threshold mismatch), or normals not antiparallel within 1e-12.
- P6 TORQUE MAP `static_torque_map_recorded`: per candidate, the full
  contact->joint torque table at the declared 60 N press (plus the separate
  gravity-torque table) is emitted from the declared CC5 map, with the MP-cap
  comparison recorded per digit joint (x_press debt rows). NO corpus number
  predicts the torque magnitudes (first measurement class); predicted properties:
  finite, and antisymmetric under contact-force reversal (re-run sanity check
  declared: tau(-F) == -tau(F) within 1e-12 N*m). FALSIFIER: a non-finite torque,
  a linearity/sanity breach, or a value mismatch on re-derivation.
- P7 LOAD SUPPORT `load_support_extended_law`: PRIMARY n=2 at placeholder mu:
  PREDICTED NON-CLOSE — P_req `82.03261090558335` N std-g > 60 N; threshold
  `0.8203261090558336` std-g / `0.8206063365000001` rec-g > 0.6; OBSERVING THE
  NON-CLOSE SUPPORTS P7 (refusal-wording law: a predicted refusal observed is a
  SUPPORTED prediction). If a SECONDARY n=3 set is achieved (CC1): PREDICTED
  CLOSE — P_req `54.68840727038889` std-g <= 60 N (the K01-measured scene-line
  number, same law, different contact set; predicted to reproduce within 1e-9 N).
  At the declared scenario parameter 0.41: both n=2 and n=3 PREDICTED NON-CLOSE
  (thresholds `0.8203261090558336` / `0.5468840727038888` std-g > 0.41), recorded
  as the labeled diagnostic (B-G5). FALSIFIER: a sustained CLOSE verdict at n=2
  placeholder, or a threshold/solver disagreement beyond 1e-9 N — a records
  discrepancy routed for review, never a win and never a tuned parameter.
- P8 FENCED `reach_transfer_palm_n4_fenced_not_run`: NO reach/path/placement
  claim, NO transfer, NO palm contact, NO n=4, NO measured friction enters any
  receipt. Stated so the fences are never smuggled; any conclusion text reading a
  GP1 verdict as reach or physical-grasp evidence fails prereg compliance.

## 6. NECESSARY vs SUFFICIENT — the honest reading, and the failure disposition

- Every GP1 verdict is NECESSARY-condition feasibility evidence under the declared
  assumption set A1-A8. A full PASS of P2-P7 on a candidate establishes: THE
  CANDIDATE FINAL POSTURE IS FEASIBLE (admits the trunk, self-collision-free and
  penetration-free at the declared proxy, opposing contacts established, static
  contact set closes and supports the declared load at placeholder mu within the
  declared ceiling). It does NOT establish: that the hand can REACH the candidate
  (GP2/x_reach, fenced), that a physical grasp exists (needs certified contact
  geometry — pads ABSENT — plus x_press qualification and measured mu), or any
  measured claim (friction GAP; ROM declared-not-measured; masses are declared
  priors).
- A candidate failure (P3/P4 overlap finding, P2 solve closure) closes THE
  INVESTIGATION OF THAT CANDIDATE per the Captain's law (section 0): the fallback
  ladder F1-F3 follows; if all four thumb-opposition candidates close, the docket
  options (friction bench at mu >= the recorded thresholds; x_aperture admission
  to the graph; resolved parameters; Captain n=4 declaration) are escalated to the
  Lieutenant with the recorded margins. The aperture result is NOT invalidated by
  any GP1 failure (the admittance necessary condition stands; B-G1).
- Failure preservation: every dev-run refusal, every candidate closure, every
  proxy-overlap table is preserved in `DEV_RUN_REFUSALS.md` in the card package
  (honest negatives, never deleted). REFINEMENT CHECKS: every threshold quoted in
  any report re-derived from pinned bytes at run (section 4 CC0); the five
  RETRACTED defective static quotes (tabulated in DERIVATION.md section 7) MUST
  NOT appear in any GP1 artifact (consistency gate asserts absence).

## 7. Input pins (verified byte-exact 2026-10-02 by this lane; drift = refusal `input_pin_mismatch` / `input_pin_missing`)

Corrected corpus and recorded lanes (the numbers this prereg quotes live in these
bytes):
- `E:/ChimeraWork/monkey-coordination/x-aperture/GRASP_MECHANISMS.md` — DUAL HASH
  RECORD (declared): pre-amendment sha256
  `855c1a9ffc5629a9cdc6877688a3656f7679a1a5e3ca22eeca0c82ec281992e1` (the dispatch
  identity; recorded by its author in the document's own section 7 APPEND-ONLY
  note) and CURRENT bytes sha256
  `ac5e258360e45f46e26117147ab944167aafea55b65df549fb4cecbcbf3c1c5d` (adds section
  7: finger-finger "closed" = RULED OUT semantics + witness-posture status; the
  author declared prefix-identity of sections 0-6; the implementation gate
  re-verifies the prefix identity and pins the current hash). THIS DISCREPANCY IS
  DECLARED, NEVER SILENTLY NORMALIZED.
- `x-aperture/aperture_report.txt`
  `d60a6aec8927ec1b35eeb510b8a71a65c649bea0706852a5f71bdb03d8e36ef5` (byte-copy of
  the sealed run output; canonical: runner job `2b32a723030646f6920191702fa8e21a`)
- `x-aperture/aperture_result.json`
  `bbfc2bbb2e23da906f6392da04481d8da304808758a5316732e1c1426f59e663`
- `x-aperture/EVIDENCE.md` (current) `68b5e429a0c5e0a81718c1fb77fc86856ed901ee7843f02f136303996ee5ad91`
- `evidence-store/MAT2-A09/numerical/grasp_package.json`
  `0a70adb1029d860ac9504683d77c2e94be2634724c63479f827fcbc8fcd97d24` (endpoints,
  frame, 22-bond topology, C01/C05/C06/C17/C18 contracts, A08-U1..U6 gaps)
- `evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json`
  `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` (certified
  kinematics: 20 bodies/22 hinges, axes, declared ranges, offsets, mass priors,
  allometry scale `0.5384048132470733`, `hand_vtp_bounds_m`, 19 stl_sha256 pins,
  muscle_anchor_mapping)
- `evidence-store/MAT2-A05/workspace_evidence/9c91124600ab_macaque_hand_mutation.xml`
  `9c91124600abc67a4a33d78ce79ab1a0604a48b5a9a2e6377d15de05717e5adf` (exact
  rendering cross-check)
- `evidence-store/MAT2-G01/report/REPORT.md`
  `e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9` (declared
  trunk diameter 0.074; recorded span; static-row standard-g authority)
- `climb-derivation/DERIVATION.md`
  `da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9` (corrected
  static law; retracted-quote tabulation; the B-G6 m_eff line)
- `climb-derivation/derivation_output.txt`
  `534ac1f3dfe98bbfb14636704132ca192ca92f47e23cf1f065f9bd5032e2d73f`
  (m_eff = 0.048761970806378674 kg line)
- `climb-derivation/grasp-geometry/grasp_geometry.py`
  `e5614b3120dc9d663c204acf6a5db21f11e5c27c7616911f07eb385eee2cfc97`;
  `climb-derivation/grasp-geometry/derivation_output.txt`
  `955956538d8b2e5236e77e14752352dd51c45065a1c5be8222efaa777965a4db`;
  `climb-derivation/grasp-geometry/SGT_GEOMETRY_REVIEW.md`
  `30a2d6aeb6ed1059c1e416a7aa39ab3285cd3fa12013e8141dab20288a3ebc3b` (WRAP-1/2
  forms, window, mu_crit — Sergeant-verified)
- `g04-friction/FRICTION_SOURCES.md` == sealed
  `evidence-store/MAT2-F05/source/FRICTION_SOURCES.md`
  `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b` (friction
  GAP verdict; 0.41 provenance; declared operating point 60 N; trunk asset class)
- `E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md`
  `d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610` (jn = 0.30
  N*s, dt 5 ms lines 93-98; 36 N / 3.6697 kg anchor; scope labels)
- `E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md`
  `0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae` (C16)

Provisional-baseline receipts (section 0):
- `evidence-store/MAT2-D-MASSREG/numerical/mass_register.json`
  `61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a`
- `b07-prereqs/RUNTIME_CONTRACT.md`
  `f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c`
  (`assembly_mass_kg 10.037998000000004`, `weight_N 98.43913308670002`; the
  declared actuator caps incl. MP `0.8875` N*m are asserted present in these
  bytes by the implementation gate)
- `evidence-store/MAT2-W04/numerical/w04_certificate.json`
  `07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598`
- `evidence-store/MAT2-B07/unclassified/adoption_record.json`
  `f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199`
- `assembly-identity/ASSEMBLY_IDENTITY.md`
  `2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035`

K01 sealed receipts (the certified contact line / mechanics reference consumed):
- FINAL run runner receipt
  `E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/receipt.json`
  sha256 `f0af6968cf9f063062a20536bb4de3460382c92e66dc1654f5b7b4396c7efbc1`
  (job 97f2145b45cb4f99a8073a772f4092bf, state PASSED, exit 0, cleanup_verified
  true; base = frozen K01 prereg commit `cdfaa8cc1535dbe723097aa1277385aeb2aa79d3`;
  sealed manifest `a972d9fd3e555f4fbe537c07526f0ab1e107c4bc70037ae101147290f44fdfb0`)
- `.../artifacts/outputs/k01_experiment_receipt.json` sha256
  `ee1b26fc8e3eda1f2a95f75806cb1caed44805aa8787698e92f09bad69304dd5` (embeds
  preregistration_sha256 `227a06c83180b68846b921e3ea36a0b594b5395d331fd487d9c36cdac764a65e`)
- `.../artifacts/outputs/k01_trace.json` sha256
  `2f342339863e41f9ce8a8b1d11e34740827442dfaa1b88c3942d85260739dc45`

Mesh assets (the CC2 instrument's certified bytes; pins live INSIDE the A05 JSON):
- 19 per-segment STLs under `E:/PythonChimera/vendor/myo_sim/meshes/` — each
  on-disk file was hash-matched 2026-10-02 by this lane against its A05
  `stl_sha256` pin (19/19 MATCH, e.g. 1mc, thumbprox, thumbdist, 2proxph ...);
  the battery re-verifies every one at run.
- Anchor envelope: the certified `hand_vtp_bounds_m` (inside the pinned A05
  bytes); the anchor VTP source pin `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6`
  (A05 anchor geometry; `tools/science_funnel/data/macaque_arm/Geometry/hand.vtp`).

Capture-gate pins (section 9):
- `E:/ChimeraWork/monkey-coordination/capture-gate-template/README.md` sha256
  `331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6`;
  `TEMPLATE_MANIFEST.json` sha256
  `1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7`
  (K01's first production integration guidance inherited; template never forked).

## 8. Honest-absent inventory (declared absences; named conditions)

- A1 CERTIFIED COLLISION GEOMETRY: ABSENT everywhere (A05 geoms are visual
  meshes; no hand-vs-trunk contact model). CC2/CC3 are DERIVED-PROXY instruments
  (conservative bounding spheres); a proxy PASS is necessary-condition clearance,
  a proxy FAIL is the declared candidate-closure instrument. No finer resolution
  is claimable.
- A2 FINGERTIP PADS: ABSENT (contact points are body origins). Contact
  " establishment" at pad level is untestable; normals are declared radial
  constructions, not pad-normal measurements.
- A3 TENDON MOMENT ARMS (C18): ABSENT (A09 C18: "l(q)/moment-arm evaluation:
  explicitly_unresolved"). The CC5 map is the certified-kinematics static map
  tau = J^T f — NOT a tendon/muscle model; no muscle capacity comparison is
  claimed (A08-U1..U5 all explicitly_unresolved: Fmax values are
  derived-provisional/defaults, not source-backed).
- A4 x_reach / placement / preshape path: ABSENT (C01 round-trip still-REQUIRED);
  fenced to GP2. CC3's placement family is a final-posture construct, declared as
  such.
- A5 x_press: ABSENT (TC-8 ports 0/8; no N*m->N derivation from caps). The 60 N
  press is the DECLARED fixture operating point; P6's cap comparison records debt,
  qualifies nothing.
- A6 MEASURED FRICTION: ABSENT (NB-01/02). All mu values are the declared
  placeholders or the labeled 0.41 scenario parameter.
- A7 MEASURED ROM: ABSENT (A09 C05 "limits: explicitly_unresolved"); the joint
  box is the DECLARED mutation-model ranges; every configuration is
  CONDITIONAL-CALCULATION of the certified model class, never a measured macaque
  posture.
- A8 DYNAMICS: ABSENT by design (static map + contact arithmetic only; no solver
  run; hand-body support through the anatomical body stays B6-UNDECIDABLE).
- A9 MASS-ACCOUNTING OPEN ITEMS OI-1..OI-5: carried open (section 0); none closed.

## 9. Evidence obligations (numerical + visual)

- NUMERICAL: the input-gate receipt (all pins + mesh matches + prefix identity);
  per-candidate records: q_c (full 22-joint vector), achieved chord + window
  membership, the 190-pair separation table with adjacency classification, the
  placement sweep map (per placement worst margins; the existential witness
  placement), contact points/normals/chord, the torque tables (contact press and
  gravity separately) + MP-cap rows, the load-support verdicts (P_req, thresholds,
  per-contact capacity) at placeholder and at 0.41, and the P1-P8 verdicts as
  named variables with derived constants; every receipt embeds
  `preregistration_sha256` of the committed prereg bytes and refuses mismatch.
- VISUAL: any visual evidence (e.g., a candidate-posture rendering, OPTIONAL for
  this derivation-class card) goes through THE STANDING TWO-STAGE GATE
  (`capture-gate-template/` v1: stage-0 palette blank-check retained + stage-1
  mask co-location; template law: a run cannot emit a pass without the gate having
  run; view spec frozen BEFORE capture; planted-defect selftest at integration).
  The "palette stage-0" minimum is the declared fallback floor if the template
  path is not yet wired for this card at capture time — the fallback is DECLARED
  here in advance, never silent, and a stage-0-only pass is labeled
  `gate_stage0_only` in the receipt. Declared views (if captured; Lt may refine at
  commit): candidate posture with trunk placement (normal + alternate angle),
  contact-region detail — each clean + diagnostic pairs.
- All CPU verification through the runner: `python -B
  E:/PythonChimera/tools/monkey_campaign/task_package.py seal|run`; sealed
  manifest hash, base SHA, run receipts and exit status recorded in
  `grasp-posture/EVIDENCE.md` with sha256 of every load-bearing artifact.

## 10. Resource allowances (frozen draft values; the committed bytes are the freeze)

- Interpreter: `C:/Python314/python.exe -B` (the corpus convention); stdlib-only;
  no physics engine, no GPU.
- CPU runner only; four fixed slots; BUSY (exit 75) = wait and retry with >= 10 s
  backoff; no new directories on BUSY.
- Frozen executable quantities (frozen grid sizes; Lt may refine at commit):
  candidate solves over the declared 6-joint subboxes (the sealed aperture
  derivation's grid/zoom/polish class); placement sweep 720 angles x 2 mirrors;
  STL parse 19 files + anchor bounds; all arithmetic tick-free (static card — no
  DT-dependent windows exist; the only "time" labels are declared N/A).
- Declared retained outputs per job <= the runner's 256 MiB admission (text/JSON
  records only; expected << 1 MiB per candidate).
- ONE chain stop: this card's package, seal, run and evidence land in
  `grasp-posture/` only; no other lane's bytes are edited; the x-aperture,
  k01-impl, k02-* lanes' bytes are read-only.

## 11. Resume state

- Draft authored by wk-grasp-posture in `grasp-posture/`; the Lieutenant commits
  this file ALONE FIRST (separate-first), then hands back the commit pin;
  implementation lanes dispatch AFTER the committed prereg exists (a seal does not
  replace the required commit) and pin their package to the committed bytes
  (`preregistration_sha256` embedded and refused-mismatch).
- Declared records discrepancy carried to the Lieutenant: the GRASP_MECHANISMS.md
  dual-hash state (section 7) — the dispatch cited the pre-amendment
  `855c1a9f...` identity; the lane now holds APPEND-ONLY section 7 bytes
  (`ac5e2583...`) whose prefix identity is author-declared and gate-re-verified.
  Nothing else drifted: all other pins re-verified byte-exact 2026-10-02.
- Open decisions awaiting the Captain/Lieutenant (bounded; NONE closed or assumed
  here): the reserved mass-line decision (section 0); the three grasp docket
  options + the GP1 outcome themselves; any n=4 declaration; GP2 (REACH/PATH)
  dispatch order.
- After the committed prereg exists: the implementation lane authors the battery
  in a task package (base = the committed prereg commit), seals, runs, and records
  evidence in this lane; Sergeant review is requested by the Lieutenant (no
  self-review).

## 12. Corrections ledger (applied verbatim obligations)

- The Captain's candidate law (section 0) and the final-vs-reaching split
  (section 1) are applied as CARD LAW, quoted at every verdict reading.
- The refusal-wording law (a predicted refusal observed is a SUPPORTED
  prediction) is applied at P5/P7; no GP1 NON-CLOSE may be reported as a failure
  of the card's predictions.
- The friction law (section 3) is applied on every use of 0.6/0.4/0.41.
- The K01 finding-1 annotation lesson: this card has NO tick windows; any seconds
  annotation is forbidden in receipts (grid sizes and counts are the frozen
  executable quantities).
