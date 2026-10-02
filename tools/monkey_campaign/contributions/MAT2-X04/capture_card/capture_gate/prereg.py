"""Card prereg binding (schema chimera.capture_gate.card_prereg.v1).

Campaign law: a card preregisters its view-spec BEFORE capture, and thresholds
are frozen in the spec. This module enforces the mechanical half of that law
at pipeline time, BEFORE a single frame is rendered:

1. The card prereg file must exist and validate (schema, card_id, both
   declared-before flags true, a law citation).
2. It must pin the view-spec identity exactly: spec_id, spec_version and the
   canonical prereg sha256 of the spec bytes the card will capture against.
3. Any mismatch is a refusal (PreregRefused) with machine problem codes; the
   pipeline never captures against an unpinned or mutated spec.

Registering the prereg file itself through the campaign prereg-commit law
remains the card owner's duty; every receipt records the prereg file's own
sha256 so the registered bytes are identifiable from the flow alone.
"""

import hashlib
import json
import os

from . import view_spec

PREREG_SCHEMA = "chimera.capture_gate.card_prereg.v1"

CARD_PREREG_FILENAME = "card_prereg.json"
VIEW_SPEC_FILENAME = "view_spec.json"


class PreregRefused(ValueError):
    """Raised when the card prereg does not pin the spec it claims."""


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def canonical_bytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def binding_problems(prereg, spec):
    """Return machine problem codes; empty list means the binding holds."""
    problems = []
    if not isinstance(prereg, dict):
        return ["prereg_not_an_object"]
    if prereg.get("schema") != PREREG_SCHEMA:
        problems.append("prereg_schema_must_be_" + PREREG_SCHEMA)
    if not isinstance(prereg.get("card_id"), str) or not prereg.get("card_id"):
        problems.append("prereg_card_id_required")
    if prereg.get("declared_before_run") is not True:
        problems.append("prereg_declared_before_run_must_be_true")
    if prereg.get("declared_before_capture") is not True:
        problems.append("prereg_declared_before_capture_must_be_true")
    if not isinstance(prereg.get("freeze_law_ref"), str) or not prereg.get("freeze_law_ref"):
        problems.append("prereg_freeze_law_ref_required")
    pin = prereg.get("view_spec")
    if not isinstance(pin, dict):
        problems.append("prereg_view_spec_pin_required")
        return problems
    if pin.get("spec_id") != spec.get("spec_id"):
        problems.append("prereg_spec_id_mismatch")
    if pin.get("spec_version") != spec.get("spec_version"):
        problems.append("prereg_spec_version_mismatch")
    pinned = pin.get("prereg_sha256")
    if not isinstance(pinned, str) or len(pinned) != 64:
        problems.append("prereg_sha256_pin_required")
    else:
        actual = view_spec.spec_prereg_sha256(spec)
        if pinned != actual:
            problems.append("prereg_spec_hash_mismatch")
    return problems


def check_prereg_stage(card_root, spec=None):
    """Load and verify the card prereg against its pinned spec.

    Returns (prereg, spec, binding) where binding carries the prereg file
    hash and the applied spec hash. Raises PreregRefused on any problem
    BEFORE capture. ``spec`` may be injected by tests (tamper cases).
    """
    prereg_path = os.path.join(card_root, CARD_PREREG_FILENAME)
    spec_path = os.path.join(card_root, VIEW_SPEC_FILENAME)
    if not os.path.isfile(prereg_path):
        raise PreregRefused("card_prereg_missing")
    if not os.path.isfile(spec_path):
        raise PreregRefused("card_view_spec_missing")
    if spec is None:
        spec = load_json(spec_path)
        problems = view_spec.validate_spec(spec)
        if problems:
            raise PreregRefused("card_view_spec_invalid:" + ";".join(problems))
    prereg = load_json(prereg_path)
    problems = binding_problems(prereg, spec)
    if problems:
        raise PreregRefused(";".join(problems))
    binding = {
        "prereg_file": CARD_PREREG_FILENAME,
        "prereg_file_sha256": sha256_file(prereg_path),
        "view_spec_file": VIEW_SPEC_FILENAME,
        "spec_id": spec["spec_id"],
        "spec_version": spec["spec_version"],
        "prereg_sha256": view_spec.spec_prereg_sha256(spec),
        "declared_before_run": True,
        "declared_before_capture": True,
    }
    return prereg, spec, binding
