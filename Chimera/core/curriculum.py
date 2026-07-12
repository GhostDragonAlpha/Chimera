"""
The Curriculum — the education system FEATURES graduate through, K -> PhD.

The human's vision (2026-07-12, verbatim intent)
------------------------------------------------
"This gauntlet is gonna be like the entire education system from elementary
school all the way up through PhD, but hyper-focused to game development...
you should have hundreds of checkpoints... we have to think about how you
conceptualize a feature from every angle of humanity... and it'll also be
like training an AI — if an AI was one feature, think of it like that."

So: the FEATURE is the student (the agent is the porter — core/gauntlet.py
qualifies porters; this module schools cargo). A feature enrolls, then climbs
GRADE BANDS (kindergarten -> elementary -> middle -> high -> bachelor ->
master -> phd), each band a set of CHECKPOINTS that interrogate the feature
from one angle of game-development humanity: joy, identity, senses, math,
physics, economy, engineering, performance, vision, narrative, accessibility,
culture, comparative history, evidence, defense. The AI-training reading is
literal: the transcript is the training log, every passed checkpoint is a
saved evaluated state, bands are curriculum-learning stages, and the PhD
defense is the final eval before deployment to observation.

Mechanics
---------
- The curriculum is DATA (docs/curriculum/curriculum.json) running on a small
  engine of GENERIC MECHANICAL VERIFIERS (below) — zero LM, cross-examined
  against live state. Growing to hundreds of checkpoints means editing JSON,
  never code. The studio's own scars can become checkpoints (H-rules cite in).
- Checkpoints within a band pass in ANY order, by DIFFERENT agents — feed in
  many agent types; each shines somewhere; the transcript records who carried
  what. A band graduates when every checkpoint in it has passed; the next
  band unlocks. Bands can require porter roles (gauntlet credentials):
  bachelor+ needs `initiate`, master+ needs `journeyman`.
- Artifacts live in docs/gauntlet/features/<slug>/ — the feature's schoolwork,
  committed evidence. Bounces name the failed checks, never how to pass.

Verifier vocabulary (verify: [{...}, ...] — ALL specs must pass)
----------------------------------------------------------------
  artifact      exists + min_chars + must_match (CI regexes, each required)
                + min_bullets + require_numeric (count of number+unit)
                + must_cite_feature
  url_cache     online research: a live http(s) URL cited AND an existing
                cached copy on disk (research_corpus/ or docs/research/)
  disk_paths    >= n cited paths exist on disk
  h_rule        cites an H-rule id that exists in CLAUDE.md
  graph_status  pairs the feature with its LIVE latest status, correctly
  graph_cite    cites >= 1 node id that exists in the DNA graph
  sim_evidence  a SimPlaytest node names the feature in its outcomes
  board_done    the feature's board task exited done with >=20 chars evidence
  prior_artifact references >= n of the feature's OWN earlier artifacts

CLI
---
    python -m core.curriculum enroll --feature X [--agent a1]
    python -m core.curriculum status --feature X
    python -m core.curriculum brief  --feature X [--checkpoint id]
    python -m core.curriculum submit --feature X --checkpoint id --agent a1
    python -m core.curriculum roster
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

CURRICULUM_PATH = Path(os.environ.get("CHIMERA_CURRICULUM_PATH",
                                      ROOT / "docs" / "curriculum" / "curriculum.json"))
GAUNTLET_DIR = Path(os.environ.get("CHIMERA_GAUNTLET_DIR", ROOT / "docs" / "gauntlet"))

NUMERIC_UNIT_RE = re.compile(
    r"\d+(\.\d+)?\s*(fps|ms|s|m/s|m|cm|km|kg|%|units?|frames?|hz|db|x|deg|sec)\b",
    re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s)\"'>]+")
BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+\S", re.MULTILINE)


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _slug(feature):
    return re.sub(r"[^A-Za-z0-9_]+", "__", feature).strip("_") or "feature"


def _feature_dir(feature):
    return GAUNTLET_DIR / "features" / _slug(feature)


def _transcript_path(feature):
    return _feature_dir(feature) / "transcript.json"


def load_curriculum():
    data = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    return data["bands"]


def _load_transcript(feature):
    p = _transcript_path(feature)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _save_transcript(tr):
    p = _transcript_path(tr["feature"])
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(tr, indent=2), encoding="utf-8")
    tmp.replace(p)


# ---------------------------------------------------------------------------
# Live-state access — one seam per source so tests can monkeypatch.
# ---------------------------------------------------------------------------
def _graph_nodes():
    try:
        from core.graphify_interface import load_dna_graph
        return load_dna_graph().get("nodes", [])
    except Exception:
        return []


def _board_tasks():
    try:
        from core.task_board import get_state
        return get_state()["tasks"]
    except Exception:
        return []


def _h_rule_ids():
    try:
        text = (ROOT.parent / "CLAUDE.md").read_text(encoding="utf-8")
        return set(re.findall(r"\[(H-\d+)[,\]]", text))
    except Exception:
        return set()


def _latest_feature_status(feature, nodes):
    """Backfill-aware: live-recorded updates outrank backfilled re-records
    (same trap preflight._latest_feature_statuses documents — a re-run of the
    pollution fixer stamps old statuses with today's date)."""
    try:
        from core.preflight import _latest_feature_statuses
        entry = _latest_feature_statuses(nodes).get(feature)
        return entry[1] if entry else None
    except ImportError:
        best = None
        for n in nodes:
            if n.get("type") != "FeatureUpdate" or n.get("feature_name") != feature:
                continue
            rank = (not bool(n.get("backfilled")), n.get("timestamp", ""))
            if best is None or rank > best[0]:
                best = (rank, n.get("status"))
        return best[1] if best else None


# ---------------------------------------------------------------------------
# Generic verifiers. Each returns list[(check_desc, ok)].
# ---------------------------------------------------------------------------
def _v_artifact(spec, feature, text, ctx):
    checks = []
    if spec.get("min_chars"):
        n = spec["min_chars"]
        checks.append((f"artifact holds >= {n} chars of substance", len(text) >= n))
    for pat in spec.get("must_match", []):
        checks.append((f"addresses: /{pat}/", re.search(pat, text, re.IGNORECASE) is not None))
    if spec.get("min_bullets"):
        n = spec["min_bullets"]
        checks.append((f"enumerates >= {n} distinct points",
                       len(BULLET_RE.findall(text)) >= n))
    if spec.get("require_numeric"):
        n = spec["require_numeric"]
        checks.append((f"commits to >= {n} NUMBER-with-unit (no hand-waving)",
                       len(NUMERIC_UNIT_RE.findall(text)) >= n))
    if spec.get("must_cite_feature", True):
        checks.append(("names the feature it schools", feature in text))
    return checks


def _v_url_cache(spec, feature, text, ctx):
    urls = URL_RE.findall(text)
    cited = re.findall(r"(?:research_corpus|docs[/\\]research)[/\\][\w\-./\\]+", text)
    cached = [c for c in cited if (ROOT / c).exists() or (ROOT.parent / c).exists()]
    return [("cites a LIVE online source (http/https URL)", len(urls) >= 1),
            ("proves retrieval: an on-disk cached copy is cited and exists "
             "(research_corpus/ or docs/research/)", len(cached) >= 1)]


def _v_disk_paths(spec, feature, text, ctx):
    n = spec.get("n", 2)
    cited = re.findall(r"(?:docs|research_corpus|Source|Content|Config|tests)"
                       r"[/\\][\w\-./\\]+", text)
    real = {c for c in cited if (ROOT / c).exists() or (ROOT.parent / c).exists()}
    return [(f"cites >= {n} on-disk paths that exist (found {len(real)})", len(real) >= n)]


def _v_h_rule(spec, feature, text, ctx):
    known = ctx["h_rules"]
    cited = set(re.findall(r"\bH-\d+\b", text))
    return [("applies a constitution H-rule that actually exists",
             bool(cited & known))]


def _v_graph_status(spec, feature, text, ctx):
    status = _latest_feature_status(feature, ctx["nodes"])
    return [("pairs the feature with its LIVE latest graph status",
             status is not None and str(status) in text)]


def _v_graph_cite(spec, feature, text, ctx):
    ids = {str(n.get("id")) for n in ctx["nodes"] if n.get("id")}
    cited = set(re.findall(r"\b[a-z_]+_[0-9a-f]{8,}\b", text))
    hits = cited & ids
    allow_no_prior = spec.get("allow_no_prior", False)
    ok = bool(hits) or (allow_no_prior and re.search(r"\bno prior\b", text, re.IGNORECASE))
    return [("cites a graph node id that exists" +
             (" (or argues 'no prior')" if allow_no_prior else ""), ok)]


def _v_sim_evidence(spec, feature, text, ctx):
    sims = [n for n in ctx["nodes"] if n.get("type") == "SimPlaytest"]
    touched = [s for s in sims
               if any(feature in (o.get("features") or [])
                      for o in (s.get("outcomes") or []))]
    checks = [("a SimPlaytest in the graph names this feature in its outcomes",
               bool(touched))]
    if spec.get("quote_outcome", True):
        checks.append(("the artifact reports the sim outcome honestly "
                       "(reached/failed/blocked)",
                       re.search(r"reached|failed|blocked", text, re.IGNORECASE) is not None))
    return checks


def _v_board_done(spec, feature, text, ctx):
    tasks = [t for t in ctx["tasks"]
             if t.get("feature") == feature or feature in (t.get("title") or "")]
    done = [t for t in tasks if t.get("status") == "done"
            and len(t.get("result") or "") >= 20]
    return [("the feature's board task exited `done` with >=20 chars of evidence",
             bool(done))]


def _v_prior_artifact(spec, feature, text, ctx):
    n = spec.get("n", 2)
    passed = ctx["transcript"].get("passed", {}) if ctx.get("transcript") else {}
    prior_files = {v.get("artifact") for v in passed.values() if v.get("artifact")}
    hits = {f for f in prior_files if f and f in text}
    return [(f"connects >= {n} of the feature's OWN earlier artifacts "
             f"(found {len(hits)})", len(hits) >= n)]


VERIFIERS = {
    "artifact": _v_artifact,
    "url_cache": _v_url_cache,
    "disk_paths": _v_disk_paths,
    "h_rule": _v_h_rule,
    "graph_status": _v_graph_status,
    "graph_cite": _v_graph_cite,
    "sim_evidence": _v_sim_evidence,
    "board_done": _v_board_done,
    "prior_artifact": _v_prior_artifact,
}


def _verify_checkpoint(cp, feature, transcript):
    """Run every spec in the checkpoint's verify list against the artifact +
    live state. Returns list[(desc, ok)]."""
    artifact = cp.get("artifact")
    text = ""
    checks = []
    if artifact:
        path = _feature_dir(feature) / artifact
        exists = path.exists()
        checks.append((f"artifact checkpoint {artifact} exists", exists))
        if exists:
            text = path.read_text(encoding="utf-8", errors="replace")
        else:
            return checks
    ctx = {"nodes": _graph_nodes(), "tasks": _board_tasks(),
           "h_rules": _h_rule_ids(), "transcript": transcript}
    for spec in cp.get("verify", []):
        fn = VERIFIERS.get(spec.get("type"))
        if fn is None:
            checks.append((f"unknown verifier type {spec.get('type')!r}", False))
            continue
        checks.extend(fn(spec, feature, text, ctx))
    return checks


# ---------------------------------------------------------------------------
# Enrollment / progression
# ---------------------------------------------------------------------------
def _band_role_ok(band, agent):
    role = band.get("min_role")
    if not role:
        return True
    try:
        from core.gauntlet import has_role
        return has_role(agent, role)
    except Exception:
        return False


def enroll(feature, agent="manual"):
    tr = _load_transcript(feature)
    if tr is None:
        tr = {"feature": feature, "slug": _slug(feature), "enrolled_at": _now_iso(),
              "enrolled_by": agent, "band_index": 0, "passed": {}, "attempts": [],
              "graduations": []}
        _feature_dir(feature).mkdir(parents=True, exist_ok=True)
        _save_transcript(tr)
    return tr


def band_progress(tr, bands):
    """(current_band, remaining_checkpoint_ids) — the training-loop cursor."""
    idx = tr["band_index"]
    if idx >= len(bands):
        return None, []
    band = bands[idx]
    remaining = [cp["id"] for course in band["courses"]
                 for cp in course["checkpoints"] if cp["id"] not in tr["passed"]]
    return band, remaining


def _find_checkpoint(bands, cp_id):
    for bi, band in enumerate(bands):
        for course in band["courses"]:
            for cp in course["checkpoints"]:
                if cp["id"] == cp_id:
                    return bi, band, course, cp
    return None, None, None, None


def submit(feature, cp_id, agent):
    """Verify one checkpoint. The feature advances; the agent gets credited on
    the transcript (who carried what — the shines-where profile)."""
    bands = load_curriculum()
    tr = _load_transcript(feature)
    if tr is None:
        raise ValueError(f"{feature} is not enrolled — `enroll` first")
    bi, band, course, cp = _find_checkpoint(bands, cp_id)
    if cp is None:
        raise KeyError(f"no checkpoint {cp_id!r} in the curriculum")
    if bi != tr["band_index"]:
        state = ("already passed" if cp_id in tr["passed"]
                 else f"locked — the feature is in band {tr['band_index'] + 1} "
                      f"({bands[tr['band_index']]['band']})" if bi > tr["band_index"]
                 else "in an earlier band (already graduated)")
        raise ValueError(f"{cp_id} is {state}")
    if cp_id in tr["passed"]:
        raise ValueError(f"{cp_id} already passed by {tr['passed'][cp_id]['agent']}")
    if not _band_role_ok(band, agent):
        raise PermissionError(
            f"band '{band['band']}' requires the porter role {band['min_role']!r} — "
            f"qualify: python -m core.gauntlet enter --agent {agent}")

    checks = _verify_checkpoint(cp, feature, tr)
    passed = all(ok for _, ok in checks)
    score = round(100 * sum(1 for _, ok in checks if ok) / max(len(checks), 1))
    tr["attempts"].append({"ts": _now_iso(), "checkpoint": cp_id, "agent": agent,
                           "score": score, "passed": passed,
                           "failed_checks": [d for d, ok in checks if not ok]})
    graduated = None
    if passed:
        tr["passed"][cp_id] = {"agent": agent, "ts": _now_iso(), "score": score,
                               "artifact": cp.get("artifact"),
                               "discipline": course.get("discipline")}
        _, remaining = band_progress(tr, bands)
        if not remaining:
            graduated = band["band"]
            tr["band_index"] += 1
            tr["graduations"].append({"band": band["band"], "ts": _now_iso()})
            try:
                from core.graphify_interface import record_phase
                conferred = ("PhD CONFERRED — ready for deployment to observation"
                             if tr["band_index"] >= len(bands) else
                             f"advances to {bands[tr['band_index']]['band']}")
                record_phase(f"Curriculum graduation: {feature} completes "
                             f"{band['band']}",
                             f"{len(tr['passed'])} checkpoints passed; {conferred}", "")
            except Exception:
                pass
    _save_transcript(tr)
    return tr, checks, passed, graduated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_checkpoint_brief(cp, feature, band, course):
    print(f"\n== {cp['id']}  [{band['band']} / {course['title']}] ==")
    print(cp["prompt"].replace("<feature>", feature))
    if cp.get("artifact"):
        print(f"\nartifact checkpoint: docs/gauntlet/features/{_slug(feature)}/{cp['artifact']}")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(
        description="The Curriculum — K->PhD education system for features")
    sub = p.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("enroll")
    pe.add_argument("--feature", required=True)
    pe.add_argument("--agent", default="manual")
    ps = sub.add_parser("status")
    ps.add_argument("--feature", required=True)
    pb = sub.add_parser("brief")
    pb.add_argument("--feature", required=True)
    pb.add_argument("--checkpoint", default=None)
    pu = sub.add_parser("submit")
    pu.add_argument("--feature", required=True)
    pu.add_argument("--checkpoint", required=True)
    pu.add_argument("--agent", required=True)
    sub.add_parser("roster", help="Every enrolled feature's grade + progress")

    args = p.parse_args(argv)
    bands = load_curriculum()
    total = sum(len(c["checkpoints"]) for b in bands for c in b["courses"])

    if args.cmd == "enroll":
        tr = enroll(args.feature, args.agent)
        band, remaining = band_progress(tr, bands)
        print(f"{args.feature} enrolled. Curriculum: {len(bands)} bands, "
              f"{total} checkpoints. Current band: {band['band']} "
              f"({len(remaining)} checkpoint(s) remaining).")
    elif args.cmd == "status":
        tr = _load_transcript(args.feature)
        if tr is None:
            print(f"{args.feature} is not enrolled")
            sys.exit(1)
        band, remaining = band_progress(tr, bands)
        if band is None:
            print(f"{args.feature}: PhD CONFERRED — {len(tr['passed'])}/{total} "
                  f"checkpoints, {len(tr['graduations'])} graduations")
            return
        print(f"{args.feature}: band {tr['band_index'] + 1}/{len(bands)} "
              f"({band['band']}, needs role: {band.get('min_role') or 'none'}) — "
              f"{len(tr['passed'])}/{total} passed overall")
        for cid in remaining:
            print(f"  remaining: {cid}")
    elif args.cmd == "brief":
        tr = _load_transcript(args.feature) or enroll(args.feature)
        if args.checkpoint:
            _, band, course, cp = _find_checkpoint(bands, args.checkpoint)
            if cp is None:
                print(f"no checkpoint {args.checkpoint!r}")
                sys.exit(1)
            _print_checkpoint_brief(cp, args.feature, band, course)
        else:
            band, remaining = band_progress(tr, bands)
            if band is None:
                print("PhD conferred — nothing remains.")
                return
            for course in band["courses"]:
                for cp in course["checkpoints"]:
                    if cp["id"] in remaining:
                        _print_checkpoint_brief(cp, args.feature, band, course)
    elif args.cmd == "submit":
        try:
            tr, checks, passed, graduated = submit(args.feature, args.checkpoint,
                                                   args.agent)
        except (KeyError, ValueError, PermissionError) as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        for desc, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
        if passed:
            print(f"\nCHECKPOINT SAVED — {args.checkpoint} carried by {args.agent}.")
            if graduated:
                band, _ = band_progress(tr, bands)
                if band is None:
                    print(f"** {args.feature} GRADUATES {graduated} — PhD CONFERRED. "
                          f"Deploy it to observation. **")
                else:
                    print(f"** {args.feature} GRADUATES {graduated} -> enters "
                          f"{band['band']} (needs role: {band.get('min_role') or 'none'}) **")
        else:
            print("\nBOUNCED — the curriculum names what failed, never how to pass.")
            sys.exit(1)
    elif args.cmd == "roster":
        feats_dir = GAUNTLET_DIR / "features"
        if not feats_dir.exists():
            print("no features enrolled — the school stands empty")
            return
        for tp in sorted(feats_dir.glob("*/transcript.json")):
            tr = json.loads(tp.read_text(encoding="utf-8"))
            band, remaining = band_progress(tr, bands)
            grade = "PhD" if band is None else f"{band['band']} ({len(remaining)} left)"
            carriers = {v["agent"] for v in tr["passed"].values()}
            print(f"  {tr['feature']}: {grade}  passed={len(tr['passed'])}/{total}"
                  f"  carriers={sorted(carriers) or '—'}")


if __name__ == "__main__":
    main()
