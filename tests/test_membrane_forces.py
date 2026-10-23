# SPDX-License-Identifier: AGPL-3.0-or-later
"""Headless membrane per-vertex force readback (chimera.studio.membrane-forces.v1).

bpy-free: launches the LOCALLY BUILT engine (build/gpu-engine/Release/chimera_engine.exe,
not the pinned runtime/gpu copy) directly, the tests/test_gpu_lifetime.py launch pattern,
and drives it with the same raw-HTTP control client the existing membrane tests use.
Builds the three-film apex-weld assembly (blocks.starter), applies a centre dead-load W,
then verifies the new /membrane_demo_forces endpoint against independent physics.
"""
import os, shutil, socket, subprocess, sys, time, uuid
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'python'))
from chimera_studio import blocks
from chimera_studio.gpu_native import membrane_packet, _control

EXE = ROOT / 'build/gpu-engine/Release/chimera_engine.exe'


def launch():
    """Start the locally built engine headless (PrivateEngine launch pattern,
    pointed at the build tree; shaders ship beside the built exe)."""
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]
    folder = ROOT / '.user/gpu-runs' / uuid.uuid4().hex; folder.mkdir(parents=True)
    shutil.copytree(EXE.parent / 'shaders', folder / 'shaders')
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    startup = None
    if os.name == 'nt':
        startup = subprocess.STARTUPINFO(); startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW; startup.wShowWindow = 0
    proc = subprocess.Popen([str(EXE), str(port), '--no-board', '384', '256', '--no-restore', '--hidden'],
                            cwd=folder, stdout=(folder / 'stdout.log').open('wb'),
                            stderr=(folder / 'stderr.log').open('wb'),
                            creationflags=flags, startupinfo=startup,
                            env={**os.environ, 'CHIMERA_STUDIO_OFFSCREEN': '1'})
    ctl = _control.EngineControl(f'http://127.0.0.1:{port}', timeout=12)
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError('Engine exited at startup: ' + (folder / 'stderr.log').read_text(errors='replace')[:2000])
        try:
            ctl.telemetry(); return proc, ctl
        except OSError:
            time.sleep(.2)
    raise TimeoutError('Engine startup timed out')


parts, connections = blocks.starter()
spec = blocks.compile_parts(parts, connections)   # 3 films, one shared apex weld, uniform gamma
FACES = np.asarray(spec['triangles'], dtype='<u4').reshape(-1, 3)
GAMMA = spec['gamma']

def heron_energy(P):
    """Client-side surface energy U(P) from 3-D edge lengths (Heron, f64)."""
    v = P[FACES].astype(float)
    ab = np.linalg.norm(v[:, 1] - v[:, 0], axis=1)
    bc = np.linalg.norm(v[:, 2] - v[:, 1], axis=1)
    ca = np.linalg.norm(v[:, 0] - v[:, 2], axis=1)
    s = (ab + bc + ca) * .5
    return np.sqrt(np.maximum(0., s * (s - ab) * (s - bc) * (s - ca))).sum() * GAMMA

proc = None
try:
    proc, ctl = launch()
    init = ctl.request('POST', '/membrane_demo_bin', membrane_packet(spec))
    assert init.get('ok'), init
    W = float(np.float32(0.8))
    st = ctl.request('POST', '/membrane_demo', {'op': 'deform', 'load_N': W})
    assert st.get('ok') and abs(st['centre_load_N'] - W) < 1e-12, st
    fdoc = ctl.request('GET', '/membrane_demo_forces')
    saved = ctl.request('GET', '/membrane_demo_save')
    status = ctl.request('GET', '/membrane_demo')

    assert fdoc['schema'] == 'chimera.studio.membrane-forces.v1', fdoc['schema']
    # (d) the forces document describes the ACCEPTED state (the id rides as a
    # decimal STRING in save/forces documents; the status route prints a number)
    sid = fdoc['accepted_state_id']
    assert sid == saved['accepted_state_id'] and int(sid) == int(status['accepted_state_id']), \
        (sid, saved['accepted_state_id'], status['accepted_state_id'])
    assert fdoc['centre_index'] == 0 and fdoc['n_verts'] == len(spec['positions']) == 601, fdoc['n_verts']
    # status prints energy with %.9g: agreement to its own print precision
    assert abs(fdoc['energy_J'] - status['energy']) < 1e-8 and abs(fdoc['centre_load_N'] - W) < 1e-12

    vf = np.asarray(fdoc['vertex_forces'], dtype='<f4').astype(float).reshape(-1, 3)
    # the deformed ACCEPTED geometry (the sagged equilibrium under W), f32 exact
    P = np.asarray(saved['positions_f32'], dtype='<f4').astype(float).reshape(-1, 3)
    assert len(P) == 601 and np.isfinite(P).all()
    assert abs(heron_energy(P) - fdoc['energy_J']) < 3e-4, (heron_energy(P), fdoc['energy_J'])

    # (a) free centre apex: matter force balances the dead-load, zero rail x/y
    apex_err = float(np.abs(vf[0] - np.array([0., 0., W])).max())
    assert apex_err < 1e-4, (vf[0], W)
    # (c) translation invariance: sum of all matter forces is zero
    sum_err = float(np.abs(vf.sum(axis=0)).max())
    assert sum_err < 1e-4, vf.sum(axis=0)

    # (b) independent finite-difference check, EVERY vertex and component:
    # R_fd = -(U(P+de)-U(P-de))/(2de) must reproduce the kernel's vf.
    delta = 1e-5
    R_fd = np.empty_like(vf)
    for v in range(len(P)):
        for c in range(3):
            plus = P.copy(); plus[v, c] += delta
            minus = P.copy(); minus[v, c] -= delta
            R_fd[v, c] = -(heron_energy(plus) - heron_energy(minus)) / (2 * delta)
    dev = np.abs(R_fd - vf)
    max_dev = float(dev.max()); arg = np.unravel_index(dev.argmax(), dev.shape)
    assert max_dev < 1e-4, (max_dev, arg, R_fd[arg], vf[arg])
    # the largest reactions live at pinned geometry (rim/anchor), not the apex:
    rim = dev.max(axis=1).copy(); rim[0] = 0
    print(f'PASS membrane-forces: apex vf={vf[0].tolist()} W={W} apex_err={apex_err:.3e} '
          f'sum_vf={vf.sum(axis=0).tolist()} sum_err={sum_err:.3e} max_fd_dev={max_dev:.3e} '
          f'at vertex {arg[0]} comp {arg[1]} max_rim_dev={float(rim.max()):.3e} energy={fdoc["energy_J"]:.9f}')
finally:
    if proc is not None:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
