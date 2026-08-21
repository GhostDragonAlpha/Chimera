# THE METHOD — the declared development methodology (2026-08-20)

> Declared by the operator, 2026-08-20, verbatim in intent: *"These are mandatory
> checklists that you must go through as a form of the workflow. Make me an engine where
> you're supposed to put all this shit to show the human. Everything should be presented
> in the web viewer first. We have to make the manual method and then we will apply the
> dyad to it — but not until we get the manual method down. All of the processes will be
> defined by MCP tools that we call as part of the MCP server system that controls
> Chimera Engine."*
>
> This document is the law of HOW work proceeds. It sits on top of
> [`THE_WORKFLOW.md`](THE_WORKFLOW.md) (the day-loop: ORIENT → NEXT → PROVE → CHECK →
> COMMIT) and [`THE_AUTHORED_PIPELINE.md`](THE_AUTHORED_PIPELINE.md) (the asset stages:
> BODY → SETTLE → PAINT → REGIONS). What it adds: **every stage has a slot in the
> Chimera viewer, and no stage passes without the human's authorization.**

## The stage slots

The Chimera Engine viewer grows a slot per stage. Each slot shows exactly one kind of
artifact; each artifact is presented in its slot before any downstream work runs.

| Slot | Artifact | Tooling that fills it |
|------|----------|-----------------------|
| **SOURCE** | the 2D picture | shown FIRST, before any generation run |
| **SPLAT** | the 3DGS cloud from the source | **multi-view orbit lane** (below) — fallback: TripoSplat single-image (`models/triposplat/gen_teddy_apose.py`) |
| **CAD** | the authored body fit to the splat | `tools/teddy_catalog.py` · `tools/fit_body_to_splat.py` |
| **COAT** | the trained/settled painted result | `tools/teddy_skin.py` · `tools/paint_from_splat.py` |
| **SCENE** | the composed scene | not built — encompasses the others when it lands |
| **STORY** | the narrative layer | not built — a slot reserved, per the declaration |

### The SPLAT stage: multi-view orbit lane (declared 2026-08-21)

**The fur law (measured, settled):** single-image feed-forward generators
(TripoSplat, DiffSplat, LGM) produce surface-membrane pancake splats — fur relief is
unobservable from one view, so the model paints a flat shell. Shard-type stand-up fur
splats come only from multi-view photogrammetric optimization, where views disagree and
force the splats off the surface. The operator identified this on sight in
`genbear_front.splat` ("I can see the shards"). The conclusion, operator-declared:
*build our own CAT3D-class lane from local $0 pieces* — no closed model.

The lane (every step local, commanded, recorded):

1. `tools/cut_anchor.py` — source photo → rembg RGBA cutout, centered, black-ready
   (SV3D is image-conditioned; the anchor IS frame_00 of every ring).
2. `external/sv3d-diffusers/gen_ring.py --elev E --name N [--flip]` — SV3D commanded
   orbit rings (eq, ±20°, ±40°; negative elevations via the verified flip trick).
   Loop-closed by construction: ring frame_00 = frame_21, drift impossible.
3. `tools/assemble_ring_poses.py` — ring dirs → `poses.json` (the commanded orbit IS
   ground truth; no pose estimation, hence no ghosting).
4. `tools/sv3d_to_colmap.py` — poses + SIFT focal calibration (RULE 0: interior minimum
   or the run is void) → gsplat COLMAP-format dataset.
5. gsplat `simple_trainer.py default --data_factor 1 --max_steps 30000 --disable_viewer`
   in `.venv-gs` (ninja on PATH; cached `gsplat_cuda.pyd`, `TORCH_CUDA_ARCH_LIST=8.9`).
6. `tools/orient_splat.py` — PLY → PCA-upright, recentered `.splat`
   (head/front sign decided by an eye-check render, never assumed).
7. `tools/densify_splat.py` — smart clip (8th-NN distance > 3× median = floater) +
   modest growth. **Never a global alpha floor** (proven by A/B to arm TripoSplat's
   background shell and blow out the bear).
8. Six-angle shots (`tools/http_shots.js`), agent self-inspection, then the SPLAT gate.

## The gates (mandatory checklist, every asset, every time)

1. **SOURCE gate** — the 2D picture is opened on the operator's screen and authorized
   *before* any generation. No authorization, no run.
2. **SPLAT gate** — the generated splat is opened in the interactive viewer
   (rotate / zoom / all angles). The agent inspects its own renders first (numbers +
   pictures; prose claims are not evidence). Then the operator authorizes or names the
   defect.
3. **CAD gate** — the fit overlay and part diagnostic are presented; the operator
   authorizes the geometry before paint rains.
4. **COAT gate** — the settled/painted result is presented at 6 angles minimum;
   the operator authorizes.
5. Defects named at any gate return work to that stage. They do not travel downstream.

## Manual first, dyad second

The manual method — this checklist, driven by the human's eye — is built and proven
FIRST. The dyad (the machine eye, `S7 DYAD` in THE_WORKFLOW) is applied to the process
only after the manual method demonstrably works. THE HUMAN remains one of the two legal
terminals (AGENTS.md); the machine eye is an assistant to the gate, never its replacement.

## MCP tools are the process surface

Every stage transition and every presentation is an MCP tool on the MCP server that
controls Chimera Engine (`ChimeraEngine/MCP_ENGINE.md`). The intended surface, to be
built in this order:

- `present_image(path)` → SOURCE slot
- `present_splat(path)` → SPLAT slot (interactive)
- `present_fit(parts_json)` → CAD slot (overlay + part colors)
- `present_coat(splat, meta)` → COAT slot
- stage tools (`generate_splat`, `fit_body`, `settle_coat`, `paint_coat`) wrap the
  existing scripts so a run is a tool call with a recorded falsifier, not an ad-hoc
  shell line
- `authorize(stage, verdict)` → records the human's gate decision beside the artifact

## Standing orders confirmed alongside this declaration

- No paid APIs. Local models only.
- No subagents for the pipeline work; the agent does the work itself.
- One heavy GPU process at a time.
- The agent never presents unverified output; it looks at its own renders first.
- Documentation is updated as the method is learned — this file changes as we work.
