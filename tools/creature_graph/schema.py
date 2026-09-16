"""Creature graph schema -- the object schema every membrane object carries.

Design (operator-approved, 2026-09-15): the creature is ONE GRAPH with three
coordinated views (spatial / physical / roadmap) projected from a single object
store. Selecting an object in any view selects the same object in all three.

Every membrane object carries:
  identity          stable dotted id, e.g. creature.leg_l.knee.capsule
  classification    membrane TYPE id -- types are reusable definitions,
                    instances are separate identities
  spatial frame     engine-coordinate placement (frames, curve endpoints,
                    envelope anchors); graph-layout positions are stored
                    SEPARATELY (store.layout), never mixed with these
  geometry          placeholder envelope -> later validated mesh, with an
                    explicit `unknowns` list
  connections       attachments to other structures (attached_to / rims)
  physical          material law, rest shape, permeability -- unknown
                    dimensions stay EXPLICITLY unknown (unknowns list)
  implementation    specified / extracted / geometry_built / simulated /
                    verified -- EXTRACTED != physically-verified is enforced
                    (extracted ranks BELOW verified and never satisfies a
                    verification requirement)
  dependencies      mirrored as requires_implementation relations (DAG)
  evidence          test results tied to an implementation version
  falsifier         statement + acceptance test + test status

Graph holds CURVES (nerve routes, tendon paths, bone centerlines), SURFACES
(skin, septa, capsules), VOLUMES (compartments), ATTACHMENTS, COORDINATE
FRAMES. A membrane references its oriented surface plus the regions on both
sides (region_a / region_b) -- enough to ask "is this compartment actually
enclosed?".

Relationship types (kept DISTINCT -- physical connections may cycle, e.g.
reflex loops; implementation prerequisites and provenance derivations are DAGs):
  physical   inside, bounds_region, attached_to, contains, transmits_force_to,
             carries_signal_to, uses_material, uses_model
  provenance derived_from (cites sources; cycles are bookkeeping errors)
  implement  requires_implementation          (must stay acyclic)
  meta       verified_by, enables_player_experience
Relations are a LIST of (src, rel, dst, note): MULTIPLE DISTINCT relationships
between the same pair are preserved (e.g. a septum attached_to a compartment
AND transmits_force_to it are two separate edges).

Schema version 2.0.0 (2026-09-15, G2-creature-graph): adds the body-machinery
kinds (actuator/sensor/pathway/material/model/parameter/requirement), the
reference-data families (source/reference_entity/relationship/
property_assertion/geometry_asset/mapping/model_definition), the provenance
relation, validation staleness, and the layout/spatial separation guard.
1.0.0-unversioned = the pre-2026-09-15 module set.
"""

KINDS = (
    "type",              # reusable membrane definition (one per inventory item)
    "volume",            # compartments, joint cavities, muscle bellies
    "surface",           # skin, septa, capsules, receptor patches
    "curve",             # bone centerlines, tendon paths, nerve routes
    "attachment",        # bonded rims, insertions, sliding interfaces
    "frame",             # coordinate frames (measured joint anchors)
    "region",            # named spatial regions (band regions, limb subregions)
    "evidence",          # test results tied to an implementation version
    "experience",        # player experiences (product-side targets)
    "capability",        # engine machinery an implementation may reuse
    "work",              # implementation work items (prerequisite DAG nodes)
    # --- body-part machinery kinds (brief entity list, 2026-09-15) ---
    "actuator",          # force/torque-limited servos etc. (labeled honestly)
    "sensor",            # receptor patches / telemetry surfaces
    "pathway",           # signal pathways (disconnectable, finite delay)
    "material",          # a physical material (water, skin membrane, glue...)
    "model",             # a physical/constitutive model (water law, press law)
    "parameter",         # a SELECTED creature parameter (units+source+applicability)
    "requirement",       # an AUTHORED product/physics requirement (never imported)
    # --- reference-data record families (brief: ingestion section) ---
    "source",            # a pinned external source (release, checksum, license)
    "reference_entity",  # an external concept (e.g. UBERON:0000981 femur)
    "relationship",      # an external relation type (RO: part_of, has_part...)
    "property_assertion",# a reference assertion (quantity, units, value, conditions)
    "geometry_asset",    # a reference mesh/geometry FILE reference (never verts)
    "mapping",           # an explicit mapping record (equiv / broader-narrower /
                         #   analogue / candidate -- similarity is a CANDIDATE)
    "model_definition",  # an imported model file's definition record (never executed)
)

# Order matters: implementation status ladder. EXTRACTED is a real measured
# state but is NOT physically verified -- it ranks below geometry_built and
# never satisfies a verification requirement.
STATUS_ORDER = ("specified", "extracted", "geometry_built", "simulated", "verified")
STATUS_RANK = {s: i for i, s in enumerate(STATUS_ORDER)}

# Priority ladder from the inventory (docs/THE_MEMBRANE_INVENTORY.md).
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}

REL_INSIDE = "inside"
REL_BOUNDS = "bounds_region"   # the brief's name for the membrane-bounds-region edge
REL_ATTACHED = "attached_to"
REL_FORCE = "transmits_force_to"
REL_SIGNAL = "carries_signal_to"
REL_CONTAINS = "contains"
REL_USES_MATERIAL = "uses_material"
REL_USES_MODEL = "uses_model"
REL_DERIVED_FROM = "derived_from"   # provenance: creature thing / assertion / task
                                    # cites the reference or authored thing it came from
REL_REQUIRES = "requires_implementation"
REL_VERIFIED_BY = "verified_by"
REL_ENABLES = "enables_player_experience"

RELATIONS = (
    REL_INSIDE, REL_BOUNDS, REL_ATTACHED, REL_FORCE, REL_SIGNAL, REL_CONTAINS,
    REL_USES_MATERIAL, REL_USES_MODEL, REL_DERIVED_FROM,
    REL_REQUIRES, REL_VERIFIED_BY, REL_ENABLES,
)

# cycles are ALLOWED on these (reflex loops are real physics)
PHYSICAL_RELS = (REL_INSIDE, REL_BOUNDS, REL_ATTACHED, REL_FORCE, REL_SIGNAL,
                 REL_CONTAINS, REL_USES_MATERIAL, REL_USES_MODEL)
# cycles are FORBIDDEN on these: implementation prerequisites form a DAG, and a
# provenance derivation cycle is a bookkeeping error, not a physical loop.
DAG_RELS = (REL_REQUIRES, REL_DERIVED_FROM)
META_RELS = (REL_VERIFIED_BY, REL_ENABLES)

# membrane object kinds that must name both sides (the enclosure question)
MEMBRANE_KINDS = ("volume", "surface")

# reference-data families: every record MUST carry provenance to its Source
REFERENCE_KINDS = ("source", "reference_entity", "relationship",
                   "property_assertion", "geometry_asset", "mapping",
                   "model_definition")

# keys that are FORBIDDEN inside `spatial`: roadmap/layout positions live in
# store.layout, never mixed with engine coordinates (the brief's distinction 6).
FORBIDDEN_SPATIAL_KEYS = ("roadmap_tier", "roadmap_x", "layout_x", "layout_y")

# environment may be one side of a membrane (the brief's enclosure question)
ENVIRONMENT = "environment"

SCHEMA_VERSION = "2.0.0"
# prior (pre-2026-09-15) store modules carried no version field
SCHEMA_VERSION_LEGACY = "1.0.0-unversioned"

# the PHYSICS-RELEVANT fields: a change to any of these stales dependent
# validation evidence. Cosmetic fields (name, notes) do NOT.
PHYSICS_FIELDS = ("physical", "spatial", "geometry", "status", "attachments",
                  "unknowns", "value", "units", "source", "applicability",
                  "science_funnel")

OBJECT_FIELDS = (
    "id", "kind", "name", "classification", "status", "priority",
    "build_rank", "order_hint", "inventory_anchor", "spatial", "geometry",
    "physical", "attachments", "dependencies", "evidence", "falsifier",
    "unknowns", "notes", "provenance",
)


def status_at_least(status: str, threshold: str) -> bool:
    """True if `status` is at or above `threshold` on the ladder.

    `available` threshold (geometry_built) means the thing exists as geometry
    you can build against. NOTE: `extracted` never counts as implemented and
    never counts as verified.
    """
    return STATUS_RANK.get(status, -1) >= STATUS_RANK[threshold]


def validate_object(obj: dict) -> list:
    """Return a list of schema violations for one object (empty = valid)."""
    errs = []
    oid = obj.get("id", "<no-id>")
    if obj.get("kind") not in KINDS:
        errs.append(f"{oid}: bad kind {obj.get('kind')!r}")
    if obj.get("status") not in STATUS_RANK:
        errs.append(f"{oid}: bad status {obj.get('status')!r}")
    if obj.get("priority") not in PRIORITY_RANK and obj.get("kind") not in (
            "evidence", "source", "reference_entity", "relationship",
            "property_assertion", "geometry_asset", "mapping",
            "model_definition", "requirement"):
        errs.append(f"{oid}: bad priority {obj.get('priority')!r}")
    for field in ("id", "kind", "name", "status"):
        if field not in obj:
            errs.append(f"{oid}: missing field {field}")
    # a membrane must name its sides enough to ask "is it actually enclosed?":
    # a SURFACE (wall) needs both regions (the environment may be one);
    # a VOLUME (region owner) needs at least its own region_a
    if obj.get("kind") == "volume" and obj.get("classification"):
        phys = obj.get("physical") or {}
        if not phys.get("region_a"):
            errs.append(f"{oid}: volume without region_a (which region does it own?)")
        if not phys.get("law"):
            errs.append(f"{oid}: volume without a material law")
        fz = obj.get("falsifier") or {}
        if not fz.get("statement"):
            errs.append(f"{oid}: membrane without a falsifier (RULE 0: no falsifier, no build)")
    if obj.get("kind") == "surface" and obj.get("classification"):
        phys = obj.get("physical") or {}
        if not phys.get("region_a") or not phys.get("region_b"):
            errs.append(f"{oid}: membrane without region_a/region_b (enclosure unanswerable)")
        if not phys.get("law"):
            errs.append(f"{oid}: membrane without a material law")
        fz = obj.get("falsifier") or {}
        if not fz.get("statement"):
            errs.append(f"{oid}: membrane without a falsifier (RULE 0: no falsifier, no build)")
    # graph-layout coordinates can NEVER travel with engine coordinates
    sp = obj.get("spatial") or {}
    for k in FORBIDDEN_SPATIAL_KEYS:
        if k in sp:
            errs.append(f"{oid}: spatial carries layout key {k!r} (layout lives in store.layout)")
    # reference records must say where they came from
    if obj.get("kind") in REFERENCE_KINDS and obj.get("kind") != "source":
        prov = obj.get("provenance") or {}
        if not prov.get("source_id"):
            errs.append(f"{oid}: reference record without provenance.source_id")
    # a SELECTED parameter must state units/source/applicability -- "unknown"
    # is an honest VALUE, absent is a violation (missing metadata stays
    # EXPLICITLY unknown)
    if obj.get("kind") == "parameter":
        for f in ("units", "source", "applicability"):
            if f not in obj:
                errs.append(f"{oid}: selected parameter without explicit {f} "
                            f"(write 'unknown' when unknown)")
    return errs


def content_projection(obj: dict) -> dict:
    """The physics-relevant projection of an object: the part a change to which
    stales dependent validation evidence."""
    return {k: obj.get(k) for k in PHYSICS_FIELDS if k in obj}
