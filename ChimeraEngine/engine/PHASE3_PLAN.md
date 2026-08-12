# SPIACE Phase 3: Multi-System

## Goals
- Procedural star system generation (spectral types, habitable zone)
- Warp/faster-than-light travel (skip between systems, preserve momentum)
- Multiple player ships (local co-op first, then networked)
- Deliverable: Travel between two star systems

## Architecture

### Procedural Star System Generator
```python
def generate_system(seed):
    # Spectral type determines star mass, luminosity, color
    spectral_types = ['O','B','A','F','G','K','M']
    # Habitable zone based on stellar luminosity
    # Place planets at stable orbital distances
    # Generate asteroid belts, gas giants, ice giants
```

### Warp Travel
- Enter warp field when velocity exceeds threshold
- Skip to target system coordinates
- Preserve momentum through jump (relativistic correction optional)
- Visual: star streak effect via ray-marched void distortion

### Multi-System Navigation UI
- Star map view (2D projection of local stellar neighborhood)
- Waypoint system for jump planning
- Fuel consumption model for interstellar travel

## Files to Create/Modify
- `engine/spiace_phase3.html` - Main demo
- `core/stellar_generator.py` - Procedural star system generation
