# Replacement-PC recovery checklist

Keywords: DISASTER RECOVERY, RESTORE, BACKUP, NEW MACHINE, INSTALL, DEPENDENCIES.

Purpose: recover development of the playable monkey after losing the entire host.
This is a recovery checklist, not a claim that a clean-machine rebuild has passed.
The Captain appoints the replacement Lieutenant; start with this document before
starting workers. [MONKEY_RUN.md](MONKEY_RUN.md) remains the campaign entry point.

## What GitHub does and does not restore

| Recovery source | Contents and boundary |
| --- | --- |
| Git repository and remote branches | Only committed, pushed source, instructions, criteria and evidence at the selected revision. An open PR is not on the integration branch. |
| GitHub PR records | Review discussion, candidate heads and merge status. Reconcile these against restored coordination state. |
| Private off-machine backup | SQLite state, mailbox, local receipts, unpublished attempts, private assets and checkpoints. Required to resume rather than reconstruct the fleet. |
| External dependencies | Compilers, SDKs, Python packages, browser binaries, model weights and scientific source assets. Need versions, source locations and hashes. |
| Captain's credential recovery | GitHub account recovery, newly provisioned host access and AI-provider access. Never publish secrets or registry role tokens. |

Loss of the PC also loses any backup stored only on another partition of that PC.
Maintain a versioned off-machine copy and an offline or separately protected copy.
Record the last successful restore drill, backup location, custodian and timestamp
in a private recovery receipt. This document does not establish that such copies exist.

Captain's selection (2026-09-26): use BOTH an external drive, disconnected between
backups, and private cloud storage. Exact drive path, cloud destination, access
configuration and retention remain to be supplied and verified before backup jobs
can be configured. Keep decryption/recovery access separately from this PC.

## Before a failure: preserve these

- [ ] Push each reviewed/recoverable commit to its intended remote branch. Record
  integration SHA, workflow SHA and every still-open PR/head. Preserve local-only
  commits in a private Git bundle with verified objects before branch cleanup.
- [ ] Back up `E:/ChimeraWork/monkey-coordination/`, including
  `agent_slots.sqlite3`, `suggestions.sqlite3` and startup receipts. These are
  private: state can contain coordination tokens and machine-specific evidence.
- [ ] Back up referenced attempt workspaces and evidence across `E:/ChimeraWork/`,
  `E:/Chimera/` and `E:/PythonChimera/`, including ignored `agent_logs/` when needed.
  Inventory actual registry artifact paths; these three directory names alone
  are not a complete manifest. Preserve dirty/untracked work without attributing
  it to an agent until its identity is established.
- [ ] Capture a coherent checkpoint: pause fleet writes, complete SQLite backups
  using the SQLite backup API, then copy referenced files and hash the copies.
  Do not copy a live `.sqlite3` alone and assume its WAL was incorporated. Verify
  each restored database with `PRAGMA integrity_check` and cross-check referenced
  artifact hashes. Resume writers only after the snapshot has been sealed.
- [ ] Preserve asset/source manifests: provenance, license, download URL or private
  backup location, exact revision/hash, units and transformations. Include meshes,
  terrain, trained policies, optimizer/checkpoint state needed to resume training,
  judge/local-model identifiers, quantization and inference settings.
- [ ] Record each actual Python environment separately (`python --version` and
  `python -m pip freeze`), executable path, compiler/SDK/driver versions, Node/npm
  versions and browser revision. Review exports for embedded private URLs or tokens
  before publication. A global package list is not a tested project lockfile.
- [ ] Export agent-harness settings and required MCP/service definitions without
  credentials. Keep secrets in the Captain's private recovery mechanism. Preserve
  SSH alias configuration separately; the fleetdeploy alias is host configuration.
- [ ] Keep a manifest of backup files with raw SHA-256, byte length, source commit,
  timestamp and whether each item is public, private or regenerable. Verify the
  copy from the off-machine destination, not just the source disk.

## Software checklist

Install from the vendors' official distribution channels. Versions below are
observations from the original host on 2026-09-26, not compatibility guarantees.

| Purpose | Requirement / observed state |
| --- | --- |
| Host and shell | Windows 11, PowerShell; restore the intended Central time zone while retaining UTC event timestamps. |
| Source control | Git for Windows; observed 2.55.0.windows.2. GitHub read access plus separately authorized push/PR/merge access. SSH push alone does not provide API merge access. |
| Workflow Python | Observed default Python 3.14.3; workflow uses SQLite from Python's standard library. Training may use a different interpreter: recover its own environment. |
| Native compiler | Visual Studio C++ build tools with an x64 compiler and Windows SDK; engine declares C++17. Exact working toolset must come from build receipts/environment inventory. |
| Build system | CMake minimum 3.20 in engine source; observed CLI 4.2.1. Preserve generator and architecture. |
| Rendering | Vulkan SDK, GPU driver, glslangValidator. Engine CMake currently defaults to `C:/VulkanSDK/1.4.328.1`; explicitly configure the real installed SDK path. Rebuild shaders from source. |
| Web/capture tooling | Observed Node 22.23.1 and npm 10.9.8. Local package.json names Playwright, Playwright MCP, acorn and gaussian-splats-3d; use the reviewed package lock when published. Browser binaries are a separate install. |
| Physics/training | Recover the selected lane's MuJoCo, numerical libraries and GPU framework versions from its environment/receipts. No complete project-wide Python lock was established by this audit. Do not infer CUDA/framework compatibility from the default Python. |
| Local models | Bionic/LM Studio and/or Ollama only for lanes configured to use them; restore exact model files/settings or pinned downloads. Re-establish the resource broker before loading models. |
| Agent execution | Install the chosen harness and its tools, authenticate through the Captain, verify shell, file, delegation and GitHub capabilities. Documentation alone cannot keep a model process running. |

Source evidence: `ChimeraEngine/engine/CMakeLists.txt`, local package manifests,
`tools/science_funnel/requirements.txt` (locally PyYAML 6.0.2), and version probes.
`.gitmodules` declares `tools/gsplat`; recover its pinned submodule revision if the
chosen build uses it. Do not substitute the latest upstream checkout.

## Restore in this order

1. **Recover access and select revisions.** Log in to GitHub independently. Select
   the verified integration commit and the corresponding workflow revision. Inventory
   open PRs; never merge them merely to reconstruct the old filesystem.
2. **Clone into the expected layout.** Existing runtime paths assume
   `E:/PythonChimera`, `E:/ChimeraWork` and sometimes `E:/Chimera`. Recreate that
   layout on the replacement machine, or perform and test an explicit path migration.
   A fresh clone elsewhere is not currently self-configuring. Use ordinary HTTPS
   clone access until the host-specific SSH alias is deliberately installed.
3. **Restore private state into quarantine.** Check backup hashes and SQLite
   integrity before placing state at its runtime path. Do not start startup.py or
   workers against unverified state. The actual entry script is worker_start.py.
4. **Reconcile state as Lieutenant.** Compare PR/head/merge facts with GitHub;
   retain old attempts as evidence. Confirm the old host's writers are stopped,
   then release old coordination claims through the documented exact-holder
   protocol. Do not resume stale role tokens or infer live workers from labels.
5. **Restore source and assets.** Reconstruct isolated worktrees from recorded
   commits, restore unpublished files and check their hashes. Never copy old Git
   worktree administrative paths blindly. Mark absent evidence UNAVAILABLE; a
   lost receipt is not a passing result.
6. **Rebuild environments.** Create separate environments for workflow, training
   and other incompatible tools. Install their reviewed pinned dependencies. With
   a reviewed package-lock present, use `npm ci`; install that Playwright version's
   required browser. Rebuild the engine and shaders in a fresh build directory,
   specifying the actual Vulkan SDK. Do not reuse old CMake caches or executables
   as proof that the replacement toolchain works.
7. **Verify instructions and offline tests.** Run the selected revision's
   instruction inspector and campaign test suite. Preserve published instruction
   hashes and checkout line-ending semantics. A mismatch needs investigation,
   not a replacement checksum. Test against temporary registries first.
8. **Restore runtime capability.** Verify engine launch/shutdown, HTTP service,
   camera-tagged capture and resource ownership. Separately qualify the GPU,
   training/runtime parity and model loading before any throughput claims.
9. **Resume one worker.** Run canonical worker_start.py, confirm assignment,
   isolated workspace, instruction revision and criteria. Exercise handoff,
   independent review and publication; verify that Review frees Development and
   only qualified completion unlocks dependencies. Then increase concurrency.

If coordination backups are lost, reconstruct from committed scope, PRs, reviews
and receipts under Lieutenant supervision. Fresh Registry.initialize() does not
rebuild historical cards, decisions, tokens or the approved campaign. Do not mark
missing work DONE. Record the reconstructed state and unresolved provenance.

## Recovery acceptance and current gaps

A recovery is demonstrated only by a clean-machine or isolated replacement-host
drill with the old host unavailable as a source. Record exact commits, installers,
dependency versions, backup manifest, commands, results and missing artifacts.
Require: source reconstruction; database/artifact integrity; instruction verification;
offline tests; native build; camera-pinned runtime capture; one full worker cycle.
GPU training recovery is a separate gate if no compatible GPU is available.

Audit baseline, 2026-09-26: no full replacement-host drill performed; no verified
off-machine private-state backup established; no complete dependency/asset lock
established. Local package.json/package-lock.json and science_funnel requirements
were absent from the inspected workflow publication tree (8d1505af). Their local
existence does not prove they are on the chosen remote revision. The workflow
publication PR #142 was still open when checked. Track these as recovery gaps,
not as silently completed installation work.

The Captain supplies the private off-machine backup destination. Publish source,
reviewed setup manifests and this checklist; never publish the live registry,
credentials, private assets or an unredacted home-directory configuration dump.
