# ONE LIMB — DESK-CHECK RECORD (physics half)

**No engine build was performed** (the lead owns window #10). The new
code has NOT been compiled by MSVC. This note is the verification until
then — and this lane upgraded the instrument: both owned .cpp files pass
a full `g++ -fsyntax-only -std=c++17 -Wall -Wextra` parse (membrane_tick
includes only std headers; main.cpp with the local Vulkan SDK include).
That is strictly stronger than a brace counter — and it ran CLEAN (only
pre-existing warnings: MSVC `#pragma comment` and two old misleading-
indentation sites, both untouched by this lane).

## The desk-check caught two real bugs (the review had teeth)

1. **The blob stride mismatch**: `limb_restore` validated its header
   against a 68-byte per-segment record; `export_limb_state` writes
   76 bytes (name 32 + cell/prox/dist 12 + plane_n 12 + plane_p 12 +
   v0 4 + pieces 4). Every restore after the first boot would have
   failed. Fixed (need = 12 + n_segs*76 + 4).
2. **A guaranteed deadlock**: `limb_partition` holds `seal_mtx_` for its
   whole body and called `split()` — which takes the SAME non-recursive
   mutex. Fixed by extracting `split_locked_()` (split's body without
   the lock); the public split() is now lock + body, and limb_partition
   calls the locked form. Same-shape audit: limb_partition's other calls
   (rest_geometry_locked_, div_pieces_, cell_topology_,
   seal_cut_core_, patch_build_locked_) are all lock-free by contract.

## The named traps (the standing rules)

1. **Windows.h `small`** — grep across the new code: the only hit is
   inside a string literal ("segment too small"); no identifier named
   `small`/`min`/`max` introduced.
2. **stod-on-booleans** — /tick_patch parses "connected" with the house
   `get_bool` and the master "on" with the literal-substring law (the
   /tick_gait and /tick_reflex precedent). No stod added anywhere.
3. **Collision greps with NO file exclusions** (the window-9 rule) —
   every new identifier (seal_cut_core_, limb_*, patch_*, LimbSeg,
   SensorPatch, LIMB_*, PATCH_*) grepped across ALL engine .cpp/.hpp:
   each MembraneTick:: definition count == 1 (patch_json's grep shows 2
   because `MembraneTick::patch_json_locked` contains the substring —
   verified distinct); anonymous-namespace constants defined once.

## Flag-gated early returns — every state has a reachable setter

- `patches_armed_` (gates patch_step + the reflex patch-trigger block):
  set by /tick_patch arm (requires a non-empty registry), restored by
  the patch-state blob (size-validated), cleared by disarm, patch
  restore(armed=0), and init(). Cannot be true with an empty patch
  vector (arm refuses; restore validates).
- `limb_done_` (the partition's already-path): set by an executed
  partition or a validated limb blob restore; cleared by init() (mesh
  swap = stale, visibly). The already-path precedes the surgery gate so
  boot replay stays a no-op.
- `!patches_.empty()` in the surgery gate (not the armed flag): the
  patch REGISTRY indexes cells by index, so ANY registry blocks further
  surgery — one limb surgery per body in this delivery. The event log
  is a record, not live state, and does not block.
- The reflex patch-block: gated by patches_armed_ && flinch && quiet &&
  pins — the same gate set as the scalar trigger minus the nerve term
  (each patch path carries its OWN connected flag; the nerve belongs to
  the scalar path). With patches disarmed the scalar path is
  byte-equivalent to window-9 (`!patches_armed_ &&` prefix only).

## The seal() refactor — behavior-preservation argument

The Y cut's body moved verbatim into `seal_cut_core_`; the only
arithmetic change is the cut coordinate: `pd = py − y`. Equivalences,
checked term by term: ordering (`pd_a >= pd_b ⟺ py_a >= py_b`), the
edge-crossing test (`py < y ⟺ pd < 0`, `y <= py ⟺ pd >= 0`), the
interpolation parameter (`pd_a/(pd_a−pd_b) = (y−py_a)/(py_b−py_a)`),
and the H8 invariant (new cut points push `pd == 0` exactly — the same
statement the old code pinned as `py.push_back(y)`; the new points' `py`
is the blend, used only for the ylo/yhi report bounds, 1000x inside the
already-tolerance). `seal_y_` updates only on Y-cut success (moved after
the core call). The first-cut branch (whole-creature volume reference)
is unchanged inside the core.

## The merge law — closure by construction (the hand proof)

Interior band walls exist twice in the merged piece set (both cap
windings, identical slot triples — the fan covers every ring edge exactly
once per winding: interior ring edges as fan rims, the two end ring
edges as fan spokes). Removing both copies of every twice-present
zero-original triangle leaves: the continuous leg skin (ring edges pair
below-piece ↔ above-piece across the removed wall) + the single-winding
hip cap (spokes self-pair within the fan; rims pair with our skin; the
torso cell holds the opposite winding). Every undirected edge pairs
exactly twice; `cell_topology_` re-proves it at run time along with
χ = V−E+F per cell.

## Residual compile risk (for window #10's build log)

MSVC specifics g++ cannot see: `std::strnlen` (portable enough; MSVC has
it), structured-binding loop `for (const auto& [e, n] : edge)` (C++17,
already used in the file), the `std::deque` include added to the hpp.
If the build fails, first suspects in order: (1) the oblique-cut lambda
inside limb_partition (large capture set), (2) the binary blob
put-lambdas, (3) printf-family format in the chain refusal (snprintf —
<cstdio> added).

## Behavior reference (the control leg)

The current binary's behavior is the control: the causal demo
(demo_nerve_cut_scratch8172.json) ran green on it today. The new code's
default-off paths (patches disarmed, no partition) add exactly three
step()-entry checks (`patches_armed_`, one `if` in detect) — the same
additive law as the reflex landing.
