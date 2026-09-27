# Semantic 3D verification

Spatial semantics are data, not a vision-model guess. A mesh can prove its triangles,
normals and connectivity, but a smooth paddle cannot prove that one face is a palm.
Chimera therefore qualifies a semantic direction only when geometry, independent
biological evidence and a physical consequence agree in one explicit coordinate frame.

This is the bridge between the institutions of human knowledge and the simulation:

1. **Biology names the relation.** An authoritative source or direct measurement
   identifies landmarks, topology, sidedness and terms such as proximal, distal,
   dorsal, palm, medial and lateral. Every claim carries a citation or artifact hash.
2. **Geometry locates it.** At least three non-collinear, identity-pinned landmarks
   bind those terms to a proper right-handed frame with explicit units and parent.
3. **Topology checks coverage.** Every required bone, digit, surface or attachment
   maps to a distinct geometric identity. Missing digits produce
   `REFUSED:semantic_geometry_coverage_missing`; a model may not fill them in.
4. **Physics tests meaning.** A held-out kinematic or contact witness checks the sign.
   For a hand, positive digit flexion must advance digit samples toward the declared
   palm half-space, and a palm contact port's outward normal must agree with the palm
   direction. Reversing the palm sign must fail this test.
5. **Rendering explains failures.** The qualified frame generates six orthographic
   axis views plus semantic-axis, landmark, topology and port-normal overlays. These
   views help humans and agents debug the packet; they do not create its semantics.

`tools/monkey_campaign/semantic_frame.py` implements the pure validator. It performs
no filesystem, network, image or model access, so it is deterministic and cheap enough
to run for every membrane and every PR. The corresponding tests include the present
failure mode: a smooth hand paddle without digit coverage is refused rather than sent
to an agent for anatomical guessing.

## Required packet layers

- **Identity:** subject, subject kind, exact source head, frame ID, parent frame and SI
  unit.
- **Frame:** origin and an orthonormal, proper right-handed basis.
- **Semantics:** opposite signed direction pairs: distal/proximal, dorsal/palm and
  lateral/medial.
- **Knowledge claims:** provenance, domain, authority class, statement and artifact
  hash. Construction and validation claims must be disjoint.
- **Landmarks and witnesses:** role-bearing points plus independent direction tests.
- **Coverage:** required semantic elements and injective geometry bindings.
- **Ports:** position, outward normal and semantic direction.
- **Physical witness:** a held-out motion or contact calculation that changes sign if
  the semantic axis is reversed.

Packets pass, fail, or refuse:

- `PASS` means all declared facts and independent witnesses agree.
- `FAIL` means supplied facts contradict geometry or physics.
- `REFUSED` means the evidence is incomplete or circular. Refusal is the expected
  result for an under-specified asset and must not be converted to a visual guess.

## Palm case

The current A04 panel is still useful as a debugging instrument, but it cannot alone
establish a reusable hand frame. A qualified hand packet needs wrist and digit
landmarks, distinct digit coverage, a sidedness source, a palm surface port and a
flexion witness. Once those exist, the palm direction follows deterministically and
propagates through child membranes and connected ports. The operator is asked only
when choosing authored semantics or resolving genuinely conflicting sources.

## Adoption rule

Any task that creates or changes an anatomical, terrain or interaction frame must add
a semantic-frame packet and run this validator before visual acceptance. A downstream
card may consume only a `PASS` packet at the exact source head. Camera manifests then
use that frame to render consistent labeled views at declared angle, distance and
projection. Runtime contact and gameplay tests remain separate gates.
