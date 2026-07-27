"""orientation — THE WORLD'S DECLARED FRAME. Everything is expressed in it or converted to it.

    +X  east      +Y  north      +Z  up (against gravity)      RIGHT-HANDED
    yaw   measured from +X toward +Y   (0 = east, pi/2 = north)
    pitch measured from the XY plane   (+ = looking up)

WHY THIS FILE EXISTS (measured 2026-07-23): nothing declared a convention, and two
modules disagreed. render_world, membrane_shapes and progeny all use +Z up. But
terrarium.py:276 builds its turtle as H,L,U = (0,0,1),(1,0,0),(0,1,0) -- heading +Z,
UP +Y. A tree grown by the terrarium therefore lands on its SIDE in the world. And every
imported scan arrives in its own frame, because Construction derives 'up' per scan by SVD
of a RANSAC ground plane. Three frames, no declaration, silent disagreement.

You cannot ask "which way is the player facing" or "which way is this thing facing" until
one frame is authoritative. This file is that declaration, plus the conversions into it.

NOT IDENTICAL TO UNREAL. UE5 is Z-up but LEFT-handed with +X forward and +Y right. This
world is Z-up RIGHT-handed. Anything imported from a UE asset needs Y negated. Stated
here so nobody has to rediscover it from a mirrored mesh.

THE SIX DIRECTIONS ARE NOT ALL THE SAME KIND OF THING:
    UP / DOWN                     absolute when gravity exists -- they are the world's
    FORWARD / BACK / LEFT / RIGHT relative to where the player is looking, always
In free space there is no gravity and all six become player-relative. `six_directions`
takes `gravity_locked` for exactly this reason -- it is the difference between standing
on a planet and floating between them.
"""
from __future__ import annotations

import numpy as np

# --- the declaration -------------------------------------------------------
EAST = np.array([1.0, 0.0, 0.0])
NORTH = np.array([0.0, 1.0, 0.0])
UP = np.array([0.0, 0.0, 1.0])
HANDEDNESS = 'right'
CONVENTION = '+X east, +Y north, +Z up, right-handed; yaw from +X toward +Y'

# terrarium's turtle is Y-up; this maps its frame into the world's.
# turtle heading +Z -> world +X (a trunk grows along heading), turtle up +Y -> world +Z.
TURTLE_TO_WORLD = np.array([[0.0, 0.0, 1.0],
                            [1.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0]])


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.clip(n, 1e-12, None)


def basis_from_up(up, forward_hint=None) -> np.ndarray:
    """Orthonormal world basis from a measured up vector. Rows are (east, north, up).

    This is what a SCAN needs: Construction finds a ground plane and its normal, and that
    normal is the scan's up. Everything else follows from one arbitrary but recorded
    choice of forward, so the result is deterministic for a given input.
    """
    u = _unit(up)
    hint = np.asarray(forward_hint, dtype=float) if forward_hint is not None else EAST
    if abs(float(np.dot(_unit(hint), u))) > 0.98:        # hint parallel to up: pick another
        hint = NORTH
    e = _unit(hint - u * float(np.dot(hint, u)))
    n = np.cross(u, e)
    return np.stack([e, n, u], 0)


def canonicalize(splats: dict, up, forward_hint=None, origin=None) -> dict:
    """Rotate a splat cloud from its own frame into the world frame.

    Rotates POSITIONS, NORMALS **and COVARIANCES**. Forgetting covariance is the trap:
    positions would land correctly while every splat stayed oriented in the old frame, so
    a wall's splats would lie flat and the anisotropy that carries material identity would
    be measured against the wrong axes. Covariance transforms as R S R^T, not R S.
    """
    B = basis_from_up(up, forward_hint)        # rows are the new axes in old coordinates
    R = B                                      # old -> new is multiplication by the rows

    out = dict(splats)
    pos = np.asarray(splats['pos'], dtype=float)
    if origin is not None:
        pos = pos - np.asarray(origin, dtype=float)
    out['pos'] = pos @ R.T

    if splats.get('normal') is not None:
        out['normal'] = _unit(np.asarray(splats['normal'], dtype=float) @ R.T)
    if splats.get('cov') is not None:
        S = np.asarray(splats['cov'], dtype=float)
        out['cov'] = np.einsum('ij,njk,lk->nil', R, S, R)
    out['_frame'] = CONVENTION
    return out


def from_turtle(splats: dict) -> dict:
    """Bring terrarium/L-system output (Y-up) into the world frame (Z-up)."""
    return canonicalize(splats, up=TURTLE_TO_WORLD[2], forward_hint=TURTLE_TO_WORLD[0])


# --- facing ----------------------------------------------------------------


def facing(yaw: float, pitch: float = 0.0) -> np.ndarray:
    """Unit direction from yaw/pitch. yaw 0 = east, pi/2 = north; pitch + = up."""
    cp = np.cos(pitch)
    return np.array([np.cos(yaw) * cp, np.sin(yaw) * cp, np.sin(pitch)])


def yaw_of(direction) -> float:
    """Inverse of facing(): the yaw of a direction, ignoring its pitch."""
    d = np.asarray(direction, dtype=float)
    return float(np.arctan2(d[1], d[0]))


def pitch_of(direction) -> float:
    d = _unit(direction)
    return float(np.arcsin(np.clip(d[2], -1.0, 1.0)))


def player_frame(yaw: float, pitch: float = 0.0) -> dict:
    """The player's own axes in world coordinates — the egocentric half of the six rule."""
    fwd = facing(yaw, pitch)
    right = _unit(np.cross(fwd, UP))
    if not np.isfinite(right).all() or np.linalg.norm(right) < 1e-9:
        right = EAST.copy()                     # looking straight up or down
    up = np.cross(right, fwd)
    return {'forward': fwd, 'right': right, 'up': up}


def six_directions(yaw: float = 0.0, pitch: float = 0.0,
                   gravity_locked: bool = True) -> dict:
    """The six work buckets as world-space vectors.

    gravity_locked=True  (standing on a planet): UP/DOWN are the WORLD's, not yours --
                         you can look at your boots without 'down' changing meaning.
    gravity_locked=False (free space): all six are player-relative, because there is no
                         privileged up. This is the frame-not-a-compass distinction made
                         executable rather than described.
    """
    f = player_frame(yaw, pitch)
    up = UP.copy() if gravity_locked else f['up']
    return {
        'forward': f['forward'], 'back': -f['forward'],
        'right': f['right'], 'left': -f['right'],
        'up': up, 'down': -up,
        '_gravity_locked': gravity_locked,
    }


def look_at(eye, target, world_up=None) -> dict:
    """Camera frame for a renderer. Matches render_world's up_hint convention."""
    eye = np.asarray(eye, dtype=float)
    fwd = _unit(np.asarray(target, dtype=float) - eye)
    wu = UP if world_up is None else _unit(world_up)
    if abs(float(np.dot(fwd, wu))) > 0.999:
        wu = NORTH
    right = _unit(np.cross(fwd, wu))
    return {'eye': eye, 'forward': fwd, 'right': right, 'up': np.cross(right, fwd)}


# --- validation ------------------------------------------------------------


def check_frame(splats: dict, expect: str = 'ground') -> dict:
    """Is this scene actually in the world frame? Returns facts, not a verdict.

    'ground'  most normals should point +Z
    'sky'     most normals should point -Z (an inward-facing dome looks DOWN at you)
    'object'  no expectation; reports the spread so you can see if it is degenerate
    """
    n = splats.get('normal')
    if n is None:
        return {'frame': splats.get('_frame', 'undeclared'), 'normals': 'absent'}
    d = _unit(np.asarray(n, dtype=float))
    z = d[:, 2]
    out = {
        'frame': splats.get('_frame', 'undeclared'),
        'mean_normal_z': float(z.mean()),
        'frac_up': float((z > 0.5).mean()),
        'frac_down': float((z < -0.5).mean()),
        'height_range': [float(np.asarray(splats['pos'])[:, 2].min()),
                         float(np.asarray(splats['pos'])[:, 2].max())],
    }
    if expect == 'ground':
        out['ok'] = out['frac_up'] > 0.6
    elif expect == 'sky':
        out['ok'] = out['frac_down'] > 0.6
    else:
        out['ok'] = None
    out['expected'] = expect
    return out


def main() -> None:
    print(f'  CONVENTION  {CONVENTION}')
    print(f'  handedness  {HANDEDNESS}   (UE5 is Z-up LEFT-handed: negate Y on import)')
    for name, yaw in (('east', 0.0), ('north', np.pi / 2), ('west', np.pi), ('south', -np.pi / 2)):
        print(f'  yaw {yaw:+.3f} -> {name:5} {np.round(facing(yaw), 3)}')
    print()
    d = six_directions(yaw=np.pi / 2, gravity_locked=True)
    print('  facing NORTH, standing on a planet:')
    for k in ('forward', 'back', 'left', 'right', 'up', 'down'):
        print(f'    {k:8} {np.round(d[k], 3)}')


if __name__ == '__main__':
    main()
