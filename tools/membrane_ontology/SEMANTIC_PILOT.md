# Read-only semantic validation pilot

Statement: a generated RDF projection can expose selected membrane contracts to
standard SHACL tools without changing the authored ontology or qualification state.
Prediction: the current ontology conforms; deletion of a required parent, a
containment cycle, missing endpoint, changed endpoint unit and duplicate matter
owner each produce a nonconforming report. Falsifier: any mutation passes, the
export mutates input, or a graph verdict is treated as physics/runtime readiness.
This protocol was written before the pilot test execution.

`ontology.json` remains the sole authored composition definition. `semantic_export.py`
first calls the existing validator, then writes deterministic N-Triples to stdout.
No registry, source, evidence or task status is modified. IDs use distinct node,
port and matter namespaces. Type, containment, port connection and matter ownership
are separate predicates. The snapshot records the existing canonical JSON digest;
this is not an RDF canonicalization hash or authentication credential.

The shapes independently reject selected corruptions to the exported graph.
They are deliberately incomplete: root uniqueness/reachability, delegation ancestry,
full source contracts and all numerical/runtime/visual gates remain with existing
validators. Missing owners on reference-only matter remain permitted. Exact protocol
and unit strings are compared; no unit conversion, frame inference or physics is
invented. No OWL inference is enabled, and no qualification is inferred from types.

Install the adjacent pinned pilot requirements in an isolated virtual environment.
From this directory run `python -B -m unittest test_semantic_export`.
Export with `python -B semantic_export.py ontology.json > ontology.nt` using a shell
that preserves UTF-8 output. Validate using pySHACL with `semantic_shapes.ttl` and
inference disabled. This is optional development tooling, not a runtime dependency.

Standards: https://www.w3.org/TR/shacl/ and https://www.w3.org/TR/owl-primer/.
Borrowed design principles: explicit contexts/provenance (Cyc microtheories), and
separation of vocabulary from constraints (DOGMA). Neither platform is installed.
KIF/Common Logic and OWL reasoning are deferred until a concrete interoperability
or inference requirement demonstrates their value. Do not create another authored
ontology or substitute this pilot for the approved membrane/port authority.

## Verification receipt — 2026-09-26

Eight tests passed in the isolated Windows/Python 3.14.3 environment specified by
requirements-semantic.txt: positive real ontology, deterministic export and input
preservation; five independently mutated RDF graphs rejected; malformed JSON still
refused by the original validator before export. No live state was used or changed.
The first CLI smoke test failed under Windows cp1252 on a Unicode label. The CLI
now explicitly emits UTF-8/LF; a subprocess regression forces the old encoding
and verifies byte-exact UTF-8 output. This failure is retained here as evidence.
RDFLib/pyparsing emitted upstream deprecation warnings; no test failed.

These checks overlap existing JSON validation. This experiment demonstrates a
standard interchange/validation path, not newly discovered ontology defects or
an expanded qualification guarantee. Runtime evidence, frame transforms, numerical
physics and task scheduling are intentionally outside the pilot. No OWL reasoner,
Cyc installation or second authored source is justified by these results.
