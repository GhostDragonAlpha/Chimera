import json
import hashlib
from datetime import datetime
from pathlib import Path

KNOWLEDGE_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_knowledge_graph.json")
DNA_GRAPH_PATH = Path("E:/PythonChimera/Chimera/docs/chimera_dna_graph.json")

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
        
    else:
        raise ValueError(f"Unknown query type: {query_type}")

def graphify_mutate(mutate_type: str, result: str = None, details: dict = None):
    """Unified mutation interface to record state changes."""
    
    if mutate_type == "compilation":
        return _mutate_compilation(result)
        
    elif mutate_type == "parse":
        return _mutate_parse(details or {})
        
    elif mutate_type == "generation":
        return _mutate_generation(details or {})
        
    elif mutate_type in ["verification", "visual_verification"]:
        return _mutate_visual_verification(result, details)
        
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

def _mutate_compilation(result: str) -> str:
    """Records a compilation mutation through Graphify."""
    dna_graph = load_dna_graph()
    nodes = dna_graph.get("nodes", [])
    edges = dna_graph.get("edges", [])
    
    mutation_node = {
        "id": f"mutation_{hashlib.sha256(f'compilation_{result}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:12]}",
        "type": "Mutation",
        "timestamp": datetime.utcnow().isoformat(),
        "error_signature": "success_no_error" if result == "pass" else f"compilation_{result}",
        "template_file": "E:\\PythonChimera\\Chimera\\Source\\Chimera\\ProceduralGenerated/DeepSpaceTrader",
        "template_line": 0,
        "error_category": "none" if result == "pass" else "compilation_error",
        "fix_description": f"build_completed" if result == "pass" else f"compilation_{result}",
        "fix_diff": f"build_completed" if result == "pass" else f"compilation_{result}",
        "compilation_result": result,
        "links": []
    }
    
    nodes.append(mutation_node)
    
    # Save back to DNA graph (which is part of the knowledge base)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
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
    description = details.get("description") if details else ""
    
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
        "compilation_result": result,
        "links": []
    }
    
    nodes.append(mutation_node)
    save_dna_graph({"nodes": nodes, "edges": edges})
    
    return mutation_node["id"]

def save_dna_graph(graph):
    DNA_GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DNA_GRAPH_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)

# Convenience functions for backward compatibility
query = graphify_query
mutate = graphify_mutate
