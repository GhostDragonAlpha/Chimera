# EVIDENCE.md - wk-connection-handground / PKT-G3-CONNECTION-HANDGROUND

Lane: E:/ChimeraWork/monkey-coordination/connection-handground/
Subject: conn.hand_ground_contact.v1 seam law (record ownership, pair rule,
release bars, ledger closure). Interiors of membrane.hand.v1 /
membrane.ground.v1 stay HIDDEN (sibling lanes); the pair RUN runtime scene
stays owed by the assembly packet (declared_pending).

## 1. Prereg chain (seal law: prereg sealed alone BEFORE run code existed)

| artifact | sha256 |
| --- | --- |
| PREREGISTRATION.md (lane copy; CHAIN STOP 1 draft) | see `sha256sum PREREGISTRATION.md` row below |
| seal 1 (prereg only) sealed dir | package/sealed/544704a5b8be44819ee93d54367491d1 |
| seal 1 manifest sha256 | 9decfd290f73b0f81c0b468e61f9abe12588ee0c1a6bc56482492f2567d69531 |
| seal 2 (prereg + conn_seam.py + test_seam.py) sealed dir | package/sealed/31d2abd2604e48e6a01cb0a1d40bf2b6 |
| seal 2 manifest sha256 | 712372f24f9def5f9f54d9d1accbbff1bd19a18cb01e1dd264818f6a4472834b |
| package base (E:/PythonChimera HEAD, read-only for this lane) | 7222729eca6e9f97f25061c8b1dc3d229bb703d8 |

## 2. Pinned inputs (verified byte-exact before use; refusals
interface_pin_missing / interface_pin_drift)

| role | path | sha256 |
| --- | --- | --- |
| pinned M06 solver (import-only, never forked) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-M06/source/local_contact.py | 1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc |
| frozen port contract pc.hand_ground_contact.v1 | E:/ChimeraWork/monkey-coordination/compiler-compile/PORT_CONTRACT.hand_ground_contact.v1.json | a54313760c766764fb95302ebe0bee1fbc65f343770a8b9930657f2a6a3f2104 |
| declaration decl.hand_ground.v1 | E:/ChimeraWork/monkey-coordination/compiler-declare/hand_ground_declaration.v1.json | a5a82d526f160be671837307419abc0f1c33a0f0636bd13220fb9b1797c3d773 |
| G04 experiment receipt | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/experiment_receipt.json | 0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8 |
| G04 falsifier receipt (a2 release bars) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/numerical/falsifier_receipt.json | 04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2 |
| G04 report (X2/X3/X4/X6) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G04/report/REPORT.md | dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8 |
| G07 report (accounted release) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-G07/report/REPORT.md | 34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1 |
| pairpath receipt (S-forms; physlang refusal) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-D-PAIRPATH/numerical/pairpath_result.json | 3d3dfae1fe6bfb759045a450e7a66bc7b3fd2e670eb9ed925e06163fd65a03a9 |
| mathspec ABI of record | E:/ChimeraWork/monkey-coordination/mathspec/membrane_abi.py | 80c5b36574a442fa829f0fa3bea52f088f32c6db5bc316e2e77c54ee03811665 |
| mathspec graph runtime (per-connection one-writer scoping) | E:/ChimeraWork/monkey-coordination/mathspec/graph_runtime.py | c7a96b07dfe4da5056a5c9b39aefa3f3d178c3be01084c823dbd4a9084fc3860 |
| mathspec spec runtime (id scheme; CombineRefusal) | E:/ChimeraWork/monkey-coordination/mathspec/spec_runtime.py | 423fca7089fc28a39825c50eaee8b4968b4beebd778807cb32eaf2e95e2cbd31 |
| A05 mutation record (hand frame + bounds) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-A05/workspace_evidence/48b037593f63_mutation_structure.json | 48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649 |
| F05 composed_meta (plateau_z_m +0.004) | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-F05/source/composed_meta.json | 8168382ff2c852b9fbf2c49831ec2021c8c3f5178af95d6ffba0ce55fa3a42f7 |
| F05 terrain_meta | E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-F05/source/terrain_meta.json | ff15fb1db3dcc128a531d21ef64d3ab62ae78190b64db36f70b5d273c1425681 |
| W03 scene (plane 0.004 / friction 0.6) | E:/ChimeraWork/monkey-coordination/kanban-reviews/MAT2-W03/review-glm53flash-confirm-20260928/blobs/scene.json | f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342 |
| hand.vtp (declared trial contact surface) | E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp | a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6 |

The substrate's own frozen-runtime pins (combine_core 8bfe6949...,
PORT_CONTRACT_V2 0f1b7dfe..., port_contract_schema.v2 69161d32...) are
verified at run time by spec_runtime.require_pins().

## 3. Lane-authored artifacts (sealed bytes verified identical)

| artifact | path | sha256 |
| --- | --- | --- |
| preregistration (CHAIN STOP 1) | PREREGISTRATION.md | e3ebe8326e57949fafdc1a7fa8d19226d14b1f5beb03fc80857e0747ba1279cc |
| seam-law implementation | package/files/tools/monkey_campaign/contributions/CMP-CONN-HG/conn_seam.py | 9b9a8285b0ed40dc14e30c5cd37cf0f046eb64fa101963204fbb2a82b611450d |
| runner test driver | package/files/tools/monkey_campaign/contributions/CMP-CONN-HG/test_seam.py | cc8077fd5837938faa9d79cf614b1e623c872a74699003b4a0c99ff923dfef71 |
| result assembler (receipts -> packet format) | assemble_result.py | 304d52b242a22860300c0786352d02a771bf28b086d9608c7e668ad65c04a3dc |
| seal 2 change patch | package/sealed/31d2abd2604e48e6a01cb0a1d40bf2b6/change.patch | 30cfef16b6845f829aa32f82ab5cc59a97d2fa605d8a0bfad6a863c3f29427e9 |
| seam spec (declared in-lane, contract-derived) | canonical json inside conn_seam.py (SEAM_SPEC) | c10f819235d12761529407165b44a74b86212b1fe4eed3b95a3900a9745d51cb |

## 4. Dev runs (preserved, not acceptance)

- dev run 1: tangential_recursion_broken at SC2_slip tick 20 (seam-only
  identity was wrong: the ground-side total y impulse across ALL ground-body
  records is the external stack y channel; fixed to the pairpath
  jt_all_ground_y form). Preserved in the session log; fix recorded here.
- dev run 2: T.CONN_release FAIL preserved -- the landing transient row
  (ground-prop records, n_records=7) was aggregated into the fall-window
  exact-zero assertion; corrected so the exact zeros are asserted on the
  fall window and the landing stays a RECORDED transient (pairpath P4.4).
  Receipt preserved: dev-outputs/seam_result.json (all_fatal_pass=false).
- targeted SC3 re-check after the fix: 6 fall rows all exact; landing tick
  20 recorded transient.

## 5. Sealed runner run (the passing claim's receipt)

- sealed manifest: 712372f24f9def5f9f54d9d1accbbff1bd19a18cb01e1dd264818f6a4472834b
- job id: 07d5233191bd4cac99fc1f6d0e8491df (slot 3; admitted after slot-2 BUSY
  retries with 25 s backoff -- BUSY is not a failed scientific test)
- receipt state PASSED, cleanup_verified true, exit_code 0
- receipt file: E:/ChimeraWork/task-runner/results/07d5233191bd4cac99fc1f6d0e8491df/receipt.json
- artifacts (hashed by the runner receipt):
  - runner.log 645e2e69d5e5ae9d198da05053d4a0309b92071b70f286391b5f935a81ad01bf
  - outputs/seam_result.json 897ba42d08df098e8d5b5ee592d9e5f6b4027f38b28ece0f8febd58acd23ba54
  - lane copy of the sealed artifact: seam_result.sealed.json (same hash)
- packet-format result (GENERATED from the receipts by assemble_result.py):
  - result.json e89079cd2d7121d2da582d1a8cbbe0abed7cf070c5f6465e29ce90fc6e60cf45
- sealed-run verdicts (from the retained artifact, all_fatal_pass true):
  T.CONN_counted_once PASS; T.CONN_friction_pair PASS; T.CONN_release PASS;
  T.CONN_ledger PASS. Key worsts: reciprocity exactly 0.0 N*s; stick arrest
  2.936886406370373e-17 m/s (bar 1e-12); slip cap dev 0.0; zero-mu jt == 0.0;
  separated fall ticks W_contact == W_press == 0.0 J exactly; ledger worst
  7.197012093545021e-16 N*s (window 1e-12); pair-per-record loss worst
  4.0766001685454967e-17 J; 10/10 refusal probes bit; 4/4 tampered arms bit;
  both port faces conformant under membrane_abi.validate_built AND
  graph_runtime.validate_built_graph (ground owner writer scoping satisfied).
- this file cannot carry its own final hash; the closing EVIDENCE.md hash is
  reported by the worker in the task result returned to the Lieutenant.

## 6. Fixture and debt ledger (fixture_based = true for every row)

- fx.mu_placeholders 0.6/0.4 (NB-01/NB-02, NAMED_PLACEHOLDER)
- fx.press_actuation 0.3 N*s/channel/tick, 60 N by the DECLARED /dt
  conversion (NB-03; actuator_qualified false)
- fx.equal_share_partition share_kg = 3.3459993333333336 (NB-04, ABSENT;
  model of the balance, scales the release bars only)
- x_reach ABSENT: translation-only placements, no transform composed
- pair_run: declared_pending (assembly packet); physlang-v0 refusal recorded

No integrated-qualification claim is made anywhere in this lane.
