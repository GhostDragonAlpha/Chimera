# LEAD TAKEOVER HANDOFF — the nvcc route (read me first)

## PROVEN (by direct lead work, 2026-09-22)
1. THE TOOLCHAIN (run verbatim): "/c/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.8/bin/nvcc.exe" -c X.cu -o X.o -arch=sm_89 -ccbin "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/cl.exe" -I. -std=c++17 --expt-relaxed-constexpr — VS18 cl is REJECTED by CUDA12.8 (host_config check); the 2022 BuildTools cl works. Double-precision device math verified at E=1024.
2. THE REAL PHYSICS COMPILES FOR DEVICE: gait_controller_ref.hpp (git-extracted @30821ef7) + gen_device_header.py (brace-depth annotation v2) -> walker_device.hpp compiles CLEAN for sm_89 (walker_batch.o, 42KB). No JIT. (Compiling ≠ instantiable: std::vector/json bodies remain host-only — the header-compile is a toolchain proof, not the port.)
3. THE ROUTE: translate walker_numba_split.py (the lane's finished flattened kernels — plan/integ/post SoA) to CUDA C++ via numba2cu.py (indent-aware v2.2): mm() translates PERFECTLY (compile-clean). The route avoids BOTH walls: no JIT ceiling (nvcc) and no re-flattening (the numba kernels are already array-C).

## THE REMAINING DEFECT (exactly one class)
Brace-balance at function tails in numba2cu.py's indent->brace emission: consecutive dedent closes (k-loop then j-loop) emit only ONE `}` in some sequences (the prev_indent arithmetic around consecutive closes + the is_chain exemption). Fix the close-emission (likely: pop closes until indent matched, not -4 steps), regenerate, recompile walker_cu_test.cu, iterate error classes down. After kernels compile: fix scalar args in signatures (phi_l0 etc. double not double*), then the host env (ctypes extern-C wrapper: alloc SoA, walker_model.py spec -> H2D, launch plan/integ/post per tick, status back), then the FIRST TICK, then bars_fullport.py's frozen bars.

## STATE
Branch agent/typeb-gpu-fullport2-20260922 (this commit). Files: numba2cu.py (the translator), walker_kernels.cuh (5900 lines generated, ~114 errors all brace-class), walker_cu_test.cu (compile harness), walker_device.hpp + generator (proof 2), engine_inc/ (headers), the lane's complete numba stack (fallback), lead_takeover2.py (the opt=False numba attempt — pending result).

## V3.1 SESSION ADDENDUM (lead, 2026-09-22 morning)
State: v3 clean rewrite (indent STACK — braces now correct; mm compiles balanced) + constants-extraction concept + arg-type heuristic. 101 errors remain, ALL normal C++ typing (zero structural). THE FOUR REMAINING CLASSES, in size order:
1. (66x) INT-INDEX INFERENCE: plain assigns default to double; ints used as array indices (h = k - 2 etc.) — improve classify(): int vars propagate (track declared int names; an expr of int literals/int vars/+-*/ on those → int).
2. (15x) "expected a" — inspect per-site; likely slice expressions mdl[OF:OF+8] (Python views) — translate `X = arr[a:b]` to a local array + copy loop; uses of X[i] then work. NOTE: constants extraction DID NOT EMIT (walker_numba.py defines OF_/OI_ etc. — check its actual line format; regex may need adjusting) — the 300-series undefined-identifier errors depend on it.
3. (2x) `t` undefined — a first-use inference miss (find the site ~line 201).
4. y/z tuple residuals (~line 35 in rot_axis: `x, y, z = axis[0], axis[1], axis[2]` — the tuple handler exists in v3 but missed this site — likely multi-space after commas defeating split).
Iteration protocol: python numba2cu.py && nvcc -c walker_cu_test.cu (the verbatim invocation) | count errors; fix the top class; repeat. Est. 3-6 more iterations to zero. THEN: scalar-arg hand-fix pass → ctypes host env (reset/set_command/step/status over the SoA arrays; walker_model.py builds the spec on host, cudaMemcpy H2D) → FIRST TICK at E=2 → bars_fullport.py.
