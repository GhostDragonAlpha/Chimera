"""dyad_scan.py — THE DYAD SCAN (docs/THE_ENGINE_STUDIO.md §G2).

The eye reads the GLASS. One image per call. Its report is the work list.

    python tools/dyad_scan.py --shots 8 --reads 3
    python tools/dyad_scan.py --shots 4 --crop 1790,60,740,420     # inspect one panel
    python tools/dyad_scan.py --prompt-file my_question.txt --shots 2
    python tools/dyad_scan.py --resume Saved/dyad/<run_id>

TERMS OF ENGAGEMENT (operator, 2026-08-31) — read this before adding anything:

    THERE IS NO SCORE. No alignment, no threshold, no pass/fail, no points. The
    eye is not a gate to clear; it is a second mind looking at the same window.
    The craft is entirely in what you ASK: be descriptive about what you are
    looking for, and it will tell you its opinion. Living in this world is
    subjective and so is this process.

    So: N reads per shot are NOT a vote and are never averaged. They are all
    reported verbatim. Where the eye disagrees with itself across reads of the
    SAME image, that disagreement IS the finding — it means the thing it is
    arguing about is genuinely ambiguous in the picture, which is precisely the
    defect worth knowing about.

WHAT IT RECORDS, per shot:
  - the glass PNG (raw, at the monitor's resolution) and its compact twin
  - the HTTP TWINS (/studio, /studio_chrome, /scene, /show): the numbers the eye
    cannot see. fps, frame time, the stage line, what is loaded. The eye reads
    pixels; the twins read state. Two systems, two kinds of output.
  - N reports, verbatim, each timestamped

WHY ONE IMAGE PER CALL (senses.MAX_IMAGES_PER_CALL): the resident eye is
qwen3.8 iq4_xs, chosen to fit the GPU, and it pays with a small context. A batch
does not fit and fails by truncation — a confident verdict over the first few
frames. N shots is N calls. That is the cost of the eye being fast.

WHY THE PNG IS RE-ENCODED: the engine's png::encode_rgba writes 14.75 MB for one
2K frame (~19 MB as base64 in the request). Losslessly re-encoded through PIL the
same frame is 37 KB — 396x smaller, pixels bit-identical. Measured 2026-08-31.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path("E:/PythonChimera")
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

import senses          # the dyad's perception — imported here so the capability
                       # probe can run BEFORE a frame is ever rendered

SAVED = ROOT / "Saved" / "dyad"
URL = "http://localhost:8090"

# The default question. Descriptive, not leading: it says what we are looking for
# and asks for an opinion. It does not say what the answer should be — an eye told
# the answer confirms instead of observing.
DEFAULT_PROMPT = """I am developing a 3D engine and this is a real screenshot of its application window, at the full resolution of the monitor it runs on. I want your honest opinion on what you are looking at.

Describe what you see: does the layout, framing, and positioning look wrong or right? Look at it like an artist. Could it be framed better? Where does the image itself lose you? Is it confusing?

Be specific about defects. Is any text too small to read, cut off, overlapping, or colliding with something else? Are the panels and windows legible, and are they proportioned sensibly against the size of the window? Is anything cramped, off-balance, or adrift in empty space? Is the 3D viewport visible, and if it is empty does the window still read as a working application?

Tell me what you actually see and what you think is wrong with it. I am not looking for praise, I am looking for defects."""


# ── engine talk ──────────────────────────────────────────────────────────────

def req_json(method, path, payload=None, timeout=15):
    data = json.dumps(payload).encode() if payload is not None else None
    r = urllib.request.Request(URL + path, data=data, method=method,
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def grab(channel="glass", timeout=40, tries=4) -> bytes:
    """GET a PNG channel. Validates the magic bytes and RETRIES on a short read.

    A capture that loses the race hands back `{"ok":false,"error":"... timeout"}`
    with content-type application/json. Decoding that as an image (or feeding it
    to the eye) is how an instrument reports on something that never happened —
    so the transport refuses to return anything that is not a PNG.
    """
    last = None
    for k in range(tries):
        with urllib.request.urlopen(f"{URL}/{channel}", timeout=timeout) as r:
            b = r.read()
        if b[:8] == b"\x89PNG\r\n\x1a\n":
            return b
        last = b[:160].decode("utf-8", "replace")
        time.sleep(0.6)
    raise RuntimeError(f"/{channel} returned no PNG after {tries} tries: {last}")


def twins() -> dict:
    """The numbers the eye cannot see. Recorded beside every shot so a report
    about the pixels always has the state that produced them next to it.

    CAVEAT, measured 2026-08-31: THE SCAN PERTURBS THE FRAME RATE IT RECORDS.
    Every capture calls vkQueueWaitIdle, so while the scan is grabbing the engine
    reads ~9.8 fps / 92 ms; at rest it is 56 fps / 8.95 ms. A per-shot `fps` is
    therefore fps-UNDER-CAPTURE-LOAD, and believing it would be an instrument
    convicting the engine for the instrument's own stall. Clean samples are taken
    before and after the run (see clean_fps) and THAT is the number to quote.
    """
    out = {}
    for key, path in (("studio", "/studio"), ("chrome", "/studio_chrome"),
                      ("scene", "/scene"), ("show", "/show")):
        try:
            out[key] = req_json("GET", path, timeout=8)
        except Exception as e:
            out[key] = {"error": str(e)[:120]}
    out["_fps_is_under_capture_load"] = True
    return out


def clean_fps(samples: int = 3) -> dict:
    """The engine's real frame rate, taken with NO capture in flight."""
    got = []
    for _ in range(samples):
        try:
            ch = req_json("GET", "/studio_chrome", timeout=8)
            got.append({"fps": ch.get("fps"), "ft_avg": ch.get("ft_avg"),
                        "ft_max": ch.get("ft_max")})
        except Exception as e:
            got.append({"error": str(e)[:100]})
        time.sleep(1.2)
    return {"samples": got, "note": "no capture in flight; this is the quotable number"}


def set_camera(radius, theta, phi) -> None:
    req_json("POST", "/camera", {"cam_radius": radius, "cam_theta": theta, "cam_phi": phi})


# ── pixels ───────────────────────────────────────────────────────────────────

def compact(src: Path, dst: Path) -> int:
    """The engine's PNG is ~uncompressed; re-encode losslessly before it goes
    anywhere near the eye. Returns the compacted size in bytes."""
    from PIL import Image
    im = Image.open(src).convert("RGB")
    if CROP:
        x, y, w, h = CROP
        im = im.crop((x, y, x + w, y + h))
    im.save(dst, optimize=True)
    return dst.stat().st_size


def diff_px(a: Path, b: Path) -> int:
    import numpy as np
    from PIL import Image
    x = np.asarray(Image.open(a).convert("RGB")).astype(np.int16)
    y = np.asarray(Image.open(b).convert("RGB")).astype(np.int16)
    if x.shape != y.shape:
        return -1
    return int((np.abs(x - y).max(axis=2) > 0).sum())


def quiesce(tag: str, timeout=12.0) -> bool:
    """Wait for the glass to settle after a state change.

    NOT byte-identity — the glass carries the status bar's LIVE fps readout, so
    it is never twice identical. The stable quantity is the STRUCTURE: how many
    pixels the glass adds over the pixel-clean frame. (Learned the hard way:
    defining settling as equality made this instrument report "never settled" on
    a channel measuring 0.0000% spread.)
    """
    t0 = time.time()
    prev = None
    while time.time() - t0 < timeout:
        gp = OUT / f"{tag}_q_glass.png"
        fp = OUT / f"{tag}_q_frame.png"
        gp.write_bytes(grab("glass"))
        fp.write_bytes(grab("frame"))
        cur = diff_px(gp, fp)
        if prev is not None and abs(cur - prev) <= max(1, int(0.001 * max(cur, 1))):
            return True
        prev = cur
        time.sleep(0.3)
    return False


CROP: tuple | None = None
OUT: Path = SAVED
READ_TIMEOUT = 1800
POSES = False          # --poses: sweep the SHOW CLOCK (the pose axis)
ORBIT = False          # --orbit: sweep the camera (opt-in; Guide S5 says leave it)
PERIOD = 12.0          # the show period to sweep across, seconds          # seconds per vision call; --read-timeout overrides
                             # (a 2560x1440 frame on the Q4_K_XL quant is slow)


# ── the scan ─────────────────────────────────────────────────────────────────

def run(run_dir: Path, shots: int, reads: int, prompt: str, radius: float,
        phi: float, keep_raw: bool) -> dict:
    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {
        "run_id": run_dir.name,
        "started": datetime.now().isoformat(timespec="seconds"),
        "engine": req_json("GET", "/studio", timeout=8),
        "prompt": prompt,
        "crop": list(CROP) if CROP else None,
        "reads_per_shot": reads,
        "shots": [],
    }
    if "fps_before" not in report:
        report["fps_before"] = clean_fps()
        print("  fps at rest (before):",
              [s.get("fps") for s in report["fps_before"]["samples"]])
    done = {s["index"] for s in report["shots"]}

    for i in range(shots):
        if i in done:
            print(f"  shot {i:02d}: already done, skipping (resume)")
            continue
        # WHAT MOVES BETWEEN SHOTS — three modes, and the default is the one the
        # Triangle Guide allows. §5: "Never set the camera from a driver or
        # kernel. The operator orbits while it moves; that is the point." So the
        # scan leaves the operator's framing ALONE unless --orbit is asked for.
        #
        # --poses sweeps the SHOW CLOCK instead, which is the right axis for an
        # articulating body: the pose is the thing under test, and the camera is
        # the operator's. (Pausing first, then scrubbing to exact instants — the
        # show clock is a parameter, not a wall clock.)
        theta = None
        show_t = None
        if POSES:
            show_t = (PERIOD * i / max(1, shots)) if shots > 1 else 0.0
            req_json("POST", "/show", {"playing": False})
            req_json("POST", "/show", {"time": show_t, "step": 0})
        elif ORBIT:
            theta = 2.0 * 3.14159265358979 * i / max(1, shots)
            set_camera(radius, theta, phi)
        quiesce(f"s{i:02d}")

        raw = frames_dir / f"shot_{i:02d}.png"
        raw.write_bytes(grab("glass"))
        small = frames_dir / f"shot_{i:02d}_compact.png"
        csize = compact(raw, small)

        shot = {"index": i, "camera": "operator's (untouched)" if not ORBIT else [radius, theta, phi],
                "theta": round(theta, 5) if theta is not None else None,
                "show_t": round(show_t, 4) if show_t is not None else None,
                "raw_png": str(raw), "compact_png": str(small),
                "compact_bytes": csize, "raw_bytes": raw.stat().st_size,
                "twins": twins(), "reads": []}
        what = f"show_t={show_t:.2f}s" if show_t is not None else (
               f"theta={theta:.2f}" if theta is not None else "camera untouched")
        print(f"  shot {i:02d}: {what} raw={shot['raw_bytes']/1e6:.2f}MB "
              f"compact={csize/1e3:.0f}KB  fps={shot['twins'].get('chrome',{}).get('fps')}")

        for r in range(reads):
            t0 = time.time()
            try:
                import senses
                # A 2K frame on the big quant is SLOW: 600s was not enough. A
                # timeout is a transport failure, not a verdict, so it is retried
                # once before the read is recorded as nothing.
                text = senses.see(str(small), prompt, timeout=READ_TIMEOUT)
                if text is None:
                    print(f"      read {r}: timed out — retrying once", flush=True)
                    text = senses.see(str(small), prompt, timeout=READ_TIMEOUT)
            except Exception as e:
                text = None
                print(f"      read {r}: FAILED {type(e).__name__}: {str(e)[:100]}")
            # A report the eye was not allowed to finish is not a report. Record
            # it as truncated rather than filing a sentence that stops mid-word
            # as though that were the whole finding.
            finish = senses.last_finish_reason()
            trunc = (finish == "length")
            if trunc:
                print(f"      read {r}: TRUNCATED by the token cap "
                      f"({senses.MAX_TOKENS}) — raise --max-tokens or shorten the ask",
                      flush=True)
            shot["reads"].append({
                "read": r, "seconds": round(time.time() - t0, 1), "report": text,
                "finish_reason": finish, "truncated": trunc})
            if text:
                print(f"      read {r}: {time.time()-t0:.1f}s  {len(text)} chars")
            # flush after EVERY read: a 6-minute vision call must never be lost
            report["shots"] = [s for s in report["shots"] if s["index"] != i] + [shot]
            report["shots"].sort(key=lambda s: s["index"])
            report_path.write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                   encoding="utf-8")

        if not keep_raw:
            raw.unlink(missing_ok=True)
            shot["raw_png"] = None

    report["fps_after"] = clean_fps()
    print("  fps at rest (after): ", [s.get("fps") for s in report["fps_after"]["samples"]])
    write_markdown(run_dir, report)
    return report


def write_markdown(run_dir: Path, report: dict) -> None:
    """A report a human reads. The JSON is the record; this is the reading."""
    lines = [f"# dyad scan — {report['run_id']}", "",
             f"- started: {report.get('started')}",
             f"- reads per shot: {report['reads_per_shot']} (NOT a vote — all reported)",
             f"- crop: {report['crop'] or 'none (whole window)'}",
             f"- engine: {report['engine'].get('w')}x{report['engine'].get('h')}", ""]
    for s in report["shots"]:
        ch = s["twins"].get("chrome", {})
        # which axis this shot moved along — None on the axes it did not touch,
        # so format the label from whichever one is actually set
        if s.get("show_t") is not None:
            what = f"show t = {s['show_t']:.2f}s"
        elif s.get("theta") is not None:
            what = f"theta {s['theta']:.2f}"
        else:
            what = "camera untouched (Guide §5)"
        lines.append(f"## shot {s['index']:02d} — {what}")
        lines.append(f"`fps {ch.get('fps')} · ft avg {ch.get('ft_avg')} ms · "
                     f"stage: {ch.get('stage', '')}`")
        lines.append("")
        for rd in s["reads"]:
            lines.append(f"**read {rd['read']}** ({rd['seconds']}s)")
            lines.append("")
            lines.append(rd["report"] or "_(the eye returned nothing)_")
            lines.append("")
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global CROP, OUT, READ_TIMEOUT, POSES, ORBIT, PERIOD
    ap = argparse.ArgumentParser(description="the dyad reads the glass, one image per call")
    ap.add_argument("--shots", type=int, default=8, help="camera stops around the subject")
    ap.add_argument("--reads", type=int, default=3, help="reads per shot (NOT a vote)")
    ap.add_argument("--radius", type=float, default=12.0)
    ap.add_argument("--phi", type=float, default=0.30)
    ap.add_argument("--crop", default=None, help="x,y,w,h — inspect one region closely")
    ap.add_argument("--prompt-file", default=None, help="a file holding the question")
    ap.add_argument("--poses", type=int, default=0,
                    help="sweep the SHOW CLOCK to N instants (the pose axis)")
    ap.add_argument("--orbit", action="store_true",
                    help="sweep the camera around the subject (opt-in: Guide S5)")
    ap.add_argument("--period", type=float, default=12.0,
                    help="show-clock period to sweep across, seconds")
    ap.add_argument("--read-timeout", type=int, default=READ_TIMEOUT,
                    help="seconds allowed per vision call (2K on the big quant is slow)")
    ap.add_argument("--keep-raw", action="store_true", help="keep the 14MB engine PNGs")
    ap.add_argument("--resume", default=None, help="run dir to continue")
    a = ap.parse_args()

    READ_TIMEOUT = a.read_timeout
    POSES, ORBIT, PERIOD = a.poses, a.orbit, a.period
    if a.crop:
        CROP = tuple(int(v) for v in a.crop.split(","))
        if len(CROP) != 4:
            raise SystemExit("--crop takes x,y,w,h")

    prompt = DEFAULT_PROMPT
    if a.prompt_file:
        prompt = Path(a.prompt_file).read_text(encoding="utf-8").strip()

    if a.resume:
        run_dir = Path(a.resume)
    else:
        run_dir = SAVED / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    OUT = run_dir / "frames"
    OUT.mkdir(parents=True, exist_ok=True)

    try:
        st = req_json("GET", "/studio", timeout=6)
    except Exception as e:
        raise SystemExit(f"engine is down on :8090 ({e})")

    # THE EYE COMES FIRST. A scan whose eye cannot see costs a full render pass
    # and a multi-minute vision call before it fails, so the capability probe runs
    # before anything is built. The served model is reported, not assumed: the
    # gateway adopts whatever is resident, so the decreed eye and the serving eye
    # can silently differ — and two reports are only comparable from one eye.
    print("checking the eye...", flush=True)
    ok, served, why = senses.can_see(timeout=120)
    print(f"  decreed eye : {senses.SENSES_MODEL}")
    print(f"  serving     : {served or '(unknown)'}")
    print(f"  takes images: {ok}" + ("" if ok else f"  -> {why}"))
    if not ok:
        raise SystemExit(
            f"THE EYE IS BLIND: {why}\n"
            f"  A dyad whose eye cannot see is not a dyad. Load a vision-capable model\n"
            f"  in LM Studio (the decreed eye is {senses.SENSES_MODEL}).")
    if served and served != senses.SENSES_MODEL:
        print(f"  !! WARNING: the serving model is NOT the decreed eye "
              f"({served} != {senses.SENSES_MODEL}).\n"
              f"     The gateway adopts whatever is resident, so this run's reports\n"
              f"     are NOT comparable to the earlier ones. Recorded in report.json.")

    print(f"dyad scan -> {run_dir}")
    print(f"engine {st['w']}x{st['h']}  overlay={st['on']}  "
          f"shots={a.shots} reads={a.reads} crop={CROP or 'none'}")
    rep = run(run_dir, a.shots, a.reads, prompt, a.radius, a.phi, a.keep_raw)
    print(f"\ndone: {len(rep['shots'])} shots, "
          f"{sum(len(s['reads']) for s in rep['shots'])} reads")
    print(f"  {run_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
