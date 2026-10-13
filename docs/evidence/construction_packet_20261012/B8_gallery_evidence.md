# B8 — Acceptance gallery: swept contact, delayed edits, retessellation (construction gate)

Date: 2026-10-12. Gate: the **acceptance gallery** of
`docs/GAME_PLAN_ACTION_RPG.md` §13 (items 1–17) plus §11.3:

> Thin layers also need a declared swept-contact/continuous-collision policy or a
> qualified timestep bound with substepping. A fast part must not tunnel through a
> wall between discrete checks. Measure this at the smallest admitted thickness and
> largest admitted relative motion. Numerical contact margins are declared
> approximations, not invisible thick walls that contradict the rendered clearance.

Gallery items 1–5, 8–12, 14 and 17 were exercised by the B2–B7 batteries (see
`FULL_PLAN_AUDIT.md` for the item→test map). This battery closes the four items
that specifically expose the discrete-contact solver and the edit pipeline:

| Gallery item | Test (`tools/construction_packet/test_b8_gallery.py`, port 8799) |
|---|---|
| 16. Move quickly toward the thinnest admitted wall | `test_gallery_16_fast_thin_wall_no_tunneling` |
| 6. Move a loose object inside a container | `test_gallery_06_loose_object_in_container` |
| 15. Select a moving part, then delay the edit | `test_gallery_15_delayed_edit_revalidates` |
| 7/13. Refine a wall / permute and retessellate | `test_gallery_07_13_retessellation_adds_no_strength` |

Result: **4/4 green**, and the full B0–B8 regression stays green
(23 + 13 + 6 + 6 + 10 + 7 + 8 = 73 prior tests + 4 gallery = **77 passed**,
128.18 s, sequential because the batteries own disjoint engine ports).

## What the engine gained (b2_scene.cpp / .hpp)

1. **Declared impact backstop** (gallery 16, §11.3). The rung constants are
   calibrated for resting contact (10 mm sink under own weight), so a thin part
   moving fast sank through the soft penalty spring and was ejected by its
   stored energy — measured: a 20 mm plate dropped from 1 m passed fully below
   the plane (COM −31 mm) before returning. Policy: the ordinary one-sided rung
   governs penetration up to `B8_STOP_M = 15 mm` (1.5× the rest sink, below the
   20 mm smallest admitted thickness — the body *visibly* sinks to the stop, so
   this is the declared approximation §11.3 demands, not an invisible thick
   wall); beyond it a stiff catch (`B8_BS_K = 200×` the rung, damping ratio
   `B8_BS_ZETA = 0.7`) engages on ground contacts and part-pair contacts
   alike. The catch is **one-way** (resists only while the contact drives
   deeper; restoring is the ordinary rung's job) and **velocity-gated**
   (`B8_BS_VGATE = 0.1 m/s` approach speed). Absorbed spring energy is booked
   (`bs_energy_`, folded into `stored_penalty_j_`) and engagements counted
   (`backstop_engagements` in `/tick_b2_state`, cumulative across admits —
   tests use deltas). Explicit-stability margins at the fixed substep:
   ω·h = 0.11 and c·h/m = 0.16, both ≪ 2.
2. **Half-space containment for pair contact** (the big correctness fix). A
   convex volume is the intersection of its face half-spaces, so a vertex
   contacts only when the *max* signed gap over **all** face planes is
   < −`B2_FACE_TOL`. Without it, a vertex laterally past a thin part sits
   "behind" the far face plane by more than the thickness and the
   shallowest-face rule picks that far face: measured, a block 0.1 mm short of
   a 20 mm wall was launched *through* it by the far face's 20 mm phantom
   (`inner->w_e P=0.1399 q=0.1600 n=+1 g=−0.02006 fn=460.9`).
3. **Coplanar-face noise floor** `B2_FACE_TOL = 1e-4` for contact candidacy.
   Two boxes resting on the same ground have coplanar bottom faces; float
   noise made the bottom face a "penetrated" candidate and the shallowest-face
   rule picked it over the side face actually entered (measured: the block
   climbed the wall to COM 0.142 and sank the wall 45 mm). Candidacy now
   requires genuine penetration past the 0.1 mm noise floor.
4. **Friction impulse caps** (ground and pair): each sticking-damper site is
   bounded by an equal share of the body mass over the substep
   (`mass/(nv·h)` ground; reduced-mass `μ_red/(nv·h)` pair), so the explicit
   sticking damper can never reverse a vertex's tangential motion in one
   substep (the `c·h/m > 2` instability). Sliding Coulomb is untouched.

## The two catch policies the measurements forced

Both failure modes below were *measured in the B0–B7 regression*, not
hypothetical:

- **Two-way spring → cannon.** Support restored while wedges sat 110 mm below
  the plane: the two-way 200× catch had stored ~17 kJ and returned it — wedge
  launched at 33 m/s (`support_and_gravity_switches`). Fix: one-way catch;
  the catch absorbs the declared stop's energy and never gives it back.
- **Ungated catch → pinned statics.** The catch is a *dynamic arrestor*, not
  a static floor. Ungated, it pinned the B4 granite at 15.02 mm although its
  honest static sink is 17.9 mm — lifting the granite-side weld anchor 2.91 mm
  and stealing the weld's load share (`connection_improvement` read 0.127 N
  for a 3.05 mm block rise); and it chattered against a tilted wedge's
  ±0.23 mm/s settling jitter, corrupting the lever-rule reaction
  (`offcenter_load_lever_rule` read 163 N vs 145.35 N). A 5 mm/s gate was
  still crossed by tilt settling (~cm/s; reaction 127.65 N). The 0.1 m/s gate
  sits above every measured static-crossing speed (granite sink crossing
  ~3 cm/s, wedge tilt settling ~3 mm/s, rest jitter ~0.5 mm/s) and far below
  any tunneling speed. Static sink past the stop is *honest* — the ordinary
  rung's job — and the granite now rests at its true 17.9 mm.

## Measurements per gallery item

- **16 (fast thin wall):** 20 mm plate dropped from 1 m onto the plane.
  Min COM −6.7 mm (assert > −8 mm), max penetration 17.4 mm (assert < 20 mm —
  the plate never passes the 20 mm thickness, and the 15 mm stop is visible
  clearance, not a hidden wall), backstop engagements rise during the impact
  and stay **flat at rest** (the catch does not hover), peak speed < 4.6 m/s
  (no ejection; free-fall impact speed 4.43 m/s), plate settles.
- **6 (loose object in container):** four squat walls + inner 100×50×100 mm
  block; 2.0 N × 0.35 s pulse (outranks the block's 1.47 N ground friction).
  Block travels 90.4 mm across the gap, is arrested by the steel east wall
  (predicted penetration ~14 mm < the 15 mm stop), never leaves the enclosure
  (|x|,|z| < 0.13 m, stays above the plane and below wall top through the
  pulse), and converges to v = 0 against the wall. The enclosure **pushes
  back**: the steel wall (79 kg anchor) moved 0.32 mm from its authored pose
  and stayed there — responds to the enclosure, no hidden welded transform,
  no pass-through.
- **15 (delayed edit):** pick a resting part; kill support; pick the *falling*
  part at its snapshot COM; after an 800-step delay the 20 N lift applied at
  the stale point still decelerates the real body (revalidated against
  current physical state); once the part is removed the load is **refused
  naming the part**, and the vacated pixel's pick ray refuses too.
- **7/13 (retessellation):** a box subdivided into more triangles has
  identical mass, identical attached reaction force and identical sink to
  1e-9 relative — visual subdivision adds no material and no strength.

## Design input: the material compliance envelope (recorded, NOT an engine change)

Per the standing directive, the gallery's failure modes are fed forward as
design input for the next gate — a **material-declared compliance envelope**
against which divergences are judged (refusal naming the material limit,
instead of NaN-freeze or silent explosion). Measured evidence:

1. **Slender standing wall topples under its own friction couple.** A wall
   with a 20 mm base and 110 mm height, pushed 2 N at COM, needs ~11 N of
   normal shift across the 20 mm base to balance the F×55 mm friction couple;
   on a foundation that sinks 10 mm that means ~18° tilt — past the ~10°
   tipping angle. Rule of thumb the numbers support: *a part whose base
   half-width is comparable to its foundation's sink cannot stand under
   lateral load.* (Gallery 6's walls were re-authored squat and wide; the
   steel east wall's 79 kg anchor gives ~310 N static friction.)
2. **The backstop's explicit-stability margin is material-dependent.**
   Authoring the inner block on 4× stiffer ground (2.5 mm sink) put ω·h and
   c·h/m past their safe range for that mass/stiffness pair: measured 81 m/s
   explosion in 5 ms. The declared envelope should state, per material, the
   mass/velocity band in which the declared contact law stays qualified.
3. **A thin *sliding* block is outside the penalty ground's honest range:**
   friction torque pitches it nose-down with no pressure redistribution to
   answer; measured 91 m/s explosion. Squat bodies (the B7 wedge family) are
   the qualified family for sliding.
4. **Static sink past the declared stop is honest** (granite 17.9 mm > 15 mm
   stop): an envelope should distinguish *arrest* (dynamic) from *rest*
   (static) rather than force one number to do both.
5. **Coulomb friction gives no terminal velocity:** a sustained 3 N on the
   0.26 kg west wall ran it away to 48 m/s. Sustained-load scenes need an
   envelope statement or a drag term, not a solver fix.

## Notes

- The B8 engine changes deliberately make
  `docs/evidence/recipe_comparison_20261013/receipt.json`'s `native_sha256`
  stale (by design — the native binary moved; the cradle is connector-suspended
  so the receipt's physical numbers should reproduce on re-run).
- This gate commits explicit paths only (`b2_scene.{cpp,hpp}`,
  `test_b8_gallery.py`, the `test_b3_layers.py` classifier fix, this file,
  `FULL_PLAN_AUDIT.md`). Other agents' dirty files (`ui.cpp`,
  `AGENT_PROTOCOL.md`, `test_b4_assembly.py` + `cradle_recipe.py` refactor,
  screenshots, `.roo/`, fleet evidence) are untouched.
- The B3 classifier fix riding along: `hue()` now requires channel dominance
  (palette timber blue is b−r ≈ 150; the background gradient is b−r ≈ 32 and
  was being mislabelled), and the render/pick agreement assertion moved to
  the exact pixel whose pick ray refused — a ±2 px scan legitimately wanders
  into the timber's own silhouette edge.
