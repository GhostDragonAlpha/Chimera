# PREREGISTRATION — ONT-A05 acquired/authorable hand-digit structure evidence

Card `ONT-A05` (planning A05, kind **decision+implementation**, verification
profile `anatomy`, kind **visible_static**), attempt
`1a7c477561f647a29f4e4775bb933547`, agent
`arrival-b249a6084f3c4525afde7644b08ead4f`, criteria
`a19ba471bfde65e094f63ef8f3e6d1edc4d55390f5901e1e82f3d6883d18823d`, scope
`01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`. Frozen
BEFORE any evidence artifact of this attempt exists (informative READ-ONLY
measurements of reference bytes were made to derive exact predictions; no
evidence/ file was written before this freeze). The probe implements EXACTLY
the frozen inventory, checks and views below; mispredictions are recorded
FIRED in `numerical_receipt.prediction_deviations`, never smoothed.

## DONE_WHEN being qualified (the ONLY clause)

"The modeled grasp has sufficient explicit bodies, joints and geometry;
sources and adaptations approved" — calculation C16 (correspondence identity
leg). Observation: "Existing asset/contract cannot map digits; no arbitrary
deformation or hidden grip". Dependency ONT-A04: DONE (PR #177 merged,
winner head `020c0a5c216a4182d0bed9c4ade59cb0beb585ad`, merge `f301e9b3`).

## RECONCILE (records reused, not duplicated)

A04 (merged) evidenced: 27/27 source bone identity pins
(`identity_table.md` `6dab6a40…`), the frame chain and per-bone anchors
(`s2_identity.json` `e1b2131d…`), the CLOSED source palm sign
(`s3_palm_normal.json` `6f29b2dd…`), and the target inventory: 13
carpals/metacarpals region-covered, **14 phalanges NOT covered as
identified digit anatomy**, scale UNDECIDED, target palm sign UNRESOLVED.
The A04 report's own gap statement names what A05 owns: the modeled grasp
lacks explicit digit bodies/joints.

THIS ATTEMPT'S RECOVERY (read-only `git show` / byte copies into
`reference/`, `EXTRACTION.json` records all hashes; nothing in any source
tree is modified):

- A04 winner artifacts (head `020c0a5c…`): identity table, chimanoid XML
  blob `7caa32c6…`, s1/s2/s3 receipts, target measures, A04's numerical
  receipt and qualification receipt.
- **The vendor acquisition candidate**: MyoSuite `myo_sim` v0.1.0
  (Apache-2.0; KEPT_SEPARATE from runtime/training per P02; `hand/assets/
  myohand_body.xml` `21a664923680…`, `hand/myohand.xml` `f05e6897ca76…`,
  LICENSE `1eb85fc9…`, VERSION `3d097c31…`).
- **Identity discovery (the basis of the acquire decision)**: the vendor
  mesh directory's UNPREFIXED `arm_r`-equivalent files `<bone>.stl` for all
  27 A04-pinned bone names hash-match A04's per-bone sha256 pins 27/27
  (frozen check C2). The vendored hand and the pinned source hand are the
  same asset identity; the vendor XML adds the digit structure that the
  pinned chimanoid assembly collapsed into one rigid body.

## THE GAP, MEASURED (the decision inputs A05 owns)

- Pinned source `chimanoid.xml` hand_r: ONE body, 3 wrist hinges
  (`wrist_dev_r`, `wrist_flex_r`, `wrist_3_r`), 27 bone MESHES as geoms,
  5 tendon sites — zero digit joints.
- Target runtime pack `monkey_joints.bin` (`74b3ab04…`, A04's pin): 28
  body-level joints (wrist_L/R etc.), ZERO digital articulation; each hand
  is one wrist + a rigid paddle.
- Vendor `myohand_body.xml`: 15 digit bodies (5 rays x proximal/mid/distal
  + firstmc/proximal_thumb/distal_thumb) and 20 digit joints (CMC flex/
  abduction, MP/IP, MCP/PM/MD) with EXPLICIT ranges.

## FROZEN INVENTORY + CHECKS (each is a numbered prediction; measured by the probe)

1. `C1_source_hand_structure` — the pinned chimanoid XML hand_r subtree
   contains exactly 1 body, exactly 3 hinge joints named `wrist_dev_r`,
   `wrist_flex_r`, `wrist_3_r`, exactly 27 `<geom type="mesh">` entries
   whose mesh names equal the 27 A04-pinned bone names, and the 5 frozen
   sites (ECRL-P4, ECRB-P4, ECU-P6, FCR-P3, FCU-P4).
2. `C2_vendor_mesh_identity_27_27` — for each of the 27 pinned bone names,
   `E:/PythonChimera/vendor/myo_sim/meshes/<bone>.stl` exists and its
   sha256 matches A04's per-bone pin (16-hex prefix) from
   `identity_table.md`; zero missing, zero mismatched. (Read-only hashing
   of pinned bytes; no mesh is modified or copied into evidence.)
3. `C3_vendor_digit_structure` — the pinned vendor `myohand_body.xml`
   declares exactly 19 digit bodies (firstmc, proximal_thumb, distal_thumb,
   secondmc..fifthmc, proxph2..5, midph2..5, distph2..5) and exactly 20
   digit joints (cmc_abduction, cmc_flexion, mp_flexion, ip_flexion,
   mcp{2..5}_flexion, mcp{2..5}_abduction, pm{2..5}_flexion,
   md{2..5}_flexion) — every digit joint carrying an explicit `range`
   attribute; the file is Apache-2.0 with the copyright header present.
4. `C4_correspondence_map` — the name-level correspondence between the 20
   vendor digit joints/bodies and the 27 A04-pinned bone names is COMPLETE
   (every vendor digit segment maps to exactly one pinned bone: 1mc->firstmc
   etc.; thumbprox->proximal_thumb; Nproxph->proxphN; Nmc->Nthmc/Nmc) and
   every one of the 14 A04-uncovered phalanges is covered by this map; the
   map is name+hash-level (A04's identity leg), NOT a scale or runtime
   binding.
5. `C5_adaptation_delta_recorded` — the probe derives and records the
   EXACT structural delta of the proposed adaptation (vendor digit tree
   grafted under the pinned chimanoid hand_r's 3-DOF wrist: 19 bodies, 20
   joints, per-joint axis/range/parent/joint-pos values copied VERBATIM
   from the pinned vendor XML into the delta manifest; per-bone geom mesh
   remapped to the 27 pinned `<bone>.stl` identities; NO scale number, NO
   target-runtime binding, NO origin promotion). The delta is a PROPOSAL
   artifact; approval is the named remaining gate.

## REVISION TRAIL (before the candidate commit; nothing smoothed)

- REVISION A (post-first-probe-run, recorded FIRED in
  numerical_receipt.prediction_deviations): the vendor digit body count was
  frozen as 15; the actual pinned count is 19 (5 rays: 16 finger-segment
  bodies + firstmc/proximal_thumb/distal_thumb). The prereg's own body
  list already named all 19; only the arithmetic was wrong. The probe
  expectation is corrected to 19 and the fired deviation is preserved in
  the receipt.
6. `C6_approval_status_honest` — the receipt records: source acquisition
   basis = vendor `myo_sim` v0.1.0 Apache-2.0, license file pinned, KEPT_
   SEPARATE per P02 preserved (no runtime/training/production role claimed);
   the adaptation is UNAPPROVED (approval is the operator/lead gate named in
   done_when "sources and adaptations approved"); palm sign of any adapted
   digit set is NOT claimed (A04's target-palm-sign UNRESOLVED verdict is
   inherited unchanged); scale remains UNDECIDED (H-LEN/H-ASP unresolved,
   H-BODY circular; nothing promoted).

## FROZEN VISUAL CAPTURE (anatomy profile, from the SAME pinned bytes)

One deterministic contact sheet `evidence/capture_a05.png` (3 profile views
x diagnostic+clean pairs; `visible_static`, tick_interval [0,0],
`fixed_bookmark` cameras; per-camera all 16 required fields with fully
declared secondary cameras; view toggles preserve one physical state hash),
rendered by `capture_build.py` from the probe's state snapshot through the
three DECLARED profile views:

- view `whole-creature overview` — the pinned source hand assembly (27
  bones at their per-bone A04 anchors, the A04 capture-truth guard) with
  frame axes (L1) and stable 3D labels (L6) for port IDs;
- view `local attachment close-up` — the 27 pinned bones with the 5 frozen
  tendon sites marked (L4 attachment sites) and selected bones/joints
  layer (L2);
- view `orthogonal side and oblique views` — the same assembly from a
  second orthogonal bookmark, muscle/tendon paths layer (L3) drawn from the
  frozen site table only.

Diagnostic rows carry the task-owned subset of the six declared layers:
outer envelope (L1: the assembly's convex hull silhouette of the placed
bones), selected bones/joints (L2), muscle/tendon paths (L3: the 5 frozen
sites + course lines to their cited bones from A04's table), attachment
sites (L4), frame axes (L5: hand_r world frame at the A04 origin pin),
stable 3D labels (L6: stable IDs from A04's identity table). Clean rows
carry the scene only. NO vendor digit geometry is rendered into a
"target" claim: the vendor structure is evidenced as an identity+XML
proposal (C3-C5), not drawn as if fitted.

## FALSIFIER

Any probe outcome deviating from checks 1-6 fires; any vendor STL hash
mismatch (identity broken); any invented constant, scale or axis; any
rendered claim that the adaptation is approved, fitted, or bound to the
target runtime; any runtime/native claim; any clean view containing
diagnostics; any camera-manifest field disagreeing with the state snapshot;
any editing of pinned reference bytes (hash drift) — fails this
qualification and reopens the card. The named remaining gate is explicit:
"sources and adaptations approved" requires lead/operator approval of the
C5 delta proposal; this candidate cannot grant it.

## BOUNDS

CPU-only; stdlib + numpy + Pillow; no GPU, no engine, no network (github
reads excepted for publication); <= 16 MiB new output; all writes inside
this attempt workspace and its prepared checkout; E:/PythonChimera and the
play worktree read-only; each test invocation bounded to 120 s. Vendor
STL/XML files are hashed in place, never modified.
