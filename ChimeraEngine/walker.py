"""walker.py -- standing inside aTerrain and walking on it.

Every membrane above this is looked AT. This is the first one you are looked OUT of.

WHY IT NEEDS ITS OWN BUFFER. `aTerrain` is 12 km across on a 128x128 grid, so one cell is 93.8 m
and a person is 1.78 m: rendered as it stands, every grain of ground would be FIFTY-TWO TIMES the
player's height, and you would be walking between boulders the size of office blocks. The membrane
is not wrong -- at its own framing 94 m is a pixel. It is the wrong LEVEL OF DETAIL to stand on.

So this does what the hierarchy already says to do: take the SHAPE from `aTerrain` (its carved
height field, interpolated) and the GRAIN from `theGround` (stones at the fractal size distribution
its law derived), and build a buffer centred on the player -- fine underfoot, coarse to the horizon.
That is LOD of meaning at walking scale: the same derivation read at the resolution a body needs.

EVERY NUMBER THE BODY MOVES BY IS DERIVED, none of them typed here:

    walk / run speed   theHuman.comfortable_speed_ms, walk_run_ms   (Froude, Fr = 0.5)
    jump               theHuman.jump_height_m                       (muscle work / g)
    gravity            aRockyPlanet.g                               (GM/R^2, fifteen membranes up)
    eye height         theHuman: 0.94 of stature
    ground under foot  aTerrain's carved surface

Change the planet and the walk changes with it, because there is nothing here to change separately.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_STORY = _HERE.parent / "story"
_TERRAIN = (_STORY / "theZero/theHorizon/theEmptying/theCooling/theCloud/theGalaxy/theSolarSystem"
            / "thePlanets/theRockyPlanet/aRockyPlanet/aBlueWorld/theTerrain/aTerrain")

_FIELD = None       # (z, dx, patch_m, acc, slope) -- carved once, then sampled
_NUMS = None


_STATIC = None      # laws + numbers, loaded once -- no carving in here
_FIELDS = {}        # (latq, lonq) -> ((z, dx, patch, acc, slope), nums-with-place)  [None = default]
_ACTIVE = None      # which place height_at()/scene_around() read -- set by Walker


def _static():
    """Everything that does NOT depend on the place: the story's numbers and its law modules.
    Loaded once; carving (the expensive, per-place part) lives in _load()."""
    global _STATIC
    if _STATIC is not None:
        return _STATIC
    import importlib.util
    import sys
    sys.path.insert(0, str(_STORY))

    def _mod(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m

    nums = json.loads((_TERRAIN / "numbers.json").read_text())
    ground = json.loads((_TERRAIN / "theGround" / "numbers.json").read_text())
    human = json.loads((_TERRAIN / "theGround" / "theHuman" / "numbers.json").read_text())
    planet = json.loads((_TERRAIN.parent.parent / "numbers.json").read_text())   # aBlueWorld: the air
    # theHumanClock: the OTHER end of the ladder -- the band of durations a player can feel.
    # The walker's clock rate is DEFINED against it, not asserted (see Walker.__init__).
    hclock = json.loads((_STORY / "theZero/theHorizon/theClock/theHumanClock" / "numbers.json").read_text())
    _STATIC = {
        "terrain": nums, "ground": ground, "human": human, "planet": planet, "human_clock": hclock,
        # the terrain law (the carve) -- run per place in _load()
        "terrain_law": _mod("aTerrain_phys", _TERRAIN / "physics.py"),
        # theGround's OWN law, imported rather than restated. `soil_depth(slope_deg)` decides
        # whether this surface shows soil or bedrock; a re-derived copy would drift on first edit.
        "ground_law": _mod("theGround_phys", _TERRAIN / "theGround" / "physics.py"),
        # theHuman's law: the body itself. Third person does not build a figure -- it borrows the
        # membrane's own emit(), so the person you watch IS the chapter's stick figure, derived.
        # aHUMAN, not theHuman: the parent draws a stick figure on purpose (it claims only the
        # skeleton it derived); the INSTANCE knows a suit's outside and can draw a surface. Third
        # person shows the person, so it borrows the instance's body.
        "human_law": _mod("aHuman_phys", _TERRAIN / "theGround" / "theHuman" / "aHuman" / "physics.py"),
        "suited": json.loads((_TERRAIN / "theGround" / "theHuman" / "aHuman" / "numbers.json").read_text()),
        # aBlueWorld's law, for temperature_at() -- ITS OWN DOCSTRING is the authority here:
        # "THE ONE LATITUDE PROFILE THIS STORY USES, and every membrane below must read it from
        # here... snow is a temperature, not a latitude." So the place picker asks the planet.
        "planet_law": _mod("aBlueWorld_phys", _TERRAIN.parent.parent / "physics.py"),
    }
    return _STATIC


def _place_key(lat, lon):
    """None means THE DEFAULT PLACE -- the story's own aTerrain, byte-identical. Anything else is
    quantised to 0.1 degree so a slider's float jitter cannot mint a second copy of one hill."""
    if lat is None and lon is None:
        return None
    st = _static()
    d_lat = float(st["terrain"]["latitude_deg"])
    la = d_lat if lat is None else float(lat)
    lo = 0.0 if lon is None else float(lon)
    la = max(-85.0, min(85.0, la))
    lo = ((lo + 180.0) % 360.0) - 180.0
    key = (round(la, 1), round(lo, 1))
    # picking the default place by hand IS the default place
    if key == (round(d_lat, 1), 0.0):
        return None
    return key


def _place_seed(key):
    """The ground under a place is DETERMINISTIC: the seed is a stable mix of the quantised
    coordinates, so walking back to (61.5, 12.0) next year finds the same hills."""
    if key is None:
        return 2029                          # the story's own patch, unchanged since it was carved
    la, lo = key
    return (int((la + 90.0) * 10) * 73856093 ^ int((lo + 180.0) * 10) * 19349663) & 0x7FFFFFFF


def place_info(lat, lon):
    """What the planet already knows about a place, WITHOUT carving it (this feeds the picker's
    label, so it must be instant). Temperature from the planet's one latitude law; snow where
    that law says water is solid; the midnight sun where the derived tilt says the sun can miss
    the horizon. Nothing here is invented -- it is aBlueWorld's own numbers, read at a latitude."""
    st = _static()
    p = st["planet"]
    la = float(st["terrain"]["latitude_deg"]) if lat is None else float(lat)
    la = max(-85.0, min(85.0, la))
    T = float(st["planet_law"].temperature_at(float(p["T_surface"]), math.sin(math.radians(abs(la)))))
    eps = float(p["obliquity_effective_deg"])
    return {
        "lat": la,
        "lon": 0.0 if lon is None else float(lon),
        "T_C": T - 273.15,
        "snow": T < 273.15,
        "ice_line_lat_deg": float(p["ice_line_lat_deg"]),
        "polar_circle_lat_deg": 90.0 - eps,
        "midnight_sun": abs(la) >= 90.0 - eps,
        "sun_overhead": abs(la) <= eps,
    }


def _load():
    """The ACTIVE place's carved field + numbers. Cached per place: carving is ~13 s of erosion,
    so each place pays it once and the default place is pre-paid at server start."""
    global _FIELDS
    key = _ACTIVE
    if key in _FIELDS:
        return _FIELDS[key]
    st = _static()
    nums = st["terrain"]
    n, dx = int(nums["grid"]), float(nums["cell_m"])
    rng = np.random.default_rng(_place_seed(key))
    mod = st["terrain_law"]
    z, recv, acc, slope = mod._carve(mod._red_surface(n, rng, 3.0), dx, 500, rng)

    info = place_info(key[0] if key else None, key[1] if key else None)
    merged = dict(st)
    merged["place"] = info
    _FIELDS[key] = ((z, dx, float(nums["patch_m"]), acc.reshape(n, n), slope.reshape(n, n)), merged)
    return _FIELDS[key]


def heights_at(X, Y):
    """THE GROUND UNDER A FOOT, bilinear between the four cells around it -- for whole arrays.

    The carved field is the truth; between samples the surface is the plane those four corners
    define. At 94 m spacing that is smooth over a stride, which is why a person walking does not
    feel the grid -- and why the fine detail below is scattered ON this surface rather than
    replacing it.

    ONE IMPLEMENTATION, and the scalar `height_at` below is a call into it. A separate scalar copy
    is how a foot ends up standing on a slightly different surface than the one being drawn, and
    that gap is invisible until the body floats."""
    (z, dx, patch, _acc, _sl), _ = _load()
    n = z.shape[0]
    fx = np.clip((np.asarray(X, dtype=np.float64) + patch / 2.0) / dx, 0.0, n - 1.001)
    fy = np.clip((np.asarray(Y, dtype=np.float64) + patch / 2.0) / dx, 0.0, n - 1.001)
    # EACH FRACTION BELONGS TO ITS OWN AXIS. This used to read `ty, tx = fy - j0, fx - i0` -- the
    # row fraction measured against the COLUMN index and vice versa. At the middle of the patch
    # fx == fy and the swap cancels exactly, so the spawn point (0, 0) and everything near it read
    # correct; at the patch edge it stopped interpolating and started EXTRAPOLATING, and returned
    # 13,414 m on a field whose true maximum is 451 m. That is what put the far shell in the sky.
    j0 = fx.astype(np.int64)          # column index <- x
    i0 = fy.astype(np.int64)          # row index    <- y
    tx = fx - j0                      # how far along the column pair
    ty = fy - i0                      # how far down the row pair
    z00, z01 = z[i0, j0], z[i0, j0 + 1]
    z10, z11 = z[i0 + 1, j0], z[i0 + 1, j0 + 1]
    top = z00 * (1 - tx) + z01 * tx
    bot = z10 * (1 - tx) + z11 * tx
    return top * (1 - ty) + bot * ty


def height_at(x, y):
    """The same surface, for one point."""
    return float(heights_at(np.array([x]), np.array([y]))[0])


def gradients_at(X, Y, h=4.0):
    """The gradient over a baseline of `h` -- and the baseline is an argument because A SLOPE IS
    SCALE-DEPENDENT. Shading a 115 m grain with a 4 m gradient reads as noise on the horizon: the
    grain covers a hillside and is being lit as though it were a pebble on one."""
    zx = (heights_at(X + h, Y) - heights_at(X - h, Y)) / (2 * h)
    zy = (heights_at(X, Y + h) - heights_at(X, Y - h)) / (2 * h)
    return zx, zy


def slope_at(x, y, h=4.0):
    """What a foot has to hold onto, here."""
    zx, zy = gradients_at(np.array([x]), np.array([y]), h)
    return float(zx[0]), float(zy[0])


def _hash01(ix, iy, salt):
    """A spatial hash that is actually decorrelated on an integer lattice -- a 32-bit avalanche mix
    of the two cell indices. The float trick (`frac(sin(dot(p,k))*43758)`) is written for continuous
    UVs and paints visible fringes when handed a grid, which is exactly what it did here."""
    h = (ix.astype(np.uint64) * np.uint64(73856093)) ^ (iy.astype(np.uint64) * np.uint64(19349663))         ^ np.uint64(salt * 83492791)
    h ^= h >> np.uint64(33); h *= np.uint64(0xff51afd7ed558ccd)
    h ^= h >> np.uint64(29); h *= np.uint64(0xc4ceb9fe1a85ec53)
    h ^= h >> np.uint64(32)
    return (h >> np.uint64(11)).astype(np.float64) / float(1 << 53)


class Walker:
    """A body on that ground. Its numbers come from theHuman and the planet; none are chosen here."""

    def __init__(self, lat=None, lon=None):
        # WHERE. Setting the module's active place is what points height_at()/scene_around() at
        # this walker's own carved field. One walker per server; the seam is explicit.
        global _ACTIVE
        _ACTIVE = _place_key(lat, lon)
        (_z, _dx, patch, _a, _s), nums = _load()
        h = nums["human"]
        place = nums["place"]
        self.g = float(h["g"])
        self.walk = float(h["comfortable_speed_ms"])
        self.run = float(h["walk_run_ms"])
        self.jump_v = math.sqrt(2.0 * self.g * float(h["jump_height_m"]))
        # READ, NOT TYPED. This was `0.94 * height` -- human anatomy asserted inside a viewer, where
        # no audit reaches it. theHuman derives it now, from a measured 0.936 of stature.
        self.eye = float(h["eye_height_m"])
        self.repose_deg = float(_static()["ground"]["repose_regolith_deg"])
        self.height_m = float(h["height_m"])
        self.patch = patch

        # ── THE CLOCK, AT HUMAN SPEED ────────────────────────────────────────────────────────────
        # Every other membrane in this story is GEARED: an aeon of collapse compressed into a movie
        # you can sit through. This is the one rung where that would be a lie, because the person is
        # standing in it -- so the clock runs 1:1, one second per second, and the sun crosses the sky
        # at exactly the rate this planet's own rotation says it does. That is what theHumanClock's
        # bottom rung MEANS: no gearing left to apply.
        #
        # It starts at the epoch theHuman declares -- 2076, 09:00 local -- because a game has to
        # begin somewhere and when is a human's call, not a planet's.
        self.day_s = float(h["day_s"])
        self.year_s = float(h["year_s"])
        self.days_per_year = float(h["days_per_year"])
        self.epoch_year = float(h["epoch_year"])
        # THE PLACE decides the latitude; the story's aTerrain is simply the default place. The
        # sun, the seasons, the daylight and the snow all follow from this one number plus the
        # planet's own laws -- nothing else about the place is free to disagree.
        self.lat = math.radians(float(place["lat"]))
        self.lat_deg = float(place["lat"])
        self.lon_deg = float(place["lon"])
        self.T_here_C = float(place["T_C"])
        self.snow = bool(place["snow"])
        self.eps = math.radians(float(h["obliquity_deg"]))
        # ONE CLOCK, counted from this world's northern spring equinox -- so it carries the season
        # AND the hour in a single number, and there is no second timeline to fall out of step.
        # Whole days plus an hour: the year is 383.21 days, so a bare year-FRACTION lands at an
        # arbitrary time of day and "09:00" came out as 04:16.
        self.clock = float(h["start_day"]) * self.day_s + float(h["start_time_s"])
        # THE RATE IS theHumanClock'S ANSWER, NOT A SETTING. That membrane's whole claim is that a
        # player can only feel events between band_lo (0.04 s) and band_hi (10 s), so every rhythm
        # in the game must be GEARED into that band -- a star needs 176.9x. The rhythm of THIS
        # membrane is one stride, and the chain that sets it runs through the solar system: the
        # star's mass fixes g, g fixes the pendulum, the pendulum fixes the stride at 3.8 s --
        # which is already INSIDE the band. A rhythm already in the band needs no gear, so play
        # is exactly 1:1 -- derived, and it would stop being 1 if the chain above ever pushed the
        # stride out of the band.
        hc = nums["human_clock"]
        stride_s = float(h["duration_s"])
        if stride_s > float(hc["band_hi_s"]):
            self.rate = stride_s / float(hc["band_hi_s"])      # too slow to feel: compress
        elif stride_s < float(hc["fusion_s"]):
            self.rate = stride_s / float(hc["fusion_s"])      # too fast to see: stretch
        else:
            self.rate = 1.0                                    # the stride lives in the band

        self.x, self.y = 0.0, 0.0
        self.z = height_at(0.0, 0.0)
        self.vz = 0.0
        self.vx, self.vy = 0.0, 0.0     # the last commanded horizontal velocity -- the gait's
                                        # direction picker (A3) reads this, not the keys
        self.on_ground = True
        self.yaw = 0.0                 # radians, 0 = +Y  (the CAMERA's facing)
        self.body_yaw = 0.0            # the FIGURE's facing -- eased toward velocity when moving,
                                       # back toward the camera at rest (velocity-facing, A1)
        self.pitch = 0.0
        self.crouch = 0.0
        self.dist = 0.0                # ground actually covered -- the gait phase reads THIS

    def look(self, dyaw, dpitch):
        """RADIANS, like the state it moves -- the caller owns sensitivity, because how far a hand
        should push a view is a preference, not a physics. Pitch stops just short of straight up
        and down (1.45 rad = 83 deg) so the horizon can never invert."""
        self.yaw = (self.yaw - dyaw) % (2 * math.pi)
        self.pitch = max(-1.45, min(1.45, self.pitch - dpitch))

    def move(self, fwd, strafe, sprint, jump, crouch, dt):
        """COMMAND THE PROCESS, NOT THE POSITION -- the operator's control law. The keys ask for an
        EFFORT in a direction; where the body ends up is whatever the ground allows."""
        speed = (self.run if sprint else self.walk) * (0.45 if crouch else 1.0)
        c, s = math.cos(self.yaw), math.sin(self.yaw)
        # forward is +Y rotated by yaw; strafe is its right-hand normal
        vx = (fwd * -s + strafe * c) * speed
        vy = (fwd * c + strafe * s) * speed
        # THE STICK'S DEFLECTION IS THE SPEED (the operator's analog law). A full key press is
        # magnitude 1 -- full speed, diagonals included; a thumbstick at half deflection is half
        # speed. This used to normalize ANY nonzero input to full speed, which killed the analog.
        mag = math.hypot(fwd, strafe)
        if mag > 0.0:
            scale = min(1.0, mag) / mag
            vx, vy = vx * scale, vy * scale
        self.vx, self.vy = vx, vy       # the gait direction picker (A3) reads the COMMAND

        ox, oy = self.x, self.y
        nx = max(-self.patch / 2 + 4, min(self.patch / 2 - 4, self.x + vx * dt))
        ny = max(-self.patch / 2 + 4, min(self.patch / 2 - 4, self.y + vy * dt))

        # THE BODY FACES WHERE IT GOES, not where the camera looks (the operator's 360-degree
        # law: walking any direction, the figure must turn to walk THAT way). The camera is
        # `yaw`; the body's own facing is `body_yaw`, eased toward the velocity heading while
        # moving and back toward the camera when standing still -- the blend every third-person
        # game does, stated once here. Before this, the figure's legs did a forward gait while
        # it slid sideways (the operator measured it at 1% of a human).
        mvx, mvy = vx, vy
        if abs(mvx) + abs(mvy) > 1e-9:
            # atan2 (0 = +X) -> the walker's yaw convention (0 = +Y): subtract pi/2
            heading = math.atan2(mvy, mvx) - math.pi / 2.0
            d_yaw = (heading - self.body_yaw + math.pi) % (2.0 * math.pi) - math.pi
            rate = 10.0
            self.body_yaw += max(-rate * dt, min(rate * dt, d_yaw))
        else:
            d_yaw = (self.yaw - self.body_yaw + math.pi) % (2.0 * math.pi) - math.pi
            rate = 3.0
            self.body_yaw += max(-rate * dt, min(rate * dt, d_yaw))

        # A SLOPE YOU CANNOT STAND ON IS A SLOPE YOU CANNOT WALK UP, and the limit is the angle of
        # repose of the stuff underfoot: past it, loose material slides and so do you.
        #
        # THIS USED TO BE A TYPED 38.0 under a comment claiming it was "the ground's own repose angle,
        # the same number the hillslopes were built with". It was neither -- theGround derives 40.03
        # for regolith and aTerrain 33.0 for loose rock, and 38 is not either of them. A literal
        # wearing a comment, in a file no audit covers, which is exactly how one survives.
        #
        # It reads theGround's REGOLITH angle, because that is what a boot is standing in. The
        # bedrock angle governs the hillside's shape, not a foot's grip on it.
        zx, zy = slope_at(nx, ny)
        grade = math.degrees(math.atan(math.hypot(zx, zy)))
        if grade < self.repose_deg or not self.on_ground:
            self.x, self.y = nx, ny

        # THE LEGS MOVE WHEN THE GROUND DOES. Distance is measured off the position that survived
        # the slope gate, so walking into a wall does not pump the stride.
        self.dist += math.hypot(self.x - ox, self.y - oy)

        gz = height_at(self.x, self.y)
        if jump and self.on_ground:
            self.vz = self.jump_v
            self.on_ground = False
        if not self.on_ground:
            self.vz -= self.g * dt
            self.z += self.vz * dt
            if self.z <= gz:
                self.z, self.vz, self.on_ground = gz, 0.0, True
        else:
            self.z = gz
        self.crouch += (( -0.35 if crouch else 0.0) - self.crouch) * min(1.0, 10.0 * dt)
        self.clock += dt * self.rate        # rate 1 = a second is a second; >1 = the declared gear

    @property
    def eye_pos(self):
        return (self.x, self.y, self.z + self.eye + self.crouch)

    @property
    def sun(self):
        """WHERE THE SUN IS, RIGHT NOW -- the standard solar-position triangle, run on this world's
        own day length and this membrane's latitude. Not a lighting setting: move the clock and it
        moves, because it is the same equation theHuman used to state the opening altitude."""
        decl = self.declination
        H = 2.0 * math.pi * ((self.clock % self.day_s) / self.day_s) - math.pi   # 0 at local noon
        sa = (math.sin(decl) * math.sin(self.lat)
              + math.cos(decl) * math.cos(self.lat) * math.cos(H))
        alt = math.asin(max(-1.0, min(1.0, sa)))
        az = math.atan2(-math.cos(decl) * math.sin(H),
                        math.sin(decl) * math.cos(self.lat)
                        - math.cos(decl) * math.sin(self.lat) * math.cos(H))
        ca = math.cos(alt)
        return (ca * math.sin(az), ca * math.cos(az), math.sin(alt)), alt

    @property
    def declination(self):
        """WHERE THE SUN IS IN THE YEAR -- the tilt projected onto how far round the orbit this world
        has got. Zero at the equinoxes, the whole tilt at the solstices. It is the entire mechanism
        of seasons in one line, and it is live: the clock runs 1:1, so standing here long enough
        genuinely moves it. (Long enough is a long time -- a season on this world is 96 days.)"""
        return math.asin(math.sin(self.eps) * math.sin(2.0 * math.pi * (self.clock / self.year_s)))

    def season(self):
        """Which quarter of its own year, named from the declination rather than a calendar."""
        f = (self.clock / self.year_s) % 1.0
        return ("spring", "summer", "autumn", "winter")[int(f * 4) % 4]

    def daylight_h(self):
        """How long today is here. The clamp on the half-day angle is polar night at one end and
        midnight sun at the other -- neither is written in, both are what the clamp means."""
        x = -math.tan(self.lat) * math.tan(self.declination)
        return math.acos(min(1.0, max(-1.0, x))) / math.pi * (self.day_s / 3600.0)

    def local_time(self):
        """The clock as a person would read it: which day of this world's year, and what o'clock."""
        day = int((self.clock % self.year_s) // self.day_s)
        f = (self.clock % self.day_s) / self.day_s * 24.0
        return day, int(f), int((f % 1.0) * 60)

    def readout(self):
        day, hh, mm = self.local_time()
        zx, zy = slope_at(self.x, self.y)
        return {"x": round(self.x, 1), "y": round(self.y, 1),
                "elev": round(self.z, 1),
                "slope": round(math.degrees(math.atan(math.hypot(zx, zy))), 1),
                "g": round(self.g, 2),
                "walk": round(self.walk, 2), "run": round(self.run, 2),
                "day": day, "hh": hh, "mm": mm, "year": int(self.epoch_year),
                "dpy": int(self.days_per_year),
                "rate": self.rate,
                "lat": round(self.lat_deg, 1), "lon": round(self.lon_deg, 1),
                "T_C": round(self.T_here_C, 1), "snow": self.snow,
                "sun_alt": round(math.degrees(self.sun[1]), 1),
                "season": self.season(),
                "decl": round(math.degrees(self.declination), 1),
                "daylight": round(self.daylight_h(), 1)}


# ── the ground you actually see, built around wherever the player is ─────────────────────────────
#
# A GEOMETRY CLIPMAP, and the reason is a measurement, not a preference.
#
# The first version was TWO SHELLS: 0.45 m samples out to 90 m, then 80 m samples to the horizon.
# The render showed a hard diagonal seam straight across the picture -- a 90x jump in grain size
# with nothing between, which is what a two-shell LOD looks like from inside. It is invisible from
# orbit because the whole shell is a pixel, and unmissable from a body's eye height.
#
# So: nested square rings, each one DOUBLE the spacing of the ring inside it. Two things follow, and
# both matter more than they look:
#
#  * A GRAIN SUBTENDS ROUGHLY THE SAME ANGLE EVERYWHERE. Screen size goes as size/distance; doubling
#    the size every time the distance doubles holds that ratio flat. The seam cannot be loud because
#    the worst discontinuity anywhere is a factor of two.
#  * THE GRID IS ANCHORED TO THE WORLD, NOT TO THE PLAYER. Each ring snaps to a multiple of its own
#    spacing, so walking slides the rings over stationary ground instead of dragging every grain
#    along with you. A player-centred grid makes the whole surface CRAWL -- the ground appears to
#    flow underfoot, which reads as motion sickness and is the classic failure of radial LOD.
#
# Cost is logarithmic: each ring holds the same number of grains, and 8 rings reach 6 km from 0.9 m.
_RING_N = 48            # half-width of every ring, in cells -- 8 rings * ~27k = the same budget
_RING_LEVELS = 8        # doubling 8 times: 0.9 m underfoot to 115 m at the horizon
# THE FINEST SPACING IN THE CLIPMAP, and it is a RENDER BUDGET -- said plainly, because the comment
# here used to claim "~half a stride" and a stride is 0.649 m, so 0.90 is 1.4 strides, not half of
# one. A false comment is a typed number's alibi and this file has no audit to catch either.
#
# What it actually buys, measured: 8 rings x 97x97 cells = ~58,000 grains reaching 6 km, with every
# ring subtending ~1.9 degrees at its inner edge. Halving it doubles the near detail and doubles the
# grain count for a horizon that does not move. Nothing derives it; it is chosen against a budget,
# and if the budget changes this is the number to change.
# THE BUDGET CHANGED (2026-08-04, INK membrane, docs/THE_RECORDED_SESSION_2.md): THE HUMAN ruled
# the terrain itself low-detail, so 0.90 -> 0.45. Measured after the move: near detail x2, grain
# COUNT UNCHANGED (~58k -- same 97x97 cells, finer spacing), horizon reach HALVED (~3 km). For a
# session that lives within metres of spawn that is the right trade; a horizon walk wants it back.
# Render row only -- shape and grain laws are aTerrain's and theGround's.
_STEP0 = 0.45

# ── EXPOSURE: A LENS ACT, NOT A PHYSICS EDIT ─────────────────────────────────────────────────────
# The planet is Earth-bright (S_earth = 1.005, measured) -- the first recorded session still read
# as "nearly empty dark landscape" (docs/THE_SLICE.md, Phase E rung 3, F2 fired). The dimness is
# not the world's light; it is how much of that light the camera admits. So this is the camera's
# EXPOSURE COMPENSATION: the one human dial, exactly the legal status of lit()'s `tone` -- THE
# HUMAN (taste), said plainly and never buried. The physics is untouched: albedo, beam, sky,
# ground-bounce and S_rel are all still derived; the LENS opens two stops (x2 on irradiance) on
# the way to the tone curve. One constant serves every lit() in this file, because one sun serves
# the whole picture -- ground, body, skin-wrap -- and the touchables' _shade reads it too, so the
# objects sit in the same photograph as the ground they rest on.
_EXPOSURE = 2.0         # THE HUMAN -- taste row; the operator's to move. Physics: unchanged.


def scene_around(w: Walker, t: float = None):
    """The buffer to render from inside: fine underfoot, coarse to the horizon, no seam between.

    SHAPE from `aTerrain` (its carved height field, interpolated); GRAIN from `theGround` (stones at
    the fractal size distribution its law derived). That is LOD of meaning at walking scale -- the
    same derivation read at the resolution a body needs.
    """
    from matter import blank, lit, SOLID          # ChimeraEngine/core/matter.py, already on the path
    (zf, dx, patch, acc, slope), nums = _load()
    gnd = nums["ground"]
    S_rel = float(nums["terrain"]["S_earth"])
    half = patch / 2.0 - 2.0
    sunv, alt = w.sun
    sun = np.array(sunv, np.float32); sun /= (np.linalg.norm(sun) + 1e-12)
    # AIRLIGHT. Below the horizon there is no direct beam, but the sky is not black until the sun is
    # well down -- the atmosphere aBlueWorld derived keeps scattering. Twilight fades over the ~12 deg
    # the geometry gives and never reaches zero, because the ground still sees the sky hemisphere.
    beam = max(0.0, math.sin(alt))
    sky = 0.09 + 0.16 * max(0.0, min(1.0, (math.degrees(alt) + 6.0) / 12.0))

    veg = np.array([0.20, 0.27, 0.14], np.float32)
    rock = np.array([0.34, 0.31, 0.27], np.float32)
    if nums["place"]["snow"]:
        # SNOW IS A TEMPERATURE, NOT A LATITUDE -- aBlueWorld's own words. Where its latitude law
        # puts this place below freezing, the soil mantle wears snow; the steep faces stay rock,
        # because the same slopes too steep to hold soil are too steep to hold a snowpack.
        veg = np.array([0.76, 0.80, 0.86], np.float32)
    bare_above = float(gnd["bare_rock_above_deg"])       # theGround's one claim about exposed rock

    parts = []
    for lvl in range(_RING_LEVELS):
        step = _STEP0 * (2 ** lvl)
        # SNAP TO THE WORLD. Anchoring each ring to a multiple of its own spacing is what stops the
        # ground crawling: the grains stay where they are and the ring slides across them.
        cx = math.floor(w.x / step) * step
        cy = math.floor(w.y / step) * step
        k = np.arange(-_RING_N, _RING_N + 1) * step
        XX, YY = np.meshgrid(k + cx, k + cy)
        X, Y = XX.ravel(), YY.ravel()
        if lvl > 0:
            # cut the hole the finer ring already fills (its extent, in this ring's coordinates)
            inner = _RING_N * (_STEP0 * (2 ** (lvl - 1)))
            keep = (np.abs(X - w.x) > inner) | (np.abs(Y - w.y) > inner)
            X, Y = X[keep], Y[keep]
        inside = (np.abs(X) < half) & (np.abs(Y) < half)
        X, Y = X[inside], Y[inside]
        if not len(X):
            continue

        # BREAK THE LATTICE. A regular grid seen at a grazing angle beats against the pixel grid and
        # fans out in stripes -- the same aliasing a picket fence makes on video. Real ground grains
        # are not on a lattice either. The offset is a function of the CELL, so a grain sits in the
        # same spot every time you walk back to it.
        ix = np.rint(X / step).astype(np.int64)
        iy = np.rint(Y / step).astype(np.int64)
        X = X + (_hash01(ix, iy, 1) - 0.5) * step * 0.45
        Y = Y + (_hash01(ix, iy, 2) - 0.5) * step * 0.45

        n = len(X)
        Z = heights_at(X, Y)
        gx, gy = gradients_at(X, Y, max(step, 4.0))   # this ring's own scale -- see gradients_at

        b = blank(n)
        b[:, 0], b[:, 1], b[:, 2] = X, Y, Z
        nrm = np.stack([-gx, -gy, np.ones(n)], axis=1)
        nrm /= (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
        b[:, 21:24] = nrm

        # ── WHAT THIS PATCH OF GROUND IS MADE OF, derived, not speckled ──────────────────────────
        # The first version scattered stones with the GLSL hash `frac(sin(dot(p, k)) * 43758)`. On a
        # perfect lattice that is not random at all: X and Y are multiples of `step`, so the hash
        # argument is LINEAR in the integers, its fractional part cycles with a short period, and the
        # render came back covered in moire fringes fanning to the horizon. There was nothing to
        # hash: `theGround` already says where rock is exposed.
        #
        # AND THE SECOND VERSION OVERREACHED THE OTHER WAY. It read soil DEPTH as a cover fraction --
        # 0.374 m of soil at this terrain's mean slope became "74% bare rock". You cannot see through
        # 37 cm of dirt. Depth says how much soil there is, not how much bedrock shows through it,
        # and turning one into the other took a scale nobody derived.
        #
        # theGround makes exactly ONE claim about exposed rock: `bare_rock_above_deg`, the slope at
        # which production can no longer keep up with removal and the soil mantle goes to zero. So
        # that is the claim this uses. The result is a landscape almost entirely mantled -- mean
        # slope 17 deg against a 32.9 deg threshold -- with rock only on the steepest faces. That is
        # not a flattering picture; it is this planet's answer, and the render's job is to state it.
        grade = np.degrees(np.arctan(np.hypot(gx, gy)))
        # the 3 deg ramp is ANTI-ALIASING, not physics: a hard step on a 0.9 m lattice stairsteps.
        bare = np.clip((grade - bare_above + 3.0) / 6.0, 0.0, 1.0)[:, None]
        alb = veg * (1.0 - bare) + rock * bare

        lam = np.clip(nrm @ sun, 0.0, None)
        b[:, 16:19] = lit(alb, _EXPOSURE * (S_rel * beam * lam + sky), e_ref=S_rel, tone=0.45)
        b[:, 19] = 0.95
        # A GRAIN MUST BE BIGGER THAN ITS GAP. On a square lattice of pitch `step`, the farthest a
        # point can be from the nearest grain centre is the half-diagonal, 0.707 * step -- so at 0.8
        # the surface was already marginal, and jittering by +/-0.45 opened it into visible streaks.
        # 1.05 covers the lattice AND the jitter, which is what turns dots back into ground.
        b[:, 20] = step * 1.05
        b[:, 11] = SOLID
        parts.append(b)

    parts.append(_sky(w, nums, sun, alt))
    return np.concatenate(parts, axis=0)


_BODY_CACHE = {}     # only "sole" now (the mean-cycle sole offset); the posed body emits per
                     # frame WITH the terrain (B1), so a per-phase cache would be a flat-floor body


def body_buffer(w: Walker):
    """theHuman's own figure, standing in the world: emit() gives the body in local units
    (1.0 tall, walking along local +X, origin at the CoM); this places it -- yaw, stature,
    soles on the carved ground -- and relights it under the walker's real sky.

    The phase is DISTANCE, not time: one emit() movie is one gait cycle, and a cycle covers
    two strides of ground, so the phase advances by dist / (2 * stride_m) -- the ACTIVE
    direction's stride (A3). A body that walks when the ground scrolls and freezes when it
    stops cannot drift out of step with its own motion."""
    st = _static()
    hn = st["suited"]                 # aHuman's numbers: the suit's shape as well as the body's
    height = float(hn["height_m"])

    # THE GAIT FOR THE DIRECTION THE BODY IS ACTUALLY MOVING (A3). body_yaw is the figure's
    # facing (A1 eases it toward the velocity); theta is where the velocity sits relative to
    # that facing, and the measured table for that sector is the pose -- so a reversal shows the
    # measured toe-first backpedal while the body is still turning, and a slew shows the
    # cross-step, instead of the forward gait rotated. theta > 0 is velocity to the LEFT of
    # facing (the yaw convention turns +Y toward -X), so that sector reads the left-sidestep
    # table, whose LEADING leg is the left one. The pose still maps onto body_yaw (A1's turn
    # animation is untouched), and B1's IK plants the soles regardless.
    cycles = hn.get("gait_cycles") or {}
    strides = hn.get("gait_dir_stride_m") or {}
    key = "forward"
    if cycles and abs(w.vx) + abs(w.vy) > 1e-6:
        heading = math.atan2(w.vy, w.vx) - math.pi / 2.0
        theta = (heading - w.body_yaw + math.pi) % (2.0 * math.pi) - math.pi
        if abs(theta) > math.radians(120.0):
            key = "backward"
        elif abs(theta) > math.radians(60.0):
            key = "left" if theta > 0.0 else "right"
    tab = cycles.get(key)

    # THE PHASE IS STILL DISTANCE, but over the ACTIVE direction's own measured stride -- a
    # backpedal's stride is shorter, and a fixed stride would make its feet skate. One
    # accumulator, advanced per frame, so switching tables does not jump the legs mid-cycle.
    stride_active = float(strides.get(key, hn["stride_m"]))
    if "phase" not in _BODY_CACHE:
        _BODY_CACHE["phase"] = 0.0
        _BODY_CACHE["dist"] = w.dist
    dd = w.dist - _BODY_CACHE["dist"]
    _BODY_CACHE["dist"] = w.dist
    _BODY_CACHE["phase"] = (_BODY_CACHE["phase"] + dd / (2.0 * stride_active)) % 1.0
    t = _BODY_CACHE["phase"]

    # WHERE THE SOLES ARE IS MEASURED, NOT ASSUMED. Placing the body by adding com_height_m to the
    # ground put the boots 50 mm UNDERGROUND: com_height is the BARE body's centre of mass, and a
    # suited figure has thicker soles under it. So the offset is the mean lowest point over the whole
    # gait cycle -- averaged rather than per-pose, because pinning every frame's lowest grain to the
    # ground would flatten the CoM bob that makes it read as a walk instead of a glide.
    if "sole" not in _BODY_CACHE:
        lows = [st["human_law"].emit(hn, k / 12.0)[:, 2].min() for k in range(12)]
        _BODY_CACHE["sole"] = float(sum(lows) / len(lows))
    lift = -_BODY_CACHE["sole"]
    com_h = float(hn["com_height_m"]) / height

    # local +X (emit's walking direction) -> the FIGURE's facing (body_yaw, velocity-facing A1)
    a = w.body_yaw + math.pi / 2.0
    c, s = math.cos(a), math.sin(a)
    wx0, wy0, wz0, wc0 = w.x, w.y, w.z, w.crouch

    def _ground(lx, ly):
        # emit's pre-CoM local frame -> world (the same transform the grains get below) -> the
        # carved field -> back to local. The foot and the floor it lands on are the SAME surface
        # by construction: this closure reads height_at(), the walker's own ground truth.
        gx = (lx * c - ly * s) * height + wx0
        gy = (lx * s + ly * c) * height + wy0
        return (height_at(gx, gy) - wz0 - wc0) / height + com_h - lift

    # B1: emit WITH the terrain every frame, so a planted sole is PLACED on the carved ground and
    # the knee absorbs the difference (aHuman/physics.py, the two-bone solve). The 48-pose cache
    # was a body walking a flat virtual floor; the terrain conform lives in the body's own
    # membrane now, and the phase still quantizes inside emit (the parent's 48-row table).
    b = st["human_law"].emit(hn, t, ground=_ground, cycle=tab)
    x, y = b[:, 0].copy(), b[:, 1].copy()
    b[:, 0] = (x * c - y * s) * height + w.x
    b[:, 1] = (x * s + y * c) * height + w.y
    # emit centres on the CoM; the walker's z is the SOLES. com_height_m up from the feet is the
    # same number both used, so the soles land exactly on the carved surface -- plus the crouch dip.
    b[:, 2] = (b[:, 2] + lift) * height + w.z + w.crouch
    nx, ny = b[:, 21].copy(), b[:, 22].copy()
    b[:, 21] = nx * c - ny * s
    b[:, 22] = nx * s + ny * c
    # COVERAGE PER PART, not one factor for all. emit() draws every part with one 0.011 grain,
    # which under-covers the limbs at 3 m (they smear) -- but a uniform blow-up was measured wrong
    # too: it ballooned the head and fattened the trunk until the legs fused into one stalk. The
    # honest rule is the clipmap's, applied per tube: a grain must close ITS OWN surface, so its
    # size follows its part's radius. The head is the opposite case -- a densely-sampled sphere
    # whose roundness survives only with SMALL grains. emit's part order is deterministic
    # (per side: thigh, shank, foot, upper arm, forearm; then trunk, head), so the ranges are known.
    if False:   # (was theHuman's 3120-grain stick figure; aHuman sizes its own surface)
        seg = [(260, 0.032), (260, 0.030), (120, 0.028), (180, 0.026), (180, 0.024)]
        sizes = np.empty(len(b), np.float32)
        i = 0
        for _rep in range(2):
            for cnt, sz in seg:
                sizes[i:i + cnt] = sz; i += cnt
        sizes[i:i + 420] = 0.048; i += 420       # trunk: the widest tube
        sizes[i:] = 0.020                         # head: keep the sphere a sphere
        b[:, 20] = sizes * height
    else:
        # aHuman sizes its own grains to close its own surface (rings on tubes), so scaling to
        # metres is all that is needed -- no re-guessing per part.
        b[:, 20] *= height

    # RELIT UNDER THE REAL SKY -- same beam + airlight as the ground, so one sun serves the
    # whole picture. emit's own sun is a demo light for the membrane view and stays there.
    from matter import lit
    (_f, nums) = _load()
    S_rel = float(nums["terrain"]["S_earth"])
    sunv, alt = w.sun
    sun = np.array(sunv, np.float64); sun /= (np.linalg.norm(sun) + 1e-12)
    beam = max(0.0, math.sin(alt))
    sky = 0.09 + 0.16 * max(0.0, min(1.0, (math.degrees(alt) + 6.0) / 12.0))
    lam = np.clip(b[:, 21:24] @ sun, 0.0, None)
    # THE BODY'S OWN MATERIALS, if it published any (matter.AR..AB). aHuman derives three -- pale
    # suit, dark visor, grey hardware -- and a single hard-coded albedo here erased all three.
    import matter as _M
    own = b[:, _M.AR:_M.AB + 1]
    body_alb = own if float(np.abs(own).max()) > 1e-6 else np.array([0.52, 0.44, 0.38], np.float32)
    # GROUND BOUNCE. A vertical surface standing on sunlit grass does not go black on its shaded
    # side: half its sky is the BRIGHT GROUND. One bounce -- ground albedo ~0.22, view factor 0.5
    # for a vertical face -- is 11% of the beam, and it is why the figure's back reads as a body
    # in daylight instead of a silhouette. Same physics as the sky term, one reflection later.
    bounce = 0.5 * 0.22 * S_rel * beam
    b[:, 16:19] = lit(body_alb, _EXPOSURE * (S_rel * beam * lam + sky + bounce), e_ref=S_rel, tone=0.45)
    # PER-CLASS SHADING (F1): the body publishes its material class in matter.MAT.
    cls = b[:, _M.MAT]
    # THE FACE SITS BEHIND THE VISOR: it is lit only by what the visor transmits, and its light
    # WRAPS -- a photon random-walks the skin's measured mean free path before forgetting its
    # direction, so the terminator softens per colour and red reaches furthest. The wrap width
    # is mfp against the head's own radius: derived, and honestly subtle at this scale.
    skin = cls == 3.0
    if skin.any():
        T_vis = float(hn.get("visor_transmission", 1.0))
        w = np.clip(np.array(hn.get("skin_sss_mfp_mm", [0.0, 0.0, 0.0]), np.float32)
                    / (1000.0 * float(hn.get("r_head_m", 0.12))), 0.0, 1.0)
        lam_s = np.clip(b[skin, 21:24] @ sun, -1.0, 1.0)
        wrapped = np.clip((lam_s[:, None] + w[None, :]) / (1.0 + w[None, :]), 0.0, 1.0)
        e_band = T_vis * (S_rel * beam * wrapped + (sky + bounce))
        # the same lens as everything above: the skin-wrap is a lit() by hand, so the exposure
        # compensation (THE HUMAN dial, declared at _EXPOSURE) multiplies its irradiance too
        scale = np.clip(_EXPOSURE * e_band / max(S_rel, 1e-30), 0.0, None) ** 0.45
        b[skin, 16:19] = np.clip(body_alb[skin] * scale, 0.0, 1.0)
    # the visor keeps its specular: a curved dark surface with a bright sky in front of it
    visor = cls == 1.0
    if visor.any():
        b[visor, 16:19] += (np.clip(lam[visor], 0.0, None)[:, None] ** 24 * 0.8).astype(np.float32)
        np.clip(b[:, 16:19], 0.0, 1.0, out=b[:, 16:19])
    return b


_SKY_DIRS = None


def _sky(w, nums, sun, alt):
    """THE SKY, FROM THE AIR THE PLANET ACTUALLY HAS.

    A black sky above a lit landscape is a contradiction the render was stating out loud:
    `aBlueWorld` derives `has_atmosphere: True` at 0.52 bar with a 10.3 km scale height, and an
    atmosphere that thick scatters. So this is not a backdrop -- it is the same matter the planet
    already claimed, drawn.

    Rayleigh single-scattering, and every term comes from upstream:

      * HOW MUCH AIR. Optical depth scales with the column, so with surface pressure. Earth is
        tau = 0.0973 at 550 nm (Bodhaine 1999); this world runs 0.52 bar, so 0.0506.
      * WHAT COLOUR. tau goes as 1/lambda^4 -- that IS why a sky is blue, and it is a ratio, not a
        palette: 0.64 / 1.12 / 1.96 across R, G, B at 615/535/465 nm.
      * HOW BRIGHT IN EACH DIRECTION. The Rayleigh phase function 3/(16 pi) (1 + cos^2 T) against
        the sun, times the airmass along the view ray, times what survives the slanted path to the
        sun. Which gives, for free and unasked: bright near the sun, deepest at 90 deg from it,
        pale at the horizon where the airmass is long, and RED at sunrise -- because at low sun the
        blue has been scattered out of the beam before it arrives.

    The dome is drawn at 40 km, beyond the terrain's 6 km reach so nothing can poke through it.
    """
    from matter import blank, GLOW
    global _SKY_DIRS
    if _SKY_DIRS is None:
        # a Fibonacci hemisphere: even coverage, no pole clumping, no seam to alias
        m = 2400
        i = np.arange(m) + 0.5
        cz = 1.0 - i / m                      # upper hemisphere only, cos(zenith) 1 -> 0
        rr = np.sqrt(np.clip(1.0 - cz * cz, 0.0, 1.0))
        ph = np.pi * (1.0 + 5.0 ** 0.5) * i
        _SKY_DIRS = np.stack([rr * np.cos(ph), rr * np.sin(ph), cz], axis=1)
    d = _SKY_DIRS
    n = len(d)

    P_bar = float(nums["planet"]["P_surface_bar"])
    tau0 = 0.0973 * P_bar                                     # 550 nm, scaled by the column
    tau = tau0 * np.array([0.640, 1.117, 1.960], np.float64)   # (550/615)^4, (550/535)^4, (550/465)^4

    # airmass along the view ray and along the ray to the sun (Kasten-Young, valid to the horizon)
    def airmass(cosz):
        c = np.clip(cosz, 0.0, 1.0)
        z = np.degrees(np.arccos(c))
        return 1.0 / (c + 0.50572 * np.power(np.clip(96.07995 - z, 1e-3, None), -1.6364))

    mv = airmass(d[:, 2])[:, None]                             # view ray
    ms = airmass(max(math.sin(alt), 0.0))                      # sun ray -- one number, the sun is one place
    cosT = np.clip(d @ np.asarray(sun, np.float64), -1.0, 1.0)[:, None]
    phase = 3.0 / (16.0 * np.pi) * (1.0 + cosT * cosT)

    scattered = (1.0 - np.exp(-tau[None, :] * mv)) * phase * np.exp(-tau[None, :] * ms)
    scattered *= 26.0                                          # 4 pi sr and the solar constant, folded
    if math.sin(alt) <= 0.0:                                   # night: only the twilight the geometry allows
        scattered *= max(0.0, 1.0 + math.degrees(alt) / 8.0) ** 2

    R = 40000.0
    b = blank(n)
    b[:, 0] = w.x + d[:, 0] * R
    b[:, 1] = w.y + d[:, 1] * R
    b[:, 2] = w.z + d[:, 2] * R
    b[:, 16:19] = np.clip(scattered, 0.0, 1.0)
    b[:, 19] = 1.0
    # 2400 points over a hemisphere is 1.6 deg of angular spacing; drawn at 1.6 deg they read as
    # 2400 dots. At 5.2 deg each one overlaps its neighbours threefold and the dome closes.
    b[:, 20] = R * 0.091
    b[:, 11] = GLOW
    return b


_COARSE = {}


def height_field_coarse(n, patch):
    """The whole patch on an n x n grid -- cached, because the far shell needs its gradients."""
    if n in _COARSE:
        return _COARSE[n]
    v = np.linspace(-patch / 2 + 2, patch / 2 - 2, n)
    XF, YF = np.meshgrid(v, v)
    Z = np.array([[height_at(x, y) for x in v] for y in v])
    _COARSE[n] = Z
    return Z


class StandSimulator:
    """MuJoCo stand policy simulator -- runs the body in physics, tracks survival.

    THEORY (stated so it can fail):
      STATEMENT  The stand policy (theta) decoded by SynergyDecoder produces muscle activations
                  that the MuJoCo body can execute in real time, and the simulator's traced
                  state (pelvis height, COM drift) is the ground truth for survival.
      PREDICTION  Over 20 s the pelvis height stays above 50% of target and the COM drift
                  stays within the base of support; the simulator reports held_time and fall_state.
      FALSIFIER   If the body falls within the window where the training score said it should
                  stand, the plant the judge runs does not match the plant the trainer optimised.

    This is the bridge between the story's terrain Walker and the MuJoCo physics: the simulator
    owns the MuJoCo state, and the live viewer reads its body positions as splats for rendering.
    """

    # MuJoCo geoms: body_id -> (color_rgb, radius_m) for splat rendering
    _BODY_COLORS = {
        "pelvis": (0.52, 0.44, 0.38),
        "torso":  (0.52, 0.44, 0.38),
        "head":   (0.52, 0.44, 0.38),
        "thigh_r": (0.20, 0.30, 0.40),
        "thigh_l": (0.20, 0.30, 0.40),
        "shank_r": (0.20, 0.30, 0.40),
        "shank_l": (0.20, 0.30, 0.40),
        "foot_r":  (0.10, 0.10, 0.10),
        "foot_l":  (0.10, 0.10, 0.10),
        "toe_r":   (0.10, 0.10, 0.10),
        "toe_l":   (0.10, 0.10, 0.10),
    }

    def __init__(self, theta_path=None, mujoco_body=None, gravity=None):
        """Create the MuJoCo simulation environment with the stand policy.

        Args:
            theta_path: path to the .npy theta file (4-block P-only, 6-block P+CoM or 7-block PD).
                        Defaults to ChimeraEngine/output/ports/stand_theta.npy
            mujoco_body: path to the MuJoCo XML model. Defaults to the myobody.
            gravity: override gravity (m/s^2). None uses the model's default.
        """
        import sys as _sys
        import mujoco
        _sys.path.insert(0, str(_HERE.parent / "tools"))
        from world import load_body
        from synergy import SynergyDecoder
        from stand_port import derive_stand_port, MYOBODY

        self.mujoco = mujoco
        self.body_path = mujoco_body or MYOBODY
        self.P = derive_stand_port()
        self.tgt = float(self.P["OUT pelvis_target_m"])

        # Load MuJoCo model
        self.m, self.g = load_body(self.body_path, mujoco)
        self._mujoco = mujoco
        self._SynergyDecoder = SynergyDecoder
        if gravity is not None:
            self.m.opt.gravity[2] = -gravity
            self.g = float(-self.m.opt.gravity[2])
        self.d = mujoco.MjData(self.m)
        self.nu = self.m.nu

        # Load policy
        self.theta_path = Path(theta_path) if theta_path else (_HERE / "output" / "ports" / "stand_theta.npy")
        self.decoder = SynergyDecoder(theta_path=self.theta_path, tgt=self.tgt, nu=self.nu)
        # SYNERGY LAYOUTS: 6/7/9-block thetas decode through the decoder's richer formulas
        # (P+CoM / PD / PD+CoM); 4-block is the parser-compatible P-only policy.
        self.is_pd = self.decoder.blocks in (6, 7, 9)

        # State tracking
        self.t = 0.0
        self.prev_obs_state = None
        self.held_time = 0.0          # how long pelvis has been above 90% of target
        self.support_score = 1.0      # COM within base of support, 0..1
        self.fall_state = "standing"  # "standing" | "falling" | "fallen"
        self.fall_time = None         # when the fall below 50% target occurred
        self.fell = False
        self.ctrl_history = []        # muscle activations over time
        self._b = lambda n: self.d.xpos[mujoco.mj_name2id(self.m, mujoco.mjtObj.mjOBJ_BODY, n)]

        # Reset to keyframe 0 (seated pose)
        self.reset()

    def reset(self):
        """Reset to the seated keyframe."""
        self.mujoco.mj_resetDataKeyframe(self.m, self.d, 0)
        self.mujoco.mj_forward(self.m, self.d)
        # Apply the stand keyframe adjustments (seat_in_limits equivalent)
        from train_stand import joint_ids, seat_in_limits
        jids = joint_ids(self.m, self.mujoco)
        seat_in_limits(self.m, self.d, self.mujoco, jids)
        self.t = 0.0
        self.prev_obs_state = None
        self.held_time = 0.0
        self.support_score = 1.0
        self.fall_state = "standing"
        self.fall_time = None
        self.fell = False
        self.ctrl_history = []

    def step(self, n_substeps=1):
        """Advance the MuJoCo simulation by n_substeps * CTRL_EVERY timesteps.

        At each control tick, decodes the policy and applies muscle activations.
        Returns (t, pelvis_z, fallen, held_time, support_score).
        """
        dt = float(self.m.opt.timestep)
        ctrl_every = 20  # 50 Hz control rate
        total_steps = n_substeps * ctrl_every

        for k in range(total_steps):
            if k % ctrl_every == 0:
                obs, self.prev_obs_state = self._SynergyDecoder.obs_from_mujoco(
                    self.d, self.m, self.tgt, prev=self.prev_obs_state)
                u = self.decoder.decode(obs)
                np.clip(u, 0.0, 1.0, out=u)
                self.d.ctrl[:] = u
                if (k % ctrl_every) == 0:
                    self.ctrl_history.append(float(np.abs(u).mean()))
                    if len(self.ctrl_history) > 300:  # keep last ~60s at 50Hz
                        self.ctrl_history.pop(0)
            self.mujoco.mj_step(self.m, self.d)
            self.t += dt

            # Check fall every control tick
            if k % ctrl_every == 0:
                z = float(self.d.qpos[2])
                fall_bar = 0.5 * self.tgt
                if z < fall_bar and not self.fell:
                    self.fell = True
                    self.fall_time = self.t
                    self.fall_state = "fallen"
                elif z < self.tgt:
                    self.fall_state = "falling"
                elif z >= 0.9 * self.tgt:
                    self.held_time += ctrl_every * dt
                    self.fall_state = "standing"

                # Update support score (COM within base of support)
                com = self.d.subtree_com[0]
                try:
                    foot = 0.25 * (self._b("calcn_r") + self._b("calcn_l") +
                                   self._b("toes_r") + self._b("toes_l"))
                    hw, hl = (self.P.get("OUT bos_half_lat_m", 0.1),
                              self.P.get("OUT bos_half_fore_m", 0.1))
                    dx = float(com[0] - foot[0])
                    dy = float(com[1] - foot[1])
                    self.support_score = float(np.exp(-((dx/hw)**2 + (dy/hl)**2)))
                except Exception:
                    self.support_score = 0.0

        return dict(t=self.t, pelvis_z=float(self.d.qpos[2]),
                    fell=self.fell, held_time=self.held_time,
                    support_score=self.support_score, fall_state=self.fall_state,
                    fall_time=self.fall_time)

    def body_splats(self):
        """Return MuJoCo geom positions as a splat buffer for the live viewer.

        Produces an N x 24 float32 array in the matter.splat format:
          [:,0:3]   = world position (x, y, z)
          [:,16:19] = RGB color
          [:,19]    = alpha
          [:,20]    = radius (m)
          [:,21:24] = normal (nx, ny, nz)
          [:,11]    = SOLID flag

        The MuJoCo model's geoms are mapped to splats so the viewer can render
        the body in the SAME pipeline as the terrain splats.
        """
        m, d = self.m, self.d
        mujoco = self._mujoco
        import sys as _sys
        _sys.path.insert(0, str(_STORY))
        from matter import blank, SOLID
        geoms = []
        for gi in range(m.ngeom):
            g = m.geom(gi)
            gtype = int(g.type)
            if gtype == 0:
                continue                    # skip the ground plane -- it is not part of the body
            pos = d.geom_xpos[gi]
            rot = d.geom_xmat[gi].reshape(3, 3)
            # geom size -> radius (use the largest dimension of the box/capsule cross-section)
            size = m.geom_size[gi]
            # for capsule/cylinder the size is (radius, half-length); a splat wants a surface
            # radius, so use the first two components (the cross-section) not the long axis
            radius = float(np.max(size[:2])) if gtype in (4, 5, 6) else float(np.max(size))
            # color from geom rgba
            rgba = m.geom_rgba[gi]
            # normal: geom's local Z axis in world frame
            normal = rot @ np.array([0, 0, 1], dtype=np.float64)
            geoms.append((pos.copy(), rgba, radius, gtype, normal))
            # soft cap: bodies are ~290 bones; keep the buffer from exploding on huge models
            if len(geoms) > 2048:
                break

        n = len(geoms)
        if n == 0:
            return np.zeros((0, 24), np.float32)

        from matter import blank, SOLID
        b = blank(n)
        for i, (pos, rgba, radius, gtype, normal) in enumerate(geoms):
            b[i, 0] = pos[0]     # x
            b[i, 1] = pos[1]     # y
            b[i, 2] = pos[2]     # z
            # scale radius for splat rendering (geoms are small)
            b[i, 20] = max(radius * 3.0, 0.01)     # splat size
            b[i, 16] = rgba[0]   # R
            b[i, 17] = rgba[1]   # G
            b[i, 18] = rgba[2]   # B
            b[i, 19] = rgba[3] if rgba[3] > 0 else 0.95  # alpha
            b[i, 21] = normal[0] # nx
            b[i, 22] = normal[1] # ny
            b[i, 23] = normal[2] # nz
            b[i, 11] = SOLID
        return np.ascontiguousarray(b, dtype=np.float32)
