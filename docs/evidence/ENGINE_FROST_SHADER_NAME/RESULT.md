# RESULT — engine-frost-shader-name-01 (gen 1)

Agent: subagent-worker-03 · Slot 8 (`E:\ChimeraWork\slot-08`) · branch
`astra/tasks/engine-frost-shader-name-01` · base
`51864412d2ffcc46acd89a3dc136e7e3c7a3350f` (HEAD==base verified clean; PR #79's
recorded adjacent defect, reviewer-verified).

## Verdict

**PASS — falsifier did not fire.** The frost render shader name contract is now
coherent at source: `load_frost` reads `shaders/render_tri_frost.frag.spv`,
the name the derived build (and every sibling vert/frag shader) already uses.
A fresh configure+build in the slot-private build dir produces the derived
artifact with the build's own glslc, frost's loader expectation resolves
against derived artifacts ALONE, and no hand staging was performed anywhere.
All 22 sibling shader name contracts are byte-identical to base and resolve in
the derived manifest.

## The fix (engine.cpp, 2 lines + 4 comment lines)

```diff
-        std::vector<char> spv = read_file("shaders/render_tri_frost.spv");
-        if (spv.empty()) { fprintf(stderr, "frost: render_tri_frost.spv missing\n"); return false; }
+        // frost-shader-name-01: read the DERIVED name. CMake emits
+        // <name>.<stage>.spv for vert/frag sources (render_tri_frost.frag
+        // -> render_tri_frost.frag.spv); the bare name was a stale hand-build
+        // artifact no clean build produces. Same rule as every sibling frag.
+        std::vector<char> spv = read_file("shaders/render_tri_frost.frag.spv");
+        if (spv.empty()) { fprintf(stderr, "frost: render_tri_frost.frag.spv missing\n"); return false; }
```

Contract ownership: the 2026-09-03 stale-spv incident made the shader manifest
DERIVED (engine/CMakeLists.txt:24-62, outside this task's scopes and
unchanged — the record's `ChimeraEngine/CMakeLists.txt` scope path does not
exist at base; the build rules live at `ChimeraEngine/engine/CMakeLists.txt`).
The build already emitted `render_tri_frost.frag.spv`; the one mismatching
read was the loader. The fix adopts the established vert/frag sibling pattern
(`render.frag.spv`, `render_tri.frag.spv`, `render_tri_edge.frag.spv`,
`render_tri_shadow.frag.spv`, `floor.frag.spv`) — no third pattern invented;
the compute family (bare `<stem>.spv`: gait, volp, water_*, frost_decode,
joints, hinge, membrane_demo, compute, sort, skin) is untouched.

## Scoreboard (prereg thresholds, all met)

| Check | Threshold | Measured |
|---|---|---|
| C1 source classification | all reads classified; exactly 1 pre-fix violator; 0 post-fix | PRE: 23 read names, **1 violator** (`render_tri_frost.spv` @ engine.cpp:4891); POST: 23 read names, **0 violators**; diff touches only the frost read + message lines |
| C2 manifest coherence | pre-fix absence demonstrated; post-fix all reads resolve | PRE: bare name ABSENT from the 51-entry derived manifest (reproduced); POST: **23/23 resolve** (`checks/c2_manifest_post.txt`) |
| C3 clean build, no hand staging | 4/4 | **4/4**: derived `render_tri_frost.frag.spv` produced by the build's own glslc (sha256 `7ea15d35…` from source `84061d7a…`); bare name exists NOWHERE under slot `.tmp`; fixed loader name == derived name; zero hand staging |
| C4 sibling contract preserved | no sibling broken | names removed == exactly {bare frost}; added == exactly {stage-suffixed frost}; **22/22** siblings byte-identical and resolving |

## Reproduction

```
cd E:/ChimeraWork/slot-08
git show 51864412:ChimeraEngine/engine/engine.cpp > .tmp/engine_base.cpp
python docs/evidence/ENGINE_FROST_SHADER_NAME/checks/check_names.py \
  --engine-text .tmp/engine_base.cpp --label PRE \
  --out-dir docs/evidence/ENGINE_FROST_SHADER_NAME/checks
cmake -S ChimeraEngine/engine -B .tmp/engine_build_fresh -G "Visual Studio 17 2022" -A x64
cmake --build .tmp/engine_build_fresh --config Release -- -m
python docs/evidence/ENGINE_FROST_SHADER_NAME/checks/check_names.py \
  --engine-text ChimeraEngine/engine/engine.cpp --label POST \
  --out-dir docs/evidence/ENGINE_FROST_SHADER_NAME/checks
```
PRE → `violators=1`; POST → `violators=0`; `checks/c3_clean_build.txt` verdict
4/4; `checks/c4_siblings.txt` PASS.

## Runtime

NOT_TESTED-with-reason: no GPU/engine admission was requested for this lane;
the deliverable is the name contract, fully determined CPU-side (C2/C3 prove
the loader expectation equals a derived artifact a clean build produces, and
the PR #79 lane already executed the frost load end-to-end — with the same
frag source compiled to SPIR-V — via its recorded staging workaround). The
runtime effect of this fix is that the staging workaround becomes unnecessary;
verifying that live is a frost-lane re-run, not a name-contract check.

## Source identity

- Base `51864412d2ffcc46acd89a3dc136e7e3c7a3350f` (merge of PR #69); fix built
  from the prereg commit + this implementation commit.
- `ChimeraEngine/engine/shaders/render_tri_frost.frag` sha256
  `84061d7ac9826d782a0c4f878ac0bf17c370c1f6ee3647d96346ba2d27608f3e` (unchanged).
- Derived `render_tri_frost.frag.spv` sha256
  `7ea15d358ecf1fa35eafdead08032a3c8c1e2218bc7c05f5391c2a34cf52e8af`.
- Toolchain: CMake + Visual Studio 17 2022 x64, Vulkan SDK 1.4.328.1 glslc.

## Corrections and limitations

1. **Read-count precision**: the prereg tabled "16 read sites"; the executed
   checker counts per shader-name literal — 23 (9 graphics + 13 compute +
   1 frost violator), because `w_make_pipeline`'s 8 call-site names and the
   hinge `spv_path` literal are individual names. The decisive thresholds
   (1 pre-fix violator → 0 post-fix; all siblings preserved) are unaffected;
   the count correction is disclosed here.
2. The checker captures `"/shaders/…"` and `"shaders/…"` literal forms; no
   backslash variants exist in engine.cpp at this base.
3. The PR #79 evidence runner (other branch, historical record) keeps its
   glslc staging workaround — after this fix integrates it is unnecessary for
   future lanes, but the retained evidence is not rewritten.

## Protected paths

`ChimeraEngine/engine/build/` was never touched: all builds ran in
`E:/ChimeraWork/slot-08/.tmp/engine_build_fresh` (slot-private scratch).
