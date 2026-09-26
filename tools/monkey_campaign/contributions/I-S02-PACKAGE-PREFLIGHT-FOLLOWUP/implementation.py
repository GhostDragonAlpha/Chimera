"""implementation.py -- I-S02-PACKAGE-PREFLIGHT-FOLLOWUP: manifest producer/adapter.

Connects the CURRENT packager entry point (the R1 double-click launch lane
``DEMO.bat`` -> ``tools/run_demo.ps1`` -> ``ChimeraEngine/gallery.py`` at PR base
``astra/gait-capture`` @ ``5e54c0b7``) to the WINNING package preflight checker
(card ``I-S02-PACKAGE-PREFLIGHT``, PR #153 head ``e0a0abc8``), which is vendored
here BYTE-PINNED at ``reference/package_preflight__e0a0abc8.py``:

    11458 bytes, sha256 1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2

The pinned checker consumes a ``chimera.package.manifest.v1`` manifest that nobody
produced on this lineage -- the winning report's integration proposal names "the
builder emits chimera.package.manifest.v1 next to the package" as future work. This
module is that producer, as an ADAPTER over the packager's ACTUAL declared inputs:

  * ``DEMO_LANE_INPUTS`` names the launcher lane's real files with their frozen
    byte identities at the pinned base (packager FACTS, not admission decisions);
  * ``produce_manifest`` turns an EXTERNAL admission record (every row carries a
    ``role`` and an ``admission_ref`` pointing at an external license/admission
    decision) into a canonical, relocation-invariant manifest: package-relative
    forward-slash paths, actual byte sizes, sha256 of bounded reads;
  * ``audit_staging`` names undeclared leftovers (``STAGE-UNDECLARED``) and missing
    declared assets (``STAGE-MISSING``) in a staged tree before publication;
  * ``run_preflight`` routes ALL checking through the PINNED module (no verdict of
    this module's own is ever issued).

LAWS (PREREGISTRATION.md, frozen before this file was written):
  * license/admission decisions are EXPLICIT and EXTERNAL -- a row without an
    ``admission_ref`` refuses ``ADMISSION-INCOMPLETE``; an unapproved asset
    structurally cannot enter the manifest because declaration is admission-driven
    and the producer never enumerates to declare;
  * ALL-OR-NOTHING: any refusal -> ``MANIFEST-REFUSED`` with ``manifest is None``;
  * manifests carry no absolute path, no source-root reference, no timestamp;
  * the only PASS/FAIL vocabulary in the system belongs to the pinned checker
    (``PREFLIGHT-PASS``/``PREFLIGHT-FAIL``, structural coherence only). This
    producer emits ``MANIFEST-PRODUCED``/``MANIFEST-REFUSED`` + refusal codes and
    can never express a distribution-permission decision.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# --- pinned dependency (byte-pin discipline) ---------------------------------

#: Contribution-local directory of THIS file (the checkout contribution dir).
_HERE = Path(__file__).resolve().parent

#: The vendored winning checker (byte-pinned to PR #153 head e0a0abc8).
REFERENCE_REL = "reference/package_preflight__e0a0abc8.py"

#: Frozen identity of the vendored bytes (see PREREGISTRATION.md section 1).
REFERENCE_SHA256 = "1f81f62e3ad1b7030fd2d1de7d6d932bbdf323b8533c89c36e462bf29e246ba2"
REFERENCE_BYTES = 11458

_pinned = None  # cached pinned module after successful verification


class AdapterRefusal(ValueError):
    """A named, deterministic refusal. ``code`` is a stable machine id."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(detail or code)


def load_pinned_preflight(reference_path=None):
    """Return the PINNED ``package_preflight`` module, byte-verified.

    Every load re-hashes the vendored file and refuses ``PIN-MISMATCH`` unless the
    bytes are exactly the frozen #153-head bytes. The module is loaded under a
    private name so it can never be shadowed by an import on ``sys.path``.
    """
    global _pinned
    if _pinned is not None and reference_path is None:
        return _pinned
    path = Path(reference_path) if reference_path is not None else _HERE / REFERENCE_REL
    data = path.read_bytes()  # noqa: PinVerification reads only contribution-owned bytes
    digest = hashlib.sha256(data).hexdigest()
    if digest != REFERENCE_SHA256 or len(data) != REFERENCE_BYTES:
        raise AdapterRefusal(
            "PIN-MISMATCH",
            f"{path.name}: sha256 {digest} / {len(data)} B does not match the frozen "
            f"#153 pin {REFERENCE_SHA256} / {REFERENCE_BYTES} B",
        )
    spec = importlib.util.spec_from_file_location(
        "chimera_i_s02_pinned_package_preflight_e0a0abc8", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if reference_path is None:
        _pinned = module
    return module


# --- the packager lane's actual declared inputs (frozen packager FACTS) ------

#: PR base of this lineage: ``astra/gait-capture`` @ 5e54c0b7 (also the base of the
#: winning PR #153). Every identity below was read with read-only ``git show``.
PACKAGER_BASE_REF = "astra/gait-capture@5e54c0b7"

#: The R1 double-click launch chain, as its own bytes declare it:
#: DEMO.bat -> tools/run_demo.ps1 -> ChimeraEngine/gallery.py (gallery.html served;
#: splat_appearance imported; live_viewer imported opportunistically).
DEMO_LANE_INPUTS = (
    {"path": "DEMO.bat", "role": "launcher", "bytes": 250,
     "sha256": "92cbcceca31a80a52e189659a3c613c03dece695ed2fd8bf7654a6b41f4df690"},
    {"path": "tools/run_demo.ps1", "role": "launcher", "bytes": 3605,
     "sha256": "6b12c3f7dbc6ec5d9f42b927f42f002eb5eb58169f661db3ee4333fc000eb089"},
    {"path": "ChimeraEngine/gallery.py", "role": "runtime", "bytes": 7353,
     "sha256": "8a326949b81175274109492e2200edd6bdab2f6cffba1dc45a723fe7103fd12a"},
    {"path": "ChimeraEngine/gallery.html", "role": "runtime", "bytes": 3187,
     "sha256": "5640c54f4539a548c56a1befaa31e0be504353e2c6eb75b2c406c480d730c6e2"},
    {"path": "ChimeraEngine/splat_appearance.py", "role": "runtime", "bytes": 33275,
     "sha256": "3fa559e46d6d93584892c694400683286a22f43c7a1343a8016bd996ed67869e"},
    {"path": "ChimeraEngine/live_viewer.py", "role": "runtime", "bytes": 122566,
     "sha256": "4a223b7d4dd3bf1c154ccdee2f0ce9bbda33e0953eab7ef25b8e6a0494f61adb"},
)

#: Text files a caller would typically mark ``text_config`` (the launcher lane's
#: scripts). DATA, not policy: the caller decides per admission row.
DEMO_LANE_TEXT_CONFIGS = ("DEMO.bat", "tools/run_demo.ps1",
                          "ChimeraEngine/gallery.py", "ChimeraEngine/splat_appearance.py",
                          "ChimeraEngine/live_viewer.py")

#: Honest boundary (PREREGISTRATION.md section 2): the OPTIONAL live_viewer import
#: closure reaches the whole engine. Recorded so no caller mistakes the demo-lane
#: list above for the complete runtime closure; the full closure is future S02
#: builder work.
KNOWN_OPEN_CLOSURE_MODULES = ("ParticleEngine", "matter", "theHuman", "walker", "one",
                              "lod", "perf_guard", "controller", "touchables",
                              "human_messenger", "numpy", "PIL")

#: Manifest schema -- used verbatim from the pinned checker, never redefined here.
SCHEMA = load_pinned_preflight().SCHEMA

# --- producer verdict vocabulary (NO permission semantics) -------------------

PRODUCED = "MANIFEST-PRODUCED"
REFUSED = "MANIFEST-REFUSED"

#: Refusal codes (machine ids, frozen in PREREGISTRATION.md section 3):
#:   ADMISSION-MALFORMED   admission record lacks source/entries
#:   ADMISSION-INCOMPLETE  admission row missing path/role/decision_ref
#:   PRODUCER-DUP          same path admitted twice
#:   PRODUCER-PATH         absolute / drive-anchored / UNC / '..' segment
#:   SOURCE-MISSING        admitted file absent at package_root
#:   SOURCE-NOT-FILE       admitted path is not a regular file
#:   PRODUCER-OVERSIZE     admitted file exceeds max_file_bytes (bounded-read law)
#:   PRODUCER-TEXT         text_config row does not decode as UTF-8
#:   PRODUCER-DEPS         declared_dependencies not a dict of lists of str
#:   PIN-MISMATCH          vendored checker bytes drift from the frozen pin


@dataclass(frozen=True)
class ManifestProduction:
    """Outcome of ``produce_manifest``. Exactly one of manifest/refusals is set."""

    verdict: str                       # MANIFEST-PRODUCED | MANIFEST-REFUSED
    manifest: dict | None
    refusals: tuple = ()
    stats: dict = field(default_factory=dict)

    def canonical_json(self) -> bytes:
        """Canonical manifest bytes (sort_keys, indent=2, ASCII, LF-terminated)."""
        return _canonical_bytes(self.manifest)

    def refusals_json(self) -> str:
        return json.dumps([{"code": c, "path": p, "detail": d}
                           for c, p, d in self.refusals], sort_keys=True)


def _canonical_bytes(manifest: dict) -> bytes:
    return (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True)
            + "\n").encode("ascii")


def _path_defect(rel) -> str | None:
    """Literal-path defects a manifest entry must never carry (relative-only law)."""
    if not isinstance(rel, str) or not rel:
        return "entry path must be a non-empty string"
    if "\\" in rel:
        return "path must use forward slashes (package-relative posix form)"
    posix = PurePosixPath(rel)
    if posix.is_absolute() or rel.startswith("/"):
        return "absolute path"
    if re.match(r"^[A-Za-z]:", rel):
        return "drive-anchored path"
    if rel.startswith("//"):
        return "UNC path"
    if ".." in posix.parts:
        return "traversal segment '..'"
    if "." in posix.parts or posix.parts and posix.parts[0] == "":
        return "empty path segment"
    return None


def _deps_errors(declared_dependencies) -> str | None:
    if declared_dependencies is None:
        return None
    if not isinstance(declared_dependencies, dict):
        return "declared_dependencies must be a dict"
    for key in ("modules", "system"):
        val = declared_dependencies.get(key, [])
        if not isinstance(val, list) or any(not isinstance(m, str) for m in val):
            return f"declared_dependencies.{key} must be a list of strings"
    extra = set(declared_dependencies) - {"modules", "system", "python"}
    if extra:
        return f"undeclared declared_dependencies keys: {sorted(extra)}"
    return None


def produce_manifest(package_root, admission, *, package_name: str,
                     max_file_bytes: int = 1048576,
                     declared_dependencies=None,
                     extra_dev_root_patterns=()) -> ManifestProduction:
    """Produce a ``chimera.package.manifest.v1`` from an EXTERNAL admission record.

    ``package_root`` is the staged tree the manifest describes (the only root this
    function touches). ``admission`` is the external decision record::

        {"source": "<external decision id, e.g. s01-matrix@<rev>+operator-2026-09-24>",
         "entries": [{"path": "DEMO.bat", "role": "launcher", "text_config": true,
                      "decision_ref": "<external row/decision id>"}, ...]}

    Declaration is admission-driven: the producer NEVER enumerates the tree to
    decide content, so an unapproved asset structurally cannot enter the manifest.
    Any refusal fails the whole production (ALL-OR-NOTHING). No absolute path,
    source-root reference or timestamp ever enters the manifest.
    """
    refusals: list[tuple[str, str, str]] = []

    if not isinstance(admission, dict) or "source" not in admission or \
            not isinstance(admission.get("entries"), list):
        return ManifestProduction(REFUSED, None,
                                  (("ADMISSION-MALFORMED", "<admission>",
                                    "admission record needs a 'source' string and an "
                                    "'entries' list"),),
                                  {"entries_declared": 0})
    source = admission.get("source")
    if not isinstance(source, str) or not source.strip():
        return ManifestProduction(REFUSED, None,
                                  (("ADMISSION-MALFORMED", "<admission>",
                                    "admission 'source' must name the external "
                                    "decision record"),),
                                  {"entries_declared": 0})
    dep_err = _deps_errors(declared_dependencies)
    if dep_err:
        return ManifestProduction(REFUSED, None,
                                  (("PRODUCER-DEPS", "<manifest>", dep_err),),
                                  {"entries_declared": 0})
    if not isinstance(max_file_bytes, int) or max_file_bytes <= 0:
        return ManifestProduction(REFUSED, None,
                                  (("PRODUCER-OVERSIZE", "<manifest>",
                                    "max_file_bytes must be a positive integer"),),
                                  {"entries_declared": 0})

    root = Path(package_root)
    entries = []
    seen = set()
    bytes_hashed = 0
    for idx, row in enumerate(admission["entries"]):
        where = f"<admission[{idx}]>"
        if not isinstance(row, dict):
            refusals.append(("ADMISSION-INCOMPLETE", where, "row must be an object"))
            continue
        rel = row.get("path")
        role = row.get("role")
        decision_ref = row.get("decision_ref")
        if not isinstance(rel, str) or not rel:
            refusals.append(("ADMISSION-INCOMPLETE", where, "missing 'path'"))
            continue
        if not isinstance(role, str) or not role:
            refusals.append(("ADMISSION-INCOMPLETE", rel, "missing 'role'"))
            continue
        if not isinstance(decision_ref, str) or not decision_ref:
            refusals.append(("ADMISSION-INCOMPLETE", rel,
                             "missing 'decision_ref' (external license/admission "
                             "decision is REQUIRED and EXTERNAL)"))
            continue
        defect = _path_defect(rel)
        if defect:
            refusals.append(("PRODUCER-PATH", rel, defect))
            continue
        if rel in seen:
            refusals.append(("PRODUCER-DUP", rel, "admitted twice"))
            continue
        seen.add(rel)

        literal = root / Path(*PurePosixPath(rel).parts)
        if not literal.exists():
            refusals.append(("SOURCE-MISSING", rel,
                             "admitted file not found at package_root"))
            continue
        if not literal.is_file():
            refusals.append(("SOURCE-NOT-FILE", rel, "not a regular file"))
            continue
        size = literal.stat().st_size
        if size > max_file_bytes:
            refusals.append(("PRODUCER-OVERSIZE", rel,
                             f"{size} B exceeds max_file_bytes {max_file_bytes} B"))
            continue
        data = literal.read_bytes()[:max_file_bytes]  # bounded read (mirrors checker)
        digest = hashlib.sha256(data).hexdigest()
        text_config = bool(row.get("text_config", False))
        if text_config:
            try:
                data.decode("utf-8")
            except UnicodeDecodeError:
                refusals.append(("PRODUCER-TEXT", rel,
                                 "text_config row does not decode as UTF-8"))
                continue
        entries.append({
            "path": rel,
            "bytes": size,
            "sha256": digest,
            "text_config": text_config,
            "role": role,
            "admission_ref": decision_ref,
        })
        bytes_hashed += size

    if refusals:
        return ManifestProduction(REFUSED, None, tuple(refusals),
                                  {"entries_declared": len(entries),
                                   "bytes_hashed": bytes_hashed})

    pinned = load_pinned_preflight()
    manifest = {
        "schema": pinned.SCHEMA,
        "package_name": str(package_name),
        "max_file_bytes": max_file_bytes,
        "declared_dependencies": dict(declared_dependencies or {"modules": [], "system": []}),
        "dev_root_patterns": list(extra_dev_root_patterns),
        "admission": {
            "source": source,
            "decision_policy": "external; this manifest records refs, never verdicts",
        },
        "entries": entries,
    }
    return ManifestProduction(PRODUCED, manifest, (),
                              {"entries_declared": len(entries),
                               "bytes_hashed": bytes_hashed,
                               "canonical_bytes": len(_canonical_bytes(manifest))})


# --- staging audit (the one enumerating step; builder-side, pre-publication) --

@dataclass(frozen=True)
class StageFinding:
    check: str   # STAGE-UNDECLARED | STAGE-MISSING | STAGE-NOT-FILE
    path: str    # package-relative posix path
    detail: str


@dataclass
class StagingAudit:
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def findings_json(self) -> str:
        return json.dumps([f.__dict__ for f in self.findings], sort_keys=True)


def audit_staging(package_root, manifest: dict) -> StagingAudit:
    """Name every staged file no manifest entry declares, and vice versa.

    This is the PRODUCER-side completeness audit for the builder's workspace: the
    pinned checker never enumerates, so leftover development artifacts (logs,
    ``__pycache__``, editor droppings, unapproved assets) would otherwise ship
    silently. Findings are deterministic (sorted by check, then path).
    """
    root = Path(package_root)
    audit = StagingAudit()
    declared = {}
    for entry in manifest.get("entries", []):
        rel = entry.get("path", "")
        declared[rel] = entry

    files_on_disk = set()
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            if path.is_file():
                files_on_disk.add(path.relative_to(root).as_posix())
        audit.stats["files_seen"] = len(files_on_disk)
    else:
        audit.stats["files_seen"] = 0
        audit.findings.append(StageFinding(
            "STAGE-MISSING", "<package_root>", "package root is not a directory"))

    for rel in sorted(files_on_disk - set(declared)):
        audit.findings.append(StageFinding(
            "STAGE-UNDECLARED", rel,
            "staged file no manifest entry declares (undeclared development path "
            "or unapproved asset -- it must not ship)"))
    for rel in sorted(declared):
        literal = root / Path(*PurePosixPath(rel).parts)
        if not literal.exists():
            audit.findings.append(StageFinding(
                "STAGE-MISSING", rel, "declared entry absent from the staged tree"))
        elif not literal.is_file():
            audit.findings.append(StageFinding(
                "STAGE-NOT-FILE", rel, "declared path is not a regular file"))
    audit.findings.sort(key=lambda f: (f.check, f.path))
    return audit


# --- connective tissue to the PINNED checker ---------------------------------

def run_preflight(package_root, manifest: dict):
    """Run the PINNED checker on this manifest, passing back its result unchanged.

    ``dev_root_patterns`` recorded by ``produce_manifest`` are handed to the
    checker's own argument (the manifest key is documentation; the checker reads
    the function argument). The adapter adds NO verdict of its own.
    """
    pinned = load_pinned_preflight()
    return pinned.preflight(manifest, package_root,
                            dev_root_patterns=tuple(manifest.get("dev_root_patterns", ())))
