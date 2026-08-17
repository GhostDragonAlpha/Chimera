"""doc_lint.py -- the broken-pointer linter: a fact duplicated in prose drifts.

The project's own law: "a doc that duplicates a fact will drift from it, always." The
agent modes, AGENTS.md, and the workflow docs all name tools and files that have since
been renamed or deleted -- and nothing caught it. This is that catch, as code.

It scans documentation and config for references to files that do not exist on disk and
refuses them. Two surfaces:

  * Markdown files  -- both inline `path` tokens and `[..](link)` targets (resolved
                        relative to the doc, then the repo root).
  * .roomodes       -- every path-like token in each mode's fields, plus a structural
                        check (valid groups, valid YAML).

Modes:
  python tools/doc_lint.py                 # full repo scan; exit 1 if any broken pointer
  python tools/doc_lint.py --staged        # only references inside staged files
  python tools/doc_lint.py --docs          # docs only
  python tools/doc_lint.py --modes         # .roomodes only
  python tools/doc_lint.py --json          # machine-readable
  python tools/doc_lint.py --apply-allow   # (re)write .doclint.allow from current findings

An allowlist (.doclint.allow, newline substrings) suppresses known-intentional legacy
refs without hiding new ones.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOW = ROOT / ".doclint.allow"

ROOT_DIRS = (
    "tools", "Chimera", "ChimeraEngine", "docs", "core", "story", "LightEngine",
    "ParticleEngine", "WorldModel", "Construction", "web", "vendor", "Build",
    "Saved", "templates", "external", "models", "ChimeraShim", "ChimeraShim",
)
EXTS = ("py", "md", "json", "cmd", "ps1", "bat", "sh", "txt", "cfg", "toml",
        "yml", "yaml", "cpp", "h", "ini")

PATH_RE = re.compile(
    r"(?<![\w./\\-])(?:"
    + "|".join(re.escape(d) for d in ROOT_DIRS)
    + r")[\\/][\w.\-]+(?:[\\/][\w.\-]+)*\.(?:" + "|".join(EXTS) + r")"
)

MD_LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
YAML_AVAILABLE = True
try:
    import yaml  # type: ignore
except Exception:
    YAML_AVAILABLE = False


def _allow_patterns() -> list[str]:
    if not ALLOW.exists():
        return []
    return [ln.strip() for ln in ALLOW.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]


def _is_allowed(candidate: str, allow: list[str]) -> bool:
    return any(a in candidate for a in allow)


def _resolve(candidate: str) -> Path | None:
    cand = candidate
    if cand.startswith("./") or cand.startswith("../"):
        return None
    p = (ROOT / cand)
    if p.exists():
        return p
    if cand.startswith("core/"):
        alt = ROOT / "Chimera" / cand
        if alt.exists():
            return alt
    alt2 = ROOT / "Chimera" / cand
    if alt2.exists():
        return alt2
    return None


def _check_candidate(candidate: str, allow: list[str], broken: list[dict], src: Path) -> None:
    if candidate.startswith(("http://", "https://", "mailto:", "#")):
        return
    if _is_allowed(candidate, allow):
        return
    if _resolve(candidate) is None:
        broken.append({
            "file": src.relative_to(ROOT).as_posix(),
            "ref": candidate,
            "kind": "path",
        })


def scan_text(text: str, src: Path, allow: list[str], broken: list[dict]) -> None:
    for m in PATH_RE.finditer(text):
        _check_candidate(m.group(0), allow, broken, src)
    if src.suffix.lower() == ".md":
        for m in MD_LINK_RE.finditer(text):
            target = m.group(1)
            frag = target.split("#", 1)[0]
            if not frag or frag.startswith(("http://", "https://", "mailto:")):
                continue
            if _is_allowed(frag, allow):
                continue
            rel = (src.parent / frag)
            ok = rel.exists() or _resolve(frag) is not None
            if not ok:
                broken.append({
                    "file": src.relative_to(ROOT).as_posix(),
                    "ref": target,
                    "kind": "md-link",
                })


def scan_modes(allow: list[str], broken: list[dict], only_staged: bool = False) -> list[str]:
    issues: list[str] = []
    path = ROOT / ".roomodes"
    if not path.exists():
        issues.append(".roomodes: file not found")
        return issues
    if only_staged and not _is_staged(path):
        return issues
    if not YAML_AVAILABLE:
        issues.append(".roomodes: PyYAML not available -- cannot validate structure")
        raw = path.read_text(encoding="utf-8")
        scan_text(raw, path, allow, broken)
        return issues
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        issues.append(f".roomodes: YAML parse error: {e}")
        return issues
    if not isinstance(doc, dict) or "customModes" not in doc:
        issues.append(".roomodes: missing top-level 'customModes'")
        return issues
    modes = doc["customModes"]
    if not isinstance(modes, list):
        issues.append(".roomodes: 'customModes' is not a list")
        return issues
    valid_groups = {"read", "edit", "command", "browser", "mcp"}
    for mode in modes:
        if not isinstance(mode, dict):
            issues.append(".roomodes: a mode entry is not a mapping")
            continue
        slug = mode.get("slug", "<no-slug>")
        for field in ("slug", "name", "description", "roleDefinition", "whenToUse"):
            if field not in mode:
                issues.append(f".roomodes [{slug}]: missing '{field}'")
        groups = mode.get("groups")
        if not isinstance(groups, list):
            issues.append(f".roomodes [{slug}]: 'groups' is not a list")
        else:
            for g in groups:
                if isinstance(g, str):
                    if g not in valid_groups:
                        issues.append(f".roomodes [{slug}]: unknown group '{g}'")
                elif isinstance(g, list) and len(g) == 2 and g[0] == "edit":
                    spec = g[1]
                    if not isinstance(spec, dict) or "fileRegex" not in spec:
                        issues.append(f".roomodes [{slug}]: edit-with-regex missing 'fileRegex'")
                else:
                    issues.append(f".roomodes [{slug}]: malformed group entry {g!r}")
        blob = "\n".join(str(mode.get(f, "")) for f in
                         ("description", "roleDefinition", "whenToUse", "name"))
        scan_text(blob, path, allow, broken)
    return issues


def _staged_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                             capture_output=True, text=True, cwd=ROOT)
        return [ROOT / ln for ln in out.stdout.splitlines() if ln.strip()]
    except Exception:
        return []


def _is_staged(path: Path) -> bool:
    return path in set(_staged_files())


_MAX_BYTES = 1_000_000  # skip huge logs; they hold no method pointers worth scanning


def _iter_targets(only_docs: bool, only_modes: bool, staged: bool):
    if only_modes:
        return
    exts = (".md", ".py", ".json", ".roomodes", ".rst", ".txt", ".yaml", ".yml")
    if staged:
        for p in _staged_files():
            if p.suffix.lower() in exts and p.exists() and p.stat().st_size <= _MAX_BYTES:
                yield p
        return
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".ruff_cache",
            ".pytest_cache", "Build", "Saved", ".idea", ".vscode", ".claude", ".crush",
            ".pi", ".pi-subagents", "archive", ".tmp", "vendor", "models", "external",
            "web", "Screenshots", "clay_exports", "research_references", "templates"}
    for p in ROOT.rglob("*"):
        if any(part in skip for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in exts and p.stat().st_size <= _MAX_BYTES:
            yield p


def main() -> int:
    ap = argparse.ArgumentParser(description="broken-pointer linter for the method docs")
    ap.add_argument("--staged", action="store_true", help="only references in staged files")
    ap.add_argument("--docs", action="store_true", help="scan docs only")
    ap.add_argument("--modes", action="store_true", help="validate .roomodes only")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--apply-allow", action="store_true",
                    help="write .doclint.allow from current findings and exit 0")
    a = ap.parse_args()

    allow = _allow_patterns()
    broken: list[dict] = []
    mode_issues: list[str] = []

    if not a.modes:
        mode_issues = scan_modes(allow, broken, only_staged=a.staged)
    if not a.docs:
        for p in _iter_targets(a.docs, a.modes, a.staged):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scan_text(text, p, allow, broken)

    broken = [b for b in broken if not _is_allowed(b["ref"], allow)]

    if a.apply_allow:
        subs = sorted({b["ref"] for b in broken})
        ALLOW.write_text("\n".join(subs) + "\n", encoding="utf-8")
        print(f".doclint.allow written with {len(subs)} patterns")
        return 0

    if a.json:
        print(json.dumps({"broken": broken, "mode_issues": mode_issues}, indent=2))
    else:
        if broken:
            print(f"BROKEN POINTERS ({len(broken)}):")
            for b in broken:
                print(f"  {b['file']}: {b['ref']}  [{b['kind']}]")
        if mode_issues:
            print(f".roomodes ISSUES ({len(mode_issues)}):")
            for i in mode_issues:
                print(f"  {i}")
        if not broken and not mode_issues:
            print("doc_lint: clean -- no broken pointers, .roomodes valid.")

    return 1 if (broken or mode_issues) else 0


if __name__ == "__main__":
    sys.exit(main())
