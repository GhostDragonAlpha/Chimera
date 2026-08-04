# Task 9 — Scene-Registry Audit (read-only)

## Method

Compared the three registries in
`ChimeraEngine/splat_appearance.py`:

1. SCENES dict (keys = term names, each entry has a "kind" field)
2. _BUILDERS dict (kind -> builder function, at lines 3075 and 3323)
3. Defined _*_buffers functions (via grep for `def _.*_buffers`)

Checked for: kinds in SCENES without builders, defined functions
not registered, kinds registered but no SCENES entry.

## The three registries compared

### SCENES dict (40 entries) — kinds used

| Kind | SCENES term |
|------|-------------|
| collapse | theStar |
| planet | aPlanet |
| terrain | theTerrain |
| row | thePlanets |
| system | theSolarSystem |
| garden | theGarden |
| ecosystem | theEcosystem |
| tree | theTree |
| treeform | theTreeForm |
| fruit | theFruit |
| planting | thePlanting |
| farming | theFarming |
| planetary_farm | thePlanetaryFarm |
| lunar_farm | theLunarFarm |
| orbital_farm | theOrbitalFarm |
| space | theSpace |
| seed | theSeed |
| determinism | theDeterminism |
| laws | theLaws |
| truth | theTruth |
| ship | theShip |
| flight | theFlight |
| ship_power | theShipPower |
| ship_combat | theShipCombat |
| shields | theShields |
| warp_drive | theWarpDrive |
| ship_view | theShipView |
| salvage | theSalvage |
| descent | theDescent |
| standing | theStanding |
| black_hole | theBlackHole |
| verbs | theVerbs |
| dig | theDig |
| grow | theGrow |
| scan | theScan |
| navigate | theNavigate |
| shoot | theShoot |
| melee | theMelee |
| eva | theEVA |
| player | thePlayer |

### _BUILDERS dict (40 entries) — kind -> function

Defined at both line 3075 (_build_movie) and line 3323 (scene_buffer):

    "planet":         _planet_buffers         (line 186)
    "terrain":        _terrain_buffers        (line 283)
    "row":            _row_buffers            (line 362)
    "system":         _system_buffers         (line 2988)
    "garden":         _garden_buffers         (line 431)
    "ecosystem":      _ecosystem_buffers      (line 506)
    "tree":           _tree_buffers           (line 571)
    "treeform":       _treeform_buffers       (line 612)
    "fruit":          _fruit_buffers          (line 686)
    "planting":       _planting_buffers       (line 752)
    "farming":        _farming_buffers        (line 813)
    "planetary_farm": _planetary_farm_buffers (line 894)
    "lunar_farm":     _lunar_farm_buffers     (line 982)
    "orbital_farm":   _orbital_farm_buffers   (line 1078)
    "space":          _space_buffers          (line 1163)
    "seed":           _seed_buffers           (line 1206)
    "determinism":    _determinism_buffers    (line 1265)
    "laws":           _laws_buffers           (line 1309)
    "truth":          _truth_buffers          (line 1352)
    "ship":           _ship_buffers           (line 1407)
    "flight":         _flight_buffers         (line 1514)
    "ship_power":     _ship_power_buffers     (line 1615)
    "ship_combat":    _ship_combat_buffers    (line 1705)
    "shields":        _shields_buffers        (line 1788)
    "warp_drive":     _warp_drive_buffers     (line 1871)
    "ship_view":      _ship_view_buffers      (line 1943)
    "salvage":        _salvage_buffers        (line 2024)
    "descent":        _descent_buffers        (line 2110)
    "standing":       _standing_buffers       (line 2187)
    "black_hole":     _black_hole_buffers     (line 2271)
    "verbs":          _verbs_buffers          (line 2354)
    "dig":            _dig_buffers            (line 2457)
    "grow":           _grow_buffers           (line 2525)
    "scan":           _scan_buffers           (line 2578)
    "navigate":       _navigate_buffers       (line 2636)
    "shoot":          _shoot_buffers          (line 2692)
    "melee":          _melee_buffers          (line 2789)
    "eva":            _eva_buffers            (line 2834)
    "player":        _player_buffers         (line 2901)
    "input":          _input_buffers          (line 2929)

## Cross-check results

| Check | Result |
|-------|--------|
| Kinds in SCENES but NOT in _BUILDERS | collapse (theStar) — by design: handled by physics-based particle code path |
| Builder functions defined but NOT in _BUILDERS | None — all 40 defined _*_buffers functions are registered |
| Kinds in _BUILDERS but NO SCENES entry | input — registered at both line 3075 and 3323, _input_buffers defined line 2929, but no SCENES entry uses kind="input" |

## The one finding

_input_buffers is registered in _BUILDERS and defined as a function, but
no entry in the SCENES dict references kind="input".

This is the mirror image of the _tree_buffers bug noted in Task 7's task
description (_tree_buffers was deleted while referenced). Here, the function
exists and is registered, but has no scene to bind to. It could be:

1. A reserved/stub builder for a not-yet-authored scene (intentional).
2. A leftover from a deleted or renamed SCENES entry.
3. theInput handled as a membrane — if story/.../theInput/ exists as a
   membrane with its own physics.py, it would be handled by the
   membrane-based scene path, bypassing SCENES entirely.

Recommendation: check whether story/.../theInput/ exists as a membrane
and whether theInput is referenced in COMPOSITIONS or SCENES. If not,
the _input_buffers registration is dead code.

## Summary

40 SCENES entries, 40 _BUILDERS entries, 40 _*_buffers functions.
All three are consistent EXCEPT:
- "collapse" kind is handled by a separate code path (not a bug)
- "input" builder is registered but never invoked (potential dead code)
