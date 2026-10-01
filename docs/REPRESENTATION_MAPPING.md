# Representation mappings and connection verification

Keywords: MAPPING CONTRACT, SOURCE BINDING, ADAPTER, PORT SEAM, VALIDITY ENVELOPE.
This is an additive engineering procedure for new or revised conversions. It does
not change the sealed campaign list, active card criteria, completed evidence or
installed instruction bundle. The Lieutenant authorizes criterion changes through
the existing workflow; a worker never edits a pin to pass a test.

## Contract at the boundary

Before converting a value between representations, name the source and destination
membrane/port IDs, representation revisions, raw artifact hashes, quantity, units,
coordinate frames and handedness, and direction/sign convention. A name match is
not correspondence evidence. Keep mappings as explicit adapters, separate from
the source definition. Record the equations, parameter sources, implementation
revision, applicability limits and the evidence that establishes correspondence.

For every affected property explicitly record **preserved**, **recomputed** or
**unresolved**, with supporting evidence. Changing length units or geometry does
not silently validate mass, density, inertia or tissue ownership. A conversion of
positions does not supply the conversion laws for normals, forces or tensors.
Connections transfer values/references; they do not create a second matter owner.

Freeze tolerances and input identities before evaluation. Hashes identify bytes;
they neither authenticate a worker nor establish that an assumption is true.
A destination produced by the same faulty algorithm is not an independent oracle.
Round trips can hide paired errors and are supplementary checks only.

## Executable first slice

[mapping_contract.py](../tools/membrane_ontology/mapping_contract.py) checks the
optional `chimera.point_mapping.v1` sidecar. It validates the pinned JSON ontology
using the existing validator, resolves its explicit endpoints, and reads raw-hash
bound source/destination sample files. The only supported protocol is
`point-position-v1`, with `m` or `mm` units. Existing ports are not retagged or
assumed to satisfy that protocol. The synthetic example authors those ports solely
for the coupon. Future real bindings require an authored adapter and review.

The equation is `p_destination = R * (scale * p_source) + t`, with translation
in destination units. Scale must equal the declared unit conversion. R must be
proper and orthonormal within a fixed 1e-12 representation check, without repair.
That matrix check is not a scientific acceptance tolerance. The authored sample
error threshold is an absolute per-coordinate tolerance in destination units.
The source-coordinate validity box is inclusive; no guarantee is made between
samples or outside that box. Point IDs must correspond exactly, once each.
Calculations use finite binary64 values. Integers that cannot be converted exactly
are refused rather than rounded into the permitted domain. This is a floating-point
coupon, not an exact-real or interval-arithmetic proof.

The caller supplies a previously approved **raw-byte contract hash**. That pin
covers the equation, input pins and error threshold. Rehashing an altered contract
in the same command proves nothing about approval. The example pin is a published
test fixture, not a secret or access key.

From the repository root (Python standard library only):

```powershell
python -B tools/membrane_ontology/mapping_contract.py tools/membrane_ontology/examples/point_mapping/mapping.json --expected-contract-sha256 EXAMPLE_PIN
python -B -m unittest discover -s tools/membrane_ontology -p test_mapping_contract.py -v
```

Replace EXAMPLE_PIN with the reviewed value in
[APPROVED_RAW_SHA256.txt](../tools/membrane_ontology/examples/point_mapping/APPROVED_RAW_SHA256.txt).
The example has four hand-calculated noncoplanar points, millimetres to metres,
a +90 degree Z rotation and a (1,2,3) metre translation. Its committed expected
receipt supports comparison after relocation. JSON is emitted as UTF-8/LF.

Results: PASS (exit 0) means only that declared samples agree within the pinned
tolerance. FAIL means numerical disagreement; UNQUALIFIED means unresolved
properties; REFUSED means malformed, unsupported, out-of-envelope or mismatched
input. All three return exit 2. No result changes task, ontology or runtime state.
The numerical coupon cannot establish scientific independence of its oracle;
that remains an explicit reviewer obligation. No anatomical or game completion
is claimed by the bundled synthetic example.

## Connection acceptance in the existing workflow

Use the existing owning card and connection membrane; do not create a second
backlog. During a newly authorized integration, the producer and consumer each
have their own checks, followed by a connection check covering their disagreement
cases. Pin both revisions and the adapter. Changing a bound input requires renewed
review of dependent evidence; it does not erase historical receipts.

1. Preregister the quantity, correspondence, domain, error budget and independent
   expected outcomes, including values near the boundary of the permitted domain.
2. Run source-to-destination cases. Introduce a reversed axis, unit error, stale
   artifact, missing endpoint and duplicate correspondence to verify rejection.
3. Where relevant, add mechanical checks: mass/COM/full-inertia conservation,
   joint length and moment-arm curves, contact gap/Jacobian agreement, or signed
   power across force/velocity and torque/angular-velocity ports. These require
   their own physical laws; the point validator does not execute them.
4. Keep implementation verification, agreement with a source model, and independent
   biological validation as separate claims. Another agent repeating the same
   assumptions supplies review independence, not a new physical oracle.
5. For a visual or motion claim, retain the existing profile: source-bound frames,
   labeled ports/frame axes, camera position/orientation/distance, projection,
   clipping, diagnostic and clean views, and independently observed runtime state.
   Numerical point agreement never substitutes for native motion evidence.

Each job retains the existing resource broker: declare CPU, RAM, output growth,
GPU class/VRAM and whether interruption is allowed. Estimate from measured inputs
and compare estimates to observed peak usage. Ten task slots do not confer ten
GPU grants. This document adds no scheduler and starts no training.

## Scientific precedents and next bounded experiment

[Genovese et al.'s liftover](https://pubmed.ncbi.nlm.nih.gov/38261650/)
motivates explicit representation conversion; its genomic algorithms are not
being applied to geometry. [MyoConverter](https://github.com/MyoHub/myoconverter)
provides a closer biomechanical precedent: structural conversion followed by
muscle kinematic and kinetic matching. [Hicks et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC4321112/)
distinguish verification, validation and sensitivity analysis in musculoskeletal
models. [Cooling and colleagues](https://pmc.ncbi.nlm.nih.gov/articles/PMC5134412/)
describe modular physiological modelling, including explicit unit conversion.
These are design precedents, not additional installed dependencies.

The next proposed experiment is one elbow and two antagonist muscles: source-bound
pose sweep, held-out poses not used for fitting, muscle lengths and moment arms,
an independently computed force/lever-arm torque, and fixed-camera overlays.
It must wait for actual body/attachment mappings and source laws; unresolved
owners cannot be filled by symmetry or names. The current work does not authorize
new anatomy, training, a whole-body conversion, or a policy change to existing cards.

A later energy-port coupon may borrow hierarchical bond-graph practice from
[Gawthrop, Cursons and Crampin](https://arxiv.org/abs/1503.01814): account for
actuator input, stored energy and dissipation, then examine residual versus
timestep. Conservation without accounting for active inputs is not a valid test.
Replay bundles should include model/data provenance, parameters, commands, software
versions and evidence, following the reconstructability principle illustrated by
[COMBINE archives](https://pubmed.ncbi.nlm.nih.gov/25494900/). No new format stack
is needed for the first coupon.
