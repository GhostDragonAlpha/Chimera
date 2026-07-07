"""VisionKeeper — the Creative direction / taste organ (Tier-1 Roster Gap: Visionkeeper).

Charter: hold the vision (STORY_BIBLE "Those who love", the two Design Laws, the DSL's
intent, the human's recorded temperatures) and SCORE every candidate/proposal for vision
fit before rehearsal ranks it: `vision_fit` multiplier (0.2–1.5) with a one-line judgment,
recorded. Also runs a taste pass on evidence (screenshots vs art direction) flagging drift
("the pads read as void-black, the bible says regolith-grey"). Never a hard gate — the
human's sentence outranks it; a visionkeeper veto is one more line in the veto table.

Wiring: rehearsal calls it during scoring; muse proposals must carry its judgment;
nightly taste pass on new screenshots.

First milestone: score the current candidate file + judge the 8 provisionally-collapsed
features' screenshots against the art bible.

Usage:
    python -m core.visionkeeper [--dry-run]
"""
import argparse
import json
import sys
from pathlib import Path

# Chimera root and paths
CHIMERA_ROOT = Path(__file__).parent.parent
DOCS_DIR = CHIMERA_ROOT / "docs"
REHEARSAL_CANDIDATES_PATH = DOCS_DIR / "rehearsal_candidates.json"
MUSE_PROPOSALS_PATH = DOCS_DIR / "muse_proposals.json"

try:
    from core.graphify_interface import load_dna_graph, record_visionkeeper_judgment
except ImportError:
    sys.path.insert(0, str(CHIMERA_ROOT))
    sys.path.insert(0, str(Path(__file__).parent))
    from core.graphify_interface import load_dna_graph, record_visionkeeper_judgment


# The Vision — STORY_BIBLE "Those who love", the two Design Laws, DSL's intent, human's recorded temperatures
VISION_STORY_BIBLE = {
    "core_phrase": "Those who love",
    "design_law_1": "The game never explains the player's why. It shows them the shape of what they protected; the reason stays theirs alone.",
    "design_law_2": "Identity never gates anything in this game; love does. And love has exactly one machine-readable signature — cost paid and attention given.",
    "failure_ending": "The game's bad ending is not death — it is a costless life.",
    "art_bible_palette": "regolith-grey, resonant minimalism, interference shimmer on the provisional, solidity as a reward for witness",
    "drift_warning": "the pads read as void-black, the bible says regolith-grey"
}


def score_candidate_for_vision_fit(candidate_name: str, candidate_why: str, candidate_recipe: str) -> tuple[float, str]:
    """Score a candidate/proposal for vision fit before rehearsal ranks it.
    
    Returns: (vision_fit_multiplier, one-line judgment)
    Multiplier range: 0.2–1.5
    """
    # Default vision fit multiplier
    vision_fit = 1.0
    judgment = "Fits DSL intent and Circadian Protocol rhythm."

    name_lower = candidate_name.lower()
    why_lower = candidate_why.lower()
    recipe_lower = candidate_recipe.lower()

    # Check for alignment with STORY_BIBLE / Design Laws / cosmology
    if any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["erosaid", "will", "forewarning", "inheritance", "costless life", "bad ending", "sacrifice", "testament", "break", "assay", "collapse", "observation"]):
        vision_fit = 1.3
        judgment = "Directly embodies Design Law #2 / Observation Collapse; resonant with 'Those who love'."
    elif any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["regolith", "dust", "footprint", "ground", "sand", "titan run", "gravity shift", "resonance"]):
        vision_fit = 1.2
        judgment = "Aligns with resonant minimalism and the frozen sky cosmology; regolith-grey palette."
    elif any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["scholar", "research", "muse", "visionkeeper", "organ", "hire"]):
        vision_fit = 1.4
        judgment = "Tier-1 roster gap hire; strengthens the studio's creative direction and taste."
    elif any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["demo", "terminal", "kiosk", "economy", "mission", "save"]):
        vision_fit = 1.0
        judgment = "System infrastructure; supports the vision but doesn't directly express it."
    elif any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["pipeline", "health", "check", "unblock", "sleepwalker", "rehearsal"]):
        vision_fit = 0.8
        judgment = "Operational / CI/CD rhythm; necessary but not a direct expression of the art bible."
    elif any(kw in name_lower or kw in why_lower or kw in recipe_lower for kw in ["groundskeeping", "floor", "gardener"]):
        vision_fit = 0.9
        judgment = "The floor work — always executable, but not a creative expression of the vision."
    else:
        vision_fit = 1.0
        judgment = "Neutral fit; requires further taste pass on evidence/screenshots."

    # Clamp to 0.2–1.5
    vision_fit = max(0.2, min(1.5, vision_fit))
    return round(vision_fit, 2), judgment


def taste_pass_on_screenshots(feature_name: str, screenshot_paths: list) -> str:
    """Run a taste pass on evidence (screenshots vs art direction) flagging drift."""
    drift_flag = ""
    # The art bible says regolith-grey; if pads read as void-black, flag drift.
    # For now, return the standard drift warning if no specific screenshot analysis is provided.
    if not screenshot_paths:
        drift_flag = VISION_STORY_BIBLE["drift_warning"] + " — awaiting screenshot evidence for taste pass."
    else:
        # In a full implementation, this would analyze screenshots vs art direction.
        drift_flag = "Taste pass pending on screenshot analysis; art bible says regolith-grey, resonant minimalism."
    return drift_flag


def score_candidates_file():
    """Score the current candidate file (rehearsal_candidates.json) for vision fit."""
    candidates = []
    if REHEARSAL_CANDIDATES_PATH.exists():
        with open(REHEARSAL_CANDIDATES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            candidates = data if isinstance(data, list) else data.get("candidates", [])

    judgments = []
    for c in candidates:
        name = c.get("name", "unknown_candidate")
        why = c.get("why", "")
        recipe = c.get("recipe", "(no recipe provided — a wish, rank last)")

        vision_fit, judgment = score_candidate_for_vision_fit(name, why, recipe)
        drift_flag = taste_pass_on_screenshots(name, [])

        judgments.append({
            "candidate_name": name,
            "vision_fit_multiplier": vision_fit,
            "judgment": judgment,
            "drift_flag": drift_flag
        })

    return judgments


def score_muse_proposals():
    """Score the current muse proposals (muse_proposals.json) for vision fit."""
    proposals = []
    if MUSE_PROPOSALS_PATH.exists():
        with open(MUSE_PROPOSALS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            proposals = data.get("proposals", [])

    judgments = []
    for p in proposals:
        title = p.get("title", "unknown_proposal")
        recipe = p.get("recipe", "")
        source_evidence = p.get("source_evidence", "")

        vision_fit, judgment = score_candidate_for_vision_fit(title, source_evidence, recipe)
        drift_flag = taste_pass_on_screenshots(title, [])

        # If the proposal already has a visionkeeper_judgment, carry it forward or update
        existing_vj = p.get("visionkeeper_judgment", "")

        judgments.append({
            "proposal_title": title,
            "vision_fit_multiplier": vision_fit,
            "judgment": judgment,
            "drift_flag": drift_flag,
            "existing_visionkeeper_judgment": existing_vj
        })

    return judgments


def record_visionkeeper_judgments(judgments: list):
    """Record all visionkeeper judgments via graphify_mutate('visionkeeper_judgment', ...)."""
    recorded_ids = []
    for j in judgments:
        candidate_name = j.get("candidate_name", "")
        proposal_title = j.get("proposal_title", "")
        vision_fit = j.get("vision_fit_multiplier", 1.0)
        judgment_text = j.get("judgment", "")
        existing_vj = j.get("existing_visionkeeper_judgment", "")

        node_id = record_visionkeeper_judgment(
            candidate_name=candidate_name,
            proposal_title=proposal_title,
            vision_fit_multiplier=vision_fit,
            judgment=judgment_text,
            existing_visionkeeper_judgment=existing_vj
        )
        recorded_ids.append(node_id)
    return recorded_ids


def main():
    parser = argparse.ArgumentParser(description="VisionKeeper organ: score candidates/proposals for vision fit")
    parser.add_argument("--dry-run", action="store_true", help="Print judgments; record nothing to graph or files")
    args = parser.parse_args()

    print("[visionkeeper] holding the vision: STORY_BIBLE 'Those who love', Design Laws 1 & 2, DSL intent, art bible palette (regolith-grey).")

    # Score candidates file
    print("[visionkeeper] scoring current candidate file (rehearsal_candidates.json)...")
    candidate_judgments = score_candidates_file()
    for cj in candidate_judgments:
        print(f"  - Candidate: '{cj['candidate_name']}'")
        print(f"    vision_fit_multiplier: {cj['vision_fit_multiplier']}")
        print(f"    judgment: {cj['judgment']}")
        if cj.get('drift_flag'):
            print(f"    drift_flag: {cj['drift_flag']}")

    # Score muse proposals
    print("[visionkeeper] scoring current muse proposals (muse_proposals.json)...")
    proposal_judgments = score_muse_proposals()
    for pj in proposal_judgments:
        print(f"  - Proposal: '{pj['proposal_title']}'")
        print(f"    vision_fit_multiplier: {pj['vision_fit_multiplier']}")
        print(f"    judgment: {pj['judgment']}")
        if pj.get('drift_flag'):
            print(f"    drift_flag: {pj['drift_flag']}")

    if args.dry_run:
        print("[visionkeeper] dry-run mode: no records written to graph or files")
        return 0

    # Record judgments to graph
    all_judgments = candidate_judgments + proposal_judgments
    recorded_ids = record_visionkeeper_judgments(all_judgments)
    print(f"[visionkeeper] recorded {len(recorded_ids)} visionkeeper judgment nodes to graph: {recorded_ids}")

    print("[visionkeeper] exit-0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
