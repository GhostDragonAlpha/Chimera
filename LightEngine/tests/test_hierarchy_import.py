"""
Tests for the WordNet hierarchy importer.
"""

import json
import os

import pytest
from nltk.corpus import wordnet as wn

from LightEngine import hierarchy_import


@pytest.fixture(scope="module")
def imported_terms():
    """Run the importer once and cache the resulting term list."""
    terms, _ = hierarchy_import.import_hierarchy()
    return terms


def test_determinism(imported_terms):
    """Two runs must produce byte-identical JSON output."""
    terms2, _ = hierarchy_import.import_hierarchy()
    a = json.dumps(imported_terms, indent=2, ensure_ascii=False, sort_keys=True)
    b = json.dumps(terms2, indent=2, ensure_ascii=False, sort_keys=True)
    assert a == b


def test_parent_references_resolve_or_root(imported_terms):
    """Every parent string must name a term in the imported set, or term is root."""
    names = {t["term"] for t in imported_terms}
    for term in imported_terms:
        parents = term.get("parents", [])
        if not parents:
            assert term.get("root") is True, f"{term['term']} has no parents but is not root"
        for p in parents:
            assert p in names, f"{term['term']} references missing parent {p}"


def test_no_weapon_ancestry(imported_terms):
    """No imported synset may have weapon.n.01 in its hypernym ancestry."""
    weapon = wn.synset("weapon.n.01")
    for term in imported_terms:
        s = wn.synset(term["synset"])
        hypernyms = set(s.closure(lambda x: x.hypernyms()))
        assert weapon not in hypernyms, (
            f"{term['term']} ({term['synset']}) descends from weapon.n.01")


def _camel_words(name: str):
    """Split a camelCase/PascalCase name into component words."""
    words = []
    buf = []
    for ch in name:
        if ch.isupper() and buf:
            words.append("".join(buf))
            buf = [ch.lower()]
        else:
            buf.append(ch.lower())
    if buf:
        words.append("".join(buf))
    return words


def test_no_banned_substrings_in_term_names(imported_terms):
    """Term-name component words must not be weapon tokens (avoids substring
    false positives like 'Processing' -> 'gun')."""
    banned = {"weapon", "gun", "bomb"}
    for term in imported_terms:
        words = _camel_words(term["term"])
        for sub in banned:
            assert sub not in words, (
                f"term name '{term['term']}' contains banned word '{sub}'")


def test_hand_authored_hierarchy_untouched():
    """The importer must not overwrite docs/THE_HIERARCHY.md."""
    # tests/ -> LightEngine/ -> project root
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "docs", "THE_HIERARCHY.md")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "# THE HIERARCHY" in text
    assert "theElectron" in text


def test_output_file_written():
    """The JSON file is created and is valid."""
    assert os.path.exists(hierarchy_import.OUTPUT_PATH)
    with open(hierarchy_import.OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("term" in rec and "synset" in rec for rec in data)
