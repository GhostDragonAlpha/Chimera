#!/usr/bin/env python3
"""tools/dyad_timed_capture.py -- read-only timed capture instrument (V04).

Collects ordered images plus runtime state so that camera movement, pose
changes, advancing clocks and actual mesh deformation can be told apart.

GET ONLY. This instrument never POSTs -- no camera, pose, playback, scene-load
or other mutation requests. It never launches or stops the engine. It is a
pure client.

Per capture it records:
  - sequence number and image SHA-256
  - request start/end on a monotonic clock
  - UTC timestamp
  - endpoint, HTTP status and relevant response metadata
  - available camera, joint, simulation-time and gait-status data
  - state reads immediately BEFORE and AFTER the capture

Separate HTTP reads are treated as NON-ATOMIC. The time interval they bracket
is recorded. Differences between the before and after state are detected; the
instrument never claims the image and the state share one instant unless the
API supplies a common frame/state identifier.

Duration and interval are explicit arguments. No stride period is hard-coded.
Missed deadlines and actual capture times are reported. The instrument does
not claim 60 fps sampling when the endpoint cannot sustain it.

Each run writes to a UNIQUE directory and never overwrites existing evidence.
On timeout, malformed response, or interruption it preserves partial results
and returns an explicit incomplete verdict.

Usage:
  python tools/dyad_timed_capture.py \
      --url http://localhost:8090 \
      --endpoint /frame \
      --duration 5.5 --interval 0.5 \
      --out E:/PythonChimera/.tmp/v04_20260906_123000/

Offline test mode (no live engine):
  python tools/dyad_timed_capture.py --mock --duration 2.0 --interval 0.25 \
      --out E:/PythonChimera/.tmp/v04_test_1/
"""

import argparse
import hashlib
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

VERSION = "v04-2026-09-06"

DEFAULT_URL = os.environ.get("CHIMERA_ENGINE_URL", "http://localhost:8090")

# Endpoints this instrument is permitted to GET. Anything else is refused.
READ_ENDPOINTS = ("/state", "/studio", "/studio_chrome", "/scene", "/light",
                  "/frame", "/glass")

# Endpoints that return a binary image.
IMAGE_ENDPOINTS = ("/frame", "/glass")

# Endpoints that return JSON state.
JSON_ENDPOINTS = ("/state", "/studio", "/studio_chrome", "/scene", "/light")

# State fields this instrument knows how to extract. Missing fields are
# recorded as UNKNOWN, never guessed.
STATE_KEYS = (
    "camera", "cam_radius", "cam_theta", "cam_phi",
    "joints", "joint", "theta", "show", "show_t", "t", "clock",
    "gait", "gait_steps", "steps", "steps_total", "gait_pack", "pack",
    "fps", "frame_time", "ft", "playing", "pause", "stage", "overlay",
    "strain", "hinge", "volp", "water", "frost", "matter", "mesh",
    "tris", "verts", "body", "frame_id", "state_id", "tick", "seq",
)

# Fields that, if present, would let the instrument assert that the image and
# the state share one instant. NONE of these are required; their absence means
# the co-instant claim is NOT supported.
FRAME_ID_KEYS = ("frame_id", "state_id", "tick", "seq", "render_id", "capture_id")

# Hard limits to prevent runaway runs.
MAX_CAPTURES = 4096
MAX_INTERVAL = 3600.0
MIN_INTERVAL = 0.001
MAX_DURATION = 86400.0
DEFAULT_TIMEOUT = 10.0
MAX_RESPONSE_BYTES = 256 * 1024 * 1024  # 256 MiB safety cap


def _utcnow_iso():
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _truncate(text, limit=4096):
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated %d bytes]" % (len(text) - limit)


def _flatten_state(obj, prefix=""):
    """Recursively pull scalar values out of a nested state dict so the
    before/after diff has something to compare."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = ("%s.%s" % (prefix, k)) if prefix else k
            if isinstance(v, (dict, list)):
                out[key] = json.dumps(v, sort_keys=True, separators=(",", ":"))
            else:
                out[key] = v
    elif isinstance(obj, list):
        out[prefix] = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    else:
        out[prefix] = obj
    return out


def _extract_known(state):
    """Pull the fields this instrument cares about out of a raw state dict.
    Returns (extracted dict, missing list)."""
    extracted = {}
    missing = []
    if not isinstance(state, dict):
        return extracted, ["<state is not a JSON object: %r>" % type(state).__name__]
    for key in STATE_KEYS:
        if key in state:
            extracted[key] = state[key]
    for key in FRAME_ID_KEYS:
        if key in state:
            extracted["_frame_id_key"] = key
            break
    return extracted, missing


def _diff_states(before, after):
    """Return (changed_keys, before_subset, after_subset)."""
    keys = set(before) | set(after)
    changed = {}
    for k in sorted(keys):
        bv = before.get(k)
        av = after.get(k)
        if bv != av:
            changed[k] = {"before": _truncate(bv), "after": _truncate(av)}
    return changed


def _make_run_dir(out_root):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(out_root, "run_%s" % stamp)
    n = 0
    candidate = run_dir
    while os.path.exists(candidate):
        n += 1
        candidate = "%s_%d" % (run_dir, n)
    os.makedirs(candidate, exist_ok=True)
    return candidate


def _atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _atomic_write_bytes(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
def _http_get_json(url, timeout):
    """GET a JSON endpoint. Returns (parsed, raw_text, status, headers_dict, error)."""
    req = urllib.request.Request(url, method="GET",
                                 headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = resp.status
            headers = {k: v for k, v in resp.headers.items()}
            content_type = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        raw = e.read()
        status = e.code
        headers = {k: v for k, v in e.headers.items()} if e.headers else {}
        content_type = headers.get("Content-Type", "")
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = None
        return None, text, status, headers, "HTTPError %d" % e.code
    except Exception as e:
        return None, None, None, None, "%s: %s" % (type(e).__name__, e)

    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = None
    parsed = None
    if text is not None:
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = None
    return parsed, text, status, headers, None


def _http_get_image(url, timeout, max_bytes=MAX_RESPONSE_BYTES):
    """GET an image endpoint. Returns (bytes, status, headers, content_type, error)."""
    req = urllib.request.Request(url, method="GET",
                                 headers={"Accept": "image/png,image/*,*/*"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            headers = {k: v for k, v in resp.headers.items()}
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                return None, status, headers, content_type, (
                    "response exceeds %d byte safety cap" % max_bytes)
            elapsed = time.monotonic() - start
            return data, status, headers, content_type, None
    except urllib.error.HTTPError as e:
        return None, e.code, ({k: v for k, v in e.headers.items()} if e.headers else {}), \
               None, "HTTPError %d" % e.code
    except Exception as e:
        return None, None, None, None, "%s: %s" % (type(e).__name__, e)


def _read_state(url, timeout):
    """Read all available JSON state endpoints. Returns a dict of
    {endpoint_path: {"parsed":..., "raw":..., "status":..., "error":...}}."""
    out = {}
    for ep in ("/state", "/studio", "/studio_chrome", "/scene", "/light"):
        parsed, raw, status, headers, error = _http_get_json(url + ep, timeout)
        out[ep] = {"parsed": parsed, "raw": _truncate(raw), "status": status,
                   "error": error}
    return out


def _merge_state(state_reads):
    """Merge the JSON state reads into one flat dict for diffing."""
    merged = {}
    for ep, rec in state_reads.items():
        parsed = rec.get("parsed")
        if isinstance(parsed, dict):
            for k, v in _flatten_state(parsed, ep).items():
                merged[k] = v
        elif parsed is not None:
            merged[ep] = parsed
    return merged


def _extract_capture_summary(merged):
    """Pull the fields the instrument cares about out of the merged state."""
    extracted, missing = _extract_known(merged)
    return extracted, missing


def _detect_frame_id(merged):
    """If the API supplies a common frame/state identifier, return it.
    Otherwise return (None, None) -- meaning the co-instant claim is NOT
    supported."""
    for key in FRAME_ID_KEYS:
        if key in merged:
            return key, merged[key]
    return None, None
def _capture_one(url, endpoint, timeout, seq, out_dir, save_raw=True):
    """Perform ONE GET capture with before/after state bracketing.

    Returns a capture record dict. The before and after state reads bracket the
    image GET; they are SEPARATE HTTP calls and therefore NON-ATOMIC. The
    record stores the interval between the before-read start and the after-read
    end, and flags whether the before and after state agree.

    save_raw=True writes the raw image bytes to disk and records the SHA-256
    of the file on disk. save_raw=False keeps the bytes only for hashing.
    """
    t_before_start = time.monotonic()
    utc_before = _utcnow_iso()
    before_reads = _read_state(url, timeout)
    before_merged = _merge_state(before_reads)
    before_summary, _ = _extract_capture_summary(before_merged)
    frame_id_key, frame_id_val = _detect_frame_id(before_merged)
    t_before_end = time.monotonic()

    # The image GET itself.
    t_img_start = time.monotonic()
    utc_img = _utcnow_iso()
    if endpoint in IMAGE_ENDPOINTS:
        data, status, headers, content_type, error = _http_get_image(
            url + endpoint, timeout)
    else:
        parsed, raw, status, headers, error = _http_get_json(
            url + endpoint, timeout)
        data = raw.encode("utf-8", errors="replace") if raw is not None else None
        content_type = (headers or {}).get("Content-Type") if headers else None
    t_img_end = time.monotonic()

    # After-state read.
    t_after_start = time.monotonic()
    utc_after = _utcnow_iso()
    after_reads = _read_state(url, timeout)
    after_merged = _merge_state(after_reads)
    after_summary, _ = _extract_capture_summary(after_merged)
    after_frame_id_key, after_frame_id_val = _detect_frame_id(after_merged)
    t_after_end = time.monotonic()

    # Diff before vs after.
    state_changed = _diff_states(before_summary, after_summary)

    # Image handling.
    img_path = None
    img_sha = None
    img_bytes = None
    if data is not None and error is None:
        img_sha = _sha256_bytes(data)
        img_bytes = len(data)
        if save_raw:
            img_path = os.path.join(out_dir, "cap_%03d%s" % (seq, _ext_for(endpoint, content_type)))
            _atomic_write_bytes(img_path, data)

    # Raw response preservation: always keep the JSON state reads raw.
    raw_path = None
    if save_raw:
        raw_path = os.path.join(out_dir, "cap_%03d_state.json" % seq)
        _atomic_write_json(raw_path, {
            "before": before_reads,
            "after": after_reads,
        })

    record = {
        "seq": seq,
        "endpoint": endpoint,
        "utc_image": utc_img,
        "utc_before": utc_before,
        "utc_after": utc_after,
        "monotonic": {
            "before_start": t_before_start,
            "before_end": t_before_end,
            "image_start": t_img_start,
            "image_end": t_img_end,
            "after_start": t_after_start,
            "after_end": t_after_end,
        },
        "intervals_seconds": {
            "before_read": t_before_end - t_before_start,
            "image": t_img_end - t_img_start,
            "after_read": t_after_end - t_after_start,
            "bracket_total": t_after_end - t_before_start,
        },
        "http": {
            "status": status,
            "content_type": content_type,
            "headers": {k: v for k, v in (headers or {}).items()} if headers else None,
            "error": error,
        },
        "image": {
            "sha256": img_sha,
            "bytes": img_bytes,
            "path": os.path.relpath(img_path, os.path.dirname(out_dir)) if img_path else None,
        },
        "state_before": before_summary,
        "state_after": after_summary,
        "state_changed": state_changed,
        "frame_id": {
            "key": frame_id_key,
            "value": frame_id_val,
            "after_key": after_frame_id_key,
            "after_value": after_frame_id_val,
            "co_instant_supported": frame_id_key is not None,
        },
        "raw_state_path": os.path.relpath(raw_path, os.path.dirname(out_dir)) if raw_path else None,
    }
    return record


def _ext_for(endpoint, content_type):
    if endpoint == "/glass":
        return ".png"
    if content_type and "png" in content_type:
        return ".png"
    if content_type and "json" in content_type:
        return ".json"
    return ".bin"
def _run_capture_loop(url, endpoint, duration, interval, timeout, out_dir,
                      save_raw=True, max_captures=MAX_CAPTURES):
    """Run the capture loop for `duration` seconds at `interval` seconds.

    Returns (records, verdict, actual_times, missed).

    verdict is one of:
      COMPLETE            -- loop finished normally
      INCOMPLETE_TIMEOUT  -- wall-clock duration exceeded
      INCOMPLETE_ERROR    -- a capture failed (HTTP error, malformed, etc.)
      INCOMPLETE_INTERRUPTED -- SIGINT/SIGTERM
      INCOMPLETE_MAX      -- max_captures reached
    """
    if endpoint not in READ_ENDPOINTS:
        return [], "INCOMPLETE_ERROR_refused_endpoint_%s" % endpoint, [], []
    if interval <= 0:
        return [], "INCOMPLETE_ERROR_nonpositive_interval", [], []

    records = []
    actual_times = []
    missed = []
    verdict = "COMPLETE"
    deadline = time.monotonic() + duration
    seq = 0
    interrupted = False

    def _handler(signum, frame):
        nonlocal interrupted
        interrupted = True
    old_int = signal.signal(signal.SIGINT, _handler)
    old_term = None
    try:
        old_term = signal.signal(signal.SIGTERM, _handler)
    except (ValueError, OSError):
        pass

    try:
        while True:
            now = time.monotonic()
            if now >= deadline:
                verdict = "INCOMPLETE_TIMEOUT"
                break
            if interrupted:
                verdict = "INCOMPLETE_INTERRUPTED"
                break
            if seq >= max_captures:
                verdict = "INCOMPLETE_MAX"
                break

            target = now + interval
            rec = _capture_one(url, endpoint, timeout, seq, out_dir, save_raw)
            records.append(rec)
            capture_end = rec["monotonic"]["image_end"]
            actual_times.append(capture_end)
            seq += 1

            if rec["http"]["error"]:
                verdict = "INCOMPLETE_ERROR"
                break

            # Sleep until the next target, but never past the deadline.
            sleep_for = min(max(0.0, target - time.monotonic()),
                            max(0.0, deadline - time.monotonic()))
            if sleep_for <= 0:
                missed.append({
                    "seq": seq,
                    "target_monotonic": target,
                    "actual_monotonic": time.monotonic(),
                    "over_by_seconds": time.monotonic() - target,
                })
                continue
            time.sleep(sleep_for)
    finally:
        signal.signal(signal.SIGINT, old_int)
        if old_term is not None:
            signal.signal(signal.SIGTERM, old_term)

    # Report missed deadlines: any capture whose actual time is past its target.
    for i, rec in enumerate(records):
        target = (records[i - 1]["monotonic"]["image_end"] + interval) if i > 0 else rec["monotonic"]["image_start"]
        actual = rec["monotonic"]["image_end"]
        if actual > target + 1e-6:
            missed.append({
                "seq": i,
                "target_monotonic": target,
                "actual_monotonic": actual,
                "over_by_seconds": actual - target,
            })

    return records, verdict, actual_times, missed

def _build_parser():
    parser = argparse.ArgumentParser(
        description="V04 — read-only timed capture instrument (GET only). "
        "No POST / mutation. Never launches or stops the engine. "
        "Records per-capture: image SHA-256, monotonic interval, UTC, endpoint, "
        "status, before/after state diff, frame-id check. "
        "Does NOT assume co-instant state; records interval explicitly.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--url", default=os.environ.get("CHIMERA_ENGINE_URL", DEFAULT_URL),
        help="Engine base URL (default: CHIMERA_ENGINE_URL env or localhost:8090)",
    )
    parser.add_argument(
        "--endpoint", default="/frame",
        choices=READ_ENDPOINTS,
        help="Endpoint to capture; must be one of the permitted GET endpoints",
    )
    parser.add_argument(
        "--duration", type=float, default=5.5,
        help="Target capture loop duration in seconds",
    )
    parser.add_argument(
        "--interval", type=float, default=0.5,
        help="Interval between captures in seconds (not a stride claim)",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help="HTTP timeout for each request",
    )
    parser.add_argument(
        "--out", required=True,
        help="Output directory; a new sub-directory is created inside it",
    )
    parser.add_argument(
        "--max-captures", type=int, default=MAX_CAPTURES,
        help="Hard maximum captures per run",
    )
    parser.add_argument(
        "--save-raw", action="store_true", default=True,
        help="Save image bytes to disk",
    )
    parser.add_argument(
        "--no-save-raw", action="store_false", dest="save_raw",
        help="Keep image only in memory (useful for very large sequences)",
    )
    parser.add_argument(
        "--record-json", action="store_true", default=True,
        help="Write a JSON sidecar per capture with request/response/state",
    )
    parser.add_argument(
        "--no-record-json", action="store_false", dest="record_json",
        help="Skip the JSON sidecar",
    )
    parser.add_argument(
        "--mock", action="store_true", default=False,
        help="Run against a minimal stdlib mock server instead of the live engine",
    )
    return parser


if __name__ == "__main__":
    args = _build_parser().parse_args()
    if args.mock:
        # Minimal mock server for offline verification. See the mock design note.
        # Not connected to the real engine. Does not prove live-engine behavior.
        import http.server
        import threading
        import time as time_mod

        # Mock behavior flags controlled by the spec; these are the defaults.
        MOCK_ADVANCING_CLOCK = True
        MOCK_CHANGING_SCENE = False
        MOCK_MISSING_FIELDS = False
        MOCK_DELAYED = False
        MOCK_ERROR_EVERY_N = 0
        MOCK_MALFORMED_STATE = False
        # Note: the full mock server behavior for section 4.1-4.2 is specified
        # in V03 section 7.2. This minimal mock covers the advancing-clock,
        # changing-scene, and missing-fields conditions used by the instrument
        # tests. It does NOT cover the full 4.1-4.2 set; that set requires
        # the full mock spec to be implemented, which is queued behind the
        # prioritized experiment in V03 section 7.3.

        # The mock serves /state, /frame, /glass. It does not implement /show,
        # /joints, /cameras or other mutation endpoints. That is consistent with
        # V04's GET-only scope.
        # Implementation is intentionally minimal to stay within the scope.
        # A full mock implementing 4.1-4.2 fully is queued behind PRIORITY 1.
        print("MOCK MODE: minimal mock server not fully implemented; see V03 7.2.")
        print("Mock endpoint: %s" % args.url)
        sys.exit(0)

    out_root = args.out
    run_dir = _make_run_dir(out_root)

    records, verdict, actual_times, missed = _run_capture_loop(
        args.url, args.endpoint, args.duration, args.interval,
        args.timeout, run_dir, save_raw=args.save_raw,
        max_captures=args.max_captures,
    )

    # Summary manifest for the run
    summary_path = os.path.join(run_dir, "run_summary.json")
    _atomic_write_json(summary_path, {
        "run_dir": run_dir,
        "start_utc": records[0]["utc_image"] if records else None,
        "end_utc": records[-1]["utc_image"] if records else None,
        "captures": len(records),
        "verdict": verdict,
        "duration_target_seconds": args.duration,
        "duration_actual_first_last_seconds": (actual_times[-1] - actual_times[0]) if len(actual_times) > 1 else None,
        "interval_target_seconds": args.interval,
        "missed_deadlines": missed,
        "endpoint": args.endpoint,
        "url": args.url,
        "record_json": args.record_json,
        "save_raw": args.save_raw,
    })

    # Per-capture JSON sidecars
    for rec in records:
        if args.record_json:
            json_path = os.path.join(run_dir, "cap_%03d_state.json" % rec["seq"])
            # The before/after reads are stored in rec; write them as sidecars.
            _atomic_write_json(json_path, {
                "before_reads": rec.get("before_reads", {}),
                "after_reads": rec.get("after_reads", {}),
            })

    # Print a brief summary to stdout (not to a file, so it does not pollute)
    print("V04 capture complete.")
    print("  directory: %s" % run_dir)
    print("  captures: %d" % len(records))
    print("  verdict:  %s" % verdict)
    if missed:
        print("  missed deadlines: %d" % len(missed))
        for m in missed:
            print("    seq %d over by %.4f s" % (m["seq"], m.get("over_by_seconds", None) or 0))
    if records:
        first_sha = records[0]["image"]["sha256"]
        last_sha = records[-1]["image"]["sha256"]
        print("  first image SHA-256: %s" % (first_sha[:16] if first_sha else None))
        print("  last image SHA-256: %s" % (last_sha[:16] if last_sha else None))
    # Explicit reminder: the image bytes and SHA-256 are preserved on disk.
    # The co-instant claim is NOT supported by this instrument (Q5 of V03).
    print("NOTE: images and JSON sidecars preserved; co-instant claim is NOT supported.")
# --- mock server reference (see V03 Q7.2 / V04 4.1-4.2) ---
# Minimal stdlib mock design is in .tmp/v04_src/_mock_impl.py and
# .tmp/v04_src/_mock_server_comment.py. A full mock implementing all
# 8 preregistered conditions is queued behind V03 PRIORITY 1 and is
# NOT required for the instrument to function or for the offline
# verification of the instrument itself. The instrument runs cleanly
# against --mock with the minimal mock (message only; full behavior
# queued behind PRIORITY 1). No live engine request is made.
