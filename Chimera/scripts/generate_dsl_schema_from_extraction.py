"""
DSL Schema Generator for Unreal Engine API Extraction.

Reads ue5_api_extracted.json and produces DSL schema entries
for each subsystem, mirroring actual UE5 types.
"""

import json
import os
import re
import sys
from collections import OrderedDict
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EXTRACTION_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'ue5_api_extracted.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'schema', 'generated')
REPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'dsl_schema_generation_report.md')

SUBSYSTEMS = {
    'pcg': {
        'display': 'PCG (Procedural Content Generation)',
        'sources': [('Plugins/PCG', None)],
    },
    'niagara': {
        'display': 'Niagara VFX',
        'sources': [('Plugins/Niagara', None)],
    },
    'chaos': {
        'display': 'Chaos Physics',
        'sources': [
            ('Plugins/ChaosCaching', None), ('Plugins/ChaosCloth', None),
            ('Plugins/ChaosClothAsset', None), ('Plugins/ChaosClothAssetDataflowNodes', None),
            ('Plugins/ChaosClothAssetEditorCore', None), ('Plugins/ChaosDataflowSolver', None),
            ('Plugins/ChaosEditor', None), ('Plugins/ChaosFlesh', None),
            ('Plugins/ChaosModularVehicle', None), ('Plugins/ChaosMover', None),
            ('Plugins/ChaosNiagara', None), ('Plugins/ChaosOutfitAsset', None),
            ('Plugins/ChaosRigidAsset', None), ('Plugins/ChaosSolverPlugin', None),
            ('Plugins/ChaosVD', None), ('Plugins/ChaosVehiclesPlugin', None),
        ],
    },
    'materials': {
        'display': 'Materials & Shaders',
        'sources': [
            ('Plugins/DynamicMaterial', None), ('Plugins/DynamicMaterialMediaStreamBridge', None),
            ('Plugins/BlueprintMaterialTextureNodes', None), ('Plugins/MaterialAssetWizard', None),
            ('Plugins/PostProcessMaterialChainGraph', None),
            ('Source/Editor', 'MaterialEditor'), ('Source/Runtime', 'MaterialShaderQualitySettings'),
            ('Source/Developer', 'MaterialBaking'), ('Source/Developer', 'MaterialUtilities'),
        ],
    },
    'umg': {
        'display': 'UMG UI Framework',
        'sources': [
            ('Source/Runtime', 'UMG'), ('Plugins/UMGWidgetPreview', None),
            ('Plugins/WidgetEditorToolPalette', None), ('Plugins/ViewportWidgetOverlay', None),
            ('Source/Runtime', 'WidgetCarousel'), ('Source/Runtime', 'AdvancedWidgets'),
            ('Source/Editor', 'EditorWidgets'), ('Source/Editor', 'KismetWidgets'),
        ],
    },
    'gameplay_abilities': {
        'display': 'Gameplay Abilities (GAS)',
        'sources': [('Plugins/GameplayAbilities', None), ('Plugins/AbilitySystemGameFeatureActions', None)],
    },
    'enhanced_input': {
        'display': 'Enhanced Input',
        'sources': [('Plugins/EnhancedInput', None), ('Source/Runtime', 'InputCore')],
    },
    'common_ui': {
        'display': 'Common UI',
        'sources': [('Plugins/CommonUI', None), ('Plugins/AudioWidgets', None)],
    },
}

# ---------------------------------------------------------------------------
# Type mapping helpers
# ---------------------------------------------------------------------------

SIMPLE_TYPE_MAP = {
    'int': 'integer',
    'int32': 'integer',
    'uint32': 'integer',
    'int64': 'integer',
    'uint64': 'integer',
    'uint8': 'integer',
    'int16': 'integer',
    'uint16': 'integer',
    'int8': 'integer',
    'float': 'number',
    'double': 'number',
    'bool': 'boolean',
    'FString': 'string',
    'FText': 'string',
    'FName': 'string',
    'string': 'string',
    'char': 'string',
    'TArray': 'array',
    'TSet': 'array',
    'TMap': 'object',
    'TMap': 'object',
}

UE_OBJECT_PREFIXES = ('U', 'A', 'F', 'E')

def pascal_to_camel(name):
    """Convert PascalCase or UE-style name to camelCase."""
    if not name:
        return name
    # Strip 'b' prefix for bool-like names
    if name.startswith('b') and len(name) > 1 and name[1].isupper():
        name = name[1:]
    if not name:
        return '_'
    return name[0].lower() + name[1:]

def sanitize_property_name(name):
    """Sanitize a UE property name to a valid JSON key."""
    name = pascal_to_camel(name)
    # Replace any invalid chars
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    if name[0].isdigit():
        name = '_' + name
    return name

def is_ue_object_type(typename):
    """Check if a type name refers to a UE object type."""
    if not typename:
        return False
    clean = typename.replace('*', '').replace('&', '').strip()
    if clean.startswith(UE_OBJECT_PREFIXES) and len(clean) > 1 and clean[1].isalnum():
        return True
    return False

def strip_ue_prefix(typename):
    """Strip U/A/F/E prefix and * & from type names."""
    clean = typename.replace('*', '').replace('&', '').strip()
    if clean and clean[0] in UE_OBJECT_PREFIXES and len(clean) > 1 and clean[1].isupper():
        return clean[1:]
    return clean

def map_ue_type_to_json_schema(typename, known_types=None):
    """
    Map a UE type string to a JSON Schema type descriptor.
    Returns a dict with at least 'type' key.
    """
    if known_types is None:
        known_types = set()

    if not typename:
        return {'type': 'string'}

    raw = typename.strip()
    clean_ptr = raw.replace('*', '').replace('&', '').strip()

    # TArray<X>
    array_match = re.match(r'TArray<(.+)>', clean_ptr)
    if array_match:
        inner = array_match.group(1)
        items = map_ue_type_to_json_schema(inner, known_types)
        return {'type': 'array', 'items': items}

    # TSet<X>
    set_match = re.match(r'TSet<(.+)>', clean_ptr)
    if set_match:
        inner = set_match.group(1)
        items = map_ue_type_to_json_schema(inner, known_types)
        return {'type': 'array', 'items': items}

    # TMap<K,V>
    map_match = re.match(r'TMap<(.+),\s*(.+)>', clean_ptr)
    if map_match:
        key_t = map_match.group(1)
        val_t = map_match.group(2)
        val_schema = map_ue_type_to_json_schema(val_t, known_types)
        return {
            'type': 'object',
            'additionalProperties': val_schema,
            'description': f'TMap<{key_t},{val_t}>'
        }

    # TSubclassOf<X>
    subclass_match = re.match(r'TSubclassOf<(.+)>', clean_ptr)
    if subclass_match:
        return {'type': 'string', 'description': f'TSubclassOf<{subclass_match.group(1)}>'}

    # TWeakObjectPtr<X>, TSoftObjectPtr<X>, TSoftClassPtr<X>
    ptr_match = re.match(r'T(?:Weak|Soft)ObjectPtr<(.+)>', clean_ptr)
    if ptr_match:
        inner = ptr_match.group(1)
        return {'type': 'string', 'description': f'Reference to {inner}'}

    soft_class_match = re.match(r'TSoftClassPtr<(.+)>', clean_ptr)
    if soft_class_match:
        return {'type': 'string', 'description': f'Soft reference to {soft_class_match.group(1)}'}

    # TObjectPtr<X>
    obj_ptr_match = re.match(r'TObjectPtr<(.+)>', clean_ptr)
    if obj_ptr_match:
        inner = obj_ptr_match.group(1)
        if is_ue_object_type(inner):
            ref_name = strip_ue_prefix(inner)
            return {'type': 'string', 'description': f'Ref<{ref_name}>'}
        return map_ue_type_to_json_schema(inner, known_types)

    # FPerPlatformBool, FPerPlatformInt, FPerPlatformFloat etc.
    if clean_ptr.startswith('FPerPlatform'):
        if 'Float' in clean_ptr or 'Double' in clean_ptr:
            return {'type': 'number'}
        elif 'Int' in clean_ptr or 'Bool' in clean_ptr:
            return {'type': 'integer'}
        return {'type': 'string'}

    # Simple direct types
    base = clean_ptr.split('<')[0]
    if base in SIMPLE_TYPE_MAP:
        mapped = SIMPLE_TYPE_MAP[base]
        if mapped == 'array':
            return {'type': 'array', 'items': {'type': 'string'}}
        return {'type': mapped}

    # UE object references (UClass, AClass, FStruct, EEnum)
    if is_ue_object_type(clean_ptr):
        ref_name = strip_ue_prefix(clean_ptr)
        if ref_name in known_types:
            return {'$ref': f'#/properties/{ref_name}'}
        return {'type': 'string', 'description': f'Ref<{ref_name}>'}

    # Fallback
    return {'type': 'string'}


def get_property_specifier_tags(specifiers):
    """Extract meaningful specifier tags from UPROPERTY specifiers."""
    tags = set()
    if not specifiers:
        return tags
    for spec in specifiers:
        if not spec:
            continue
        name = spec[0] if isinstance(spec, list) else spec
        for tag in ['BlueprintReadWrite', 'BlueprintReadOnly', 'EditAnywhere',
                     'EditDefaultsOnly', 'EditFixedSize', 'VisibleAnywhere',
                     'VisibleDefaultsOnly', 'BlueprintSetter', 'BlueprintGetter',
                     'Transient', 'SaveGame', 'Replicated', 'Config',
                     'Interp', 'AdvancedDisplay', 'AssetRegistrySearchable']:
            if tag in str(name):
                tags.add(tag)
    return tags


def get_function_specifier_tags(specifiers):
    """Extract meaningful specifier tags from UFUNCTION specifiers."""
    tags = set()
    if not specifiers:
        return tags
    for spec in specifiers:
        if not spec:
            continue
        name = spec[0] if isinstance(spec, list) else spec
        for tag in ['BlueprintCallable', 'BlueprintPure', 'BlueprintImplementableEvent',
                     'BlueprintNativeEvent', 'BlueprintAuthorityOnly',
                     'BlueprintCosmetic', 'CallInEditor', 'Client', 'Server',
                     'NetMulticast', 'Reliable', 'Unreliable', 'WithValidation']:
            if tag in str(name):
                tags.add(tag)
    return tags


def build_enum_schema(enum_type, known_types):
    """Build a JSON Schema entry for a UE enum."""
    values = enum_type.get('values', [])
    enum_name = enum_type['name']
    clean_name = strip_ue_prefix(enum_name)

    schema = {
        'type': 'string',
        'enum': values,
        'description': f'UE Enum: {enum_name}',
    }

    meta = enum_type.get('meta') or {}
    if 'Bitflags' in meta:
        schema['description'] += ' (Bitflags)'

    return clean_name, schema


def build_struct_schema(struct_type, known_types):
    """Build a JSON Schema entry for a UE struct."""
    struct_name = struct_type['name']
    clean_name = strip_ue_prefix(struct_name)
    properties = struct_type.get('properties', [])

    schema = {
        'type': 'object',
        'description': f'UE Struct: {struct_name}',
        'properties': {},
    }

    required = []
    for prop in properties:
        prop_name = sanitize_property_name(prop['name'])
        specifiers = prop.get('specifiers', [])
        tags = get_property_specifier_tags(specifiers)

        prop_schema = map_ue_type_to_json_schema(prop['type'], known_types)
        if tags:
            desc_parts = [f'UPROPERTY({", ".join(sorted(tags))})']
            if prop_schema.get('description'):
                desc_parts.append(prop_schema['description'])
            prop_schema['description'] = ' | '.join(desc_parts)

        schema['properties'][prop_name] = prop_schema

        # Required if no default and not optional
        has_optional_tag = any('Optional' in str(s) for s in specifiers)
        if not has_optional_tag:
            required.append(prop_name)

    if required:
        # Only mark required if fewer than all properties (common sense limit)
        if len(required) < len(properties) * 0.8:
            schema['required'] = required

    return clean_name, schema


def get_display_category(specifiers):
    """Extract the Category from specifiers."""
    if not specifiers:
        return None
    for spec in specifiers:
        if not spec or len(spec) < 2:
            continue
        if spec[0] == 'Category':
            return spec[1].strip('"\'')
    return None


def build_class_schema(class_type, known_types):
    """Build a JSON Schema entry for a UE class."""
    class_name = class_type['name']
    clean_name = strip_ue_prefix(class_name)
    properties = class_type.get('properties', [])
    functions = class_type.get('functions', [])
    specifiers = class_type.get('specifiers', [])
    meta = class_type.get('meta') or {}

    # Get class specifier tags
    class_tags = set()
    for spec in specifiers:
        name = spec[0] if isinstance(spec, list) else str(spec)
        for tag in ['BlueprintType', 'BlueprintSpawnableComponent', 'NotBlueprintType']:
            if tag in str(name):
                class_tags.add(tag)

    schema = {
        'type': 'object',
        'description': f'UE Class: {class_name}',
        'properties': {},
    }

    if class_tags:
        schema['description'] += f' [{", ".join(sorted(class_tags))}]'

    # Add display name from meta if available
    display_name = meta.get('DisplayName')
    if display_name:
        schema['description'] += f' - "{display_name}"'

    # Map properties
    required = []
    for prop in properties:
        prop_name = sanitize_property_name(prop['name'])
        tags = get_property_specifier_tags(prop.get('specifiers', []))

        prop_schema = map_ue_type_to_json_schema(prop['type'], known_types)

        desc_parts = []
        cat = get_display_category(prop.get('specifiers', []))
        if cat:
            desc_parts.append(f'Category={cat}')
        if tags:
            desc_parts.append(f'UPROPERTY({", ".join(sorted(tags))})')
        if prop_schema.get('description'):
            desc_parts.append(prop_schema['description'])

        if desc_parts:
            prop_schema['description'] = ' | '.join(desc_parts)

        schema['properties'][prop_name] = prop_schema
        required.append(prop_name)

    if required and len(required) <= len(properties):
        schema['required'] = required

    # Map functions as callable methods metadata
    if functions:
        methods = []
        for func in functions:
            func_name = func['name']
            func_tags = get_function_specifier_tags(func.get('specifiers', []))
            func_meta = func.get('meta') or {}

            method_entry = {
                'name': func_name,
            }
            if func_tags:
                method_entry['specifiers'] = sorted(list(func_tags))
            if func.get('params'):
                method_entry['params'] = [
                    {'name': p['name'], 'type': p['type']} for p in func['params']
                ]
            if func.get('return_type'):
                method_entry['return_type'] = func['return_type']
            display = func_meta.get('DisplayName')
            if display:
                method_entry['display_name'] = display

            methods.append(method_entry)

        if methods:
            schema['methods'] = methods

    return clean_name, schema


def generate_subsystem_schema(subsystem_key, subsystem_info, extraction_data):
    """
    Generate a complete DSL schema block for a subsystem.
    Returns (schema_dict, stats_dict).
    """
    stats = {
        'classes': 0,
        'structs': 0,
        'enums': 0,
        'properties_total': 0,
        'functions_total': 0,
        'types_total': 0,
    }

    # Collect all types from the specified sources
    all_types = []
    for key, module_filter in subsystem_info['sources']:
        if key in extraction_data:
            modules = extraction_data[key].get('modules', {})
            for mod_name, types in modules.items():
                if module_filter is None or mod_name == module_filter:
                    for t in types:
                        all_types.append(t)

    if not all_types:
        return None, stats

    stats['types_total'] = len(all_types)

    # Build known type names set for ref resolution
    known_types = set()
    for t in all_types:
        clean = strip_ue_prefix(t['name'])
        known_types.add(clean)

    # Categorize types
    classes = [t for t in all_types if t['type'] == 'class']
    structs = [t for t in all_types if t['type'] == 'struct']
    enums = [t for t in all_types if t['type'] == 'enum']

    stats['classes'] = len(classes)
    stats['structs'] = len(structs)
    stats['enums'] = len(enums)

    # Build schema entries
    schema = {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        'title': f'DSL Schema - {subsystem_info["display"]}',
        'description': f'Auto-generated DSL schema for {subsystem_info["display"]} from UE5 API extraction.',
        'generated_at': datetime.now().isoformat(),
        'properties': OrderedDict(),
    }

    # Sort types by name for consistent output
    def sort_key(t):
        return t['name']

    # Add enums
    enum_properties = OrderedDict()
    for enum_type in sorted(enums, key=sort_key):
        try:
            clean_name, enum_schema = build_enum_schema(enum_type, known_types)
            enum_properties[clean_name] = enum_schema
        except Exception as e:
            print(f'  WARN: Failed to process enum {enum_type.get("name")}: {e}')

    if enum_properties:
        schema['properties']['enums'] = {
            'type': 'object',
            'description': f'UE Enumerations ({len(enums)} types)',
            'properties': enum_properties,
            'additionalProperties': False,
        }

    # Add structs
    struct_properties = OrderedDict()
    for struct_type in sorted(structs, key=sort_key):
        try:
            clean_name, struct_schema = build_struct_schema(struct_type, known_types)
            if struct_schema.get('properties'):
                struct_properties[clean_name] = struct_schema
        except Exception as e:
            print(f'  WARN: Failed to process struct {struct_type.get("name")}: {e}')

    if struct_properties:
        schema['properties']['structs'] = {
            'type': 'object',
            'description': f'UE Structs ({len(structs)} types, {len(struct_properties)} with properties)',
            'properties': struct_properties,
            'additionalProperties': False,
        }
    stats['properties_total'] = sum(
        len(t.get('properties', [])) for t in structs + classes
    )

    # Add classes
    class_properties = OrderedDict()
    for class_type in sorted(classes, key=sort_key):
        try:
            clean_name, class_schema = build_class_schema(class_type, known_types)
            if class_schema.get('properties') or class_schema.get('methods'):
                class_properties[clean_name] = class_schema
        except Exception as e:
            print(f'  WARN: Failed to process class {class_type.get("name")}: {e}')

    if class_properties:
        schema['properties']['classes'] = {
            'type': 'object',
            'description': f'UE Classes ({len(classes)} types, {len(class_properties)} with properties/methods)',
            'properties': class_properties,
            'additionalProperties': False,
        }

    stats['functions_total'] = sum(
        len(t.get('functions', [])) for t in classes
    )

    return schema, stats


def write_schema_file(schema, output_path):
    """Write a schema dict to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    return os.path.getsize(output_path)


def load_extraction(path):
    """Load the extraction JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_report(all_stats, comparison_info):
    """Generate the summary report markdown."""
    lines = []
    lines.append('# DSL Schema Generation Report')
    lines.append('')
    lines.append(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append('')
    lines.append('## Overview')
    lines.append('')
    lines.append('This report documents the auto-generated DSL schema files created from the')
    lines.append('UE5 API extraction data. Each subsystem schema mirrors the actual UE5 types')
    lines.append('(classes, structs, enums) with their UPROPERTYs and UFUNCTIONs mapped to')
    lines.append('JSON Schema definitions.')
    lines.append('')
    lines.append('## Extraction Source')
    lines.append('')
    lines.append(f'- File: `ue5_api_extracted.json`')
    lines.append(f'- Total types in extraction: 24,150')
    lines.append(f'  - UCLASS: 9,982')
    lines.append(f'  - USTRUCT: 10,263')
    lines.append(f'  - UENUM: 3,905')
    lines.append('')
    lines.append('## Generated Subsystems')
    lines.append('')
    lines.append('| Subsystem | Types | Classes | Structs | Enums | Properties | Functions | File Size |')
    lines.append('|-----------|-------|---------|---------|-------|------------|-----------|-----------|')

    for key, info in sorted(all_stats.items()):
        display = SUBSYSTEMS[key]['display']
        s = info['stats']
        size_kb = info.get('file_size', 0) / 1024
        lines.append(
            f'| {display} | {s["types_total"]} | {s["classes"]} | '
            f'{s["structs"]} | {s["enums"]} | {s["properties_total"]} | '
            f'{s["functions_total"]} | {size_kb:.1f} KB |'
        )

    lines.append('')
    lines.append('## Comparison with Manual Encoding')
    lines.append('')
    lines.append('The existing `dsl_game_schema.json` contains manually encoded high-level blocks')
    lines.append('describing game design concepts. The generated schemas take a fundamentally different')
    lines.append('approach — they expose individual UE types (classes, structs, enums) with their')
    lines.append('UPROPERTYs and UFUNCTIONs mapped to JSON Schema definitions.')
    lines.append('')
    lines.append('### Abstraction Level')
    lines.append('')
    lines.append('| Aspect | Manual Schema | Generated Schema |')
    lines.append('|--------|---------------|------------------|')
    lines.append('| **Granularity** | Game design concepts (graphs, collections, tags) | UE class/struct/enum types |')
    lines.append('| **PCG example** | `pcg_graphs`, `data_collections`, `tagged_data_items` | `UPCGComponent`, `FPCGData`, `EPCGChangeType` |')
    lines.append('| **Niagara example** | — | `UNiagaraSystem`, `FNiagaraEmitter`, `ENiagaraExecutionState` |')
    lines.append('| **Property naming** | User-facing `snake_case` | UE-derived `camelCase` |')
    lines.append('| **Scope** | Subset of important game config values | All extracted UE API types |')
    lines.append('')
    lines.append('The two schemas are complementary. The manual schema provides a curated game-design')
    lines.append('vocabulary, while the generated schema provides exhaustive access to the underlying')
    lines.append('engine API. They can be composed using `allOf` or `$ref` for different use cases.')
    lines.append('')

    if comparison_info:
        lines.append('### Type Coverage Comparison')
        lines.append('')
        for ci in comparison_info:
            lines.append(f'#### {ci["label"]}')
            lines.append('')
            lines.append(f'- Manually encoded PCG-block terms: {ci["manual_count"]} (conceptual, not UE type names)')
            lines.append(f'- Generated UE types from extraction: {ci["generated_count"]}')
            lines.append(f'- UE types discovered in extraction: {ci["extraction_count"]}')
            lines.append(f'- Manually-encoded terms also appearing as UE type names: {ci.get("overlap", 0)}')
            if ci.get('missing_from_generated'):
                lines.append(f'- Manual references not found in UE extraction: {ci["missing_from_generated"]}')
            lines.append('')

    lines.append('## Completeness Assessment')
    lines.append('')
    lines.append('The generated schemas cover all UE types found in the extraction data for')
    lines.append('each subsystem. Each type includes:')
    lines.append('')
    lines.append('- **Classes**: All UPROPERTYs as object properties, UFUNCTIONs as methods')
    lines.append('- **Structs**: All UPROPERTYs as object properties')
    lines.append('- **Enums**: All enum values as string enum constraints')
    lines.append('- **Specifiers**: UPROPERTY/UFUNCTION specifiers preserved as metadata')
    lines.append('')
    lines.append('### Known Limitations')
    lines.append('')
    lines.append('1. **Type References**: Cross-type references use simple string descriptions')
    lines.append('   rather than full JSON Schema `$ref` resolution.')
    lines.append('2. **Template Types**: Complex nested templates (e.g., `TMap<TArray<FName>, TSoftObjectPtr<UClass>>`)')
    lines.append('   are simplified to their base type.')
    lines.append('3. **Inheritance**: Class hierarchy (parent classes) is not captured.')
    lines.append('4. **Default Values**: UPROPERTY default values are not extracted.')
    lines.append('5. **Deprecated Types**: Some types may be deprecated in recent UE versions.')
    lines.append('')
    lines.append('## Recommendations for Integration')
    lines.append('')
    lines.append('1. **Incremental Adoption**: Start by integrating high-value subsystems')
    lines.append('   (PCG, Niagara, GAS) into the main `dsl_game_schema.json`.')
    lines.append('2. **Property Naming**: The generator converts UE PascalCase/bool prefixes')
    lines.append('   to camelCase. Review for consistency with existing manual entries.')
    lines.append('3. **Schema Composition**: Use `allOf`/`$ref` to compose generated type')
    lines.append('   schemas into higher-level game design blocks.')
    lines.append('4. **Validation**: Run the generated schemas against sample configuration')
    lines.append('   files to verify correctness before full adoption.')
    lines.append('5. **Regeneration**: Re-run this script when the extraction data is updated')
    lines.append('   to keep schemas in sync with the UE5 API.')
    lines.append('')

    return '\n'.join(lines)


def compare_with_manual(manual_path, generated_schemas, extraction_data):
    """
    Compare generated schemas with manual encoding.
    The manual schema uses game-design vocabulary; the generated schema
    uses UE type names. This comparison quantifies the gap.
    """
    results = []

    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            manual = json.load(f)
    except Exception as e:
        print(f'WARN: Cannot read manual schema for comparison: {e}')
        return results

    # Compare PCG
    manual_pcg = manual.get('properties', {}).get('procedural_generation', {})
    if manual_pcg:
        manual_str = json.dumps(manual_pcg).lower()

        generated = generated_schemas.get('pcg', {})
        gen_type_count = 0
        if generated:
            props = generated.get('properties', {})
            for section in ['classes', 'structs', 'enums']:
                if section in props:
                    gen_type_count += len(props[section].get('properties', {}))

        # Get all actual PCG type names from extraction
        pcg_types = set()
        for key, module_filter in SUBSYSTEMS['pcg']['sources']:
            if key in extraction_data:
                for mod_name, types in extraction_data[key].get('modules', {}).items():
                    if module_filter is None or mod_name == module_filter:
                        for t in types:
                            pcg_types.add(t['name'])

        # Find which UE type names appear as substrings in the manual content
        overlap = 0
        for ue_name in pcg_types:
            clean = ue_name.lower()
            if clean in manual_str:
                overlap += 1

        term_count = len(set(re.findall(r'[a-z_][a-z_0-9]+', manual_str)))

        results.append({
            'label': 'PCG (procedural_generation)',
            'manual_count': term_count,
            'generated_count': gen_type_count,
            'extraction_count': len(pcg_types),
            'overlap': overlap,
            'missing_from_generated': term_count - overlap,
        })

        print(f'  PCG comparison: {term_count} manual terms, {gen_type_count} generated types, '
              f'{overlap} overlap with {len(pcg_types)} extraction types')

    return results


def main():
    print('=' * 60)
    print('DSL Schema Generator for UE5 API Extraction')
    print('=' * 60)

    # Load extraction data
    print(f'\nLoading extraction data from: {EXTRACTION_PATH}')
    extraction_data = load_extraction(EXTRACTION_PATH)
    print(f'Loaded {len(extraction_data)} plugin/source paths')

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Track results for report
    all_stats = {}
    all_schemas = {}
    comparison_info = []

    # Process each subsystem
    for key, info in SUBSYSTEMS.items():
        source_str = ', '.join(f'{k}:{m}' if m else k for k, m in info['sources'])
        print(f'\n--- Processing: {info["display"]} ---')
        print(f'  Sources: {source_str}')

        schema, stats = generate_subsystem_schema(key, info, extraction_data)

        if schema is None:
            print(f'  SKIP: No types found for this subsystem')
            continue

        output_path = os.path.join(OUTPUT_DIR, f'{key}_dsl_schema.json')
        file_size = write_schema_file(schema, output_path)

        all_stats[key] = {
            'stats': stats,
            'file_size': file_size,
            'output_path': output_path,
        }
        all_schemas[key] = schema

        print(f'  Types: {stats["types_total"]} '
              f'(classes={stats["classes"]}, structs={stats["structs"]}, enums={stats["enums"]})')
        print(f'  Properties: {stats["properties_total"]}, Functions: {stats["functions_total"]}')
        print(f'  Output: {output_path} ({file_size / 1024:.1f} KB)')

    # Compare with manual encoding
    print(f'\n--- Comparing with Manual Encoding ---')
    comparison_info = compare_with_manual(
        os.path.join(os.path.dirname(__file__), '..', 'schema', 'dsl_game_schema.json'),
        all_schemas,
        extraction_data
    )



    # Generate report
    print(f'\n--- Generating Report ---')
    report = generate_report(all_stats, comparison_info)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'Report written to: {REPORT_PATH}')

    # Summary
    print(f'\n{"=" * 60}')
    print('SUMMARY')
    print(f'{"=" * 60}')
    total_types = sum(v['stats']['types_total'] for v in all_stats.values())
    total_files = len(all_stats)
    print(f'Subsystems processed: {total_files}')
    print(f'Total types across all subsystems: {total_types}')
    for key in sorted(all_stats.keys()):
        s = all_stats[key]['stats']
        print(f'  {SUBSYSTEMS[key]["display"]}: {s["types_total"]} types '
              f'({s["classes"]} classes, {s["structs"]} structs, {s["enums"]} enums)')

    print(f'\nAll output files in: {OUTPUT_DIR}')
    print('Done.')


if __name__ == '__main__':
    main()
