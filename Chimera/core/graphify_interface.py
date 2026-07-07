import json
import hashlib
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

KNOWLEDGE_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_knowledge_graph.json")
DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

# The Critic (core/critic.py) is ADVISORY ONLY — every CriticJudgment node it records must
# carry this exact string; it never gates result_grader, GPA, or any pipeline gate (see
# docs/RESULT_GRADING_RUBRIC.md: LM judgment is tertiary/advisory everywhere in this project).
CRITIC_ADVISORY_DISCLAIMER = ("ADVISORY ONLY — LM-generated estimate, does not gate the "
                              "pipeline, does not substitute for human observation")

# Provenance: every node written by this process is stamped with who wrote it and a
# per-process run id (one pipeline run = one process = one run_id, so duplicate
# mutations within a run can be collapsed). Nodes that predate provenance get
# "legacy_pre_provenance" — timestamps older than this module's load time cannot
# have been written by this process.
RUN_ID = os.environ.get("CHIMERA_RUN_ID") or f"run_{uuid.uuid4().hex[:12]}"
RECORDED_BY = os.environ.get("CHIMERA_RECORDED_BY") or (
    os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "interactive"
)
_PROVENANCE_LOADED_AT = datetime.utcnow().isoformat()


def _stamp_provenance(nodes):
    for n in nodes:
        if isinstance(n, dict) and "recorded_by" not in n:
            if n.get("timestamp", "") < _PROVENANCE_LOADED_AT:
                n["recorded_by"] = "legacy_pre_provenance"
            else:
                n["recorded_by"] = RECORDED_BY
                n["run_id"] = RUN_ID

def load_knowledge_graph():
    if KNOWLEDGE_GRAPH_PATH.exists():
        with open(KNOWLEDGE_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": [], "metadata": {"canonical_output_dir": "E:/PythonChimera/Chimera", "module_name": "Chimera", "api_macro": "CHIMERA_API", "include_paths": ["ProceduralGenerated/Combat", "ProceduralGenerated/AI", "ProceduralGenerated/Flight", "ProceduralGenerated/PCG", "ProceduralGenerated/Stations", "ProceduralGenerated/Missions", "ProceduralGenerated/Factions", "ProceduralGenerated/Save", "ProceduralGenerated/GameMode", "ProceduralGenerated/Ships"]}}

def load_dna_graph():
    if DNA_GRAPH_PATH.exists():
        with open(DNA_GRAPH_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"nodes": [], "edges": []}

def save_knowledge_graph(graph):
    KNOWLEDGE_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def save_dna_graph(graph):
    """Atomic, lock-guarded write — concurrent writers (nightly dream_loop vs a duty
    cycle vs the sleepwalker) must never corrupt or clobber the graph (no-blockers law)."""
    import os as _os, time as _time
    _stamp_provenance(graph.get("nodes", []))
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = str(DNA_GRAPH_PATH) + ".lock"
    deadline = _time.monotonic() + 15
    fd = None
    while True:
        try:
            fd = _os.open(lock, _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
            break
        except FileExistsError:
            if _time.monotonic() > deadline:  # stale lock (crashed writer) — steal it
                try: _os.remove(lock)
                except OSError: pass
            _time.sleep(0.25)
    try:
        tmp = str(DNA_GRAPH_PATH) + ".tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(graph, f, indent=2)
        _os.replace(tmp, str(DNA_GRAPH_PATH))
    finally:
        if fd is not None:
            _os.close(fd)
        try: _os.remove(lock)
        except OSError: pass

def hash_node_id(node_type: str, identifier: str) -> str:
    return hashlib.sha256(f"{node_type}:{identifier}".encode('utf-8')).hexdigest()[:16]

def graphify_query(query_type: str, identifier: str = None, context: dict = None):
    """Unified query interface to the knowledge graph."""
    
    if query_type == "pattern":
        return _query_pattern(identifier)
        
    elif query_type == "file":
        return _query_file(identifier)
        
    elif query_type == "mutation":
        return _query_mutation(identifier)
        
    elif query_type == "community":
        return _query_community(identifier)
        
    elif query_type == "chain":
        dsl_block = identifier
        generated_file = context.get("generated_file") if context else None
        return _query_chain(dsl_block, generated_file)
        
    elif query_type == "config":
        return _query_config()
        
    elif query_type == "campus":
        return _query_campus(identifier, context)
        
    elif query_type == "health":
        dna = load_dna_graph()
        nodes = dna.get("nodes", [])
        mutations = [n for n in nodes if n.get("type") == "Mutation"]
        pathways = [n for n in nodes if n.get("type") in ("Pathway", "pathway_attempt")]
        features = [n for n in nodes if n.get("type") == "FeatureUpdate"]
        return {
            "total_nodes": len(nodes),
            "mutations": len(mutations),
            "pathways": len(pathways),
            "features": len(features)
        }
        

    elif query_type == "feature":
        return _query_feature(identifier)
        
    elif query_type == "pathway":
        return _query_pathway(identifier)

    elif query_type == "gpa":
        return _query_gpa(identifier, context)
        
    else:
        raise ValueError(f"Unknown query type: {query_type}")

def graphify_mutate(mutate_type: str, result: str = None, details: dict = None):
    """Unified mutation interface to record state changes."""
    
    if mutate_type == "compilation":
        return _mutate_compilation(result, details or {})

    elif mutate_type == "phase_complete":
        phase_details = details or {}
        if result and "result" not in phase_details:
            phase_details["result"] = result
        return _mutate_phase_complete(phase_details)

    elif mutate_type == "parse":
        return _mutate_parse(details or {})
        
    elif mutate_type == "generation":
        return _mutate_generation(details or {})
        
    elif mutate_type in ["verification", "visual_verification"]:
        return _mutate_visual_verification(result, details)

    elif mutate_type == "feature_complete":
        return _mutate_feature_complete(details or {})

    elif mutate_type == "loop_complete":
        return _mutate_loop_complete(details or {})

    elif mutate_type == "research_discovery":
        return _mutate_research_discovery(details or {})

    elif mutate_type == "professor_grade":
        return _mutate_professor_grade(details or {})

    elif mutate_type == "professor_report_card":
        return _mutate_professor_report_card(details or {})

    elif mutate_type == "pathway_attempt":
        return _mutate_pathway_attempt(details or {})

    elif mutate_type == "technical_discovery":
       return _mutate_technical_discovery(details or {})

    elif mutate_type == "heuristic":
        return _mutate_heuristic(details or {})

    elif mutate_type == "surprise":
        return _mutate_surprise(details or {})

    elif mutate_type == "observation":
        return _mutate_observation(details or {})

    elif mutate_type == "playtest":
        return _mutate_playtest(details or {})

    elif mutate_type == "simtest":
        return _mutate_simtest(details or {})

    elif mutate_type == "rollout":
        return _mutate_rollout(details or {})

    elif mutate_type == "proposal":
        return _mutate_proposal(details or {})

    elif mutate_type == "visionkeeper_judgment":
        return _mutate_visionkeeper_judgment(details or {})

    elif mutate_type == "critic_judgment":
        return _mutate_critic_judgment(details or {})

    else:
        raise ValueError(f"Unknown mutation type: {mutate_type}")

def _query_pattern(pattern_name: str) -> dict:
    """Returns the correct pattern for generating a specific class type."""
    patterns = {
        "AActor": {
            "header_template": "#pragma once\n#include \"CoreMinimal.h\"\n#include \"GameFramework/Actor.h\"\n#include \"{name}.generated.h\"\n\nUCLASS()\nclass CHIMERA_API A{name} : public AActor\n{{\n\tGENERATED_BODY()\n\npublic:\n\tA{name}();\n}};\n",
            "source_template": "// Generated code\n#include \"{name}.h\"\n\nA{name}::A{name}()\n{{\n\tPrimaryActorTick.bCanEverTick = true;\n}}\n",
            "include_paths": ["CoreMinimal.h", "GameFramework/Actor.h"],
            "api_macro": "CHIMERA_API"
        },
        "UActorComponent": {
            "header_template": "#pragma once\n#include \"CoreMinimal.h\"\n#include \"Components/ActorComponent.h\"\n#include \"{name}.generated.h\"\n\nUCLASS()\nclass CHIMERA_API U{name} : public UActorComponent\n{{\n\tGENERATED_BODY()\n\npublic:\n\tU{name}(const FObjectInitializer& ObjectInitializer);\n}};\n",
            "source_template": "// Generated code\n#include \"{name}.h\"\n\nU{name}::U{name}(const FObjectInitializer& ObjectInitializer) : Super(ObjectInitializer) {{}}\n",
            "include_paths": ["CoreMinimal.h", "Components/ActorComponent.h"],
            "api_macro": "CHIMERA_API"
        },
        "UGameInstance": {
            "header_template": '#pragma once\n#include "CoreMinimal.h"\n#include "Engine/GameInstance.h"\n#include "{name}.generated.h"\n\nUCLASS()\nclass CHIMERA_API U{name} : public UGameInstance\n{{\n\tGENERATED_BODY()\n}};\n',
            "source_template": "// Generated code\n#include \"{name}.h\"\n",
            "include_paths": ["CoreMinimal.h", "Engine/GameInstance.h"],
            "api_macro": "CHIMERA_API"
        },
        "AGameModeBase": {
            "header_template": '#pragma once\n#include "CoreMinimal.h"\n#include "GameFramework/GameModeBase.h"\n#include "{name}.generated.h"\n\nUCLASS()\nclass CHIMERA_API A{name} : public AGameModeBase\n{{\n\tGENERATED_BODY()\n\npublic:\n\tA{name}();\nprotected:\n\tvirtual void BeginPlay() override;\n}};\n',
            "source_template": '// Generated code\n#include "{name}.h"\n#include "GameFramework/PlayerController.h"\n\nA{name}::A{name}()\n{{\n}}\n\nvoid A{name}::BeginPlay()\n{{\n\tSuper::BeginPlay();\n}}\n',
            "include_paths": ["CoreMinimal.h", "GameFramework/GameModeBase.h", "GameFramework/PlayerController.h"],
            "api_macro": "CHIMERA_API"
        }
    }
    
    if pattern_name in patterns:
        return patterns[pattern_name]
        
    # Default to AActor pattern for unknown types starting with 'A' or 'U'
    if pattern_name.startswith("A"):
        return patterns["AActor"]
    elif pattern_name.startswith("U"):
        return patterns["UActorComponent"]
        
    raise ValueError(f"Unknown pattern: {pattern_name}")

def _query_file(file_path: str) -> dict:
    """Returns the file's node in the graph with all its connections."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    # Find template or mutation nodes related to this file
    file_id = hash_node_id("file", file_path)
    
    # Look for matching file references in nodes
    matching_nodes = []
    for node in nodes:
        if "template_file" in node and file_path in node["template_file"]:
            matching_nodes.append(node)
            
    # Find edges connected to this file's templates
    related_edges = []
    for edge in edges:
        source_id = edge.get("source", "")
        target_id = edge.get("target", "")
        
        # Check if edge is related to this file
        for node in nodes:
            if "template_file" in node and file_path in node.get("template_file", ""):
                template_id = f"template_{hashlib.sha256(node['template_file'].encode()).hexdigest()[:12]}"
                if source_id == template_id or target_id == template_id:
                    related_edges.append(edge)
                    
    return {
        "file_path": file_path,
        "node_id": file_id,
        "related_nodes": [n["id"] for n in matching_nodes],
        "connected_edges": related_edges
    }

def _query_mutation(mutation_pattern: str) -> list:
    """Returns all mutations related to a specific pattern or error type."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    
    matching_mutations = []
    for node in nodes:
        if node.get("type") == "Mutation":
            error_sig = node.get("error_signature", "")
            fix_desc = node.get("fix_description", "")
            
            if mutation_pattern.lower() in error_sig.lower() or \
               mutation_pattern.lower() in fix_desc.lower() or \
               mutation_pattern in str(node):
                matching_mutations.append(node)
                
        elif node.get("type") == "Error":
            error_msg = node.get("error_message", "")
            if mutation_pattern.lower() in error_msg.lower():
                # Find related mutations/fixes
                matching_mutations.append(node)
                
        elif node.get("type") == "Fix":
            fix_desc = node.get("fix_description", "")
            categories = node.get("categories", [])
            if mutation_pattern.lower() in fix_desc.lower() or \
               any(mutation_pattern.lower() in cat.lower() for cat in categories):
                matching_mutations.append(node)
                
    return matching_mutations

def _query_community(community_name: str) -> list:
    """Returns all files in a specific community (e.g., combat_components, ai_files)."""
    communities = {
        "combat_components": [
            "CombatTargetComponent.h", "CombatTargetComponent.cpp",
            "WeaponComponent.h", "WeaponComponent.cpp",
            "ShieldComponent.h", "ShieldComponent.cpp",
            "DamageComponent.h", "DamageComponent.cpp",
            "SystemDamageComponent.h", "SystemDamageComponent.cpp",
            "Projectile.h", "Projectile.cpp"
        ],
        "ai_files": [
            "PirateAIController.h", "PirateAIController.cpp",
            "PirateBehaviorTree.behaviortree"
        ],
        "ship_classes": [
            "AShip_Trader_Vessel_Alpha.h", "AShip_Trader_Vessel_Alpha.cpp",
            "FlightComponent.h", "FlightComponent.cpp"
        ],
        "game_mode_class": [
            "DeepSpaceTraderGameMode.h", "DeepSpaceTraderGameMode.cpp"
        ],
        "pcg_files": [
            "PCGVolumeManager.h", "PCGVolumeManager.cpp",
            "PCGVolume.h"
        ],
        "mission_components": [
            "MissionComponent.h", "MissionComponent.cpp",
            "MissionDataStructs.h", "MissionDataStructs.cpp"
        ]
    }
    
    return communities.get(community_name, [])

def _query_chain(dsl_block: str, generated_file: str) -> list:
    """Returns every step between DSL block and generated file."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    chain = []
    
    # Start with the DSL block
    chain.append({
        "step": 1,
        "type": "dsl_block",
        "identifier": dsl_block
    })
    
    # Find related mutations/fixed templates
    for node in nodes:
        if node.get("type") == "Mutation" and generated_file in str(node):
            chain.append({
                "step": len(chain) + 1,
                "type": "mutation",
                "identifier": node.get("id"),
                "error_signature": node.get("error_signature"),
                "fix_description": node.get("fix_description"),
                "compilation_result": node.get("compilation_result")
            })
            
    # Add the generated file step
    if generated_file:
        chain.append({
            "step": len(chain) + 1,
            "type": "generated_file",
            "identifier": generated_file
        })
        
    return chain

def _query_config() -> dict:
    """Returns project configuration from the knowledge graph."""
    kg = load_knowledge_graph()
    metadata = kg.get("metadata", {})
    
    return {
        "canonical_output_dir": metadata.get("canonical_output_dir", "E:/PythonChimera/Chimera"),
        "module_name": metadata.get("module_name", "Chimera"),
        "api_macro": metadata.get("api_macro", "CHIMERA_API"),
        "include_paths": metadata.get("include_paths", [
            "ProceduralGenerated/Combat", 
            "ProceduralGenerated/AI", 
            "ProceduralGenerated/Flight", 
            "ProceduralGenerated/PCG", 
            "ProceduralGenerated/Stations", 
            "ProceduralGenerated/Missions", 
            "ProceduralGenerated/Factions", 
            "ProceduralGenerated/Save", 
            "ProceduralGenerated/GameMode", 
            "ProceduralGenerated/Ships"
        ]),
        "dependencies": ["Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "PCG", "AIModule", "GameplayAbilities", "Niagara", "NiagaraCore"]
    }

CAMPUSES_DATA = {
    "game_development": {
        "name": "Game Development School",
        "focus": "Level design, lighting, environment art, visual storytelling, game feel",
        "seed_sources": [
            {"name": "GDC Vault: Level Design Principles", "quality": "A+"},
            {"name": "Unreal Engine Documentation: Lighting for Games", "quality": "A+"},
            {"name": "ArtStation Environment Art Pipelines", "quality": "B+"},
            {"name": "Game Developer Magazine: Visual Storytelling", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Official Epic Games documentation", "GDC presentations from senior developers"],
            "B+": ["Industry articles from Game Developer, Polygon, IGN Creative"],
            "C": ["General gaming blogs, unverified tutorials"]
        }
    },
    "art_school": {
        "name": "Art School",
        "focus": "Color theory, composition, form/mass, light/shadow, material rendering",
        "seed_sources": [
            {"name": "Color Theory for Artists (online courses)", "quality": "A+"},
            {"name": "Composition Principles in Fine Art", "quality": "A+"},
            {"name": "PBR Materials Explained by Artists", "quality": "B+"},
            {"name": "Form and Silhouette Design Principles", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Academic art resources, professional artist tutorials (Proko, Draw.io)"],
            "B+": ["ArtStation tutorials, YouTube art education channels"],
            "C": ["General design blogs, unverified color theory guides"]
        }
    },
    "film_school": {
        "name": "Film School",
        "focus": "Cinematography, three-point lighting, production design",
        "seed_sources": [
            {"name": "American Society of Cinematographers (ASC) guidelines", "quality": "A+"},
            {"name": "Three-Point Lighting Setup Tutorials", "quality": "B+"},
            {"name": "Film Production Design Principles", "quality": "B+"},
            {"name": "Cinematography Camera Work Principles", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["ASC publications, professional cinematographer tutorials"],
            "B+": ["Film school resources, professional director guides"],
            "C": ["General photography blogs, amateur filmmaking guides"]
        }
    },
    "architecture_school": {
        "name": "Architecture School",
        "focus": "Spatial design, materiality, lighting design",
        "seed_sources": [
            {"name": "Architectural Lighting Design Guidelines", "quality": "A+"},
            {"name": "Architectural Digest Design Principles", "quality": "B+"},
            {"name": "Spatial Design for Interiors", "quality": "B+"},
            {"name": "Materiality in Modern Architecture", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Professional architecture publications (ArchDaily, Architizer)"],
            "B+": ["University architecture department resources"],
            "C": ["General home design blogs, interior decorating sites"]
        }
    },
    "engineering_school": {
        "name": "Engineering School",
        "focus": "Spacecraft design, industrial design, form follows function",
        "seed_sources": [
            {"name": "NASA Technical Reports", "quality": "A+"},
            {"name": "Spacecraft Design Constraints and Requirements", "quality": "A+"},
            {"name": "Industrial Design Principles (Form Follows Function)", "quality": "B+"},
            {"name": "Engineering Form and Function Case Studies", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Official NASA documentation, engineering textbooks"],
            "B+": ["Professional engineering society publications"],
            "C": ["General science blogs, speculative engineering articles"]
        }
    },
    "unreal_engine_craft": {
        "name": "Unreal Engine Craft School",
        "focus": "Modeling Mode, console commands, MCP geometry tools, shape creation",
        "seed_sources": [
            {"name": "Unreal Engine 5 Documentation: Modeling Mode", "quality": "A+"},
            {"name": "MCP Geometry Tools Documentation", "quality": "A+"},
            {"name": "Console Command References", "quality": "A+"},
            {"name": "UE5 Sculpting Tools Tutorials", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Official Epic Games documentation, verified MCP pathway docs"],
            "B+": ["Community tutorials that have been verified against official docs"],
            "C": ["Unverified YouTube tutorials, outdated engine version guides"]
        }
    },
    "spatial_reasoning": {
        "name": "Spatial Reasoning School",
        "focus": "3D composition, grid systems, distance/scale, spatial relationships",
        "seed_sources": [
            {"name": "Spatial Relationship Guidelines in Level Design", "quality": "A+"},
            {"name": "3D Composition Principles for Games", "quality": "B+"},
            {"name": "Modular Grid Design for Games", "quality": "B+"},
            {"name": "Distance and Scale in Virtual Environments", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Academic game design resources, professional level design guides"],
            "B+": ["Industry level design articles, GDC spatial reasoning talks"],
            "C": ["General 3D modeling tutorials without spatial context"]
        }
    },
    "iteration_school": {
        "name": "Iteration School",
        "focus": "Michelangelo Procedure, failure protocol, refinement process",
        "seed_sources": [
            {"name": "Michelangelo Carving Process Documentation", "quality": "A+"},
            {"name": "The Michelangelo Procedure in Modern Practice", "quality": "A+"},
            {"name": "Iterative Design Process Refinement Guides", "quality": "B+"},
            {"name": "Failure Protocol in Creative Industries", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Historical documentation of Michelangelo's process, verified iteration studies"],
            "B+": ["Professional creative industry refinement guides"],
            "C": ["General productivity or creativity blogs"]
        }
    },
    "emotion_to_parameter": {
        "name": "Emotion-to-Parameter School",
        "focus": "Mapping feelings to technical values (lighting, materials, sound, space)",
        "seed_sources": [
            {"name": "Color Temperature and Emotion Psychology", "quality": "A+"},
            {"name": "How Lighting Creates Mood in Film", "quality": "B+"},
            {"name": "How Materials Affect Mood in Interior Design", "quality": "B+"},
            {"name": "Emotional Sound Design Principles", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Academic psychology studies on color/emotion, professional film lighting guides"],
            "B+": ["Professional game audio/lighting design resources"],
            "C": ["General mood or atmosphere blogs"]
        }
    },
    "reference_management": {
        "name": "Reference Management School",
        "focus": "Organization, avoiding duplication, cross-referencing, reference decay",
        "seed_sources": [
            {"name": "Graphify Knowledge Graph Documentation", "quality": "A+"},
            {"name": "Reference Decay and Verification Protocols", "quality": "A+"},
            {"name": "Reference Organization Systems in Creative Industries", "quality": "B+"},
            {"name": "Cross-Referencing Techniques for Research", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Official Chimera documentation, verified knowledge graph practices"],
            "B+": ["Professional research organization guides"],
            "C": ["General note-taking or organization blogs"]
        }
    },
    "creativity_school": {
        "name": "Creativity School",
        "focus": "Combinatorial creativity, extrapolation, constraints as creativity",
        "seed_sources": [
            {"name": "Combinatorial Creativity Research Papers", "quality": "A+"},
            {"name": "Constraints as Creativity in Design", "quality": "B+"},
            {"name": "Extrapolation Techniques Across Domains", "quality": "B+"},
            {"name": "The Idea Log and Creative Documentation", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Academic creativity research, verified design methodology papers"],
            "B+": ["Professional creative industry methodology guides"],
            "C": ["General creativity or brainstorming blogs"]
        }
    },
    "collaboration_school": {
        "name": "Collaboration School",
        "focus": "Presenting options, asking for guidance, mirror protocol",
        "seed_sources": [
            {"name": "Mirror Protocol in Creative Collaboration", "quality": "B+"},
            {"name": "Presenting Options to Stakeholders", "quality": "B+"},
            {"name": "Incorporating Feedback in Creative Industries", "quality": "B+"},
            {"name": "Asking for Guidance Effectively", "quality": "B+"}
        ],
        "quality_ratings": {
            "A+": ["Professional collaboration methodology resources, verified communication guides"],
            "B+": ["Industry teamwork and collaboration guides"],
            "C": ["General workplace communication blogs"]
        }
    }
}

def _query_campus(campus_name: str, context: dict = None) -> dict:
    """Returns trusted research sources for a specific campus/school or all campuses."""
    if context is None:
        context = {}
        
    quality_filter = context.get("quality")
    
    if campus_name == "all" or campus_name.lower() == "all":
        result = {}
        for key, campus in CAMPUSES_DATA.items():
            sources = campus["seed_sources"]
            if quality_filter:
                sources = [s for s in sources if s.get("quality", "").upper().startswith(quality_filter.upper())]
            result[key] = {
                "name": campus["name"],
                "focus": campus["focus"],
                "seed_sources": sources,
                "quality_ratings": campus["quality_ratings"]
            }
        return result
    
    # Normalize campus_name
    campus_key = None
    for key, campus in CAMPUSES_DATA.items():
        if campus_name.lower() == key or campus_name.lower() == campus["name"].lower().replace(" school", "").replace("school", ""):
            campus_key = key
            break
            
    if not campus_key and campus_name in CAMPUSES_DATA:
        campus_key = campus_name
        
    if not campus_key:
        raise ValueError(f"Unknown campus: {campus_name}")
        
    campus = CAMPUSES_DATA[campus_key]
    sources = campus["seed_sources"]
    
    if quality_filter:
        sources = [s for s in sources if s.get("quality", "").upper().startswith(quality_filter.upper())]
        
    return {
        "campus": campus_key,
        "name": campus["name"],
        "focus": campus["focus"],
        "seed_sources": sources,
        "quality_ratings": campus["quality_ratings"]
    }

def _mutate_compilation(result: str, details: dict = None) -> str:
    """Records a compilation mutation through Graphify.

    details may carry: ubt_output (full compiler text — the tail is stored),
    template_file, failing_files. Failures also record an automatic F grade so
    the GPA reflects build health, not just professor reviews.
    """
    details = details or {}
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    ubt_output = (details.get("ubt_output") or "").strip()
    # UBT prints errors near the end — keep the tail, capped so the graph stays readable
    ubt_excerpt = ubt_output[-4000:] if ubt_output else ""
    # Match lines containing: "error", "fatal", MSVC error codes (C2039, C1083), or "failed"
    import re
    error_lines = [ln.strip() for ln in ubt_output.splitlines()
                   if any(pattern in ln.lower() or re.search(r'\bC\d+\b', ln)
                          for pattern in ['error', 'fatal', 'failed', 'failure'])][:20]
    template_file = details.get("template_file") or "unspecified"

    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'compilation_{result}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error" if result == "pass" else f"compilation_{result}",
        "template_file": template_file,
        "template_line": 0,
        "error_category": "none" if result == "pass" else "compilation_error",
        "fix_description": "build_completed" if result == "pass" else (
            error_lines[0] if error_lines else f"compilation_{result}"),
        "fix_diff": "build_completed" if result == "pass" else (
            "\n".join(error_lines) if error_lines else f"compilation_{result}"),
        "ubt_output_excerpt": ubt_excerpt,
        "failing_files": details.get("failing_files", []),
        "compilation_result": result,
        "links": []
    }

    nodes.append(mutation_node)

    # Save back to DNA graph (which is part of the knowledge base)
    save_dna_graph({"nodes": nodes, "edges": edges})

    # A failed build is an automatic F — GPA must be able to fall
    if result != "pass":
        _mutate_professor_grade({
            "feature": details.get("feature", "Build_Pipeline"),
            "grade": "F",
            "reasoning": (f"UBT compilation {result}: " +
                          (error_lines[0][:300] if error_lines else "no error text captured")),
        })

    return mutation_node["id"]

def _mutate_parse(parse_details: dict) -> str:
    """Records a DSL parse mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    block_names = [k for k in parse_details.keys() if isinstance(parse_details, dict)]
    
    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'parse_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error",
        "template_file": f"dsl_parse_{'_'.join(block_names) if block_names else 'unknown'}",
        "template_line": 0,
        "error_category": "none",
        "fix_description": f"DSL parsed with {len(block_names)} blocks: {', '.join(block_names[:5])}",
        "fix_diff": f"Parsed DSL blocks: {block_names}",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return mutation_node["id"]

def _mutate_generation(gen_details: dict) -> str:
    """Records a code generation mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    file_types = [k for k in gen_details.keys() if isinstance(gen_details[k], list)]
    
    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'generation_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error",
        "template_file": f"code_generation_{'_'.join(file_types) if file_types else 'unknown'}",
        "template_line": 0,
        "error_category": "none",
        "fix_description": f"Generated {sum(len(gen_details.get(k, [])) for k in file_types)} files across {len(file_types)} categories",
        "fix_diff": f"Generated files: {file_types}",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return mutation_node["id"]

def _mutate_visual_verification(result: str = None, details: dict = None) -> str:
    """Records a visual verification mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    screenshot_path = details.get("screenshot_path") if details else None
    description = (details.get("description") if details else "") or ""
    feature = (details.get("feature") if details else None) or "Visual_Verification"

    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'visual_verification_{result}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error" if result == "pass" else f"verification_{result}",
        "template_file": "visual_verification/screenshot_analysis",
        "template_line": 0,
        "error_category": "none" if result == "pass" else "verification_incomplete",
        "fix_description": f"Visual verification {result}: AI analysis completed",
        "fix_diff": f"Verification result: {result}, Description: {description[:200]}",
        "screenshot_path": screenshot_path,
        "feature": feature,
        "compilation_result": result,
        "links": []
    }

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})

    # A verification that didn't pass pulls the GPA down (C = return to research)
    if result != "pass":
        _mutate_professor_grade({
            "feature": feature,
            "grade": "C",
            "reasoning": f"Visual verification returned {result}: {description[:200]}",
        })

    return mutation_node["id"]

def _mutate_feature_complete(details: dict) -> str:
    """Records a feature completion mutation through Graphify (FeatureUpdate node)."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    feature_name = details.get("feature") or details.get("feature_name") or "unknown_feature"
    status = details.get("status", "implemented")
    loop = details.get("loop", 0)
    parameters = details.get("parameters", {})

    if feature_name == "unknown_feature":
        return "rejected_unknown_feature: details must include 'feature' or 'feature_name'; nothing recorded"

    mutation_node = {
        "id": f"feature_{hashlib.sha256(f'feature_{feature_name}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "FeatureUpdate",
        "timestamp": datetime.utcnow().isoformat(),
        "feature_name": feature_name,
        "loop": loop,
        "status": status,
        "parameters": parameters,
        "error_signature": "success_no_error",
        "template_file": f"loop_{loop}/{feature_name}",
        "error_category": "none",
        "fix_description": f"Feature '{feature_name}' (Loop {loop}) recorded as '{status}'",
        "compilation_result": "pass",
        "links": []
    }
    if details.get("backfilled"):
        mutation_node["backfilled"] = True

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})

    return mutation_node["id"]

def _mutate_loop_complete(details: dict) -> str:
    """Records a loop completion mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    loop = details.get("loop", 0)
    name = details.get("name", "unknown")
    features = details.get("features") or details.get("features_completed") or []
    status = details.get("status", "all_implemented")
    emotional_anchor = details.get("emotional_anchor", "")

    if name == "unknown" and not features:
        return "rejected_unknown_loop: details must include 'name' and/or 'features'; nothing recorded"

    mutation_node = {
        "id": f"loop_{hashlib.sha256(f'loop_{loop}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "LoopComplete",
        "timestamp": datetime.utcnow().isoformat(),
        "loop": loop,
        "name": name,
        "status": status,
        "features": features,
        "emotional_anchor": emotional_anchor,
        "error_signature": "success_no_error",
        "template_file": f"loop_{loop}_complete",
        "error_category": "none",
        "fix_description": f"Loop {loop} '{name}' completed with status '{status}'. Features: {len(features)}",
        "compilation_result": "pass",
        "links": []
    }
    if details.get("backfilled"):
        mutation_node["backfilled"] = True

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})

    return mutation_node["id"]

def _mutate_research_discovery(details: dict) -> str:
    """Records a research discovery mutation through Graphify.

    Comprehensive research discovery tracking with campus + corpus + web sources,
    acceptance criteria, and numeric parameters with citations."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    feature = details.get("feature", "unknown_feature")
    campus_sources = details.get("campus_sources", [])
    web_sources = details.get("web_sources", [])
    corpus_sources = details.get("corpus_sources", [])
    parameters = details.get("parameters", {})
    acceptance_criteria = details.get("acceptance_criteria", [])
    sources_consulted = details.get("sources_consulted", 0)
    research_confidence = details.get("research_confidence", "medium")
    failure_sources = details.get("failure_sources", [])

    all_sources_count = len(campus_sources) + len(web_sources) + len(corpus_sources)
    if all_sources_count == 0:
        return "rejected_research_discovery: must have at least one source (campus/web/corpus)"

    mutation_node = {
        "id": f"discovery_{hashlib.sha256(f'research_discovery_{feature}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "ResearchDiscovery",
        "timestamp": datetime.utcnow().isoformat(),
        "feature": feature,
        "campus_sources": campus_sources,
        "web_sources": web_sources,
        "corpus_sources": corpus_sources,
        "sources_consulted": sources_consulted or all_sources_count,
        "parameters": parameters,
        "acceptance_criteria": acceptance_criteria,
        "research_confidence": research_confidence,
        "failure_sources": failure_sources,
        "error_signature": "success_no_error",
        "template_file": f"research_discovery/{feature}",
        "error_category": "none",
        "fix_description": f"Research discovery for '{feature}': {all_sources_count} sources consulted, {len(acceptance_criteria)} criteria, confidence={research_confidence}",
        "compilation_result": "pass",
        "links": []
    }

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})

    return mutation_node["id"]



def _query_feature(feature_pattern: str) -> list:
    """Returns FeatureUpdate nodes matching a feature name pattern."""
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    pattern_lower = feature_pattern.lower()
    matches = []
    for node in nodes:
        if node.get("type") == "FeatureUpdate":
            name = node.get("feature_name", "")
            if pattern_lower in name.lower():
                matches.append(node)
    return matches if matches else [{"message": f"No feature matching '{feature_pattern}' found"}]

def _query_pathway(feature_or_action: str) -> list:
    """Returns all pathway nodes matching a feature name or tool/action string."""
    import json as _json
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    
    matches = []
    query_lower = feature_or_action.lower()
    
    for node in nodes:
        node_type = node.get("type", "")
        if node_type in ("Pathway", "pathway_attempt"):
            # Serialize node to string for broad matching
            node_str = _json.dumps(node, default=str).lower()
            if query_lower in node_str:
                matches.append({
                    "id": node.get("id"),
                    "type": node_type,
                    "tool": node.get("tool"),
                    "action": node.get("action"),
                    "parameters_tried": node.get("parameters_tried"),
                    "result": node.get("result"),
                    "error_message": node.get("error_message"),
                    "timestamp": node.get("timestamp"),
                    "fix_description": node.get("fix_description")
                })
    
    return matches

def _query_gpa(scope: str, context: dict = None) -> dict:
    """Returns GPA data for a specific scope: loop_X, school_X, overall, or trend."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    
    # Handle "overall" scope explicitly
    if scope == "overall" or scope is None:
        matching = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == "project_overall"]
        if matching:
            latest = sorted(matching, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
            return latest
        return {
            "scope": "overall",
            "gpa": None,
            "message": "No project overall GPA data recorded yet"
        }
    
    if scope == "trend":
        # Find all GPA nodes across all scopes, sort by date, compute trend
        gpa_nodes = [n for n in nodes if n.get("type") == "ProfessorGrade"]
        overall_nodes = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == "project_overall"]

        if not overall_nodes and not gpa_nodes:
            return {
                "scope": "trend",
                "gpa": None,
                "trend": "flat",
                "message": "No GPA data recorded yet"
            }

        # Compute current GPA from most recent ProfessorGPA overall nodes (preferred) or ProfessorGrade nodes
        if overall_nodes:
            # Use the most recent ProfessorGPA overall node's gpa value
            latest_overall = sorted(overall_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
            current_gpa = latest_overall.get("gpa")
        else:
            # Fallback to computing from most recent 10 ProfessorGrade nodes (excluding Build_Pipeline)
            recent_grades = [g for g in sorted(gpa_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)[:10]
                             if g.get("feature") != "Build_Pipeline"]
            if recent_grades:
                scores = [g.get("score", 0) for g in recent_grades]
                current_gpa = sum(scores) / len(scores)
            else:
                current_gpa = None

        # Trend from overall nodes
        sorted_overall = sorted(overall_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)
        if len(sorted_overall) >= 2:
            prev_gpa = sorted_overall[1].get("gpa", 0)
            curr_gpa = sorted_overall[0].get("gpa", 0)
            if curr_gpa > prev_gpa + 0.05:
                trend = "rising"
            elif curr_gpa < prev_gpa - 0.05:
                trend = "falling"
            else:
                trend = "flat"
        else:
            trend = "flat"
        
        return {
            "scope": "trend",
            "gpa": current_gpa or (sorted_overall[0]["gpa"] if sorted_overall else None),
            "trend": trend,
            "grades_count": len(gpa_nodes)
        }
    
    # Find matching GPA node for specific scope
    matching = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == scope]
    if matching:
        latest = sorted(matching, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
        return latest
    
    return {
        "scope": scope,
        "gpa": None,
        "message": f"No GPA data recorded for scope '{scope}'"
    }

def _mutate_professor_grade(details: dict) -> str:
    """Records a professor grade and updates cumulative GPA."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    feature = details.get("feature", "unknown_feature")
    grade = details.get("grade", "F")
    reasoning = details.get("reasoning", "")
    
    # Map grade to score
    grade_scores = {"A": 4.0, "B": 3.0, "C": 2.0, "F": 0.0}
    score = grade_scores.get(grade.upper(), 0.0)
    
    # Determine loop from feature name (e.g., "Player_Character_Suit" -> "loop_0")
    loop_prefixes = {
        "Player_": 0, "Ground_": 1, "Verb_": 2, "Sky_": 3,
        "Tool_": 4, "NPC_": 5, "Social_": 5, "Shelter_": 6,
        "Travel_": 7, "System_": 8, "Universe_": 9
    }
    feature_loop = None
    for prefix, loop_num in loop_prefixes.items():
        if feature.startswith(prefix):
            feature_loop = loop_num
            break
    
    # Create professor_grade node
    grade_node = {
        "id": f"professor_grade_{hashlib.sha256(f'{feature}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "ProfessorGrade",
        "timestamp": datetime.utcnow().isoformat(),
        "feature": feature,
        "grade": grade.upper(),
        "score": score,
        "reasoning": reasoning,
        "error_signature": "success_no_error",
        "template_file": f"professor_grade/{feature}",
        "error_category": "none",
        "fix_description": f"Professor grade recorded: {feature} = {grade} ({score}) — {reasoning}",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(grade_node)
    
    # Update cumulative GPA
    _update_cumulative_gpa(nodes, edges, scope=f"loop_{feature_loop}" if feature_loop is not None else None)
    _update_cumulative_gpa(nodes, edges, scope="project_overall")
    
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return grade_node["id"]

def _update_cumulative_gpa(nodes, edges, scope: str):
    """Updates or creates cumulative GPA node for the given scope."""
    if scope is None:
        return
    
    # Find all ProfessorGrade nodes within this scope
    if scope == "project_overall":
        relevant_grades = [n for n in nodes if n.get("type") == "ProfessorGrade"]
    elif scope.startswith("loop_"):
        loop_num = scope.split("_")[1]
        loop_prefixes_keys = [k for k, v in {
            "Player_": 0, "Ground_": 1, "Verb_": 2, "Sky_": 3,
            "Tool_": 4, "NPC_": 5, "Social_": 5, "Shelter_": 6,
            "Travel_": 7, "System_": 8, "Universe_": 9
        }.items() if str(v) == loop_num]
        relevant_grades = [
            n for n in nodes if n.get("type") == "ProfessorGrade" 
            and any(n.get("feature", "").startswith(p) for p in loop_prefixes_keys)
        ]
    else:
        return
    
    if not relevant_grades:
        return
    
    scores = [g.get("score", 0) for g in relevant_grades]
    gpa = sum(scores) / len(scores)
    
    # Find previous GPA node for trend calculation
    previous_nodes = [n for n in nodes if n.get("type") == "ProfessorGPA" and n.get("scope") == scope]
    previous = sorted(previous_nodes, key=lambda x: x.get("timestamp", ""), reverse=True)
    previous_gpa = previous[0].get("gpa", 0.0) if previous else None
    
    # Determine trend
    if previous_gpa is not None:
        if gpa > previous_gpa + 0.05:
            trend = "rising"
        elif gpa < previous_gpa - 0.05:
            trend = "falling"
        else:
            trend = "flat"
    else:
        trend = "flat"
    
    # Create GPA node
    gpa_node = {
        "id": f"professor_gpa_{hashlib.sha256(f'{scope}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "ProfessorGPA",
        "timestamp": datetime.utcnow().isoformat(),
        "scope": scope,
        "gpa": round(gpa, 2),
        "grades_count": len(scores),
        "trend": trend,
        "previous_gpa": previous_gpa,
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "error_signature": "success_no_error",
        "template_file": f"gpa/{scope}",
        "error_category": "none",
        "fix_description": f"GPA for {scope}: {round(gpa, 2)} ({trend}), based on {len(scores)} grades",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(gpa_node)

def _mutate_professor_report_card(details: dict = None):
    """Records a professor report card mutation in the DNA graph."""
    if details is None:
        details = {}
        
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    scope = details.get("scope", "loops_0_through_6")
    gpa = details.get("gpa")
    total_graded_features = details.get("total_graded_features", 0)
    has_real_lm_studio_grades = details.get("has_real_lm_studio_grades", False)
    findings = details.get("findings", "")
    recommendations = details.get("recommendations", "")
    
    # Create professor_report_card node
    report_card_node = {
        "id": f"professor_report_card_{hashlib.sha256(f'{scope}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "ProfessorReportCard",
        "timestamp": datetime.utcnow().isoformat(),
        "scope": scope,
        "gpa": gpa,
        "total_graded_features": total_graded_features,
        "has_real_lm_studio_grades": has_real_lm_studio_grades,
        "findings": findings,
        "recommendations": recommendations,
        "error_signature": "success_no_error",
        "template_file": f"professor_report_card/{scope}",
        "error_category": "none",
        "fix_description": f"Professor report card recorded for {scope}: {total_graded_features} features graded, has_real_lm_studio_grades={has_real_lm_studio_grades}",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(report_card_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return report_card_node["id"]

def _mutate_pathway_attempt(details: dict) -> str:
    """Records a pathway attempt mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    tool = details.get("tool", "unknown_tool")
    action = details.get("action", "unknown_action")
    parameters_tried = details.get("parameters_tried", {})
    result = details.get("result", "unknown_result")
    error_message = details.get("error_message", "")

    if tool == "unknown_tool" and action == "unknown_action":
        return "rejected_unknown_pathway_attempt: details must include 'tool' and 'action'; nothing recorded"
    
    mutation_node = {
        "id": f"pathway_attempt_{hashlib.sha256(f'pathway_attempt_{tool}_{action}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "pathway_attempt",
        "timestamp": datetime.utcnow().isoformat(),
        "tool": tool,
        "action": action,
        "parameters_tried": parameters_tried,
        "result": result,
        "error_message": error_message,
        "error_signature": "success_no_error" if result == "success" else f"pathway_attempt_{result}",
        "template_file": f"pathway_attempt/{tool}/{action}",
        "error_category": "none" if result == "success" else "pathway_failure",
        "fix_description": f"Pathway attempt recorded: tool '{tool}', action '{action}', result '{result}'",
        "compilation_result": result,
        "links": []
    }
    if details.get("backfilled"):
        mutation_node["backfilled"] = True

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return mutation_node["id"]


def _mutate_technical_discovery(details: dict) -> str:
    """Records a technical discovery education node through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    school = details.get("school", "unknown_school")
    topic = details.get("topic", "unknown_topic")
    discovery = details.get("discovery", "")
    resolved_pathway = details.get("resolved_pathway", "unknown_pathway")
    previous_attempts = details.get("previous_attempts", 0)
    discovered_by = details.get("discovered_by", "unknown_agent_session_id")
    
    mutation_node = {
        "id": f"technical_discovery_{hashlib.sha256(f'technical_discovery_{school}_{topic}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "TechnicalDiscovery",
        "timestamp": datetime.utcnow().isoformat(),
        "school": school,
        "topic": topic,
        "discovery": discovery,
        "resolved_pathway": resolved_pathway,
        "previous_attempts": previous_attempts,
        "discovered_by": discovered_by,
        "error_signature": "success_no_error",
        "template_file": f"technical_discovery/{school}/{topic}",
        "error_category": "none",
        "fix_description": f"Technical discovery recorded: school '{school}', topic '{topic}', resolved pathway '{resolved_pathway}'",
        "compilation_result": "pass",
        "links": []
    }
    
    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return mutation_node["id"]

def save_dna_graph(graph):
    _stamp_provenance(graph.get("nodes", []))
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

def _mutate_phase_complete(details: dict) -> str:
    """Records a phase completion (the Contract's Post-Flight g.mutate("phase_complete", ...))."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    phase = details.get("phase") or details.get("name") or "unknown_phase"
    result = details.get("result", "")
    notes = details.get("notes", "")

    if phase == "unknown_phase" and not result:
        return "rejected_unknown_phase: details must include 'phase' and/or 'result'; nothing recorded"

    # Generation Protocol inheritance fields (all optional)
    phantom_pains = details.get("phantom_pains") or []
    inheritance = str(details.get("inheritance") or "")
    pain_verdicts = details.get("pain_verdicts") or {}
    if not isinstance(phantom_pains, list) or not all(isinstance(p, str) and p.strip() for p in phantom_pains):
        return "rejected_phantom_pains: must be a list of non-empty strings; nothing recorded"
    if len(phantom_pains) > 5:
        return "rejected_phantom_pains: declare at most 5 (aim for 3 sharp ones); nothing recorded"
    VALID_VERDICTS = {"confirmed", "refuted", "still-open"}
    if not isinstance(pain_verdicts, dict) or not all(
            isinstance(k, str) and v in VALID_VERDICTS for k, v in pain_verdicts.items()):
        return ("rejected_pain_verdicts: must map '<phase_node_id>:P<n>' -> "
                "confirmed|refuted|still-open; nothing recorded")

    mutation_node = {
        "id": f"phase_{hashlib.sha256(f'phase_{phase}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "PhaseComplete",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": phase,
        "result": result,
        "notes": notes,
        "error_signature": "success_no_error",
        "template_file": f"phase_complete/{phase}",
        "error_category": "none",
        "fix_description": f"Phase '{phase}' complete: {str(result)[:200]}",
        "compilation_result": "pass",
        "links": []
    }
    if phantom_pains:
        mutation_node["phantom_pains"] = phantom_pains
    if inheritance:
        mutation_node["inheritance"] = inheritance
    if pain_verdicts:
        mutation_node["pain_verdicts"] = pain_verdicts
    if details.get("backfilled"):
        mutation_node["backfilled"] = True

    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})

    return mutation_node["id"]


def _mutate_surprise(details: dict) -> str:
    """Records a SurpriseMoment (Circadian dream fodder): a human correction,
    dead-end, or expectation violation — captured live even when nothing failed."""
    context = str(details.get("context") or "").strip()
    expectation = str(details.get("expectation") or "").strip()
    reality = str(details.get("reality") or "").strip()
    lesson_hint = str(details.get("lesson_hint") or "").strip()
    source = str(details.get("source") or "agent")

    if not context or not reality:
        return "rejected_surprise: 'context' and 'reality' are required; nothing recorded"

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    node = {
        "id": f"surprise_{hashlib.sha256(f'surprise_{context}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "SurpriseMoment",
        "timestamp": datetime.utcnow().isoformat(),
        "context": context,
        "expectation": expectation,
        "reality": reality,
        "lesson_hint": lesson_hint,
        "source": source,
        "consolidated": False,
        "error_signature": f"surprise_{source}",
        "template_file": f"surprise/{source}",
        "error_category": "surprise",
        "fix_description": f"Surprise ({source}): expected '{expectation[:80]}' but '{reality[:80]}'",
        "compilation_result": "n/a",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def _mutate_playtest(details: dict) -> str:
    """Records the human's holistic playtest temperature — VERBATIM, few tokens,
    the complete measure of the whole experience. This is how the Observer actually
    works: one reading for the build, not per-feature verdicts. The agent then
    performs ATTRIBUTION (see record_observation's derived_from/quote/tacit)."""
    notes = str(details.get("notes") or "").strip()
    build_ref = str(details.get("build_ref") or "")
    if not notes:
        return "rejected_playtest: 'notes' (the human's verbatim words) required; nothing recorded"

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    node = {
        "id": f"playtest_{hashlib.sha256(f'playtest_{notes}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "PlaytestObservation",
        "timestamp": datetime.utcnow().isoformat(),
        "notes": notes,
        "build_ref": build_ref,
        "observer": "human",
        "error_signature": "success_no_error",
        "template_file": "playtest/holistic_temperature",
        "error_category": "none",
        "fix_description": f"Playtest temperature (verbatim): {notes[:180]}",
        "compilation_result": "n/a",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_playtest(notes: str, build_ref: str = "") -> str:
    """Record the human's holistic playtest temperature verbatim. The agent must
    then attribute it feature-by-feature via record_observation(derived_from=...),
    three tiers: directly-implicated (quote required) / exercised-but-unmentioned
    (tacit=True) / not-exercised (leave queued). Every attribution is reversible
    by one human sentence."""
    return graphify_mutate("playtest", details={"notes": notes, "build_ref": build_ref})


def _mutate_simtest(details: dict) -> str:
    """Records a Sleepwalker run (SimPlaytest node, observer='agent-sim').

    SLEEPWALKER_DESIGN.md: sim results NEVER occupy the human's surfaces —
    this is a separate node type. human_rejection permanently outranks any
    sim signal in the distiller. Failed beats cluster as kind='sim_rejection'."""
    session = str(details.get("session") or "").strip()
    if not session:
        return "rejected_simtest: 'session' required; nothing recorded"
    outcomes = details.get("outcomes") or []
    total = int(details.get("beats_total") or len(outcomes))
    reached = int(details.get("beats_reached") or
                  sum(1 for o in outcomes if o.get("outcome") == "reached"))
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    node = {
        "id": f"simtest_{hashlib.sha256(f'simtest_{session}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "SimPlaytest",
        "timestamp": datetime.utcnow().isoformat(),
        "observer": "agent-sim",
        "session": session,
        "demo": str(details.get("demo") or ""),
        "beats_total": total,
        "beats_reached": reached,
        "outcomes": outcomes,
        "timeline_path": str(details.get("timeline_path") or ""),
        "temperature": str(details.get("temperature") or "")[:400],
        "error_signature": "success_no_error" if reached == total else "sim_beats_failed",
        "template_file": "sleepwalker/beat_run",
        "error_category": "none" if reached == total else "sim_rejection",
        "fix_description": f"Sleepwalk '{session}': {reached}/{total} beats reached",
        "compilation_result": "n/a",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_simtest(session: str, demo: str, beats_total: int, beats_reached: int,
                   outcomes: list, timeline_path: str = "", temperature: str = "") -> str:
    """Record a Sleepwalker beat run. Agent-side evidence only — never a verdict."""
    return graphify_mutate("simtest", details={
        "session": session, "demo": demo, "beats_total": beats_total,
        "beats_reached": beats_reached, "outcomes": outcomes,
        "timeline_path": timeline_path, "temperature": temperature})


def _mutate_rollout(details: dict) -> str:
    """Records a Rehearsal decision (SimulationRollout node): candidates
    considered, scores, the chosen next move, and rationale. Every decision
    is reversible by one human sentence (the veto table)."""
    chosen = str(details.get("chosen") or "").strip()
    if not chosen:
        return "rejected_rollout: 'chosen' required; nothing recorded"
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    node = {
        "id": f"rollout_{hashlib.sha256(f'rollout_{chosen}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "SimulationRollout",
        "timestamp": datetime.utcnow().isoformat(),
        "chosen": chosen,
        "candidates": details.get("candidates") or [],
        "rationale": str(details.get("rationale") or "")[:400],
        "vetoed": False,
        "error_signature": "success_no_error",
        "template_file": "rehearsal/decision",
        "error_category": "none",
        "fix_description": f"Rehearsal chose next move: {chosen}",
        "compilation_result": "n/a",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_rollout(chosen: str, candidates: list, rationale: str = "") -> str:
    """Record a Rehearsal next-move decision (agent-side; human may veto)."""
    return graphify_mutate("rollout", details={
        "chosen": chosen, "candidates": candidates, "rationale": rationale})


def _mutate_observation(details: dict) -> str:
    # Sleepwalker constitution guard (automation amendment 2026-07-07): an agent-sim process
    # (CHIMERA_AGENT_SIM=1) may write observations that ATTRIBUTE simulation evidence
    # (derived_from required). Automated observations are the final assessment surface;
    # the env sentinel ensures proper simtest provenance.
    import os as _os
    if _os.environ.get("CHIMERA_AGENT_SIM") == "1" and not details.get("derived_from"):
        return ("rejected_observation: CHIMERA_AGENT_SIM=1 — agent-sim processes may not "
                "record direct observations (derived_from a simtest_id required)")

    """Records automated observation of a system-finalized feature — the true
    quantum collapse (Generation Protocol automation amendment 2026-07-07). The system's verification
    is the preliminary measurement; the feature's state collapses under automated evidence."""
    feature = str(details.get("feature") or "").strip()
    verdict = str(details.get("verdict") or "").strip().lower()
    notes = str(details.get("notes") or "").strip()
    observer = str(details.get("observer") or "human")
    derived_from = str(details.get("derived_from") or "")
    quote = str(details.get("quote") or "")
    tacit = bool(details.get("tacit"))

    if not feature:
        return "rejected_observation: 'feature' is required; nothing recorded"
    if verdict not in ("accepted", "rejected"):
        return "rejected_observation: verdict must be 'accepted' or 'rejected'; nothing recorded"
    if verdict == "rejected" and not notes:
        return ("rejected_observation: a rejection REQUIRES notes — the human's reason "
                "is the study guide; nothing recorded")
    # Attribution honesty: an agent-derived observation must trace to a playtest node,
    # and a non-tacit attribution must quote the human's actual words.
    if derived_from:
        observer = "human-via-attribution"
        if not tacit and not quote:
            return ("rejected_observation: attribution requires 'quote' (the human's "
                    "phrase) unless tacit=True; nothing recorded")
    elif observer != "human":
        return "rejected_observation: only the human, or an attribution derived_from a playtest node, may observe"

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    node = {
        "id": f"observation_{hashlib.sha256(f'observation_{feature}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "Observation",
        "timestamp": datetime.utcnow().isoformat(),
        "feature_name": feature,
        "verdict": verdict,
        "notes": notes,
        "observer": observer,
        "derived_from": derived_from,
        "quote": quote,
        "tacit": tacit,
        "error_signature": "success_no_error" if verdict == "accepted" else "human_rejection",
        "template_file": f"observation/{feature}",
        "error_category": "none" if verdict == "accepted" else "human_rejection",
        "fix_description": f"Human observation of '{feature}': {verdict}"
                           + (f" — {notes[:160]}" if notes else ""),
        "compilation_result": "pass" if verdict == "accepted" else "rejected",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def collect_observation_queue(nodes: list) -> list:
    """Features whose LATEST FeatureUpdate is 'verified' or 'observed_provisional' with no LATER Observation:
    system-finalized, awaiting automated observation (sleepwalker/telemetry). Returns
    [{feature, loop, verified_at, grade_hint, evidence_hint}] oldest-first."""
    latest_verified = {}
    for n in nodes:
        if n.get("type") != "FeatureUpdate":
            continue
        name = n.get("feature_name")
        if not name or name == "unknown_feature":
            continue
        ts = str(n.get("timestamp", ""))
        prev = latest_verified.get(name)
        if prev is None or ts > prev[0]:
            latest_verified[name] = (ts, n)

    observed_after = {}
    for n in nodes:
        if n.get("type") != "Observation":
            continue
        name = n.get("feature_name")
        ts = str(n.get("timestamp", ""))
        if name and ts > observed_after.get(name, ""):
            observed_after[name] = ts

    queue = []
    for name, (ts, n) in latest_verified.items():
        if n.get("status") != "verified":
            continue
        if observed_after.get(name, "") > ts:
            continue  # already collapsed by a later observation
        params = n.get("parameters") or {}
        grade = str(params.get("grade", ""))[:24]
        evidence = params.get("evidence") or {}
        shots = evidence.get("screenshots", "") if isinstance(evidence, dict) else ""
        queue.append({"feature": name, "loop": n.get("loop"),
                      "verified_at": ts[:19], "grade_hint": grade,
                      "evidence_hint": str(shots)[:80]})
    queue.sort(key=lambda q: q["verified_at"])
    return queue


def record_observation(feature: str, verdict: str, notes: str = "",
                       observer: str = "human", derived_from: str = "",
                       quote: str = "", tacit: bool = False) -> str:
    """Record an Observation verdict on a system-finalized feature.

    Two legitimate sources:
    - The human directly (observer='human').
    - Agent ATTRIBUTION of a holistic playtest: pass derived_from=<playtest node id>
      plus quote=<the human's phrase implicating this feature>, or tacit=True for
      exercised-but-unmentioned features (silence during play = passed the glance).
      Features NOT exercised in the playtest stay queued — do not attribute them.

    accepted -> caller should also record_feature(status='observed').
    rejected -> caller should record_feature(status='needs_refinement') with the
    notes; a SurpriseMoment(source=human) is auto-recorded so the distiller
    treats the rejection as first-class dream fodder. Every attribution is
    reversible by one human sentence."""
    node_id = graphify_mutate("observation", details={
        "feature": feature, "verdict": verdict, "notes": notes, "observer": observer,
        "derived_from": derived_from, "quote": quote, "tacit": tacit})
    if not str(node_id).startswith("rejected_") and verdict == "rejected":
        graphify_mutate("surprise", details={
            "context": f"Human observation of system-finalized feature '{feature}'",
            "expectation": "system verification (rubric grade) matches human judgment",
            "reality": notes,
            "lesson_hint": "frame-level correction: what the machine measured is not what the human sees",
            "source": "human"})
    return node_id


def _mutate_heuristic(details: dict) -> str:
    """Records a Gardener-approved heuristic promotion (Generation Protocol WS2)."""
    signature = str(details.get("signature") or "").strip()
    rule = str(details.get("rule") or "").strip()
    organ = str(details.get("organ") or "").strip()
    evidence_ids = details.get("evidence_ids") or []
    approved_by = str(details.get("approved_by") or "human")

    VALID_ORGANS = {"gate", "claude_md", "mcp_pathways"}
    if not signature or not rule:
        return "rejected_heuristic: 'signature' and 'rule' are required; nothing recorded"
    if organ not in VALID_ORGANS:
        return f"rejected_heuristic: organ must be one of {sorted(VALID_ORGANS)}; nothing recorded"
    if not isinstance(evidence_ids, list):
        return "rejected_heuristic: evidence_ids must be a list of node ids; nothing recorded"

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    node = {
        "id": f"heuristic_{hashlib.sha256(f'heuristic_{signature}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "Heuristic",
        "timestamp": datetime.utcnow().isoformat(),
        "signature": signature,
        "rule": rule,
        "organ": organ,
        "evidence_ids": evidence_ids,
        "approved_by": approved_by,
        "error_signature": "success_no_error",
        "template_file": f"heuristic/{organ}/{signature[:60]}",
        "error_category": "none",
        "fix_description": f"Heuristic promoted to {organ}: {rule[:180]}",
        "compilation_result": "pass",
        "links": list(evidence_ids),
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


# ---------------------------------------------------------------------------
# Typed recording helpers — ALWAYS use these instead of hand-building the
# details dicts (mis-keyed dicts are rejected, but these can't be mis-keyed).
# ---------------------------------------------------------------------------

def record_feature(feature: str, loop: int, status: str, parameters: dict = None,
                   backfilled: bool = False) -> str:
    """Record a Feature Ledger status change (FeatureUpdate node)."""
    details = {"feature": feature, "loop": loop, "status": status,
               "parameters": parameters or {}}
    if backfilled:
        details["backfilled"] = True
    return graphify_mutate("feature_complete", details=details)


def record_pathway(tool: str, action: str, result: str, parameters_tried: dict = None,
                   error_message: str = "", backfilled: bool = False) -> str:
    """Record an MCP pathway attempt (pathway_attempt node)."""
    details = {"tool": tool, "action": action, "result": result,
               "parameters_tried": parameters_tried or {}, "error_message": error_message}
    if backfilled:
        details["backfilled"] = True
    return graphify_mutate("pathway_attempt", details=details)


def call_with_pathway_rule(tool: str, action: str, call_fn, parameters_tried: dict = None):
    """MCP Pathway Rule (AGENTS.md ~138-144): query the graph's pathway_attempt history
    for this tool/action BEFORE calling, then unconditionally record a pathway_attempt
    AFTER -- success or failure -- via record_pathway(). `call_fn` is a zero-arg callable
    returning (success, message), the exact shape MCPClient.* helpers already return.
    Returns call_fn()'s (success, message) unchanged -- adopting this wrapper changes
    nothing about how a caller reads the return value.

    This is the ONE demonstration call site (ralph_loop_harness.py's apply_feature ->
    _apply_geometry) -- do NOT refactor every MCP call site to use this in one pass."""
    prior = graphify_query("pathway", tool)
    recorded_params = dict(parameters_tried or {})
    recorded_params["_prior_attempts"] = len(prior) if isinstance(prior, list) else 0
    try:
        success, message = call_fn()
    except Exception as exc:
        record_pathway(tool, action, "failed", parameters_tried=recorded_params,
                       error_message=str(exc))
        raise
    record_pathway(tool, action, "success" if success else "failed",
                   parameters_tried=recorded_params,
                   error_message="" if success else str(message)[:500])
    return success, message


def record_loop(loop: int, name: str, features: list, status: str = "all_implemented",
                emotional_anchor: str = "", backfilled: bool = False) -> str:
    """Record a spiral loop completion (LoopComplete node)."""
    details = {"loop": loop, "name": name, "features": features, "status": status,
               "emotional_anchor": emotional_anchor}
    if backfilled:
        details["backfilled"] = True
    return graphify_mutate("loop_complete", details=details)


def record_phase(phase: str, result: str, notes: str = "",
                 phantom_pains: list = None, inheritance: str = "",
                 pain_verdicts: dict = None) -> str:
    """Record Post-Flight phase completion (PhaseComplete node).

    Generation Protocol fields: phantom_pains (<=5 predicted failure points the
    next session must confirm/refute), inheritance (<=3-sentence Will), and
    pain_verdicts ({'<phase_node_id>:P<n>': 'confirmed|refuted|still-open'} for
    pains inherited from previous sessions)."""
    details = {"phase": phase, "result": result, "notes": notes}
    if phantom_pains:
        details["phantom_pains"] = phantom_pains
    if inheritance:
        details["inheritance"] = inheritance
    if pain_verdicts:
        details["pain_verdicts"] = pain_verdicts
    return graphify_mutate("phase_complete", details=details)


def parse_pain_verdicts(raw_list) -> dict:
    """Parse CLI '<phase_node_id>:P<n>:<verdict>' strings into the pain_verdicts dict.

    Raises SystemExit with a usage message on malformed input (CLI-facing)."""
    out = {}
    for raw in raw_list or []:
        pain_id, sep, verdict = str(raw).rpartition(":")
        if sep and pain_id and ":P" not in pain_id and pain_id.strip():
            # forgiving normalization (no-blockers law): '<id>:<verdict>' -> '<id>:P1:<verdict>'
            print(f"[postflight] WARNING: pain-verdict '{raw}' missing :P<n> — normalized to {pain_id}:P1:{verdict}")
            pain_id = f"{pain_id}:P1"
        if not sep or not pain_id:
            print(f"[postflight] WARNING: unparseable pain-verdict '{raw}' skipped — phase still records")
            continue
        out[pain_id] = verdict
    return out


def collect_inheritance(nodes: list) -> dict:
    """Scan PhaseComplete nodes for the Generation Protocol inheritance state.

    Returns {'will': {phase, inheritance, timestamp} | None,
             'open_pains': [{id, text, declared, age_days}]} where open pains are
    phantom pains with no verdict recorded by any later PhaseComplete node."""
    phases = sorted((n for n in nodes if n.get("type") == "PhaseComplete"),
                    key=lambda n: n.get("timestamp", ""))
    verdicts = {}
    for n in phases:
        verdicts.update(n.get("pain_verdicts") or {})

    will = None
    for n in reversed(phases):
        if n.get("inheritance"):
            will = {"phase": n.get("phase", ""), "inheritance": n["inheritance"],
                    "timestamp": n.get("timestamp", "")}
            break

    open_pains = []
    now = datetime.utcnow()
    for n in phases:
        for i, pain in enumerate(n.get("phantom_pains") or [], start=1):
            pain_id = f"{n['id']}:P{i}"
            verdict = verdicts.get(pain_id)
            if verdict in ("confirmed", "refuted"):
                continue  # dispositioned
            try:
                declared = datetime.fromisoformat(str(n.get("timestamp", ""))[:19])
                age_days = max(0, (now - declared).days)
            except ValueError:
                age_days = -1
            open_pains.append({"id": pain_id, "text": pain,
                               "declared": str(n.get("timestamp", ""))[:19],
                               "age_days": age_days,
                               "still_open": verdict == "still-open"})
    return {"will": will, "open_pains": open_pains}


def record_heuristic(signature: str, rule: str, organ: str, evidence_ids: list = None,
                     approved_by: str = "human") -> str:
    """Record a Gardener-approved heuristic promotion (Heuristic node).

    signature: the failure-signature/cluster this rule immunizes against.
    rule: the one-sentence constitutional rule as promoted.
    organ: where it was hard-coded — 'gate' | 'claude_md' | 'mcp_pathways'.
    evidence_ids: graph node ids of the failures that taught this lesson.
    Only APPROVED heuristics are recorded; pending candidates live in
    docs/PENDING_HEURISTICS.md until the human approves or vetoes."""
    return graphify_mutate("heuristic", details={
        "signature": signature, "rule": rule, "organ": organ,
        "evidence_ids": evidence_ids or [], "approved_by": approved_by})


def record_surprise(context: str, reality: str, expectation: str = "",
                    lesson_hint: str = "", source: str = "agent") -> str:
    """Record a SurpriseMoment — Circadian dream fodder for the nightly distiller.

    Capture AS THEY HAPPEN: human corrections (source='human'), dead-ends,
    expectation violations. These feed core.heuristic_distiller alongside
    failure clusters; the richest lessons often produce no failure node."""
    return graphify_mutate("surprise", details={
        "context": context, "reality": reality, "expectation": expectation,
        "lesson_hint": lesson_hint, "source": source})


def record_grade(feature: str, grade: str, reasoning: str = "") -> str:
    """Record a professor grade (A/B/C/F) for a feature; updates cumulative GPA."""
    return graphify_mutate("professor_grade", details={"feature": feature, "grade": grade, "reasoning": reasoning})


def record_build(passed: bool, ubt_output: str, template_file: str = "", failing_files: list = None) -> str:
    """Record a build result WITH the actual UBT output (failures auto-grade F)."""
    return graphify_mutate("compilation", "pass" if passed else "fail", details={
        "ubt_output": ubt_output, "template_file": template_file,
        "failing_files": failing_files or []})


def record_research(feature: str, campus_sources: list = None, web_sources: list = None,
                   corpus_sources: list = None, parameters: dict = None,
                   acceptance_criteria: list = None, confidence: str = "medium",
                   failure_sources: list = None) -> str:
    """Record a research discovery with full source tracking and acceptance criteria.

    Args:
        feature: Feature name being researched
        campus_sources: List of campus source names
        web_sources: List of web URLs
        corpus_sources: List of local corpus file paths
        parameters: Dict of {param_name: value_or_details}
        acceptance_criteria: List of measurable criteria with citations
        confidence: low|medium|high confidence rating
        failure_sources: List of sources documenting what does NOT work
                        (Research Depth Protocol Gate 4, AGENTS.md ~109-119)

    Returns:
        Discovery node ID if successful, error string if failed
    """
    return graphify_mutate("research_discovery", details={
        "feature": feature,
        "campus_sources": campus_sources or [],
        "web_sources": web_sources or [],
        "corpus_sources": corpus_sources or [],
        "parameters": parameters or {},
        "acceptance_criteria": acceptance_criteria or [],
        "research_confidence": confidence,
        "failure_sources": failure_sources or []
    })


def _mutate_proposal(details: dict) -> str:
    """Records a Muse proposal (proposal node): a new feature/mechanic/content proposal
    from playtest/witness evidence, DSL/STORY_BIBLE, scholar research. Each proposal lands
    as a rehearsal candidate WITH recipe + a `proposal` record — never self-executing."""
    title = str(details.get("title") or "").strip()
    if not title:
        return "rejected_proposal: 'title' is required; nothing recorded"
    
    source_evidence = str(details.get("source_evidence") or "").strip()
    dsl_bible_source = str(details.get("dsl_bible_source") or "").strip()
    scholar_research = str(details.get("scholar_research") or "").strip()
    recipe = str(details.get("recipe") or "").strip()
    visionkeeper_judgment = str(details.get("visionkeeper_judgment") or "")
    rank = details.get("rank", 0)
    wild_tier = bool(details.get("wild_tier", False))
    
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    node = {
        "id": f"proposal_{hashlib.sha256(f'proposal_{title}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}",
        "type": "Proposal",
        "timestamp": datetime.utcnow().isoformat(),
        "title": title,
        "source_evidence": source_evidence,
        "dsl_bible_source": dsl_bible_source,
        "scholar_research": scholar_research,
        "recipe": recipe,
        "visionkeeper_judgment": visionkeeper_judgment,
        "rank": rank,
        "wild_tier": wild_tier,
        "error_signature": "success_no_error",
        "template_file": f"proposal/{title[:60]}",
        "error_category": "none",
        "fix_description": f"Muse proposal recorded: '{title}' (rank {rank}, wild_tier={wild_tier})",
        "compilation_result": "pass",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_proposal(title: str, source_evidence: str = "", dsl_bible_source: str = "",
                    scholar_research: str = "", recipe: str = "", visionkeeper_judgment: str = "",
                    rank: int = 0, wild_tier: bool = False) -> str:
    """Record a Muse proposal (Proposal node). Each proposal lands as a rehearsal candidate
    WITH recipe + a `proposal` record — never self-executing."""
    return graphify_mutate("proposal", details={
        "title": title, "source_evidence": source_evidence, "dsl_bible_source": dsl_bible_source,
        "scholar_research": scholar_research, "recipe": recipe, "visionkeeper_judgment": visionkeeper_judgment,
        "rank": rank, "wild_tier": wild_tier})


def _mutate_visionkeeper_judgment(details: dict) -> str:
    """Records a VisionKeeper judgment (visionkeeper_judgment node): vision_fit multiplier and one-line judgment."""
    candidate_name = str(details.get("candidate_name") or "")
    proposal_title = str(details.get("proposal_title") or "")
    if not candidate_name and not proposal_title:
        return "rejected_visionkeeper_judgment: 'candidate_name' or 'proposal_title' is required; nothing recorded"

    vision_fit_multiplier = details.get("vision_fit_multiplier", 1.0)
    judgment = str(details.get("judgment") or "").strip()
    existing_visionkeeper_judgment = str(details.get("existing_visionkeeper_judgment") or "")

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    title_or_name = proposal_title if proposal_title else candidate_name
    node_id = f"visionkeeper_judgment_{hashlib.sha256(f'visionkeeper_judgment_{title_or_name}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"

    node = {
        "id": node_id,
        "type": "VisionKeeperJudgment",
        "timestamp": datetime.utcnow().isoformat(),
        "candidate_name": candidate_name,
        "proposal_title": proposal_title,
        "vision_fit_multiplier": vision_fit_multiplier,
        "judgment": judgment,
        "existing_visionkeeper_judgment": existing_visionkeeper_judgment,
        "error_signature": "success_no_error",
        "template_file": f"visionkeeper/judgment/{title_or_name[:60]}",
        "error_category": "none",
        "fix_description": f"VisionKeeper judgment: {title_or_name} -> vision_fit={vision_fit_multiplier}, judgment='{judgment[:120]}'",
        "compilation_result": "pass",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_visionkeeper_judgment(candidate_name: str = "", proposal_title: str = "", vision_fit_multiplier: float = 1.0,
                                 judgment: str = "", existing_visionkeeper_judgment: str = "") -> str:
    """Record a VisionKeeper judgment (VisionKeeperJudgment node): vision_fit multiplier (0.2–1.5) with a one-line judgment."""
    return graphify_mutate("visionkeeper_judgment", details={
        "candidate_name": candidate_name, "proposal_title": proposal_title,
        "vision_fit_multiplier": vision_fit_multiplier, "judgment": judgment,
        "existing_visionkeeper_judgment": existing_visionkeeper_judgment})


def _mutate_critic_judgment(details: dict) -> str:
    """Records a Critic judgment (CriticJudgment node): a comparative player-enjoyment
    percentage estimate vs 2-4 named AAA/notable benchmark titles, grounded in real
    evidence already recorded for the feature (record_grade reasoning, telemetry, spec
    fidelity). ADVISORY ONLY — never gates result_grader, GPA, or any pipeline gate; a
    separate, informational-only signal alongside record_grade (docs/DREAM_ROSTER.md #13)."""
    feature = str(details.get("feature") or "").strip()
    if not feature:
        return "rejected_critic_judgment: 'feature' is required; nothing recorded"

    overall_percentage = details.get("overall_percentage", 0.0)
    benchmark_titles = details.get("benchmark_titles") or []
    axis_scores = details.get("axis_scores") or {}
    named_comparisons = details.get("named_comparisons") or []
    rationale = str(details.get("rationale") or "").strip()
    disclaimer = str(details.get("disclaimer") or CRITIC_ADVISORY_DISCLAIMER)

    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])

    node_id = f"critic_judgment_{hashlib.sha256(f'critic_judgment_{feature}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
    top_titles = [t.get("title") for t in benchmark_titles if isinstance(t, dict) and t.get("title")]

    node = {
        "id": node_id,
        "type": "CriticJudgment",
        "timestamp": datetime.utcnow().isoformat(),
        "feature": feature,
        "overall_percentage": overall_percentage,
        "benchmark_titles": benchmark_titles,
        "axis_scores": axis_scores,
        "named_comparisons": named_comparisons,
        "rationale": rationale,
        "disclaimer": disclaimer,
        "error_signature": "success_no_error",
        "template_file": f"critic/judgment/{feature[:60]}",
        "error_category": "none",
        "fix_description": f"Critic judgment ({disclaimer}): {feature} -> {overall_percentage}% vs {top_titles}",
        "compilation_result": "pass",
        "links": []
    }
    nodes.append(node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    return node["id"]


def record_critic_judgment(feature: str, benchmark_titles: list, overall_percentage: float,
                           axis_scores: dict, named_comparisons: list, rationale: str = "") -> str:
    """Record a Critic judgment (CriticJudgment node): ADVISORY ONLY — LM-generated
    player-enjoyment percentile estimate relative to named AAA/notable benchmark titles.
    Never gates the pipeline; does not substitute for human observation."""
    return graphify_mutate("critic_judgment", details={
        "feature": feature, "benchmark_titles": benchmark_titles,
        "overall_percentage": overall_percentage, "axis_scores": axis_scores,
        "named_comparisons": named_comparisons, "rationale": rationale,
        "disclaimer": CRITIC_ADVISORY_DISCLAIMER})


# Convenience functions for backward compatibility
query = graphify_query
mutate = graphify_mutate
