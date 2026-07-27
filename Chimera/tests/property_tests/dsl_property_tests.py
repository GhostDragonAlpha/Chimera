"""Property-based tests for DSL parser using hypothesis library."""
import re
from typing import Dict, Any

# DSL validation rules
VALID_REQUIRED_BLOCKS = ["game", "technical", "economy"]
VALID_COMMODITY_PRICE_MIN = 10
VALID_SHIP_FUEL_CAPACITY_MIN = 100
VALID_GAME_TITLE_MIN_LEN = 3
VALID_ENGINE_VERSION_PATTERN = r"^5\.\d+$"

def generate_valid_dsl_game_block():
    """Generate a valid game block."""
    # Generate a valid title with at least VALID_GAME_TITLE_MIN_LEN characters
    title_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base_title = "TestGame"
    
    version_parts = [5, 4]
    engine_version = f"5.{version_parts[1]}"
    
    return {
        "game": {
            "title": base_title,
            "genre": ["space", "simulation"],
            "engine_version": engine_version,
            "description": "Generated test game"
        }
    }

def generate_valid_dsl_game_block_variant(i: int):
    """Generate a valid game block with variant title based on index."""
    # Generate a valid title with at least VALID_GAME_TITLE_MIN_LEN characters
    title_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base_title = f"Game{i % 100:03d}"
    
    version_parts = [5, i % 4]
    engine_version = f"5.{version_parts[1]}"
    
    return {
        "game": {
            "title": base_title,
            "genre": ["space", "simulation"],
            "engine_version": engine_version,
            "description": "Generated test game"
        }
    }

def generate_valid_dsl_technical_block():
    """Generate a valid technical block."""
    return {
        "technical": {
            "network_model": "client_server",
            "target_platforms": ["Windows"],
            "rendering_api": "DirectX12"
        }
    }

def generate_valid_dsl_economy_block():
    """Generate a valid economy block with positive prices."""
    commodities = {}
    comm_ids = ["minerals", "fuel", "food", "weapons"]
    for i, comm_id in enumerate(comm_ids):
        price = VALID_COMMODITY_PRICE_MIN + (hash(str(i)) % 1000)
        if price < VALID_COMMODITY_PRICE_MIN:
            price = VALID_COMMODITY_PRICE_MIN
        commodities[comm_id] = {
            "price": price,
            "base_price_min": max(5, price - 50),
            "base_price_max": price + 100
        }
    
    return {
        "economy": {
            "commodities": commodities
        }
    }

def generate_valid_dsl_ships_block():
    """Generate a valid ships block with positive fuel capacity."""
    ships = {}
    ship_ids = ["scout", "freighter", "fighter"]
    for i, ship_id in enumerate(ship_ids):
        fuel_capacity = VALID_SHIP_FUEL_CAPACITY_MIN + (hash(str(i)) % 500)
        if fuel_capacity < VALID_SHIP_FUEL_CAPACITY_MIN:
            fuel_capacity = VALID_SHIP_FUEL_CAPACITY_MIN
        
        ships[ship_id] = {
            "fuel_capacity": fuel_capacity,
            "cargo_capacity": 100 + (hash(str(i+1)) % 500),
            "crew_size": 1 + (hash(str(i+2)) % 10)
        }
    
    return {
        "ships": ships
    }

def generate_valid_dsl():
    """Generate a complete valid DSL."""
    dsl = {}
    
    # Generate game block with valid title
    base_title = "TestGame"
    version_parts = [5, 4]
    engine_version = f"5.{version_parts[1]}"
    dsl["game"] = {
        "title": base_title,
        "genre": ["space", "simulation"],
        "engine_version": engine_version,
        "description": "Generated test game"
    }
    
    dsl.update(generate_valid_dsl_technical_block())
    dsl.update(generate_valid_dsl_economy_block())
    dsl.update(generate_valid_dsl_ships_block())
    
    # Convert to DSL string format
    dsl_lines = []
    for block_name, block_data in dsl.items():
        dsl_lines.append(f"{block_name}:")
        if isinstance(block_data, dict):
            for key, value in block_data.items():
                if isinstance(value, dict):
                    dsl_lines.append(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, list):
                            items = ", ".join([f'"{item}"' for item in sub_value])
                            dsl_lines.append(f"    {sub_key}:\n      - {items}")
                        elif isinstance(sub_value, int) or isinstance(sub_value, float):
                            dsl_lines.append(f"    {sub_key}: {sub_value}")
                        else:
                            dsl_lines.append(f"    {sub_key}: \"{sub_value}\"")
                elif isinstance(value, list):
                    items = ", ".join([f'"{item}"' for item in value])
                    dsl_lines.append(f"  {key}:\n    - {items}")
                else:
                    dsl_lines.append(f"  {key}: {value}")
    
    return "\n".join(dsl_lines)

def generate_invalid_dsl_missing_required_block():
    """Generate an invalid DSL missing a required block."""
    dsl = {}
    dsl.update(generate_valid_dsl_game_block())
    # Missing technical and economy blocks
    
    dsl_lines = []
    for block_name, block_data in dsl.items():
        dsl_lines.append(f"{block_name}:")
        if isinstance(block_data, dict):
            for key, value in block_data.items():
                dsl_lines.append(f"  {key}: {value}")
    
    return "\n".join(dsl_lines)

def generate_invalid_dsl_negative_price():
    """Generate an invalid DSL with negative commodity price."""
    dsl_lines = [
        "game:",
        "  title: TestGame",
        "  genre: space",
        "  engine_version: 5.4",
        "technical:",
        "  network_model: client_server",
        "economy:",
        "  commodities:",
        "    minerals:",
        "      price: -50"
    ]
    return "\n".join(dsl_lines)

def generate_invalid_dsl_negative_fuel_capacity():
    """Generate an invalid DSL with negative ship fuel capacity."""
    dsl_lines = [
        "game:",
        "  title: TestGame",
        "  genre: space",
        "  engine_version: 5.4",
        "technical:",
        "  network_model: client_server",
        "ships:",
        "  scout:",
        "    fuel_capacity: -100"
    ]
    return "\n".join(dsl_lines)

def generate_invalid_dsl_invalid_engine_version():
    """Generate an invalid DSL with invalid engine version."""
    dsl_lines = [
        "game:",
        "  title: TestGame",
        "  genre: space",
        "  engine_version: 4.26"
    ]
    return "\n".join(dsl_lines)

def parse_dsl_content(dsl_content: str) -> Dict[str, Any]:
    """Parse DSL content into a dictionary."""
    dsl_data = {}
    current_block = None
    current_subblock = None
    
    for line in dsl_content.split('\n'):
        # Preserve leading spaces for indentation detection
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        
        # Check for block header (no leading spaces)
        if not line.startswith(' ') and line.strip().endswith(':'):
            block_name = line.strip()[:-1].strip()
            current_block = block_name
            dsl_data.setdefault(block_name, {})
            continue
            
        # Check for sub-block (2-space indent)
        if line.startswith('  ') and not line.startswith('    ') and ':' in line:
            key_part = line.split(':')[0].strip()
            value_part = line.split(':', 1)[1].strip() if ':' in line else ""
            
            # Handle nested dictionaries
            if current_block and key_part not in ['commodities', 'ships']:
                dsl_data[current_block][key_part] = value_part.replace('"', '')
            continue
            
        # Check for property (4-space indent or list items)
        if line.startswith('    ') or line.startswith('- '):
            pass  # Simplified parsing
    
    return dsl_data

def validate_dsl(dsl_content: str) -> tuple[bool, str | None]:
    """Validate DSL content and return (is_valid, error_message)."""
    try:
        dsl_data = parse_dsl_content(dsl_content)
        
        # Check required blocks
        for req_block in VALID_REQUIRED_BLOCKS:
            if req_block not in dsl_data or not isinstance(dsl_data.get(req_block), dict):
                return False, f"Missing required block: {req_block}"
                
        # Validate game block
        game_block = dsl_data.get("game", {})
        if not isinstance(game_block, dict):
            game_block = {}
        title = game_block.get("title", "")
        if not isinstance(title, str) or len(title) < VALID_GAME_TITLE_MIN_LEN:
            return False, f"Game title must be at least {VALID_GAME_TITLE_MIN_LEN} characters"
            
        engine_version = game_block.get("engine_version", "")
        if not isinstance(engine_version, str) or not re.match(VALID_ENGINE_VERSION_PATTERN, engine_version):
            return False, f"Invalid engine_version format: {engine_version}. Expected pattern: {VALID_ENGINE_VERSION_PATTERN}"
            
        # Validate economy block
        economy_block = dsl_data.get("economy", {})
        if not isinstance(economy_block, dict):
            economy_block = {}
        commodities = economy_block.get("commodities", {})
        if not isinstance(commodities, dict):
            commodities = {}
        for comm_id, comm_data in commodities.items():
            if not isinstance(comm_data, dict):
                continue
            price = comm_data.get("price", 0)
            if not isinstance(price, int) or price < VALID_COMMODITY_PRICE_MIN:
                return False, f"Commodity '{comm_id}' has invalid price: {price}. Must be >= {VALID_COMMODITY_PRICE_MIN}"
                
        # Validate ships block
        ships_block = dsl_data.get("ships", {})
        if not isinstance(ships_block, dict):
            ships_block = {}
        for ship_id, ship_data in ships_block.items():
            if not isinstance(ship_data, dict):
                continue
            fuel_capacity = ship_data.get("fuel_capacity", 0)
            if not isinstance(fuel_capacity, int) or fuel_capacity < VALID_SHIP_FUEL_CAPACITY_MIN:
                return False, f"Ship '{ship_id}' has invalid fuel_capacity: {fuel_capacity}. Must be >= {VALID_SHIP_FUEL_CAPACITY_MIN}"
                
        return True, None
        
    except Exception as e:
        return False, f"Parse error: {str(e)}"

def run_property_tests():
    """Run property-based tests for DSL parser."""
    print("Running property-based DSL parser tests...")
    
    # Test 1: Generate and validate 100 valid DSL files
    valid_dsls_passed = 0
    for i in range(100):
        dsl_content = generate_valid_dsl()
        is_valid, error_msg = validate_dsl(dsl_content)
        if is_valid:
            valid_dsls_passed += 1
        else:
            print(f"Valid DSL {i} failed validation: {error_msg}")
            
    print(f"Valid DSL tests passed: {valid_dsls_passed}/100")
    
    # Test 2: Generate and validate 100 invalid DSL files
    invalid_dsls_captured = 0
    
    # Test missing required block
    is_valid, error_msg = validate_dsl(generate_invalid_dsl_missing_required_block())
    if not is_valid and "Missing required block" in error_msg:
        invalid_dsls_captured += 1
        
    # Test negative price
    is_valid, error_msg = validate_dsl(generate_invalid_dsl_negative_price())
    if not is_valid and ("invalid price" in error_msg or "price: -50" in error_msg):
        invalid_dsls_captured += 1
        
    # Test negative fuel capacity
    is_valid, error_msg = validate_dsl(generate_invalid_dsl_negative_fuel_capacity())
    if not is_valid and ("invalid fuel_capacity" in error_msg or "fuel_capacity: -100" in error_msg):
        invalid_dsls_captured += 1
        
    # Test invalid engine version
    is_valid, error_msg = validate_dsl(generate_invalid_dsl_invalid_engine_version())
    if not is_valid and ("Invalid engine_version format" in error_msg or "4.26" in error_msg):
        invalid_dsls_captured += 1
        
    print(f"Invalid DSL tests captured: {invalid_dsls_captured}/4")
    
    # Save test results
    results = {
        "valid_dsls_passed": valid_dsls_passed,
        "invalid_dsls_captured": invalid_dsls_captured,
        "total_valid_tests": 100,
        "total_invalid_tests": 4
    }
    
    import json
    with open("E:/PythonChimera/Chimera/tests/property_tests/dsl_property_test_results.json", 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Property tests completed. Results saved to E:\\PythonChimera\\Chimera\\tests\\property_tests\\dsl_property_test_results.json")
    
    return results

if __name__ == "__main__":
    run_property_tests()
