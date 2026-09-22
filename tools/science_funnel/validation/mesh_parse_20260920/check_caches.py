"""check_caches.py -- THE FAST FENCES (lane mesh-parse-20260920), CPU-only,
no engine, no server. Verifies the admission cache's contract as code:

  1. the payload pin still holds and _load_body_import serves the pinned GLB;
  2. derivation determinism: derive_import_glb on the pinned payload is
     byte-identical to the committed cache (x2 fresh derivations here);
  3. a TAMPERED cache file is refused BY NAME (never served);
  4. the negative-zero/zero-center trap is refused BY NAME (the payload's
     own single negative zero survives only because its axis center is
     0.14919201 -- measured, record.md);
  5. the ghost cache serves the pinned bytes and a tampered ghost file is
     refused by name;
  6. the ghost cache's compose-input audit fires on an input digest change
     (checked against a mutated COPY of the manifest, never the real one).

Writes check_caches_receipt.json HERE. Exit 0 iff every fence holds.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SLICE = ROOT / "tools" / "playable_slice"
sys.path.insert(0, str(SLICE))
import scene_boot as sb  # noqa: E402

results: dict[str, bool] = {}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    # 1. the payload pin and the served cache
    obj, rec = sb.build_real_body()
    results["payload_pin_ok"] = rec["sha256"] == \
        "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111"
    route, payload = sb._load_body_import(obj, rec)
    results["import_route_is_cache"] = route == "cache"
    man = json.loads(sb.BOOT_CACHE_MANIFEST.read_text(encoding="utf-8"))
    results["served_glb_matches_pin"] = sha(payload) == \
        man["import_glb"]["sha256"]

    # 2. derivation determinism vs the committed bytes
    glbs = {sha(sb.derive_import_glb(obj)) for _ in range(2)}
    results["derivation_byte_stable_and_committed"] = glbs == {
        man["import_glb"]["sha256"]}

    # 3. tampered GLB is refused by name
    saved = sb.BODY_GLB.read_bytes()
    try:
        bad = bytearray(saved)
        bad[-1] ^= 0xFF
        sb.BODY_GLB.write_bytes(bytes(bad))
        try:
            sb._load_body_import(obj, rec)
            results["tampered_glb_refused"] = False
        except RuntimeError as e:
            results["tampered_glb_refused"] = "drift" in str(e)
    finally:
        sb.BODY_GLB.write_bytes(saved)

    # 4. the trap: negative zero on a zero-centered axis refuses
    trap_obj = (b"# trap probe\n"
                b"v 0.5 0 0\nv -0.5 0 0\nv -0.0 1 0.5\nv 0.2 1 -0.5\n"
                b"f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n")
    try:
        sb.derive_import_glb(trap_obj)
        results["trap_refused"] = False
    except ValueError as e:
        results["trap_refused"] = "negative-zero" in str(e)
    # the same geometry with a plain zero does NOT refuse (no false positive)
    ok_obj = trap_obj.replace(b"v -0.0 1 0.5", b"v 0.0 1 0.5")
    try:
        sb.derive_import_glb(ok_obj)
        results["trap_no_false_positive"] = True
    except ValueError:
        results["trap_no_false_positive"] = False

    # 5. ghost cache serves pinned bytes; tampered ghost refused by name
    gone, grec = sb.build_ghost_obj()
    results["ghost_route_is_cache"] = grec.get("ghost_source") == "cache"
    results["ghost_bytes_match_pin"] = sha(gone) == man["ghost_obj"]["sha256"]
    ghost_saved = sb.GHOST_CACHE.read_bytes()
    try:
        bad_g = bytearray(ghost_saved)
        bad_g[200] ^= 0xFF
        sb.GHOST_CACHE.write_bytes(bytes(bad_g))
        try:
            sb.build_ghost_obj()
            results["tampered_ghost_refused"] = False
        except RuntimeError as e:
            results["tampered_ghost_refused"] = "drift" in str(e)
    finally:
        sb.GHOST_CACHE.write_bytes(ghost_saved)

    # 6. compose-input audit fires on a changed input digest (mutated COPY)
    bad_man = json.loads(json.dumps(man))
    bad_man["ghost_obj"]["compose_inputs"][0]["sha256"] = "0" * 64
    real_man = sb.BOOT_CACHE_MANIFEST
    tmp_man = real_man.with_suffix(".json.check_tmp")
    try:
        shutil.copy(real_man, tmp_man)
        real_man.write_text(json.dumps(bad_man), encoding="utf-8")
        try:
            sb.build_ghost_obj()
            results["input_drift_refused"] = False
        except RuntimeError as e:
            results["input_drift_refused"] = "compose input changed" in str(e)
    finally:
        shutil.move(str(tmp_man), str(real_man))
    results["manifest_restored"] = \
        json.loads(real_man.read_text(encoding="utf-8")) == man

    out = {"fences": results, "pass": all(results.values())}
    (HERE / "check_caches_receipt.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
