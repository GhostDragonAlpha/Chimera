"""det-mpm whole-run MPM determinism arm runner.

PREREG-BOUND: this script is executed only after the prereg draft
(PREREG_MPM_DETERMINISM.md) is committed and the Lieutenant hands back the
commit pin. Each invocation is ONE process running ONE arm.

Scene: "mpm-multi-spec" -- structure copied from
newton/examples/mpm/example_mpm_multi_material.py (newton 1.6.0): kinematic
boundary block + sand + snow + mud, ground plane, example default material
parameters, voxel_size 0.05, particles_per_cell 3, builder-seeded jitter RNG.
Headless (no viewer). solver.step + solver.project_outside per frame.

Arms (--mode x --contention x --device):
  mode: not_guaranteed | run_to_run   (warp.config.deterministic, set before
        newton import so it applies at module-load time; readback recorded)
  contention: 0 = clean; N > 0 = N back-to-back launches of an atomic-heavy
        kernel on a second CUDA stream, queued before frame 1 so the whole run
        is contended. Precise workload: dim 32768 threads (block_dim 256),
        each thread performs 8192 wp.atomic_add(float32) ops into a shared
        4096-element window => 268,435,456 atomic adds per launch, ~2.1e11 at
        N=800. The kernel writes only its own array; it cannot change MPM
        inputs, it competes for GPU resources.
  device: cuda:0 (GPU arms, via the GPU queue) | cpu (control arm; sets
        CUDA_VISIBLE_DEVICES="" before importing warp so zero GPU contact is
        possible).

Outputs (declared per job): receipt.json, frame_hashes.csv, checkpoint npz
files, env.json (GPU arms only).
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--arm", required=True)
PARSER.add_argument("--mode", required=True, choices=["not_guaranteed", "run_to_run"])
PARSER.add_argument("--device", required=True, choices=["cuda:0", "cpu"])
PARSER.add_argument("--frames", type=int, required=True)
PARSER.add_argument("--contention", type=int, default=0, help="0 = clean arm")
PARSER.add_argument("--contention-iters", type=int, default=None,
                    help="atomic adds per thread per contention launch; default CONTENTION_ITERS (8192); AMENDMENT-5 r2r variant passes 1024")
PARSER.add_argument("--out", required=True, help="artifact output directory")
ARGS = PARSER.parse_args()

if ARGS.device == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import numpy as np  # noqa: E402
import warp as wp  # noqa: E402

wp.config.deterministic = wp.DeterministicMode[ARGS.mode.upper()]
import newton  # noqa: E402  (after deterministic is set: applies at module load)
from newton.solvers import SolverImplicitMPM  # noqa: E402

MODE_SET = int(wp.config.deterministic)
assert MODE_SET == wp.DeterministicMode[ARGS.mode.upper()], "deterministic mode not applied"

VOXEL = 0.05
FPS = 60.0
FRAME_DT = 1.0 / FPS
SUBSTEPS = 1
CHECKPOINT_EVERY = 20
CONTENTION_DIM = 32768
CONTENTION_BLOCK = 256
CONTENTION_ITERS = 8192
# AMENDMENT-5: the r2r variant runs iters=1024 (33,554,432 records/launch) because the R2R sort-reduce workspace for 268M records (10,871,935,487 B) exceeds the int32 array-shape limit; total per-frame atomic traffic is preserved by scaling N in the sizing formula.
CONTENTION_ITERS_EFFECTIVE = (ARGS.contention_iters
                              if ARGS.contention_iters is not None
                              else CONTENTION_ITERS)
# AMENDMENT-4/5: deterministic atomics record (key, value) scatters in a
# buffer bounded per-thread by deterministic_max_records (default 0 = static
# codegen bound); the R2R sort-reduce workspace is sized from this bound, so
# it must track the per-thread visit count (iters) -- a larger bound wastes
# workspace, a smaller one overflows. Set to the effective per-thread atomic
# count; NG mode ignores it. Applied before module creation.
wp.config.deterministic_max_records = CONTENTION_ITERS_EFFECTIVE
assert int(wp.config.deterministic_max_records) == CONTENTION_ITERS_EFFECTIVE, \
    "deterministic_max_records not applied"
CONTENTION_WINDOW = 4096


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def array_digest(a):
    return hashlib.sha256(a.numpy().tobytes()).hexdigest()


def state_arrays(state):
    found = {}
    for name in dir(state):
        if name.startswith("_"):
            continue
        try:
            v = getattr(state, name)
        except Exception:
            continue
        if isinstance(v, wp.array):
            found[name] = v
    return dict(sorted(found.items()))


def hash_state(state):
    parts = {}
    for name, arr in state_arrays(state).items():
        parts[name] = array_digest(arr)
    combined = hashlib.sha256(
        "|".join(f"{k}:{v}" for k, v in parts.items()).encode()
    ).hexdigest()
    return combined, parts


@wp.kernel(enable_backward=False)
def contention_kernel(dst: wp.array[float], iters: int):
    tid = wp.tid()
    for k in range(iters):
        # return value discarded: pure scatter-add. Under DeterministicMode
        # RUN_TO_RUN, warp 1.17.0 codegen rejects CONSUMED-return float atomics
        # ("supports consumed-return counter atomics only for int32 counter
        # arrays"); the atomic traffic (dim, block_dim, iters, window, add
        # count) is identical to the registered workload.
        wp.atomic_add(dst, (tid + k) % CONTENTION_WINDOW, 1.0)


def emit_scene(builder):
    """Same structure and parameters as example_mpm_multi_material.emit_particles."""

    def spawn(bounds_lo, bounds_hi, density, flags):
        particles_per_cell = 3
        res = np.ceil(particles_per_cell * (bounds_hi - bounds_lo) / VOXEL).astype(int)
        cell_size = (bounds_hi - bounds_lo) / res
        radius = np.max(cell_size) * 0.5
        mass = np.prod(cell_size) * density
        begin_id = len(builder.particle_q)
        builder.add_particle_grid(
            pos=wp.vec3(bounds_lo),
            rot=wp.quat_identity(),
            vel=wp.vec3(0.0),
            dim_x=int(res[0]) + 1,
            dim_y=int(res[1]) + 1,
            dim_z=int(res[2]) + 1,
            cell_x=float(cell_size[0]),
            cell_y=float(cell_size[1]),
            cell_z=float(cell_size[2]),
            mass=float(mass),
            jitter=2.0 * radius,
            radius_mean=float(radius),
            flags=flags,
        )
        return np.arange(begin_id, len(builder.particle_q), dtype=int)

    kin = spawn(np.array([-0.5, -0.5, 0.0]), np.array([0.5, 0.5, 0.25]), 0.0, newton.ParticleFlags.ACTIVE)
    sand = spawn(np.array([-0.5, 0.25, 0.5]), np.array([0.5, 0.75, 0.75]), 2500.0, newton.ParticleFlags.ACTIVE)
    snow = spawn(np.array([-0.5, -0.75, 0.5]), np.array([0.5, -0.25, 0.75]), 300.0, newton.ParticleFlags.ACTIVE)
    mud = spawn(np.array([-0.25, -0.5, 1.0]), np.array([0.25, 0.5, 1.5]), 1000.0, newton.ParticleFlags.ACTIVE)
    return {"kinematic": kin, "sand": sand, "snow": snow, "mud": mud}


def main():
    os.makedirs(ARGS.out, exist_ok=True)
    receipt = {
        "lane": "det-mpm",
        "arm": ARGS.arm,
        "mode_requested": ARGS.mode,
        "mode_set_int": MODE_SET,
        "deterministic_max_records": int(wp.config.deterministic_max_records),
        "device_requested": ARGS.device,
        "frames": ARGS.frames,
        "contention_launches": ARGS.contention,
        "contention_iters": CONTENTION_ITERS_EFFECTIVE,
        "scene": "mpm-multi-spec",
        "voxel_size": VOXEL,
        "frame_dt": FRAME_DT,
        "substeps": SUBSTEPS,
        "checkpoint_every": CHECKPOINT_EVERY,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": sys.version.split()[0],
    }
    csv_path = os.path.join(ARGS.out, "frame_hashes.csv")
    env_path = os.path.join(ARGS.out, "env.json")
    csv = open(csv_path, "w", buffering=1)
    csv.write("frame,frame_ns,state_hash\n")
    try:
        # --- environment identity (GPU arms) ---
        if ARGS.device == "cuda:0":
            smi = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,compute_cap,memory.total,uuid",
                 "--format=csv"],
                capture_output=True, text=True, timeout=60,
            )
            env = {"nvidia_smi_csv": smi.stdout.strip(), "nvidia_smi_err": smi.stderr.strip()}
            dev = wp.get_device("cuda:0")
            env["warp_device_name"] = getattr(dev, "name", None)
            env["warp_device_arch"] = str(getattr(dev, "arch", None))
            with open(env_path, "w") as f:
                json.dump(env, f, indent=1)
            receipt["env_json_sha256"] = sha256_file(env_path)

        # --- scene construction ---
        builder = newton.ModelBuilder()
        SolverImplicitMPM.register_custom_attributes(builder)
        groups = emit_scene(builder)
        builder.add_ground_plane()
        model = builder.finalize(device=ARGS.device)
        receipt["particle_count"] = int(model.particle_count)
        receipt["group_ranges"] = {k: [int(v[0]), int(v[-1])] for k, v in groups.items()}
        receipt["ic_builder_particle_q_sha256"] = hashlib.sha256(
            np.asarray(builder.particle_q, dtype=np.float32).tobytes()
        ).hexdigest()

        sand, snow, mud = (
            wp.array(groups["sand"], dtype=int, device=model.device),
            wp.array(groups["snow"], dtype=int, device=model.device),
            wp.array(groups["mud"], dtype=int, device=model.device),
        )
        model.mpm.yield_pressure[snow].fill_(2.0e4)
        model.mpm.tensile_yield_ratio[snow].fill_(0.2)
        model.mpm.friction[snow].fill_(0.1)
        model.mpm.hardening[snow].fill_(10.0)
        model.mpm.dilatancy[snow].fill_(1.0)
        model.mpm.yield_pressure[mud].fill_(1.0e10)
        model.mpm.yield_stress[mud].fill_(3.0e2)
        model.mpm.tensile_yield_ratio[mud].fill_(1.0)
        model.mpm.friction[mud].fill_(0.0)
        model.mpm.viscosity[mud].fill_(100.0)

        config = SolverImplicitMPM.Config()
        config.voxel_size = VOXEL
        config.tolerance = 1.0e-6
        config.max_iterations = 250
        solver = SolverImplicitMPM(model, config=config, enable_timers=False)
        receipt["mode_after_solver_construct"] = int(wp.config.deterministic)
        assert int(wp.config.deterministic) == MODE_SET, "mode changed at solver construction"

        state_0 = model.state()
        state_1 = model.state()
        receipt["state_array_names"] = sorted(state_arrays(state_0))

        ic_hash, ic_parts = hash_state(state_0)
        receipt["ic_state_hash"] = ic_hash
        receipt["ic_state_parts"] = ic_parts

        # --- contention workload, interleaved with the scene ---
        # v3: kernel takes runtime `iters` (call site passes CONTENTION_ITERS,
        # byte-identical atomic workload per launch as registered). The total
        # launch budget N is distributed evenly across frames: before each
        # frame's timed window the host queues that frame's share on the
        # contention stream (bounded pending depth <= chunk+share), so the
        # atomic-heavy stream executes CONCURRENTLY with every scene frame.
        cont_stream = None
        cont_arr = None
        contention_share = 0
        contention_rem = 0
        if ARGS.contention > 0:
            if ARGS.device != "cuda:0":
                raise RuntimeError("contention arms are GPU-only")
            cont_stream = wp.Stream(device=model.device)
            cont_arr = wp.zeros(CONTENTION_WINDOW, dtype=float, device=model.device)
            base_share, rem = divmod(ARGS.contention, ARGS.frames)
            if base_share == 0:
                raise RuntimeError("contention budget N must be >= frames")
            contention_share = base_share
            contention_rem = rem

        # --- timed whole run ---
        wp.synchronize()
        rolling = hashlib.sha256()
        frame_ns = []
        checkpoints = []
        t_run0 = time.perf_counter()
        for f in range(ARGS.frames):
            if contention_share:
                share = contention_share + (1 if f < contention_rem else 0)
                for _ in range(share):
                    wp.launch(
                        contention_kernel,
                        dim=CONTENTION_DIM,
                        inputs=[cont_arr, CONTENTION_ITERS_EFFECTIVE],
                        device=model.device,
                        stream=cont_stream,
                        block_dim=CONTENTION_BLOCK,
                    )
            t0 = time.perf_counter()
            state_0.clear_forces()
            solver.step(state_0, state_1, None, None, FRAME_DT)
            solver.project_outside(state_1, state_1, FRAME_DT)
            state_0, state_1 = state_1, state_0
            wp.synchronize()
            t1 = time.perf_counter()
            frame_ns.append(t1 - t0)
            f_hash, _ = hash_state(state_0)
            csv.write(f"{f},{(t1 - t0) * 1e9:.0f},{f_hash}\n")
            rolling.update(f"{f:06d}:{f_hash}\n".encode())
            if (f + 1) % CHECKPOINT_EVERY == 0 or f == ARGS.frames - 1:
                cp = {
                    "frame": f,
                    "state_hash": f_hash,
                    "rolling_hash": rolling.copy().hexdigest(),
                }
                npz_path = os.path.join(ARGS.out, f"state_f{f:04d}.npz")
                np.savez(
                    npz_path,
                    particle_q=state_0.particle_q.numpy(),
                    particle_qd=state_0.particle_qd.numpy(),
                )
                cp["npz"] = os.path.basename(npz_path)
                cp["npz_sha256"] = sha256_file(npz_path)
                checkpoints.append(cp)
        receipt["whole_run_rolling_hash"] = rolling.hexdigest()
        receipt["checkpoints"] = checkpoints

        # --- contention drain ---
        if ARGS.contention > 0:
            t0 = time.perf_counter()
            wp.synchronize()
            receipt["contention_drain_wait_s"] = time.perf_counter() - t0
            receipt["contention_drain_wait_cap_s"] = 300.0
            receipt["contention_underflow"] = receipt["contention_drain_wait_s"] <= 1e-9

        t_run = time.perf_counter() - t_run0
        fa = np.asarray(frame_ns[1:])
        receipt["timing"] = {
            "boundary": "perf_counter around clear_forces+step+project_outside+wp.synchronize, per frame",
            "frame0_s": frame_ns[0] if frame_ns else None,
            "frames_2_to_N_mean_s": float(fa.mean()) if fa.size else None,
            "frames_2_to_N_p50_s": float(np.percentile(fa, 50)) if fa.size else None,
            "frames_2_to_N_p95_s": float(np.percentile(fa, 95)) if fa.size else None,
            "frames_2_to_N_max_s": float(fa.max()) if fa.size else None,
            "total_run_s_excl_construction_and_hashing": t_run,
            "scope": "THIS scene, THIS hardware, THIS env only; no engine generalization",
        }
        receipt["mode_at_end"] = int(wp.config.deterministic)
        receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        receipt["frame_hashes_csv_sha256"] = sha256_file(csv_path)
        receipt["status"] = "COMPLETED"
    except Exception as exc:  # failure preservation: keep partial artifacts
        receipt["status"] = "FAILED"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        csv.flush()
        csv.close()
        receipt["frame_hashes_csv_sha256"] = sha256_file(csv_path)
        with open(os.path.join(ARGS.out, "receipt.json"), "w") as f:
            json.dump(receipt, f, indent=1)


if __name__ == "__main__":
    main()
