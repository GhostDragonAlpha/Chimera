# IMPORT PROVENANCE — the table of record (G2-creature-graph, 2026-09-15)

Generated from `tools/reference_data/data/import_provenance.json` (machine-readable twin). 
Checksums are sha256, pinned at first fetch in `tools/reference_data/data/pins.json`; 
a re-import REFUSES to run against drift (pin semantics).


## src.uberon.appendicular-minimal

- **Family:** anatomy ontology subset (appendicular skeleton: limbs)
- **Pinned entry:** http://purl.obolibrary.org/obo/uberon/appendicular-minimal.obo
- **Resolved:** https://github.com/obophenotype/uberon/releases/download/v2026-06-23/appendicular-minimal.obo
- **Release:** uberon v2026-06-23 (resolved via purl 302 chain, 2026-09-15)
- **License:** CC BY 3.0
- **License evidence:** license: label 'CC BY 3.0' (http://creativecommons.org/licenses/by/3.0/) (artifact: `obo_registry/uberon.md`)
- **Coverage:** the appendicular-minimal module (1,227 [Term] stanzas): limb skeleton concepts (femur, tibia/fibula, pes, autopod...) with is_a/part_of relations -- the musculoskeletal subset relevant to the selected limb
- **Known gaps:** full Uberon (~700 MB uberon.owl) NOT imported; axial skeleton and organs deferred; no developmental/axiom-heavy subsets
- **Artifacts:**
  - `uberon/appendicular-minimal.obo` — 910801 bytes — sha256 `9456e0a671633cdedbcfd671cbcf6062466eb7e279fb574b0c2141cfb100ab8b` — pin verified

## src.ro.base

- **Family:** relation ontology (relation types + meanings)
- **Pinned entry:** https://raw.githubusercontent.com/oborel/obo-relations/v2026-09-04/ro-base.owl
- **Resolved:** https://raw.githubusercontent.com/oborel/obo-relations/v2026-09-04/ro-base.owl
- **Release:** obo-relations v2026-09-04 (latest release tag, published 2026-09-07, observed 2026-09-15)
- **License:** CC0 1.0
- **License evidence:** license: label 'CC0 1.0' (http://creativecommons.org/publicdomain/zero/1.0/) (artifact: `obo_registry/ro.md`)
- **Coverage:** ro-base.owl (876 KB): the relation TYPES referenced by the Uberon subset (part_of, has_part, connected/continuous...) with labels + definitions
- **Known gaps:** ro-full.owl (with domain/range axioms over all of OBO) NOT imported; only the selected relation IRIs are projected
- **Artifacts:**
  - `ro/ro-base.owl` — 876042 bytes — sha256 `bdfe8dda3adc4b9cda9d9c843b02e1031772280a92c07003af7c9c22cde027fe` — pin verified

## src.qudt.units

- **Family:** units + quantity kinds (QUDT)
- **Pinned entry:** https://qudt.org/vocab/unit/{UNIT}
- **Resolved:** https://qudt.org/vocab/unit/{UNIT} (Turtle via Accept: text/turtle)
- **Release:** QUDT live LOD endpoint, served 2026-09-15; NOT a release-pinned artifact -- pinned instead by per-file sha256 in data/pins.json (drift fails the import loudly)
- **License:** not stated in the served unit documents -- recorded UNKNOWN (QUDT site terms govern; qudt-public-repo not fetched this run)
- **License evidence:** absence recorded honestly (missing metadata stays unknown)
- **Coverage:** the units the creature's physical laws actually use (Pa, Pa^-1, m^3, N/m, N*m, kg, s, hydraulic resistance Pa*s/m^3...) + 9 quantity kinds
- **Known gaps:** full QUDT vocabularies (all units/prefixes/currencies) NOT imported; no unit-conversion graph beyond SI multipliers
- **Artifacts:**
  - `qudt/quantitykind_Density.ttl` — 4884 bytes — sha256 `dc4532f486b3c1d1920b316197873c57156f706623d67ec06d81c9ebcfd90a5b` — pin verified
  - `qudt/quantitykind_Dimensionless.ttl` — 2150 bytes — sha256 `4351dcb58e4068a811b3d3da524e4d1ee0fc7ef1a483f211d874a2c529e79b62` — pin verified
  - `qudt/quantitykind_Force.ttl` — 3894 bytes — sha256 `e994b74481bad5a1996fe48a2f3b8d5824036b5e691110c9cd4252a89e75f061` — pin verified
  - `qudt/quantitykind_Length.ttl` — 4127 bytes — sha256 `f1573a5e7a5a473f43387216d8d1369f62ebae79530775bce26abbda63150423` — pin verified
  - `qudt/quantitykind_Mass.ttl` — 4604 bytes — sha256 `2b922a9701f9e5a3a6b1f13579cbeef4481bc4b6ba689787a8de333b067a6db1` — pin verified
  - `qudt/quantitykind_Pressure.ttl` — 6347 bytes — sha256 `18ce5beca15ccd95dbcc29ee3b9086f5ca7c98b510b809391e2fd06082998db9` — pin verified
  - `qudt/quantitykind_Time.ttl` — 3714 bytes — sha256 `89fd34240786271750ddd66c5bae26af844783b3fe6d015398099e19fd99a3c2` — pin verified
  - `qudt/quantitykind_Velocity.ttl` — 4398 bytes — sha256 `ae09f786beb34afdbeb3cd8f45cf3a3abefac94481c70f4b919aa9e89ea7e335` — pin verified
  - `qudt/quantitykind_Volume.ttl` — 3733 bytes — sha256 `14e641ef810f564ee307ac96255fbd0d0cefb704ed5538f79a6d60ab662649ab` — pin verified
  - `qudt/unit_HR.ttl` — 2883 bytes — sha256 `0c4365e4bb0076c7555070590f3656c2dae674cfdf3a4a667b404095824c83df` — pin verified
  - `qudt/unit_J.ttl` — 4962 bytes — sha256 `f6e96999e29eb598dd14330f3e19d2bc04962e06d5234f093312d4530b1e7784` — pin verified
  - `qudt/unit_K.ttl` — 4671 bytes — sha256 `55e000fd8bd96ba1fc2fb29f5e1ee4d976a95717e330d5586531f4b717241807` — pin verified
  - `qudt/unit_KiloGM-PER-M3.ttl` — 4174 bytes — sha256 `19193ce84e3bb9120d7c82c91d04afab03089fca47e9b822e65f1626c3232e53` — pin verified
  - `qudt/unit_KiloGM.ttl` — 3870 bytes — sha256 `5a3bb00f9a162a897d5fd45c4894e2ebea5be4c022f3cc6ab2a24b93f23749c3` — pin verified
  - `qudt/unit_M-PER-SEC.ttl` — 3805 bytes — sha256 `1df4e457378aec00102b7881da043b7cec8c207872752f76d7717ad597d0d6ea` — pin verified
  - `qudt/unit_M.ttl` — 3401 bytes — sha256 `f37934471e09bf0211aca761eb5882587bd5da4b0e9537bd47af0de47e726fe1` — pin verified
  - `qudt/unit_M2.ttl` — 3248 bytes — sha256 `c58ffbeae1c0e3670d59efbac25600a3ef0d1a886d45a52581aeb392cdf469c8` — pin verified
  - `qudt/unit_M3.ttl` — 3176 bytes — sha256 `6b05100b3b531535c292bc206342e71bcb6156a02dd41941884a0bbec3a9724a` — pin verified
  - `qudt/unit_MIN.ttl` — 2905 bytes — sha256 `c635d34660fdd7728df355f1df13b117219e9d8d33224c7ea266d3c3583b75a2` — pin verified
  - `qudt/unit_N-M.ttl` — 3546 bytes — sha256 `58d9fe68631a7af876bdf7934d02f26de0408e8ad7e7a6f54f9c2765cce09cf1` — pin verified
  - `qudt/unit_N-PER-M.ttl` — 3373 bytes — sha256 `126a554321a277a103dace6225e9214fc6083f606fd9e989f2c405681c6e51e4` — pin verified
  - `qudt/unit_N.ttl` — 3513 bytes — sha256 `c72c158bd3a6f4087676649412918cf5a8f94d99e23732c4e1c958676dda4854` — pin verified
  - `qudt/unit_PA-SEC-PER-M3.ttl` — 4222 bytes — sha256 `b260f587d614cf2264b55fd7d5072e27b03719e8c661f5fe66d4e0fc5aaf90cb` — pin verified
  - `qudt/unit_PA.ttl` — 3681 bytes — sha256 `a21ff8e8655f9faa4030e06527e7869d1bdae451e0e03b863f51d9350846bc13` — pin verified
  - `qudt/unit_PER-PA.ttl` — 2747 bytes — sha256 `d02e8b9ab906023e4a2ec46de484d60f22832bcbeee5b356c6275e8e9f23e760` — pin verified
  - `qudt/unit_RAD-PER-SEC.ttl` — 3353 bytes — sha256 `2563ef2a290bf88525c0968ad3a6c6d9f4fae3c5bcd10fc3384030510ed2c4db` — pin verified
  - `qudt/unit_RAD.ttl` — 4932 bytes — sha256 `786596996c43bab1500ae57be5ae035f87d90dee6b917a663b68d1c067a00d43` — pin verified
  - `qudt/unit_SEC.ttl` — 5405 bytes — sha256 `5f8b0c864d23571f7ea99481c3f16cfca84c1a8c80113c157e2b6a9b98ed8458` — pin verified
  - `qudt/unit_W.ttl` — 4176 bytes — sha256 `b057374daff1e8dfa5a08c665161ecc5fe2ce82b7cb5c8b6aff8398277d1b127` — pin verified

## src.opensim.leg6dof9musc

- **Family:** musculoskeletal reference model (ONE limb)
- **Pinned entry:** https://github.com/opensim-org/opensim-models
- **Resolved:** https://raw.githubusercontent.com/opensim-org/opensim-models/master/Models/Leg6Dof9Musc/leg6dof9musc.osim
- **Release:** opensim-models master as of 2026-09-15 (repo default branch 'master', last push 2025-11-05; commit-level pin via sha256)
- **License:** NOT STATED in the repo (no LICENSE file at repo root, checked 2026-09-15 via the GitHub contents API) -- recorded UNKNOWN; treated as reference-only
- **License evidence:** absence recorded honestly (missing metadata stays unknown)
- **Coverage:** the human RIGHT leg: bodies pelvis/femur_r/tibia_r/patella_r/talus_r/calcn_r/toes_r; joints ground_pelvis, hip_r, knee_r, tib_pat_r, ankle_r (CustomJoint) + subtalar_r, mtp_r (WeldJoint); 9 Thelen2003Muscle units with max isometric force, optimal fiber length, tendon slack length, pennation
- **Known gaps:** human proportions are REFERENCE, not Chimera proportions; model is one side (right); tendon wrapping paths simplified; NO license terms -- selection/adaptation is a human decision
- **Artifacts:**
  - `osim/leg6dof9musc.osim` — 127479 bytes — sha256 `3f02c0036210fc2ed8b1f3e8cbe220dcf5b75198dbd95fd3f6b9e47e32555ca1` — pin verified

## src.bodyparts3d

- **Family:** anatomy geometry (DEFERRED -- registered, not imported)
- **Pinned entry:** https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- **Resolved:** https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html
- **Release:** archive layout observed 2026-09-15 (FMA-based tables + mesh zips; no release versioning on the archive)
- **License:** CC Attribution 4.0 International
- **License evidence:** "The license for this database is specified in the Creative Commons Attribution 4.0 International"; attribution: "BodyParts3D, (c) The Database Center for Life Science licensed under CC Attribution 4.0 International" (artifact: `bp3d/lic.html`)
- **Coverage:** NONE imported this run -- registration + license only
- **Known gaps:** bulk mesh/table zips NOT imported: geometry is only useful once the leg partition needs conforming caps; HUMAN proportions are NOT Chimera proportions (the sealed-compartment design remains a Chimera requirement)
- **Artifacts:**
  - `bp3d/lic.html + bp3d/download.html` — 14694 bytes — sha256 `7fd311e6646fb82711e9cec857095dde7906ab976e50e89f7a79aaba86306f00` — pin verified

## Import metrics — uberon

`{"n_terms": 1253, "n_uberon_entities": 1221, "n_structural_stanzas_not_projected": 6, "n_edges_projected": 2200, "omissions": "the simplified graph projection preserves is_a and named relationships; it OMITS intersection_of axioms, disjointness, and property_value annotations (present in the pinned cache, re-parseable any time)"}`


## Import metrics — ro

`{"n_selected": 9, "n_selected_available": 10}`


## Import metrics — qudt

`{"n_records": 29}`


## Import metrics — osim

`{"n_bodies": 7, "n_joints": 7, "n_muscles": 9, "n_property_assertions": 63}`


## Import metrics — mappings

`{"n_dataset_candidates": 6}`


## Idempotency verdict (acceptance item 6)

5/5 checks pass. Second import: created=0, unchanged=1253+ records, zero conflicts, store bytes identical (see acceptance_results.json).
