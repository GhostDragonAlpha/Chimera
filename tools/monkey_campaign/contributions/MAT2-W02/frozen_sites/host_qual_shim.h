/* host_qual_shim.h -- ONT-W02 compile-time qualifier neutralizer.
 *
 * The pinned ucrt_math.c (git blob efd87d67, archive ref
 * refs/chimera-archive-source/20260925/agent/typeb-gpu-finish-20260922) carries
 * nvcc address-space qualifiers (__host__/__device__) on its inline helpers so
 * the same translation unit dual-compiles for the CUDA device gate. For a
 * plain-cl HOST build those markers must expand to nothing. This mirrors the
 * lane's own host_shim/cuda_runtime.h precedent (closeout-8: "host_shim/
 * cuda_runtime.h neutralizes nvcc qualifiers for the plain-cl drill builds").
 *
 * This file is forced-include (/FI) only; no pinned source byte is modified.
 * Compile recipe (frozen in PREREGISTRATION.md before the run):
 *   cl /nologo /O2 /fp:precise /EHsc /FI host_qual_shim.h ^
 *      ucrt_math.c parity_gate_host.cxx /Fe:parity_gate.exe
 */
#if !defined(UCRT_MATH_DEVICE)
#ifndef ONT_W02_HOST_QUAL_SHIM
#define ONT_W02_HOST_QUAL_SHIM
#define __host__
#define __device__
#endif
#endif
