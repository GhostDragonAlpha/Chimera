# MAT2-W02 report — Close transcendental parity defects (reconciliation + fresh re-verification)

Card: **MAT2-W02**, kind=implementation, group="Walking foundation", calculation C09,
profile `records` (offline, numerical evidence required, no camera required).
criteria_sha256 `a9014f57b2cd9b88425fe1a92e26031e4cb7d2fb0884787de385f33736385e19`,
scope_sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`
(95-item material catalog, instruction revision astra-0031).
done_when: **"Reference-math equivalence is demonstrated at the frozen sites without
tolerance relaxation."** Card observation to reconcile: *"31/125 sites reported; fdlibm
equivalence must not be assumed."*

Attempt `296a4a34840e4c81a3a65f95ec491d11`, arrival `arrival-f2170bddbe024617aae68cfdfd9d7b0e`.
Isolated checkout `branch-4` @ `9ba1be77228e181f55ed2e4d2eb3e73e2f09685f`; publication base
`astra/gait-capture` @ `8ec90f13e76954596af3711c241c08b843ff78bf`; publication branch reserved
by the card: `review/MAT2-W02`. Contribution root:
`tools/monkey_campaign/contributions/MAT2-W02`.

## Verdict

**done_when demonstrated at the current lineage, with no tolerance relaxation.** Fresh CPU-only
gate on this machine: **125/125 frozen sites bit-identical**, dense sweep **55,392/55,392**
bit-identical, two runs byte-identical (`RESULT PASS_NO_TOLERANCE`). The pass condition is
IEEE-754 bit equality — the probe compares `B(oracle) == B(reconstruction)` with no epsilon,
no ulp allowance and no relaxed flag (`/fp:precise`, explicit `fma()` in the reconstruction).

The card's stale observation ("31/125 sites reported") is a **libdevice-vs-CRT** measurement of
the *old* GPU path against the CRT oracle, preserved as history; it is not the state of the
adopted reference math. The adopted implementation (UCRT reconstruction) is bit-exact against
that oracle at every frozen site.

**Claim class (DELIVERY.md taxonomy): component complete.** The reference-math parity
component is closed on the host leg with zero tolerance and its adopted implementation is present
in the walker kernel at the publication base. This card does not deliver a playable feature: named
downstream integration cards are MAT2-W01, MAT2-W03, MAT2-W04, MAT2-W07 and MAT2-W08, and
`PLAYABLE_BUILD.json` remains `UNQUALIFIED` (source_commit / build_recipe / executable_sha256 null).
No new port or scheduler is introduced; the existing gait phase/consts SSBO seam is untouched.

## 1. What existed vs what this attempt did

Per `MATERIAL_PLAN_ADOPTION.md`, old DONE does not become MAT2-DONE automatically, but known-good
code must not be reimplemented. Historical card `ONT-W02` (read-only scope archive
`01ea5cdd…`) is DONE: PR #184 head `531b99354ef241ced711abbaa137105afb28ca5b`, merge commit
`6348533e4c0e25d8968b50e312151f6105146ae4`, merged into `astra/gait-capture`.

Reused unchanged (byte-identical, extracted only with `git -c core.autocrlf=false show`):
the 125-site probe `parity_gate_host.cxx`, the dense sweep it ports verbatim, the pinned
reconstruction `ucrt_math.c` + generated tables/consts, `trig_inputs.txt`, the host shim, and
the five preserved lane records. The gate driver is the merged `ONT-W02/run_gate.py` with **only**
its identity header changed; `reconcile_lineage.py` proves segment A (pins table + helpers) and
segment B (tolerance declaration through end of file) are byte-identical to the merged driver,
so no gate condition could have been softened here.

Built by this attempt (task-owned, small): `extract_pins.py` (provenance extraction),
`reconcile_lineage.py` + `lineage_receipt.json` (identity/lineage checks R1–R4),
`capture_compiler.py` + `build_gate/compiler_identity.txt` (toolchain identity the historical
ledger did not record in-machine), this report and `qualification_receipt.json`.

## 2. Frozen predictions — outcomes (frozen in PREREGISTRATION.md before any build or run)

| id | prediction | outcome |
|---|---|---|
| P1 | reconstruction vs live CRT bit-identical at 125/125 frozen sites | **CONFIRMED** (`FROZEN125 125/125`) |
| P2 | fresh live-CRT oracle bits equal preserved `trig_host.txt` bits at all 125 sites; pinned inputs unchanged | **CONFIRMED** (0 drift, input bits match) |
| P3 | dense sweep zero differing pairs, census summing to 55,392 | **CONFIRMED** (SIN 6396, COS 6396, ATAN2 40400, ACOS 1000, HYPOT 1200) |
| P4 | fdlibm is NOT reference-equivalent: 115/125 identical, 10 differing (all 1 ulp) | **CONFIRMED** — "fdlibm equivalence must not be assumed" holds; the adopted substitution is the UCRT reconstruction |
| P5 | preserved libdevice-vs-CRT recount = 31 diffs, SIN 5 / COS 5 / ATAN2 6 / ACOS 4 / HYPOT 11 | **CONFIRMED** (exact match) |
| P5-sub | "always exactly 1 ulp" | **REFUTED** — 30 sites at exactly 1 ulp, `HYPOT` input 16 at exactly 2 ulps (carries finding F-ONTW02-ULPCLASS) |
| P6 | preserved on-device leg record present and consistent (`55517/55517 bit-identical -- PASS`) | **CONFIRMED as a cited record** — not re-measured (no GPU work in this attempt) |
| P7 | two probe runs byte-identical | **CONFIRMED** (`stdout_sha256_first == stdout_sha256_second`) |
| R1 | every pinned input identical at ONT-W02 head and at the publication base, equal to the frozen sha256+size table, and equal to what this attempt holds on disk (12/12) | **CONFIRMED** (`pin_manifest.json` verdict `PINS_OK`) |
| R2 | ONT-W02 merge and both dependency merges are ancestors of the publication base | **CONFIRMED** (5/5 ancestry checks) |
| R3 | the walker kernel at the publication base carries the adopted UCRT transcription with explicit-fma precise arithmetic, unchanged since the historical head | **CONFIRMED** (`ChimeraEngine/engine/shaders/gait.comp`, sha256 `b2f28e29…`) |
| R4 | archived ONT-W02 evidence files hash to their recorded values and the historical ledger's first-run stdout digest equals the independent reviewer's run | **CONFIRMED** (3/3 hashes; `517096e5…` equal) |

## 3. Cross-attempt reproducibility (new result of this reconciliation)

This attempt's fresh gate produced stdout sha256
`517096e569b6bc7bbeb3e581ab590c5f84fa8e1da9e97962ab2d34f61291d935` — **identical** to the
historical ONT-W02 ledger's first-run digest and to the independent reviewer's own recorded run
(`independent_stdout_run1.txt`). Same toolchain identity was captured rather than assumed:
MSVC 19.44.35228 for x64, toolset 14.44.35207, `cl /nologo /O2 /fp:precise /EHsc`, vcvars64 from
VS 2022 BuildTools (`build_gate/compiler_identity.txt`). The claim is reproducible, not merely
re-asserted.

## 4. Evidence classes (honest labeling)

- **Fresh runs here:** MSVC host compile of the pinned probe + two executions; per-site oracle /
  reconstruction hex ledger in `parity_gate_result.json` (`frozen125.sites`, dense census). This
  is a component-level numerical probe of pinned math implementations against the live UCRT.
- **Fresh identity checks here:** `lineage_receipt.json` (pins at two refs, ancestry, kernel
  adoption text, archived-evidence hashes, registry agreement read-only from SQLite).
- **Preserved records (hash-pinned, cited, not re-measured):** `trig_gpu.txt` (libdevice class),
  `trig_fdlibm_out.txt`, `co7_gate_out2.txt` (on-device gate), `co7_dense_full2.txt`,
  `co6_trig_dense.txt`, `trig_host.txt`.
- **Not claimed:** fresh GPU/on-device re-qualification, engine launch, walker-runtime behavior,
  walking/training completion. Those belong to W01/W03–W08 and the runtime lanes; a records-profile
  card cannot close them and this report does not.

## 5. done_when mapping

"Reference-math equivalence … at the frozen sites": the frozen sites are the card's original 125
(25 pinned inputs × 5 functions with the original probe's exact argument derivations), verified
byte-identical to the historical lane (R1). "Reference-math equivalence": bit equality between the
adopted reconstruction and its declared reference, the MSVC UCRT actually linked by the probe.
"Without tolerance relaxation": the only pass condition is `B(oracle) == B(reconstruction)`; any
ulp/epsilon allowance would fail this gate, and the driver's segment-identity check proves no such
allowance was introduced in this attempt.

## 6. Findings carried forward (unchanged, still true at this head)

- **F-ONTW02-ULPCLASS** — of the 31 preserved libdevice-vs-CRT differences, 30 are exactly 1 ulp
  and `HYPOT` input 16 is exactly 2 ulps; the closeout-3 "always exactly 1 ulp" wording is wrong.
  Recorded again in `parity_gate_result.json.preserved_libdevice_vs_crt`.
- **F-ONTW02-CENSUS** — the historical preregistration's grand total line (53,392) was an author
  addition slip; the frozen per-function census (sums to 55,392) is what the probe reproduces. The
  historical prereg file stays frozen; the correction stands.
- **F-MAT2W02-STALEOBS** — the catalog observation "31/125 sites reported" describes the rejected
  libdevice path, not the adopted reference math. It should be read as history; the current
  qualification statement is 125/125 bit-exact at zero tolerance on the host leg, with the device
  leg preserved rather than re-measured.

## 7. Remaining gates (open, honestly)

1. Independent review of this candidate (auto-offered after publication request).
2. Lead-serialized publication to `review/MAT2-W02` and exact-head verified merge; nothing here
   merges or self-approves.
3. Fresh on-device/GPU parity re-qualification remains with the GPU lanes; this card does not
   substitute for it, and no invisible support or kinematic shortcut is implied.
4. Downstream W01/W03 (tick-3 forelimb parity, frozen walk anchors) are separate cards; a merged
   diagnostic never qualifies them.

## 8. Constraints honored

CPU-only: `gpu_runs=0`, `engine_launches=0`, `training_runs=0`. All writes confined to this attempt
workspace (`checkout/tools/monkey_campaign/contributions/MAT2-W02` plus the `build_gate` scratch
directory, ~333 KiB). Source repository touched read-only via `git show`; registry read-only via
SQLite `mode=ro`. No credentials, no controller mutation, no numbered-branch push.

Trailer Agent: GLM 5.3 (monkey campaign worker, MAT2-W02 attempt 296a4a34840e4c81a3a65f95ec491d11).
