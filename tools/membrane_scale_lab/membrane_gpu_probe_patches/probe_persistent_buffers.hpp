{
  "membrane.comp": "80a0981dd1f245aa551035c9336df521d363e33ea8a17137fc5cf60307d7c2ac",
  "probe.cpp": "2501542b7d70728b1aee82e85c79b62024de1dbf56b56dae46bc3f35ea2e4108",
  "probe_core.hpp": "b136b9bd7957448d8bca1a45cf8ea56cf8ef9714bf9d948c5e5dc90773ec04d3",
  "relax.cpp": "1923d89f69dcda93794a02911e980ef8bc869ab9e9ee9f2dcf2a91f0398d23ef",
  "CMakeLists.txt": "61362c250bba3591f899b616678a4d09c1cf093a1d2ecd5ffb4cbac293173770",
  "candidate": "B",
  "description": "In the original probe_core.hpp, run_case() allocates nine device buffers,\ncopies input, builds a descriptor set, records commands, submits, waits,\nread back, then frees ALL buffers. For a relaxation loop of K iterations,\nthis repeats K times.\n\nCandidate B allocates the buffers ONCE outside the loop, maps them once,\nand reuses the same descriptor set + command buffer across iterations.\nOnly the positions/gamma inputs change between iterations.\n\nExpected benefit: amortize allocation + descriptor-set build + command-record\ncost over K dispatches. For K=12 (B2) the setup overhead drops by ~11x;\nfor K=200 it drops by ~199x.\n\nFALSIFIER: any correctness regression vs the original single-shot probe,\nmeasured on the frozen B2 and fan12 fixtures."
}