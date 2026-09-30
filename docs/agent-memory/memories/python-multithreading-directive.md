---
name: python-multithreading-directive
description: Alan's 2026-09-14 directive — single-threaded Python is a named
  defect; long Python programs must vectorize or fan out (multiprocessing/
  asyncio); 2026-09-18 lane-worker timeout supplement; operator hardware
  revealed (24 physical cores + RTX 4090) and the compute harness dispatched;
  2026-09-21 hardware sufficiency verdict (YES, E: disk the binding constraint,
  sparse-clone + merge-prune disk policy)
metadata:
  node_type: memory
  type: feedback
  originSessionId: sess_141e362c-a25b-452d-bd03-88fb5f876ce6
---

Alan (2026-09-14), watching a subagent's Python program run single-threaded:
"If we have to run Python programs single threaded we're never going to be able
to finish this video game. We need a multi threaded situation."

**Why:** the fleet's harnesses (bench, gait verify, walker, reference models,
batteries) and the serving layer (shell 8206, website 8210) are Python; serial
execution of independent work wastes the 128 GB / many-core host and stretches
every verification cycle. Reinforced 2026-09-18 when Buffy threads 3-4 hit
command timeouts from large single-threaded operations (batch_qualify on 35k+
objects, full unittest discovery ~250 tests, multi-GB CSV parsing).

**How to apply:** every lane brief for Python work carries the standing rule:
independent work must not be serialized — vectorize with numpy (BLAS releases
the GIL), fan out scenarios with multiprocessing, overlap I/O with asyncio or
threads; a long single-threaded loop in a delivered tool is a defect to name
and fix. CPU-bound pure-Python loops get multiprocessing, not threading (GIL);
I/O-bound polling gets asyncio/threads. C++ engine remains the compute core;
Python orchestrates concurrently.

**Lane-worker timeout supplement (2026-09-18, issued to Buffy 3+4 as a paste-ready directive):**
- **ProcessPoolExecutor** for CPU-bound work (parsing, transforming, hashing) — see `batch/ingest.py::admit_connectors` for the proven pattern; 4-8 workers on this 128 GB host; chunk 50-500 items.
- **ThreadPoolExecutor** for I/O-bound work (downloads, shard loading) — see `build_graph.py` parallel shard loading and `batch/reprove.py` _blob_index.
- **numpy** for array-heavy work (the venv has numpy 2.2.6) — a loop over 10k rows building Python lists is a defect; np.array or np.loadtxt is the fix.
- **NEVER increase command timeouts — chunk the work instead.** Long ops get backgrounded from .ps1 via `Start-Process -FilePath $py -ArgumentList "-B","-m","<module>","<args>" -RedirectStandardOutput $log -NoNewWindow -PassThru`, then poll the log via Get-Content in a bounded loop (60s intervals, max 15 min).
- **Staged test qualification:** run the lane's own test module first (`python -B -m unittest tools.science_funnel.tests.test_<module> -v`), then the full suite as a final gate only. The full discovery suite takes 5-15+ min at 250+ tests and grows.
- **Split batch applies if timeouts hit:** `--admit <connector_1> --apply` then `--admit <connector_2> --apply` sequentially — the pipeline is idempotent, multiple partial applies ≡ one large apply.
- **CSV at scale:** csv.DictReader in a single pass to select derived columns, NOT pandas (not a dependency). If parse >60s: split by row ranges across a ProcessPool, merge subsets.
- **sha256 of large files:** hash in 1 MB chunks (pattern in `reference_data/fetch_cache.py`), never read whole file into memory at once.
- **CreatureGraph.load() takes 10-30s on 35k+ objects:** do it ONCE per script invocation, never in a loop. Cache in a module-level variable.
- **build_graph.py takes 30-60s:** run in background, poll output for "saved".
- **THE DISCIPLINE:** every long operation gets (a) parallelized internals, (b) chunked into bounded pieces, or (c) backgrounded with a polled log. Never a single blocking call that exceeds the command timeout.

Related: [[alan-operator-preferences]], [[astra-consultation-channel]], [[parallel-lanes-2026-09-17]].

**2026-09-18 compute harness DELIVERED (13× speedup measured):**
- **Operator hardware confirmed: 24 physical cores + NVIDIA RTX 4090 (16,384 CUDA cores, 24 GB VRAM); PyTorch 2.5.1+cu124 working.**
- `tools/parallel_test.ps1`: 23 funnel test modules as independent Python processes, up to 12 concurrent — **3879s sequential → 297s parallel (13.1× speedup)**, `-Quick` mode skips compile-heavy modules for ~4min cycles.
- `tools/compute_harness.py`: subcommands `build` (/MP24 parallel cmake), `test-native`, `test-python-quick`, `test-python-full`, `gpu-info`, `gpu-oracle`, `profile` — all with wall-time reporting.
- `tools/gpu_oracle.py`: torch float64 batched M(q)/gravity/bias/Jacobians over the 7-coordinate macaque arm — **4096 poses in 0.776s, parity vs CPU 5.55e-17**.
- `/MP24` on all 6 ChimeraEngine CMakeLists + CMakePresets.json (parallel24 preset).
- Honest caveat: builds were already 23s on VS 2026 (the 10-20min premise didn't reproduce); the 13× test gain is partly host-contention removal. 3 test failures verified pre-existing on pristine master.
- **Every agent now has one-command access to parallel builds, parallel tests, and the GPU oracle.**

**2026-09-21 HARDWARE SUFFICIENCY VERDICT (operator asked "do we have sufficient hardware to continue"; answer delivered: YES with margin, E: disk the one binding constraint):** measured live with ~8 lanes running — i9-13900K 24c/32t at 28% load, 127.8 GB RAM with 96.8 GB FREE, RTX 4090 (CIM AdapterRAM reads 4 GB — the known 32-bit WMI artifact, real VRAM 24 GB), C: 402 GB free / E: 46.3 GB free of 1.9 TB. **Why E: fills (the operator's next question):** ~15 lane worktrees × ~10 GB each (full clones — the repo carries meshes/datasets/receipts), nothing deletable before master absorbs lanes (prune ancestor gate), the integration itself spiked 25 GB in two full clones (81G→23G crash; recovered to 46.3G by deleting the integrator's re-derivable clones, logs kept). **Standing disk policy:** new lanes use SPARSE clones (wave-34's 2.2 GB vs 12 GB full — 5× cut); merge→prune is a standing cycle (~45 GB frees next cycle); Vanhoof-class CT acquisitions (10–50 GB each) go to C: or wait for a prune; the 4090 is shared with the operator's Warzone (route headless). Added-disk threshold: only past ~15 concurrent lanes or all-data-local-at-once. Related: [[gait-walk-campaign-20260920]] (the prune manifest + four unmerged receipt branches queued for the next integration pass).
