"""signature.py -- the death signature (death class + slice shape) and the
similar-prior-failure match against the past waves' death records.

The library (prior_faces.json) is BUILT from the wave receipts' death records by
build_prior_library.py; the packet generator only reads the emitted JSON and
HARD-DROPS every entry at or after the diagnosed run's wave (--prior-waves-through).
The slice shape is a coarse structural hash -- never the trace bytes -- so the
match is over slice SHAPE (era-length buckets, band states, seed classes), which
is what "same death, different wave" means here.
"""
from __future__ import annotations

import hashlib
import json


def _bucket_len(n):
    if n is None:
        return "?"
    if n <= 9:
        return "S"
    if n <= 18:
        return "M"
    return "L"


def _band_state(era):
    from .eras import KBAND, GRAZE_FACTOR, KTOUCH
    if era["era_max_pm"] <= 0.0:
        return "0"
    if era["era_max_pm"] <= KBAND:
        return "H"      # held under the band
    if era["era_max_pm"] <= GRAZE_FACTOR * KTOUCH:
        return "G"      # the graze fight
    return "A"          # away from the band


def slice_shape(death_info: dict, eras: list, diverge: dict, fired_classes: list) -> dict:
    tail = [e for e in eras if e["td"] and e["t0"] >= 90][-8:]
    shape = dict(
        seeds=sorted({s["seed"] for s in death_info["seeds"]}),
        fired=sorted(fired_classes),
        era_len_tail="".join(_bucket_len(e["length"]) for e in tail),
        band_tail="".join(_band_state(e) for e in tail),
        n_misfires=len(death_info["misfires"]),
        n_drains=len(death_info["drains"]),
        n_folds=len(death_info["folds"]),
        first_div_family=diverge.get("first_family"),
    )
    return shape


def signature_sha16(shape: dict) -> str:
    blob = json.dumps(shape, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def load_library(path: str, prior_waves_through: int) -> list:
    with open(path, encoding="utf-8") as f:
        faces = json.load(f)
    kept = [x for x in faces if x.get("wave") is not None and x["wave"] < prior_waves_through]
    return kept


def match_priors(shape: dict, library: list, k: int = 3) -> list:
    """Rank priors: the PRIMARY seed (the first in causal order) dominates, then
    secondary seed classes, then shared shape features."""
    seeds = list(shape["seeds"])
    primary = seeds[0] if seeds else None
    secondary = set(seeds[1:])
    scored = []
    for x in library:
        s = 0.0
        notes = []
        if primary and x.get("death_class") == primary:
            s += 3.0
            notes.append(f"same PRIMARY seed class ({primary})")
        elif x.get("death_class") in secondary:
            s += 1.0
            notes.append(f"secondary seed class ({x['death_class']})")
        shared = sum(1 for kk in ("fired", "era_len_tail", "band_tail", "first_div_family")
                     if x.get("shape", {}).get(kk) == shape.get(kk))
        s += 0.5 * shared
        if x.get("shape", {}).get("era_len_tail") == shape.get("era_len_tail") and shape.get("era_len_tail"):
            notes.append("same era-length tail shape")
        scored.append(dict(wave=x.get("wave"), face=x.get("face"), death_class=x.get("death_class"),
                           similarity=round(s, 2), why=notes,
                           receipt=x.get("receipt")))
    scored.sort(key=lambda r: -r["similarity"])
    top = scored[:k]
    maxs = max((r["similarity"] for r in scored), default=0.0)
    return top, maxs
