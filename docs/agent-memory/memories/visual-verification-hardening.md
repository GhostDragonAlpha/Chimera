---
name: visual-verification-hardening
description: Operator directive 2026-09-20 — visual deliverables get
  deterministic pixel falsifiers, not agent eyeballs; the splat-cloud monkey
  divergence root cause is not worth chasing
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_4e19803a-d027-4ebb-bbb3-e07c9c521e7a
---

The monkey-rendered-as-splat-cloud divergence (standing law = triangle technique; a visual lane splatified the marching-cubes OBJ meshes and rendered 118k splats; the grid also rendered opaque/one-sided) exposed a verification gap: a visual deliverable was accepted by an agent that either could not truly see the image (non-vision model using MCP image viewing) or latched onto old docs/code (the renderer-contract line describing the teddy's splat shell).

**Why:** Alan's call (2026-09-20): tracking the root cause is hard and not worth it — "strengthen our visual verification and just fix the problem, then forget about researching why it happened."

**How to apply:** every visual lane's falsifiers must be DETERMINISTIC PIXEL CHECKS runnable by any agent with no vision model and no image viewing: pre-registered grain/coverage metrics (splat cloud = grained + holey; mesh = smooth + filled), pixel-presence checks per camera pose (e.g., grid transparency from both sides), and a conformance gate failing if the scene posts the wrong render path. Record incidental git evidence as "undetermined" context — never budget archaeology on it. Also: the data layer is marching-cubes OBJ triangle meshes (meshes_preview/*.obj + manifest.json); "point cloud" appearance is always a render-path artifact — if a true point cloud ever arrives, the transfer is points → density raster → marching cubes (the pipeline's own proven route). Related: [[gait-walk-campaign-20260920]] (the walk-movie lane must bank SIZE/proportion vocab terms — same hardening, for the dyad scorer).
