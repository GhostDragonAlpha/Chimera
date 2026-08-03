"""touchables.py -- the world answers back. Phase E, rung 2 (TOUCH), docs/THE_SLICE.md.

THE MEMBRANE (stated 2026-08-03, before this file was built):

    STATEMENT. Three passive classes suffice to make the world tangible: a RIGID stone (contact
    impulse + Coulomb friction), a GROWN tuft (damped spring -- the passive-tissue port,
    grass-sized), a GRANULAR pile (kicked grains, repose-limited settle). Each is driven by the
    player's COMMANDED VELOCITY at contact -- the process principle: the object decides where it
    ends up, the touch only hands it energy.

    PREDICTION (what tools/touch_tests.py measures):
      1. the stone's post-contact speed scales with m_body/m_stone and it stops within the
         mu-derived braking distance v^2/(2*mu*g);
      2. the tuft deflects away from the player and recovers to rest in < 2 s, never diverging;
      3. the pile keeps a permanent footprint and every kicked grain settles (max grain speed
         < 1 cm/s at 3 s after contact);
      4. GRAB (E) picks the stone up inside arm's reach and drops it at the feet.

    FALSIFIER. Any class violating its own equation, OR any constant below tracing to neither a
    numbers.json nor a named citation.

PROVENANCE TABLE -- every constant in this file, one line each, PHYSICS or THE HUMAN:

    STONE
      diameter 0.35 m               THE HUMAN -- design placeholder ("a stone you can shove"); the
                                    operator moves it. (theGround's fractal_D governs the terrain
                                    grain sizes, not this set piece.)
      quartzite density 2,650 kg/m^3 PHYSICS -- Schoen 2011, "Physical Properties of Rocks"
                                    (quartzite 2.6-2.7 g/cm^3); the stone IS quartzite now --
                                    its albedo and its mass must be the same rock (F1 fired on
                                    the quartz-look/basalt-mass mismatch, 2026-08-03).
      stone mass 59.5 kg            PHYSICS -- derived: rho_quartzite x (4/3) pi r^3.
      friction mu = 0.841           PHYSICS -- derived: tan(theGround.repose_regolith_deg 40.03),
                                    stone-on-regolith Coulomb friction = the slope loose regolith
                                    holds. Read from theGround/numbers.json, never typed.
      body mass 94.504 kg           PHYSICS -- theHuman/numbers.json mass_kg (suited).
      contact margin 0.35 m         THE HUMAN -- v1: the body shoves, it is not blocked; the margin
                                    is a stand-in for hip/shoulder width and the operator tunes it.
      arm reach = 0.44 x height     PHYSICS -- ANSUR II anthropometry (US Army 2012; the repo
                                    already ingests it, tools/build_ansur_anchors.py): functional
                                    reach ~0.44 of stature. height_m from theHuman/numbers.json.
      waist height = com_height_m   PHYSICS -- theHuman/numbers.json (1.009 m): a carried load
                                    rides at the body's centre of mass.
      carry offset 0.5 m            THE HUMAN -- render placement, ahead-right of facing.
      drop offset 0.3 m             THE HUMAN -- render placement, "at the feet" but visible.

    TUFT
      13 blades, 0.4 m disk         DERIVED (was 60, a design placeholder) -- splat_ruler's
                                    measured footprint and disk projection: 13 blades x 19
                                    grains = coverage ~1 at the probe rig; 60 painted 4.7x
                                    over and blobbed (THE_VEGETATION_GEOMETRY.md, membrane 4).
                                    The aggregate spring is count-invariant -- physics unmoved.
      blade height 0.35 m           THE HUMAN -- design placeholder.
      blade diameter 1.6 mm         PHYSICS -- Kosmalla et al. 2025 (Earth Surf. Dynam. 13, 791):
                                    marram grass green-leaf outer diameter 1.57-1.63 mm, mean taken.
      blade Young's modulus 1.42 GPa  PHYSICS -- Kosmalla et al. 2025, 3-point bending of marram
                                    grass: measured E spans 1050-1910 MPa across green living parts
                                    (sprouts 1069-1162, stems 1049-1374, green leaves ~1910 MPa).
                                    A RANGE, so the GEOMETRIC MEAN sqrt(1050x1910) = 1416 MPa is
                                    used -- said plainly, per the brief.
      blade section I = pi d^4/64   PHYSICS (stated simplification) -- solid circular section; the
                                    source treats stems as hollow ellipses, a blade as solid.
      tissue density 1,000 kg/m^3   PHYSICS (stated assumption) -- fresh herbaceous tissue is
                                    mostly water; water's density is the physical constant.
      aggregate k = 45.3 s^-2       PHYSICS -- derived: cantilever scaling k_blade = 3EI/L^3 per
                                    blade, 60 blades in parallel, over the aggregate blade mass;
                                    omega_n = sqrt(k) = 6.73 rad/s.
      damping zeta = 0.8            THE HUMAN -- feel row, CONSTRAINED by the membrane: recovery to
                                    rest < 2 s without divergence (this gives ~0.9 s). Inter-blade
                                    friction in a tuft is what a single-blade damping measurement
                                    would not cover; the membrane's spec is the authority here.
      theta_max 60 deg              THE HUMAN -- how far a body flattens a tuft, by eye.
      blade display width 0.02 m    THE HUMAN -- render row: 12.5x the measured blade,
                                    legibility, not physics (as the pile's clod).
      grains per blade = 19         PHYSICS (derived) -- ceil(L/w)+1 over the two rows
                                    above: a blade reads as a LINE when its grain spacing
                                    <= the splat's own width (docs/THE_VEGETATION_
                                    GEOMETRY.md, 2026-08-04). 3 dots measured a smudge.
      blade shape = ball chain      PHYSICS (derived from the renderer) -- a blade is a
                                    1-D line; a line has no tangent plane, so the tangent
                                    DISC a normal selects (_p2s: 1.45x wide, 0.10x along)
                                    leaves 84% of a vertical blade undrawn. Zero normal =
                                    isotropic ball = a TUBE (docs/THE_VEGETATION_GEOMETRY.
                                    md, membrane 3). Lighting stays baked from up.

    PILE
      400 grains                    THE HUMAN -- design placeholder count.
      base radius 1.0 m             THE HUMAN -- design placeholder size.
      height 0.841 m                PHYSICS -- derived: base x tan(repose_regolith_deg): a granular
                                    cone cannot stand steeper than its own repose angle.
      grain d50 0.35 mm             PHYSICS -- theGround/numbers.json d_median_mm (the regolith's
                                    own median grain).
      grain solid density 2,650     PHYSICS -- derived: bulk_density 1537 / (1 - porosity 0.42),
                                    theGround/numbers.json.
      display clod 0.06 m           THE HUMAN -- render size: a 0.35 mm grain is a sub-pixel dot;
                                    each splat shows a CLOD, the physics still counts 400 grains.
                                    (Raised from 0.04 after the rung-3 blind read: at 3.2 m camera
                                    distance 4 cm clods merged into a faint patch, not a pile.)
      kick factors 0.6 / 0.4        THE HUMAN -- feel rows, per the brief: a kicked grain gets
                                    0.6 x the player's velocity plus 0.4 m/s up.
      kick radius 0.5 m             THE HUMAN -- how close a boot passes to scatter grains.
      settle threshold 1 cm/s       THE HUMAN -- the membrane's own settle criterion.
      grain friction mu = 0.841     PHYSICS -- same derived tan(repose): grain on regolith.
      layout seed 7                 THE HUMAN -- sampling only; any seed draws the same cone.

    SHARED
      gravity g                     PHYSICS -- walker.g, the planet's own GM/R^2, fifteen membranes up.
      sun / sky / bounce lighting   PHYSICS -- the exact beam + airlight + ground-bounce formula of
                                    walker.body_buffer, reused so one sun serves every object.
      exposure x2.0                 THE HUMAN -- walker._EXPOSURE, the camera's lens compensation
                                    (taste, same status as lit()'s tone), shared with the ground so
                                    object and terrain sit in the same photograph.
      stone albedo = quartz         PHYSICS -- theGround/numbers.json mineral_materials.quartz
                      rgb_mean                rgb_mean (0.710, 0.708, 0.642), material-genome scan:
                                    a quartzite stone in this ground's own mineral table, read live
                                    like the pile's mean. (The bare-rock palette this replaced is
                                    exposed BEDROCK -- a different claim than a loose stone.)
      veg albedo (0.20,0.27,0.14)   THE HUMAN -- render: walker.py's vegetation palette (a spatial
                                    mean of blades + soil; kept here for reference).
      tuft albedo (0.24,0.36,0.16)  THE HUMAN -- render: a dense tuft is PURE blade, not the
                                    ground's mean, so the blades sit toward the palette's green
                                    end; at palette-parity the tuft measured invisible (rung-3).
      pile albedo (0.55,0.54,0.44)  PHYSICS -- mean of theGround's measured mineral albedos
                                    (quartz/feldspar/oxide rgb_mean, material-genome scans).
      spawn positions               THE HUMAN -- level design placeholders, the operator's to move.

THE PLAYER IS NEVER BLOCKED (v1). The stone is shoved, the tuft bends away, the grains scatter --
the walker's own path is untouched. Blocking is a later membrane with its own falsifier.
"""
from __future__ import annotations

import math

import numpy as np

import walker as _wk          # height_at / _static / _load -- the carved ground is the truth

# -- the three measured/cited numbers this file cannot re-derive at runtime ----------------------
_RHO_QUARTZITE = 2650.0      # kg/m^3 -- Schoen 2011, quartzite 2.6-2.7 g/cm^3 (see provenance)
_BLADE_E = 1.416e9           # Pa -- Kosmalla et al. 2025, geometric mean of the 1050-1910 MPa range
_BLADE_D = 1.6e-3            # m  -- Kosmalla et al. 2025, green-leaf outer diameter, mean
_RHO_TISSUE = 1000.0         # kg/m^3 -- fresh tissue ~ water (stated assumption)

# -- design placeholders (THE HUMAN; the operator moves them) ------------------------------------
_STONE_D = 0.35
_TUFT_BLADES = 13            # DERIVED 2026-08-04 (docs/THE_VEGETATION_GEOMETRY.md, membrane 4):
                             # was 60, a design placeholder. tools/splat_ruler.py measured one
                             # grain's footprint (2.4-2.7x s = ~17.3 px2) and the disk's
                             # projection (~4,200 px) at the probe rig: 60 blades x 19 grains
                             # painted it 4.7x over -- a saturated blob no shape survives.
                             # 4200 / (19 x 17.3) = 12.8 -> 13 blades at coverage ~1. The
                             # aggregate spring is count-INVARIANT (k = N*k_blade / N*m_blade),
                             # so this moves the render row only; the physics is untouched.
_TUFT_DISK_R = 0.2           # the 0.4 m disk
_BLADE_L = 0.35
_BLADE_W = 0.02            # display width of a blade -- render row (THE HUMAN): 12.5x the
                           # measured 1.6 mm (Kosmalla 2025); legibility, not physics.
_GRAINS_PER_BLADE = math.ceil(_BLADE_L / _BLADE_W) + 1   # = 19. DERIVED (docs/
                           # THE_VEGETATION_GEOMETRY.md): a blade reads as a LINE when its
                           # grain spacing <= the splat's own width (0.0194 <= 0.02 m);
                           # 3 hand-placed dots measured a smudge at 3.2 m (rung 3).
_THETA_MAX = math.radians(60.0)
_PILE_GRAINS = 400
_PILE_R = 1.0
_KICK_V = 0.6                # of the player's velocity, handed to a kicked grain
_KICK_UP = 0.4               # m/s up
_KICK_R = 0.5
_SETTLE = 0.01               # m/s -- the membrane's settle criterion
_CLOD = 0.06                 # display size of one grain-splat (a clod, not a grain) -- THE HUMAN.
                             # Raised 0.04 -> 0.06 after the rung-3 blind read: at the 3.2 m
                             # third-person camera distance, 4 cm clods merged into a faint mush.
                             # Display only; the physics still counts 400 grains of d50 0.35 mm.

_VEG_ALB = np.array([0.20, 0.27, 0.14], np.float32)
# THE TUFT IS NOT THE GROUND'S MEAN. walker.py's veg palette is a spatial MEAN -- blades plus the
# soil between them, averaged at the 0.9 m grain. A dense tuft is PURE blade, and drawn at
# palette-parity it has zero contrast against its own mean: the rung-3 record and the 2026-08-03
# probe both measured it invisible. So the blades sit slightly toward the palette's high (green)
# end. THE HUMAN render row -- the physics (E, I, k, damping) is untouched.
_TUFT_ALB = np.array([0.24, 0.36, 0.16], np.float32)


def _ground_nums():
    st = _wk._static()
    return st["ground"], st["human"]


def _mu_repose() -> float:
    gnd, _ = _ground_nums()
    return math.tan(math.radians(float(gnd["repose_regolith_deg"])))


def _sun_light(w):
    """The one sun, the one sky -- the beam/airlight/ground-bounce formula of walker.body_buffer,
    so every touchable is lit by the same light as the ground it sits on."""
    (_f, nums) = _wk._load()
    S_rel = float(nums["terrain"]["S_earth"])
    sunv, alt = w.sun
    sun = np.array(sunv, np.float64)
    sun /= (np.linalg.norm(sun) + 1e-12)
    beam = max(0.0, math.sin(alt))
    sky = 0.09 + 0.16 * max(0.0, min(1.0, (math.degrees(alt) + 6.0) / 12.0))
    bounce = 0.5 * 0.22 * S_rel * beam
    return S_rel, sun, beam, sky, bounce


def _shade(b, albedo, w):
    from matter import lit
    S_rel, sun, beam, sky, bounce = _sun_light(w)
    lam = np.clip(b[:, 21:24] @ sun, 0.0, None)
    # one sun, one lens: the camera's exposure compensation (walker's THE HUMAN dial) admits the
    # same light here as on the ground the object rests on -- physics untouched, the lens opened.
    b[:, 16:19] = lit(albedo, _wk._EXPOSURE * (S_rel * beam * lam + sky + bounce),
                      e_ref=S_rel, tone=0.45)
    b[:, 19] = 0.95


class Stone:
    """RIGID. A quartzite sphere: shoved by momentum (m_body/m_stone along the contact normal),
    stopped by Coulomb friction at the regolith's own repose tangent. Carriable within arm's reach."""

    def __init__(self, x, y):
        gnd, hum = _ground_nums()
        self.r = _STONE_D / 2.0
        self.mass = _RHO_QUARTZITE * (4.0 / 3.0) * math.pi * self.r ** 3
        self.mu = _mu_repose()
        self.repose_deg = float(gnd["repose_regolith_deg"])
        self.m_body = float(hum["mass_kg"])
        self.reach = 0.44 * float(hum["height_m"])          # ANSUR functional reach
        self.waist = float(hum["com_height_m"])
        # THE STONE'S COLOUR IS THIS GROUND'S OWN MINERAL. theGround's mineral table carries
        # measured rgb_means (material-genome scans); a stone lying in this regolith reads as
        # quartzite -- pale quartz -- not the terrain's bare-rock palette (that palette is for
        # exposed bedrock faces, a different claim). Read live, like the pile's albedo mean.
        self._alb = np.array(gnd["mineral_materials"]["quartz"]["rgb_mean"], np.float32)
        self.x, self.y = float(x), float(y)
        self.z = _wk.height_at(self.x, self.y) + self.r
        self.vx = self.vy = 0.0
        self.carried = False

    def step(self, w, dt):
        """One tick. Returns True if anything visibly changed (the viewer re-uploads on it)."""
        if self.carried:
            # rides ahead-right of the facing at waist (CoM) height
            f = (-math.sin(w.yaw), math.cos(w.yaw))
            r = (math.cos(w.yaw), math.sin(w.yaw))
            d = ((f[0] + r[0]) / math.sqrt(2.0), (f[1] + r[1]) / math.sqrt(2.0))
            self.x, self.y = w.x + 0.5 * d[0], w.y + 0.5 * d[1]
            self.z = w.z + self.waist
            self.vx = self.vy = 0.0
            return True
        # CONTACT: the shove hands the stone momentum along the contact normal -- but only what
        # it does not already have (a stone outrunning the shove is not pushed again). The player
        # is never blocked: nothing here touches the walker.
        dx, dy = self.x - w.x, self.y - w.y
        dist = math.hypot(dx, dy)
        if 1e-9 < dist < self.r + 0.35:
            nx, ny = dx / dist, dy / dist
            cmd = w.vx * nx + w.vy * ny                    # commanded speed into the stone
            have = self.vx * nx + self.vy * ny
            dv = max(0.0, cmd - have) * (self.m_body / self.mass)
            if dv > 0.0:
                self.vx += dv * nx
                self.vy += dv * ny
        # COULOMB: |v| decays by mu*g*dt to zero -- never negative, never creeping.
        sp = math.hypot(self.vx, self.vy)
        if sp > 0.0:
            nsp = max(0.0, sp - self.mu * w.g * dt)
            if nsp == 0.0:
                self.vx = self.vy = 0.0
            else:
                self.vx *= nsp / sp
                self.vy *= nsp / sp
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z = _wk.height_at(self.x, self.y) + self.r
            return True
        return False

    def interact(self, w) -> bool:
        """E. Toggle carried -- inside arm's reach to pick up; anywhere to put down at the feet."""
        if self.carried:
            self.carried = False
            f = (-math.sin(w.yaw), math.cos(w.yaw))
            self.x, self.y = w.x + 0.3 * f[0], w.y + 0.3 * f[1]
            self.z = _wk.height_at(self.x, self.y) + self.r
            self.vx = self.vy = 0.0
            return True
        if math.hypot(self.x - w.x, self.y - w.y) <= self.reach:
            self.carried = True
            return True
        return False

    def buffer(self, w):
        from matter import blank, SOLID, surface_grain, fibonacci_sphere
        # n=40 -> 160, 2026-08-04, measured by tools/stone_legibility.py: at the blind read's
        # 3.2 m camera distance 40 splats read as a ~15 px faint smudge (stone_before.jpg) --
        # sparse dots, not a rock. RENDER ROW ONLY: the physics (mass, friction, impulse) is
        # untouched, and surface_grain rescales the splat size with n, so the sphere's SIZE
        # does not change -- only its solidity. THE HUMAN dial, legibility, F2's own rule
        # (fix the presentation physics, never the tolerance).
        n = 160
        d = fibonacci_sphere(n)
        b = blank(n)
        b[:, 0] = self.x + d[:, 0] * self.r
        b[:, 1] = self.y + d[:, 1] * self.r
        b[:, 2] = self.z + d[:, 2] * self.r
        b[:, 21:24] = d
        b[:, 20] = surface_grain(n, self.r)
        b[:, 11] = SOLID
        _shade(b, self._alb, w)
        return b

    def probe(self, w) -> str:
        state = "carried" if self.carried else f"{math.hypot(self.vx, self.vy):.2f} m/s"
        return (f"the stone -- {self.mass:.1f} kg of quartzite (Schoen 2011), "
                f"mu {self.mu:.2f} = tan({self.repose_deg:.2f} deg repose) -- {state}")


class Tuft:
    """GROWN. ~60 grass blades in a disk, read as ONE damped spring (the aggregate bend state):
    theta'' = k*(target - theta) - c*omega, k from cantilever scaling 3EI/L^3 with the measured
    grass modulus, semi-implicit Euler at the frame dt. Driven flat AWAY from a body standing in
    it; recovers to rest in < 2 s."""

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        # the aggregate spring, derived (see the provenance table)
        I = math.pi * _BLADE_D ** 4 / 64.0
        k_blade = 3.0 * _BLADE_E * I / _BLADE_L ** 3                      # N/m, one blade
        m_blade = _RHO_TISSUE * math.pi * (_BLADE_D / 2.0) ** 2 * _BLADE_L
        m_agg = _TUFT_BLADES * m_blade
        self.k = _TUFT_BLADES * k_blade / m_agg                           # s^-2
        self.omega_n = math.sqrt(self.k)
        zeta = 0.8                                                        # THE HUMAN, membrane-capped
        self.c = 2.0 * zeta * self.omega_n
        self.theta = 0.0             # bend angle, rad, along bend_dir
        self.omega = 0.0
        self.bend_dir = (0.0, 1.0)
        # the blades' feet: a golden-angle scatter over the disk (sampling only -- THE HUMAN seed)
        i = np.arange(_TUFT_BLADES) + 0.5
        rr = _TUFT_DISK_R * np.sqrt(i / _TUFT_BLADES)
        ph = i * math.pi * (3.0 - 5.0 ** 0.5)
        self._bx = self.x + rr * np.cos(ph)
        self._by = self.y + rr * np.sin(ph)

    def step(self, w, dt):
        dx, dy = self.x - w.x, self.y - w.y
        d = math.hypot(dx, dy)
        if d < _TUFT_DISK_R and d > 1e-9:
            self.bend_dir = (dx / d, dy / d)         # flat AWAY from the body
            target = _THETA_MAX
        else:
            target = 0.0
        acc = self.k * (target - self.theta) - self.c * self.omega
        self.omega += acc * dt
        self.theta += self.omega * dt
        return abs(self.theta) > math.radians(0.5) or abs(self.omega) > 1e-3

    def interact(self, w) -> bool:
        return False                     # grass does not care about E

    def buffer(self, w):
        from matter import blank, SOLID
        n = _TUFT_BLADES
        g = _GRAINS_PER_BLADE
        b = blank(g * n)
        gz = _wk.heights_at(self._bx, self._by)
        st, ct = math.sin(self.theta), math.cos(self.theta)
        dx, dy = self.bend_dir
        for k in range(g):                     # the blade is a LINE: spacing <= splat width
            f = k / (g - 1)
            sl = slice(k * n, (k + 1) * n)
            b[sl, 0] = self._bx + f * _BLADE_L * st * dx
            b[sl, 1] = self._by + f * _BLADE_L * st * dy
            b[sl, 2] = gz + f * _BLADE_L * ct
        b[:, 21:24] = (0.0, 0.0, 1.0)            # the LIGHTING claim: blades lit as grass
        b[:, 20] = _BLADE_W
        b[:, 11] = SOLID
        _shade(b, _TUFT_ALB, w)
        # the SHAPE claim, AFTER the shade: a blade is a 1-D line, and a line has no
        # tangent plane. A normal makes the renderer draw a tangent DISC (_DISC_WIDE
        # across, _DISC_THIN along the normal -- gpu_pipeline.py _p2s): 0.0032 m of
        # z-extent against the 0.0194 m grain spacing = 84% of every vertical blade
        # undrawn (membrane 1, fired), or the cull eating half the blades (membrane 2,
        # fired). A ZERO normal is the isotropic ball: a chain of balls is a TUBE,
        # contiguous from every viewpoint, un-cullable -- grass has no back face
        # (docs/THE_VEGETATION_GEOMETRY.md, membrane 3).
        b[:, 21:24] = 0.0
        return b

    def probe(self, w) -> str:
        return (f"the tuft -- {_TUFT_BLADES} blades, E {_BLADE_E / 1e9:.2f} GPa (Kosmalla 2025), "
                f"k {self.k:.1f} s^-2 -- bent {math.degrees(self.theta):.0f} deg")


class Pile:
    """GRANULAR. 400 grains in a cone whose height IS the repose angle made visible. A passing
    boot kicks the near grains; they fly under the planet's g, land on the cone profile (or the
    ground past the base), and STAY -- the footprint is permanent, the deformed state is the pile."""

    def __init__(self, x, y):
        gnd, _ = _ground_nums()
        self.x, self.y = float(x), float(y)
        self.R = _PILE_R
        self.repose_deg = float(gnd["repose_regolith_deg"])
        self.h = self.R * math.tan(math.radians(self.repose_deg))
        self.mu = _mu_repose()
        d_m = float(gnd["d_median_mm"]) / 1000.0
        rho_s = float(gnd["bulk_density"]) / (1.0 - float(gnd["porosity"]))
        self.grain_mg = rho_s * (4.0 / 3.0) * math.pi * (d_m / 2.0) ** 3 * 1e6
        self.d_mm = float(gnd["d_median_mm"])
        # fill the cone: uniform in VOLUME, interior by construction (r/R <= 1 - z/h at its layer)
        rng = np.random.default_rng(7)
        n = _PILE_GRAINS
        zf = rng.random(n) ** (1.0 / 3.0)
        rad = self.R * (1.0 - zf) * np.sqrt(rng.random(n))
        ang = rng.random(n) * (2.0 * math.pi)
        self.px = self.x + rad * np.cos(ang)
        self.py = self.y + rad * np.sin(ang)
        self.pz = _wk.heights_at(self.px, self.py) + zf * self.h
        self.vx = np.zeros(n)
        self.vy = np.zeros(n)
        self.vz = np.zeros(n)
        self.home = np.stack([self.px, self.py, self.pz], axis=1).copy()
        # the pile's colour is theGround's own measured minerals, averaged
        mins = gnd["mineral_materials"]
        self._alb = np.mean([mins[m]["rgb_mean"] for m in mins], axis=0).astype(np.float32)

    def surface(self, px, py):
        """The cone profile over the carved ground: repose-height at the centre, ground past the base."""
        r = np.hypot(px - self.x, py - self.y)
        return _wk.heights_at(px, py) + self.h * np.clip(1.0 - r / self.R, 0.0, None)

    def step(self, w, dt):
        n = _PILE_GRAINS
        # THE KICK: settled grains within a boot's reach of a MOVING player are scattered.
        ps = math.hypot(w.vx, w.vy)
        if ps > 0.05:
            dx, dy = self.px - w.x, self.py - w.y
            settled = (self.vx ** 2 + self.vy ** 2 + self.vz ** 2) < _SETTLE ** 2
            kick = (dx * dx + dy * dy < _KICK_R ** 2) & settled
            if kick.any():
                self.vx[kick] = w.vx * _KICK_V
                self.vy[kick] = w.vy * _KICK_V
                self.vz[kick] = _KICK_UP
        moving = (self.vx ** 2 + self.vy ** 2 + self.vz ** 2) > 0.0
        if not moving.any():
            return False
        idx = np.nonzero(moving)[0]
        # ballistic under the planet's own g
        self.vz[idx] -= w.g * dt
        self.px[idx] += self.vx[idx] * dt
        self.py[idx] += self.vy[idx] * dt
        self.pz[idx] += self.vz[idx] * dt
        s = self.surface(self.px[idx], self.py[idx])
        landed = self.pz[idx] <= s
        if landed.any():
            li = idx[landed]
            self.pz[li] = s[landed]
            self.vz[li] = 0.0
            # slide with Coulomb friction, then settle
            sp = np.hypot(self.vx[li], self.vy[li])
            nsp = np.maximum(0.0, sp - self.mu * w.g * dt)
            scale = np.where(sp > 0.0, nsp / np.maximum(sp, 1e-12), 0.0)
            self.vx[li] *= scale
            self.vy[li] *= scale
            slow = nsp < _SETTLE
            self.vx[li[slow]] = 0.0
            self.vy[li[slow]] = 0.0
        # anything still creeping below the criterion stops dead
        creep = (self.vx ** 2 + self.vy ** 2 + self.vz ** 2) < _SETTLE ** 2
        self.vx[creep] = 0.0
        self.vy[creep] = 0.0
        self.vz[creep] = 0.0
        return True

    def interact(self, w) -> bool:
        return False                     # you cannot pick up a pile with one key

    def max_speed(self) -> float:
        return float(np.sqrt((self.vx ** 2 + self.vy ** 2 + self.vz ** 2).max()))

    def buffer(self, w):
        from matter import blank, SOLID
        n = _PILE_GRAINS
        b = blank(n)
        b[:, 0], b[:, 1], b[:, 2] = self.px, self.py, self.pz
        b[:, 21:24] = (0.0, 0.0, 1.0)
        b[:, 20] = _CLOD
        b[:, 11] = SOLID
        _shade(b, self._alb, w)
        return b

    def probe(self, w) -> str:
        moved = float(np.sqrt(((np.stack([self.px, self.py, self.pz], axis=1)
                                - self.home) ** 2).sum(axis=1)).max())
        return (f"the pile -- {_PILE_GRAINS} grains of regolith (d50 {self.d_mm} mm, "
                f"{self.grain_mg:.2f} mg each), repose cone {self.h:.2f} m tall -- "
                f"footprint {moved:.2f} m")


def spawn():
    """The three placeholders, near spawn. Placement is level design -- THE HUMAN's, to move."""
    return [Stone(3.0, 5.0), Tuft(-3.5, 8.0), Pile(4.0, 12.0)]


def touchables_buffer(objs, w):
    return np.concatenate([o.buffer(w) for o in objs], axis=0)


def hud_line(objs, w) -> str:
    """The HUD's one touch line: the affordance when E would do something, else the nearest
    object's probe (within 6 m -- a HUD choice, not a physics)."""
    stone = next((o for o in objs if isinstance(o, Stone)), None)
    if stone is not None:
        if stone.carried:
            return f"E: put down the stone ({stone.mass:.1f} kg)"
        if math.hypot(stone.x - w.x, stone.y - w.y) <= stone.reach:
            return f"E: pick up the stone ({stone.mass:.1f} kg)"
    best, bd = None, 6.0
    for o in objs:
        d = math.hypot(o.x - w.x, o.y - w.y)
        if d < bd:
            best, bd = o, d
    return best.probe(w) if best is not None else ""
