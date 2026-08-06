"""
WordNet noun-hierarchy importer for the Chimera light-era term tree.

Per docs/THE_HIERARCHY.md's exclusion rule, this script imports only
non-dangerous physical concepts: objects, artifacts, substances, body parts,
plants, animals, food, phenomena, and processes.  Weapons, poisons, drugs, and
related injury-optimized structures are removed by ancestry and a substring
backstop.
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

from nltk.corpus import wordnet as wn
from nltk.corpus.reader.wordnet import WordNetError


# Physical lexnames selected for the light-era tree.
PHYSICAL_LEXNAMES = {
    "noun.object",
    "noun.artifact",
    "noun.substance",
    "noun.body",
    "noun.plant",
    "noun.animal",
    "noun.food",
    "noun.phenomenon",
    "noun.process",
}

# Exclusion roots: any descendant of these synsets is dropped.
EXCLUSION_ROOT_NAMES = [
    "weapon.n.01",
    "weaponry.n.01",
    "ammunition.n.01",
    "explosive.n.01",
    "poison.n.01",
    "drug.n.01",
]

# Substring backstop: drop synsets whose lemma names contain these tokens.
# This is a safety net *after* the ancestry filter; false positives are logged.
SUBSTRING_BANLIST = {
    "weapon", "gun", "rifle", "pistol", "sword", "dagger", "bomb",
    "missile", "torpedo", "bullet", "bayonet", "cudgel", "bludgeon",
    "knife", "machete", "axe", "hatchet", "spear", "lance", "arrow",
    "bow", "crossbow", "catapult", "cannon", "mortar", "grenade",
    "mine", "warhead", "poison", "venom", "toxin", "torture", "execution",
}

# Lemma names that are allowed if the synset is clearly a tool/implement.
REVIEWED_EXCEPTIONS = {"axe", "hatchet"}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "hierarchy_import")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "wordnet_terms.json")


def _camelize(lemma_name: str) -> str:
    """Turn a WordNet lemma like 'dog_foo' into 'DogFoo'."""
    parts = lemma_name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _build_exclusion_set(report: dict) -> Set:
    """Collect every descendant of the named exclusion roots."""
    excluded: Set = set()
    by_root: Dict[str, int] = {}
    lookup_errors: Dict[str, str] = {}

    for name in EXCLUSION_ROOT_NAMES:
        try:
            root = wn.synset(name)
        except WordNetError as exc:
            lookup_errors[name] = str(exc)
            continue
        descendants = set(root.closure(lambda s: s.hyponyms()))
        descendants.add(root)
        by_root[name] = len(descendants)
        excluded.update(descendants)

    report["exclusion_lookup_errors"] = lookup_errors
    report["exclusions_by_root"] = by_root
    report["total_excluded_by_ancestry"] = len(excluded)
    return excluded


def _tool_synsets() -> Set:
    """Synsets that mark a reviewed tool/implement exception."""
    tool_names = ["tool.n.01", "implement.n.01"]
    out = set()
    for name in tool_names:
        try:
            out.add(wn.synset(name))
        except WordNetError:
            pass
    return out


def _is_substring_drop(
    synset,
    tool_synsets: Set,
    reviewed_log: List[Tuple[str, str, str]],
    dropped_log: List[Tuple[str, str, str]],
) -> bool:
    """
    Apply the substring backstop.  Return True if the synset should be dropped.
    Logs reviewed exceptions (tool-belonging axe/hatchet) separately from drops.
    """
    matched: str | None = None
    for lemma in synset.lemma_names():
        # whole-word match: lemmas may be multiword tokens joined by '_'.
        # (Substring matching dropped mineral via 'mine', rainbow via 'bow',
        # bowel via 'bow', narrow via 'arrow' — ancestry is the real filter;
        # this backstop only needs whole-word precision.)
        tokens = lemma.lower().split("_")
        for sub in SUBSTRING_BANLIST:
            if sub in tokens:
                matched = sub
                break
        if matched:
            break

    if matched is None:
        return False

    # Reviewed exception: an axe/hatchet that is a tool stays in the tree.
    if any(lemma.lower() in REVIEWED_EXCEPTIONS for lemma in synset.lemma_names()):
        hypernyms = set(synset.closure(lambda s: s.hypernyms()))
        if tool_synsets & hypernyms:
            reviewed_log.append((synset.name(), ", ".join(synset.lemma_names()), matched))
            return False

    dropped_log.append((synset.name(), ", ".join(synset.lemma_names()), matched))
    return True


def _assign_term_names(synsets: List) -> Dict:
    """Deterministically map each synset to a unique camelized 'theXxx' name."""
    term_map: Dict = {}
    used: Set[str] = set()

    # Sort by synset name so collisions are resolved deterministically.
    for s in sorted(synsets, key=lambda x: x.name()):
        base = "the" + _camelize(s.lemma_names()[0])
        # Extract WordNet sense number, e.g. 'dog.n.01' -> '01'
        sense = s.name().split(".")[-1]
        candidates = [base, f"{base}{sense}"]
        # Rare further collisions get the full offset appended.
        if candidates[1] in used:
            candidates.append(f"{base}{sense}_{s.offset():08d}")
        for cand in candidates:
            if cand not in used:
                term_map[s] = cand
                used.add(cand)
                break
        else:
            # Should never happen, but fall back to a guaranteed-unique name.
            fallback = f"{base}_{s.offset():08d}"
            term_map[s] = fallback
            used.add(fallback)

    return term_map


def _body_sample_chains(imported: List[dict], term_by_synset: Dict[str, str]) -> List[str]:
    """Return short parent-chain strings for 10 noun.body terms."""
    body_terms = [t for t in imported if t["lexname"] == "noun.body"]
    body_terms.sort(key=lambda t: t["term"])
    lines = []
    for term in body_terms[:10]:
        chain = " -> ".join([term["term"]] + term.get("parents", []))
        lines.append(chain)
    return lines


def import_hierarchy() -> Tuple[List[dict], dict]:
    """Run the full import and return (terms, report)."""
    report: dict = {}

    # 1. Census all noun lexnames.
    lexname_counts = Counter(s.lexname() for s in wn.all_synsets("n"))
    report["lexname_census"] = dict(sorted(lexname_counts.items()))

    # 2. Physical-world candidates.
    physical_candidates = [
        s for s in wn.all_synsets("n") if s.lexname() in PHYSICAL_LEXNAMES
    ]
    report["physical_candidates"] = len(physical_candidates)

    # 3. Build exclusion set.
    excluded = _build_exclusion_set(report)
    after_exclusion = [s for s in physical_candidates if s not in excluded]

    # 4. Substring backstop.
    tool_synsets = _tool_synsets()
    reviewed: List[Tuple[str, str, str]] = []
    dropped: List[Tuple[str, str, str]] = []
    survivors = [
        s for s in after_exclusion
        if not _is_substring_drop(s, tool_synsets, reviewed, dropped)
    ]

    report["substring_reviewed_exceptions"] = reviewed
    report["substring_drops"] = dropped
    report["substring_drop_count"] = len(dropped)

    # 5. Assign unique term names.
    term_map = _assign_term_names(survivors)

    # 6. Build parent links and records.
    synset_to_term = {s.name(): name for s, name in term_map.items()}
    imported: List[dict] = []
    for s in survivors:
        parents = [
            synset_to_term[h.name()]
            for h in s.hypernyms()
            if h.name() in synset_to_term
        ]
        record = {
            "term": term_map[s],
            "synset": s.name(),
            "lexname": s.lexname(),
            "parents": parents,
            "definition": s.definition(),
        }
        if not parents:
            record["root"] = True
        imported.append(record)

    imported.sort(key=lambda r: r["term"])

    # 7. Report summary.
    report["imported_count"] = len(imported)
    report["root_count"] = sum(1 for r in imported if r.get("root"))
    report["counts_by_lexname"] = dict(sorted(Counter(
        r["lexname"] for r in imported).items()))
    report["body_sample_chains"] = _body_sample_chains(imported, synset_to_term)

    return imported, report


def main():
    terms, report = import_hierarchy()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(terms, f, indent=2, ensure_ascii=False, sort_keys=True)

    print("=" * 60)
    print("WordNet noun lexname census:")
    for lexname, count in report["lexname_census"].items():
        marker = "  <-- physical" if lexname in PHYSICAL_LEXNAMES else ""
        print(f"  {lexname:20s} {count:6d}{marker}")
    print("=" * 60)
    print(f"Physical candidates: {report['physical_candidates']}")
    print(f"Excluded by ancestry: {report['total_excluded_by_ancestry']}")
    print("Exclusions by root:")
    for name, cnt in report["exclusions_by_root"].items():
        print(f"  {name:20s} {cnt:6d}")
    if report["exclusion_lookup_errors"]:
        print("Lookup errors (expected for absent senses):")
        for name, err in report["exclusion_lookup_errors"].items():
            print(f"  {name}: {err}")
    print(f"Substring backstop drops: {report['substring_drop_count']}")
    for synset, lemmas, sub in report["substring_drops"]:
        print(f"  - {synset} ({lemmas}) matched '{sub}'")
    print(f"Reviewed exceptions kept: {len(report['substring_reviewed_exceptions'])}")
    for synset, lemmas, sub in report["substring_reviewed_exceptions"]:
        print(f"  + {synset} ({lemmas}) matched '{sub}' but is a tool")
    print("-" * 60)
    print(f"Imported terms: {report['imported_count']}")
    print(f"Root terms: {report['root_count']}")
    print("Counts by lexname:")
    for lexname, count in report["counts_by_lexname"].items():
        print(f"  {lexname:20s} {count:6d}")
    print("-" * 60)
    print("10 noun.body sample chains:")
    for chain in report["body_sample_chains"]:
        print(f"  {chain}")
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
