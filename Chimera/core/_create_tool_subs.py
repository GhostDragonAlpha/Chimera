"""Create 3 Tool sub-features: Scanner_Tool_Implementation, Tool_Durability_Maintenance, Tool_Crafting_System
Each with 26 answered questions (12 node + 5 edge + 5 meta + 4 mirror = 26).
Records each in the DNA graph via graphify_record."""

import json
import datetime
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feature_graph import create_feature, answer_question, load_feature, FEATURES_DIR

FEATURES = {
    "Scanner_Tool_Implementation": {
        "description": "The core handheld scanner tool: equip, aim, scan, read-out. Real-time geological/mineral/atmospheric data collection with educational contextual feedback.",
        "loop": 4,
        "questions": [
            # --- NODE CATEGORIES (12) ---
            ("education", "Does the scanner teach real geological identification through in-game analysis?",
             "Yes. Scanner classifies rock types by grain size, color, hardness, and effervescence. Player learns to identify basalt vs. granite vs. sandstone by observable properties, not just labels."),
            ("fame", "Does the scanner generate screenshot-worthy 'discovery' moments?",
             "Yes. Full scan readout with cross-sectional terrain analysis and annotated mineral layers makes a visually impressive screenshot. Rich HUD overlay with real data is shareable."),
            ("world", "Does the scanner give meaningful data that changes by location and time?",
             "Yes. Scans differ by biome, altitude, time of day, and weather. Mineral composition, atmosphere, POIs, and hazard warnings all vary dynamically. World feels alive and scientific."),
            ("shipping", "Can the scanner be prototyped in one sprint using existing patterns?",
             "Yes. Scanner equips to tool slot using existing Verb_Look/tool-switching patterns. UMG readout display uses standard widgets. Core scan raycast + mineral ID can be built in 3-5 days."),
            ("foundation", "Is scanner logic data-driven and extendable?",
             "Yes. Mineral definitions, atmosphere tables, hardness values, and scan range are DataTable-driven. Adding new minerals or gases requires only data changes."),
            ("platform", "Does the scanner work in UE5.8 without hacks?",
             "Yes. Uses GAS (Gameplay Ability System), UMG widgets, line traces -- all standard UE5.8 subsystems. No engine modifications needed."),
            ("performance", "Does the scanner run at 30+ fps on RTX 3060?",
             "Yes. Scanner uses a single line trace on activation (negligible CPU cost), simple data lookup, and lightweight UMG overlay. No GPU impact."),
            ("accessibility", "Can a colorblind or hearing-impaired player fully use the scanner?",
             "Yes. Results are primarily text-based with icons. Mineral ID uses shape + text, not color-only. Audio scan sound is supplementary."),
            ("audio", "Does the scanner have distinctive sound design?",
             "v1: equip hum, charge-up ascending tone, data-burst release, result ping -- all achievable with synthetic audio. No dedicated audio team needed for prototype."),
            ("multiplayer", "Does the scanner work in multiplayer?",
             "v1 is single-player. Each player has own scanner; scan results are independent. Scan data sharing is v2."),
            ("modding", "Can the community add new scannable items?",
             "Yes. Mineral and atmosphere data tables are JSON/DataTable. Modders add new scannables, data categories, and custom scan feedback."),
            ("localization", "Can scanner data be localized?",
             "Yes. All mineral names, descriptions, property labels, and measurement units use UE5 FText. Scientific symbols and numbers are locale-friendly."),
            # --- EDGE CATEGORIES (5) ---
            ("depends_on", "Does Scanner_Tool_Implementation depend on Tool_Systems parent?",
             "Yes. Tool_Systems provides the tool-equip framework, slot system, and tool-switching input. Scanner is one tool type within that system."),
            ("proves", "Does Scanner_Tool_Implementation prove educational tools are viable in UE5?",
             "Yes. A working scanner with real scientific data output proves educational content can be delivered through gameplay tools, not menus or text boxes."),
            ("derived_from", "Was Scanner_Tool_Implementation derived from Tool_Systems Q1 (educational science)?",
             "Yes. Tool_Systems Q1 asked 'Do tools teach real science through their use?' and answered yes. This sub-feature materializes that answer as a specific tool."),
            ("conflicts", "Does scanner conflict with the environmental demo focus?",
             "No. Scanner enhances the environmental demo. A canyon scan revealing strata layers is a highlight moment that showcases both the environment AND the educational tool."),
            ("requires", "What UE5 knowledge is required for scanner implementation?",
             "GAS, line traces, UMG widgets, data tables. Moderate difficulty. Core scanning logic is ~1 week for a UE5-capable C++ developer."),
            # --- META QUESTIONS (5) ---
            ("depth", "Does this need sub-features or is it detailed enough?",
             "Detailed enough at this level. Future sub-features: Scanner_Mineral_Database, Scanner_Atmosphere_Analyzer, Scanner_Discovery_Log."),
            ("breadth", "Are siblings missing at this level?",
             "No. Scanner (core tool), Durability (lifecycle), Crafting (creation) form the complete tool system triad."),
            ("parent", "Is Tool_Systems complete enough to support this?",
             "Yes. Tool_Systems is at DESIGNED status with all 41 questions answered."),
            ("priority", "Should Scanner_Tool_Implementation be built before its siblings?",
             "Yes. Scanner is the highest-priority tool as it directly supports the educational mission and environmental demo."),
            ("dependency", "Does Scanner_Tool_Implementation block other features?",
             "Partially. Tool_Crafting_System benefits from scanner (identifying materials) but does not require it. Tool_Durability is independent."),
            # --- MIRROR QUESTIONS (4) ---
            ("vision", "Does Scanner_Tool_Implementation serve the educational RPG goal?",
             "Yes. Scanner is the primary educational tool. Through scanning, players learn real geology, meteorology, and astronomy."),
            ("tradeoff", "What is sacrificed by building scanner now?",
             "Building scanner prioritizes educational tool depth over other tool types (weapon, construction). Acceptable: scanner is the most educational tool."),
            ("evidence", "What evidence shows real-data scanners drive engagement?",
             "Elite Dangerous' discovery scanner and No Man's Sky's analysis visor prove scan-based gameplay with real data is deeply engaging."),
            ("terminal", "Does scanner chain reach a human learning something real?",
             "Yes. Player learns geological identification, Mohs hardness scale, atmospheric science -- transferable scientific literacy skills."),
        ]
    },
    "Tool_Durability_Maintenance": {
        "description": "Tool degradation over use, material-dependent wear rates, repair mechanics with tools and workstations, and maintenance as a gameplay loop.",
        "loop": 4,
        "questions": [
            # --- NODE CATEGORIES (12) ---
            ("education", "Does tool durability teach real material science principles?",
             "Yes. Different materials wear at different rates: stone chips quickly, iron lasts longer, steel longest. Player learns material choice affects lifespan -- a real engineering principle."),
            ("fame", "Does tool degradation create compelling emergent gameplay moments?",
             "Yes. A tool breaking at a critical moment creates emergent tension and memorable stories. Multi-stage degradation (pristine/worn/damaged/broken) is deeper than binary durability in competitors."),
            ("world", "Does tool wear feel physically grounded by material interaction?",
             "Yes. Tools degrade based on target: scanning hard rock wears lens faster than soft soil; digging frozen ground wears shovel faster than loam. Wear reflects real physics."),
            ("shipping", "Can durability be prototyped in one sprint using existing patterns?",
             "Yes. Durability counter + wear-on-use + visual states + basic field repair can be prototyped in 3-5 days. Uses UE5 health/damage pattern."),
            ("foundation", "Is durability system data-driven and extendable?",
             "Yes. Material wear rates, repair costs, degradation thresholds, and visual condition mappings are DataTable-driven. Designer tunes by editing data."),
            ("platform", "Does durability work in UE5.8 without hacks?",
             "Yes. UHealthComponent pattern, surface material system, mesh material swapping -- all standard UE5.8. No engine modifications."),
            ("performance", "Does durability tracking impact performance on RTX 3060?",
             "No. Durability is integer arithmetic per use (negligible). Visual degradation is pre-baked material parameter swap. No runtime cost."),
            ("accessibility", "Can a colorblind or hearing-impaired player perceive tool condition?",
             "Yes. Visual degradation states use distinct mesh changes (cracks, dents, missing parts), not color alone. Text durability readout when inspecting tool."),
            ("audio", "Does durability have distinctive sound feedback?",
             "v1: wear sounds per use (scratches, creaks), break sound (snap/crackle), repair sounds (hammer clink, file scrape). Achievable with synthetic audio."),
            ("multiplayer", "Does durability syncing work in multiplayer?",
             "v1 is single-player. Multiplayer needs per-player tool state replication. Each player's tool durability is persisted independently."),
            ("modding", "Can community create custom durability behaviors?",
             "Yes. Wear rate tables, repair recipes, and degradation visual sets are data-driven. Modders define unique durability curves for custom tools."),
            ("localization", "Can durability system be localized?",
             "Yes. Condition names, repair instructions, and descriptions use FText. Numerical values (durability %, repair cost) are locale-formatted."),
            # --- EDGE CATEGORIES (5) ---
            ("depends_on", "Does Tool_Durability_Maintenance depend on Tool_Systems parent?",
             "Yes. Tools must exist before they can degrade. Tool_Systems provides the tool framework and slot system. Durability applies to any tool type."),
            ("proves", "Does durability prove that material science can be a compelling game mechanic?",
             "Yes. Material-dependent wear rates and repair requirements prove real science principles create engaging gameplay, not just educational overhead."),
            ("derived_from", "Was Tool_Durability_Maintenance derived from Tool_Systems Q10 (degradation)?",
             "Yes. Tool_Systems Q10 asked 'Do tools degrade or need maintenance?' and answered yes. This sub-feature materializes that answer as a concrete durability and repair system."),
            ("conflicts", "Does durability conflict with accessible gameplay?",
             "No. Durability adds depth without tedium. Auto-repair at stations is available. Player chooses engagement level."),
            ("requires", "What UE5 knowledge is required for durability system?",
             "UHealthComponent pattern, surface material system, mesh component state management. Low-medium difficulty. 3-5 days for core loop."),
            # --- META QUESTIONS (5) ---
            ("depth", "Does this need sub-features?",
             "Not at this level. Future sub-features: Tool_Condition_Visuals, Tool_Repair_Recipes, Workstation_Repair_System."),
            ("breadth", "Are siblings missing at this level?",
             "No. Scanner (discovery), Durability (lifecycle), Crafting (creation) form the complete tool system."),
            ("parent", "Is Tool_Systems complete enough for this?",
             "Yes. Tool_Systems confirmed tool degradation, maintenance, and material interactions at DESIGNED status."),
            ("priority", "Should Tool_Durability_Maintenance be built before or after siblings?",
             "Build second, after Scanner_Tool_Implementation. Scanner gives a concrete tool to test durability on."),
            ("dependency", "What does durability block?",
             "Blocks crafting system (crafting produces tools that need durability). Does not block scanner."),
            # --- MIRROR QUESTIONS (4) ---
            ("vision", "Does durability system serve the educational RPG goal?",
             "Yes. Durability teaches material science, entropy, and preventative maintenance. Every broken and repaired tool is a lesson in real materials behavior."),
            ("tradeoff", "What is sacrificed by building durability now?",
             "Durability adds complexity to every tool interaction. Risk mitigated by: auto-repair stations, clear visual feedback, and educational framing."),
            ("evidence", "What evidence shows durability systems improve games?",
             "Zelda: Breath of the Wild's weapon durability proved breakable tools create emergent gameplay. Minecraft's tool durability is a core engagement loop."),
            ("terminal", "Does durability chain reach a human learning something real?",
             "Yes. Player learns: wear rates depend on material hardness vs. target, preventative maintenance is more efficient than reactive repair."),
        ]
    },
    "Tool_Crafting_System": {
        "description": "Building tools from raw materials: assembly at crafting stations, material properties affecting tool stats, upgrade paths, and creative tool combinations.",
        "loop": 4,
        "questions": [
            # --- NODE CATEGORIES (12) ---
            ("education", "Does crafting teach real materials engineering and tool design?",
             "Yes. Tool stats depend on material properties: density, tensile strength, hardness, thermal conductivity. Player chooses head/handle/binding materials with real engineering tradeoffs."),
            ("fame", "Does tool crafting generate shareable 'look what I made' content?",
             "Yes. Material-property-driven crafting means every tool is unique. 'I built a tungsten-tipped drill with carbon-fiber handle' is shareable achievement content."),
            ("world", "Are crafting materials distributed realistically across the world?",
             "Yes. Materials follow real geology: basalt in volcanic regions, hematite in iron deposits, chert in chalk formations. Player learns real geology by gathering."),
            ("shipping", "Can basic crafting be prototyped in one sprint?",
             "Partially. Material-to-tool assembly with 3 material types (stone, iron, obsidian) and 2 tool schemas can be prototyped in 5-7 days. Uses existing UE5 inventory system."),
            ("foundation", "Is crafting system data-driven and extendable?",
             "Yes. Material properties, craftable schemas, and station capabilities are DataTable-driven. Adding new materials or tools requires only data changes."),
            ("platform", "Does crafting work in UE5.8 without hacks?",
             "Yes. Inventory system, UMG crafting UI, data tables, Chaos Physics assembly -- all standard UE5.8. No engine modifications."),
            ("performance", "Does crafting system impact performance on RTX 3060?",
             "No. Crafting is UI-driven with negligible CPU cost (material lookup = memory read, assembly animation = one-time event). No ongoing impact."),
            ("accessibility", "Can a colorblind or hearing-impaired player fully use crafting?",
             "Yes. Material properties shown as text + icons, not color-only. High-contrast labels. Assembly feedback is visual (tool appears on bench) with optional audio."),
            ("audio", "Does crafting have satisfying sound feedback?",
             "v1: place material (thud/click), assemble (hammer + scrape), complete (confirmation chime). Each material has distinct handling sound (stone clink, metal ring)."),
            ("multiplayer", "Does crafting work with multiple players?",
             "v1 is single-player. Multiplayer features (shared stations, collaborative assembly, material pooling) are v2."),
            ("modding", "Can community create custom tools and materials?",
             "Yes. Material property tables, crafting schemas, and station definitions are all data-driven. Modders add entire new tool tiers and material families."),
            ("localization", "Can crafting system be localized?",
             "Yes. Material names, property labels, schema names, and station names use FText. Numerical stats are locale-formatted."),
            # --- EDGE CATEGORIES (5) ---
            ("depends_on", "Does Tool_Crafting_System depend on Scanner_Tool_Implementation?",
             "Partially. Scanner identifies materials for crafting unlock. Basic crafting works with pre-scanned materials, but scan-to-craft is the designed flow."),
            ("proves", "Does crafting prove that educational engineering can BE the gameplay?",
             "Yes. Choosing materials by real engineering properties to create different-performing tools proves educational content IS the gameplay, not a layer on top."),
            ("derived_from", "Was Tool_Crafting_System derived from Tool_Systems Q11 (upgrades) and Q4 (combinations)?",
             "Yes. Tool_Systems Q11 answered 'Tools can be upgraded.' Q4 answered 'Tools can be combined.' This sub-feature materializes both as a unified crafting system."),
            ("conflicts", "Does crafting conflict with the environmental demo focus?",
             "Minor. Crafting asset creation takes time from environment art. Acceptable: crafting gives environmental resources a purpose in the core loop."),
            ("requires", "What UE5 knowledge is required for crafting system?",
             "Inventory system, UMG UI, data tables, Chaos Physics. Moderate-high difficulty. 1-2 weeks for core loop with 3 material types."),
            # --- META QUESTIONS (5) ---
            ("depth", "Does this need sub-features?",
             "Not at this level. Future sub-features: Tool_Material_Properties_Engine, Crafting_Station_Tiers, Tool_Upgrade_Paths."),
            ("breadth", "Are siblings missing at this level?",
             "No. Scanner (discovery), Durability (lifecycle), Crafting (creation) form a complete tool system: discover materials -> craft tools -> use -> maintain."),
            ("parent", "Is Tool_Systems complete enough for this?",
             "Yes. Tool_Systems confirmed tool crafting, material-based stats, and upgrade paths at DESIGNED status."),
            ("priority", "Should Tool_Crafting_System be built before or after siblings?",
             "Build third, after scanner and durability. Crafting needs scanner (material ID) and produces tools needing durability. It is the capstone."),
            ("dependency", "What does crafting system block?",
             "Blocks player tool-tier progression and the resource economy. Does not block scanner or durability."),
            # --- MIRROR QUESTIONS (4) ---
            ("vision", "Does crafting system serve the educational RPG goal?",
             "Yes. Crafting teaches materials engineering, tool design, geology (material sourcing), and resource logistics. Real engineering through making tools."),
            ("tradeoff", "What is sacrificed by building crafting now?",
             "Crafting is the most complex of the three systems (assets, UI, data tables). Building it now defers other loop-4 tools. Acceptable: crafting is foundational."),
            ("evidence", "What evidence shows material-property crafting engages players?",
             "Minecraft's wood/stone/iron/diamond tier progression and Subnautica's material-based tool crafting prove this pattern is deeply engaging in sci-fi settings."),
            ("terminal", "Does crafting chain reach a human learning real skills?",
             "Yes. Player learns: material selection determines tool performance (engineering), rock cycle determines availability (geology), logistics requires planning (supply chain)."),
        ]
    }
}


def create_feature_json(name, description, question_tuples):
    """Create a feature JSON file with exactly 26 questions answered (12 node + 5 edge + 5 meta + 4 mirror)."""
    feature = create_feature(name, description)
    q_id = 1
    for category, question, answer in question_tuples:
        is_edge = category in ["depends_on", "proves", "derived_from", "conflicts", "requires"]
        feature["questions"].append({
            "id": q_id,
            "category": category,
            "question": question,
            "is_edge": is_edge,
            "mirror_trace": None,
            "answered": True,
            "answer": answer,
        })
        q_id += 1

    feature["status"] = "designed"
    _save_feature(feature)
    print(f"[GRAPH] '{name}' FULLY DESIGNED -- {len(feature['questions'])} questions answered.")
    return feature


def _save_feature(feature):
    """Save a feature back to disk."""
    path = FEATURES_DIR / f"{feature['name'].replace(' ', '_').replace('/', '_')}.json"
    path.write_text(json.dumps(feature, indent=2), encoding="utf-8")


if __name__ == "__main__":
    for name, data in FEATURES.items():
        print(f"\n=== Creating {name} (Loop {data['loop']}) ===")
        questions = data["questions"]
        print(f"  {len(questions)} questions prepared")

        feature = create_feature_json(name, data["description"], questions)

        # Verify count
        node_count = sum(1 for q in feature["questions"] if not q["is_edge"] and q["category"] not in
                        ["depends_on", "proves", "derived_from", "conflicts", "requires",
                         "depth", "breadth", "parent", "priority", "dependency",
                         "vision", "tradeoff", "evidence", "terminal"])
        edge_count = sum(1 for q in feature["questions"] if q["is_edge"])
        meta_count = sum(1 for q in feature["questions"] if q["category"] in ["depth","breadth","parent","priority","dependency"])
        mirror_count = sum(1 for q in feature["questions"] if q["category"] in ["vision","tradeoff","evidence","terminal"])
        print(f"  Stats: Node={node_count} Edge={edge_count} Meta={meta_count} Mirror={mirror_count} Total={len(feature['questions'])}")

    print("\n=== All 3 sub-features created. Now recording in DNA graph... ===")

    # Record each in the DNA graph
    for name, data in FEATURES.items():
        cmd = [
            sys.executable, "-m", "core.graphify_record", "feature",
            "--name", name,
            "--loop", str(data["loop"]),
            "--status", "designed",
            "--param", "parent=Tool_Systems",
            "--param", f"description={data['description'][:100]}",
        ]
        print(f"\nRecording {name}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    cwd="E:/PythonChimera/Chimera", timeout=30)
            print(f"  stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                print(f"  stderr: {result.stderr.strip()}")
            if result.returncode != 0:
                print(f"  ERROR: exit code {result.returncode}")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT (30s)")

    print("\n=== Done! ===")
