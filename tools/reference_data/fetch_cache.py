"""Pinned fetch + cache for reference sources.

Semantics:
  * cache dir = data/cache/<relative path from the source registry>
  * data/pins.json holds the sha256 observed at FIRST successful fetch
  * a later run verifies the cached bytes against the pin and FAILS LOUDLY on
    drift (a source that changed under a pinned id stops the import -- it never
    silently re-imports different bytes under the same provenance)
  * --refresh re-downloads and RE-PINS (explicit human action, reported)
  * downloads run CONCURRENTLY (ThreadPoolExecutor) -- I/O-bound, per the
    standing no-serial-long-runs rule
"""

import concurrent.futures
import hashlib
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "data", "cache")
PINS_PATH = os.path.join(HERE, "data", "pins.json")

USER_AGENT = "chimera-reference-importer/1.0 (pinned deterministic import)"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_pins() -> dict:
    if os.path.exists(PINS_PATH):
        with open(PINS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_pins(pins: dict) -> None:
    os.makedirs(os.path.dirname(PINS_PATH), exist_ok=True)
    with open(PINS_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(pins, f, indent=1, sort_keys=True, ensure_ascii=False)


def _fetch(url: str, timeout: float = 90.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def resolve_artifact(source_id: str, entry: dict) -> list:
    """Expand one registry entry into concrete (rel_cache_path, url) artifacts."""
    rel = entry["cache"]
    if "{UNIT}" in rel or "{KIND}" in rel:
        out = []
        for u in entry.get("units", []):
            out.append((f"qudt/unit_{u}.ttl",
                        entry["entry_url"].replace("{UNIT}", u)))
        for k in entry.get("quantity_kinds", []):
            out.append((f"qudt/quantitykind_{k}.ttl",
                        "https://qudt.org/vocab/quantitykind/" + k))
        return out
    return [(rel, entry["resolved_url"])]


def ensure_cached(source_id: str, rel: str, url: str,
                  pins: dict, refresh: bool = False) -> dict:
    """Return a provenance record for one artifact; enforce pin semantics."""
    pin_key = f"{source_id}::{rel}"
    path = os.path.join(CACHE_DIR, rel.replace("/", os.sep))
    if refresh or not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = _fetch(url)
        with open(path, "wb") as f:
            f.write(data)
    else:
        with open(path, "rb") as f:
            data = f.read()
    digest = sha256_bytes(data)
    rec = {"sha256": digest, "bytes": len(data), "cached_path": rel,
           "url": url}
    if refresh or pin_key not in pins:
        pins[pin_key] = digest
        rec["pin"] = "set" if refresh else "new"
    else:
        pinned = pins[pin_key]
        if pinned != digest:
            raise SystemExit(
                f"PIN DRIFT for {pin_key}: pinned sha256 {pinned} != observed "
                f"{digest}. The pinned source changed upstream. If this is "
                f"intended, re-run with --refresh (a human decision) and record "
                f"the new release in sources.py.")
        rec["pin"] = "verified"
    return rec


def ensure_all_cached(registry: dict, refresh: bool = False) -> dict:
    """Fetch/verify every artifact of every source, concurrently."""
    pins = load_pins()
    jobs = []
    for sid, entry in registry.items():
        for rel, url in resolve_artifact(sid, entry):
            jobs.append((sid, rel, url))
    provenance = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(ensure_cached, sid, rel, url, pins, refresh): (sid, rel)
                   for sid, rel, url in jobs}
        for fut in concurrent.futures.as_completed(futures):
            sid, rel = futures[fut]
            provenance[f"{sid}::{rel}"] = fut.result()
    save_pins(pins)
    return provenance
