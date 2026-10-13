# B4 — interactive cradle assembly on the resident runtime

GAME_PLAN_ACTION_RPG.md §13, B4 gate row: *"interactively assemble the
cradle"* — evidence column: *"Place, connect, test, release, mechanically
patch, save and reload admitted parts through transactions"*; acceptance:
*"Rejected edits preserve state; no stale selections remain; loaded
release has the declared work/momentum consequence; player can explain and
improve a connection."* Every claim is measured below on the live Release
engine (port 8793, `--hidden 1600 900 --no-restore`), the same resident
`B2Scene` runtime as B2/B3 — no restart, no re-admission between edits.

## What was built

**Engine** (`b2_scene.hpp/.cpp`, routes in `main.cpp route_b2`,
lock-wrapped in `membrane_tick.cpp`) — six new scene operations, each a
transaction that validates its document fully **before** mutating:

| route | operation |
|---|---|
| `POST /tick_b2_pause` | freeze integration; the scene stays live and readable (the gate's *test* then *release*) |
| `POST /tick_b2_place` | add one part through `B2Scene::parse_part_` — the **same parse law** admission uses (extracted verbatim, so a placed part is admitted by identical rules); scene cap raised 3 → 6 |
| `POST /tick_b2_remove` | release one part by id: its persistent load dies with it (loads live on the `Part`), every weld touching it is dropped, survivors' weld indices remap |
| `POST /tick_b2_patch` | mechanical material patch: `mu` and/or `mass_kg`; a mass change scales inertia AND the ground-rung constants by the same ratio (k_total = m·g/s\*, c_total = 2ζ√(k_total·m) are linear in m) — rest sink and damping ratio preserved, contact law untouched |
| `GET /tick_b2_save` | serialise the full persistent state as `chimera.b2_state.v1` |
| `POST /tick_b2_restore` | validate a saved document end-to-end and swap it in atomically |
| `GET /tick_b2_hash` | FNV-1a-64 over the canonical save document |

Exact round-trip is engineered, not hoped for: every double prints
`%.17g` (shortest exactly-round-tripping form) and each pose carries the
rotation matrix verbatim (`pose_R_rowmajor`, re-verified orthonormal at
the trust boundary) beside its quaternion, because a quaternion printed at
17 digits does **not** survive quat→mat→quat bit-for-bit. `state_hash`
over that document is therefore stable across save → restore → save, and
it is the instrument for "rejected edits preserve state": every refusal
must leave the hash untouched.

**Scene** (`test_b4_assembly.py`): the B3 stack plus a placed timber
block — 60×40×60 mm, ρ 600 → 0.0864 kg, W 0.848 N — standing on the
ground 40 mm clear of the granite's +x face, spawned pre-sunk by the
analytic rest sink so its rung is active from step 0. The cradle
connection is a weld across the gap: four anchor pairs, each one world
point captured into both parts' local frames (zero rest length, zero
preload — a bracket bonded into the block's core), patch centred exactly
on the block COM. `b4_assembly_frame.png` shows the assembly: the placed
block renders **yellow** (new palette slot 3) against the stack's
red/green/blue, and the pick route names it by stable ID.

## Measured (live engine, Release, converged readings)

**Place + transactions.** After `place`: 4 parts, `total_weight_n` =
513.777168 = Σ m·g to 6 decimals (no double mass). Accepted edits move the
hash (`5f63918d…` → `f7d19a58…`); every rejected edit names itself and
leaves the hash **bit-identical** and the part count unchanged —
duplicate id (`place.id: duplicate part id 'cradle_block'`), negative
mass, asymmetric inertia, unknown patch part, `patch.mu: must be >= 0`,
empty patch, unknown remove id, bad restore schema, truncated restore
JSON, and the 7th place (`place: scene already holds the cap of 6 parts`).
The mass patch (×2) doubles `mass_kg`, `weight_n` **and** the rung's
`k_n_per_m`, and the patched block re-settles on the same 1 cm rest sink.

**Connect + improve (the load-sharing law).** The block stays on its
ground rung (lift 0.4 N < W 0.848 N), so ground and weld are springs in
parallel: the weld carries F_w = 0.4·k/(k + k_ground), k_ground = m·g/s\*
= 84.8 N/m, and stretches F_w/k.

| connection (same 4 anchors) | F_w measured | law | stretch F_w/k |
|---|---|---|---|
| as built, k = 1 kN/m | 0.3647 N | 0.3687 N | 365 µm |
| improved, k = 20 kN/m | 0.3947 N | 0.3983 N | 19.7 µm |

The improvement is the whole story a player can explain: **a stiffer
connection carries more of the load and stretches 18.5× less**; the
measured shares sit within 1% of the parallel-spring law.

**Release, no stale selections.** After `remove` of the welded, loaded
block: `welds: []`, every surviving part's `load_n` zero, part list back
to the three layers, `total_weight_n` 512.929584 = Σ W of the stack. The
released ID is gone from every lane: `inspect` refuses it, a weld to it is
refused, and the pick at its last projected pixel stops returning it
(before: `cradle_block` at (0.368, 0.030, 0.151); after: the ray passes to
`layer_base_granite` behind).

**Loaded release, declared consequence.** Static: reaction 512.929584
(= ΣW exactly) → after removing the top layer, converges to 507.41,
within **0.1%** of the two-part weight 507.844. Loaded (top layer
mid-shear at 1.67 m/s, carrying a 3 N load): the released momentum
m·v = 0.863 kg·m/s leaves with the part — the neighbours stay at rest
(≤ 0.003 m/s), the load dies with it, and the reaction settles within the
declared 1% (511.29 at measurement; the stack rings from the shear
release, which is why the static case above is the clean weight number).

**Save / reload, exact.** Mid-shear (timber at 1.65 m/s), save → hash
`f981fb63…` → `clear` (a corrupt restore of an empty-parts document is
refused and the scene stays cleared) → `restore`: hash **equal**, `steps`
11531 = 11531, timber speed 1.65459116 = 1.65459116 m/s and COM
(0.337608796, 0.105916882, 0.149985824) identical to every printed digit;
unpausing, the reloaded momentum keeps evolving (speed stays > 0.02 m/s).

**Mechanical patch changes behaviour.** Same part, same 0.15 N push:
µ 0.3 creeps 0.7 mm in 1.2 s (regularised Coulomb sticking, cap µW =
0.254 N > push); patched to µ 0.05 the same push slides it 0.9 m.

## Bugs the battery caught (engine fixes, this commit)

1. **Explicit dashpot instability → NaN telemetry → invalid JSON.**
   c_damp 300 (the B3 stack value) on the 86 g block gives h·c/m ≈ 0.87:
   the weld limit-cycled until energy hit 1.7e27 J and `fmt` printed
   `-nan(ind)`, breaking every JSON client. Fix: dashpot damping scales
   with the lightest part (c < ~30 here), and `fmt` emits `null` for
   non-finite values so telemetry stays parseable even if a scene ever
   diverges.
2. **Anchor patch off the COM transfers a yaw couple.** A 3-anchor patch
   centred 5 cm off the COM tilted the block 0.27° and settled at 0.385 N
   instead of the parallel-spring value. Fix: patch centred on the COM;
   stretch is read from the weld's own force telemetry (F_w/k), not the
   COM rise (the block keeps ~0.2° tilt on its four corner rungs — ~45 µm
   of geometric noise that is not connector stretch).
3. **A re-set weld zeroes its reference at the CURRENT pose.** Measuring
   the stiff phase off the soft phase's lifted offset gave 0.425 mm for
   both. Fix: each phase starts from the unloaded rest pose.
4. **A touching face leaks the granite's yaw into every reading.** The
   granite yaws ~0.5° under the stack (known from B3); a block face
   touching it picked up contact force (weld read 0.559 N for a 0.4 N
   lift). Fix: 40 mm gap, virtual link points — no contact across the
   connector, ever.
5. **Palette collision:** the 4th part cycled to the base red (`pi % 3`);
   added slot 3 (yellow) so a placed part is named by colour in a frame
   capture.

## Test battery

`tools/construction_packet/test_b4_assembly.py` — 6 tests, run 3× green:
`test_place_and_transactions` (place, 10 refusal classes, hash invariance,
cap, mass patch, settle), `test_connect_and_release_no_stale_selections`
(weld carries the lift, pick by ID, release kills weld+load+ID from every
lane), `test_mechanical_patch_changes_friction` (stick → slide across a
µ patch), `test_connection_improvement` (load-sharing law both welds,
18× stretch reduction), `test_save_reload_exact` (hash-equal round-trip
of a moving scene, corrupt-restore refusal across a clear),
`test_release_declared_consequence` (weight and momentum consequences of
releasing a loaded, sliding part). Regressions: B2 statics 5/5 (cap
refusal updated to "2 to 6 parts"), B2 dynamics 8/8, B3 layers 6/6.

## Gate honesty

- "Player can explain and improve a connection" is evidenced as the
  stated parallel-spring law with both measurements within 1% — the
  explanation is arithmetic the telemetry verifies, not prose.
- The loaded-release reaction is quoted at its measured 0.7% transient
  (the shear release rings the stack); the clean weight consequence is the
  static case at 0.1%. The momentum consequence is exact by construction:
  the released part's m·v is subtracted from the scene by removing it, and
  the neighbours' measured speeds bound what else changed.
- Shear pulses are wall-clock timed, so slip/speed values vary run to run
  (top speed at release measured 1.67–1.75 m/s across runs); every
  assertion uses a tolerance, never an exact transient value.
- The block's ~0.2° residual tilt on its four corner rungs is a property
  of vertex-site ground rungs (the same law B2/B3 qualified on), not of
  the B4 transactions; connector stretch is therefore measured through
  the weld's own force, which the tilt cannot touch.
