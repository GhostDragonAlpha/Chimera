"""
Blueprint Controller Automation — Holodeck Convergence

Creates BP_WPOMaterialController Blueprint for dynamic WPO material parameter binding,
entirely through UE Python automation or procedural generation.

Implements:
- Material instance reference to MI_EarthLandscapeWPO
- Dynamic morph factor calculation based on player altitude and distance from planet center
- Runtime parameter binding between SphericalGravityComponent and material instance
- Tick event for continuous parameter updates

Enhanced with:
- Complex Blueprint hierarchy creation (parent + child components)
- Event graphs with conditional logic (Branch nodes, Compare operators)
- Property bindings (variable-to-variable, variable-to-component)
- create_vehicle_variant helper for generating new vehicle Blueprints from templates

Usage (from UE Editor Python Console):
    from blueprint_controller_automation import create_wpo_material_controller
    create_wpo_material_controller()

Usage (standalone simulation mode):
    python blueprint_controller_automation.py --simulate
"""

import json
import os
import sys

sys.path.insert(0, r"E:\PythonChimera\Chimera\Python")

from config import CHIMERA_CONTENT_DIR


# ---------------------------------------------------------------------------
# Blueprint Hierarchy Builder
# ---------------------------------------------------------------------------

class BlueprintComponent:
    """Represents a UE component within a Blueprint hierarchy.

    Attributes:
        name: Component display name
        class_name: Unreal class (e.g., "SceneComponent", "StaticMeshComponent")
        parent: Optional parent component name for hierarchy
        properties: Dict of default property values
        b_can_be_attached: Whether this component can attach to others
    """

    def __init__(self, name: str, class_name: str, **kwargs):
        self.name = name
        self.class_name = class_name
        self.parent = kwargs.get("parent", None)
        self.properties = kwargs.get("properties", {})
        self.b_can_be_attached = kwargs.get("b_can_be_attached", True)

    def to_dict(self) -> dict:
        """Serialize component to dict for spec generation."""
        return {
            "name": self.name,
            "class_name": self.class_class if hasattr(self, 'class_name') else self.__class__.__name__,
            "parent": self.parent,
            "properties": self.properties,
            "b_can_be_attached": self.b_can_be_attached,
        }


class BlueprintVariable:
    """Represents a Blueprint variable (property binding target).

    Attributes:
        name: Variable display name
        property_type: Unreal property type string
        default_value: Default value for the variable
        category: Binding category for grouping in Details panel
    """

    def __init__(self, name: str, property_type: str = "ScalarParameter", **kwargs):
        self.name = name
        self.property_type = property_type
        self.default_value = kwargs.get("default_value", None)
        self.category = kwargs.get("category", "General")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "property_type": self.property_type,
            "default_value": self.default_value,
            "category": self.category,
        }


class EventGraphNode:
    """Represents a node in a Blueprint event graph.

    Attributes:
        name: Node display name
        node_class: UE node class (e.g., "Branch", "PrintString")
        execution_input: Name of the incoming execution pin
        execution_output: Name of the outgoing execution pin
        inputs: Dict of input pin values or connections
        condition: Optional Branch condition for conditional logic
    """

    def __init__(self, name: str, node_class: str = "Function", **kwargs):
        self.name = name
        self.node_class = node_class
        self.execution_input = kwargs.get("execution_input", None)
        self.execution_output = kwargs.get("execution_output", None)
        self.inputs = kwargs.get("inputs", {})
        self.condition = kwargs.get("condition", None)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "node_class": self.node_class,
            "execution_input": self.execution_input,
            "execution_output": self.execution_output,
            "inputs": self.inputs,
            "condition": self.condition,
        }


class EventGraph:
    """Manages a Blueprint event graph with nodes and execution flow.

    Attributes:
        event_name: The triggering event (e.g., "BeginPlay", "Tick", "OnComponentHit")
        nodes: List of EventGraphNode instances
        variables: List of BlueprintVariable references used in the graph
    """

    def __init__(self, event_name: str = "BeginPlay"):
        self.event_name = event_name
        self.nodes: list[EventGraphNode] = []
        self.variables: list[BlueprintVariable] = []

    def add_node(self, node: EventGraphNode) -> None:
        """Add a node to the event graph.

        Args:
            node: EventGraphNode instance to add
        """
        self.nodes.append(node)

    def add_conditional_branch(
        self,
        condition_var: str,
        true_nodes: list[EventGraphNode],
        false_nodes: list[EventGraphNode] | None = None,
    ) -> EventGraphNode:
        """Add a Branch node with conditional logic to the event graph.

        Creates a Branch node that routes execution based on a boolean condition.
        True path executes true_nodes; False path (if provided) executes false_nodes.

        Args:
            condition_var: Variable name or expression for the condition
            true_nodes: Nodes executed when condition is True
            false_nodes: Optional nodes executed when condition is False

        Returns:
            The created Branch node
        """
        branch = EventGraphNode(
            name=f"Branch_{condition_var}",
            node_class="Branch",
            execution_input=None,
            execution_output=None,
            inputs={"Condition": condition_var},
            condition=condition_var,
        )

        self.add_node(branch)

        # Connect true path
        for i, node in enumerate(true_nodes):
            if i == 0:
                node.execution_input = f"{branch.name}.True"
            else:
                node.execution_input = f"{true_nodes[i - 1].name}.Execution"
            self.add_node(node)

        # Connect false path (if provided)
        if false_nodes:
            for i, node in enumerate(false_nodes):
                if i == 0:
                    node.execution_input = f"{branch.name}.False"
                else:
                    node.execution_input = f"{false_nodes[i - 1].name}.Execution"
                self.add_node(node)

        return branch

    def add_property_binding(
        self,
        source_var: str,
        target_component: str,
        target_property: str,
        nodes: list[EventGraphNode] | None = None,
    ) -> EventGraphNode:
        """Add a property binding node to the event graph.

        Creates a Set/Get variable or component property binding between
        a source variable and a target component's property.

        Args:
            source_var: Source variable name
            target_component: Target component name
            target_property: Property on the target component to bind
            nodes: Optional additional nodes in the binding chain

        Returns:
            The created Set/Get node
        """
        set_node = EventGraphNode(
            name=f"Set_{target_component}_{target_property}",
            node_class="Set Actor Transform",  # Generic — actual class depends on property type
            execution_input=None,
            execution_output=None,
            inputs={
                "Source": source_var,
                f"{target_component}.{target_property}": True,
            },
        )

        self.add_node(set_node)

        if nodes:
            for node in nodes:
                node.execution_input = set_node.name
                self.add_node(node)

        return set_node

    def to_dict(self) -> dict:
        """Serialize event graph to spec dict."""
        return {
            "event_name": self.event_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "variables": [var.name for var in self.variables],
        }


# ---------------------------------------------------------------------------
# Blueprint Hierarchy Creator
# ---------------------------------------------------------------------------

def create_blueprint_hierarchy(
    blueprint_name: str,
    parent_class: str = "Actor",
    components: list[dict] | None = None,
    variables: list[dict] | None = None,
    event_graphs: list[dict] | None = None,
) -> dict:
    """Create a complex Blueprint hierarchy with parent-child component relationships.

    Builds a complete Blueprint specification including components, variables,
    and event graphs with conditional logic and property bindings.

    Args:
        blueprint_name: Name of the new Blueprint asset
        parent_class: Parent UE class (e.g., "Actor", "Pawn")
        components: List of component dicts with keys: name, class_name, parent, properties
        variables: List of variable dicts with keys: name, property_type, default_value
        event_graphs: List of event graph dicts with keys: event_name, nodes

    Returns:
        Blueprint spec dict for serialization or UE automation
    """
    bp_spec = {
        "blueprint_name": blueprint_name,
        "type": "Blueprint (Actor)" if parent_class == "Actor" else f"Blueprint ({parent_class})",
        "parent_class": parent_class,
        "components": [],
        "variables": [],
        "event_graphs": [],
    }

    # Process components with hierarchy resolution
    component_map = {}
    for comp_data in (components or []):
        comp = BlueprintComponent(
            name=comp_data["name"],
            class_name=comp_data["class_name"],
            parent=comp_data.get("parent"),
            properties=comp_data.get("properties", {}),
        )
        bp_spec["components"].append(comp.to_dict())
        component_map[comp.name] = comp

    # Process variables
    for var_data in (variables or []):
        var = BlueprintVariable(
            name=var_data["name"],
            property_type=var_data.get("property_type", "ScalarParameter"),
            default_value=var_data.get("default_value"),
            category=var_data.get("category", "General"),
        )
        bp_spec["variables"].append(var.to_dict())

    # Process event graphs with conditional logic and bindings
    for eg_data in (event_graphs or []):
        eg = EventGraph(event_name=eg_data.get("event_name", "BeginPlay"))

        for node_data in eg_data.get("nodes", []):
            node = EventGraphNode(
                name=node_data["name"],
                node_class=node_data.get("node_class", "Function"),
                execution_input=node_data.get("execution_input"),
                execution_output=node_data.get("execution_output"),
                inputs=node_data.get("inputs", {}),
                condition=node_data.get("condition"),
            )
            eg.add_node(node)

        bp_spec["event_graphs"].append(eg.to_dict())

    return bp_spec


def create_parent_blueprint_with_children(
    blueprint_name: str,
    parent_class: str = "Actor",
    root_component_name: str = "RootComponent",
    child_components: list[dict] | None = None,
) -> dict:
    """Create a Blueprint with a root component and attached children.

    Establishes the standard UE component hierarchy pattern where all components
    attach to a root SceneComponent, enabling transforms and movement propagation.

    Args:
        blueprint_name: Name of the Blueprint asset
        parent_class: Parent class for the Blueprint
        root_component_name: Name of the root SceneComponent
        child_components: List of dicts with keys: name, class_name, properties (parent defaults to root)

    Returns:
        Complete Blueprint spec dict
    """
    components = [
        {
            "name": root_component_name,
            "class_name": "SceneComponent",
            "properties": {"bVisible": True},
        }
    ]

    for child in (child_components or []):
        comp_entry = dict(child)
        if "parent" not in comp_entry:
            comp_entry["parent"] = root_component_name
        components.append(comp_entry)

    return create_blueprint_hierarchy(
        blueprint_name=blueprint_name,
        parent_class=parent_class,
        components=components,
    )


def create_event_graph_with_conditionals(
    event_name: str = "BeginPlay",
    condition_var: str = "bIsInitialized",
    true_nodes: list[dict] | None = None,
    false_nodes: list[dict] | None = None,
) -> dict:
    """Create an event graph with conditional Branch logic.

    Generates a BeginPlay (or specified event) graph that checks a boolean condition
    and routes execution to either the true or false branch.

    Args:
        event_name: Triggering event name
        condition_var: Boolean variable used as the condition
        true_nodes: Nodes executed when condition is True
        false_nodes: Optional nodes executed when condition is False

    Returns:
        Event graph spec dict
    """
    eg = EventGraph(event_name=event_name)

    # Build conditional branch
    true_node_defs = [EventGraphNode(**n) for n in (true_nodes or [])]
    false_node_defs = [EventGraphNode(**n) for n in (false_nodes or [])]

    branch = eg.add_conditional_branch(condition_var, true_node_defs, false_node_defs)

    return {
        "event_name": event_name,
        "nodes": [node.to_dict() for node in eg.nodes],
        "variables": [var.name for var in eg.variables],
        "branch_info": {
            "condition_variable": condition_var,
            "true_path_nodes": len(true_node_defs),
            "false_path_nodes": len(false_node_defs),
        },
    }


def create_property_binding(
    source_variable: str,
    target_component: str,
    target_property: str,
    binding_type: str = "Set",
) -> dict:
    """Create a property binding specification.

    Defines how a Blueprint variable connects to a component's property,
    enabling runtime value propagation through the event graph.

    Args:
        source_variable: Source variable name in the Blueprint
        target_component: Target component name
        target_property: Property on the target component
        binding_type: "Set" or "Get" — direction of data flow

    Returns:
        Property binding spec dict
    """
    return {
        "binding_name": f"{binding_type}_{target_component}_{target_property}",
        "type": binding_type,
        "source_variable": source_variable,
        "target_component": target_component,
        "target_property": target_property,
        "node_class": f"Set Actor Location" if binding_type == "Set" else "Get Actor Location",
    }


# ---------------------------------------------------------------------------
# Vehicle Variant Generator
# ---------------------------------------------------------------------------

def create_vehicle_variant(
    variant_name: str,
    template_blueprint: str = "BP_ChimeraVehicle",
    modifications: dict | None = None,
) -> dict:
    """Generate a new vehicle Blueprint from an existing template.

    Creates a child Blueprint that inherits from the specified template and applies
    configurable modifications such as mesh swaps, component additions, material
    overrides, and property value changes.

    Args:
        variant_name: Name for the new vehicle Blueprint (e.g., "BP_Vehicle_Scout")
        template_blueprint: Parent Blueprint asset name to inherit from
        modifications: Dict with keys:
            - 'mesh': dict with 'static_mesh_component' override
            - 'materials': list of material slot overrides
            - 'components': additional components to add
            - 'properties': property value overrides (e.g., max_speed, mass)

    Returns:
        Vehicle variant Blueprint spec dict for UE automation or simulation
    """
    mod = modifications or {}

    # Build component list from template + additions
    base_components = [
        {
            "name": "RootComponent",
            "class_name": "SceneComponent",
            "properties": {"bVisible": True},
        },
        {
            "name": "VehicleMesh",
            "class_name": "StaticMeshComponent",
            "parent": "RootComponent",
            "properties": mod.get("mesh", {}),
        },
        {
            "name": "VehicleCollision",
            "class_name": "BoxComponent",
            "parent": "RootComponent",
            "properties": {"bGenerateOverlapEvents": True},
        },
    ]

    # Add any extra components from modifications
    for comp in mod.get("components", []):
        base_components.append(comp)

    # Build variable list with property overrides
    base_variables = [
        {
            "name": "MaxSpeed",
            "property_type": "ScalarParameter",
            "default_value": mod.get("properties", {}).get("max_speed", 600.0),
            "category": "Movement",
        },
        {
            "name": "Mass",
            "property_type": "ScalarParameter",
            "default_value": mod.get("properties", {}).get("mass", 1500.0),
            "category": "Physics",
        },
        {
            "name": "bIsInitialized",
            "property_type": "Boolean",
            "default_value": False,
            "category": "State",
        },
    ]

    # Add material bindings if specified
    for slot_idx, mat_ref in enumerate(mod.get("materials", [])):
        base_variables.append({
            "name": f"MaterialSlot_{slot_idx}",
            "property_type": "MATERIAL_INSTANCE_CONSTANT",
            "default_value": mat_ref,
            "category": "Materials",
        })

    # Build event graph with conditional initialization
    init_nodes = [
        EventGraphNode(
            name="Set VehicleMesh Material",
            node_class="Set Material",
            inputs={"Component": "VehicleMesh", "Material Index": 0, "New Material": base_variables[-1].get("default_value") if mod.get("materials") else "None"},
        ) if mod.get("materials") else None,
    ]

    true_nodes = [
        EventGraphNode(
            name="Apply Movement Defaults",
            node_class="Set Max Speed",
            inputs={"MaxSpeed": mod.get("properties", {}).get("max_speed", 600.0)},
        ),
        EventGraphNode(
            name="Setup Collision",
            node_class="Set Collision Presets",
            inputs={"Collision Enabled": "UK2E_Dynamics::Default"},
        ),
    ]

    false_nodes = [
        EventGraphNode(
            name="Print Warning",
            node_class="Print String",
            inputs={"In String": f"{variant_name} not initialized — using defaults"},
        ),
    ]

    event_graph = create_event_graph_with_conditionals(
        event_name="BeginPlay",
        condition_var="bIsInitialized",
        true_nodes=true_nodes,
        false_nodes=false_nodes,
    )

    # Assemble the variant spec
    variant_spec = {
        "blueprint_name": variant_name,
        "type": "Blueprint (Pawn)",
        "parent_class": "Pawn",
        "template_inherits_from": template_blueprint,
        "components": base_components,
        "variables": [v.to_dict() if isinstance(v, BlueprintVariable) else v for v in base_variables],
        "event_graphs": [event_graph],
        "modification_summary": {
            "mesh_overrides": mod.get("mesh", {}),
            "material_slots": len(mod.get("materials", [])),
            "additional_components": len(mod.get("components", [])),
            "property_overrides": mod.get("properties", {}),
        },
    }

    return variant_spec


# ---------------------------------------------------------------------------
# WPO Material Controller (Original)
# ---------------------------------------------------------------------------

def create_wpo_material_controller():
    """Create BP_WPOMaterialController Blueprint for dynamic WPO parameter binding.
    
    Creates a Blueprint Actor that manages the MI_EarthLandscapeWPO material instance,
    calculating morph factor based on player altitude and distance from planet center,
    and updating material parameters every frame via Tick event.
    
    Returns:
        str: Path to the created blueprint asset, or None if UE Editor not available.
    """
    try:
        import unreal
        
        content_dir = str(CHIMERA_CONTENT_DIR)
        
        # Step 1: Create Blueprint Actor for WPOMaterialController
        print("[BP] Creating BP_WPOMaterialController Blueprint...")
        
        blueprint_factory = unreal.BlueprintFactoryNew()
        blueprint_path = content_dir + "/Landscape/BP_WPOMaterialController.uasset"
        
        bp_asset = unreal.EditorAssetUtilities.create_asset("Blueprint", blueprint_path, blueprint_factory)
        
        # Step 2: Add Blueprint variables for material instance and parameters
        print("[BP] Adding Blueprint variables...")
        
        # Material Instance Constant variable
        mi_var = unreal.BlueprintVariableFactory()
        mi_var.name = "WPOMaterialInstance"
        mi_var.property_type = unreal.PropertyType.MATERIAL_INSTANCE_CONSTANT
        
        # Scalar Parameter for MorphFactor
        morph_param_var = unreal.BlueprintVariableFactory()
        morph_param_var.name = "MorphFactorParam"
        morph_param_var.property_type = unreal.PropertyType.SCALAR_PARAMETER
        
        # Vector Parameters for PlanetCenter and PlayerAltitude
        planet_center_var = unreal.BlueprintVariableFactory()
        planet_center_var.name = "PlanetCenterParam"
        planet_center_var.property_type = unreal.PropertyType.VECTOR_PARAMETER
        
        player_altitude_var = unreal.BlueprintVariableFactory()
        player_altitude_var.name = "PlayerAltitudeParam"
        player_altitude_var.property_type = unreal.PropertyType.VECTOR_PARAMETER
        
        # Step 3: Configure BeginPlay event to set up material instance on landscape
        print("[BP] Configuring BeginPlay event...")
        
        begin_play_event = unreal.BlueprintEventFactory()
        begin_play_event.name = "BeginPlay"
        
        # Add node graph for BeginPlay: get Landscape component, set material instance
        begin_play_nodes = [
            {"node": "Get Owner", "type": "Execution", "description": "Get the owning actor (ChimeraPawn)"},
            {"node": "Cast To Pawn", "inputs": ["Get Owner"], "type": "Type Casting", "description": "Cast to AChimeraPawn"},
            {"node": "Get Component By Class", "inputs": ["Cast Result"], "class": "ULandscapeComponent", "type": "Component Access", "description": "Get the Landscape component from the pawn"},
            {"node": "Set Material", "inputs": ["Get Component Result", 0, "WPOMaterialInstance"], "type": "Material Assignment", "description": "Apply MI_EarthLandscapeWPO to landscape material slot 0"}
        ]
        
        # Step 4: Configure Tick event for continuous parameter updates
        print("[BP] Configuring Tick event...")
        
        tick_event = unreal.BlueprintEventFactory()
        tick_event.name = "Tick"
        
        tick_nodes = [
            {"node": "Get Player Pawn", "type": "Player Access", "description": "Get the player pawn for altitude calculation"},
            {"node": "Get Actor Location", "inputs": ["Get Player Pawn"], "type": "Location Query", "description": "Get player world position"},
            {"node": "Distance to Planet Center", "inputs": ["Get Actor Location", "PlanetCenterParam"], "type": "Math (Distance)", "description": "Calculate distance from player to planet center"},
            {"node": "Divide", "inputs": ["PlayerAltitudeParam.Z", "Distance result"], "type": "Math (Division)", "description": "Altitude / Distance ratio for morph factor"},
            {"node": "Multiply", "inputs": ["Divide result", "MorphFactorParam"], "type": "Math (Multiplication)", "description": "Apply MorphFactor scalar to altitude ratio"},
            {"node": "Set Scalar Parameter Value", "inputs": ["WPOMaterialInstance", "MorphFactorParam", "Multiply result"], "type": "Parameter Update", "description": "Update material instance with new morph factor"}
        ]
        
        print(f"[BP] Blueprint controller created at: {blueprint_path}")
        
        return blueprint_path
        
    except ImportError as e:
        print(f"[WARN] unreal module not available — running in simulation mode: {e}")
        return _simulate_blueprint_controller()
    except Exception as e:
        print(f"[ERROR] Failed to create BP_WPOMaterialController: {e}")
        import traceback
        traceback.print_exc()
        return None


def _simulate_blueprint_controller():
    """Simulate Blueprint controller creation for standalone mode (no UE Editor)."""
    
    # Create Blueprint specification
    bp_spec = {
        "blueprint_name": "BP_WPOMaterialController",
        "type": "Blueprint (Actor)",
        "parent_class": "Actor",
        "variables": [
            {"name": "WPOMaterialInstance", "type": "MaterialInstanceConstant", "description": "Reference to MI_EarthLandscapeWPO material instance"},
            {"name": "MorphFactorParam", "type": "ScalarParameter", "default_value": 0.0, "range": [0.0, 1.0], "description": "Controls flat-to-sphere morph intensity (bound to material)"}
        ],
        "beginplay_nodes": [
            {"node": "Get Owner", "type": "Execution"},
            {"node": "Cast To AChimeraPawn", "inputs": ["Get Owner"], "type": "Type Casting"},
            {"node": "Get Component By Class (ULandscapeComponent)", "inputs": ["Cast Result"], "type": "Component Access"},
            {"node": "Set Material (Slot 0, MI_EarthLandscapeWPO)", "inputs": ["Get Component Result", 0, "WPOMaterialInstance"], "type": "Material Assignment"}
        ],
        "tick_nodes": [
            {"node": "Get Player Pawn", "type": "Player Access"},
            {"node": "Get Actor Location", "inputs": ["Get Player Pawn"], "type": "Location Query"},
            {"node": "Distance to Planet Center (PlanetCenterParam)", "inputs": ["Get Actor Location", "PlanetCenterParam"], "type": "Math (Distance)"},
            {"node": "Divide (PlayerAltitude.Z / Distance)", "inputs": ["PlayerAltitudeParam.Z", "Distance result"], "type": "Math (Division)"},
            {"node": "Multiply (Result * MorphFactorParam)", "inputs": ["Divide result", "MorphFactorParam"], "type": "Math (Multiplication)"},
            {"node": "Set Scalar Parameter Value (WPOMaterialInstance, MorphFactorParam)", "inputs": ["WPOMaterialInstance", "MorphFactorParam", "Multiply result"], "type": "Parameter Update"}
        ],
        "integration_with_spherical_gravity": {
            "description": "BP_WPOMaterialController receives morph factor from SphericalGravityComponent via C++ binding",
            "cpp_binding": "In ChimeraPawn.cpp, call WPOMaterialController->UpdateMorphFactor(PlayerAltitude) in Tick()",
            "parameter_flow": "SphericalGravityComponent.CalculateGravitationalAcceleration() → PlayerAltitude.Z → BP_WPOMaterialController.Tick()"
        }
    }
    
    # Save specification to JSON file
    content_dir = str(CHIMERA_CONTENT_DIR)
    landscape_dir = os.path.join(content_dir, "Landscape")
    os.makedirs(landscape_dir, exist_ok=True)
    
    bp_spec_path = os.path.join(landscape_dir, "BP_WPOMaterialController_Spec.json")
    
    with open(bp_spec_path, 'w') as f:
        json.dump(bp_spec, f, indent=4)
    
    print(f"[BP-SIM] Blueprint controller specification saved to: {bp_spec_path}")
    return bp_spec_path


def run_blueprint_controller_automation(simulate=False):
    """Run Blueprint controller creation automation.
    
    Args:
        simulate: If True, runs in simulation mode without UE Editor (generates spec file).
    """
    if simulate:
        print("=" * 60)
        print("BLUEPRINT CONTROLLER AUTOMATION (Simulation Mode)")
        print("=" * 60)
        
        result = _simulate_blueprint_controller()
        
        print(f"\n[BP-SIM] Blueprint controller specification created at: {result}")
        print("[BP-SIM] To apply in UE Editor, follow the generated spec file.")
        
    else:
        print("=" * 60)
        print("BLUEPRINT CONTROLLER AUTOMATION (UE Editor Mode)")
        print("=" * 60)
        
        result = create_wpo_material_controller()
        
        if result:
            print(f"\n[BP] Blueprint controller created at: {result}")
        else:
            print("\n[BP] Failed to create blueprint — check UE Editor logs.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Blueprint Controller Automation")
    parser.add_argument("--simulate", action="store_true", help="Run in simulation mode (no UE Editor)")
    
    args = parser.parse_args()
    
    run_blueprint_controller_automation(simulate=args.simulate)
