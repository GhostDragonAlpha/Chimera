#!/usr/bin/env python3
"""MAT2-W10 DEV DIAGNOSTIC (not evidence): isolate the FFV1 bgr0
encode/decode identity roundtrip on synthetic frames through the exact
run_capture pipeline. Runner-gated like every other command."""
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

W, H = 960, 540


def fb(colour):
    buf = bytearray(W * H * 4)
    i = 0
    for y in range(H):
        row = colour[y]
        for x in range(W):
            r, g, b = row[x]
            buf[i], buf[i + 1], buf[i + 2], buf[i + 3] = b, g, r, 0
            i += 4
    return bytes(buf)


def main():
    frames = []
    for k in range(3):
        frames.append([[(k * 40 % 256, (x // 7) % 256, (y // 5) % 256)
                        for x in range(W)] for y in range(H)])
    enc = list(map(fb, frames))
    tmp = Path(tempfile.mkdtemp(prefix="w10codec_"))
    vid = tmp / "probe.mkv"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", "%dx%d" % (W, H),
           "-r", "1", "-i", "-",
           "-c:v", "ffv1", "-pix_fmt", "bgr0", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", str(vid)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for e in enc:
        p.stdin.write(e)
    p.stdin.close()
    print("encode rc:", p.wait())
    for idx, want in enumerate(enc):
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(vid),
             "-vf", "select=eq(n\\,%d)" % idx, "-vsync", "0", "-frames:v",
             "1", "-f", "rawvideo", "-pix_fmt", "bgr0", "-"],
            capture_output=True)
        got = out.stdout
        print("frame", idx, "want", hashlib.sha256(want).hexdigest()[:16],
              "got", hashlib.sha256(got).hexdigest()[:16],
              "len", len(got), "match", got == want)
        # also probe without the select filter (first frame decode)
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(vid),
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr0", "-"],
        capture_output=True)
    print("plain-first:", out.stdout == enc[0], len(out.stdout))
    # pix_fmt info
    pr = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=pix_fmt,codec_name", "-of", "csv", str(vid)],
        capture_output=True, text=True)
    print("stream:", pr.stdout.strip())
    return 0


if __name__ == "__main__":
    sys.exit(main())
