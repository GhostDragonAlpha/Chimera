# Current hierarchy-continuation result

This additive record supersedes the acceptance interpretation of generation 1 (`2a8d356a`) and generation 2 (`0b4e7dd0`) while retaining their original files byte-for-byte as historical attempts. It does not erase their failures or convert their results into evidence for this candidate.

## Candidate identity

Base: `0b4e7dd019be585d30714b32231ac820d84f3ec9`

- `ChimeraEngine/engine_state.py`: `1dffea21d1888dbeb00fa5a8d3f8d2e3dd70326e01aa778d5fd2a0e56e00231a`
- `ChimeraEngine/mcp_server.py` (unchanged identity/control): `3a505601753b21853437cbada39f2301249501fdd7803655d711fb401d89cc59`
- `ChimeraEngine/ONBOARDING.md`: `297f93ef48d05c7608c0586ab8db1c1327677cab673a74611dc5f4941c8fe3af`
- `tools/orient.py`: `8a5fe4219bb34f536639d7546c798a9e460e993f3c66efceab53b8153a9a7b66`
- `tools/test_orient_continuation.py`: `8a5bbe1449dad5526df995008940e471fc4e14023154aece0796a1cf9b57d794`
- `docs/THE_HIERARCHY_CONTINUATION.md`: `d1a5be581c1fd86b5fa1145bc35fbefb2c0acfaa470a7f50918ac0fdbc892062`

## Private candidate test

`python -m unittest tools.test_orient_continuation -v`

Result: 9/9 PASS in 1.068 s. Raw output SHA-256: `02b245d2a20eeb024400ae681239a79e07358171939c17b38acac252251e5e51` (`final_tests.log`).

The private overlay loaded dependencies from the exact PR36 checkout but path- and SHA-bound the candidate Engine, orient, and MCP modules in the test itself. An installed-tree rerun is still required before acceptance. All state mutation in the suite is confined to temporary directories. No controller, live engine, GPU, MCP process, or repository store was changed.

## Installed-tree correction

The required no-override installed command was rerun after byte-exact copy: python -m unittest tools.test_orient_continuation -v returned exit 0 with 9/9 PASS. Raw output is gen3_installed_tests.log; its SHA-256 is 765ce7095a8442974cfe7d91739072cd718a7e4764fcd4fa4596577a4b94c99e. The environment variables CHIMERA_FIXTURE_REPO and CHIMERA_FIXTURE_CANDIDATE were unset. Final source hashes match the candidate identities above; mcp_server remains unchanged. The private inal_tests.log is retained separately and is not substituted for this installed-tree result.
