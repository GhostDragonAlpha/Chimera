# Scientific data funnels

Run from the project root: `python -m tools.science_funnel --help`.
This is offline intake. The native engine remains the physical runtime.

## Contract stated before implementation

**Statement:** source-specific deterministic adapters can preserve scientific
assertions in one graph without mistaking extracted facts for verified game laws.
**Prediction:** pinned inputs reproduce identical bundles; incompatible units,
ambiguous identity, absent frames, stale graph writes and altered captures fail
their named controls. Parallel importers cannot overwrite the graph.
**Falsifier:** an altered source is accepted under its old pin; a condition or unit
mismatch binds silently; a failed import changes the graph; or import promotes a
physical claim. Test entry: `python -m unittest discover -s tools/science_funnel/tests -v`.

## The route

`database -> pinned raw bytes -> database adapter -> typed assertions -> graph proposal`

`selected assertions -> explicit scientific reduction -> candidate parameter -> independent runtime test`

Each source manifest pins a database release, artifact bytes, license, adapter,
field mappings and known conditions. Each database gets its own manifest; adapters
are reusable by format. No AI extraction is required for the implemented routes.
Raw bytes are stored once per intake bundle, addressed by SHA-256, with a complete
graph index. The graph is the authority; large data blobs are its backing storage.
Unprojected source fields remain recoverable from the original bytes.

The database-family catalog and remaining connector work are graph records:

```powershell
python -m tools.science_funnel catalog
```

## Existing pinned sources

`prepare-pinned` packages the existing Uberon, RO, QUDT and OpenSim cache using the
**original** recorded pins. It refuses drift and makes no network requests.
Supply the actual cache directory, not a worktree with some similarly named files.

```powershell
python -m tools.science_funnel prepare-pinned --cache PATH_TO_PINNED_CACHE --output .tmp/intake-inputs
python -m tools.science_funnel ingest --manifest .tmp/intake-inputs/uberon.appendicular-minimal/manifest.json --manifest .tmp/intake-inputs/ro.base/manifest.json --output .tmp/intake-bundles
python -m tools.science_funnel verify .tmp/intake-bundles/BUNDLE_HASH
python -m tools.science_funnel propose .tmp/intake-bundles/BUNDLE_HASH --graph SNAPSHOT.json --output .tmp/intake-proposal.json
```

The proposal contains `operation: graph_apply` and `payload`, including the exact
expected graph hash, objects, and append-only provenance edges. The existing
authenticated controller client submits that payload with its current lead epoch.
No credentials or graph ownership are created by this tool. A stale proposal is
regenerated against a fresh snapshot. Separate import workers can run concurrently;
only controller transactions admit their outputs. Source snapshots never disappear
when a later database version is imported. Admitted science records are immutable.

For an undeployed controller, proposals are reviewable files; generating one is
not a claim of admission. The tests exercise admission through a real temporary
controller. No deployed project controller or live engine is touched.

## A new database's manifest

```json
{
  "schema_version": "1.0.0",
  "adapter": "measurements_csv",
  "source": {"id": "dataset.example", "release": "r1", "license": "unknown", "url": "https://example.org/data"},
  "artifacts": [{"id": "table", "path": "table.csv", "sha256": "EXPECTED_64_HEX_DIGIT_HASH"}],
  "columns": {"id": "row_id", "subject": "specimen", "quantity": "property", "value": "reading", "unit": "units"},
  "quantity_map": {"Elastic modulus": "young_modulus"},
  "conditions": {"species": "unknown", "temperature": "unknown"},
  "condition_columns": {"loading": "test_protocol"}
}
```

The adapter never silently creates or refreshes expected hashes. Prepare a manifest
from the published release and recorded download. A source may say `unknown` for
license or conditions; that allows archiving, never automatic deployment approval.

### Implemented format adapters

| Adapter | Supported input and limits |
|---|---|
| `uberon_obo` | Existing OBO subset parser: concepts, typedefs, names, parents, relationships. Full axioms remain raw. |
| `ro_owl` | Existing selected RO relation definitions in RDF/XML; no reasoner or full ontology import. |
| `qudt_ttl` | Existing selected unit/quantity-kind projection. Imported definitions do not modify executable conversions. |
| `opensim_xml` | Existing partial model parser and Thelen muscle parameters; no model execution or automatic species scaling. |
| `measurements_csv` | Long-format scalar measurements; columns or constants for id, subject, quantity, value, unit and optional absolute uncertainty. Explicit quantity/unit aliases only. |
| `series_csv` | Curves/time series grouped by id; additionally x, x_quantity, x_unit. Strictly increasing x, unchanged subject/conditions. Preserves irregular sample times; no resampling or interpolation. |
| `geometry_json` | List of id, two 3D anchors, length_unit, frame {id, handedness: right, axis_convention}, optional shape specification. Builds a local orthonormal frame and length. No mesh generation or engine-frame registration. |
| `model_json` | List of id, equations, ports [{name, quantity, unit}], assumptions, validity_domain. Declarative content only; compilation remains a separate task. |

CSV is strict UTF-8 with a unique header. A bad scalar row is quarantined; an invalid
curve group is withheld as a unit. Duplicate IDs within a source version withhold
all contenders. Same-named concepts from different sources remain distinct. Empty
captures, unknown units and nonfinite numbers fail. `ingest` exits 2 on any quarantine
or source failure. A partial graph proposal requires explicit `--allow-partial`.
The quarantine and original bytes stay attached to the source record either way.

Four pinned synthetic examples are included under `examples/` (materials, response,
geometry and a declared model). Run `ingest --manifest
tools/science_funnel/examples/materials.manifest.json --output .tmp/intake-bundles`
to try one. Their numbers are test fixtures, not biological measurements.

The SI converter is a small reviewed table, including affine temperature conversion
and absolute uncertainty scaling. It refuses unsupported quantities and units.
Its dimensions use [mass, length, time, current, temperature, amount, luminous
intensity]. Equal dimensions do not imply equal meaning: pressure is not Young's
modulus and a torque is not an energy parameter. Tensor rotation, correlated
uncertainties, complex units, missing-data interpolation and multidimensional
property surfaces are explicitly unimplemented.

### The reduction bridge

Three reductions are implemented with derivations and named assumptions:

* Axial stiffness: stress = E strain, F/A = E deltaL/L, hence k = EA/L.
* Hydraulic compliance: kappa = -(1/V)dV/dP, hence C = kappa V0 about the rest state.
* Propagation delay: dt = ds/v(s), hence delay = L/v for constant propagation speed.

`reduce --bundle PATH --request REQUEST.json --output RESULT.json` selects immutable
record IDs. Add `--graph SNAPSHOT.json` to produce a provenance-linked graph proposal;
inputs and target must already exist in that graph. Inputs are `{symbol: {record:
ID, field: value_si}}`; a geometry record may supply `field: length_m` to a length
port. Supply `law`, `target_id`, `context`, written justifications keyed by each law's
`assumptions`, and `validation` {observable, falsifier, acceptance_rule}.

A known context mismatch refuses calculation. Missing context becomes a named
blocker. All results remain `derived_candidate`, with runtime validation and
uncertainty propagation outstanding. A two-anchor length is a straight segment;
using it for a curved nerve or wrapping tendon requires an explicit path model.
The deterministic roll convention is not an anatomical measurement. No arbitrary
source equations, instructions, Python, XML hooks or shape scripts are executed.

## Verification and limits

Bundles are immutable directories named by receipt hash. `verify` checks original
bytes, input pins, producer source hashes, record counts and exact adapter replay.
Matching a self-authored hash alone is not proof of source authenticity or physics.
The independent verifier must pin this code and the expected source releases.
Implementation changes require re-ingestion into a new bundle; old captures remain.

The current size ceilings are 64 MiB per artifact and 256 MiB per bundle (resource
limits, not physical constants). This is a bounded batch implementation. Streaming
large atlases, authenticated downloads, source-specific remote APIs, global identity
resolution, species adaptation, tensor constitutive fitting, native rule compilation
and rendering are future graph tasks. Broad database portals are catalog entries,
not claims that every dataset behind them has an operational connector.

Reproduce the whole qualification with `python -m tools.science_funnel.qualify
--cache PATH_TO_PINNED_CACHE --output NEW_SCRATCH_DIRECTORY`. It runs regressions,
admits source assertions through an isolated instance of the real controller, and
checks the real Graphify consumer. It also connects synthetic modulus and area
measurements to a two-point shape and derives the independently checkable 100 N/m
bar stiffness. The graph still labels that result a candidate. Use a direct Python
interpreter for fleet process-identity tests; `--consumer-python` may point to the
project virtual environment with Graphify dependencies. `--targeted` replaces the
whole fleet regression with its graph-workflow suite when broader unaffected checks
already passed; reports name exactly which suites ran.
