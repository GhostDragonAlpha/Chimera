# RESULT — product-feel-probe-01

Agent: subagent-worker-02 · branch `astra/tasks/product-feel-probe-01` · base 4a0f2ac7 (merged tip d9477713)
Resources: `rtx4090` + `engine_demo` granted via controller (rev 977), released with drain after.

## What was run (exactly as preregistered)

- Private build `.tmp/engine_build/feelfeel` (base + tip; no engine source
  changes by this lane; `ChimeraEngine/engine/build/` untouched).
- Loaded the committed subject pair: `Saved/meshes/monkey_birth.bin` (18459
  verts, 36424 tris — via `cpp_bridge.load_mesh_bin`) + `Saved/meshes/
  monkey_joints.bin` (JNT3 rig, nv 18459 — via `POST /joints_bin`). The live
  rig doc reports **28 joints** (the fleet's "19 joints" label refers to the
  driving-joint count of earlier packs; the recorded live truth is 28 named
  joints, see render_records.json `rig.doc`).
- The declared interaction: frame-indexed REST → PERTURB → HOLD → RESPONSE on
  the right-arm chain (exact name match `shoulder_R`, `elbow_R`), 10 fps,
  45 frames, fixed 3/4 camera (r=27, θ=0.5, φ=0.35). Peak thetas: shoulder 36°
  (0.6 × 60), elbow 75° (0.6 × 125) — engine-clamped.
- Captured `/glass` (the product surface) and `/frame` (pixel-clean twin) per
  frame; encoded with `cpp_bridge.encode_movie` → `product_feel_after.mp4`
  (860,351 bytes, sha256 in render_records.json) and the clean twin
  `product_feel_after_frame.mp4`.

## DYAD disposition: NOT_RUN in this lane — judge spawn requested via fleet mailbox

- Attempted honestly: the template's movie review was REFUSED by the provider
  contract itself (`temporal_review_requires_multiple_captures`, then
  `provider_cannot_verify_temporal_claim`) — the fleet's SubagentDyadProvider
  declares temporal capability `frames`, not `movie`. The preregistered
  fallback fired: the ordered-frames spec (6 keyframes f0/f12/f20/f25/f35/f44,
  chronological, hash-verified) PASSED plan —
  `dyad_plan/exact_prompt_product-feel-after-orderedframes-v1.txt`
  (sha256 e8a50fce23453d3ca3a86fbb3969baba29f1da86436620667c652dfd4f80534a).
- The spawn itself is the lead's Agent call; this lane has no subagent-spawn
  tool, and the local eye (LM Studio) is off-limits to fleet lanes. A
  coordination request was posted to the lead's mailbox (message id
  `a5f70dbe7d7b`, 2026-09-11T19:58Z): spawn the reviewer with the exact
  prompt, then `assemble` — the verdict lands in this directory as the dyad
  report. **The verdict is therefore NOT yet measured; acceptance stays
  NOT_CLAIMED and the probe's PASS/FAIL question is OPEN until the lead's
  assembled report arrives.**
- The judge spec is blind: the reviewer is told only the physical context
  (an application window, a creature, a clip) — nothing about the family, the
  scripting, or the expected behavior (r7 law; questions 1–4 in the spec).

## Retained artifacts

- `product_feel_after.mp4` — the judge's product-surface movie (committed).
- `product_feel_after_frame.mp4` — the pixel-clean twin (committed).
- `frames/g000,g012,g020,g025,g035,g044.png` — the judge's six keyframes
  (committed; hash-verified in the spec).
- `frames/MANIFEST_sha256.txt` — sha256 of all 90 captured stills (45 glass +
  45 frame). The non-judge stills stay local-only under manifest (git weight);
  the `/frame` stills were removed from local disk after manifesting — the
  `/frame` movie retains that channel's content.
- `attempt1_retired/` — the first render attempt (retired): the selection
  filter's bug matched `spine_upper` (ends with "r") and the prereg's peak
  formula read from the ext anchor (elbow peaked at 17° of a straddling ROM) —
  the creature bent its spine, not its arm. Both corrections are declared in
  the script comments; the interaction rule itself was unchanged.
- `render_records.json/.txt` — the full run log (launch sha256, loads, rig
  doc, selection, per-frame thetas, encode, drain).

## The measured state of the product question

The movie exists and is watchable (the scripted arm raise-and-return plays on
the creature in the product surface). Whether a BLIND judge can name the
behavior and state the lay lesson — the operator's actual question — is
pending the spawned judgment. **No product-feel verdict is claimed by this
lane.** If the judge later fails the rubric, the honest negative
("not-yet-human-legible") is the deliverable, exactly as preregistered.

## Resource record

Granted rtx4090 + engine_demo (rev 977) → both released with drain evidence
after the render (owned engine process exit recorded; port 8131 freed;
operator checkout and `ChimeraEngine/engine/build/` untouched).
