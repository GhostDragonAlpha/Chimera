"""Spiral Forks — the Generation Protocol's bounded sacrifice (WS3).

The tamed Legacy Loop Step 1: instead of 100 cost-blind agents, N=3 research
forks per feature (HARNESS_CONFIG['fork_budget']) — one CONSERVATIVE
(campus-canonical), one ALTERNATIVE (different reference family), one WILD
(explicit permission to propose rule-bending approaches ON PAPER). Forks are
research/design candidates ONLY:

    SCOPE GUARD: forks never touch the live level, never write generated C++,
    never record grades. The only graph writes are the losers' autopsy lessons
    (research_discovery, fork_autopsy marker) — paid tuition for the distiller.

Each brief is scored against the Research Depth rubric deterministically
(research writes the exam: acceptance criteria weigh heaviest). The winner
enters the normal cycle (Phase 1.5 onward); losers are autopsied with one
regret-minimization line each.

Execution modes (serial fallback is the default — subagent infra has failed
twice in this environment):
  --use-lm       three sequential LM Studio calls generate the briefs
  --briefs-dir   read agent/subagent-authored briefs (fork_*.json) from a dir

Usage:
    python -m core.spiral_forks --feature Ground_Sand_Particles --use-lm
    python -m core.spiral_forks --feature X --briefs-dir path/ [--dry-run]
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from core.graphify_interface import graphify_mutate, graphify_query
    from core.ralph_loop_harness import HARNESS_CONFIG
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import graphify_mutate, graphify_query

    HARNESS_CONFIG = {
        "fork_budget": 3,
        "lm_studio_url": "http://localhost:1234/v1/chat/completions",
        "lm_studio_model": "qwen3.6-35b-a3b-mtp@iq2_m",
    }

try:
    from core.scholar import scholar_brief_from_research, retrieve_corpus
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from scholar import scholar_brief_from_research, retrieve_corpus
    except ImportError:
        # Scholar not available — fall back to LM-only mode (graceful degradation)
        def _scholar_unavailable(feature: str, topic: str) -> dict:
            raise RuntimeError(
                "Scholar organ not installed; use --use-lm or --briefs-dir"
            )

        scholar_brief_from_research = _scholar_unavailable
        retrieve_corpus = lambda *a, **k: []
CHIMERA_ROOT = Path(__file__).parent.parent
REPORT_DIR = CHIMERA_ROOT / "docs" / "fork_reports"

FORK_SEEDS = [
    (
        "conservative",
        "Follow the campus-canonical approach: locked reference from the relevant "
        "school's A+ sources, standard proven parameters.",
    ),
    (
        "alternative",
        "Use a DIFFERENT reference family than the obvious one: a second-choice "
        "canonical source, different technique for the same visual/system target.",
    ),
    (
        "wild",
        "RULE-BENDING PERMITTED ON PAPER: propose a non-obvious approach that ignores "
        "convention (unusual tools, inverted parameters, cross-domain technique). It will "
        "probably lose — its autopsy is the tuition. It must still declare acceptance "
        "criteria and exact parameters.",
    ),
]

BRIEF_SCHEMA_HINT = {
    "fork": "conservative|alternative|wild",
    "feature": "<name>",
    "approach": "<2-3 sentences>",
    "canonical_reference": "<specific locked reference>",
    "campus_sources": ["<source>", "..."],
    "parameters": {"<param>": "<exact value>"},
    "principles": ["<school principle applied>"],
    "emotional_anchor": "<from mapping table>",
    "acceptance_criteria": ["<criterion measurable in-engine>"],
    "failure_sources": ["<source documenting what does NOT work>", "..."],
}


def _known_seed_sources() -> set:
    """All seed source names across every campus, via the SAME graphify_query('campus',
    'all') that retrieve_campus()/_query_campus() actually serve — validates against
    exactly what the system told the researcher was available, no separate list that
    could drift out of sync."""
    try:
        campuses = graphify_query("campus", "all")
    except Exception:
        campuses = {}
    names = set()
    for campus in (campuses or {}).values():
        for seed in campus.get("seed_sources", []):
            name = str(seed.get("name", "")).strip().lower()
            if name:
                names.add(name)
    return names


def is_reference_recognized(reference: str, known_seeds: set = None) -> bool:
    """Research Depth Protocol Gate 3/6 (AGENTS.md ~109-119): does `reference` share a
    recognizable keyword with ANY known campus seed? Catches wholly-invented citations
    (e.g. the fake "JPL Planetary Science Archive: Regolith Rheology Datasets v2.1" that
    previously scored a full 20/20 unchecked — docs/POST_THE_SYSTEM_THAT_SLEEPS.md)
    without false-flagging a real citation that specializes a generic seed (e.g. a
    specific report number under the seed "NASA Technical Reports")."""
    if known_seeds is None:
        known_seeds = _known_seed_sources()
    ref_words = set(re.findall(r"[a-z]{4,}", reference.lower()))
    if not ref_words:
        return False
    return any(ref_words & set(re.findall(r"[a-z]{4,}", seed)) for seed in known_seeds)


def score_brief(brief: dict) -> tuple:
    """Deterministic Research Depth score, 0-100. Acceptance criteria weigh
    heaviest — research writes the exam."""
    pts, notes = 0.0, []
    ref = str(brief.get("canonical_reference", "")).strip()
    if ref:
        if is_reference_recognized(ref):
            pts += 20
            notes.append("locked reference +20 (recognized against campus seeds)")
        else:
            pts += 5
            notes.append(
                "locked reference present but NOT recognized against any "
                "campus seed source (+5/20) — verify this citation actually exists"
            )
    else:
        notes.append("NO locked reference (0/20)")
    params = brief.get("parameters") or {}
    exact = sum(
        1
        for v in params.values()
        if isinstance(v, (int, float)) or re.search(r"\d", str(v))
    )
    p_pts = min(20, exact * 2)
    pts += p_pts
    notes.append(f"exact params {exact} (+{p_pts}/20)")
    sources = brief.get("campus_sources") or []
    if len(sources) >= 2:
        pts += 10
        notes.append("sources +10")
    else:
        notes.append(f"sources {len(sources)} (0/10)")
    principles = brief.get("principles") or []
    pr_pts = min(10, len(principles) * 2)
    pts += pr_pts
    notes.append(f"principles {len(principles)} (+{pr_pts}/10)")
    if str(brief.get("emotional_anchor", "")).strip():
        pts += 10
        notes.append("anchor +10")
    else:
        notes.append("no anchor (0/10)")
    criteria = brief.get("acceptance_criteria") or []
    c_pts = min(30, len(criteria) * 5)
    pts += c_pts
    notes.append(f"criteria {len(criteria)} (+{c_pts}/30)")
    failure_sources = brief.get("failure_sources") or []
    notes.append(
        f"failure_sources {len(failure_sources)} (Gate 4 met)"
        if failure_sources
        else "failure_sources 0 (Gate 4 unmet)"
    )
    return round(pts, 1), "; ".join(notes)


def autopsy_line(brief: dict, score: float, note: str) -> str:
    """Regret minimization: the single pre-condition that would have saved it."""
    if "generation failed" in str(brief.get("approach", "")):
        return (
            f"Fork '{brief.get('fork')}' for {brief.get('feature')} died at generation — "
            f"the pre-condition that would have saved it: schema-validated LM output with "
            f"/no_think and an adequate token budget (heuristic H-3)."
        )
    weakest = "declare measurable acceptance criteria before building"
    if "NO locked reference" in note:
        weakest = "lock ONE canonical reference before proposing parameters"
    elif "criteria 0" in note or "(+0/30)" in note:
        weakest = "declare measurable acceptance criteria before building"
    elif "exact params 0" in note:
        weakest = "extract exact numeric parameters from the reference, not adjectives"
    return (
        f"Fork '{brief.get('fork')}' for {brief.get('feature')} lost at {score}/100 — "
        f"the pre-condition that would have saved it: {weakest}."
    )


def _lm_generate(feature: str, seed_name: str, directive: str) -> dict:
    # H-3 lesson applied: /no_think suppresses qwen's reasoning phase, the budget
    # is generous, and BOTH content and reasoning_content are schema-checked.
    payload = {
        "model": HARNESS_CONFIG.get("lm_studio_model", "qwen3.6-35b-a3b-mtp@iq2_m"),
        "messages": [
            {
                "role": "user",
                "content": f"/no_think You are one research fork of three for the game feature '{feature}' "
                f"(UE 5.8 space-trader, NASA-reference realism). Your directive: {directive}\n"
                f"Return ONLY a JSON object exactly matching this schema (no prose):\n"
                f"{json.dumps(BRIEF_SCHEMA_HINT, indent=1)}",
            }
        ],
        "max_tokens": 4000,
        "temperature": 0.4 if seed_name == "conservative" else 0.9,
    }
    req = urllib.request.Request(
        HARNESS_CONFIG.get(
            "lm_studio_url", "http://localhost:1234/v1/chat/completions"
        ),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        msg = json.load(r)["choices"][0]["message"]
    for text in (msg.get("content") or "", msg.get("reasoning_content") or ""):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                brief = json.loads(m.group(0))
                brief["fork"] = seed_name
                brief["feature"] = feature
                return brief
            except json.JSONDecodeError:
                continue
    raise ValueError(
        f"LM returned no valid JSON for fork {seed_name} "
        f"(schema-validate before consuming; see heuristic H-3)"
    )
    raise ValueError(
        f"LM returned no valid JSON for fork {seed_name} "
        f"(schema-validate before consuming; see heuristic H-3)"
    )


def _scholar_generate(feature: str, seed_name: str) -> dict:
    """Generate a research-backed brief via Scholar instead of raw LM memory.

    This closes the Scholar -> spiral_forks wiring gap (DREAM_ROSTER #1).
    Queries campus sources + local corpus to produce deterministic, cited briefs
    that score higher on the Research Depth rubric than un-cited LM output.
    """
    from core.scholar import scholar_brief_from_research

    # Map fork type to topic keywords for campus auto-detection
    topic_map = {
        "conservative": f"{feature} canonical approach",
        "alternative": f"{feature} alternative reference family",
        "wild": f"{feature} unconventional approaches",
    }

    try:
        brief = scholar_brief_from_research(
            feature=feature, topic=topic_map.get(seed_name, f"{feature} research")
        )
        brief["fork"] = seed_name
        return brief
    except Exception as e:
        raise RuntimeError(f"Scholar generation failed for fork {seed_name}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Run bounded sacrificial research forks for a feature"
    )
    parser.add_argument("--feature", required=True)
    parser.add_argument(
        "--budget", type=int, default=HARNESS_CONFIG.get("fork_budget", 3)
    )
    parser.add_argument(
        "--use-lm",
        action="store_true",
        help="generate briefs via LM Studio (serial; needs localhost:1234)",
    )
    parser.add_argument(
        "--use-scholar",
        action="store_true",
        help="generate research-backed briefs via Scholar (campus + corpus sources)",
    )
    parser.add_argument(
        "--briefs-dir", help="read fork_*.json briefs authored by agent/subagents"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="score and rank only; record no autopsies",
    )
    args = parser.parse_args()

    seeds = FORK_SEEDS[: max(1, args.budget)]
    briefs = []
    if args.briefs_dir:
        for f in sorted(Path(args.briefs_dir).glob("fork_*.json")):
            briefs.append(json.loads(f.read_text(encoding="utf-8")))
        if not briefs:
            print(f"no fork_*.json briefs in {args.briefs_dir}")
            print(f"expected schema:\n{json.dumps(BRIEF_SCHEMA_HINT, indent=1)}")
            return 1
    elif args.use_scholar:
        # Scholar -> spiral_forks wiring (DREAM_ROSTER #1): research-backed briefs
        for name, directive in seeds:
            print(f"[fork:{name}] generating via Scholar (campus + corpus)...")
            try:
                briefs.append(_scholar_generate(args.feature, name))
            except Exception as e:
                print(
                    f"[fork:{name}] generation failed: {e} — fork dies, autopsy recorded"
                )
                briefs.append(
                    {
                        "fork": name,
                        "feature": args.feature,
                        "approach": f"(generation failed: {e})",
                    }
                )
    elif args.use_lm:
        for name, directive in seeds:
            print(f"[fork:{name}] generating via LM Studio (serial)...")
            try:
                briefs.append(_lm_generate(args.feature, name, directive))
            except Exception as e:
                print(
                    f"[fork:{name}] generation failed: {e} — fork dies, autopsy recorded"
                )
                briefs.append(
                    {
                        "fork": name,
                        "feature": args.feature,
                        "approach": f"(generation failed: {e})",
                    }
                )
    else:
        print(
            "choose --use-lm, --use-scholar, or --briefs-dir. For subagent-parallel mode, have each "
            "subagent write fork_<name>.json into a dir, then pass --briefs-dir."
        )
        print(f"brief schema:\n{json.dumps(BRIEF_SCHEMA_HINT, indent=1)}")
        return 1

    scored = []
    for b in briefs:
        s, note = score_brief(b)
        scored.append((s, note, b))
    scored.sort(key=lambda t: -t[0])

    print(f"\n=== FORK RESULTS: {args.feature} (budget {len(briefs)}) ===")
    for s, note, b in scored:
        print(f"  {b.get('fork', '?'):<14} {s:>5}/100  {note}")
    winner = scored[0]
    losers = scored[1:]
    if winner[0] < 40:
        # fail-safety: a dead brief must not "win" — everything is a loser
        print(
            f"\nALL FORKS DIED (best {winner[0]}/100 < 40 floor) — no winner. "
            f"Regenerate or hand-author briefs; do NOT proceed with a dead brief."
        )
        losers = scored
        winner = None
    else:
        print(
            f"\nWINNER: {winner[2].get('fork')} at {winner[0]}/100 — proceed to Phase 1.5 "
            f"with this brief."
        )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report = REPORT_DIR / f"{args.feature}_{stamp}.md"
    lines = [f"# Fork report: {args.feature} ({stamp}Z)", ""]
    for s, note, b in scored:
        tag = (
            "WINNER" if winner is not None and (s, note, b) == winner else "sacrificed"
        )
        lines += [
            f"## {b.get('fork')} — {s}/100 ({tag})",
            f"- scoring: {note}",
            "```json",
            json.dumps(b, indent=1),
            "```",
            "",
        ]
    report.write_text("\n".join(lines), encoding="utf-8")
    print(f"report -> {report}")

    if args.dry_run:
        print("dry-run: no autopsies recorded.")
        return 0

    for s, note, b in losers:
        line = autopsy_line(b, s, note)
        node_id = graphify_mutate(
            "research_discovery",
            details={
                "source": f"fork_autopsy:{args.feature}:{b.get('fork')}",
                "campus": "iteration",
                "quality_rating": "autopsy",
                "principles": [line],
            },
        )
        print(f"autopsy recorded: {node_id}  {line[:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
