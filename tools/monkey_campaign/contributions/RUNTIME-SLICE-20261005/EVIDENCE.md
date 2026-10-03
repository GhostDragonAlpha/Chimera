# EVIDENCE.md — wk-runtime-slice (CHAIN STOP 1)

Lane: `E:/ChimeraWork/monkey-coordination/runtime-slice/` (sole write scope).
Worker: wk-runtime-slice (chimera-worker under the main Lieutenant). Date:
2026-10-02. NO_WORKTREES.md obeyed: no worktrees, no clones, no runner jobs
launched (phase 1 = design + readiness audit only). All verification reads
were read-only against `E:/PythonChimera` (shared repo object database and
working tree) and `E:/Chimera` (coordination inputs).

## 1. Load-bearing lane artifacts (sha256)

| artifact | role | sha256 |
|---|---|---|
| `PREREG_DRAFT.md` | the chain-stop-1 prereg draft (readiness verdict + named-refusal table + conditional positive-run design + falsifiers + honest-absent list) | `5233067b5f5a430d1c44d0d86db52a5621e15734b21b3c99b31a6674c8a76b41` |
| `EVIDENCE_JOIN_SPEC.md` | the six-link player_command -> frame_hash join spec | `ea73c8c300aca564993b19354f1d4a85da438507eafbfc3996752ba9fb618c15` |
| `EVIDENCE.md` | this file (updated with its own hash excluded; self-hash impossible) | (this file) |

## 2. Checkout + source identities (verified this session)

- Checkout: `E:/PythonChimera`, common git dir `.git`, branch
  `WK-ENGINE-PATHS-20260929-PR`, HEAD `7222729eca6e9f97f25061c8b1dc3d229bb703d8`,
  working tree heavily dirty (preserved untouched; the four pinned files are
  clean vs HEAD except PLAYABLE_BUILD.json which is untracked `??`).
- Ahead/behind vs upstream: 2 / 508 (matches the task brief).
- Pinned-file hashes — ALL FOUR match the task brief bit-exact:
  - `ChimeraEngine/engine/main.cpp`
    `5f2c4e9408c6c0ffab575fff9b0db24438e7a98b90b6759740ab7ca0b1eb5060`
  - `ChimeraEngine/engine/membrane_tick.cpp`
    `2dbe02c7da611b915bd8f8a4fa186569e37cffaa3ae63bbf6da30fbcba5dff76`
  - `ChimeraEngine/engine/membrane_tick.hpp`
    `3d71781a698d3a9ba27f77c290386615243e2d9b8e670128089224156844b51e`
  - `tools/monkey_campaign/PLAYABLE_BUILD.json`
    `1d0d7bb3fe2b3ae64a3cbee9c9bb5377355093669c10c4c846eb24add3dc2643`
- Runtime/build identity: NO executable matches the pinned source. Prebuilt
  `ChimeraEngine/native/ChimeraEngine.exe`
  sha256 `3cb959a24ea88442f5b23977e7e72d8f17e43d4b588516994da624b4e8839d4b`
  (mtime 2026-08-16) predates the branch. `native/ca_core.exe`
  sha256 `2b963ae351b47d62749eaec9bfa3ecc33f467b3bd08cc73e0652c7fbe851514c`.
  Build system: `ChimeraEngine/engine/CMakeLists.txt` (CMake >= 3.20, C++17,
  Vulkan SDK C:/VulkanSDK/1.4.328.1 pinned inside).

## 3. Task-brief factual claims — all verified TRUE against the tree

| claim | verification |
|---|---|
| /walk directly writes root x/y | `ChimeraEngine/walker.py:311-363`: `Walker.move` computes `nx/ny` from `self.x + vx*dt` and assigns `self.x, self.y = nx, ny` (lines 329-330, 363). Kinematic camera-class walker. RULED OUT as locomotion evidence. |
| /sim is stand-only, no player movement command | `ChimeraEngine/live_viewer.py:~880`: `/sim` constructs `_wk.StandSimulator(theta_path=...)`; class docstring walker.py:845-859: MuJoCo STAND policy, tracks pelvis height/COM drift survival. No movement command channel. RULED OUT. |
| native seam main.cpp -> MembraneTick::step -> engine.update_mesh | `main.cpp:4473-4474` on the render thread; tick dt = measured frame time clamped [0, 0.1] s (main.cpp:4466-4472); mesh init at main.cpp:4196-4201 (slot-0 load). |
| body_actuation is KINEMATIC | `membrane_tick.cpp:4660` `"body_actuation":"kinematic"` in state_json; `joint_binding.hpp:3` "Geometry binding only: these operations do not supply actuator dynamics." |
| PLAYABLE_BUILD.json UNQUALIFIED, null pins | Verified: status UNQUALIFIED; source_commit/build_recipe/executable_sha256/body_scene_policy_identity all null; integrated_features/verified_player_actions/runtime_evidence all empty. |
| readiness: 0 kg counted, 17.039978509953905 kg uncounted | `tools/assembly_handoff/out/real_packet_readiness.json`: counted_mass_kg.value = 0.0; uncounted_mass_kg.value = 17.039978509953905. |
| 0/8 qualified attachments | attachment_status_summary: mechanically_qualified = 0; anatomical_ports_covered_by_a_qualified_attachment = 0; attachment_port_unqualified = 8. |
| nine undecided masses, nine missing frames, two absent required inputs, ambiguous root frame | gap_census: component_mass_undecided = 9; component_frame_missing = 9; required_input_absent = 2; root_frame_ambiguous = 1. Both required inputs (`material_volume_document.json`, `mechanical_requirements.json`) exist:false; `tools/assembly_handoff/inputs/` ABSENT from the tree (checked 2026-10-02). |
| MembraneTick 13,824.5 kg water scalar, not an owned mass table | membrane_tick.hpp:418-427: mass derived 13.8245 m^3 x water; drives only the single root-Y DOF (cpp:865). Confirmed NOT an owned macaque mass table. |
| walkphys precedent PR #328 merged; drives->contacts->free-base moved a body | `gh pr view 328`: state MERGED, mergeCommit 42614bac879b3ba38bf039163de9700a19d8922e, title "WALK-PHYS: the physicalized walk battery - propulsion contact-driven, hand transmission measured". Local commit fd5c6910: "the W03 native walk: 302 ticks, dx 0.9131 m, drives->contacts->free base". W03 line = gait_controller.hpp scene f6844eea... — a DIFFERENT runtime line from the product MembraneTick path; method-only inheritance. |
| corrected momentum-change identity | WALK-PHYS EVIDENCE.md (at 42614bac), Appendix: adopted form `|M*(east[t+2] - 2*east[t+1] + east[t])/dt| <= sum|f|*dt`; 61/240 window ticks failing, clustered at impacts; signed-tangent channel = the named feed-forward; scalar serialization = the known gap. |

## 4. Ownership answer (task-file entry blocker)

- `tools/assembly_handoff/inputs/` does not exist at HEAD; both required
  packet inputs remain absent (readiness JSON + filesystem check agree).
- Sibling monkey-coordination mass lanes (mass-reg, lineage-verify,
  assembly-identity, pair-assembly) address the W03 sealed walk-scene lineage
  (10.038 kg; VERIFIED-AS-SEALED-DYNAMICS-MASS per lineage-verify/REPORT.md
  with findings LV-1..LV-5) — NONE owns the assembly_handoff packet inputs.
- Therefore: this lane does NOT wait on an existing pinned result; it REQUESTS
  the Lieutenant to assign a separate owner for material-volume, mechanical
  requirements, component frames, and the root-frame decision. The LV-1
  per-body build-time emission-receipt gate (EVIDENCE-PACKAGE-20261002
  PACKAGE_SPEC.md, commit 7d9a7189) is adopted as the binding law for any
  live-build claim.

## 5. Commands run (all read-only; no source or sealed bytes mutated)

- `git rev-parse/show-toplevel/branch/HEAD/status`, `git rev-list --left-right --count`
- `sha256sum` on the four pinned files + the two prebuilt exes
- `python -B -m tools.creature_graph.project_spec --check` (ok:true) and
  `--show doc.handoff.zcode` / `req.agent_operation` (graph reads)
- grep/sed reads of walker.py, live_viewer.py, main.cpp, membrane_tick.{hpp,cpp},
  joint_binding.hpp, engine.hpp, CMakeLists.txt
- `gh pr view 328 --repo GhostDragonAlpha/Chimera` (PR metadata)
- `git show` reads of 42614bac / 7d9a7189 / fd5c6910 blobs (read-only cat-file
  class against the shared object database)
- filesystem checks: tools/assembly_handoff/inputs/, E:/ChimeraWork/monkey-coordination/*

No `task_package.py seal|run` was executed (no gated experiment in phase 1).
No evidence anchoring was required yet (nothing measured); this file will be
the anchor list when phase artifacts exist.
