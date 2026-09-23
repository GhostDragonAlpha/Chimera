#pragma once
#include <cmath>
#include <cstring>
/* closeout-8: the generated kernels now include ucrt_math.c, whose helpers
   carry nvcc's __host__/__device__ qualifiers. The plain-cl host drill builds
   (substep_probe, host_loop) see this shim instead of the real CUDA header,
   so neutralize the qualifiers here (nvcc builds never see this file).
   Trailer: Agent: GLM 5.3 */
#ifndef __CUDACC__
#define __host__
#define __device__
#endif
