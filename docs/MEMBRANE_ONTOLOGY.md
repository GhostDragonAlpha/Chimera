# Membranes: the hierarchy of the ontology

Operator clarification, 2026-09-24; lead architectural interpretation v1.

A membrane is a unit in the ontology. It encompasses its definition, boundary,
contents, physics and validation. It can contain other membranes and connect to
other membranes through ports. This applies recursively: the creature contains
its skeletal structure, musculature and skin; the skeletal structure contains
individual bones and their joint connections. A connection can itself be a
membrane, with its own ports, law, parameters and evidence.

The chosen outer skin/mesh supplies the creature's geometric envelope. The skin
as tissue/material is also a constituent of the creature. Referencing the same
surface as an envelope does not create another mass contribution. A membrane can
also be non-spatial (a controller or software service); its boundary then names
an interface or responsibility rather than inventing a physical surface.

## The two relations

**Containment** gives each entry one immediate parent in this authored hierarchy.
Stable IDs survive moves and renames. A child's membership does not automatically
inherit mass, density, a frame, proof, or runtime readiness from its parent.

**Connection** links explicit ports on named membranes. It never reparents them.
Ports declare a protocol and units; connection compatibility is a structural
check, not proof of mechanical sufficiency. Nested interfaces can expose a
descendant's port through an explicit `delegates_to` mapping. Direction, stiffness,
limits and transfer laws belong in the physical contract when applicable; the
inspector must not manufacture them. A connected joint or tendon can still be
unqualified. An open port is useful information, not automatically an error.

## One definition for people and agents

`tools/membrane_ontology/ontology.json` is the authored composition definition.
`tools/membrane_ontology/inspect_ontology.py` validates it and produces the same JSON that
`web/ontology/index.html` displays. The definition is an architectural model,
not a claim that its runtime bindings are complete. Authored connections are
explicitly marked planned until their actual implementation is qualified.

Every entry has an ID, parent, kind, description, boundary, physics, validation,
ports and source references. Connection entries also name endpoint membrane/port
pairs. Source file existence and SHA-256 identify inspected bytes, not truth.
The snapshot hash detects a content change; it does not authenticate the author.
Only the designated lead changes the composition contract. Workers propose PRs
and use the existing task-ID inbox. Shared-account write access is not a security
boundary, and the inspector supplies no editing or task-completion endpoint.

## Matter and imported anatomy

Matter remains owned by explicit stable matter/cell IDs and authored body groups.
The ontology locates those definitions; the existing material compiler and
admission/export checks remain responsible for mass accounting. Connecting,
reparenting or displaying a membrane must not duplicate or validate matter.
Density and full-tensor/frame rules remain those of the material-volume contract.

MuJoCo XML is a source of authored body, joint, tendon and actuator declarations.
An import must preserve identifiers, source hierarchy, coordinates, defaults and
include provenance. A MuJoCo body is not automatically one anatomical bone, and
a source-model joint tree is not automatically the ontology's containment tree.
Any proposed mapping between them needs explicit evidence. Loading XML or drawing
a hierarchy does not qualify the mesh, physical assembly or gameplay.

This first inspector exposes the composition and source references. It does not
compile MuJoCo or silently resolve anatomical owners. Individual bones, muscles
and attachment ports must enter through an explicit source-bound import; absent
ones are recorded as gaps rather than filled from names or symmetry guesses.

## Legacy sources and migration

`Chimera/docs/THE_STORY.md` currently declares the teddy-bear terms; its generated
`ChimeraEngine/terms_data.py` supplies the engine hierarchy shape. Saved
`engine_state.json` carries historical progress. Those records are not the current
playable-monkey acceptance ledger and are not silently rewritten by this viewer.
Graphify's code graph is a useful implementation index, not an authored anatomical
ownership or membrane-containment authority. Link it as evidence when relevant.

The older wording "every membrane is a theory" describes the validation obligation
on a membrane's claims. It does not remove its structural role in the ontology.
Physics, boundaries and falsifiers stay attached to the membrane they describe.

## Next implementation steps

1. Source-bound anatomy import: preserve MuJoCo includes/defaults and distinguish
   model bodies from anatomical bones; reconcile the existing forearm decisions.
2. Bind the chosen envelope and skin without creating duplicate matter ownership.
3. Resolve actual port contracts, units, frames and mechanical parameters; run the
   existing assembly gates before any runtime binding.
4. Add a per-PR ontology diff and invalidate only evidence whose bound inputs changed.
5. Link accepted task IDs and native visual receipts to their membrane IDs. Graph
   validity and a browser screenshot never substitute for a playable runtime test.

## Preregistered inspector checks

Statement: one authored hierarchy can be inspected by agents and the browser
without altering physics or hiding missing relationships.

Prediction: valid nested definitions and explicit port connections export
deterministically; malformed containment and endpoint references produce named
refusals; missing source files remain visible; source bytes are unchanged.

Falsifiers (declared before implementation): O1 duplicate IDs; O2 missing parent,
multiple roots or containment cycles; O3 missing endpoint/port or incompatible
protocol/units; O4 invalid descendant port exposure; O5 unsafe source path; O6
nondeterministic output or changed input bytes; O7 missing source presented as
present; O8 browser tree/port/details disagree with the exported JSON; O9 browser
search, deep-link, refresh, mobile layout or missing-data display fails.
