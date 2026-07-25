"""appearance.py -- THE APPEARANCE MESSENGER (the light-view of a membrane).

Your idea, made mechanism: gravity and light are one thing measured by two independent systems, so
a term's PHYSICS (its measured interior -- the genome) and its APPEARANCE (its emitted surface --
the render) are two messengers of ONE membrane, and proof is their AGREEMENT. This module is the
appearance messenger: it PROJECTS a term's physics into a visual, generated FROM the term's own
world so it cannot be an unrelated picture. A term with no projector has no light-view yet, and
honestly cannot be proven by two-messenger agreement until one is built. (No aesthetic passes:
appearance derives from the matter model, never beside it.)
"""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "Chimera"))       # reach core.*


def _star(out: Path) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor("#04050b"); ax.set_facecolor("#04050b")
    rng = np.random.default_rng(7)
    ax.scatter(rng.uniform(-1, 1, 300), rng.uniform(-1, 1, 300),
               s=rng.uniform(.3, 2.2, 300), c="#c9d4ff", alpha=.35, lw=0)
    for r, a in [(.62, .10), (.5, .16)]:
        ax.add_patch(Circle((0, 0), r, fill=False, ec="#39c07a", lw=1, alpha=a, ls=(0, (5, 5))))
    from convergence import blackbody_srgb
    base = blackbody_srgb(5778)                         # THE PHYSICS: Planck's law -> the Sun's true color
    def mix(t):                                         # blend toward white by t (a hot core saturates the sensor)
        return tuple((base[i] + (255 - base[i]) * t) / 255 for i in range(3))
    for k in range(16):
        th = k * np.pi / 8
        ax.plot([.09 * np.cos(th), .46 * np.cos(th)], [.09 * np.sin(th), .46 * np.sin(th)],
                color=mix(0.0), alpha=.12, lw=2)
    for rr, t, a in [(.34, .0, .10), (.24, .0, .22), (.15, .0, .60), (.11, .35, .92), (.06, .85, 1.0)]:
        ax.add_patch(Circle((0, 0), rr, color=mix(t), alpha=a, lw=0))
    ax.set_xlim(-.85, .85); ax.set_ylim(-.85, .85); ax.set_aspect("equal"); ax.axis("off")
    fig.text(.5, .95, "THE STAR", color=mix(.5), ha="center", fontsize=24, weight="bold")
    fig.text(.5, .05, f"G2V  ·  ~5778 K  ·  color COMPUTED from Planck's law -> sRGB {base}",
             color="#7e88ad", ha="center", fontsize=10)
    p = out / "appear_theStar.png"
    fig.savefig(p, dpi=110, facecolor=fig.get_facecolor()); plt.close(fig)
    return str(p)


def _solarsystem(out: Path) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Wedge
    orbits = [(.236, "#ff5a44"), (.444, "#ffb020"), (.834, "#7fc0ff"), (.976, "#3fe0a0")]  # grown AU
    fig, ax = plt.subplots(figsize=(9, 9))
    fig.patch.set_facecolor("#04050b"); ax.set_facecolor("#04050b")
    ax.add_patch(Wedge((0, 0), 1.37, 0, 360, width=1.37 - 0.95, facecolor="#39c07a", alpha=.16, lw=0))
    for a, c in orbits:
        ax.add_patch(Circle((0, 0), a, fill=False, ec="#6f7fb0", lw=1, alpha=.5))
        th = np.random.default_rng(int(a * 1000)).uniform(0, 6.28)
        ax.scatter([a * np.cos(th)], [a * np.sin(th)], s=70, c=c, edgecolors=(.45, .5, .65), lw=.4, zorder=5)
    from convergence import blackbody_srgb
    sb = blackbody_srgb(5778)                           # the central star: its true blackbody color...
    def smix(t): return tuple((sb[i] + (255 - sb[i]) * t) / 255 for i in range(3))
    for rr, t, a in [(.20, .0, .10), (.13, .0, .30), (.08, .35, .70), (.05, .7, .95), (.03, 1., 1.)]:
        ax.add_patch(Circle((0, 0), rr, color=smix(t), alpha=a, lw=0, zorder=4))  # ...brightest, at the barycenter
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_aspect("equal"); ax.axis("off")
    fig.text(.5, .94, "THE SOLAR SYSTEM", color="#6f6a44", ha="center", fontsize=20, weight="bold")
    fig.text(.5, .06, "a yellow G-star  ·  4 grown worlds  ·  habitable zone shaded",
             color="#7e88ad", ha="center", fontsize=10)
    p = out / "appear_theSolarSystem.png"
    fig.savefig(p, dpi=110, facecolor=fig.get_facecolor()); plt.close(fig)
    return str(p)


def _planets(out: Path) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor("#04050b"); ax.set_facecolor("#04050b")
    orbits = [0.45, 0.75, 1.05, 1.6, 2.6]                 # grown worlds, inner -> outer (AU)

    def t_eq(a):                                          # equilibrium temperature, Sun-like, albedo folded in
        return 278.0 * a ** -0.5

    def climate(T):                                       # THE PHYSICS: color DERIVED from T_eq, not chosen
        if T > 360:  return (0.86, 0.30, 0.18)           # hot rock (molten red)
        if T > 300:  return (0.80, 0.46, 0.27)           # warm rock / desert (orange)
        if T > 250:  return (0.20, 0.52, 0.62)           # temperate ocean (blue-green) -- the habitable band
        if T > 205:  return (0.56, 0.71, 0.86)           # cold (pale blue)
        return (0.86, 0.91, 0.97)                        # frozen (white)

    xs = np.linspace(-0.82, 0.82, len(orbits))
    radii = [0.11, 0.13, 0.14, 0.12, 0.10]
    for a, x, r in zip(orbits, xs, radii):
        T = t_eq(a); c = climate(T)
        ax.add_patch(Circle((x, 0), r, color=c, lw=0))
        ax.add_patch(Circle((x, 0), r, fill=False, ec=(1, 1, 1), lw=.5, alpha=.22))
        ax.text(x, -0.34, f"{a:.2f} AU\n{T:.0f} K", color="#8892b0", ha="center", va="center", fontsize=9)
    ax.set_xlim(-1, 1); ax.set_ylim(-0.6, 0.6); ax.set_aspect("equal"); ax.axis("off")
    fig.text(.5, .93, "THE PLANETS", color="#cfe0ff", ha="center", fontsize=22, weight="bold")
    fig.text(.5, .06, "grown worlds, inner -> outer  ·  T_eq ∝ a^-0.5  ·  hot rock -> ocean -> frozen",
             color="#7e88ad", ha="center", fontsize=10)
    p = out / "appear_thePlanets.png"
    fig.savefig(p, dpi=110, facecolor=fig.get_facecolor()); plt.close(fig)
    return str(p)


def _globe(out: Path) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    rng = np.random.default_rng(11)
    fig, ax = plt.subplots(figsize=(8, 8))
    fig.patch.set_facecolor("#04050b"); ax.set_facecolor("#04050b")
    ax.scatter(rng.uniform(-1, 1, 200), rng.uniform(-1, 1, 200), s=rng.uniform(.3, 1.8, 200),
               c="#c9d4ff", alpha=.3, lw=0)
    R = 0.62
    for rr, a in [(R + .06, .10), (R + .03, .18), (R + .012, .30)]:          # atmosphere limb (blue haze)
        ax.add_patch(Circle((0, 0), rr, color=(0.45, 0.65, 0.95), alpha=a, lw=0))
    ocean = Circle((0, 0), R, color=(0.11, 0.31, 0.62), lw=0)               # THE PHYSICS: liquid water
    ax.add_patch(ocean)
    for _ in range(7):                                                       # continents (land = habitable + green)
        th = rng.uniform(0, 6.28); rad = rng.uniform(0, R * .78)
        blob = Circle((rad * np.cos(th), rad * np.sin(th)), rng.uniform(.11, .20), color=(0.20, 0.52, 0.24), lw=0)
        blob.set_clip_path(ocean); ax.add_patch(blob)
    for cy in (R * .82, -R * .82):                                          # polar ice caps
        cap = Circle((0, cy), .17, color=(0.90, 0.93, 0.97), alpha=.92, lw=0)
        cap.set_clip_path(ocean); ax.add_patch(cap)
    term = Circle((R * .5, 0), R, color=(0, 0, 0), alpha=.28, lw=0)         # a soft day/night terminator
    term.set_clip_path(ocean); ax.add_patch(term)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1); ax.set_aspect("equal"); ax.axis("off")
    fig.text(.5, .95, "A PLANET", color="#bfe0d0", ha="center", fontsize=24, weight="bold")
    fig.text(.5, .05, "a grown world from space  ·  oceans + continents + ice  ·  liquid water = habitable",
             color="#7e88ad", ha="center", fontsize=10)
    p = out / "appear_aPlanet.png"
    fig.savefig(p, dpi=110, facecolor=fig.get_facecolor()); plt.close(fig)
    return str(p)


def _garden(out: Path) -> str:
    from core.eden import grow_tree_of_knowledge, make_eden
    from core.scene3d import render
    onion, garden, _ = make_eden(7, lush=True)
    bones = grow_tree_of_knowledge(3)
    return render(onion, garden, bones, path=str(out / "appear_theGarden.png"))


# term -> its projector (the light-view). Reuses the proven core systems, so the appearance is a
# real projection of the term's physics, not an authored picture. Grows as more terms get a view.
PROJECTORS = {
    "theStar": _star,
    "theSolarSystem": _solarsystem,
    "thePlanets": _planets,      # the family of worlds, colored by their equilibrium temperature
    "aPlanet": _globe,           # ONE world from space -- oceans + continents (its own light-view, not the garden's)
    "theGarden": _garden,        # a scene ON the world: its lush surface, the tree of knowledge
}


def project(term: str, out_dir) -> str | None:
    """Generate the appearance messenger for `term` (a PNG projected from its physics), or None
    if no projector exists yet (no light-view -> the term can't be proven by two-messenger agreement)."""
    fn = PROJECTORS.get(term)
    if fn is None:
        return None
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    return fn(out)
