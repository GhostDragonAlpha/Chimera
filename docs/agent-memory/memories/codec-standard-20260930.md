---
name: codec-standard-20260930
description: 2026-09-30 measured capture-video codec standard for MAT2 cards — FFV1 -level 3 -g 1 mkv stays (only zero-drift codec), ADD -fflags +bitexact for sha-stable re-encodes; lossy codecs forbidden for evidence; adopted by addendum into M09/M10
metadata:
  node_type: memory
  type: project
  originSessionId: sess_1e40894c-78a5-4c13-b68b-d2141a225db1
---

Decided 2026-09-29/30 by the codec-benchmark lane (E:/ChimeraWork/monkey-coordination/codec-benchmark/CODEC_STANDARD.md + evidence/benchmark_results.json), adopted same day by Lieutenant addendum to the M09/M10 card workers.

**THE STANDARD (for M09+ captures; M08's sealed capture is never re-encoded):**
```
ffmpeg -y -loglevel error -framerate 1 -i <frames>/frame_%02d.png -c:v ffv1 -level 3 -g 1 -fflags +bitexact <out>.mkv
```

**Why (measured on M08's 9 frames, two encodes per config):**
- FFV1 is the ONLY zero-drift codec (decode delta 0). Every lossy 4:2:0 config (x264 crf18/23, x265 crf20, AV1 crf30) shifts >= 1 LSB on ~86-87% of pixels — pixel-gate corruption; yuv444p cuts magnitude 4x but still touches 85.5%.
- Plain FFV1 mkv re-encodes differ in exactly 44 bytes (muxer SegmentInfo DateUTC wall-clock; payload identical) — `-fflags +bitexact` pins the sha (measured stable; muxer-level flag suffices, `-flags:v +bitexact` is a no-op). mp4 mvhd timestamps are 0 in this build.
- Reviewer-accessible derivative (NON-evidence side file only): x264 crf18 yuv444p mp4 +faststart +bitexact. Size-pressure fallback vs P9 caps: same. x265/AV1 rejected (no advantage; AV1 worst drift max-221 + 18x encode time).
- Record the ffmpeg version line in capture receipts (bit-exact shas remain build-dependent via Lavf strings).

**DURABLE benchmark-methodology lessons:** (1) any NEW metric needs a second, independently-written computation before entering a decision doc — the first harness had an axis bug (`delta.max(axis=2)` collapses width not channels) reporting 22,680 px instead of ~86%; caught only by independent recount. (2) `cmp -l` lies after header-size shifts (~841K false diffs from an 82-byte shorter header) — run a size diff first and prove payload equivalence by DECODE-ROUNDTRIP, not byte-position compares. (3) Windows `subprocess(text=True)` crashes on ffmpeg's non-UTF-8 stderr — use `errors='replace'`.

Context: [[m08-status-and-goal-loaded-20260930]] (M08's capture = the incumbent that verified lossless); ffmpeg 8.1.1-full_build-www.gyan.dev on PATH (libx264/x265/aom/ffv1 all present).
