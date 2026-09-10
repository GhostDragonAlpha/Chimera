# doclint-header-path-01 preregistration

**STATEMENT:** The documentation linter recognizes supported file extensions
with a filename boundary, so an existing `ChimeraEngine/engine/http_server.hpp`
reference is checked against its full path while a missing `.h` reference still
fails.

**PREDICTION:** Temporary documents referencing existing `.hpp`, `.cpp`, `.py`,
`.md`, and links will pass; missing `.hpp`, `.h`, and `.cpp` references and
prefix lookalikes will fail with their complete candidate path.

**FALSIFIER:** An existing `.hpp` reference is reported broken, a missing
supported header is silently ignored, or a prefix lookalike is accepted as the
referenced file.

The test harness uses temporary paths and preserves each stdout/JSON result in
the append-only evidence record. No allowlist or shared configuration is
changed.
