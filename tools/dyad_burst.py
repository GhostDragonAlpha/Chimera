"""dyad_burst.py — MULTI-FRAME MOVEMENT READ: N frames, ONE request, one report.

Born from the operator's law (2026-09-06): the eye's context is 30,208 tokens
(LM Studio loaded_context_length), so pictures per request are BUDGETED, and
movement detection needs several frames in ONE message — the eye can only
compare poses it sees together.

Measured token law (probe .tmp/dyad_capacity.py, 2026-09-06):
  text+1 image = 3668 tok, each extra 2K compact PNG = +3602 tok.
The budget check refuses a burst that would fill the context before the eye
can answer. senses.watch() enforces the same law independently.

The frame axis is the STRIDE CLOCK (the pose axis): the stride player is
paused, scrubbed to N phases evenly spaced across one full L/R cycle
(220 samples = 3.667 s at dt=1/60), each phase settled, grabbed, re-encoded,
then all N sent in ORDER as one message. The operator's playing state and
stride time are restored afterwards — a scan is a loan, not a seizure.
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, "ChimeraEngine")
import dyad_scan          # grab / compact / quiesce / req_json / SAVED
import senses             # watch() carries the same 30k law


def stride_period() -> float:
    """One full L/R cycle in seconds, from the player's own numbers."""
    s = dyad_scan.req_json("GET", "/stride", timeout=8)
    if not s.get("active"):
        raise SystemExit("no stride stream loaded — POST /stride_bin first")
    loop0, n, dt = s.get("loop0", 110), s.get("n", 331), s.get("dt", 1 / 60)
    return (n - loop0) * dt


def stride_loop_start() -> float:
    """Wall-time where the PERIODIC walk begins (the startup/prep segment
    plays once before it). Scrubbing phases must base here: t < loop start is
    the prep pose, and a burst that samples it reads startup frames as if
    they were walk phases (the 2026-09-06 co-phase misread)."""
    s = dyad_scan.req_json("GET", "/stride", timeout=8)
    return s.get("loop0", 110) * s.get("dt", 1 / 60)


def run(n_frames: int, prompt: str, run_dir: Path) -> dict:
    period = stride_period()
    cap = senses.capacity_report(n_frames)
    print(f"stride period: {period:.3f}s   frames: {n_frames}   "
          f"input ~{cap['input_tokens_est']} tok, "
          f"left for answer ~{cap['left_for_output']} tok "
          f"({'FITS' if cap['fits'] else 'TOO FULL'})", flush=True)
    if not cap["fits"]:
        raise SystemExit(
            f"REFUSED: {n_frames} frames leaves {cap['left_for_output']} tokens "
            f"for reasoning+answer. Practical max: {senses.max_images()} frames.")

    frames_dir = run_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # THE LOAN: freeze the stride, remember everything, restore at the end.
    st = dyad_scan.req_json("GET", "/stride", timeout=8)
    t0_stride = float(st.get("t", 0.0))
    was_playing = bool(st.get("playing"))
    dyad_scan.req_json("POST", "/stride", {"playing": False}, timeout=8)

    report = {"run_id": run_dir.name,
              "started": datetime.now().isoformat(timespec="seconds"),
              "kind": "stride-burst", "n_frames": n_frames,
              "stride_period_s": round(period, 4),
              "loop_start_s": round(stride_loop_start(), 4),
              "prompt": prompt, "budget": cap, "frames": [], "report": None}

    try:
        paths = []
        loop_start = stride_loop_start()
        for i in range(n_frames):
            # phase i of the PERIODIC cycle: base at the loop start, or the
            # first frames capture the one-shot startup segment instead.
            t_i = loop_start + i * period / n_frames
            dyad_scan.req_json("POST", "/stride",
                               {"t": t_i, "playing": False}, timeout=8)
            time.sleep(0.6)                      # the glass settles
            raw = frames_dir / f"burst_{i:02d}.png"
            raw.write_bytes(dyad_scan.grab("glass"))
            small = frames_dir / f"burst_{i:02d}_compact.png"
            csize = dyad_scan.compact(raw, small)
            raw.unlink(missing_ok=True)
            paths.append(str(small))
            report["frames"].append({"index": i, "t": round(t_i, 4),
                                     "compact_png": str(small),
                                     "compact_bytes": csize})
            print(f"  frame {i:02d}: stride t={t_i:.3f}s  compact="
                  f"{csize/1e3:.0f}KB", flush=True)

        t_read = time.time()
        text = senses.watch(paths, prompt)
        dt_read = time.time() - t_read
        finish = senses.last_finish_reason()
        report["report"] = text
        report["read_seconds"] = round(dt_read, 1)
        report["finish_reason"] = finish
        print(f"  eye read: {dt_read:.1f}s  {len(text or '')} chars  "
              f"finish={finish}", flush=True)
    finally:
        # HAND BACK the operator's stride exactly as found.
        try:
            dyad_scan.req_json("POST", "/stride",
                               {"t": t0_stride % period, "playing": was_playing},
                               timeout=8)
        except Exception:
            pass

    (run_dir / "report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    md = ["# dyad burst — " + run_dir.name,
          f"- frames: {n_frames} across one stride ({period:.3f}s)",
          f"- input budget: ~{cap['input_tokens_est']} tok / 30208 loaded",
          f"- eye read: {report.get('read_seconds')}s  "
          f"finish={report.get('finish_reason')}", "",
          (text or "(EMPTY — the eye burned the budget on reasoning)") + "\n",
          "## frames", ""]
    for f in report["frames"]:
        md.append(f"- [{f['index']}] stride t={f['t']}s  "
                  f"({f['compact_bytes']/1e3:.0f} KB)")
    (run_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    return report


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(
        description="N stride phases, ONE eye request — the movement read")
    ap.add_argument("--frames", type=int, default=4,
                    help=f"frames across one stride (budget max: "
                         f"{senses.max_images()})")
    ap.add_argument("--prompt-file", default=None)
    a = ap.parse_args()
    prompt = (Path(a.prompt_file).read_text(encoding="utf-8").strip()
              if a.prompt_file else
              "These N images are frames of a creature's walk, IN ORDER across "
              "one full stride cycle. Describe the movement: which limbs move, "
              "in which direction, and whether the sequence reads as walking. "
              "Name anything that does not move but should.")
    run_dir = dyad_scan.SAVED / datetime.now().strftime("%Y-%m-%d_%H%M%S_burst")
    run_dir.mkdir(parents=True, exist_ok=True)
    dyad_scan.req_json("GET", "/studio", timeout=6)   # engine must be alive
    ok, served, why = senses.can_see(timeout=120)
    print(f"eye: {served or '?'}  takes images: {ok}" +
          ("" if ok else f" -> {why}"), flush=True)
    if not ok:
        raise SystemExit("the eye is blind: " + str(why))
    run(a.frames, prompt, run_dir)
    print(f"done -> {run_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
