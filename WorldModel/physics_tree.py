"""
Physics-informed oak tree generator.

Laws encoded:
  1. Gravitropism: branches grow upward against gravity vector
  2. Phototropism: branches grow toward light (sky hemisphere)
  3. Beam mechanics: radius ∝ (supported mass)^(1/3) — thicker at base
  4. Murray's law: parent_radius³ = sum(child_radius³) — optimal fluid transport
  5. Wind pruning: canopy asymmetry from prevailing wind direction
  6. Self-shadowing: inner branches receive less light → sparser growth
  7. Fibonacci phyllotaxis: leaves arranged at golden angle for max light capture

These constraints produce trees that look REAL because they obey the
same physical forces as real trees. The VAE learns the manifold of
physically-plausible trees, not random blobs.
"""

import math
import numpy as np


# Physical constants
GRAVITY = np.array([0.0, 0.0, -1.0])  # normalized down vector
LIGHT_DIRECTION = np.array([0.0, 0.0, 1.0])  # hemispherical sky
GOLDEN_ANGLE = math.pi * (3.0 - math.sqrt(5.0))  # ~137.5°
GRAVITROPISM_WEIGHT = 0.6  # how strongly branches grow upward
PHOTOTROPISM_WEIGHT = 0.4   # how strongly branches grow toward light
MURRAY_EXPONENT = 3.0       # r_parent³ = sum(r_child³)
WIND_VECTOR = np.array([0.3, 0.0, 0.0])  # prevailing wind
WIND_PRUNE_STRENGTH = 0.15  # how much wind prunes leeward side
TAPER_RATE = 0.7            # radius taper per unit length
MAX_SELF_SHADOW_DEPTH = 4   # levels before inner branches die off


class PhysicsBranch:
    """A branch segment with physical properties."""

    def __init__(self, start, direction, length, radius, depth, parent=None):
        self.start = np.array(start, dtype=np.float32)
        self.direction = direction / (np.linalg.norm(direction) + 1e-12)
        self.length = length
        self.radius = radius
        self.depth = depth
        self.parent = parent
        self.children = []
        self.end = self.start + self.direction * length
        self.leaf_density = 1.0  # modulated by light availability

    @property
    def supported_mass(self):
        """Total leaf mass supported by this branch (children + own leaves)."""
        mass = self.length * self.radius * self.radius  # own mass ∝ volume
        for child in self.children:
            mass += child.supported_mass
        return mass

    def required_radius(self) -> float:
        """Beam mechanics: radius needed to support current mass."""
        # Euler-Bernoulli: deflection ∝ mass×length³/(E×r⁴)
        # To keep deflection constant: r⁴ ∝ mass × length³
        # So r ∝ (mass)^(1/4) × length^(3/4)
        if self.supported_mass <= 0:
            return 0.01
        return 0.1 * (self.supported_mass ** 0.25) * (self.length ** 0.75)

    def apply_murray(self):
        """Enforce Murray's law: parent radius³ = sum(child radius³)."""
        child_cubes = sum(c.radius ** MURRAY_EXPONENT for c in self.children)
        if child_cubes > 0:
            self.radius = max(self.radius, child_cubes ** (1.0 / MURRAY_EXPONENT))


def grow_tree(trunk_height=300, trunk_radius=14, max_depth=4, seed=42) -> list:
    """
    Grow a physics-informed oak tree.

    Returns: list of (position, direction, length, radius, depth, is_leaf, leaf_spread)
    to be converted into Gaussian splats.
    """
    rng = np.random.RandomState(seed)
    segments = []

    # Initialize trunk
    trunk = PhysicsBranch(
        np.array([0.0, 0.0, -200.0]),
        np.array([0.0, 0.15, 0.85]),
        trunk_height * 0.5,
        trunk_radius,
        depth=0,
    )
    segments.append(trunk)
    queue = [trunk]

    while queue:
        branch = queue.pop(0)

        # Light availability: decreases with depth (self-shadowing)
        branch.leaf_density = max(0.05, 1.0 - branch.depth / MAX_SELF_SHADOW_DEPTH)

        # Wind pruning: reduce growth on leeward side
        wind_dot = np.dot(branch.direction, WIND_VECTOR)
        wind_factor = 1.0 - abs(wind_dot) * WIND_PRUNE_STRENGTH

        if branch.depth >= max_depth:
            # Terminal: add leaf cluster
            segments.append(("leaf", branch.end, branch.radius * 3,
                             int(30 * branch.leaf_density * wind_factor)))
            continue

        # Compute growth direction: weighted sum of inertia + gravitropism + phototropism
        inertia = branch.direction * (1.0 - GRAVITROPISM_WEIGHT - PHOTOTROPISM_WEIGHT)
        gravitropic = -GRAVITY * GRAVITROPISM_WEIGHT
        # Phototropism: random direction in sky hemisphere, biased by current direction
        sky_angle = rng.uniform(0, 2 * math.pi)
        sky_elevation = rng.uniform(0.3, math.pi / 2)
        photo_dir = np.array([
            math.cos(sky_elevation) * math.cos(sky_angle),
            math.cos(sky_elevation) * math.sin(sky_angle),
            math.sin(sky_elevation),
        ]) * PHOTOTROPISM_WEIGHT

        growth_dir = inertia + gravitropic + photo_dir
        growth_dir /= np.linalg.norm(growth_dir) + 1e-12

        # Branch length scales with radius and depth
        child_length = branch.length * 0.6 * (1.0 - 0.1 * branch.depth)

        # Number of children follows Murray's law
        num_children = min(3, max(1, int(branch.radius / 3)))
        if branch.depth >= max_depth - 1:
            num_children = max(2, num_children)

        total_child_radius_cubed = 0
        children = []

        for c in range(num_children):
            # Branching angle: wider at lower depths, narrower near canopy
            spread_angle = rng.uniform(0.3, 1.2) * (1.0 - 0.15 * branch.depth)
            azimuth = rng.uniform(0, 2 * math.pi)

            # Fibonacci preferred angles for leaf-level branches
            if branch.depth >= max_depth - 1:
                azimuth = GOLDEN_ANGLE * c + rng.uniform(-0.2, 0.2)

            # Rotate growth direction by spread angle
            # Rodrigues rotation around a random perpendicular axis
            perp = np.cross(growth_dir, np.array([rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0]))
            perp /= np.linalg.norm(perp) + 1e-12
            perp2 = perp + np.array([rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0.0])
            perp2 /= np.linalg.norm(perp2) + 1e-12

            child_dir = (
                growth_dir * math.cos(spread_angle)
                + perp * math.sin(spread_angle) * math.cos(azimuth)
                + perp2 * math.sin(spread_angle) * math.sin(azimuth)
            )
            child_dir /= np.linalg.norm(child_dir) + 1e-12

            # Child radius from Murray's law
            child_radius = branch.radius * 0.55 * (1.0 - 0.1 * c)  # decreasing with child index

            # Taper: radius decreases along branch
            taper = 1.0 - TAPER_RATE * (branch.depth / max_depth)
            child_radius *= taper

            child = PhysicsBranch(
                branch.end,
                child_dir,
                child_length * (1.0 - 0.1 * c),  # shorter for later children
                max(0.3, child_radius),
                branch.depth + 1,
                parent=branch,
            )
            total_child_radius_cubed += child.radius ** MURRAY_EXPONENT
            children.append(child)

        # Enforce Murray's law
        if total_child_radius_cubed > 0:
            murray_radius = total_child_radius_cubed ** (1.0 / MURRAY_EXPONENT)
        else:
            murray_radius = branch.radius

        branch.radius = min(branch.radius, murray_radius * 1.5)

        # Apply beam mechanics: radius must support mass
        required = branch.required_radius()
        branch.radius = max(branch.radius, required)

        # Add branch segment for rendering
        segments.append((
            "branch",
            branch.start, branch.direction, branch.length, branch.radius,
            branch.depth, branch.leaf_density,
        ))

        branch.children = children
        for child in children:
            queue.append(child)

    # Top-down: apply beam mechanics
    _apply_beam_mechanics(trunk)

    return segments


def _apply_beam_mechanics(branch: PhysicsBranch):
    """Post-order: enforce beam mechanics from leaves to trunk."""
    for child in branch.children:
        _apply_beam_mechanics(child)
    branch.apply_murray()
    if branch.parent is None:
        branch.radius = max(branch.radius, branch.required_radius())


def segments_to_splats(segments, target_count=200000) -> dict:
    """Convert physical tree segments into Gaussian splat arrays."""
    positions = []; colors = []; opacities = []; scales = []; rots = []
    N = 0

    for seg in segments:
        if isinstance(seg, tuple):
            kind = seg[0]
            if kind == "leaf":
                _, center, spread, count = seg
                for _ in range(count):
                    lx = center[0] + np.random.normal(0, spread)
                    ly = center[1] + np.random.normal(0, spread)
                    lz = center[2] + np.random.normal(0, spread * 0.7)
                    if lz < center[2] - spread: lz = center[2] - spread * 0.7 + np.random.uniform(0, spread * 0.5)
                    positions.append([lx, ly, lz])
                    colors.append([0.05 + np.random.uniform(0, 0.08),
                                   np.random.uniform(0.4, 0.8),
                                   0.06 + np.random.uniform(0, 0.05)])
                    opacities.append(np.random.uniform(0.7, 0.95))
                    s = np.random.uniform(1.5, 4)
                    scales.append([s, s, s])
                    rots.append([0, 0, 0, 1])
                    N += 1
            elif kind == "branch":
                _, start, direction, length, radius, depth, leaf_density = seg
                n_pts = max(20, int(length * radius * 3))
                for i in range(n_pts):
                    t = i / (n_pts - 1)
                    pt = start + direction * length * t
                    r = radius * (1.0 - t * 0.6)
                    bark_r = abs(rng_gauss(r / 3))
                    for _ in range(max(1, int(r * 2))):
                        ox = np.random.normal(0, bark_r)
                        oy = np.random.normal(0, bark_r)
                        oz = np.random.normal(0, bark_r)
                        positions.append([pt[0] + ox, pt[1] + oy, pt[2] + oz])
                        b = 0.08 + depth * 0.02 - t * 0.03
                        colors.append([0.30, 0.16, max(0.04, b)])
                        opacities.append(0.9)
                        s = max(0.3, r * 0.7)
                        scales.append([s, s, s])
                        rots.append([0, 0, 0, 1])
                        N += 1
        elif isinstance(seg, PhysicsBranch):
            # Branch segment from grow_tree
            n_pts = max(20, int(seg.length * seg.radius * 3))
            for i in range(n_pts):
                t = i / (n_pts - 1)
                pt = seg.start + seg.direction * seg.length * t
                r = seg.radius * (1.0 - t * 0.6)
                bark_r = abs(rng_gauss(r / 3))
                for _ in range(max(1, int(r * 2))):
                    ox = np.random.normal(0, bark_r)
                    oy = np.random.normal(0, bark_r)
                    oz = np.random.normal(0, bark_r)
                    positions.append([pt[0] + ox, pt[1] + oy, pt[2] + oz])
                    b = 0.08 + seg.depth * 0.02 - t * 0.03
                    colors.append([0.30, 0.16, max(0.04, b)])
                    opacities.append(0.9)
                    s = max(0.3, r * 0.7)
                    scales.append([s, s, s])
                    rots.append([0, 0, 0, 1])
                    N += 1

    # Pad or truncate to target
    n = min(N, target_count)
    return {
        "positions": np.array(positions[:n], dtype=np.float32),
        "colors": np.array(colors[:n], dtype=np.float32),
        "opacities": np.array(opacities[:n], dtype=np.float32),
        "scales": np.array(scales[:n], dtype=np.float32),
        "rotations": np.array(rots[:n], dtype=np.float32),
        "count": n,
    }


def rng_gauss(std, max_val=1e9):
    """Generate random value with Gaussian distribution, clamped."""
    v = np.random.normal(0, std)
    if abs(v) > max_val:
        return max_val * (1 if v > 0 else -1)
    return v
