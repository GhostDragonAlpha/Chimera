{
  "membrane.comp": "80a0981dd1f245aa551035c9336df521d363e33ea8a17137fc5cf60307d7c2ac",
  "probe.cpp": "2501542b7d70728b1aee82e85c79b62024de1dbf56b56dae46bc3f35ea2e4108",
  "probe_core.hpp": "b136b9bd7957448d8bca1a45cf8ea56cf8ef9714bf9d948c5e5dc90773ec04d3",
  "relax.cpp": "1923d89f69dcda93794a02911e980ef8bc869ab9e9ee9f2dcf2a91f0398d23ef",
  "CMakeLists.txt": "61362c250bba3591f899b616678a4d09c1cf093a1d2ecd5ffb4cbac293173770",
  "candidate": "C",
  "description": "relax.cpp currently runs:\n  1. kernel: x+ = x + alpha*p  (trial update)\n  2. host: memcpy trial positions back\n  3. kernel: full eval of trial state (3 stages)\n\nCandidate C adds a single compute stage that writes the trial positions\nand immediately begins face evaluation in the same dispatch, overlapping\nthe PCIe write with the first wave of face work. Requires persistent\nmapped positions buffer (Candidate B).\n\nExpected benefit: hide host->device transfer latency behind GPU compute.\nFor large meshes where face evaluation dominates, the overlap is small;\nfor small meshes where transfer is a larger fraction, the gain is larger.\n\nFALSIFIER: no correctness change; wall-clock accepted-step time does not\ndecrease for large face counts (where compute dominates transfer)."
}