"""Grounded research with machine-checkable citations.

The premise: agents skip research because skipping is free, and they fabricate
research because fabricating is also free. Neither is fixable by asking nicely.

This module makes a *claim* worthless unless it carries a *citation*, and makes
a citation worthless unless it *re-verifies* against a source the agent did not
write. Verification runs without the agent present and without its cooperation.

Three source tiers, cheapest first:

    1. engine  — UE 5.8 source on local disk.  Authoritative. Free. Instant.
    2. repo    — this project's own tree.      Free.
    3. web     — Playwright + local Chromium.  Free (no search API).

Synthesis, when needed, runs on LM Studio (localhost:1234). Also free.

A citation is not a URL. A citation is a *reproducible read*:

    engine/repo : path + line + the exact text expected at that line
    web         : url + sha256 of the fetched body + the exact quote

`verify()` performs the read again and returns False on any drift. A research
record whose citations do not all verify is not research. It is prose.

CLI
    python -m core.research symbol Crouch --scope engine
    python -m core.research ask "How does UE5.8 apply crouch half-height?"
    python -m core.research verify docs/research/<id>.json
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Iterator, Sequence

# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

ENGINE_ROOT = Path(os.environ.get("UE_ENGINE_ROOT", r"C:\Program Files\Epic Games\UE_5.8"))
ENGINE_SOURCE = ENGINE_ROOT / "Engine" / "Source"
REPO_ROOT = Path(__file__).resolve().parent.parent

RESEARCH_DIR = REPO_ROOT / "docs" / "research"
SNAPSHOT_DIR = RESEARCH_DIR / "snapshots"

LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1")

# Searching the whole engine is slow and mostly noise. These subtrees hold the
# gameplay framework the project actually links against.
ENGINE_SUBTREES: tuple[str, ...] = (
    r"Runtime\Engine\Classes\GameFramework",
    r"Runtime\Engine\Classes\Components",
    r"Runtime\Engine\Private\Components",
    r"Runtime\Engine\Private\GameFramework",
    r"Runtime\Engine\Classes\Engine",
    r"Runtime\EnhancedInput",
    r"Runtime\NavigationSystem",
)

SOURCE_SUFFIXES = frozenset({".h", ".cpp", ".inl", ".cs"})


class ResearchError(Exception):
    pass


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------


@dataclass
class Citation:
    """A reproducible read of a source that the agent did not author.

    `verify()` re-performs the read. It does not trust any stored text except
    as the thing to compare against. Drift, deletion, or fabrication all fail.
    """

    kind: str  # "engine" | "repo" | "web"
    locator: str  # absolute path, or url
    quote: str  # exact text that must be found
    line: int | None = None  # 1-indexed, for file kinds
    sha256: str | None = None  # of the fetched body, for web kind
    fetched_at: str | None = None

    # -- verification --------------------------------------------------------

    def verify(self) -> tuple[bool, str]:
        if self.kind in ("engine", "repo"):
            return self._verify_file()
        if self.kind == "web":
            return self._verify_web()
        return False, f"unknown citation kind {self.kind!r}"

    def _verify_file(self) -> tuple[bool, str]:
        path = Path(self.locator)
        if not path.is_file():
            return False, f"no such file: {path}"
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            return False, f"unreadable: {exc}"

        if self.line is None:
            hit = any(self.quote in ln for ln in lines)
            return (True, "quote present") if hit else (False, "quote absent from file")

        if not (1 <= self.line <= len(lines)):
            return False, f"line {self.line} out of range (file has {len(lines)})"

        actual = lines[self.line - 1]
        if self.quote.strip() in actual:
            return True, "exact"

        # Tolerate small edits: search a window before declaring drift, and say
        # so explicitly rather than silently passing.
        lo, hi = max(0, self.line - 6), min(len(lines), self.line + 5)
        for offset in range(lo, hi):
            if self.quote.strip() in lines[offset]:
                return False, f"drifted: quote now at line {offset + 1}, cited {self.line}"
        return False, "quote not at cited line, nor within +/-5"

    def _verify_web(self) -> tuple[bool, str]:
        snap = SNAPSHOT_DIR / f"{self.sha256}.txt" if self.sha256 else None
        if snap and snap.is_file():
            body = snap.read_text(encoding="utf-8", errors="replace")
            if hashlib.sha256(body.encode("utf-8")).hexdigest() != self.sha256:
                return False, "snapshot content does not match its own sha256"
            if self.quote not in body:
                return False, "quote absent from snapshot"
            return True, "verified against local snapshot"
        return False, "no snapshot on disk; cannot verify without refetch"


# ---------------------------------------------------------------------------
# Tier 1 — engine source (free, authoritative, instant)
# ---------------------------------------------------------------------------


def _iter_source_files(roots: Iterable[Path]) -> Iterator[Path]:
    for root in roots:
        if not root.is_dir():
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in filenames:
                if Path(name).suffix in SOURCE_SUFFIXES:
                    yield Path(dirpath) / name


def _ripgrep(pattern: str, roots: Sequence[Path], max_hits: int) -> list[Citation] | None:
    """Use ripgrep when available. Returns None if rg is not on PATH."""
    globs: list[str] = []
    for suffix in sorted(SOURCE_SUFFIXES):
        globs += ["-g", f"*{suffix}"]
    cmd = ["rg", "--no-heading", "--line-number", "--color", "never",
           "-m", str(max_hits), *globs, pattern, *[str(r) for r in roots]]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                              encoding="utf-8", errors="replace")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode not in (0, 1):  # 1 == no matches, which is a real answer
        return None

    out: list[Citation] = []
    for raw in proc.stdout.splitlines():
        # rg on Windows emits  C:\path\file.h:123:text
        m = re.match(r"^(.*?):(\d+):(.*)$", raw)
        if not m:
            continue
        path, line, text = m.group(1), int(m.group(2)), m.group(3)
        out.append(Citation(kind="engine", locator=path, line=line, quote=text.strip()))
        if len(out) >= max_hits:
            break
    return out


def _python_grep(pattern: str, roots: Sequence[Path], max_hits: int) -> list[Citation]:
    rx = re.compile(pattern)
    out: list[Citation] = []
    for path in _iter_source_files(roots):
        try:
            with path.open("r", encoding="utf-8", errors="replace") as fh:
                for lineno, text in enumerate(fh, start=1):
                    if rx.search(text):
                        out.append(Citation(kind="engine", locator=str(path),
                                            line=lineno, quote=text.strip()))
                        if len(out) >= max_hits:
                            return out
        except OSError:
            continue
    return out


def search_engine(pattern: str, max_hits: int = 40,
                  subtrees: Sequence[str] = ENGINE_SUBTREES) -> list[Citation]:
    """Search UE engine source. Every hit comes back as a verifiable citation."""
    if not ENGINE_SOURCE.is_dir():
        raise ResearchError(
            f"engine source not found at {ENGINE_SOURCE}. "
            f"Set UE_ENGINE_ROOT, or install the engine source component."
        )
    roots = [ENGINE_SOURCE / s for s in subtrees]
    hits = _ripgrep(pattern, roots, max_hits)
    if hits is None:
        hits = _python_grep(pattern, roots, max_hits)
    return hits


def search_repo(pattern: str, max_hits: int = 40) -> list[Citation]:
    roots = [REPO_ROOT / "Source", REPO_ROOT / "core"]
    hits = _ripgrep(pattern, roots, max_hits) or _python_grep(pattern, roots, max_hits)
    for h in hits:
        h.kind = "repo"
    return hits


# ---------------------------------------------------------------------------
# Tier 3 — web via local Chromium (free; no search API key)
# ---------------------------------------------------------------------------


def _snapshot(body: str) -> str:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    (SNAPSHOT_DIR / f"{digest}.txt").write_text(body, encoding="utf-8")
    return digest


def web_fetch(urls: Sequence[str], timeout_ms: int = 20_000) -> list[tuple[str, str, str]]:
    """Fetch pages with local headless Chromium.

    Returns (url, sha256, text). Every body is snapshotted to disk so that any
    quote taken from it can be re-verified later without touching the network.
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise ResearchError("playwright not installed: pip install playwright") from exc

    results: list[tuple[str, str, str]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        ))
        try:
            for url in urls:
                try:
                    page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                    page.wait_for_timeout(400)
                    text = page.evaluate(
                        "() => { for (const s of document.querySelectorAll("
                        "'script,style,nav,footer,header')) s.remove();"
                        " return document.body ? document.body.innerText : ''; }"
                    )
                except Exception as exc:  # noqa: BLE001 — one bad page must not kill the run
                    print(f"  [web] FAILED {url}: {type(exc).__name__}", file=sys.stderr)
                    continue
                text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
                if not text:
                    continue
                results.append((url, _snapshot(text), text))
        finally:
            browser.close()
    return results


_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


def web_search(query: str, k: int = 5) -> list[str]:
    """Result URLs from a search engine that actually answers a headless browser.

    Measured 2026-07-10, headless chromium, realistic UA:

        startpage   200  a.result-link = 10   <- used
        bing        200  li.b_algo = 10 (requires wait_until="networkidle")
        ddg-lite    403  blocked
        ddg-html    403  blocked              <- what this function used to hit
        mojeek      200  "Captcha"
        marginalia  502

    Raises rather than returning [] on total failure. An empty list is
    indistinguishable from "researched and found nothing", and that ambiguity is
    exactly how unresearched work gets graded as researched.
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        raise ResearchError("playwright not installed: pip install playwright") from exc

    urls: list[str] = []
    tried: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(user_agent=_UA, locale="en-US")
        try:
            try:
                page.goto(
                    "https://www.startpage.com/sp/search?query=" + urllib.parse.quote(query),
                    timeout=25_000,
                    wait_until="domcontentloaded",
                )
                page.wait_for_timeout(700)
                for a in page.query_selector_all("a.result-link"):
                    href = a.get_attribute("href")
                    if href and href.startswith("http"):
                        urls.append(href)
                    if len(urls) >= k:
                        break
                if not urls:
                    tried.append("startpage: 0 results")
            except Exception as exc:  # noqa: BLE001
                tried.append(f"startpage: {type(exc).__name__}")

            if not urls:  # fallback: bing, which needs the JS to settle
                try:
                    page.goto(
                        "https://www.bing.com/search?q=" + urllib.parse.quote(query),
                        timeout=25_000,
                        wait_until="networkidle",
                    )
                    for a in page.query_selector_all("li.b_algo h2 a"):
                        href = a.get_attribute("href")
                        if href:
                            urls.append(_unwrap_bing(href))
                        if len(urls) >= k:
                            break
                    if not urls:
                        tried.append("bing: 0 results")
                except Exception as exc:  # noqa: BLE001
                    tried.append(f"bing: {type(exc).__name__}")
        finally:
            browser.close()

    if not urls:
        raise ResearchError(
            f"web_search found nothing for {query!r}; every backend failed: "
            + "; ".join(tried)
            + ". The search did not happen — do not proceed as if it did."
        )
    return urls


def _unwrap_bing(href: str) -> str:
    """Bing wraps hits in /ck/a?...&u=a1<base64url>. Recover the real target."""
    try:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
        raw = q.get("u", [""])[0]
        if not raw.startswith("a1"):
            return href
        pad = "=" * (-len(raw[2:]) % 4)
        decoded = base64.urlsafe_b64decode(raw[2:] + pad).decode("utf-8", "replace")
        return decoded if decoded.startswith("http") else href
    except Exception:  # noqa: BLE001
        return href


# ---------------------------------------------------------------------------
# Records + the gate
# ---------------------------------------------------------------------------


@dataclass
class Claim:
    text: str
    citations: list[Citation] = field(default_factory=list)


@dataclass
class ResearchRecord:
    question: str
    claims: list[Claim] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))

    @property
    def id(self) -> str:
        return hashlib.sha256(self.question.encode("utf-8")).hexdigest()[:16]

    def save(self) -> Path:
        RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
        path = RESEARCH_DIR / f"{self.id}.json"
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "ResearchRecord":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            question=raw["question"],
            created_at=raw.get("created_at", ""),
            claims=[
                Claim(text=c["text"], citations=[Citation(**cc) for cc in c["citations"]])
                for c in raw["claims"]
            ],
        )


def gate_research_grounded(record: ResearchRecord) -> tuple[bool, list[str]]:
    """BLOCKER. Every claim must carry at least one citation that re-verifies.

    This is the gate `core/gates.py` never had. It does not ask the agent
    whether it did research; it re-reads the sources and checks.
    """
    failures: list[str] = []
    if not record.claims:
        return False, ["no claims: an empty record is not research"]

    for i, claim in enumerate(record.claims):
        if not claim.citations:
            failures.append(f"claim[{i}] uncited: {claim.text[:70]!r}")
            continue
        verdicts = [c.verify() for c in claim.citations]
        if not any(ok for ok, _ in verdicts):
            why = "; ".join(reason for _, reason in verdicts)
            failures.append(f"claim[{i}] no citation verifies ({why}): {claim.text[:70]!r}")

    return (not failures), failures


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_symbol(args: argparse.Namespace) -> int:
    pattern = re.escape(args.symbol) if args.literal else args.symbol
    hits = search_engine(pattern, max_hits=args.limit) if args.scope in ("engine", "both") else []
    if args.scope in ("repo", "both"):
        hits += search_repo(pattern, max_hits=args.limit)

    if not hits:
        print(f"no hits for {args.symbol!r} in scope={args.scope}")
        return 1
    for h in hits:
        rel = h.locator.replace(str(ENGINE_SOURCE) + os.sep, "").replace(str(REPO_ROOT) + os.sep, "")
        print(f"{h.kind:6} {rel}:{h.line}\n       {h.quote[:150]}")
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    record = ResearchRecord(question=args.question)
    print(f"[1/3] engine source: {ENGINE_SOURCE}")
    for term in args.term or []:
        for hit in search_engine(re.escape(term), max_hits=6):
            record.claims.append(Claim(text=f"{term} appears in engine source", citations=[hit]))

    if args.web:
        print("[2/3] web via local chromium")
        urls = web_search(args.question, k=args.k)
        for url, digest, text in web_fetch(urls):
            first = next((ln for ln in text.splitlines() if len(ln.strip()) > 60), "")
            if first:
                record.claims.append(Claim(
                    text=f"source: {url}",
                    citations=[Citation(kind="web", locator=url, quote=first.strip(),
                                        sha256=digest,
                                        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))],
                ))
    else:
        print("[2/3] web skipped (--web to enable)")

    print("[3/3] gate")
    ok, failures = gate_research_grounded(record)
    path = record.save()
    print(f"  saved {path}")
    for f in failures:
        print(f"  FAIL {f}")
    print(f"  gate_research_grounded: {'PASS' if ok else 'FAIL'} "
          f"({len(record.claims)} claims)")
    return 0 if ok else 1


def _cmd_verify(args: argparse.Namespace) -> int:
    record = ResearchRecord.load(args.path)
    print(f"{record.question}\n  {len(record.claims)} claims, recorded {record.created_at}")
    for i, claim in enumerate(record.claims):
        for c in claim.citations:
            ok, reason = c.verify()
            mark = "ok  " if ok else "FAIL"
            print(f"  [{mark}] claim[{i}] {c.kind}:{Path(c.locator).name}:{c.line} — {reason}")
    ok, failures = gate_research_grounded(record)
    print(f"\ngate_research_grounded: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="core.research", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("symbol", help="find a symbol in engine/repo source")
    s.add_argument("symbol")
    s.add_argument("--scope", choices=["engine", "repo", "both"], default="engine")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--literal", action="store_true", help="treat symbol as literal, not regex")
    s.set_defaults(func=_cmd_symbol)

    a = sub.add_parser("ask", help="build a cited research record")
    a.add_argument("question")
    a.add_argument("--term", action="append", help="engine symbol to ground on (repeatable)")
    a.add_argument("--web", action="store_true", help="also search the web via local chromium")
    a.add_argument("-k", type=int, default=4, help="web results to fetch")
    a.set_defaults(func=_cmd_ask)

    v = sub.add_parser("verify", help="re-verify every citation in a saved record")
    v.add_argument("path")
    v.set_defaults(func=_cmd_verify)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except ResearchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
