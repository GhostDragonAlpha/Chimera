# Physical ports: material-owned interaction fields

Captain's architectural decision, 2026-09-27; recorded by the Lieutenant.
Status: adopted definition and implementation direction, not a runtime qualification.

> A port is a localized physical interaction field owned by one element of matter.

The Captain described this as "a collision field but for only one element of
matter." A port belongs to that element before another element interacts with it.
It is not the pairwise connection itself. A membrane defines that element's
boundary, contents and material state; its physical ports define where and how
it can interact. A port may cover an entire surface or a selected region.

## Containment and interaction

Physical containment establishes the enclosing material environment. The outer
membrane's state and laws constrain its contents through applicable pressure,
contact, friction, fluid coupling or bonds. The interior material retains its
own state and response law and pushes back on its surroundings. Enclosure is
not automatic rigid attachment or a copied parent transform. Whether it holds,
slides, deforms or releases depends on the participating material/interface laws.
An organizational parent such as a software subsystem is not a physical enclosure.

Contact or declared embedding activates the compatible interaction laws over the
affected region automatically: these elements are physically connected there
without manually wiring each triangle pair. The runtime discovers and maintains
the interaction between their material-owned fields. Contact regions evolve with
geometry; ordinary contact deactivates on separation. Bonded or embedded interfaces
persist, slip, fail or release according to their declared laws. Accidental mesh
penetration must not silently become authored embedding or adhesion.

The port identifies the applicable law and its support region; contact does not
invent coefficients, valid material parameters or mechanical qualification.
Missing or incompatible laws must be reported explicitly. Constitutive choices
remain versioned, measurable and subject to their existing scientific gates.

## Force transfer and bookkeeping

Pressure acts through surface area and the local normal. For uniform pressure
difference on a planar patch, the pressure contribution is delta_p * area * normal;
equal pressure does not mean equal force on differently sized triangles. Other
traction laws can add tangential forces or depend on strain, velocity and history.

Coupled elements exchange forces through the same physical interaction, with
balanced action/reaction accounting. Record environmental loads and boundary
conditions separately. Count each interaction once even though both ports observe
it. Changing containment or adding a port must not duplicate mass, state or force.
Local contacts, bonds and pressure are not automatically Barnes-Hut far-field laws.

## Implementation and visual verification

Use the existing MAT2 material foundation and composition tasks. Reconcile existing
code first; this decision does not authorize a replacement solver or a new campaign.
The implementation needs stable owner/port IDs, a geometric support region, law and
parameter identity, relevant state, and active interaction records referencing both
participants and their affected regions. These are semantic requirements, not a
new JSON schema imposed on running workers.

The first applicable demonstration should show two independently owned elements:
approach, contact activation, force transfer, sliding where permitted, and separation.
An enclosure case should show a child's response to the parent's changing physical
state and the child's reaction on the parent. Where embedding or bonding is tested,
show the specified persistence and release/failure behavior separately.

Numerical probes must distinguish contact from a permanent weld, account for paired
forces without double counting, and verify area-dependent pressure loading. Check
mesh refinement against the declared error tolerance rather than changing physical
behavior merely by changing the number of triangles.

Native visual evidence should expose owner and port IDs, active interface patches,
force directions and relevant material state. Preserve camera position, orientation,
target, angle/FOV, distance, clipping, resolution and tick interval, with both
diagnostic and clean views. Hiding diagnostic fields must not alter the simulation.
Required physical evidence is not replaced by a diagram of the proposed interface.

## Adoption boundary

This supersedes descriptions of physical ports as only manually authored links.
Explicit source-model joints, tendons and software/protocol interfaces remain valid
records; their presence is not proof that automatic material interactions exist.
The current ontology JSON is an authored structural view, not yet a runtime inventory
of every discovered contact. Do not silently reinterpret legacy schema fields.

Workers read this ruling at their next checkpoint/startup, reconcile it with their
assigned scope, and report a specific conflict through the task inbox. Preserve
existing criteria hashes and receipts. If a frozen task cannot express a required
behavior, obtain an explicit lead amendment before implementation/acceptance;
do not rewrite its criteria or retroactively declare its old evidence sufficient.
