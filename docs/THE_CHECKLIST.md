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
- [ ] **Rule 0 — the null configuration (the floor)**: AN OPERATIONAL DEFINITION MUST EXCLUDE
      THE TRIVIALLY-SATISFIED CONFIGURATION. Before optimizing any "the system achieves X"
      objective, evaluate X at the null configuration (rest/corpse/zero) BEFORE the run and
      bank the number in the preregistration as the objective's floor. A ~satisfied floor
      means the objective is missing its discriminating term (clearance, separation, sign) —
      it must gain that term or the preregistration is incomplete and the run proves nothing.
      Case: standing-pose (agent/standing-pose-20260921 @ 4ea008cb) — the corpse itself
      satisfied pad coplanarity (1.94 of 1.94 mm²), the numeric battery went green, and the
      fired visual falsifier showed the collapsed heap; successor v2.
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
- [ ] **Rule 0 — the instrument identity gate**: EVERY NEW TRACE SERIES SHIPS A
      PRE-REGISTERED KNOWN-ANCHOR IDENTITY CHECK — a measured equality the series must pass
      BEFORE its numbers enter any mine. An instrument that cannot prove it reads the thing
      it names is not an instrument; its numbers are prose. Model instance: the wave-42
      fire-anchor identity — the first [dvfa] pad_y sample equals the fire line's fy at ALL
      18 fire ticks (max |diff| 4.x mm), which is what licensed the tick-start-evaluation
      basis. Cautionary tale: the wave-45 [dvfl] pair — g1==g2 to machine precision in every
      line (452/452 inserted lines); the band's read site structurally erases the pad
      identity, the registered read-site (g1 vs g2) does not exist, and the degenerate read
      was reported verbatim, never tuned away.
      Evidence: waves 42-45 receipts (tools/science_funnel/validation/gait_zero_20260919/,
      lanes agent/gait-wave42-arch … agent/gait-wave45-*).

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
- [ ] **The publication gate**: a lane's completion report must include its own canonical
      verification — the literal `git ls-remote <canonical> refs/heads/<branch>` output,
      branch → tip — proving the branch landed at the tip the report cites. NO REPORT
      WITHOUT IT MAY CLAIM DONE: an unpushed branch is not a ship, and an outage is not a
      push. Instances: the vh-agent lane stranded by an SSH outage that nobody re-verified
      past; the port lane reporting complete with its branch unpushed at completion.

---

**The one-line law underneath all of it: no reference, no verdict; a description survives any
result, a theory can lose. If your step cannot lose, it is not a step — it is prose.**


---

## THE CONSTITUTION POINTERS (the three body laws, Amendment 2)

<!-- Appended 2026-09-20, lane agent/constitution-bio-laws-20260920. The
     operator's three body laws are constitution-grade in docs/THE_GAME.md
     (Amendment 2). This checklist POINTS; it does not duplicate law text. -->

- [ ] **THE BIOLOGICAL LAW** — one creature, one life stage; allometric
      coherence per stage; stage labels admission-required (adult must be
      adult-CONFIRMED, like sha256). Enforced by section 1 · DATA INTAKE (the
      stage-label + allometry steps). Canonical home: docs/THE_GAME.md,
      Amendment 2; gate: tools/creature_graph/reality_gate.py,
      stage_consistency + allometric_coherence.
- [ ] **THE TWO-CATEGORY LAW** — REALITY is the default and the reference;
      FANTASY is developer-driven explicit construction with an acknowledged
      violation manifest; violations never silent. Enforced by section 1 ·
      DATA INTAKE (the classification step). Canonical home: docs/THE_GAME.md,
      Amendment 2; gate output {category, violations[]} +
      bio.fantasy_acknowledge.
- [ ] **THE TRIANGLE DOCTRINE** — mesh-with-triangles is the data currency;
      anatomy layers are triangle-defined membrane outlines (bones, muscles,
      skin); never splatified for rendering. Enforced by section 2 ·
      CONSTRUCTION and section 3 · VISUAL. Canonical home: docs/THE_GAME.md,
      Amendment 2; the conformance gate + pixel_truth.

---

## 7 · TOOLING (any tool that claims a side effect)

<!-- Appended 2026-09-22, lane agent/workflow-rules-conversion-20260922. The
     janitor retrospective cycles 9-11 found the log saying `deleted` for paths
     that survived as empty shells: rmtree ran, the postcondition was never
     checked, and the word did the proving. This section is the general law;
     the instance lives in the tool itself. -->

- [ ] **THE POSTCONDITION LAW — TOOLS VERIFY THEIR OWN EFFECTS**: A TOOL THAT
      CLAIMS A SIDE EFFECT ASSERTS THE EFFECT BEFORE IT LOGS SUCCESS.
      `deleted` means the path is gone (the existence check runs AFTER the
      delete); `FAILED` means it survived — logged honestly, never a success
      word for an unverified state. A log entry is a claim about the world, and
      the world, not the call's return code, is the witness. Case:
      worktree_janitor.py cycles 9-11 — `shutil.rmtree(..., ignore_errors=True)`
      followed by an unconditional `action="deleted"` recorded surviving empty
      shells as deleted; the retrospective, not the tool, caught the lie.
      Instance: `E:/ChimeraWork/tools/worktree_janitor.py` (host-level;
      provenance copy: `tools/agent_fleet/worktree_janitor.py`).
