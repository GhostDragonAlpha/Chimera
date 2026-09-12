# Portable capture-code instrument

This builds the **existing engine PNG encoder** as a native C++17 test executable,
without Windows, Vulkan, a display or third-party Python packages. It is a CPU byte
transport test, not a renderer, headless engine, physics simulation or DYAD verdict.
The engine and its production CMake configuration are unchanged.

From the repository root, with a GCC/Clang-compatible compiler or MSVC available:

```sh
python tools/platform_probe/check.py
```

Select a compiler executable explicitly if needed:

```sh
python tools/platform_probe/check.py --compiler g++
```

Use an MSVC developer shell for `--compiler cl`. That route is implemented but has
not been executed in the Linux development workspace. Missing tools produce FAIL,
never an invented Windows or GPU result.

An optional standalone CMake target is provided. It does not invoke the engine's
Windows-specific CMakeLists.txt. Keep output outside the protected engine build tree:

```sh
cmake -S tools/platform_probe -B .tmp/platform-probe-cmake
cmake --build .tmp/platform-probe-cmake --config Release
ctest --test-dir .tmp/platform-probe-cmake -C Release --output-on-failure
```

The CMake route requires Python3 and CMake 3.20+. It was not exercised where CMake
was unavailable. Direct C++ compilation and the supplied-executable check route are
separate recorded tests; neither certifies CMake configuration.

The runner creates a unique directory under `.tmp/platform_probe/` with compiler
output, fixture PNGs and `report.json`. Fixtures are synthetic pixel patterns, not
screenshots. The independent Python decoder verifies chunk CRCs, zlib checksums,
dimensions, filtering, channel/row order and every source byte. One fixture spans
multiple stored-deflate blocks. Negative controls alter CRC, phase and channel order.

Default mode reports 9 checks, including native compilation; a supplied executable
reports 8 checks and explicitly does not certify its source/build provenance. Both
record its binary hash and the checked-out header hash separately. Exit 0 means
all instrument checks passed; exit 1 means a check/tool/run failed. Runtime, visual
and human states are reported separately and never inferred from this result.

See `docs/FOUNDATION_P01_REPORT.md` for preregistration, results, OS dependency
inventory and the next Windows baseline gate.
