# Mapping coupon verification — 2026-09-26

Base: master 8be966ee8b384ec77006ce5871040b4684f7c548. Isolated branch
codex/membrane-mapping-contracts; no active worker checkout or instruction bundle
modified. MAPPING_PROTOCOL.md was written before implementation/test execution.

Initial 15 mapping tests passed. Independent subagent review then found lossy
integer conversion: 9007199254740993 becomes 9007199254740992 under float(),
allowing a one-unit difference and envelope breach to disappear. A dedicated
regression was added first and FAILED with `ValueError not raised` on the original
code. The validator now refuses non-exact integer conversions (`lossy_integer`).
The prediction wording was also narrowed: declared frame-label agreement is
machine-checkable, while real correspondence and oracle independence need review.

Final combined check, Python 3.14.3 in the existing isolated semantic-pilot venv:

```
python -B -m unittest discover -s tools/membrane_ontology -p test_*.py -v
Ran 24 tests ... OK
```

16 mapping tests plus 8 existing semantic-export tests passed. The semantic stack
emits existing pyparsing deprecation warnings; no failures or skips. The mapping
checker itself uses only the standard library. The published example CLI receipt
matches expected_receipt.json with exactly zero maximum coordinate error. Tests
cover relocation/determinism/input preservation, externally pinned thresholds,
raw artifact drift, units/frames/representations, mapping direction, proper
rotation, endpoint/correspondence errors, validity bounds, unresolved properties,
unsupported properties, path escape and duplicate JSON keys.

The coupon uses independent hand-calculated expected coordinates; it exercises
synthetic interfaces only. No existing membrane, anatomy, live task, training run
or gameplay feature is newly qualified. No GPU or engine is started.

Bootstrap defect observed before work: README's documented
`python -B -m tools.creature_graph.project_spec --check` and `--show` commands fail
on this master with ModuleNotFoundError (`tools.creature_graph` absent). This
explicitly authorized isolated change proceeded without claiming controller
admission. Repairing that older graph/bootstrap mismatch is separate work.
