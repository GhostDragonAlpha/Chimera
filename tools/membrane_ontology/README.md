# Membrane ontology inspector

Read [the ontology contract](../../docs/MEMBRANE_ONTOLOGY.md). The operator's model
is recursive containment plus explicit port connections. This tool checks and
displays that structure without executing physics or changing campaign state.

```powershell
python -B tools/membrane_ontology/inspect_ontology.py
python -B tools/membrane_ontology/serve.py
```

Open `http://127.0.0.1:8029/`. Select a membrane, open its children, inspect its
ports and follow a connection to its endpoints. Refresh reads the current
definition and source files; there is no browser polling. The server is bound to
loopback and exits after 30 minutes without a request. Stop the command with
Ctrl+C. It starts no engine, GPU work, model or fleet workers. To serve a separate
source checkout, use `--root E:/PythonChimera`. `--port 0` chooses a free port.

The **Work & verification** tab projects the approved 83-task plan onto each
membrane: primary/related tasks, dependencies, zero-based logical layers, original
acceptance clauses and integration checkpoints. Camera angle/orientation,
distance, projection/FOV, clipping, resolution and motion requirements accompany
the diagnostic/clean views. These are planned requirements, not earned passes.
The seven conditional tasks remain inactive. See
[ONTOLOGY_WORK_PLAN.md](../../docs/ONTOLOGY_WORK_PLAN.md).

Agents consume the same JSON through the CLI or `GET /api/ontology`. CLI
`--definition <file>` selects an explicit definition; `--output <file>` saves a
snapshot. Exit 0 means structural inspection succeeded; exit 2 is a named
refusal. HTTP 422 carries the same refusal. Missing referenced files are visible
source warnings and do not silently become accepted evidence. Physics and
validation labels are authored claims, not independent measurements.

`--catalog <file>` selects the catalog paired with the definition. A mismatched
definition hash, invalid task binding, missing camera requirement or cyclic
checkpoint graph refuses the snapshot. `--root` changes source inspection only;
the definition/catalog default to this tool's checkout. No source plan is guessed
from a different checkout and no mutable acceptance store is read or written.

`ontology.json` is the single authored composition definition. `model.py` is its
executable v1 structural contract: exact top-level/node/port keys, one acyclic
containment root, stable IDs, named endpoints, matching protocol/unit labels,
descendant-only port exposure and unique explicit matter owners. A `reference`
matter claim does not count as ownership. It does not reconcile that ledger to
the material compiler; that binding remains a separate qualified input.

The definition's raw-file SHA-256 identifies exact bytes. `snapshot_sha256` is
SHA-256 of the complete snapshot excluding that field, serialized as sorted-key
compact UTF-8 JSON, Unicode unescaped, array order preserved, nonfinite numbers
refused. Source hashes are raw-byte hashes. There is no timestamp or absolute
checkout path in the snapshot. Hashes detect drift; no signature or author
authentication is claimed. The current policy bundle pins the definition and
its architectural document for workers to read.

Run structural/source/server checks:

```powershell
python -B tools/membrane_ontology/test_model.py
```

The browser inspector is a working view of the authored composition. It is not
a 3D anatomy viewer, runtime compiler, MuJoCo importer or gameplay acceptance
instrument. Those bindings must be added explicitly; the current gaps name them.
The existing engine story/terms retain their historical teddy lineage. This
inspector does not replace that runtime's store or mark its proofs current.
