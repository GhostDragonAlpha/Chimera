"""AAA-Expanded Result Grader — comprehensive game quality analysis across 12 development dimensions.

Builds on the narrow 4-category technical rubric (correctness, stability, checklist, fidelity)
with 8 additional AAA game development dimensions (immersion, gameplay flow, systems depth,
visual fidelity, audio design, narrative, accessibility, polish). Total 400-point scale.

Provides detailed guidance for refinement and drives game toward AAA-level enjoyment.

Usage (module):
    from core.result_grader_aaa_expanded import grade_feature_aaa_expanded
    result = grade_feature_aaa_expanded("Ground_Sand_Particles", evidence={...}, benchmark_titles=["No Man's Sky", "Subnautica"])

Usage (CLI):
    python -m core.result_grader_aaa_expanded --feature Ground_Sand_Particles --evidence evidence.json --benchmark "No Man's Sky" "Subnautica"
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Tuple, List

try:
    from core.graphify_interface import load_dna_graph, save_dna_graph
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import load_dna_graph, save_dna_graph

# AAA-Expanded rubric weights (total 400 points)
RUBRIC_WEIGHTS = {
    "technical_correctness": 40,      # test pass rate, criteria coverage
    "stability_performance": 25,      # crash-free, FPS, growth bounds
    "design_checklist": 20,           # feedback, consistency, meaningful parameters, fail-safety, balance sanity
    "spec_fidelity": 15,              # DSL parameter verification
    "player_immersion": 50,           # moment-to-moment feel, animation smoothness, visual polish, audio-visual sync
    "gameplay_flow": 40,              # pacing, progression clarity, reward cadence, difficulty tuning
    "systems_depth": 30,              # mechanical interdependencies, emergent complexity, player agency
    "visual_fidelity": 35,            # lighting quality, material detail, environmental storytelling, LOD performance
    "audio_design": 25,               # diegetic/non-diegetic mix, feedback responsiveness, ambient richness
    "narrative_worldbuilding": 30,    # lore consistency, character development, world coherence
    "accessibility_inclusivity": 20, # colorblind modes, difficulty options, control remapping
    "polish_juiciness": 35,           # particle effects, screen shake, UI feedback, animation juice
}

TOTAL_POINTS = sum(RUBRIC_WEIGHTS.values())


def _score_technical_correctness(tests: dict) -> tuple[float, dict]:
    """Score test pass rate and criteria coverage (40 pts)."""
    passed = int(tests.get("passed", 0))
    failed = int(tests.get("failed", 0))
    criteria_total = max(int(tests.get("criteria_total", 0)), passed + failed)
    total = passed + failed

    if total == 0 or criteria_total == 0:
        return 0.0, {
            "score": 0.0,
            "note": "no tests executed or no acceptance criteria defined",
            "details": {"passed": passed, "failed": failed, "criteria_total": criteria_total}
        }

    coverage = min(1.0, total / criteria_total)
    pass_rate = passed / total
    pts = pass_rate * coverage * RUBRIC_WEIGHTS["technical_correctness"]

    return pts, {
        "score": pts,
        "note": f"{passed}/{total} tests passed; coverage {total}/{criteria_total} declared criteria",
        "pass_rate": pass_rate,
        "coverage": coverage,
        "details": {"passed": passed, "failed": failed, "criteria_total": criteria_total}
    }


def _score_stability_performance(telemetry: dict) -> tuple[float, dict]:
    """Score stability and performance (25 pts)."""
    pts = 0.0
    notes = []
    details = {}

    # Crash-free (15 pts)
    if telemetry.get("crash_free") is True:
        pts += 15
        notes.append("crash-free (15/15)")
        details["crash_free"] = True
    else:
        notes.append("crash evidence or unknown (0/15)")
        details["crash_free"] = False

    # FPS performance (5 pts)
    fps, target = telemetry.get("fps"), telemetry.get("target_fps", 60)
    if fps is not None:
        if float(fps) >= float(target):
            pts += 5
            notes.append(f"fps {fps} >= {target} (5/5)")
            details["fps_meets_target"] = True
        else:
            notes.append(f"fps {fps} < target {target} (0/5)")
            details["fps_meets_target"] = False
    else:
        notes.append("fps unmeasured (0/5)")
        details["fps_meets_target"] = None

    # Unbounded growth (5 pts)
    if telemetry.get("unbounded_growth") is False:
        pts += 5
        notes.append("no unbounded growth (5/5)")
        details["unbounded_growth"] = False
    else:
        notes.append("growth unmeasured or unbounded (0/5)")
        details["unbounded_growth"] = True

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_design_checklist(checklist: dict) -> tuple[float, dict]:
    """Score design checklist (20 pts)."""
    items = ("feedback", "consistency", "meaningful_parameters", "fail_safety", "balance_sanity")
    per_item = RUBRIC_WEIGHTS["design_checklist"] / len(items)
    earned = [item for item in items if checklist.get(item) is True]
    missed = [item for item in items if checklist.get(item) is not True]

    pts = per_item * len(earned)
    note = f"met: {', '.join(earned) or 'none'}"
    if missed:
        note += f" | missed: {', '.join(missed)}"

    return pts, {
        "score": pts,
        "note": note,
        "earned": earned,
        "missed": missed,
        "details": {item: checklist.get(item, False) for item in items}
    }


def _score_spec_fidelity(fidelity: float) -> tuple[float, dict]:
    """Score spec fidelity (15 pts)."""
    fidelity_fraction = float(fidelity) if fidelity is not None else 0.0
    pts = fidelity_fraction * RUBRIC_WEIGHTS["spec_fidelity"]

    return pts, {
        "score": pts,
        "note": f"spec fidelity {fidelity_fraction:.1%}",
        "fidelity": fidelity_fraction
    }


def _score_player_immersion(immersion: dict) -> tuple[float, dict]:
    """Score player immersion (50 pts) — moment-to-moment feel, animation, visual polish, audio-visual sync."""
    pts = 0.0
    details = {}
    notes = []

    # Moment-to-moment feel (12 pts)
    if immersion.get("moment_to_moment_feel_quality") in ("AAA", "high"):
        pts += 12
        notes.append("moment-to-moment feel (AAA/high) (12/12)")
        details["moment_to_moment"] = 12
    elif immersion.get("moment_to_moment_feel_quality") in ("moderate", "mid"):
        pts += 6
        notes.append("moment-to-moment feel (moderate) (6/12)")
        details["moment_to_moment"] = 6
    else:
        notes.append("moment-to-moment feel (low/none) (0/12)")
        details["moment_to_moment"] = 0

    # Animation smoothness (12 pts)
    if immersion.get("animation_smoothness") in ("60fps+", "fluid"):
        pts += 12
        notes.append("animation smoothness (60fps+/fluid) (12/12)")
        details["animation"] = 12
    elif immersion.get("animation_smoothness") in ("30fps+", "acceptable"):
        pts += 6
        notes.append("animation smoothness (30fps+/acceptable) (6/12)")
        details["animation"] = 6
    else:
        notes.append("animation smoothness (low/choppy) (0/12)")
        details["animation"] = 0

    # Visual polish (13 pts)
    if immersion.get("visual_polish") in ("AAA", "high"):
        pts += 13
        notes.append("visual polish (AAA/high) (13/13)")
        details["visual_polish"] = 13
    elif immersion.get("visual_polish") in ("moderate", "mid"):
        pts += 7
        notes.append("visual polish (moderate) (7/13)")
        details["visual_polish"] = 7
    else:
        notes.append("visual polish (low/debug) (0/13)")
        details["visual_polish"] = 0

    # Audio-visual synchronization (13 pts)
    if immersion.get("audio_visual_sync") is True:
        pts += 13
        notes.append("audio-visual sync (13/13)")
        details["audio_visual_sync"] = 13
    else:
        notes.append("audio-visual sync (missing/poor) (0/13)")
        details["audio_visual_sync"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_gameplay_flow(flow: dict) -> tuple[float, dict]:
    """Score gameplay flow (40 pts) — pacing, progression clarity, reward cadence, difficulty tuning."""
    pts = 0.0
    details = {}
    notes = []

    # Pacing (10 pts)
    if flow.get("pacing") in ("AAA", "excellent"):
        pts += 10
        notes.append("pacing (AAA/excellent) (10/10)")
        details["pacing"] = 10
    elif flow.get("pacing") in ("good", "moderate"):
        pts += 5
        notes.append("pacing (good/moderate) (5/10)")
        details["pacing"] = 5
    else:
        notes.append("pacing (poor/undefined) (0/10)")
        details["pacing"] = 0

    # Progression clarity (10 pts)
    if flow.get("progression_clarity") in ("clear", "intuitive"):
        pts += 10
        notes.append("progression clarity (clear/intuitive) (10/10)")
        details["progression"] = 10
    elif flow.get("progression_clarity") in ("partial", "moderate"):
        pts += 5
        notes.append("progression clarity (partial/moderate) (5/10)")
        details["progression"] = 5
    else:
        notes.append("progression clarity (unclear/confusing) (0/10)")
        details["progression"] = 0

    # Reward cadence (10 pts)
    if flow.get("reward_cadence") in ("satisfying", "AAA"):
        pts += 10
        notes.append("reward cadence (satisfying/AAA) (10/10)")
        details["rewards"] = 10
    elif flow.get("reward_cadence") in ("present", "adequate"):
        pts += 5
        notes.append("reward cadence (present/adequate) (5/10)")
        details["rewards"] = 5
    else:
        notes.append("reward cadence (absent/weak) (0/10)")
        details["rewards"] = 0

    # Difficulty tuning (10 pts)
    if flow.get("difficulty_tuning") in ("balanced", "engaging"):
        pts += 10
        notes.append("difficulty tuning (balanced/engaging) (10/10)")
        details["difficulty"] = 10
    elif flow.get("difficulty_tuning") in ("present", "attempted"):
        pts += 5
        notes.append("difficulty tuning (present/attempted) (5/10)")
        details["difficulty"] = 5
    else:
        notes.append("difficulty tuning (absent/trivial) (0/10)")
        details["difficulty"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_systems_depth(systems: dict) -> tuple[float, dict]:
    """Score systems depth (30 pts) — mechanical interdependencies, emergent complexity, player agency."""
    pts = 0.0
    details = {}
    notes = []

    # Mechanical interdependencies (10 pts)
    if systems.get("mechanical_interdependencies") in ("high", "complex"):
        pts += 10
        notes.append("mechanical interdependencies (high/complex) (10/10)")
        details["interdependencies"] = 10
    elif systems.get("mechanical_interdependencies") in ("moderate", "some"):
        pts += 5
        notes.append("mechanical interdependencies (moderate/some) (5/10)")
        details["interdependencies"] = 5
    else:
        notes.append("mechanical interdependencies (low/siloed) (0/10)")
        details["interdependencies"] = 0

    # Emergent complexity (10 pts)
    if systems.get("emergent_complexity") is True:
        pts += 10
        notes.append("emergent complexity (true) (10/10)")
        details["emergent"] = 10
    else:
        notes.append("emergent complexity (false/linear) (0/10)")
        details["emergent"] = 0

    # Player agency (10 pts)
    if systems.get("player_agency") in ("high", "meaningful"):
        pts += 10
        notes.append("player agency (high/meaningful) (10/10)")
        details["agency"] = 10
    elif systems.get("player_agency") in ("moderate", "limited"):
        pts += 5
        notes.append("player agency (moderate/limited) (5/10)")
        details["agency"] = 5
    else:
        notes.append("player agency (low/scripted) (0/10)")
        details["agency"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_visual_fidelity(visual: dict) -> tuple[float, dict]:
    """Score visual fidelity (35 pts) — lighting, material detail, environmental storytelling, LOD performance."""
    pts = 0.0
    details = {}
    notes = []

    # Lighting quality (9 pts)
    if visual.get("lighting_quality") in ("AAA", "realistic"):
        pts += 9
        notes.append("lighting quality (AAA/realistic) (9/9)")
        details["lighting"] = 9
    elif visual.get("lighting_quality") in ("good", "stylized"):
        pts += 5
        notes.append("lighting quality (good/stylized) (5/9)")
        details["lighting"] = 5
    else:
        notes.append("lighting quality (poor/flat) (0/9)")
        details["lighting"] = 0

    # Material detail (9 pts)
    if visual.get("material_detail") in ("AAA", "PBR-high"):
        pts += 9
        notes.append("material detail (AAA/PBR-high) (9/9)")
        details["materials"] = 9
    elif visual.get("material_detail") in ("good", "PBR-moderate"):
        pts += 5
        notes.append("material detail (good/PBR-moderate) (5/9)")
        details["materials"] = 5
    else:
        notes.append("material detail (poor/placeholder) (0/9)")
        details["materials"] = 0

    # Environmental storytelling (9 pts)
    if visual.get("environmental_storytelling") is True:
        pts += 9
        notes.append("environmental storytelling (true) (9/9)")
        details["storytelling"] = 9
    elif visual.get("environmental_storytelling") in ("partial", "minimal"):
        pts += 4
        notes.append("environmental storytelling (partial/minimal) (4/9)")
        details["storytelling"] = 4
    else:
        notes.append("environmental storytelling (false/none) (0/9)")
        details["storytelling"] = 0

    # LOD performance (8 pts)
    if visual.get("lod_performance") in ("optimized", "AAA"):
        pts += 8
        notes.append("LOD performance (optimized/AAA) (8/8)")
        details["lod"] = 8
    elif visual.get("lod_performance") in ("acceptable", "moderate"):
        pts += 4
        notes.append("LOD performance (acceptable/moderate) (4/8)")
        details["lod"] = 4
    else:
        notes.append("LOD performance (poor/missing) (0/8)")
        details["lod"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_audio_design(audio: dict) -> tuple[float, dict]:
    """Score audio design (25 pts) — diegetic/non-diegetic mix, feedback responsiveness, ambient richness."""
    pts = 0.0
    details = {}
    notes = []

    # Diegetic/non-diegetic mix (8 pts)
    if audio.get("diegetic_nondiegetic_mix") in ("AAA", "balanced"):
        pts += 8
        notes.append("diegetic/non-diegetic mix (AAA/balanced) (8/8)")
        details["mix"] = 8
    elif audio.get("diegetic_nondiegetic_mix") in ("present", "adequate"):
        pts += 4
        notes.append("diegetic/non-diegetic mix (present/adequate) (4/8)")
        details["mix"] = 4
    else:
        notes.append("diegetic/non-diegetic mix (poor/missing) (0/8)")
        details["mix"] = 0

    # Feedback responsiveness (9 pts)
    if audio.get("feedback_responsiveness") in ("tight", "AAA"):
        pts += 9
        notes.append("feedback responsiveness (tight/AAA) (9/9)")
        details["feedback"] = 9
    elif audio.get("feedback_responsiveness") in ("adequate", "moderate"):
        pts += 5
        notes.append("feedback responsiveness (adequate/moderate) (5/9)")
        details["feedback"] = 5
    else:
        notes.append("feedback responsiveness (poor/delayed) (0/9)")
        details["feedback"] = 0

    # Ambient richness (8 pts)
    if audio.get("ambient_richness") in ("immersive", "AAA"):
        pts += 8
        notes.append("ambient richness (immersive/AAA) (8/8)")
        details["ambient"] = 8
    elif audio.get("ambient_richness") in ("present", "adequate"):
        pts += 4
        notes.append("ambient richness (present/adequate) (4/8)")
        details["ambient"] = 4
    else:
        notes.append("ambient richness (sparse/none) (0/8)")
        details["ambient"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_narrative_worldbuilding(narrative: dict) -> tuple[float, dict]:
    """Score narrative & world building (30 pts) — lore consistency, character development, world coherence."""
    pts = 0.0
    details = {}
    notes = []

    # Lore consistency (10 pts)
    if narrative.get("lore_consistency") in ("high", "airtight"):
        pts += 10
        notes.append("lore consistency (high/airtight) (10/10)")
        details["lore"] = 10
    elif narrative.get("lore_consistency") in ("moderate", "consistent"):
        pts += 5
        notes.append("lore consistency (moderate/consistent) (5/10)")
        details["lore"] = 5
    else:
        notes.append("lore consistency (low/contradictory) (0/10)")
        details["lore"] = 0

    # Character development (10 pts)
    if narrative.get("character_development") in ("deep", "compelling"):
        pts += 10
        notes.append("character development (deep/compelling) (10/10)")
        details["characters"] = 10
    elif narrative.get("character_development") in ("present", "functional"):
        pts += 5
        notes.append("character development (present/functional) (5/10)")
        details["characters"] = 5
    else:
        notes.append("character development (minimal/absent) (0/10)")
        details["characters"] = 0

    # World coherence (10 pts)
    if narrative.get("world_coherence") in ("high", "believable"):
        pts += 10
        notes.append("world coherence (high/believable) (10/10)")
        details["world"] = 10
    elif narrative.get("world_coherence") in ("moderate", "adequate"):
        pts += 5
        notes.append("world coherence (moderate/adequate) (5/10)")
        details["world"] = 5
    else:
        notes.append("world coherence (low/fragmented) (0/10)")
        details["world"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_accessibility_inclusivity(access: dict) -> tuple[float, dict]:
    """Score accessibility & inclusivity (20 pts) — colorblind modes, difficulty options, control remapping."""
    pts = 0.0
    details = {}
    notes = []

    # Colorblind modes (7 pts)
    if access.get("colorblind_modes") is True:
        pts += 7
        notes.append("colorblind modes (true) (7/7)")
        details["colorblind"] = 7
    else:
        notes.append("colorblind modes (false) (0/7)")
        details["colorblind"] = 0

    # Difficulty options (7 pts)
    if access.get("difficulty_options") is True:
        pts += 7
        notes.append("difficulty options (true) (7/7)")
        details["difficulty"] = 7
    else:
        notes.append("difficulty options (false) (0/7)")
        details["difficulty"] = 0

    # Control remapping (6 pts)
    if access.get("control_remapping") is True:
        pts += 6
        notes.append("control remapping (true) (6/6)")
        details["controls"] = 6
    else:
        notes.append("control remapping (false) (0/6)")
        details["controls"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def _score_polish_juiciness(polish: dict) -> tuple[float, dict]:
    """Score polish & juiciness (35 pts) — particle effects, screen shake, UI feedback, animation juice."""
    pts = 0.0
    details = {}
    notes = []

    # Particle effects (9 pts)
    if polish.get("particle_effects") in ("AAA", "abundant"):
        pts += 9
        notes.append("particle effects (AAA/abundant) (9/9)")
        details["particles"] = 9
    elif polish.get("particle_effects") in ("present", "adequate"):
        pts += 5
        notes.append("particle effects (present/adequate) (5/9)")
        details["particles"] = 5
    else:
        notes.append("particle effects (sparse/none) (0/9)")
        details["particles"] = 0

    # Screen shake (9 pts)
    if polish.get("screen_shake") in ("impactful", "AAA"):
        pts += 9
        notes.append("screen shake (impactful/AAA) (9/9)")
        details["shake"] = 9
    elif polish.get("screen_shake") in ("present", "subtle"):
        pts += 5
        notes.append("screen shake (present/subtle) (5/9)")
        details["shake"] = 5
    else:
        notes.append("screen shake (absent/weak) (0/9)")
        details["shake"] = 0

    # UI feedback (9 pts)
    if polish.get("ui_feedback") in ("responsive", "AAA"):
        pts += 9
        notes.append("UI feedback (responsive/AAA) (9/9)")
        details["ui"] = 9
    elif polish.get("ui_feedback") in ("adequate", "functional"):
        pts += 5
        notes.append("UI feedback (adequate/functional) (5/9)")
        details["ui"] = 5
    else:
        notes.append("UI feedback (poor/missing) (0/9)")
        details["ui"] = 0

    # Animation juice (8 pts)
    if polish.get("animation_juice") in ("abundant", "AAA"):
        pts += 8
        notes.append("animation juice (abundant/AAA) (8/8)")
        details["juice"] = 8
    elif polish.get("animation_juice") in ("present", "adequate"):
        pts += 4
        notes.append("animation juice (present/adequate) (4/8)")
        details["juice"] = 4
    else:
        notes.append("animation juice (minimal/none) (0/8)")
        details["juice"] = 0

    return pts, {
        "score": pts,
        "note": "; ".join(notes),
        "details": details
    }


def grade_feature_aaa_expanded(feature_name: str, evidence: dict, benchmark_titles: list = None) -> dict:
    """Grade a feature across 12 AAA game development dimensions (400-point scale).

    Args:
        feature_name: Name of the feature being graded
        evidence: Evidence dict with keys like "tests", "telemetry", "checklist", "spec_fidelity",
                  "immersion", "flow", "systems", "visual", "audio", "narrative", "access", "polish"
        benchmark_titles: List of AAA benchmark games for comparison

    Returns:
        Comprehensive grading dict with all 12 dimension scores, overall score, and study guide.
    """
    benchmark_titles = benchmark_titles or []

    # Score all 12 dimensions
    correctness_pts, correctness_detail = _score_technical_correctness(evidence.get("tests", {}))
    stability_pts, stability_detail = _score_stability_performance(evidence.get("telemetry", {}))
    checklist_pts, checklist_detail = _score_design_checklist(evidence.get("checklist", {}))
    fidelity_pts, fidelity_detail = _score_spec_fidelity(evidence.get("spec_fidelity", 0.0))
    immersion_pts, immersion_detail = _score_player_immersion(evidence.get("immersion", {}))
    flow_pts, flow_detail = _score_gameplay_flow(evidence.get("flow", {}))
    systems_pts, systems_detail = _score_systems_depth(evidence.get("systems", {}))
    visual_pts, visual_detail = _score_visual_fidelity(evidence.get("visual", {}))
    audio_pts, audio_detail = _score_audio_design(evidence.get("audio", {}))
    narrative_pts, narrative_detail = _score_narrative_worldbuilding(evidence.get("narrative", {}))
    access_pts, access_detail = _score_accessibility_inclusivity(evidence.get("access", {}))
    polish_pts, polish_detail = _score_polish_juiciness(evidence.get("polish", {}))

    # Calculate totals
    total_pts = (correctness_pts + stability_pts + checklist_pts + fidelity_pts +
                 immersion_pts + flow_pts + systems_pts + visual_pts + audio_pts +
                 narrative_pts + access_pts + polish_pts)
    overall_percentage = (total_pts / TOTAL_POINTS) * 100

    # Letter grade (AAA standard scale)
    if overall_percentage >= 85:
        letter_grade = "A+"
    elif overall_percentage >= 75:
        letter_grade = "A"
    elif overall_percentage >= 65:
        letter_grade = "B"
    elif overall_percentage >= 50:
        letter_grade = "C"
    else:
        letter_grade = "F"

    # Build comprehensive study guide for refinement
    study_guide = []

    if correctness_pts < RUBRIC_WEIGHTS["technical_correctness"] * 0.75:
        study_guide.append(f"⚠ Technical Correctness ({correctness_pts:.0f}/{RUBRIC_WEIGHTS['technical_correctness']}): {correctness_detail['note']}")

    if immersion_pts < RUBRIC_WEIGHTS["player_immersion"] * 0.75:
        study_guide.append(f"⚠ Player Immersion ({immersion_pts:.0f}/{RUBRIC_WEIGHTS['player_immersion']}): {immersion_detail['note']}")

    if visual_pts < RUBRIC_WEIGHTS["visual_fidelity"] * 0.75:
        study_guide.append(f"⚠ Visual Fidelity ({visual_pts:.0f}/{RUBRIC_WEIGHTS['visual_fidelity']}): {visual_detail['note']}")

    if polish_pts < RUBRIC_WEIGHTS["polish_juiciness"] * 0.75:
        study_guide.append(f"⚠ Polish & Juiciness ({polish_pts:.0f}/{RUBRIC_WEIGHTS['polish_juiciness']}): {polish_detail['note']}")

    if flow_pts < RUBRIC_WEIGHTS["gameplay_flow"] * 0.75:
        study_guide.append(f"⚠ Gameplay Flow ({flow_pts:.0f}/{RUBRIC_WEIGHTS['gameplay_flow']}): {flow_detail['note']}")

    if systems_pts < RUBRIC_WEIGHTS["systems_depth"] * 0.75:
        study_guide.append(f"⚠ Systems Depth ({systems_pts:.0f}/{RUBRIC_WEIGHTS['systems_depth']}): {systems_detail['note']}")

    # Build result dict
    result = {
        "feature": feature_name,
        "overall_percentage": overall_percentage,
        "letter_grade": letter_grade,
        "total_score": total_pts,
        "total_possible": TOTAL_POINTS,
        "benchmark_titles": benchmark_titles,
        "dimensions": {
            "technical_correctness": {
                "score": correctness_pts,
                "possible": RUBRIC_WEIGHTS["technical_correctness"],
                "detail": correctness_detail
            },
            "stability_performance": {
                "score": stability_pts,
                "possible": RUBRIC_WEIGHTS["stability_performance"],
                "detail": stability_detail
            },
            "design_checklist": {
                "score": checklist_pts,
                "possible": RUBRIC_WEIGHTS["design_checklist"],
                "detail": checklist_detail
            },
            "spec_fidelity": {
                "score": fidelity_pts,
                "possible": RUBRIC_WEIGHTS["spec_fidelity"],
                "detail": fidelity_detail
            },
            "player_immersion": {
                "score": immersion_pts,
                "possible": RUBRIC_WEIGHTS["player_immersion"],
                "detail": immersion_detail
            },
            "gameplay_flow": {
                "score": flow_pts,
                "possible": RUBRIC_WEIGHTS["gameplay_flow"],
                "detail": flow_detail
            },
            "systems_depth": {
                "score": systems_pts,
                "possible": RUBRIC_WEIGHTS["systems_depth"],
                "detail": systems_detail
            },
            "visual_fidelity": {
                "score": visual_pts,
                "possible": RUBRIC_WEIGHTS["visual_fidelity"],
                "detail": visual_detail
            },
            "audio_design": {
                "score": audio_pts,
                "possible": RUBRIC_WEIGHTS["audio_design"],
                "detail": audio_detail
            },
            "narrative_worldbuilding": {
                "score": narrative_pts,
                "possible": RUBRIC_WEIGHTS["narrative_worldbuilding"],
                "detail": narrative_detail
            },
            "accessibility_inclusivity": {
                "score": access_pts,
                "possible": RUBRIC_WEIGHTS["accessibility_inclusivity"],
                "detail": access_detail
            },
            "polish_juiciness": {
                "score": polish_pts,
                "possible": RUBRIC_WEIGHTS["polish_juiciness"],
                "detail": polish_detail
            }
        },
        "study_guide": study_guide if study_guide else ["✓ All dimensions scored at 75%+ — excellent AAA-level quality"]
    }

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AAA-Expanded Result Grader")
    parser.add_argument("--feature", required=True, help="Feature name")
    parser.add_argument("--evidence", required=True, help="Path to evidence JSON file")
    parser.add_argument("--benchmark", nargs="*", help="Benchmark game titles for comparison")
    args = parser.parse_args()

    with open(args.evidence, 'r') as f:
        evidence = json.load(f)

    result = grade_feature_aaa_expanded(args.feature, evidence, args.benchmark)
    print(json.dumps(result, indent=2))
