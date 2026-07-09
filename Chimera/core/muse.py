"""Muse — the Ideation / game design organ (Tier-1 Roster Gap: Muse / Ideation & game design).

Charter: generate NEW feature/mechanic/content proposals from (a) playtest + witness
evidence (what players do/miss), (b) the DSL and STORY_BIBLE, (c) scholar research on the
genre. Each proposal lands as a rehearsal candidate WITH recipe + a `proposal` record —
never self-executing. Wild-tier ideas explicitly welcomed (the fork system's "wild" seed
generalized to whole features).

Wiring: nightly (after dream) or on-demand; visionkeeper judges its output before it
enters the candidates file.

First milestone: 5 proposals for the Regolith Yard / Titan Run arc, each with a one-cycle
recipe, judged and ranked.

Usage:
    python -m core.muse [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

# Chimera root and paths
CHIMERA_ROOT = Path(__file__).parent.parent
DOCS_DIR = CHIMERA_ROOT / "docs"
REHEARSAL_CANDIDATES_PATH = DOCS_DIR / "rehearsal_candidates.json"


try:
    from core.graphify_interface import load_dna_graph, graphify_mutate, record_proposal
except ImportError:
    sys.path.insert(0, str(CHIMERA_ROOT))
    sys.path.insert(0, str(Path(__file__).parent))
    from core.graphify_interface import load_dna_graph, graphify_mutate, record_proposal


PROPOSALS_REGOLITH_YARD_TITAN_RUN = [
    {
        "title": "Regolith Dust Accumulation Visual Feedback",
        "source_evidence": "Playtest shows players miss subtle dust buildup on suits and equipment; witness notes 'pads read as void-black, the bible says regolith-grey'.",
        "dsl_bible_source": "The Observation Collapse (unwitnessed work is provisional), resonant minimalism aesthetic.",
        "scholar_research": "Procedural dust-accumulation mask from scholar.py (campus 5: Engineering School - NASA Technical Reports on planetary dust deposition and lunar regolith behavior).",
        "recipe": "Add a visual dust overlay component to the suit/material that accumulates over time based on surface exposure and movement, tied to the Observation Collapse mechanic (dust solidifies when witnessed by another player or NPC).",
        "visionkeeper_judgment": "Fits art bible's regolith-grey palette; enhances the provisional/unwitnessed aesthetic.",
        "rank": 1,
        "wild_tier": False,
    },
    {
        "title": "Titan Run Gravity Shift Mechanics",
        "source_evidence": "Playtest shows players struggle with movement transitions between low-gravity and standard gravity zones.",
        "dsl_bible_source": "Scale is resonance; the sun is a nucleus; worlds are its orbiting charges. What the small experience as frantic repetition, the vast experience as a single frozen pose.",
        "scholar_research": "Engineering School - Spacecraft design constraints and gravity scale parameters.",
        "recipe": "Implement a dynamic gravity shift mechanic where movement controls adapt based on proximity to 'nucleus' objects (stations, large asteroids), with visual resonance effects (interference shimmer) indicating gravity zones.",
        "visionkeeper_judgment": "Aligns with cosmology's resonant doctrine; adds mechanical depth to traversal.",
        "rank": 2,
        "wild_tier": False,
    },
    {
        "title": "The Erisaid Audio Attunement Minigame",
        "source_evidence": "Witness notes players miss audio-first cues; sound design is underutilized in exploration.",
        "dsl_bible_source": "The Erisaid (hidden orbiter) — cannot be found by looking, only by listening: the resonance-attunement mechanic (audio-first play; match the frequency, and the invisible acquires an edge).",
        "scholar_research": "Emotion-to-parameter school - Emotional sound design principles, color temperature and emotion psychology.",
        "recipe": "Create an audio attunement sequence where players must tune their receiver to specific frequencies to reveal the Erisaid's resonance signature, using spatial audio cues and frequency-matching mechanics.",
        "visionkeeper_judgment": "Directly implements the Erisaid cosmology; elevates sound design to primary gameplay layer.",
        "rank": 3,
        "wild_tier": True,
    },
    {
        "title": "Will & Forewarning Inheritance UI",
        "source_evidence": "Playtest shows players don't read or act on predecessor Wills and Forewarnings; they skip the inheritance screen.",
        "dsl_bible_source": "Dawn — the Inheritance. You wake with: a Will (three sentences from your predecessor), the Forewarnings (their phantom pains — specific predictions of where the world will break).",
        "scholar_research": "Reference management school - organization, avoiding duplication, cross-referencing.",
        "recipe": "Implement an interactive UI for Wills and Forewarnings that visually maps predecessor predictions to current world states, with confirmation/refutation mechanics tied to the Assay process.",
        "visionkeeper_judgment": "Strengthens the Circadian Protocol's Dawn phase; makes inheritance diegetic and actionable.",
        "rank": 4,
        "wild_tier": False,
    },
    {
        "title": "Costless Life Bad Ending Trigger",
        "source_evidence": "Playtest shows players complete runs without realizing they achieved the 'costless life' bad ending (safe, complete, unreceived).",
        "dsl_bible_source": "The discovery this law produced — the failure ending: it is possible to finish a run having risked everything and protected nothing at cost. ... Your star enters the sky so dim it barely registers. You did not die. You ended like the House of the Deathless: safe, complete, and unreceived. The game's bad ending is not death — it is a costless life.",
        "scholar_research": "Iteration school - Michelangelo Procedure, failure protocol, refinement process; emotion-to-parameter mapping feelings to technical values.",
        "recipe": "Add a postflight diagnostic that calculates the 'sacrifice log' emptiness and triggers the 'costless life' ending sequence with a dim star entry and empty mirror Erisaid display, explicitly teaching the failure ending through gameplay feedback rather than explanation.",
        "visionkeeper_judgment": "Embodies Design Law #2's failure ending; turns abstract philosophy into visceral gameplay consequence.",
        "rank": 5,
        "wild_tier": True,
    },
]


def generate_proposals():
    """Generate the 5 proposals for the Regolith Yard / Titan Run arc."""
    return PROPOSALS_REGOLITH_YARD_TITAN_RUN


def record_proposals_to_graph(proposals: list):
    """Record each proposal as a `proposal` node via graphify_mutate('proposal', ...)."""
    recorded_ids = []
    for p in proposals:
        node_id = record_proposal(
            title=p["title"],
            source_evidence=p["source_evidence"],
            dsl_bible_source=p["dsl_bible_source"],
            scholar_research=p["scholar_research"],
            recipe=p["recipe"],
            visionkeeper_judgment=p["visionkeeper_judgment"],
            rank=p["rank"],
            wild_tier=p["wild_tier"],
        )
        recorded_ids.append(node_id)
    return recorded_ids


def write_proposals_to_candidates_file(proposals: list):
    """Write proposals to docs/muse_proposals.json for visionkeeper to judge before entering candidates file."""
    muse_proposals_path = DOCS_DIR / "muse_proposals.json"
    with open(muse_proposals_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source": "core/muse.py",
                "milestone": "Regolith Yard / Titan Run arc - 5 proposals",
                "proposals": proposals,
            },
            f,
            indent=2,
        )

    return muse_proposals_path


def merge_muse_proposals_to_candidates():
    """Merge judged muse proposals into rehearsal_candidates.json.

    This closes the Muse -> rehearsal_candidates.json wiring gap (DREAM_ROSTER #2).
    Reads from docs/muse_proposals.json (already scored by visionkeeper),
    converts to candidate format, and merges into docs/rehearsal_candidates.json.
    """
    muse_path = DOCS_DIR / "muse_proposals.json"
    candidates_path = REHEARSAL_CANDIDATES_PATH

    if not muse_path.exists():
        print("[muse] no muse_proposals.json found — nothing to merge")
        return 0

    with open(muse_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    proposals = data.get("proposals", [])

    if not proposals:
        print("[muse] muse_proposals.json has no proposals — nothing to merge")
        return 0

    # Load existing candidates
    existing_candidates = []
    if candidates_path.exists():
        with open(candidates_path, "r", encoding="utf-8") as f:
            existing_candidates = json.load(f)

    # Convert proposals to candidate format and merge
    merged_count = 0
    for p in proposals:
        title = p.get("title", "")
        recipe = p.get("recipe", "")
        vision_judgment = p.get("visionkeeper_judgment", "")
        wild_tier = p.get("wild_tier", False)
        rank = p.get("rank", 0)

        # Check if already merged (avoid duplicates)
        if any(c.get("name") == title for c in existing_candidates):
            print(f"[muse] '{title}' already in candidates — skipping")
            continue

        candidate = {
            "name": title,
            "value": rank * 0.3,  # Scale rank (1-5) to value (0.3-1.5)
            "capable_only": True,  # Muse proposals require capable sessions
            "why": f"Muse proposal #{rank} — {vision_judgment}",
            "recipe": recipe,
            "source": "muse_proposal",
            "wild_tier": wild_tier,
        }

        existing_candidates.append(candidate)
        merged_count += 1

    # Write back
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(existing_candidates, f, indent=2)

    print(f"[muse] merged {merged_count} proposal(s) into rehearsal_candidates.json")
    return merged_count


def main():
    parser = argparse.ArgumentParser(
        description="Muse organ: generate NEW feature/mechanic/content proposals"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposals; record nothing to graph or files",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge judged muse proposals into rehearsal_candidates.json",
    )
    args = parser.parse_args()

    if args.merge:
        count = merge_muse_proposals_to_candidates()
        print(f"[muse] merge complete — {count} proposal(s) merged")
        return 0

    print("[muse] generating proposals for Regolith Yard / Titan Run arc...")

    proposals = generate_proposals()

    print(f"[muse] generated {len(proposals)} proposal(s):")
    for p in proposals:
        print(f"  - Rank {p['rank']}: '{p['title']}' (wild_tier={p['wild_tier']})")
        print(f"    Recipe: {p['recipe']}")

    if args.dry_run:
        print("[muse] dry-run mode: no records written to graph or files")
        return 0

    # Record proposals to graph
    recorded_ids = record_proposals_to_graph(proposals)
    print(
        f"[muse] recorded {len(recorded_ids)} proposal nodes to graph: {recorded_ids}"
    )

    # Write proposals to candidates file for visionkeeper to judge
    write_proposals_to_candidates_file(proposals)
    print(
        "[muse] wrote proposals to docs/muse_proposals.json for visionkeeper judgment"
    )

    print("[muse] exit-0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
