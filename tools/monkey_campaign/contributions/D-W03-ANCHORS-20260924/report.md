# D-W03-ANCHORS-20260924 — report (versioned anchor adoption evidence)

Card `D-W03-ANCHORS-20260924` (planning id **W03**, kind `bounded_diagnostic`), attempt
`f7fd439796784e7e980a33cd90978c0d`, arrival `arrival-ec97e63be318447499de475cc02077cd`,
local branch `branch-2` (checkout head `c525b82c7c3ce0128565424764293a3c85811ab3`).
Criteria hash `841796bb2d8c072af8d571e3d4222c93126c44bfff6e406b43bd6faa0fb3c886`.
Constraints honored: `source_edit_allowed=false`, `gpu_allowed=false`, max 16 MiB new
output. Source repo `E:/ChimeraWork/monkey-play-20260924` read-only; every source byte
read via `git show`/`ls-tree`/`cat-file -e` (all read-only), zero working-tree changes,
zero checkouts, no engine/model/GPU/broad runs. This card is read-and-report only.

Deliverables in this directory: `report.md`, `receipt.json`,
`anchor_manifest_v2.proposal.json` (machine-readable proposed v2 manifest).

## 1. Objective and falsifier

- **Objective:** "Prepare the versioned anchor adoption evidence and isolate the remaining
  C++/host/device gap."
- **Falsifier:** *Changed old anchors, an unexplained out-of-band change, or a CPU result
  labeled as new device qualification fails.*

## 2. Reconciliation of the prior attempt (cc6f1126) — three corrections, one confirmation

The prior report (task-results/D-W03-ANCHORS-20260924/report.md) is substantially built
on but contains three errors this card corrects with evidence:

**C1 — the W03 ruling EXISTS and already decides Option B.** The prior report states "No
`tools/monkey_campaign/DOC_AUDIT.md` exists in the repo" and leaves "Option A vs B" as
its first open checklist item. The ruling file exists at
`E:/PythonChimera/tools/monkey_campaign/DOC_AUDIT.md` (astra-0008, "W03 ruling: versioned
corrected anchors, with adoption gates"): *"Choose **Option B, explicit versioned
re-baselining**"*, with the authority limits: retain v1 hashes/failure receipts
byte-for-byte, explain changed v2 sites against the derived tie/band rule, demonstrate
independent boundary oracles + outside-band preservation + C++/host/device parity per
changed path, keep GPU and C3 gates open until measured, non-author review before the
coordinator publishes the versioned compatibility certificate, no seed substitutions or
success-driven re-runs. The prior report's checklist item 1 ("Decide Option A vs B
(Astra)") is **already answered** — the manifest below is therefore built under Option B.
Ruling-file content sha256 `46f7df841858d5d49ec7b727136918135993a2f8cf8cdb432fd98e11291a1ff2`;
note the file is currently an **untracked** working file at `57beb8b2` (absent from
`origin/master` and `monkey-play-20260924`) — the lead should commit it so the ruling
itself is reproducible (recorded as a finding, not an action this card takes).

**C2 — the "identity gap" hash-mismatch table is an extraction-convention artifact.**
The prior report compared registry sha256 values against raw `git show` blob bytes and
found 5 MISMATCHes, concluding "the v1-preserved / v2-recorded anchor identities … are
not reproducible from the repository." This card recomputed every registry entry two
ways: **raw blob** and **blob with LF→CRLF conversion**. Result: all 18 text anchors in
the registry reproduce **exactly** from the `a62b286e` blobs — 15 under the CRLF
convention (the registry hashed the on-disk working-tree bytes, which carry CRLF, while
the committed blobs store LF), 3 raw (`scene_sha256.txt`, `README.md`, empty
`co8_csub310.out`). **Zero content mismatches.** The reproducibility protocol simply
needs the newline convention declared (both hashes are recorded per entry in the
manifest). The prior report's "smudge/line-ending artifact" suspicion was tested and
rejected by that worker; this card's two-sided test confirms the artifact was exactly
that.

**C3 — the tick-41 fixture IS tracked in git.** The prior report's §3 table notes
"(fixture dir not tracked in git)". `git ls-tree -r a62b286e` lists all 7 fixture files
(`co8_t41_fixture/{README.md, device_drill_t41.out, host_drill_t41.out, scene_sha256.txt,
state_t39_cpp.txt, state_t40_gpu.txt, state_t40_host.txt}`) and all 7 hashes verify
(5 CRLF, 2 raw).

**Confirmed from the prior report (re-verified by this card):**

- `a62b286e` is an **orphan**: `git branch -a --contains` returns nothing; not an
  ancestor of `origin/master`. It exists only as a commit object named in receipt text.
  This is the **one hard identity blocker**: no other worker can re-verify any anchor
  until the lead/publisher brings `a62b286e` onto a reachable ref (or re-commits its
  tree under one).
- The four v2 binaries (`walker_env_v2.dll`, `host_loop.exe`, `walker_env_co8.dll`,
  `walker_env_d41.dll`) are **not in git anywhere**, by design: the `typeb_gpu`
  `.gitignore` excludes `*.dll`/`*.exe` ("Built binaries stay on disk, git carries
  source (recompile is minutes; source is the truth). Banked gotcha 2026-09-22."). Their
  registry hashes were on-disk measurements; the on-disk files no longer exist. The
  manifest re-anchors binaries to **source + build script + rebuild hash**.
- TIE2 commit `ebc00096` is on branch `monkey-play-20260924`; its 5 battery artifacts
  (`run/tie_boundary_probe.{cxx,exe}`, `run/build_tie_probe.cmd`,
  `receipts/case123_tie_boundary_host.out`, `receipts/case5_replay_host_v2.out`) are
  **on disk now and verify RAW** against the registry (5/5, checked by this card).

## 3. Verified anchor inventory (all values recomputed by this card)

Full machine-readable table: `anchor_manifest_v2.proposal.json` (22 entries). Summary:

| Class | Entries | Verified | Convention | Not in git |
|---|---|---|---|---|
| v1-preserved fixture (`co8_t41_fixture/*`) | 7 | 7 | 5 CRLF + 2 raw | 0 |
| v1-band (`co8_csub310.err/.out`) | 2 | 2 | 1 CRLF + 1 raw(empty) | 0 |
| pre-v2 tolerance (`co8_ksub_prorow*.out`) | 3 | 3 | 3 CRLF | 0 |
| v2-recorded runs (`co8_{hl,dll,dllb,cp,dll50,host50}…`) | 6 | 6 | 6 CRLF | 0 |
| v2 binaries (`walker_env_*.dll`, `host_loop.exe`) | 4 | 0 | — | 4 (gitignored by design) |
| TIE2 battery (on-disk, `ebc00096` branch) | 5 | 5 | raw | 0 |

Extraction conventions (declared, per entry, in the manifest):

- **raw**: `sha256(git show <rev>:<path>)` — byte-for-byte blob.
- **crlf**: `sha256(git show <rev>:<path>` after LF→CRLF`)` — equals the on-disk
  working-tree bytes the registry hashed at shutdown.

Constant across every receipt: scene
`f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342`, stdout `8c537cdb…`,
refusal 302 ticks, worst ledger `30.970714` J (W03's frozen bar, cited-in-receipts; not
recomputed by this CPU-only card).

## 4. C++ / host / device coverage map — historical vs fresh (the gap, isolated)

| Evidence | C++/device | Host | Nature |
|---|---|---|---|
| host-v2 vs GPU-v2 parity: FULL states bit-identical t=1..43 (`co8_dll_v2b_120.txt` vs `case5_replay_host_v2.out`) | walker_env_v2.dll (gone; rebuild required) | walker_kernels.cuh CPU-compiled | **HISTORICAL** — single capture preserved at shutdown `a62b286e`; not a fresh run |
| host pre-v2 vs host v2: bit-identical t=1..40, first divergence t=41 (tie engagement tick; 60 FULL lines differ t=41..100) | — | both host | HISTORICAL; the divergence is the Option-B version bump's own expected diff, explained by the tie/band rule |
| reach-band v1 endpoint oracle: 10/10 preregistered cases PASS; outside-band drift=ok, feasibility=ok (`reach_band_test.c`) | device kernel via regenerated source | `walker_numba_split.py` + gait_controller host | The **independent boundary oracle** the ruling demands; committed evidence |
| tick-74 2-ulp chain: host q2 reconstructed exactly from printed intermediates under BOTH ucrt and CRT; cpp differs by 1 ULP upstream (FK/T-matrix last-ulp translation; host==GPU by construction) | cpp leg characterized | host leg characterized | Diagnosed knife, registered as its own v2 item (not the band) |
| TIE2 case 1–3 tie-boundary host probe (`case123_tie_boundary_host.out`) | — | host | CPU legs executed |
| TIE2 GPU legs | — | — | **NEVER EXECUTED** — "queued behind broker (steam live)" at commit `ebc00096` |

**Isolated gap (what W03 still lacks, none of it available to this gpu_allowed=false card):**

1. **Fresh uncontended GPU device leg** of tie-v2 (replay past tick 41 on the device from
   the fixture state), in a broker-scheduled clean window — to reproduce the t=1..43
   host-vs-device parity *now*, rather than from shutdown memory.
2. **C3 bars re-measure** in that uncontended window (W03 `done_when`: Freefall/stand/
   C1/C2, scene `f6844ee…`, stdout `8c537cdb…`, 302 ticks, `30.970714` J on the training
   revision).
3. **Rebuilt v2 binaries** (or a decision to anchor binaries to source+script only) —
   required before any fresh device run can even load `walker_env_v2` semantics.
4. **Tick-41 row-0 sign knife** (g0 = −6.9e-18): separate v2 registration with its own
   scale (kTouch 1e-5 pad resolution quantum) — the reach band does NOT resolve it
   (Measured Finding 2, per the prereg's separation clause).

Nothing in this report labels a CPU result as new device qualification; the only
host-vs-device parity on record is explicitly tagged historical.

## 5. The proposed versioned anchor manifest v2 (Option B)

Schema `chimera.anchor_manifest.v2.proposal` in `anchor_manifest_v2.proposal.json`.
Design points, per the ruling:

- **v1 retained byte-for-byte:** every v1-preserved/v1-band/pre-v2 registry hash is
  carried unchanged into the manifest with its provenance commit and a now-verified
  extraction convention. Nothing old is overwritten.
- **v2 recorded, not adopted:** the v2-recorded runs are recorded as evidence with their
  `a62b286e` identities; adoption waits on the gates below.
- **Binaries re-anchored:** `source revision + build script (build_dll_v2.ps1,
  build_host_loop.ps1, build_dll_co8.ps1, build_d41.ps1) + declared rebuild-and-hash
  step`. Binary blob hashes are recorded as historical-only.
- **Declared extraction convention per entry** (raw and CRLF both recorded), so any
  future verification reproduces the exact comparison this card made.
- **Adoption gates (all OPEN, each with an owner):**
  - **G1-reachable-ref** — bring `a62b286e` onto a reachable branch (lead/publisher);
    then re-verify all 22 entries via the declared conventions. *This is the smallest
    unblocked next action and the one hard identity blocker.*
  - **G2-binary-rebuild** — rebuild v2 binaries from pinned sources; record fresh hashes
    or retire binary hashes to source+script anchoring.
  - **G3-fresh-gpu-device** — fresh uncontended device tie-v2 replay (broker window);
    reproduce host-vs-device parity t=1..43 now.
  - **G4-c3-bars** — uncontended re-measure of the frozen W03 bar on the training
    revision.
  - **G5-tick41-sign-knife** — register the row-0 sign decision as its own v2 item with
    the kTouch scale.
  - **G6-review-certificate** — non-author review of the manifest; coordinator publishes
    the versioned compatibility certificate. No seed substitutions, no success-driven
    re-runs.

## 6. Remaining-check checklist (precise, corrected)

1. [x] ~~Decide Option A vs B~~ — **decided: Option B** (`DOC_AUDIT.md` astra-0008;
   prior report's "missing ruling" finding corrected — see §2 C1).
2. [ ] **G1**: lead/publisher brings `a62b286e` onto a reachable ref; re-verify the 22
   manifest entries with the declared conventions (expected values already in the
   manifest).
3. [ ] Commit the ruling file itself (`DOC_AUDIT.md` is untracked at `57beb8b2`).
4. [ ] **G2**: rebuild v2 binaries from pinned sources; record fresh hashes.
5. [ ] **G3**: fresh uncontended GPU device tie-v2 replay in a broker window.
6. [ ] **G4**: uncontended C3 bars re-measure against the frozen W03 bar.
7. [ ] **G5**: register the tick-41 row-0 sign knife with its own scale.
8. [ ] **G6**: non-author review; coordinator publishes the versioned compatibility
   certificate.

## 7. Falsifier self-check

- **Changed old anchors?** No — zero writes anywhere outside this attempt directory; all
  source reads were `git show`/`ls-tree`/`cat-file -e`; `a62b286e` and all refs
  untouched; the manifest *copies* old hashes, never replaces them.
- **Unexplained out-of-band change?** The only new bytes are this report, receipt.json
  and the manifest proposal in this attempt workspace. Every hash in them is either
  cited (with source file + commit) or recomputed here (command class recorded in
  receipt.json).
- **CPU result labeled as new device qualification?** No — the sole host-vs-device
  parity on record is tagged HISTORICAL (shutdown capture); the fresh device run is an
  explicitly OPEN gate (G3) requiring broker/hardware outside this card's limits.

## 8. Next implementation step

W03 stays OPEN until gates G1–G6 close. The smallest unblocked action is **G1** (a
lead/publisher git operation: make `a62b286e` reachable), immediately followed by G2
(source rebuild of the v2 binaries — minutes, per the banked gitignore gotcha). G3/G4
need the broker/GPU window; G5 is a registration write; G6 is process. This card hands
the verified manifest to the reviewer/lead as the adoption evidence the ruling requires.
