import json
import hashlib
from datetime import datetime
from pathlib import Path

DNA_GRAPH_PATH = Path(__file__).parent / "docs" / "chimera_dna_graph.json"

dna_graph = json.loads(DNA_GRAPH_PATH.read_text(encoding='utf-8'))
nodes = dna_graph.get("nodes", [])
edges = dna_graph.get("edges", [])

timestamp = datetime.utcnow().isoformat()
node_id = f"tech_research_{hashlib.sha256(f'technical_research_procedural_dust_accumulation_mask_material_creation_{timestamp}'.encode()).hexdigest()[:16]}"

technical_research_node = {
    "id": node_id,
    "type": "TechnicalResearch",
    "timestamp": timestamp,
    "feature_type": "technical_research",
    "target_action": "procedural dust-accumulation mask material creation using noise functions, vertex normal-based masking, and crevice accumulation logic",
    "attempts": [
        {
            "attempt": 1,
            "tool": "manage_asset",
            "action": "create_material",
            "parameters": {"name": "MAT_MetalSurface_Dust", "path": "/Game/Chimera/Materials/MAT_MetalSurface_Dust"},
            "status": "failure",
            "error_message": "Error `PARENT_FOLDER_NOT_FOUND`"
        },
        {
            "attempt": 2,
            "tool": "manage_asset",
            "action": "create_folder",
            "parameters": {"directoryPath": "/Game/Chimera/Materials"},
            "status": "success_but_insufficient",
            "error_message": "Success but insufficient for material creation"
        },
        {
            "attempt": 3,
            "tool": "manage_asset",
            "action": "create_material_instance",
            "parameters": {"instancePath": "/Game/Chimera/Materials/MAT_MetalSurface_Dust/MAT_MetalSurface_Dust_Instance", "parentMaterial": "/Game/Chimera/Materials/MAT_MetalSurface_PBR/MAT_MetalSurface_PBR.MAT_MetalSurface_PBR"},
            "status": "success",
            "error_message": "Material instance created"
        },
        {
            "attempt": 4,
            "tool": "manage_asset",
            "action": "add_scalar_parameter",
            "parameters": {"materialPath": "/Game/Chimera/Materials/MAT_MetalSurface_Dust/MAT_MetalSurface_Dust_Instance", "parameterName": "DustMaskStrength", "value": 0.5},
            "status": "failure",
            "error_message": "Error `ASSET_NOT_FOUND` (add_scalar_parameter is for material graphs, not material instances)"
        },
        {
            "attempt": 5,
            "tool": "manage_asset",
            "action": "create_material",
            "parameters": {"name": "MAT_MetalDustMask", "path": "/Game/Chimera/Materials/MAT_MetalDustMask"},
            "status": "failure",
            "error_message": "Error `PARENT_FOLDER_NOT_FOUND`"
        }
    ],
    "blocked_features": [
        "Ground_Metal_Surface procedural dust-accumulation mask refinement (Loop 0–2 refinement)",
        "Any future metal surface materials requiring procedural dust/wear accumulation masking"
    ],
    "error_signature": "technical_research_procedural_dust_accumulation_mask",
    "template_file": "technical_research/procedural_dust-accumulation_mask_material_creation",
    "error_category": "pathway_failure",
    "fix_description": "Technical research task spawned for procedural dust-accumulation mask material creation",
    "compilation_result": "pending_discovery",
    "links": []
}

nodes.append(technical_research_node)
dna_graph["nodes"] = nodes

DNA_GRAPH_PATH.write_text(json.dumps(dna_graph, indent=2), encoding='utf-8')
print("Technical research node added successfully.")
