"""adapter.py -- I-R02-SAVE-STORE-FOLLOWUP: subprocess fault-injection harness
for the MERGED save-store of parent card I-R02-SAVE-STORE.

WHAT THIS ADAPTER OWNS: killing a REAL writer subprocess at deterministic points
inside the accepted module's atomic write, and corrupting stored envelope BYTES on
disk, so the parent card's durability laws are measured against actual process
death -- not against mocks, exceptions, or a rewritten stand-in.

THE ACCEPTED MODULE (exact bytes, hash-pinned):
    PR            https://github.com/GhostDragonAlpha/Chimera/pull/117
    head (merged) 9ba1be77228e181f55ed2e4d2eb3e73e2f09685f  (branch-4)
    tree path     tools/monkey_campaign/contributions/I-R02-SAVE-STORE/save_store.py
    raw sha256    cf175ea73508927697905cb9faa96737bb454ce7e946caa1ccc247338e4f9347
load_accepted_module() REFUSES (AdapterRefusal "stand_in_module") any file whose
SHA-256 differs. A stand-in cannot load, so the card falsifier is self-enforcing.

CHILD PROCESS MODEL (`python adapter.py child ...`): the child loads the accepted
module (hash re-verified in the child), arms one injection by monkeypatching
`builtins.open` / `os.fsync` / `os.replace` IN ITS OWN PROCESS ONLY, calls the real
`SaveStore.save`, and dies with `os._exit` at the armed point -- hard death, no
exception unwinding, no temp-file cleanup. Marker lines (one JSON object per line)
are printed to stdout so the parent can prove WHERE the child died:

    {"event": "armed",   "point": "before_replace"}     patches installed
    {"event": "died_at", "point": "before_replace"}     immediately before _exit
    {"event": "saved",   ...}                            clean save, exit 0
    {"event": "refused", "code": "slot_traversal"}      SaveError refused, exit 3

INJECTION POINTS AND EXIT CODES (all inside SaveStore.save, after input checks):
    none           0   no patch; full atomic save (clean control)
    before_open   10   death before the temp file is created
    mid_write      9   death after HALF the envelope bytes are written
    before_fsync   8   death after full write, before fsync
    before_replace 7   death after write+flush+fsync, immediately before
                       os.replace -- THE targeted "interrupted writer before the
                       atomic replace" point

NO CLAIM ABOUT PHYSICS STATE: the payload is opaque bytes end to end. Nothing here
tests or qualifies engine snapshot semantics (parent card law; prediction F4).

Standalone, stdlib only, CPU-only, temporary directories only.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ACCEPTED_SAVE_STORE_SHA256 = (
    "cf175ea73508927697905cb9faa96737bb454ce7e946caa1ccc247338e4f9347"
)
ACCEPTED_SOURCE_PR = "https://github.com/GhostDragonAlpha/Chimera/pull/117"
ACCEPTED_SOURCE_HEAD = "9ba1be77228e181f55ed2e4d2eb3e73e2f09685f"

CHILD_TIMEOUT_SECONDS = 30          # per subprocess; card bound is 120 s/invocation
EXIT_CLEAN = 0
EXIT_REFUSED = 3
EXIT_BY_POINT = {"before_replace": 7, "before_fsync": 8,
                 "mid_write": 9, "before_open": 10}
POINTS = ("before_open", "mid_write", "before_fsync", "before_replace")

# Deterministic payloads (byte-identical on every rerun; no randomness).
def payload_a() -> bytes:
    """2048 B prior-save payload: chained sha256 blocks labeled for slot A."""
    out = bytearray()
    seed = b"I-R02-SAVE-STORE-FOLLOWUP/payload-A"
    block = seed
    for _ in range(64):
        block = hashlib.sha256(block).digest()
        out += block
    return bytes(out)


def payload_b(tag: str = "B") -> bytes:
    """48 KiB overwrite payload: counter-hashed blocks labeled per attempt."""
    out = bytearray()
    for i in range(1536):
        out += hashlib.sha256(f"FOLLOWUP/{tag}/{i}".encode("ascii")).digest()
    return bytes(out)


class AdapterRefusal(Exception):
    """The harness refuses to proceed; code names the law that fired."""


# ── accepted-module resolution + hash pin ────────────────────────────────────
def resolve_save_store_path(explicit: str | None = None) -> Path:
    """Locate the accepted save_store.py: explicit arg > env > published-tree
    sibling > attempt-workspace reference copy. Raise AdapterRefusal if absent."""
    here = Path(__file__).resolve().parent
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("SAVE_STORE_PATH")
    if env:
        candidates.append(Path(env))
    candidates.append(here.parent / "I-R02-SAVE-STORE" / "save_store.py")  # merged tree
    candidates.append(here / "reference" / "I-R02-SAVE-STORE" / "save_store.py")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise AdapterRefusal(
        f"save_store_path_unresolved: none of {[str(c) for c in candidates]} exists; "
        f"pass --save-store-path or set SAVE_STORE_PATH")


def file_sha256(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_accepted_module(path=None):
    """Import the accepted save_store module AFTER verifying its exact bytes.

    Raises AdapterRefusal("stand_in_module", ...) when the hash differs -- the
    card falsifier makes a rewritten stand-in impossible to load."""
    resolved = resolve_save_store_path(str(path) if path else None)
    actual = file_sha256(resolved)
    if actual != ACCEPTED_SAVE_STORE_SHA256:
        raise AdapterRefusal(
            f"stand_in_module: {resolved} sha256 {actual} != accepted "
            f"{ACCEPTED_SAVE_STORE_SHA256} (PR #117 head {ACCEPTED_SOURCE_HEAD}); "
            f"refusing to fault-inject a stand-in")
    spec = importlib.util.spec_from_file_location("accepted_save_store", resolved)
    module = importlib.util.module_from_spec(spec)
    sys.modules["accepted_save_store"] = module   # dataclasses needs this entry
    spec.loader.exec_module(module)
    module._accepted_path = str(resolved)      # provenance for tests/report
    module._accepted_sha256 = actual
    return module


# ── child side: arm one injection, run the real save, die at the point ───────
def _emit(event: str, **fields) -> None:
    print(json.dumps({"event": event, **fields}), flush=True)


class _HalfWriteProxy:
    """File proxy that writes HALF the envelope bytes, then kills the process."""

    def __init__(self, real_handle, point: str):
        self._real = real_handle
        self._point = point

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._real.close()
        return False

    def write(self, data):
        half = bytes(data[: max(1, len(data) // 2)])
        self._real.write(half)                  # partial envelope on disk
        self._real.flush()
        _emit("died_at", point=self._point)
        os._exit(EXIT_BY_POINT[self._point])    # hard death, no cleanup

    def flush(self):
        self._real.flush()

    def fileno(self):
        return self._real.fileno()

    def close(self):
        self._real.close()


def _arm_injection(point: str, slot_name: str) -> None:
    """Monkeypatch builtins.open / os.fsync / os.replace in THIS child process so
    the next real SaveStore.save dies at `point`. Patches fire exactly once."""
    if point not in EXIT_BY_POINT:
        raise AdapterRefusal(f"injection_point_unknown: {point!r}")

    temp_prefix = f".{slot_name}.tmp-"
    fired = {"done": False}

    def is_temp(name):
        return temp_prefix in os.path.basename(str(name))

    if point == "before_open":
        def patched_open(file, mode="r", *a, **k):
            if mode == "wb" and is_temp(file):
                if not fired["done"]:
                    fired["done"] = True
                    _emit("died_at", point=point)
                    os._exit(EXIT_BY_POINT[point])
            return real_open(file, mode, *a, **k)
        real_open = open
        builtins_patch = patched_open
    elif point == "mid_write":
        def patched_open(file, mode="r", *a, **k):
            real = real_open(file, mode, *a, **k)
            if mode == "wb" and is_temp(file):
                if not fired["done"]:
                    fired["done"] = True
                    return _HalfWriteProxy(real, point)
            return real
        real_open = open
        builtins_patch = patched_open
    else:
        builtins_patch = None
    if builtins_patch is not None:
        import builtins
        builtins.open = builtins_patch          # noqa: A001 -- child process only

    if point == "before_fsync":
        real_fsync = os.fsync

        def patched_fsync(fd):
            if not fired["done"]:
                fired["done"] = True
                _emit("died_at", point=point)
                os._exit(EXIT_BY_POINT[point])
            return real_fsync(fd)
        os.fsync = patched_fsync

    if point == "before_replace":
        real_replace = os.replace

        def patched_replace(src, dst):
            if not fired["done"]:
                fired["done"] = True
                _emit("died_at", point=point,
                      src=os.path.basename(str(src)), dst=os.path.basename(str(dst)))
                os._exit(EXIT_BY_POINT[point])
            return real_replace(src, dst)
        os.replace = patched_replace


def child_main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="adapter.py child")
    parser.add_argument("--save-store-path", required=True)
    parser.add_argument("--user-dir", required=True)
    parser.add_argument("--slot", required=True)
    parser.add_argument("--format-version", type=int, required=True)
    parser.add_argument("--build-id", required=True)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--policy-id", required=True)
    parser.add_argument("--payload-file", required=True,
                        help="raw opaque payload bytes; never interpreted")
    parser.add_argument("--inject", default="none",
                        choices=["none", *EXIT_BY_POINT])
    args = parser.parse_args(argv)

    module = load_accepted_module(args.save_store_path)   # hash re-verified here
    payload = Path(args.payload_file).read_bytes()
    if args.inject != "none":
        _arm_injection(args.inject, args.slot)
    _emit("armed", point=args.inject,
          save_store_sha256=module._accepted_sha256, pid=os.getpid())
    try:
        store = module.SaveStore(user_directory=args.user_dir)
        result = store.save(args.slot, format_version=args.format_version,
                            build_id=args.build_id, scene_id=args.scene_id,
                            policy_id=args.policy_id, payload=payload)
    except module.SaveError as exc:                       # named refusal, exit 3
        _emit("refused", code=exc.refusal.code, detail=exc.refusal.detail)
        return EXIT_REFUSED
    _emit("saved", slot=result.slot_name, path=result.path,
          bytes_written=result.bytes_written, atomic=result.atomic)
    return EXIT_CLEAN


# ── parent side: spawn children and collect markers ─────────────────────────
def run_child(adapter_path, save_store_path, user_dir, slot, payload, *,
              format_version=3, build_id="b-8630", scene_id="forest-one",
              policy_id="gait-v2", inject="none", timeout=CHILD_TIMEOUT_SECONDS):
    """Run one writer child. Returns (CompletedProcess, events, payload_path)."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".payload") as tmp:
        tmp.write(payload)
        payload_path = tmp.name
    command = [sys.executable, "-B", str(adapter_path), "child",
               "--save-store-path", str(save_store_path),
               "--user-dir", str(user_dir), "--slot", slot,
               "--format-version", str(format_version),
               "--build-id", build_id, "--scene-id", scene_id,
               "--policy-id", policy_id,
               "--payload-file", payload_path,
               "--inject", inject]
    try:
        proc = subprocess.run(command, capture_output=True, timeout=timeout)
        events = [json.loads(line) for line in proc.stdout.decode("utf-8")
                  .splitlines() if line.strip()]
    finally:
        os.unlink(payload_path)
    proc.events = events
    return proc


def slot_path(user_dir, slot, suffix=".save.json"):
    return Path(user_dir) / (slot + suffix)


# ── parent side: byte-level on-disk tamper helpers (bypass the module) ───────
def _read_envelope_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write_envelope_bytes(path, blob: bytes) -> None:
    Path(path).write_bytes(blob)


def _rewrite_doc(path, mutate) -> None:
    """Parse the canonical envelope, apply mutate(dict), re-serialize canonically.
    Used only for tampered-field scenarios that must remain valid JSON."""
    doc = json.loads(_read_envelope_text(path))
    mutate(doc)
    text = json.dumps(doc, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False) + "\n"
    _write_envelope_bytes(path, text.encode("utf-8"))


def tamper_truncate_raw(path, fraction=0.55):
    """Raw byte truncation of the stored file -> invalid JSON on load."""
    raw = Path(path).read_bytes()
    _write_envelope_bytes(path, raw[: int(len(raw) * fraction)])
    return "json_corrupt"


def tamper_flip_b64_char(path):
    """Flip the first payload_b64 character (still valid base64) -> decoded
    payload changes -> stored hash no longer matches."""
    def mutate(doc):
        b64 = doc["payload_b64"]
        doc["payload_b64"] = ("B" if b64[0] != "B" else "C") + b64[1:]
    _rewrite_doc(path, mutate)
    return "payload_hash_mismatch"


def tamper_stored_hash(path):
    """Overwrite payload_sha256 with the hash of unrelated bytes."""
    def mutate(doc):
        doc["payload_sha256"] = hashlib.sha256(b"tampered-not-the-payload").hexdigest()
    _rewrite_doc(path, mutate)
    return "payload_hash_mismatch"


def tamper_payload_size(path):
    """Declare payload_size one byte larger than the decoded payload."""
    def mutate(doc):
        doc["payload_size"] = int(doc["payload_size"]) + 1
    _rewrite_doc(path, mutate)
    return "payload_size_mismatch"


def tamper_invalid_utf8(path):
    """Insert a 0xFF byte -> not valid UTF-8."""
    raw = Path(path).read_bytes()
    cut = len(raw) // 2
    _write_envelope_bytes(path, raw[:cut] + b"\xff" + raw[cut:])
    return "not_utf8"


def tamper_duplicate_key(path):
    """Textually duplicate the build_id key -> last-win JSON is refused."""
    text = _read_envelope_text(path).rstrip("\n")
    assert text.endswith("}")
    _write_envelope_bytes(path, (text[:-1] + ',"build_id":"duplicate"}\n').encode("utf-8"))
    return "key_duplicate"


def tamper_nan_literal(path):
    """Replace the payload_size value with a NaN literal."""
    text = _read_envelope_text(path)
    import re
    patched, count = re.subn(r'"payload_size":\d+', '"payload_size":NaN', text, count=1)
    if count != 1:
        raise AdapterRefusal("tamper_nan_literal: payload_size field not found")
    _write_envelope_bytes(path, patched.encode("utf-8"))
    return "not_finite_json"


def tamper_wrong_schema(path):
    def mutate(doc):
        doc["schema"] = "chimera.some_other_schema.v9"
    _rewrite_doc(path, mutate)
    return "schema_unknown"


def tamper_bad_format_version(path):
    def mutate(doc):
        doc["format_version"] = 0
    _rewrite_doc(path, mutate)
    return "format_version_type"


def tamper_delete_identity(path):
    def mutate(doc):
        del doc["scene_id"]
    _rewrite_doc(path, mutate)
    return "scene_id_missing"


TAMPER_MATRIX = (
    ("truncate_raw", tamper_truncate_raw),
    ("flip_b64_char", tamper_flip_b64_char),
    ("stored_hash", tamper_stored_hash),
    ("payload_size", tamper_payload_size),
    ("invalid_utf8", tamper_invalid_utf8),
    ("duplicate_key", tamper_duplicate_key),
    ("nan_literal", tamper_nan_literal),
    ("wrong_schema", tamper_wrong_schema),
    ("bad_format_version", tamper_bad_format_version),
    ("delete_identity", tamper_delete_identity),
)


# ── parent side: the preregistered scenarios (used by tests + verify) ────────
IDENT_A = dict(format_version=3, build_id="b-8630", scene_id="forest-one",
               policy_id="gait-v2")
SLOT = "clearing_1"


def _load_via_accepted(module, user_dir, slot=SLOT, **expected):
    store = module.SaveStore(user_directory=str(user_dir))
    return store.load(slot, **expected), store


def scenario_interruption_preserves_prior(adapter_path, save_store_path, user_dir,
                                          module, point):
    """One trial: clean save A -> interrupted overwrite -> prior save intact."""
    a = payload_a()
    clean = run_child(adapter_path, save_store_path, user_dir, SLOT, a, **IDENT_A)
    assert clean.returncode == EXIT_CLEAN, clean.stderr[-2000:]
    prior_sha = file_sha256(slot_path(user_dir, SLOT))
    prior_stat = slot_path(user_dir, SLOT).stat()

    killed = run_child(adapter_path, save_store_path, user_dir, SLOT,
                       payload_b(point), inject=point, **IDENT_A)
    events = killed.events
    died = [e for e in events if e["event"] == "died_at"]
    after_sha = file_sha256(slot_path(user_dir, SLOT))
    after_stat = slot_path(user_dir, SLOT).stat()
    result, store = _load_via_accepted(module, user_dir)
    listing = store.list()
    return {
        "point": point,
        "child_rc": killed.returncode,
        "expected_rc": EXIT_BY_POINT[point],
        "died_at_marker": bool(died) and died[0]["point"] == point,
        "slot_bytes_unchanged": after_sha == prior_sha,
        "slot_mtime_ns_unchanged": after_stat.st_mtime_ns == prior_stat.st_mtime_ns,
        "load_status": result.status,
        "payload_matches_prior": result.payload == a,
        "payload_sha256_matches_prior": result.payload_sha256 == hashlib.sha256(a).hexdigest(),
        "listed_slots": len(listing),
        "listed_ok": all(s.status == "ok" for s in listing),
        "prior_sha256": prior_sha,
    }


def scenario_interrupted_first_save(adapter_path, save_store_path, user_dir, module,
                                    point="before_replace"):
    b = payload_b("first")
    killed = run_child(adapter_path, save_store_path, user_dir, SLOT, b,
                       inject=point, **IDENT_A)
    result, store = _load_via_accepted(module, user_dir)
    debris = [p.name for p in Path(user_dir).iterdir()
              if p.name.startswith(f".{SLOT}.tmp-")]
    return {
        "point": point,
        "child_rc": killed.returncode,
        "load_status": result.status,           # expect first_run
        "listed_slots": len(store.list()),      # expect 0
        "real_slot_exists": slot_path(user_dir, SLOT).exists(),   # expect False
        "debris_temp_files": debris,            # allowed; must lack .save.json
    }


def scenario_corruption_matrix(user_dir, module):
    """Fresh clean save, one tamper, load must refuse with the exact named code."""
    rows = []
    for name, tamper in TAMPER_MATRIX:
        store = module.SaveStore(user_directory=str(user_dir))
        store.save(SLOT, payload=payload_a(), **IDENT_A)    # clean baseline
        path = slot_path(user_dir, SLOT)
        expected_code = tamper(path)
        result, _ = _load_via_accepted(module, user_dir)
        rows.append({
            "tamper": name,
            "expected_code": expected_code,
            "status": result.status,
            "refusal_code": (result.refusals[0].code if result.refusals else None),
            "payload_empty": result.payload == b"",
        })
        path.unlink()
    # identity mismatches on an INTACT envelope (load-time expected_* laws)
    store = module.SaveStore(user_directory=str(user_dir))
    store.save(SLOT, payload=payload_a(), **IDENT_A)
    mismatch_rows = []
    for label, expected in (
        ("format_version", {"expected_format_version": 99}),
        ("build_id", {"expected_build_id": "different-build"}),
        ("scene_id", {"expected_scene_id": "different-scene"}),
        ("policy_id", {"expected_policy_id": "different-policy"}),
    ):
        result, _ = _load_via_accepted(module, user_dir, **expected)
        mismatch_rows.append({
            "mismatch": label,
            "status": result.status,
            "refusal_code": (result.refusals[0].code if result.refusals else None),
        })
    return rows, mismatch_rows


def scenario_crash_loop(adapter_path, save_store_path, user_dir, module):
    a = payload_a()
    clean = run_child(adapter_path, save_store_path, user_dir, SLOT, a, **IDENT_A)
    assert clean.returncode == EXIT_CLEAN
    prior_sha = file_sha256(slot_path(user_dir, SLOT))
    trials = []
    for k, point in enumerate(POINTS + ("mid_write",)):
        killed = run_child(adapter_path, save_store_path, user_dir, SLOT,
                           payload_b(f"loop-{k}"), inject=point, **IDENT_A)
        result, _ = _load_via_accepted(module, user_dir)
        intact = (result.status == "loaded" and result.payload == a
                  and file_sha256(slot_path(user_dir, SLOT)) == prior_sha)
        trials.append({"iteration": k, "point": point,
                       "child_rc": killed.returncode, "prior_intact": intact})
    final = run_child(adapter_path, save_store_path, user_dir, SLOT,
                      payload_b("final"), **IDENT_A)
    result, _ = _load_via_accepted(module, user_dir)
    b_final = payload_b("final")
    return {
        "trials": trials,
        "all_prior_intact": all(t["prior_intact"] for t in trials),
        "final_rc": final.returncode,
        "final_status": result.status,
        "final_payload_exact": result.payload == b_final,
    }


def scenario_child_refusal_law(adapter_path, save_store_path, user_dir):
    """Refusal laws also fire inside the child: traversal slot name refused."""
    killed = run_child(adapter_path, save_store_path, user_dir, "../escape",
                       payload_a(), inject="none", **IDENT_A)
    refused = [e for e in killed.events if e["event"] == "refused"]
    return {
        "child_rc": killed.returncode,
        "refused_event": bool(refused),
        "code": refused[0]["code"] if refused else None,   # expect slot_traversal
    }


# ── verify: one-shot published evidence run ──────────────────────────────────
def verify(save_store_path=None) -> dict:
    started = time.monotonic()
    module = load_accepted_module(save_store_path)
    adapter_path = Path(__file__).resolve()
    ssp = module._accepted_path
    verdict = {"schema": "chimera.save_store_followup_verify.v1",
               "save_store_path": ssp, "save_store_sha256": module._accepted_sha256,
               "source_pr": ACCEPTED_SOURCE_PR, "source_head": ACCEPTED_SOURCE_HEAD}
    with tempfile.TemporaryDirectory(prefix="r02fuv-") as user_dir:
        interruption = []
        for point in POINTS:
            with tempfile.TemporaryDirectory(prefix="r02fup-") as trial_dir:
                interruption.append(scenario_interruption_preserves_prior(
                    adapter_path, ssp, trial_dir, module, point))
        verdict["interruption"] = interruption
    with tempfile.TemporaryDirectory(prefix="r02fuf-") as user_dir:
        verdict["interrupted_first_save"] = scenario_interrupted_first_save(
            adapter_path, ssp, user_dir, module)
    with tempfile.TemporaryDirectory(prefix="r02fuc-") as user_dir:
        rows, mismatches = scenario_corruption_matrix(user_dir, module)
        verdict["corruption"] = rows
        verdict["identity_mismatch"] = mismatches
    with tempfile.TemporaryDirectory(prefix="r02ful-") as user_dir:
        verdict["crash_loop"] = scenario_crash_loop(adapter_path, ssp, user_dir, module)
    with tempfile.TemporaryDirectory(prefix="r02fur-") as user_dir:
        verdict["child_refusal"] = scenario_child_refusal_law(adapter_path, ssp,
                                                              user_dir)
    verdict["elapsed_seconds"] = round(time.monotonic() - started, 2)
    verdict["pass"] = (
        all(r["child_rc"] == r["expected_rc"] and r["died_at_marker"]
            and r["slot_bytes_unchanged"] and r["load_status"] == "loaded"
            and r["payload_matches_prior"] and r["listed_slots"] == 1
            and r["listed_ok"] for r in verdict["interruption"])
        and verdict["interrupted_first_save"]["load_status"] == "first_run"
        and verdict["interrupted_first_save"]["listed_slots"] == 0
        and not verdict["interrupted_first_save"]["real_slot_exists"]
        and all(r["status"] == "refused" and r["refusal_code"] == r["expected_code"]
                and r["payload_empty"] for r in verdict["corruption"])
        and all(r["status"] == "refused"
                and r["refusal_code"] == f"{r['mismatch']}_mismatch"
                for r in verdict["identity_mismatch"])
        and verdict["crash_loop"]["all_prior_intact"]
        and verdict["crash_loop"]["final_rc"] == EXIT_CLEAN
        and verdict["crash_loop"]["final_status"] == "loaded"
        and verdict["crash_loop"]["final_payload_exact"]
        and verdict["child_refusal"]["child_rc"] == EXIT_REFUSED
        and verdict["child_refusal"]["code"] == "slot_traversal"
    )
    return verdict


def main(argv=None) -> int:
    tokens = list(argv if argv is not None else sys.argv[1:])
    if tokens and tokens[0] == "child":
        return child_main(tokens[1:])
    parser = argparse.ArgumentParser(prog="adapter.py")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("child", help="internal: one writer child (killed by design); "
                                 "argparse-unparsed by design -- child_main owns it")
    verify_parser = sub.add_parser("verify", help="run the full preregistered matrix")
    verify_parser.add_argument("--save-store-path", default=None)
    args = parser.parse_args(tokens)
    if args.command == "child":                       # not reachable: routed above
        return child_main(tokens[1:])
    verdict = verify(args.save_store_path)
    print(json.dumps(verdict, indent=1))
    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
