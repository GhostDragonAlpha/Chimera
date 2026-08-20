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
| **SPLAT** | the 3DGS cloud from the source | TripoSplat (`models/triposplat/gen_teddy_apose.py`) |
| **CAD** | the authored body fit to the splat | `tools/teddy_catalog.py` · `tools/fit_body_to_splat.py` |
| **COAT** | the trained/settled painted result | `tools/teddy_skin.py` · `tools/paint_from_splat.py` |
| **SCENE** | the composed scene | not built — encompasses the others when it lands |
| **STORY** | the narrative layer | not built — a slot reserved, per the declaration |

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
