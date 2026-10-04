"""test_pair.py -- the campaign-runner entry for the assembled pair
(pair.hand_ground.v1, packet PKT-G3-ASSEMBLY-HANDGROUND).

Runs the two-leg battery in pair_assembly.main(): the co-instantiated
runtime scene through the GENERATED wiring (T.ASMB_runtime_scene) and the
physics pair run (the pairpath fixture clauses) -- all fatal windows per
the sealed PREREGISTRATION.md. Writes CHIMERA_OUTPUT_DIR/pair_result.json.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import pair_assembly  # noqa: E402

if __name__ == '__main__':
    pair_assembly.main()
