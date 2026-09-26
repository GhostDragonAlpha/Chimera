# System layout and development setup

Keywords: SETUP, DIRECTORY STRUCTURE, NEW PC, INSTALL, CLEAN COPY.

Start here to understand what to install and where it belongs. Follow
[disaster recovery](DISASTER_RECOVERY.md) to restore a lost campaign, and
[workflow index](WORKFLOW_INDEX.md) for agent procedures. The online repository
is the public manual; the external drive is an additional recovery copy.

## Directory structure on the operator's Windows host

```text
E:/PythonChimera/                 canonical source checkout
  AGENTS.md                      campaign entry pointer and repository rules
  docs/MONKEY_RUN.md              installed campaign directive
  docs/SYSTEM_SETUP.md            this setup guide
  tools/monkey_campaign/          assignment, review, merge and recovery tooling
  tools/membrane_ontology/        ontology tooling
  ChimeraEngine/engine/           native C++ renderer/runtime and shaders
  .venv-workflow/                 proposed isolated workflow Python environment
E:/ChimeraWork/                   fleet work area (not source authority)
  monkey-coordination/           private registry, mailbox and startup receipts
  ...                            assigned worktrees and attempt evidence
E:/Chimera/                       Lieutenant review/integration workspaces
F:/ChimeraRecovery/               Captain-selected external recovery root
  kits/<revision>/               immutable public setup kits with checksums
  private-snapshots/              reserved for separately verified private backups
```

The virtual environment and F: layout are setup conventions, not a claim that
all directories or backups already exist. Existing F:/PythonChimera copies are
not automatically authoritative. Do not delete, merge or overwrite them to make
this layout. No running agent should work directly in the recovery copy.

Absolute E: paths currently appear in tools, instructions and receipts. Recreating
this layout is the least invasive recovery. A different drive requires an explicit
path migration with provenance preserved; moving the clone alone is insufficient.

## Installation sequence

1. Install Git for Windows, a supported Python interpreter for the selected
   workflow revision, Visual Studio C++ x64 build tools with Windows SDK, CMake,
   and Vulkan SDK/driver. See the observed versions and optional training/browser
   software in [the software checklist](DISASTER_RECOVERY.md#software-checklist).
2. Clone source into an empty destination. Do not run this over an existing tree:

   ```powershell
   git clone https://github.com/GhostDragonAlpha/Chimera.git E:/PythonChimera
   git -C E:/PythonChimera fetch origin
   ```

   Check out the Captain/Lieutenant-selected verified commit using `git checkout
   --detach COMMIT_SHA` inside that new clone. Replace COMMIT_SHA with the actual
   recorded revision. Default branch HEAD and an unreviewed PR are not substitutes.
   Retrieve required pinned submodules with `git submodule update --init --recursive`
   only after checking the selected revision's .gitmodules.
3. Create a workflow environment and run read-only instruction verification:

   ```powershell
   python -m venv E:/PythonChimera/.venv-workflow
   E:/PythonChimera/.venv-workflow/Scripts/python.exe -B E:/PythonChimera/tools/monkey_campaign/instruction_state.py --root E:/PythonChimera
   ```

   Do not regenerate hashes to silence a failure. The repo contains multiple
   historical workflows; the selected instruction bundle must exist and validate.
4. In the source root run workflow tests before restoring active coordination:

   ```powershell
   ./.venv-workflow/Scripts/python.exe -B -m unittest discover -s tools/monkey_campaign -p "test_*.py"
   ```

   Record failures, missing optional tools and skips. Tests do not establish that
   private state or gameplay assets have been restored.
5. From the Visual Studio x64 developer shell, configure a fresh native build:

   ```powershell
   cmake -S E:/PythonChimera/ChimeraEngine/engine -B E:/PythonChimera/build-recovery -DVULKAN_SDK=C:/VulkanSDK/1.4.328.1
   cmake --build E:/PythonChimera/build-recovery --config Release --parallel 2
   ```

   Substitute the actual installed SDK path, record CMake's selected generator
   and compiler, and require glslangValidator so shaders rebuild. These are source-
   derived example commands, not a completed clean-machine build receipt. Use the
   selected native lane's launch and runtime tests; starting an exe is not parity proof.
6. Restore other environments only when needed. Training needs its exact numerical
   stack, policy assets and device qualification. Browser automation needs the
   reviewed Node lock and matching browser binaries. Local model services need
   model identifiers and resource-broker configuration. Do not install arbitrary
   latest packages to make an import disappear.
7. Restore/reconcile private state using the recovery checklist. Configure new
   host credentials independently; never copy a different harness's credentials.
   Only then run canonical worker_start.py and test one assignment-to-review cycle.

## Clean-copy selection rules

A clean source copy consists of Git-tracked files at an explicitly selected
commit, pinned submodule content when needed, and a separate manifest of required
non-Git inputs. It is not a copy of the entire working drive.

Exclude regenerable build directories, Python caches, node_modules, browser
profiles, downloaded model caches and duplicate working-tree copies from the public
setup kit. Do not discard a unique asset or unpublished change merely because it is
ignored: inventory it for the private snapshot first. Runtime databases, credentials
and provider configurations never belong in the public kit.

The initial F: kit contains selected committed instructions and workflow source,
plus revision/hash manifests. It is a navigation/recovery seed, not the complete
engine source, private state, model assets, installed environment or Git history.
The online repo supplies the full source once the required revisions are published.
Keep the kit's classification explicit so a small clean folder is not mistaken for
a complete backup. The private snapshot and cloud destination are separate work.

## Remaining reproducibility work

- Establish reviewed dependency locks for each executable environment.
- Inventory required non-Git assets, download provenance and private source copies.
- Verify an off-machine private snapshot and its cloud counterpart.
- Perform the clean-host build and end-to-end workflow restore drill.
- Resolve/merge the workflow publication PRs so setup instructions are reachable
  from the integration branch, not only from open PR branches.

Do not label the project fully reproducible until these checks have receipts.
