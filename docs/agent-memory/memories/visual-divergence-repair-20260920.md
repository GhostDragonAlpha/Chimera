---
name: visual-divergence-repair-20260920
description: The triangle-monkey/grid visual divergence repair lane — operator's
  two visual defects, the data-format vs off-script root-cause question, and the
  verdict-before-repair protocol
metadata:
  node_type: memory
  type: project
  originSessionId: sess_4e19803a-d027-4ebb-bbb3-e07c9c521e7a
---

Operator defect report (2026-09-20, two visual divergences from standing law):
1. **The monkey renders as bones AND a splat cloud** — wrong; the TRIANGLE technique is the standing law (matter-kernel triangles law); the splat cloud path (`ct_skeleton_layer.layer_splat_buffer` → POST `/membrane_bin`, 118k splats) is a DIVERGENCE/regression, not a technique to migrate to. Operator confirmed the framing sharply ("it was already supposed to be the fucking technique").
2. **The guide grid occludes and is single-sided** — anything behind/below it is culled from above; from underneath the top side is culled. It is a "Gaussian guide" by intent and must be double-sided + non-occluding (depth-write off, drawn after opaque geometry).

**Root cause UNRESOLVED by the operator**: "It could be an issue with the data format of the source data, or it could be the fact that an agent went off script and grabbed onto old ideas. We are not sure which." → the repair lane was REDIRECTED mid-flight (SendMessage): its receipt must open with a VERDICT (data-format | off-script | both) backed by git evidence (the introducing commit, its agent trailer, whether its receipt cited a measured ingestion constraint) AND a direct ingestion test (load the source bone meshes through the established triangle/mesh path; success = the splat path was never forced by data). The repair branches by verdict: off-script → restore triangle path + a conformance gate (a test failing if the monkey scene posts a splat buffer); data-format → fix the ingestion/data path first, then the same falsifiers.

**Lane**: `agent/triangle-monkey-grid-20260920`, worktree `E:\ChimeraWork\trimonkey-agent`, branched from master, own free port (8127/8096/8097/8129/8131 are taken by operator/other lanes). Master's engine still has the argc>3 FAST_FAIL trap (the fix lives on `agent/engine-determinism-argc`, unmerged) — launch with the port only. Deterministic pixel falsifiers (no model calls): grain + silhouette-coverage metrics with pre-registered thresholds for the mesh-vs-splat distinction; two-camera grid transparency check (object below grid visible from above and vice versa) with before/after PNGs.

**DATA-FORMAT HALF ANSWERED (2026-09-20, relayed to the lane)**: the source data is NOT point cloud — the committed artifacts are marching-cubes per-bone OBJ TRIANGLE MESHES (`tools/science_funnel/data/morphosource_ct/meshes_preview/*.obj`, ≤30k faces each + manifest.json; full-res gitignored with sha256 receipts). The 118k-splat buffer was a RENDER-TIME splatification of those meshes — so the point-cloud hypothesis is answered NO at the data layer and the verdict leans off-script (the lane's ingestion test + git evidence settle it). The operator's follow-up ("if the data is point cloud, how do we transfer to triangle mesh — I believe I have solved it") was answered: no conversion needed; if a true point cloud ever arrives, the transfer is points → volumetric density raster → marching cubes (the pipeline's own proven volume→mesh route). The operator's enumeration of "what is wrong" arrived truncated mid-sentence — pending.

**The baby-macaque curl issue is real and measured at every stage it touched**: it mirror-refused bone-ID v1, capped specimen B at 14/24, collapsed the mounting chain links to −71% vs standing Table-1 (the specimen is folded), and gave the dyad its "curled-up, fetal-like" read; the mounting lane's H2 per-bone scaffold is the standing answer for the final visual.

**Lead's verification thread**: if the verdict is off-script, the deeper divergence may be the RENDERER-CONTRACT DOC LINE describing the splat shell (AGENTS.md/visual-lane briefs quoted it — the ct-skeleton-visual lane brief cited "splat shell /membrane + /frame"), leading agents to the old technique; the durable fix then includes correcting the doc pointer, not just the code.

Related: [[gait-walk-campaign-20260920]] (the walk lanes are file-disjoint), [[matter-kernel-spec-and-build]] (the triangles law), [[alan-operator-preferences]] (the regression-not-migration correction, 2026-09-20).
