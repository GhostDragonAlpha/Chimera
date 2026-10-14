# Representation mapping and membrane-connection checks

Lead-authorized bounded implementation, 2026-09-26. This protocol precedes the
new implementation and its test execution. Existing JSON ontology, task criteria,
evidence and runtime qualification remain authoritative and unchanged.

Statement: two structurally compatible components can still disagree about the
meaning of a value crossing their boundary. A source-bound mapping contract and
a numerical connection coupon make selected disagreements executable failures.

Prediction: an explicitly authored millimetre-to-metre point mapping with rotation
and translation passes against independently hand-calculated destination points.
Wrong source bytes, inconsistent declared frame, representation, unit, direction, correspondence,
rotation, translation, unresolved properties or out-of-envelope points cannot
produce a passing numerical receipt. Inputs are unchanged and relocation works.

Falsifiers: any named corruption passes; reviewer accepts producer output as its own oracle;
round-trip agreement is the only oracle; a hash is treated as scientific truth;
a coupon pass changes live task state or claims mechanical/runtime qualification.
The numerical checker can only check declared frame-label consistency. Scientific
frame correctness, oracle independence and approval of the external pin require
upstream review; the checker cannot establish them from the files alone.

Implementation scope: optional stdlib sidecar validator, not an ontology schema
migration. Version 1 executes only a rigid 3D point mapping plus declared m/mm
conversion. It does not map mass, inertia, forces, normals, attachment mechanics,
uncertainty, non-rigid anatomy or trained policies. Other quantities require their
own equations and independent tests; never reuse point translation for vectors.

Primary inspiration: [Genovese et al., BCFtools/liftover](https://pubmed.ncbi.nlm.nih.gov/38261650/)
(reference-aware conversion) and [MoChA workflows](https://github.com/freeseek/mochawdl)
(explicit parallel work and recombination). These Chimera contracts are our
adaptation, not algorithms or game-engine claims from those authors.
