# THE CHECKLIST — the one workflow every agent runs

<!-- THE POINTER LAW: this file holds the SEQUENCE and the GATES. Each line points at its
     law's canonical home. It does not duplicate law text — a doc that duplicates a fact
     drifts from it (AGENTS.md's own lesson). Amendment history is git; laws live in their homes. -->

**Origin (2026-09-20):** the operator's directive — "there's gotta be a workflow checklist
document that all agents use to develop in the project, otherwise we're gonna just be fighting
this in different ways all the time." The splat-cloud divergence (a visual lane rendering the
bone meshes as an old-technique splat cloud against the standing triangle law) was the proof
case: every gate below exists because prose said one thing and an agent did another.

**How to use this:** walk it top to bottom, every task, no skipping. A step you cannot pass is
a BLOCKED-with-evidence verdict (AGENTS.md: blocked must be earned), never a workaround.

---

## 0 · BEFORE YOU BUILD

- [ ] **Orient first**: `python tools/orient.py`; read AGENTS.md → `docs/THE_LAW.md` → this file.
- [ ] **Rule 0 banked BEFORE any code**: statement (disagreeable) · prediction (unmeasured) ·
      falsifier (named before the run). Home: `Chimera/docs/EXPERIMENTAL_METHOD.md`.
- [ ] **Rule 1 — derive it**: no parameter sweeps; every number traces to an equation or a
      measurement. Home: AGENTS.md CHIMERA-LAW.
- [ ] **Scope**: own worktree, own branch (`agent/<lane>-YYYYMMDD`), NEVER master, NEVER
      port 8127, NEVER `E:\PythonChimera`. Commits carry your agent trailer. Receipts
      append-only. Data files byte-stable (`tools/science_funnel/data/** -text`; blob-verify
      before commit).

## 1 · DATA INTAKE (any external anatomy/imaging data)

- [ ] **Format**: mesh-with-triangles is ALL WE NEED — translate the triangles into the
      project's triangle format (the CA/matter system) and the systems apply. Point-cloud
      sources: raster→density→marching cubes (the proven in-house route) — never render raw
      points. Volume sources (CT/MRI): the segmentation pipeline owns volume→mesh.
- [ ] **Provenance**: sha256 receipts, download receipts, license recorded (commercial-OK,
      e.g. CC BY 4.0). MorphoSource is PERMANENTLY manual-only (the operator downloads).
- [ ] **STAGE LABEL admission-required** (the biological law): every specimen carries
      species + life-stage + provenance (adult must be adult-CONFIRMED from collection
      records, never presumed). Unlabeled = unadmitted. One creature, one life stage —
      stage mixing is refused (a baby macaque's proportions are adaptive: clinging, large
      head ratio, flexed posture — biology, not noise).
- [ ] **THE CLASSIFICATION**: the adjudicator outputs `{category: reality|fantasy,
      violations[]}`. REALITY is the default (the reference); FANTASY is developer-driven
      explicit construction with the violation manifest acknowledged — violations are never
      silent. Home: `tools/creature_graph/reality_gate.py` (the gate module) + the
      two-category law in the campaign receipts.
- [ ] **Allometry coherence**: segment proportions vs the stage's scaling tables (the gate
      checks; PROVISIONAL table entries are marked, never bare guesses).

## 2 · CONSTRUCTION (anatomy → membranes)

- [ ] **Triangles define membranes.** Every anatomical layer is a membrane outline: bones
      (compartments — the anatomy pivot) now, muscles next, skin eventually. The data gives
      the outline; the membranes are defined with triangles in the matter construction system.
- [ ] **The MATTER SYSTEM owns geometry**: triangles-are-weights residency, bonds-are-materials
      (bond geometry from MEASURED adjacency — e.g. the touching-edge chains — never invented
      joints), cure strength, the scratch law. Home: the matter kernel docs + format tests.
      NEVER splatify mesh data for rendering (the canonical violation — the monkey-as-splat-cloud).
- [ ] **Stage-true at scale 1.0**: no cross-stage stretching (the H2 3.79–8.8× per-bone
      factors are the negative example, measured and adjudicated FANTASY).

## 3 · VISUAL

- [ ] **The TRIANGLE technique is standing law** (the renderer decision + the matter laws).
      No splat clouds for creatures.
- [ ] **Deterministic pixel verification — no vision model, no agent eyeballs**: grain +
      coverage metrics (per-region), pixel-presence per camera pose (e.g. grid transparency
      both sides), orbit clip censuses, conformance gates (the scene posts the right render
      path). Thresholds pre-registered. Home: the visual checker script + its receipts.
- [ ] **Dyad judgments** (when a human-verdict channel is needed): pre-banked vocabulary
      INCLUDING size/proportion terms; verbatim reads recorded; the scorer's blind spots are
      findings, never tuned away.

## 4 · PHYSICS / WALK LANES

- [ ] **One membrane per lane**; the falsifier names the successor; at most ONE itemized
      implementation repair per run (the wave pattern). Receipts: statement/prediction/
      falsifiers FIRST, measurements appended, pre-registered block never edited.
- [ ] **The standing falsifier battery**: free-fall exact, determinism bit-identical, graph
      tests green (both PYTHONPATH roots), caps enforced in code (never raised away), ledger
      diagnostics named per channel.

## 5 · VERIFICATION (what the lead runs on YOUR lane)

- [ ] Engine lanes: fresh cmake build, digit-exact reproduction of the receipt's headline
      numbers. Derivation lanes: script re-run in a fresh clone, clean `git diff` = byte-exact.
      Visual lanes: the pixel checker. Research lanes: sources re-checked, criteria stated
      before ranking.
- [ ] Reds are banked honestly (a falsifier that fires is a finding); greens are reproduced,
      not trusted.

## 6 · SHIP

- [ ] Commit (trailer) + push YOUR BRANCH ONLY. Report: the derivation with measured inputs,
      falsifier verdicts (greens AND reds), refusal/pass numbers, commit hash. Done-is-a-commit.

---

**The one-line law underneath all of it: no reference, no verdict; a description survives any
result, a theory can lose. If your step cannot lose, it is not a step — it is prose.**
