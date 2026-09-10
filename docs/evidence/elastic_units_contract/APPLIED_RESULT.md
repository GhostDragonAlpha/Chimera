# Applied units contract result

The earlier `RESULT.md`, `evaluator-final.json`, and `evaluator-v2.json` are
historical candidate records; their old CLI wording is not the current
interface. The applied source/test blobs are:

```text
units_contract.py       a823d2b1397165c18f2e5bb958d7e4af136f6a05
test_units_contract.py  8ffdadd6751ef0bb6d097bbee66ff8331e337efc
```

Validation commands and outcomes:

```text
CHIMERA_UNITS_CANDIDATE unset
python -m unittest tools.elastic_foundation.test_units_contract -v  -> 12/12 PASS
python -m tools.elastic_foundation.run_falsify --suffix unitscontract20260910 -> 19 checks, 0 failed
python -m tools.elastic_foundation.verify_fixtures --version <temporary copy> -> all_ok true
git diff --check -> clean
```

The battery raw output is preserved under
`newvalidation/run_20260910T192929Z_unitscontract20260910/`. The frozen
fixture `trisingle_stretch.npz` remains byte-identical, SHA-256
`2cb83077485447909e22e4322152bdfd8baa835f43dea973604a111024035ded`.

The applied evaluator retains physical thickness, explicit 2-D equivalence,
full force/energy/volume outputs, structured provenance, and named refusal
paths. Historical compatibility remains separately labelled; no GPU or engine
claim follows.

Final evidence correction: `reproduce_final.py` requires a new `--output`
path, refuses overwrite before launching children, uses `sys.executable`,
removes `CHIMERA_UNITS_CANDIDATE`, propagates either child failure, and its
self-test rejects forced test/verifier failures. Outputs are
`reproduce-final-20260910.json` and `reproduce-correction-20260910.json`.
