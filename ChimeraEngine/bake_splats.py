"""bake_splats.py — bake all proven terms' settled buffers to disk.

THEORY: A membrane's emit(nums, t=1.0) produces the settled-state splat buffer. Baking writes
this buffer to disk as a .npy file, one per term. Load-time verification compares the baked
buffer bit-identical to live emission — if they differ, the bake is lossy and the term must
be re-baked.

RULE 0:
  STATEMENT: Every proven term's settled buffer can be serialized to disk and reloaded
  bit-identically, because emit() is deterministic (theZero's RNG is seeded).
  PREDICTION: All 38 terms load from their baked .npy files in under 2 seconds total.
  FALSIFIER: Any baked buffer differs from live emit — the bake is lossy, and the term
  is reported with a hash mismatch.

Output: ChimeraEngine/baked/term_name.npy for each proven term.
Also writes bake_manifest.json with hashes and timestamps.

Author: Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))  # repo root for story/matter.py
sys.path.insert(0, str(_HERE))         # ChimeraEngine for splat_appearance

import splat_appearance as sa

BAKE_DIR = _HERE / "baked"
MANIFEST = BAKE_DIR / "bake_manifest.json"


def hash_buffer(buf: np.ndarray) -> str:
    """SHA-256 of the buffer bytes (deterministic, bit-exact)."""
    return hashlib.sha256(buf.tobytes()).hexdigest()[:16]


def bake_all(force: bool = False) -> dict:
    """Bake every proven term's settled buffer to disk.

    Returns manifest dict: {term: {file, n_grains, hash, elapsed_ms}}
    """
    BAKE_DIR.mkdir(parents=True, exist_ok=True)
    terms = sa.scene_terms()
    manifest: dict[str, dict] = {}
    total_ms = 0.0
    baked = 0
    skipped = 0
    failed = 0

    for term in terms:
        t0 = time.perf_counter()
        try:
            live = sa.scene_buffer(term)
        except Exception as e:
            manifest[term] = {"error": str(e), "n_grains": 0}
            failed += 1
            continue

        if live is None or live.shape[0] == 0:
            manifest[term] = {"error": "emit returned empty buffer", "n_grains": 0}
            failed += 1
            continue

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        live_hash = hash_buffer(live)

        npz_path = BAKE_DIR / f"{term}.npz"
        existing_hash = None
        if npz_path.exists() and not force:
            try:
                existing = np.load(npz_path)["splats"]
                existing_hash = hash_buffer(existing)
            except Exception:
                existing_hash = None

        if existing_hash == live_hash and not force:
            manifest[term] = {
                "file": str(npz_path.name),
                "n_grains": int(live.shape[0]),
                "hash": live_hash,
                "elapsed_ms": round(elapsed_ms, 2),
                "status": "unchanged",
            }
            skipped += 1
            total_ms += elapsed_ms
            continue

        np.savez_compressed(npz_path, splats=live)
        manifest[term] = {
            "file": str(npz_path.name),
            "n_grains": int(live.shape[0]),
            "hash": live_hash,
            "elapsed_ms": round(elapsed_ms, 2),
            "status": "baked",
        }
        baked += 1
        total_ms += elapsed_ms

    manifest["_meta"] = {
        "total_terms": len(terms),
        "baked": baked,
        "skipped": skipped,
        "failed": failed,
        "total_elapsed_ms": round(total_ms, 2),
        "baked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    MANIFEST.write_text(json.dumps(manifest, indent=2))
    print(f"Bake complete: {baked} baked, {skipped} unchanged, {failed} failed "
          f"({total_ms:.0f} ms total)")
    for term, info in sorted(manifest.items()):
        if term == "_meta":
            continue
        status = info.get("status", info.get("error", "?"))
        n = info.get("n_grains", 0)
        print(f"  {term:30s}  {n:>6d} grains  {status}")
    return manifest


def verify_all() -> tuple[bool, dict]:
    """Load every baked buffer and verify bit-identical to live emission.

    Returns (all_ok, {term: {hash_match, live_hash, baked_hash}})
    """
    results: dict[str, dict] = {}
    all_ok = True
    terms = sa.scene_terms()

    for term in terms:
        npz_path = BAKE_DIR / f"{term}.npz"
        if not npz_path.exists():
            results[term] = {"error": "no baked file", "match": False}
            all_ok = False
            continue

        try:
            baked = np.load(npz_path)["splats"]
            baked_hash = hash_buffer(baked)
        except Exception as e:
            results[term] = {"error": f"load failed: {e}", "match": False}
            all_ok = False
            continue

        try:
            live = sa.scene_buffer(term)
            if live is None:
                results[term] = {"error": "live emit returned None", "match": False}
                all_ok = False
                continue
            live_hash = hash_buffer(live)
        except Exception as e:
            results[term] = {"error": f"live emit failed: {e}", "match": False}
            all_ok = False
            continue

        ok = live_hash == baked_hash
        results[term] = {
            "match": ok,
            "live_hash": live_hash,
            "baked_hash": baked_hash,
            "n_grains": int(baked.shape[0]),
        }
        if not ok:
            all_ok = False

    return all_ok, results


def load_baked(term: str) -> np.ndarray | None:
    """Load a baked buffer from disk (fast, no emit)."""
    npz_path = BAKE_DIR / f"{term}.npz"
    if not npz_path.exists():
        return None
    try:
        return np.ascontiguousarray(np.load(npz_path)["splats"], dtype=np.float32)
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    if "--verify" in sys.argv:
        ok, results = verify_all()
        print(f"\nVerification: {'ALL OK' if ok else 'MISMATCHES FOUND'}")
        for term, r in sorted(results.items()):
            if not r.get("match", False):
                print(f"  {term}: {r}")
        raise SystemExit(0 if ok else 1)

    force = "--force" in sys.argv
    bake_all(force=force)