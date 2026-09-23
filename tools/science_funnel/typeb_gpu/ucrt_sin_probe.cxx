// ucrt_isa_check.cxx -- which UCRT libm path is live: __isa_available and
// __use_fma3_lib decide whether sin/cos run the SSE2 or the FMA3 variant.
// Trailer Agent: GLM 5.3.
#include <cstdio>
#include <cmath>
extern "C" extern const int __isa_available;
extern "C" extern int __use_fma3_lib;
int main() {
    // __ISA_AVAILABLE_X86=0 SSE2=1 SSE42=2 AVX=3 AVX2=4 AVX512=5 ARM64=6
    printf("isa_available=%d use_fma3_lib=%d\n", __isa_available, __use_fma3_lib);
    volatile double a = 0.7;
    printf("sin(0.7)=%.17g\n", sin(a));
    return 0;
}
