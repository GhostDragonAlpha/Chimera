# Third-party and historical licensing notices

The root LICENSE applies only to material the Chimera copyright holder can
license. Third-party components, submodules, dependencies and assets retain their
own terms, including notices embedded in their source. No notice is removed or
replaced by this transition. More specific valid grants govern their material.

Known locations checked during this transition:

| Material | Existing notice / authority |
| --- | --- |
| `ChimeraEngine/native/viewer3rd/json.hpp` | JSON for Modern C++ 3.11.3; Niels Lohmann; embedded SPDX `MIT` |
| `ChimeraEngine/native/viewer3rd/webgpu.h` | WebGPU-Native developers; embedded SPDX `BSD-3-Clause` |
| `tools/gsplat` | Git submodule of `nerfstudio-project/gsplat`; the pinned checkout's own license applies |
| Research anatomy and sound assets | `Chimera/docs/ASSET_LICENSES.md` records sources and MIT/CC0 notices; verify each actual distributed asset |
| Previously AGPL-released Chimera revisions/material | Existing grants preserved; see `LICENSES/AGPL-3.0-historical.txt` and `docs/LICENSING_TRANSITION.md` |

This is an index of observed notice locations, not a claim that every dependency
has been audited or that every component is redistributable in every package.
Keep the complete notices required by the actual versions being distributed.
The campaign's S01 distribution audit must check the final package and all assets.
