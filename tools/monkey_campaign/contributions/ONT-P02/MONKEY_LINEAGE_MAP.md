# MONKEY LINEAGE MAP — P02 / card ONT-P02 (attempt ab7b304e0a0446e99f324557addb21fb)

Status: **RECONCILED — five items related explicitly or kept separate, every claim
pinned to a re-verifiable record.** Machine-readable authority:
`monkey_lineage_map.json` (same directory); verifier `verify_monkey_lineage.py`;
falsifier suite `test_verify_monkey_lineage.py` (23 tests).

Reconcile-first: this map REUSES the already-verified prior receipts — the P02P03
lineage pin (commit `8feea42a`), the S01 provenance audit (`762eb589`), the D-W04
mass diagnostic (attempt `26382263eb094eaf98a8354a2fe8592c`), and the lead decisions
memo `decisions/20260924_campaign_handoffs.md` — and re-verifies their pins against
the git object store. No new anatomy, no new numbers, nothing invented.

## The five card items

| Item | Identity (pinned) | Relation to the playable build |
|---|---|---|
| **CT monkey** | MorphoSource media **000875604**, *Macaca mulatta* **USNM 497136-3** (Smithsonian NMNH), infant, 160 µm CT; segmented to 25 closed bones (`meshes/manifest.json` @ `33e7a444`) | **SOURCE_ASSET of the runtime render body** (DERIVED relation below). Distribution **BLOCKED FOR SHIP**: Commercial Use Prohibited, copyright UND, re-archival duty; operator decision request filed (`066485ae`) |
| **Source musculoskeletal model** | **FreeMusco Chimanoid** — a fictional 120-muscle **human-based** character (56.88 kg), NOT a macaque (`USTR_DIAGNOSTIC_RECEIPT.md` @ `b04a3acd`; S01 R18) | **KEPT SEPARATE**: analysis-only source of the forearm/paddle packet; structurally excluded from the shipped tree |
| **Older forearm/paddle assets** | `forearm_package` on `forearm-package-20260924` (`b04a3acd` I7 receipt; `43b599a7` Buffy 02 package): U-STR ulna candidate, bowed paddle + palm-plane proxy (both FAILED their frozen O2 tests), Buffy transported assembly **17.039978509953905 kg counted 0.0, readiness false** | **KEPT SEPARATE** — "Nothing here executes anything"; never the play or training body; must not change the walking runbook, training body, seeds, bars or certificate (decisions memo §2) |
| **Training body** | Oku, Ide & Ogihara 2021 (Commun Biol 4:1831) Table 1 rigid assembly: HAT 8.184 + 2x(0.557+0.269+0.080+0.021) = **10.038 kg**, weight **98.4391527 N** (`derived_numbers.json` @ `33e7a444`; `gait_scene.py`; scene `f6844eea…`, walk anchors stdout `8c537cdb…`, 302 ticks, 30.970714 J) | **THE body the walk trains and runs on** (SIMULATED_IN the pinned gait scene). Also explicitly SOURCE_OF the playable trunk's geometry (height 1.158 m, radius 0.037 m derived from the Oku numbers, cited inside `trunk_declaration.json`) |
| **Runtime body** | RENDER: `tools/playable_slice/standing_body.obj` sha256 `bc9033bf…9111` (18,469,042 bytes; 499,976 tris / 249,743 verts) = repaired+decimated derivative of the 25 CT preview bones (`body_manifest.json`, ratio 0.7020263287954351); boot cache `.glb` byte-identical; `ghost_standing.obj` composed from the same CT previews. PHYSICS: slice-engine membrane default `mass_kg_ = 13824.5f` (`membrane_tick.hpp` @ `0a1a7c5f`) | **ACTIVE** in the playable slice (PLACED_IN the campaign clearing + trunk). Visual = CT derivative; physics mass = the separate 13824.5 kg membrane lineage |

## Explicit relations

1. **ct_monkey → runtime_body: DERIVED** (render only; confers no mass/physics identity).
2. **training_body → runtime_body: RENDER_BINDING** — the declared geometric fit v3
   (`rig_fit.json` @ `17ba94b9`, 249,743 verts) couples the 10.038 kg walker to the CT
   render for the visible walk. A rendering coupling, **not a physics identity**.
3. **source_msk_model → forearm_paddle_assets: SOURCE_OF** (the packet fits the Chimanoid).
4. **forearm_paddle_assets → runtime_body / training_body: KEPT_SEPARATE** (analysis-only;
   transported mass counted 0.0; readiness false).
5. **source_msk_model → ct_monkey: KEPT_SEPARATE** (same name, not the same body).
6. **training_body → scene_monkey_trunk: SOURCE_OF** (Oku-derived trunk geometry, cited).
7. **runtime_body → scene_monkey_clearing: PLACED_IN**; **training_body →
   scene_gait_walker: SIMULATED_IN** — the gait scene and the playable clearing are
   DIFFERENT scenes with different pinned identities.
8. **myo_sim_reference → runtime_body: KEPT_SEPARATE** (vendored myo_sim v0.1.0,
   Apache-2.0, LICENSE sha256 `1eb85fc9…c8c6`; grab/foot science lanes only; not shipped).

## Mass lineages — DISTINCT, NEVER INTERCHANGED (D-W04 ruling context)

| kg | Lineage | Role |
|---|---|---|
| **13824.5** | membrane creature inventory (13.824536 m^3 at water density) | slice engine physics default; frozen first-skill CoT denominator (`acceptance.py` @ `8294053b`: `M_BODY_KG = 13824.5`) |
| **10.038** | Oku 2021 gait walker | THE TRAINING BODY |
| **6.15** | Turnquist & Kessler 1989 AF band midpoint (5.4–6.9) | muscle/deposit BOOK context only |
| **17.039978509953905** | Buffy transported assembly (`transported_source_effective`) | counted **0.0**, readiness **false**; deliberately separate |
| **7.006001** | coupled-arm assembly (`derived_numbers.json` engine_scaling) | anatomy-side lane context, distinct from the walker |
| **56.88** | FreeMusco Chimanoid total | the fictional MSK model's own body |

Named mismatch (recorded, never reconciled by force): the frozen CoT denominator
(13824.5) vs the simulated training body (10.038) = **1377.2166x**, RESOLVED-AS-WRONG by
D-W04; selection-invariant, so no pass/fail decision changes; correction requires a
lead-authorized NEW registration (D-W04 §7).

## Where the lineages live (lane map)

- **Game lineage** `origin/master 33e7a444…`: gait engine, walk receipts, CT body,
  playable slice, morphosource_ct data.
- **Campaign lanes**: `monkey-play-20260924 @ 762eb589` (S01 audit, scene data), `066485ae`
  (ship-asset decision request), `8feea42a` (P02P03 pin); `forearm-package-20260924`
  (`b04a3acd`, `43b599a7`; later `70c9ff41`, `57beb8b2`); `lane/visible-walk-20260923 @
  17ba94b9` (render fit); `agent/typeb-gpu-finish-20260922 @ a62b286e` (GPU trainer);
  `agent/first-skill-prestage-20260922 @ 8294053b` (frozen first-skill contract).
- **Current campaign workflow lane** `branch-4 @ 9ba1be77` (base `astra/gait-capture
  5e54c0b7`): campaign tooling; the playable/science trees are not in this lane's tip and
  remain on the lanes above until integration. All pinned commits are present in this
  lane's object store and re-verify by read-only plumbing.

## Remaining gates (named, not claimed)

1. Camera-pinned anatomy diagnostic capture (checkpoint V01, shared with W04) — cannot be
   produced offline; not claimed by this card.
2. Operator decision on the MorphoSource ship-asset request (distribution gate; does not
   change lineage).
3. W04 owner: lead-authorized NEW registration binding the CoT denominator to the
   training body (D-W04 §7).
4. Independent review (auto-queued on publication request); lead publication to
   `review/ONT-P02`.
