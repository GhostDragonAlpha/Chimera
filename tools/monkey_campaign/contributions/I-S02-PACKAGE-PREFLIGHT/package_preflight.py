"""package_preflight.py -- I-S02: read-only structural preflight for a self-contained package.

Card I-S02-PACKAGE-PREFLIGHT, planning row S02: "Clean machine/user can launch without
repo paths, development Python or operator-installed tools beyond declared dependencies."
This module checks the STRUCTURAL half of that sentence from a caller-supplied manifest:

  * every declared file exists under the caller-supplied package root (P-MISSING);
  * every declared path is relative, drive/UNC-free and free of `..` (P-PATH);
  * no reparse point (junction/symlink) redirects an entry outside the root (P-JUNCTION);
  * declared size matches and no file exceeds the manifest's cap; hashing reads at most
    that cap (P-SIZE);
  * sha256 matches the declared digest (P-HASH);
  * declared text configs import only declared modules (P-DEP);
  * declared text configs reference only declared system executables (P-EXT-TOOL);
  * declared text configs contain no development-root paths (P-DEVROOT);
  * the manifest declares no duplicate entry (P-DUP) and text configs decode (P-TEXT).

OUT OF SCOPE, BY CONSTRUCTION (S01 is BLOCKED-FOR-SHIP on MorphoSource assets; nothing
here may bless around that): this checker makes NO distribution-rights decision of any
kind. Its entire verdict vocabulary is PREFLIGHT-PASS / PREFLIGHT-FAIL about structural
coherence. File roles are manifest facts, never graded. Asset licensing stays with S01's
recorded matrix; permission to distribute is a human decision this tool cannot express.

SCOPE LAWS (agents' PREREGISTRATION.md, frozen before this file was written): the package
root arrives only as a call argument; manifests carry no absolute paths; only entries
marked text_config are opened for content; hashing is byte-capped; no directory is ever
enumerated — only manifest-named paths are touched (stats["paths_opened"] proves it).
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

SCHEMA = "chimera.package.manifest.v1"
VERDICTS = ("PREFLIGHT-PASS", "PREFLIGHT-FAIL")

# Development roots a clean package must not name. DATA, not policy: the caller extends
# this list via manifest["dev_root_patterns"] (e.g. the build checkout that produced the
# package); defaults cover this fleet's known development locations, both slash styles.
DEFAULT_DEV_ROOT_PATTERNS = (
    "e:/pythonchimera",
    "e:\\pythonchimera",
    "e:/chimerawork",
    "e:\\chimerawork",
    "c:/vulkansdk",
    "c:\\vulkansdk",
    "c:\\python3",
    "c:/python3",
)

# Executables whose invocation inside a text config counts as depending on an
# operator-installed or OS tool; each must be declared in declared_dependencies.system.
SYSTEM_TOOL_WATCHLIST = ("powershell", "pwsh", "cmd", "wscript", "cscript", "mshta",
                         "python", "pythonw", "py", "pip", "bash", "sh")

_IMPORT_RE = re.compile(r"^\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import)",
                        re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    check: str          # P-MISSING | P-PATH | P-JUNCTION | P-SIZE | P-HASH | P-DEP
                        # | P-EXT-TOOL | P-DEVROOT | P-DUP | P-TEXT
    path: str           # relative manifest path (or "<manifest>") — never an absolute path
    detail: str


@dataclass
class PreflightResult:
    verdict: str
    findings: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def findings_json(self) -> str:
        import json
        return json.dumps([f.__dict__ for f in self.findings], sort_keys=True)


def _path_errors(rel: str) -> str | None:
    """Literal-path defects: absolute, drive-anchored, UNC, or `..` traversal."""
    if not isinstance(rel, str) or not rel:
        return "entry path must be a non-empty string"
    p = PurePosixPath(rel.replace("\\", "/"))
    if PurePosixPath(rel.replace("\\", "/")).is_absolute() or rel.startswith(("/", "\\")):
        return "absolute path"
    if re.match(r"^[A-Za-z]:", rel):
        return "drive-anchored path"
    if rel.replace("\\", "/").startswith("//"):
        return "UNC path"
    if ".." in p.parts:
        return "traversal segment '..'"
    return None


def _contained(resolved: Path, root_resolved: Path) -> bool:
    """True iff resolved sits inside root_resolved (both already resolved)."""
    try:
        resolved.relative_to(root_resolved)
        return True
    except ValueError:
        return False


def _iter_imports(text: str):
    for match in _IMPORT_RE.finditer(text):
        mod = match.group(1) or match.group(2)
        if mod:
            yield mod.split(".")[0]


def preflight(manifest: dict, package_root, dev_root_patterns=()) -> PreflightResult:
    """Run the structural preflight of `manifest` against the tree at `package_root`.

    `package_root` is the ONLY root this function ever touches; every other path comes
    from the manifest. Findings report relative paths so the result is invariant under
    relocation of the same package to a different root.
    """
    root = Path(package_root)
    root_resolved = root.resolve()
    findings: list[Finding] = []
    paths_opened: list[str] = []
    bytes_read: dict[str, int] = {}
    stdlib = set(getattr(sys, "stdlib_module_names", ()))

    if not isinstance(manifest, dict):
        return PreflightResult(VERDICTS[1], [Finding("P-MANIFEST", "<manifest>",
                                                     "manifest must be a JSON object")])
    if manifest.get("schema") != SCHEMA:
        findings.append(Finding("P-MANIFEST", "<manifest>",
                                f"expected schema {SCHEMA!r}, got {manifest.get('schema')!r}"))
    cap = manifest.get("max_file_bytes")
    if not isinstance(cap, int) or cap <= 0:
        cap = None
        findings.append(Finding("P-MANIFEST", "<manifest>",
                                "max_file_bytes must be a positive integer"))
    deps = manifest.get("declared_dependencies") or {}
    declared_modules = {m.split(".")[0] for m in (deps.get("modules") or [])}
    declared_system = {s.lower() for s in (deps.get("system") or [])}
    dev_patterns = tuple(dev_root_patterns) + tuple(DEFAULT_DEV_ROOT_PATTERNS)

    seen: dict[str, int] = {}
    for idx, entry in enumerate(manifest.get("entries") or []):
        rel = entry.get("path", "")
        where = rel or f"<entry[{idx}]>"
        seen[rel] = seen.get(rel, 0) + 1

        err = _path_errors(rel)
        if err:
            findings.append(Finding("P-PATH", where, err))
            continue
        if seen[rel] > 1:
            findings.append(Finding("P-DUP", where, f"declared {seen[rel]} times"))
            continue

        literal = root / Path(*PurePosixPath(rel.replace("\\", "/")).parts)
        resolved = literal.resolve()
        paths_opened.append(rel)
        if not _contained(resolved, root_resolved):
            # The literal path was clean, so something it traverses (a junction or
            # symlink) redirected it outside the root.
            findings.append(Finding(
                "P-JUNCTION", where,
                "reparse point redirects entry outside the package root"))
            continue
        if not resolved.exists():
            findings.append(Finding("P-MISSING", where, "declared file not found"))
            continue

        actual_size = resolved.stat().st_size
        declared_size = entry.get("bytes")
        if declared_size is not None and declared_size != actual_size:
            findings.append(Finding("P-SIZE", where,
                                    f"declared {declared_size} B, actual {actual_size} B"))
        if cap is not None and actual_size > cap:
            # Oversize is a finding; the digest of an oversize file is never verified
            # (verifying it would require an unbounded read).
            findings.append(Finding("P-SIZE", where,
                                    f"{actual_size} B exceeds max_file_bytes {cap} B"))
            with resolved.open("rb") as fh:
                bytes_read[rel] = len(fh.read(cap))
            continue

        digest = hashlib.sha256()
        with resolved.open("rb") as fh:
            chunk = fh.read(65536)
            total = 0
            while chunk:
                digest.update(chunk)
                total += len(chunk)
                chunk = fh.read(65536)
        bytes_read[rel] = total
        declared_sha = entry.get("sha256", "")
        if declared_sha and digest.hexdigest() != declared_sha:
            findings.append(Finding("P-HASH", where, "sha256 mismatch"))

        if entry.get("text_config"):
            try:
                text = resolved.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                findings.append(Finding("P-TEXT", where, "text_config not valid UTF-8"))
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                low = line.lower()
                for pat in dev_patterns:
                    if pat.lower() in low:
                        findings.append(Finding(
                            "P-DEVROOT", where,
                            f"line {lineno}: development-root reference {pat!r}"))
                        break
                for tool in SYSTEM_TOOL_WATCHLIST:
                    if re.search(rf"(?<![\w.]){re.escape(tool)}(\.exe)?(?![\w.])", low):
                        if tool not in declared_system:
                            findings.append(Finding(
                                "P-EXT-TOOL", where,
                                f"line {lineno}: system tool {tool!r} not declared"))
                        break
            if resolved.suffix == ".py":
                for mod in _iter_imports(text):
                    if mod not in declared_modules and mod not in stdlib:
                        findings.append(Finding("P-DEP", where,
                                                f"undeclared module import {mod!r}"))

    verdict = VERDICTS[0] if not findings else VERDICTS[1]
    return PreflightResult(verdict, findings,
                           {"paths_opened": paths_opened, "bytes_read": bytes_read})
