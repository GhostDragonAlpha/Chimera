"""Deterministic parsers for the pinned reference artifacts.

NO LLM rows: every record is produced by a fixed textual rule. NO execution:
the .osim model file is parsed as XML only (xml.etree refuses external entity
expansion by default; we additionally never touch its geometry/executable
content beyond the declarative elements listed).

Parsers return plain dicts so the importer can build records + provenance
without hidden state.
"""

import os
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# OBO (Uberon appendicular-minimal)
# ---------------------------------------------------------------------------

def parse_obo(path: str) -> dict:
    """Parse OBO stanzas. Returns {header: {...}, terms: [term dicts]}.
    Each term: id, name, definition, is_a [ids], relationships [(type, target)],
    subsets, synonyms, comment. Multiline `def`/`property_value` handled with a
    quoted-string scanner; xref suffixes stripped from def."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    header = {}
    terms = []
    cur = None
    stanza_re = re.compile(r"^\[(Term|Typedef)\]$")

    def flush():
        nonlocal cur
        if cur is not None:
            terms.append(cur)
        cur = None

    for line in text.splitlines():
        line = line.rstrip("\n")
        if stanza_re.match(line.strip()):
            flush()
            cur = {"id": None, "name": None, "definition": None, "is_a": [],
                   "relationships": [], "subsets": [], "synonyms": [],
                   "comment": None, "is_typedef": line.strip() == "[Typedef]",
                   "property_values": []}
            continue
        if cur is None:
            if ": " in line and not line.startswith("!") and line.strip():
                k, v = line.split(": ", 1)
                header.setdefault(k, []).append(v.strip())
            continue
        if not line.strip():
            continue
        m = re.match(r"^(id|name|comment|subset|is_a|relationship|def|synonym|"
                     r"property_value|intersection_of|consider|replaced_by|"
                     r"disjoint_from|alt_id|xref|ontology|namespace): (.*)$",
                     line)
        if not m:
            continue  # lines we do not understand are skipped (recorded nowhere)
        key, val = m.group(1), m.group(2)
        if key == "id":
            cur["id"] = val
        elif key == "name":
            cur["name"] = val
        elif key == "comment":
            cur["comment"] = val
        elif key == "subset":
            cur["subsets"].append(val)
        elif key == "is_a":
            cur["is_a"].append(val.split("!")[0].strip())
        elif key == "relationship":
            parts = val.split("!")[0].strip()
            bits = parts.split()
            if len(bits) >= 2:
                # strip any {…} constraints, keep type + target id
                tgt = re.sub(r"\{.*\}", "", " ".join(bits[1:])).strip()
                cur["relationships"].append((bits[0], tgt))
        elif key == "def":
            mm = re.match(r'^"(.*)"\s*(\[[^\]]*\])?\s*$', val, re.S)
            cur["definition"] = mm.group(1) if mm else val
        elif key == "synonym":
            mm = re.match(r'^"(.*)"', val, re.S)
            if mm:
                cur["synonyms"].append(mm.group(1))
        elif key == "property_value":
            cur["property_values"].append(val)
    flush()
    return {"header": header, "terms": terms}


# selected RO relation IRIs the projection needs (meaning preserved, cited)
RO_SELECTED = {
    "http://purl.obolibrary.org/obo/BFO_0000050": "part_of",
    "http://purl.obolibrary.org/obo/BFO_0000051": "has_part",
    "http://purl.obolibrary.org/obo/RO_0002150": "continuous_with",
    "http://purl.obolibrary.org/obo/RO_0002170": "adjacent_region_of",
    "http://purl.obolibrary.org/obo/RO_0001018": "contained_in",
    "http://purl.obolibrary.org/obo/RO_0001019": "contains",
    "http://purl.obolibrary.org/obo/RO_0002371": "attached_to_part_of",
    "http://purl.obolibrary.org/obo/RO_0002372": "attached_to SurfaceOf",
    "http://purl.obolibrary.org/obo/BFO_0000056": "participates_in",
    "http://purl.obolibrary.org/obo/RO_0000053": "realizes",
}


def parse_ro_owl(path: str) -> list:
    """Extract the SELECTED relation IRIs from ro-base.owl (RDF/XML):
    label + definition. Returns [{iri, label, definition, short}] -- the
    relation-TYPE records. Anything the simplified projection omits (domain/
    range/chains) is documented by the importer, not silently dropped here.
    Terms appear as owl:ObjectProperty / owl:AnnotationProperty / owl:Class /
    rdf:Description elements carrying rdf:about."""
    ns = {
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "owl": "http://www.w3.org/2002/07/owl#",
    }
    defn_tag = "{http://purl.obolibrary.org/obo/}IAO_0000115"
    about_attr = "{%s}about" % ns["rdf"]
    label_tag = "{%s}label" % ns["rdfs"]
    tree = ET.parse(path)
    root = tree.getroot()
    found = {}
    for el in root.iter():
        about = el.get(about_attr)
        if about in RO_SELECTED and about not in found:
            label = el.findtext(label_tag)
            definition = el.findtext(defn_tag)
            found[about] = {"iri": about, "short": RO_SELECTED[about],
                            "label": label, "definition": definition}
    return [found[iri] for iri in sorted(found)]


# ---------------------------------------------------------------------------
# QUDT Turtle (subset parser: the predicates the creature laws need)
# ---------------------------------------------------------------------------

QUDT_PREDICATES = {
    "rdfs:label": ("label", re.compile(r'^\s*rdfs:label\s+"([^"]*)"')),
    "qudt:symbol": ("symbol", re.compile(r'^\s*qudt:symbol\s+"([^"]*)"')),
    "qudt:conversionMultiplier": ("conversion_multiplier",
                                  re.compile(r"^\s*qudt:conversionMultiplier(?:SN)?\s+"
                                             r"([-+0-9.eE]+)")),
    "qudt:hasDimensionVector": ("dimension_vector",
                                re.compile(r"^\s*qudt:hasDimensionVector\s+(\S+)")),
    "qudt:hasQuantityKind": ("quantity_kinds",
                             re.compile(r"^\s*qudt:hasQuantityKind\s+(\S+)")),
    "qudt:applicableUnit": ("applicable_units",
                            re.compile(r"^\s*qudt:applicableUnit\s+(\S+)")),
    "qudt:iec61360Code": ("iec61360_code",
                          re.compile(r'^\s*qudt:iec61360Code\s+"([^"]*)"')),
    "qudt:uneceCommonCode": ("unece_common_code",
                             re.compile(r'^\s*qudt:uneceCommonCode\s+"([^"]*)"')),
    "dcterms:description": ("description", re.compile(r'^\s*dcterms:description\s+"([^"]*)"')),
}


def parse_qudt_ttl(path: str) -> dict:
    """Parse ONE unit/quantitykind Turtle file (the served document for one
    IRI). Deterministic line-based subset: subject = the first declared IRI,
    predicates from QUDT_PREDICATES. LangSuffix '@en' and '^^xsd:...' stripped.
    The projection omits factor-unit structures / SYUN references (documented)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    subject = None
    rec = {"subject": None, "label": None, "symbol": None,
           "conversion_multiplier": None, "dimension_vector": None,
           "quantity_kinds": [], "applicable_units": [], "iec61360_code": None,
           "unece_common_code": None, "description": None}
    for line in text.splitlines():
        if subject is None:
            m = re.match(r"^(unit:\S+|quantitykind:\S+)$", line.strip())
            if m:
                subject = m.group(1)
                rec["subject"] = subject
            continue
        if line.strip().startswith("@") or line.strip().startswith("#"):
            continue
        m = re.match(r"^(unit:\S+|quantitykind:\S+)\s*$", line.strip())
        if m and m.group(1) != subject:
            subject = m.group(1)
            continue
        for pred, (slot, rx) in QUDT_PREDICATES.items():
            mm = rx.match(line)
            if mm:
                val = mm.group(1).rstrip(" ,;")
                val = re.sub(r"@en$", "", val)
                if slot == "quantity_kinds":
                    rec["quantity_kinds"].append(val.split(":")[-1])
                elif slot == "applicable_units":
                    rec["applicable_units"].append(val.split(":")[-1])
                elif rec[slot] is None:
                    rec[slot] = val
    return rec


# ---------------------------------------------------------------------------
# OpenSim .osim (XML ONLY -- never executed)
# ---------------------------------------------------------------------------

def parse_osim(path: str, max_bytes: int = 20 << 20) -> dict:
    """Parse a .osim model DEFINITION: model name/version, bodies (name, mass,
    inertia presence), joints (name, type, parent/child), muscles (name +
    Thelen parameters). Importing NEVER executes the model; only declarative
    elements are read. Raises if the file is unexpectedly large."""
    if os.path.getsize(path) > max_bytes:
        raise ValueError(f"refusing to parse oversized model file: {path}")
    tree = ET.parse(path)  # refuses undefined entities (no XXE) by default
    root = tree.getroot()
    version = root.get("Version")
    model = root.find(".//Model")
    out = {"model_name": model.get("name") if model is not None else None,
           "osim_version": version, "bodies": [], "joints": [], "muscles": [],
           "coordinates": []}
    bodies = {}
    for body in root.iter("Body"):
        name = body.get("name")
        mass = body.findtext("Mass")
        bodies[name] = True
        out["bodies"].append({"name": name, "mass_kg": mass,
                              "has_inertia": body.find("InertialParameters") is not None
                              or body.find("inertial_parameters") is not None})
    for joint in root.iter():
        if joint.tag.endswith("Joint") and joint.get("name"):
            texts = [c.text for c in joint.iter("socket_parent_frame")]
            out["joints"].append({"name": joint.get("name"), "type": joint.tag,
                                  "parent_frames": texts[:2]})
    for coord in root.iter("Coordinate"):
        name = coord.get("name")
        rng = [coord.findtext("range_min"), coord.findtext("range_max")]
        out["coordinates"].append({"name": name, "range": rng})
    for mus in root.iter("Thelen2003Muscle"):
        def f(tag):
            v = mus.findtext(tag)
            return float(v) if v not in (None, "") else None
        out["muscles"].append({
            "name": mus.get("name"),
            "max_isometric_force_N": f("max_isometric_force"),
            "optimal_fiber_length_m": f("optimal_fiber_length"),
            "tendon_slack_length_m": f("tendon_slack_length"),
            "pennation_angle_at_optimal_rad": f("pennation_angle_at_optimal"),
            "max_contraction_velocity": f("max_contraction_velocity"),
            "activation_time_constant_s": f("activation_time_constant"),
            "deactivation_time_constant_s": f("deactivation_time_constant"),
        })
    out["n_bodies"] = len(out["bodies"])
    out["n_joints"] = len(out["joints"])
    out["n_muscles"] = len(out["muscles"])
    return out
