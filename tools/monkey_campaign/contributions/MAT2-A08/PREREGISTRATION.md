# PREREGISTRATION — MAT2-A08 Define evidenced muscle/tendon parameter envelope

Freeze timestamp: 2026-09-30 (CDT), composed against `CARD_STARTER.md` v2
(v1 base + v2 additions, evidence-anchoring + sequential-banking laws) at
`E:/ChimeraWork/monkey-coordination/CARD_STARTER.md`, house standards
`IMPLEMENTER_CHECKLIST.md` (G1-G9) and `TOOLKIT.md` (P1-P9) at
`E:/ChimeraWork/monkey-coordination/house-standards/`, card-kit
`E:/ChimeraWork/monkey-coordination/card-kit/` and `FORMAT_SPEC.md` v0.

## 0. Existence statement (what did NOT yet exist at freeze)

At this commit, none of the following existed: `parameter_envelope.py`,
`parameter_envelope.json`, `qualification_receipt.json`, `make_report.py`,
`report.md`, `lint_report_numbers.py`, `test_parameter_envelope.py`, any
`evidence/` file of this card. No measurement, classification, screen or
envelope arithmetic for this card had been run. The only reads performed were
the sealed-dependency reads listed in section 4 (their values are quoted, not
computed by this card).

## 1. Task identity

- Task: MAT2-A08 (planning id A08) — "Define evidenced muscle/tendon parameter envelope"
- criteria_sha256: `f784d613aaebc3c2c24350a6cd4a5fb103f72f929f83b5fd9926395b55a040e8`
  (identical on the card, this attempt, and asserted equal in the generator's
  checks identity; read from `agent_slots.sqlite3` mode=ro)
- scope_sha256: `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`
- definition_raw_sha256: `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
- Attempt: `91219426ace44ca8829000815780caaf`; arrival id
  `arrival-f9d11eb9da3f44a3842d11e8736d73e9`
- Verification profile (read-only registry load, G7/P7): id `records`,
  kind `offline`, subject "Pinned definitions, ledgers and numerical evidence",
  `numerical_evidence_required: true`, `clean_view_required: false`,
  `camera_required_fields: []`, nonvisual_reason: "A source/contract/measurement
  task whose truth requires records or numerical oracles, not a 3D image."
- Base: line tip `362da5056f84b56b62a13cfb878dddb98538b18f` (= PR #271 merge =
  `origin/astra/gait-capture`); attempt branch
  `codex/monkey-mat2-a08-91219426ac`; publication branch `review/MAT2-A08`.
- task_id SHORT form used everywhere in generated artifacts: `A08`.

## 2. done_when (verbatim)

"Strength, force-length/velocity, compliance, limits and applicability are
defined for the selected animal. Material-first addition: Separate
source-backed biological parameters from chosen engineering active-pressure
material parameters. No inferred density/stiffness/activation law from
geometry alone."

Card observation (verbatim): "Do not inherit unrelated human or differently
scaled masses/strengths".

Card falsifier (verbatim): "Missing identities or a claimed pass unsupported
by records fails; a screenshot is not a substitute."

Profile falsifier (verbatim): "Missing identities or a claimed pass
unsupported by records fails; a screenshot is not a substitute."

## 3. Lawful-close discipline (declared BEFORE measurement)

The card closes lawfully ONLY as: (a) source-backed parameters carrying pinned
measured sources, or (b) explicit unresolved entries naming the missing
evidence and the authorizing rank, or (c) declared carrier values whose
provenance class is recorded honestly (never relabeled as measured). The
sealed A07 law binds this card: no density/stiffness/activation law inferred
from geometry alone; biological vs engineering active-pressure parameters
separated; any NEW fitting experiment is separately authorized (none is
authorized; none is run; the emitted document refuses fitted*/optimized*
keys). The sealed M04 law binds: "density is never an input to stiffness".
The atlas screen law binds: screens never flip sealed statuses.

## 4. Base, reconciliation and dependency INPUT PINS (sha256 per file)

Base head `362da5056f84b56b62a13cfb878dddb98538b18f`; sealed line tip equals
base (PR #271 merged; wave-2 M09+M10 DONE; A06 DONE). Repo inputs are read at
the candidate commit; host inputs are read at their absolute pinned paths
(license law: Cheng transcriptions stay license-internal at their host path;
only derived statistics enter the contribution).

| role | file | sha256 |
|---|---|---|
| sealed arm model (claims carrier; 39 actuators) | repo `tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim` @ base | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| sealed A06 ownership registry (endpoint/waypoint owner) | repo `tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json` @ base | `f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c` |
| measured morphometry (21 M. mulatta muscles, n=6) | host `E:/ChimeraWork/research-data/20260929/cheng_tables/M2-3_mulatta_morphometry.csv` | `16ca8bcd9be48b3766125801eb05a8f4f10b446b4caed76d9fddeb2e45df71fa` |
| measured segment bands (n=6) | host `E:/ChimeraWork/research-data/20260929/cheng_tables/M2-6_mulatta_inertials.csv` | `1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3` |
| BW regressions (stress-test-only class) | host `E:/ChimeraWork/research-data/20260929/cheng_tables/M2-8_regressions.csv` | `b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22` |
| atlas screen receipt (sealed screen counts to agree with) | host `E:/ChimeraWork/research-data/20260929/atlas/atlas_receipt.json` | `51a591eb938e032ce32c2a09f8b089d9bdd3138d1fc367081c2093b2d52a7586` |
| atlas document (method + honesty tags) | host `E:/ChimeraWork/research-data/20260929/atlas/MUSCLE_ATLAS.md` | `e51c8bb211ec15ea9fbe84cfb6c8f5dae421d276b48f39b4703936d6c88d1a16` |
| re-pin study (gap list, mass-lineage adjudication, re-pin order) | host `E:/ChimeraWork/monkey-coordination/re-pin/REPIN_STUDY.md` | `99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e32290c318b` |
| Fmax provenance adjudication (22/6/11 verdict) | host `E:/ChimeraWork/datastore-agent/docs/research/20260921_arm_architecture_options.md` | `60e97cc8f7bf37c69d5230da7a1c030f91e5636ff7f958855fea592f2fd74e25` |
| chosen active-pressure material carrier | host attempt checkout `E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M03/61aa525f80da4b61a10b7e3c788d87fc/checkout/tools/monkey_campaign/contributions/MAT2-M03/pressure_state.json` | `8182da4720f26154dfff3c54711e66cb318cc7bb9c989de77b7ee0a2f2b2ec03` |
| chosen arm passive-law carrier (rigid-by-declaration) | host attempt checkout `E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M04/262e9d2a30ae4c4b82d84de7de9661a1/checkout/tools/monkey_campaign/contributions/MAT2-M04/arm_rigid_laws.json` | `a9e971db4b36c1a6c35f9c27171ebd06787d5ffc96d58cd4b039e9e4e7f02d32` |
| recorded data-gap round (CT/pQCT/friction gaps) | host `E:/ChimeraWork/monkey-coordination/ASTRA_DATA_ROUND_20260929.md` | `e082aa812af21031a1c3a6e41111fe078b86d04f0dfff1a40d6061ad87064986` |

The generator verifies every pin against on-disk bytes before any emission and
refuses `input_pin_drift` on mismatch. The registry profile is loaded
read-only (`file:...agent_slots.sqlite3?mode=ro`) and its snapshot plus
provenance are written under `evidence/` (G7/P7).

Runtime verification refuses `input_pin_drift`.

## 5. Selected animal and the two lawful mass systems (registration, not repair)

- Selected animal: Macaca mulatta (rhesus macaque); the sealed grasp/receipt
  book context is an adult female, body-mass reference band 5.4-6.9 kg
  (Turnquist & Kessler 1989, midpoint 6.15 kg) per the sealed grasp benchmark
  and the re-pin study section 3.
- The sealed walk scene's dynamics mass 10.038 kg is a DIFFERENT quantity
  (sealed-scene assembly mass, hash-anchored by W03, uneditable). This card
  REGISTERS the two classes side by side and edits neither.
- Inheritance law: no human data and no differently scaled species data are
  admissible. M. fascicularis tables (M2-5/M2-7) are sealed-inadmissible
  (S-MASS-08) and are neither pinned nor read by the generator. Human-norm
  torque is refused by a named falsifier.

## 6. Frozen implementation statement

One generator, `parameter_envelope.py`, emits `parameter_envelope.json`
(schema `chimera.a08_parameter_envelope.v1`) from the pinned inputs and
validates it (recompute-and-refuse). One receipt family:
`qualification_receipt.json` (`chimera.qualification_receipt.v1`) and
`evidence/falsifier_receipt.json` (`chimera.a08_falsifiers.v1`). Report
`report.md` is generated by `make_report.py` from the receipts only (zero
hand-transcribed numbers) and policed by `lint_report_numbers.py` (+`--selftest`).
Named checks live in `test_parameter_envelope.py` (unittest). Determinism:
two consecutive `--emit` runs must be byte-identical (sha256 equal, P9).

Document structure (frozen):
1. `identity` — task, criteria, attempt, arrival, base, profile snapshot sha.
2. `input_pins` — the section-4 table as verified bytes.
3. `selected_animal` — species, book context, two-mass-system registration.
4. `biological_registry` — per-actuator rows (39): osim declared values with
   per-row placeholder fingerprints, per-row provenance sub-class where
   recomputable (default-excluded), class-level citation for the sealed 22/6
   derived-provisional vs provenance-unknown adjudication; per-quantity atlas
   screen class RECOMPUTED from pinned M2-3 bytes (independent oracle;
   disagreement with the sealed atlas receipt is a refusal, not a source).
5. `unresolved_entries` — every class the selected animal has NO source-backed
   value for, each naming the missing evidence and authorizing rank:
   specific tension (blocks PCSA<->Fmax round trip; sigma unknown),
   muscle mass and PCSA (CT-derived muscle volumes behind the operator gate
   `066485ae`, RESTRICTED_RECORDED CT-chain; separately authorized release
   required), force-velocity parameters, activation dynamics, tendon
   stiffness/elastic modulus, passive force-length parameters, biological ROM
   limits for this specimen class.
6. `engineering_registry` — chosen (authored) active-pressure material
   parameters read from the sealed M03 carrier (damping_per_s 240.0; dt_s
   1/300; edge_compliance 0.025 m/N; max_delta_p 5000 Pa; max_dV/dt 1e-3
   m^3/s; p_int_peak 120 Pa; xpbd_iterations 8; membrane mass 0.05 kg) and
   the M04 arm passive law (7 regions rigid, parameters {}, source_status
   synthetic_authored) — each row class `chosen_engineering`, flag
   `never_biological: true`. The two registries are disjoint by identity
   (refuses overlap).
7. `calculation_contracts` — C07 "Actuator limits and passive response" and
   C18 "Tendon routing and moment arms" registered OPEN-INVENTORY exactly as
   the completion map records them ("no new numerical result claimed"): for
   each, required inputs (catalog text), which envelope classes supply them,
   per-input status (source_backed / declared / explicitly_unresolved), and
   the verification still REQUIRED downstream (C07: independent parameter
   provenance + saturated/obstructed-motion controls; C18: finite
   differences/virtual work + unresolved-owner rejection). This card runs
   neither evaluation; it defines and gates the parameter state they consume.
8. `checks` — preregistered predictions P1-P8 (below), gate codes, criteria
   hash identity.

## 7. Declared gates, thresholds and preregistered predictions

All thresholds are inherited from sealed sources (cited), never tuned by this
card: SD-band boundaries inclusive (atlas method A2), t-PI multiplier
2.776546 (= t(0.975,5) x sqrt(1+1/6)), pennation census bound 5 deg (M2-3
caption law), placeholder fingerprints = the sealed model's own repeated
values (0.122492 m / 0.1225 m; 0.002 m; 30.0 N).

- P1: the osim parses to exactly 39 `Schutte1993Muscle_Deprecated` actuators;
  each carries exactly the four parameter fields; muscle-mass and PCSA fields
  count 0 in the whole model (atlas premise correction re-verified from bytes).
- P2: placeholder fingerprints — Fmax == 30.0 N exactly on 11 actuators;
  optimal_fiber_length == 0.122492 m (or 0.1225 m) on 14; tendon_slack_length
  == 0.002 m on 14.
- P3: `flex_carpi_ulnaris` tendon_slack_length equals its own
  optimal_fiber_length (the documented slot swap; value 0.1225 m class).
- P4: M2-3 mapping from pinned bytes — 19 matched 1:1, 5 granularity
  NOT-COMPARABLE, 15 MUSCLE-ABSENT; recomputed screen classes agree with the
  sealed atlas receipt counts: fiber OUTSIDE 16 / INSIDE-1SD 2 / INSIDE-2SD 1;
  tendon OUTSIDE 9 / INSIDE-1SD 5 / INSIDE-2SD 5; pennation INSIDE-1SD 11 /
  CONSISTENT-CENSORED 7 / OUTSIDE-CENSORED 1 (`ext_carpi_rad_longus`).
- P5: segment-mass screens from M2-6 — hand 0.049, humerus 0.203,
  radius_plus_ulna 0.154 kg: all INSIDE-1SD (B06 S-MASS-05 re-verification).
- P6: engineering registry — all 8 M03 constants and 7 M4 rigid assignments
  parse at the pinned values; biological and engineering namespaces are
  disjoint (zero shared row identity).
- P7: geometry-inference census — zero biological rows cite geometry as the
  SOURCE of a density, stiffness or activation value.
- P8: inheritance census — zero rows cite human or M. fascicularis sources;
  M2-5/M2-7 bytes are not pinned and not read.

Falsifier arms (every arm: clean control FIRST, named premature guard
`a08_fb<n>_premature`, receipt row with clean_control block; each must BIT on
its tampered fixture only):

- FB1 `geometry_only_inference_refused` — inject a biological row whose
  stiffness is "derived from mesh/path geometry".
- FB2 `human_norm_substitution_refused` — inject a human-norm strength/torque
  source into a biological row.
- FB3 `engineering_value_in_biological_registry` — move an M03 constant into
  the biological namespace.
- FB4 `fitting_unauthorized_refused` — smuggle a `fitted_*`/`optimized_*` key
  into the document (sealed A07 law; also scanned at validation time).
- FB5 `source_pin_mismatch` — mutate any pinned input sha.
- FB6 `screen_classification_mismatch` — flip one recomputed screen class
  (validator recomputes and refuses).
- FB7 `silent_default_refused` — replace an explicitly_unresolved entry with a
  resolved value without provenance.

## 8. Applicable house gates at freeze (G1-G9 disposition)

G1 applies (falsifier arms carry clean controls + guards + receipt rows).
G2 applies (lint + selftest; every report number traceable at printed
precision). G3 applies (qualitative claims rendered from probe receipts with
named refusal codes). G4 NOT APPLICABLE — no encoded video exists in a
records/offline card; disclosed, not skipped silently. G5 applies where any
relative-window comparison exists (classification bands carry
refuse_vacuous_comparison on the compared quantities). G6 applies in the
screen-class sense (per-quantity extractors keyed by quantity, never mixed
scans). G7 applies (profile loaded read-only; task_id SHORT; criteria identity
across dispatch/registry/prereg/checks). G8 NOT APPLICABLE in its capture
form (no image/video artifact; the single gate identity of this card is the
emitted document sha256, recorded in the receipt and report). G9 applies
(prereg committed separately BEFORE implementation; contribution within
32 files / 16 MB; commit-message metrics generated from FINAL receipts;
byte-exact carry via `.gitattributes` `* -text` only; publication is ONE
commit on the base with the `Agent:` trailer).

Two-sided pin law (friction study): this card pins NO surface contact
property; the elementwise_min pair budgeting is therefore not triggered —
disclosed as not-applicable with reason.

## 9. Evidence anchoring (CARD_STARTER v2)

Qualification evidence references are file paths (never directories),
store-relative where possible; before any attempt-workspace artifact is
referenced by the registry it is copied into
`E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-A08/` sha-verified.
No prose in reference fields; compound pins live in the report body.
