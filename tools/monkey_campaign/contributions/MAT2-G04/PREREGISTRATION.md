# PREREGISTRATION - MAT2-G04 (Implement and verify physical grip contact)

Frozen BEFORE implementation and before any experiment run. Composed against
CARD_STARTER.md v3; house standards IMPLEMENTER_CHECKLIST.md (G1-G9) and
TOOLKIT.md (P1-P9) will be cited at the candidate commit. Base:
`7956d2e42a6789a16ee7abc439d0a0dce40662dd` (= origin/astra/gait-capture, the
MAT2-G01 merge PR #296). Attempt `8163c9e40a5d48b8b8a63b71b09a4799`,
agent `wk-g04-grip`, branch `codex/monkey-mat2-g04-8163c9e4`.

done_when (verbatim): "Attachment, friction, reaction loads and release
operate through the physical solver without invisible anchors. Material-first
addition: Use the same local contact and material interface implementation as
ground locomotion; grasp cannot add a hidden sticky constraint."

Card observation (verbatim): "Model choice stays inside approved architecture".
Profile falsifier (verbatim): "Unresolved owner, nonphysical attachment,
unsupported transfer, concealment behind the trunk or force/pose inconsistency
fails."

## 1. The established interface (material-first addition compliance)

The local contact and material interface implementation is MAT2-M06's
`chimera.local_contact.v1` (`local_contact.py`, raw sha256
`1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`), the SAME
module the ground-locomotion contact card MAT2-F04 vendored byte-identical and
hash-asserted ("imported -- never forked"). G04 does the same: the module is
imported at run time from its in-repo path, its sha256 is asserted against the
frozen pin, and NOT ONE BYTE of it is modified or forked. Every attachment,
friction, reaction and release impulse in this card is produced by
`lc.solve_tick` / `lc.solve_contact` of that module.

`grep`-level honesty: this card adds no bond, weld, sticky, or constraint
object; the only pinned body is the declared rooted trunk; there is no
`lambda_min`, no penalty stiffness, no invented density or areal stiffness
anywhere in the module (a named lint check asserts the absence literals).

## 2. Frozen fixture (declared, inside the approved architecture)

Frame: `m06_experiment_z_up` (M06's frame; trunk base at origin, axis +z,
gravity -z). Geometry transform is the sealed asset's own
`frame_transform_to_m06` map `m06 = (x - bx, -(z - bz), y - by)` with
`(bx, by, bz) = (11.976783, 0.0, 2.471766)`; no other transform is composed
(the A09 frame law stands; no hand-to-trunk placement is created).

- Trunk: pinned body `trunk_01.lateral` built from the in-repo pinned asset
  `contributions/MAT2-F03/assets/trunk_01_mesh.json` (raw sha256
  `3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7`),
  partitioned by the F03 per-triangle rule (vertex 128 -> base_cap, 129 ->
  top_cap, else lateral); exactly the `trunk_01.lateral` part is instantiated
  (F04 combined-instantiation heritage: instantiate exactly the parts the
  scenario touches). Trunk material: the F03 material layer verbatim
  (`wood_trunk_01`, mu_s = mu_k = 0.6, thickness 0.0). Pinned (rooted), so its
  per-tick anchor reaction is RECORDED in the ledger -- a visible, verified
  anchor, never an invisible one.
- Grip pads: `n` declared tetra pad bodies (F03's `TETRA_LOCAL` /
  `TETRA_TRIS`, contact face = local x=0 face), each an INDEPENDENT unpinned
  M06 `Body` with thickness 0.0. Pad k (k = 0..n-1) contacts the lateral
  facet at the sealed S1 height band (centroid z = 0.386 m):
  channel 0 is THE sealed F03 S1 facet (lateral triangle 0, centroid m06
  `[0.036763, -0.002406, 0.386]`, outward normal `[0.9951835289511874,
  -0.09802930023345664, 0.0]`); channel k>0 is the same-band facet whose
  centroid azimuth is nearest to `azimuth(channel_0) + 360*k/n` degrees
  (deterministic, ties to the lowest triangle index). Pad start pose: facet
  centroid offset outward along the facet's outward normal by the declared
  `PAD_OFFSET_M = 0.9e-5` m, with the pad's contact face parallel to the
  facet plane, `ex = n` (facet outward), `(ey, ez)` = F03 `_orthobasis(n)`.
  The 0.9e-5 m offset puts every first tick on M06's persistent-contact
  branch (gap `0.9e-5 <= MARGIN 1e-5 + tol`) with zero Baumgarte bias
  (pen - SLOP < 0), so every recorded `jn` is exact momentum bookkeeping, not
  bias.
- Pad mass: the equal share `m / n` of the declared body reading (the G01
  equal-share case model carried into the fixture; per-port load share stays
  the named absent variable `x_share`).
- Pad material: mu_s = 0.6, mu_k = 0.4 -- the DECLARED PLACEHOLDERS (M06
  `contact_law.json` block constants; F03 named them "acquisition is G04's
  debt"). The friction measured-source study (`g04-friction/FRICTION_SOURCES.md`,
  sha256 `336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b`)
  verdicts govern: NO lawful measured mu exists for macaque volar skin on
  bark at the operating load (its section 6 recommendation is adopted
  verbatim: keep mu_s 0.6 / mu_k 0.4 as NAMED placeholders; do NOT re-pin to
  the L2 human forearm-on-textile 0.41). The L1/L2 measured envelope
  (fingerpad-on-rigid 0.5-3.0 at <= 1.64 N; forearm-on-textile 0.41-0.95 at
  14.8 N) is carried in the report as the falsifier BAND context only. The
  pair rule is M06's `elementwise_min`: pair mu_s = min(0.6, 0.6) = 0.6,
  pair mu_k = min(0.4, 0.6) = 0.4.

## 3. The press channel (attachment without a sticky constraint)

Attachment is a DECLARED EXTERNAL IMPULSE CHANNEL, exactly like gravity and
exactly the sealed F03 S1 operating point: per tick, per pad, an inward
normal impulse `P = jn = 0.30 N*s` along `-n(channel)` (the F03 record
`jn = 0.30 N*s` at `dt = 0.005 s`, i.e. the demonstrated 60 N normal-force
operating point). The impulse is applied to the pad velocity before
`lc.solve_tick`, is RECORDED per tick in the scenario ledger extension, and
the full-tick identity is asserted every tick:

    m*(v_after - v_before_press) == press_impulse + gravity + contact + anchor
    (per body; residual <= 1e-12 N*s)

The hold, slip, reaction and release decisions are made ONLY by
`lc.solve_contact`'s normal + Coulomb law. If the press stops, nothing holds:
there is no mechanism in this card that can retain a tangential or normal
force once `jn -> 0`. x_press (the measured actuator bound behind the press)
is ABSENT (G01: ports 0/8 qualified, A08-U1 unresolved): the press is a
fixture input at the demonstrated operating point, NEVER an actuator
qualification; every capacity number inherits the ASTRA R1 wording law
("simulated supported-load capacity conditional on the model and mu_s; NOT a
measured grip force").

## 4. Frozen scenario battery

Phases per scenario (M06 constants G = 9.81 record-g, DT = 0.005 s):
HOLD ticks 1..20 (press on), RELEASE ticks 21..30 (press channel = 0).
30 ticks per scenario, deterministic, CPU-only, no RNG, no wall clock.

Grip cases: readings {band_lo 5.4, band_mid 6.15, band_hi 6.9,
scene 10.037998} kg x channels n in {1, 2, 3} = 12 cases. The two mass
systems stay DISTINCT ledgers (sealed register; reconciliation REFUSED
upstream) and verdicts are recorded per reading, never averaged.

Controls: (a) zero-mu control -- n = 3, band_mid, pad mu_s = mu_k = 0.0,
press ON: hold is impossible without friction; (b) release phase is part of
every case; (c) capacity anchor recomputed from the measured hold-tick `jn`
of every stick case.

## 5. Preregistered predictions (closed forms; the solver must reproduce them)

Per pad per hold tick (trunk pinned -> m_eff = m_pad; gravity exactly
tangential for lateral facets; bias 0; restitution 0):

- Normal: `jn_pad = sum of the pad's contact-record jn = P = 0.30 N*s`
  within 1e-9 (momentum: press-induced normal velocity cancelled; no other
  normal input).
- Stick case (`m*g*DT <= n_pair_available`: per-channel stick iff
  `(m/n)*g*DT <= mu_s*jn`): tangential arrested, `vt_post <= 1e-12 m/s`
  (F03 S1 bar); hold-phase vertical displacement <= 1e-9 m after tick 1.
- Slip case: `mode = slip`, `vt_post(k) = vt_post(k-1) + g*DT -
  mu_k*P/m_pad` (exact recursion; window 1e-9 m/s per tick); downward
  displacement accumulates by `v(k)*DT` (window 1e-9 m after the first
  recorded tick).
- Boundary table (solver stick/slip MUST equal the G01 feasibility rows;
  record-g arithmetic `n*0.6*0.30` vs `m*9.81*0.005` in N*s):

  | reading | n=1 | n=2 | n=3 |
  |---|---|---|---|
  | band_lo 5.4 kg (0.26487) | SLIP | STICK | STICK |
  | band_mid 6.15 kg (0.30166) | SLIP | STICK | STICK |
  | band_hi 6.9 kg (0.33845) | SLIP | STICK | STICK |
  | scene 10.037998 kg (0.49236) | SLIP | SLIP | STICK |

  i.e. single-channel support OUTSIDE at every lawful reading; multi-channel
  closes at n >= 2 (band) / n = 3 (scene) -- EXACTLY the G01
  OUTSIDE-CONDITIONAL verdict. No row flips under the g convention (G01 used
  standard-g capacity; the largest g-convention delta is 1.7e-4 N*s against a
  minimum row margin 2.16e-2 N*s; both g readings are verified in the check).
- Reaction loads: trunk anchor per tick equals minus the summed contact
  impulse on the trunk (re-verified externally every tick, <= 1e-12);
  trunk-side normal reaction force per loaded channel = jn/DT = 60 N at the
  operating point (equal and opposite through the contact records).
- Release: every release tick records jn = 0 and jt = 0 per pad (within
  1e-12) and the displacement follows free fall `v(k) = v(k-1) + g*DT`
  (window 1e-9); nothing retains a force after the press stops.
- Capacity anchor: `mu_s * jn / (G * DT)` from any measured hold-tick stick
  `jn` bit-reproduces `3.6697247706422016` kg (36.0 N at record-g; 35.9877 N
  at standard g) -- recorded with the ASTRA R1 conditional wording.

Where the physics says a case cannot close, it does not close: the three
scene/band slip rows are EXPECTED honest failures executed by the solver,
consistent with G01. Named absent variables are carried, never filled:
x_press, x_share, x_aperture, x_reach, x_com, x_inertia, x_trajectory,
x_sequence, x_losses, x_trunk_strength (verbatim provenance inherited from
the sealed G01 receipt; no synthetic constant occupies an absent slot; the
term `lambda_min` occurs in no artifact of this card).

Creature-side components are OUT of the fixture and inventoried as absent:
no creature body, no wrist/digit anatomy, no tendons, no joint axes beyond
the declared pad/trunk frames; grasp endpoint ids of the A09 package are NOT
used as fixture ids (their owners stay unresolved in records; x_reach). The
fixture pads are declared fixture objects with fixture-scoped ids.

## 6. Named checks (test_g04_checks.py; executed, none skipped)

- X1 attachment_through_solver: every hold tick of every case records
  contact(s) between `trunk_01.lateral` and each pad through solve records;
  `jn_pad = P` within 1e-9; the module source contains no bond/weld/sticky
  construction (literal scan) and the only pinned body is the trunk.
- X2 friction_law: stick arrest bar (1e-12), slip recursion (1e-9), zero-mu
  control slides.
- X3 reaction_loads: trunk anchor == -contact every tick (1e-12); reciprocity
  residual 0; 60 N per-channel reaction at the operating point recorded.
- X4 release_opens: post-press (jn, jt) = (0, 0) (1e-12) and free-fall
  displacement (1e-9).
- X5 boundary_agreement: the 12-row solver-vs-G01 table agrees; no row flips
  under record-g vs standard-g arithmetic; the two mass systems stay split.
- X6 ledger_identity: full-tick identity (press + gravity + contact +
  anchor) residual <= 1e-12 for every body, every tick, every scenario.
- X7 determinism: two independent main runs byte-identical (trace) with the
  declared augmentation keys scoped (card-kit X2 form).
- P-class: capacity anchor bit-reproduce; named-variable law (the ten named
  variables present with status ABSENT and verbatim provenance in the
  receipt; `lambda_min` and `penalty stiffness` literals absent from all card
  sources); placeholder naming (mu provenance strings present); input pins
  verified at run time (refusals: input_pin_missing, input_pin_drift).

## 7. Falsifier arms (F-class; every arm clean-control FIRST, named premature
guard, discriminator; a non-biting arm fails the build)

- FB1 release_hidden_sticky: clean = release ticks are (0, 0) with free fall;
  tamper = a scratch variant that re-applies the last hold friction impulse
  after press-off (the weld a hidden sticky constraint would create);
  discriminator = the release check must PASS clean and FAIL tampered
  (free-fall displacement differs by >> window).
- FB2 zero_mu_adhesion: clean = the zero-mu control slides under press;
  tamper = pair_mu patched to ignore the declared zero (adhesion-like
  mu-independent hold); discriminator = zero-mu displacement clean > 1e-3 m,
  tampered ~ 0; check must fail on the tampered build.
- FB3 ledger_concealment: clean = X6 residual <= 1e-12 everywhere; tamper =
  an unrecorded upward `0.02 N*s` per-tick impulse on one pad (an invisible
  anchor); discriminator = the ledger identity fires with residual ~ 2e-2.
- FB4 boundary_flip: clean = the 12-row agreement passes; tamper = one
  recorded expectation row flipped (band_hi n=2 STICK -> SLIP);
  discriminator = verdict_row_disagrees fires (G01 fb1 heritage).
- FB5 slip_mode_assertion: clean = scene n=2 hold ticks record
  mode = slip with vt_post > 0; tamper = the stick assertion substituted;
  discriminator = the mode check fails on the tampered trace (F03 B7
  heritage: the S2 discriminator must discriminate).

## 8. Refusal codes (named; nothing silently repaired)

input_pin_missing, input_pin_drift, interface_pin_drift (the M06 vendored
pin), empty_entries (M06), unknown_surface_id, bad_friction, bad_thickness
(M06 refusals re-declared), zero_area_interface, nonfinite_state,
ledger_imbalance (M06), vacuous_comparison_refused + vacuous_guard_selftest
(G5 law), scenario_refusal:* for any preregistration-scenario mismatch.

## 9. Input pins (verified at run time; drift refuses the run)

| pin | path | sha256 |
|---|---|---|
| local_contact_py | tools/monkey_campaign/contributions/MAT2-M06/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| m06_test_suite | tools/monkey_campaign/contributions/MAT2-M06/test_local_contact.py | b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77 |
| contact_law_json | tools/monkey_campaign/contributions/MAT2-M06/contact_law.json | 583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b |
| m06_experiment_receipt | tools/monkey_campaign/contributions/MAT2-M06/experiment_receipt.json | 2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397 |
| trunk_mesh_json | tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_mesh.json | 3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7 |
| f03_material_state | tools/monkey_campaign/contributions/MAT2-F03/assets/trunk_01_material_state.json | 91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd |
| g01_feasibility_receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G01/numerical/feasibility_receipt.json | 4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42 |
| grasp_benchmark_md | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |
| friction_sources_md | E:/ChimeraWork/monkey-coordination/g04-friction/FRICTION_SOURCES.md | 336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b |

## 10. Capture plan (grasp/motion profile; registry row read mode=ro)

Profile views mapped to the task-owned fixture (creature absence inventoried,
never faked): 'whole-body/trunk relationship' -> trunk + all pad channels +
support-state labels overview; 'wrist/digit attachment close-up' -> the
sealed S1 channel contact close-up (attachment patch, normals, force arrows;
the wrist/digit anatomy absence is the inventoried debt); 'orthogonal view of
each loaded interface' -> two orthogonal cameras per loaded interface group.
Diagnostic layers: attachment patches and endpoint ids (fixture-scoped pad
ids), contact normals and forces, support state, declared pad/trunk frame
axes; 'tendon paths' layer: ABSENT (inventoried; no tendons exist in this
fixture). Clean view REQUIRED: clean pairs share the exact camera and the
exact physical state; state hash preserved across view toggles. Full
17-field camera record on every row. Codec: FFV1 `-level 3 -g 1 -fflags
+bitexact` mkv; lossy never evidence; ffmpeg version recorded. Pixel presence
measured per frame (committed stills re-measured by check_capture_pixels.py);
task_id SHORT form (G04) in manifest AND context. visual_acceptance stays
false BY DESIGN: independent visual review remains the Sergeant/Lieutenant
gate (this text-only worker inspects no pictures).

## 11. Regression

The declared upstream suite is M06's own `test_local_contact.py` (P1-P13,
F1-F4) re-run UNMODIFIED on this exact candidate revision (it imports the
pinned interface this card reuses); exit 0 required, receipt recorded.

## 12. Amendments

- a1 (pre-receipt-run): the capacity anchor is bit-reproduced by the FORMULA
  at the sealed `P = 0.30 N*s`; the MEASURED stick `jn` carries O(1e-11) N*s
  float arithmetic drift (closest-feature projections), so the
  measured-capacity bar is `|capacity_measured - 3.6697247706422016| kg
  <= 1e-8`, recorded beside the bit-exact formula value. Physics, constants
  and every other window unchanged.
- a2 (pre-receipt-run): the release-tick `(jn, jt)` zero bar is rescaled to
  `share_kg * 1e-10 N*s` per release tick (was the flat 1e-12). Reason: the
  M06 closest-feature normal carries O(1e-12) absolute float noise, so a
  SLIDING pad's separating velocity projects onto it as
  `~ share * |v| * 6e-12`; the development shakedown measured a worst
  1.17e-11 N*s per kg (band_lo n=1). The zero bar still excludes any
  retained force (the FB1 weld class produces release `jt = m*g*DT ~
  3.4e-2 N*s`, four orders above the bar) and the free-fall displacement
  window (1e-9 m) is unchanged. Physics, constants and every other window
  unchanged.
- Scenario-label hygiene (recorded with a2, pre-receipt-run): the zero-mu
  control's trace key gains the suffix `|mu=0` so it can never collide with
  the `band_mid|n=3` grip case it shares readings with (a development
  shakedown run hit exactly that collision; the control OVERWROTE the real
  case's rows; disclosed here because the falsifier must be able to fail).
- No amendment touches the press channel, mu placeholders, closed forms,
  boundary table or falsifier-arm designs.
