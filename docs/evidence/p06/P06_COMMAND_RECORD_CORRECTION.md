# P06 — P05 command-record correction (actual commands as run)

Status: CORRECTION RECORD, appended in the P06 evidence commit. R0 evidence
is untouched (repo append-only convention, `docs/evidence/p05/P05_REPAIR_R1.md:1–9`).

Why this exists: the recorded P05 build commands in
`docs/evidence/p05/P05_IMPLEMENTATION.md` §"Build comparison (P05 §B)" used
the shorthand form

```
cmake -S <tree>/ChimeraEngine/engine -B <scratch>/<side> -G "Visual Studio 18 2026" -A x64
cmake --build <scratch>/<side> --config Release
```

The `<tree>`/`<side>` placeholder collapsed three distinct configure sources
(the two engine trees AND the standalone probe) into one combined shorthand,
and the probe's own commands (correct in its README) were never recorded in
the run evidence next to the engine's. The correction below records the ACTUAL
commands as they were run — every configure source, build dir, generator, and
mode — verified 2026-09-07 against each build directory's `CMakeCache.txt`
(`CMAKE_HOME_DIRECTORY` = the configure source; `CMAKE_GENERATOR` = the
generator; `CMAKE_CXX_FLAGS` = the mode).

## Facts that anchor the record

- Engine candidate and baseline are DIFFERENT source trees; the standalone
  probe is a THIRD source tree. Each configures from its own `-S`.
- Three configure targets were built from these four build dirs:
  - `p05_builds/base` ← engine HEAD `abdea9a5` baseline (the `chimera_pub_base`
    worktree)
  - `p05_builds/cand` ← engine candidate (the `chimera_pub` worktree; R0 and
    R1 both rebuilt this dir)
  - `p05_builds/probe` ← the standalone probe (`tools/platform_surface_probe`)
  - `p05_builds/probe_asan` ← the same probe source, ASan flags
- Native path style in records: forward slashes in `-S`/`-B` (CMake cache
  absolutes), backslashes on the Command Prompt / PowerShell prompt line.

## R1-evidence slice (the commands behind P05_REPAIR_R1.md's re-measures)

Engine baseline (chimera_pub_base worktree @ `abdea9a5`, Detached HEAD):

```bat
cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub_base/ChimeraEngine/engine -B C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/base -G "Visual Studio 18 2026" -A x64
cmake --build C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/base --config Release
```

Engine candidate (`chimera_pub` worktree, R1 content; same dir also carried
the R0 build `53f37456` → `435b2073` step):

```bat
cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub/ChimeraEngine/engine -B C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/cand -G "Visual Studio 18 2026" -A x64
cmake --build C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/cand --config Release
```

## Standalone probe (the missing half of the record)

Release build + run (source: `tools/platform_surface_probe`, NOT the engine):

```bat
cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub/tools/platform_surface_probe -B C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe -G "Visual Studio 18 2026" -A x64
cmake --build C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe --config Release
C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe/Release/platform_surface_probe.exe
```

ASan variant (MSVC `/fsanitize=address /Zi`; ASan runtime
`clang_rt.asan_dynamic-x86_64.dll` supplied from
`C:\Program Files\Microsoft Visual Studio\18\Community\VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\`
by prepending it to PATH before the run):

```bat
cmake -S C:/Users/allen/AppData/Local/Temp/opencode/chimera_pub/tools/platform_surface_probe -B C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe_asan -G "Visual Studio 18 2026" -A x64 -DCMAKE_CXX_FLAGS="/fsanitize=address /Zi"
cmake --build C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe_asan --config Release
C:/Users/allen/AppData/Local/Temp/opencode/p05_builds/probe_asan/Release/platform_surface_probe.exe
```

## Toolchain / mode (one line each is enough, all four runs shared it)

- `CMAKE_GENERATOR:INTERNAL=Visual Studio 18 2026` (all four caches)
- `CMAKE_CXX_FLAGS:STRING=/DWIN32 /D_WINDOWS /EHsc` (base, cand, probe)
- `CMAKE_CXX_FLAGS:STRING=/fsanitize=address /Zi` (probe_asan only)
- Result gates (unchanged from `P05_REPAIR_R1.md`): Release 31/31, ASan
  31/31, 23/23 `.spv` identical; exe hashes as recorded there (measurements
  only).

## Corrections to the PUBLIC record (deltas vs. the shorthand)

1. The shorthand's single `-S` implied one source tree; the correction names
   all three (`…/chimera_pub_base/ChimeraEngine/engine`,
   `…/chimera_pub/ChimeraEngine/engine`, `…/chimera_pub/tools/platform_surface_probe`).
2. "Build comparison" covered only the engine; the probe commands now sit in
   the run evidence next to the engine's, distinguished by their own `-S`.
3. No `<tree>`/`<scratch>` expansion ambiguity remains: every path above is
   an absolute path that a fresh session can read from the cache it creates.