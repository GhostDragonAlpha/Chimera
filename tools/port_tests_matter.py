"""port_tests_matter.py -- the NON-HUMAN passive ports, registering into the same harness.

`docs/THE_COMPILER.md` says passive tissue is universal:

    ligament : human  ::  cellulose : grass  ::  crystal lattice : rock  ::  rebar : wall

and then says, honestly, that grass, rock, tree, building, vehicle, fabric and terrain have ZERO
validated ports and that nothing in that table may be cited as proven. This file is the beginning
of paying that down. Same registry, same three-part Rule 0, same refusal on a missing falsifier.

    13 grass_blade        a lamina is a DISTRIBUTED beam, and a lumped root spring is not it
    14 rock_fracture      sigma = E*eps to sigma_t, and the flaw size the literature IMPLIES
    15 tree_trunk         orthotropic wood: E_L bends it, G_LR shears it, and G_LR/E_L = 0.086
    16 terrain_footprint  a foot leaves a mark, or the soil is decorative
    17 granular_repose    a pile stands at its friction angle, and the world already grew one

TWO THINGS THIS FILE REFUSES TO DO, both named in THE_COMPILER's own honest-status block:

  * IT DOES NOT CHOOSE A CONSTANT. Every E, k, sigma comes from `tools/matter_data.py`, which
    raises rather than default. Where nothing is published the port REFUSES BY NAME -- grass
    damping `c` has no measurement and so no port claims one.

  * IT DOES NOT CHOOSE A TOLERANCE WHERE THE DATA PUBLISHES ONE. "within 5%" is a round number
    with no source, and a tolerance chosen to be comfortable is a falsifier chosen to be
    survivable. Where a constant carries a published spread, the spread sets the bar and the
    round number is reported beside it so the difference is visible. Where a port is testing the
    ENGINE against a closed form rather than the world against a measurement, the bar is tight
    (the discretisation is computable, so there is nothing to be generous about).

Run through the harness: `python tools/port_tests.py`
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from port_registry import port_test
import matter_data as md


def _published(membrane: str) -> dict:
    """One membrane's PUBLISHED numbers, read off numbers.json -- never by importing its physics.

    THE INSTRUMENT MUST MOVE WITH THE MEMBRANE AND KEEP NO COPY OF IT, and it must not import the
    membrane it judges: four stale-copy convictions landed in a single day. theGround's own
    `sinkage()` is exactly the function the terrain port is about to disagree with, so calling it
    would be asking the defendant to testify. Its published numbers are fair game; its reasoning
    is not.
    """
    hits = [p for p in (ROOT / "story").rglob("numbers.json") if p.parent.name == membrane]
    if not hits:
        raise md.Uncited(f"no {membrane}/numbers.json under story/ -- run `python story/grow.py`. "
                         f"Refusing to assume a value for a membrane that has not been grown.")
    import json
    return json.loads(hits[0].read_text(encoding="utf8"))


def _terzaghi(phi_deg: float) -> tuple[float, float]:
    """Terzaghi's bearing factors from the friction angle alone. Nothing else enters."""
    phi = math.radians(phi_deg)
    nq = math.exp(math.pi * math.tan(phi)) * math.tan(math.radians(45.0) + phi / 2.0) ** 2
    return nq, (nq - 1.0) / math.tan(phi)


# ── SHARED: THE DISCRETE CANTILEVER ───────────────────────────────────────────────────────────
# One helper, three ports. A blade of grass, a rock beam and a tree trunk are the same object at
# three scales and three moduli -- which is the whole claim of "passive tissue is universal", so
# it would be incoherent to write it three times.

def _chain_xml(L, N, E, I, A, rho, g=0.0, axial=False, damp_mult=2.0):
    """N segments, hinge (or slide) at the ROOT of each, stiffness derived from E and the section.

    THE STIFFNESS IS NOT A PARAMETER. k_seg = E*I/ell for bending and E*A/ell for stretch, which
    is the segment's own flexural/axial rigidity divided by its length. Nothing here is tuned:
    change E or the section and every number downstream moves, which is the slider test.

    GRAVITY DEFAULTS TO ZERO AND THAT IS A STATEMENT, not a convenience. These tests measure a
    STIFFNESS: the load must be the one applied, not the one applied plus the specimen's own
    weight. A self-weight term would make the answer depend on a density none of these three
    materials needs for a static deflection. The density that IS supplied only sets how fast the
    transient dies.
    """
    ell = L / N
    k = E * (A if axial else I) / ell
    jt = "slide" if axial else "hinge"
    ax = "1 0 0" if axial else "0 1 0"
    m_seg = rho * A * ell
    body = ""
    for i in range(N):
        # DAMPING IS SIZED PER HINGE, and getting this wrong cost a run. A single c computed from
        # ONE segment's inertia critically damps the TIP hinge and leaves the ROOT hinge -- which
        # swings the whole distal chain -- badly under-damped, so the run hit its step cap with
        # |qvel| still at 5e-4 and a 0.25% residual that looked like discretisation. The distal
        # inertia about hinge i is m_seg*ell^2*(N-i)^3/3, a factor of N^3 across the chain, and
        # critical damping against THAT settles the whole beam in a few thousand steps.
        #
        # It costs nothing in truth: with gravity off, damping changes only how fast the static
        # equilibrium is reached, never where it is. That is why it may be sized freely and why
        # sizing it badly is a measurement failure rather than a physics one.
        J = m_seg * (ell ** 2) * (N - i) ** 3 / 3.0 if not axial else m_seg * (N - i)
        c = damp_mult * math.sqrt(max(k * J, 1e-300))
        pos = "0 0 0" if i == 0 else f"{ell} 0 0"
        body += (f'<body name="s{i}" pos="{pos}">'
                 f'<joint name="j{i}" type="{jt}" axis="{ax}" pos="0 0 0" '
                 f'stiffness="{k!r}" damping="{c!r}" limited="false"/>'
                 f'<geom type="box" pos="{ell/2} 0 0" size="{ell/2} {math.sqrt(A)/2} '
                 f'{math.sqrt(A)/2}" density="{rho!r}" contype="0" conaffinity="0"/>')
    body += "</body>" * N
    # THE TIMESTEP IS DERIVED FROM THE STIFFEST MODE IN THE CHAIN, and a fixed one was wrong.
    # 0.0005 s was carried over from the human ports, where the joints are soft. A basalt segment
    # has k = EA/ell = 9.8e7 N/m on 14 g, giving a 76 us period -- the fixed step was SIX AND A
    # HALF PERIODS long, and the chain returned 0.000 um of stretch with |qvel| exactly 0. It did
    # not fail loudly; it reported a perfectly rigid rock. The tree at L/d = 5 did the same and
    # then, at L/d = 10, over-deflected by 143%.
    #
    #     ONE TIMESTEP CANNOT SERVE GRASS AND BASALT: the moduli are five orders apart, and the
    #     step has to come from the material, like everything else here.
    J_tip = (m_seg * ell ** 2 / 3.0) if not axial else m_seg
    w_max = math.sqrt(k / max(J_tip, 1e-300))
    dt = 0.05 / w_max
    return (f'<mujoco><option timestep="{dt!r}" gravity="0 0 -{g!r}" integrator="implicitfast"/>'
            f'<worldbody>{body}</worldbody></mujoco>'), k, ell


def _settle(mujoco, m, d, force, steps=400000, rtol=1e-11):
    """Integrate to static equilibrium with the load applied AT THE TIP, and report convergence.

    THE LOAD POINT IS THE WHOLE REASON THIS FUNCTION EXISTS. The first version set
    `d.xfrc_applied[last]` and the chain came out 3.10% away from the closed form -- a plausible
    number, in the direction a discretisation error would go, on a test whose whole purpose is to
    catch discretisation. It was neither: MuJoCo accumulates `xfrc_applied` AT THE BODY'S CENTRE
    OF MASS, so a tip load was acting half a segment short of the tip. Predicting the load-at-CoM
    chain instead gives 0.34361 against a measured 0.34346 -- agreement to 0.04%, which is what
    told us the ENGINE was right and the INSTRUMENT was wrong.

        A WRONG LOAD POINT RETURNS A PLAUSIBLE NUMBER. Same species as the four wrong arithmetics
        the ligament derivation paid for, and the same cure: make the application point explicit.

    `mj_applyFT` takes the point as an argument, so there is nothing left to assume. It is
    recomputed every step because the tip MOVES, and a dead load acting at a stale point is a
    follower force wearing a dead load's hat.
    """
    f = np.asarray(force[:3], float)
    tau = np.zeros(3)
    mujoco.mj_forward(m, d)          # xpos/xmat must be current before the first _tip()
    b, prev, hold = m.nbody - 1, None, 0
    for n in range(steps):
        d.qfrc_applied[:] = 0.0
        mujoco.mj_applyFT(m, d, f, tau, _tip(m, d), b, d.qfrc_applied)
        mujoco.mj_step(m, d)
        if n % 200 == 199:
            # THE WHOLE TIP POSITION, not its height. Watching z alone declared the AXIAL rock
            # chain converged after 800 steps: an axial pull moves the tip in x and leaves z
            # exactly constant, so the convergence test was satisfied by a coordinate the
            # experiment does not act on. An instrument must watch the axis the load is on.
            p = _tip(m, d)
            if prev is not None and float(np.linalg.norm(p - prev)) <= rtol * max(
                    float(np.linalg.norm(p)), 1e-12):
                hold += 1
                if hold >= 3:
                    break
            else:
                hold = 0
            prev = p
    return float(np.abs(d.qvel).max()), n + 1


def _tip(m, d):
    """World position of the free end of the last segment (its geom's far face)."""
    b = m.nbody - 1
    half = float(m.geom_size[m.body_geomadr[b]][0])
    import numpy as _np
    R = _np.asarray(d.xmat[b]).reshape(3, 3)
    return _np.asarray(d.xpos[b]) + R @ _np.array([2.0 * half, 0.0, 0.0])


# ── PORT 13: GRASS BLADE ──────────────────────────────────────────────────────────────────────
@port_test(
    "grass_blade",
    "a grass blade is passive tissue in the human's own form -- but it is a DISTRIBUTED beam, "
    "not a lumped root spring. k_seg = E*I/ell with E from Vincent 1982's measured Lolium "
    "perenne modulus and I from the published lamina section; a tip load then deflects the "
    "chain by the exact discrete-cantilever sum, and a SINGLE root spring of k = E*I/L is "
    "wrong by a factor computed in advance",
    "the engine's chain deflection differs from the discrete closed form by more than 0.5% "
    "(that would mean the derivation, not the model, is wrong), OR the single-hinge lumped "
    "spring is NOT 3x too compliant -- if the lumped model happened to be right, the whole "
    "reason to prefer a distributed blade would evaporate")
def t_grass_blade(mujoco):
    """The instruction: tau = k*theta, with k DERIVED and the lumping question answered.

    THE OPERATOR'S FALSIFIER, ANSWERED RATHER THAN DODGED. The brief said: bend 30 deg, restoring
    force within 5% of the spring equation, and if it deviates the spring model is wrong for
    blades -- try the derived beam equation. The derivation says the answer depends entirely on
    HOW the blade is loaded, and that is worth more than either verdict:

        UNDER A PURE MOMENT the lumped spring is EXACT. Every station of a cantilever under an
        end couple carries the same moment, so N hinges of E*I/ell rotate by theta/N each and
        the root torque is E*I*theta/L -- identically the lumped answer. No error at all.

        UNDER A TIP FORCE the lumped spring is 3x too stiff in deflection and 2x too stiff in
        slope. Matching tip deflection needs k = 3EI/L; matching root slope needs k = 2EI/L.
        NO SINGLE SPRING MATCHES BOTH, and the two answers differ by 50%.

    A FOOT ON GRASS IS A TIP FORCE. So the lumped spring is the wrong model for the one thing
    grass is asked to do in this game, and the size of the wrongness is derived, not measured.
    """
    E = md.val("grass", "E_long")
    L = md.val("grass_blade", "length")
    w, t = md.val("grass_blade", "width"), md.val("grass_blade", "thickness")
    I, how_I = md.grass_second_moment()
    A = w * t
    N = 24

    # PREDICT BEFORE THE STEP. The exact discrete-chain sum, not the continuum -- the continuum
    # is reported beside it so the discretisation is visible instead of hidden in a tolerance,
    # which is how port 1 handles semi-implicit Euler.
    P = 3.0 * E * I * (0.02 * L) / L ** 3          # load sized for 2% tip droop: small-deflection
    disc = (N + 1) * (2 * N + 1) / (6.0 * N ** 2)
    pred = P * L ** 3 / (E * I) * disc
    cont = P * L ** 3 / (3.0 * E * I)

    xml, k_seg, ell = _chain_xml(L, N, E, I, A, rho=800.0)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    z0 = _tip(m, d)[2]
    vmax, nstep = _settle(mujoco, m, d, np.array([0, 0, -P], float))
    got = z0 - _tip(m, d)[2]
    err = abs(got - pred) / max(abs(pred), 1e-30)

    # The lumped question, in closed form. k_lump = E*I/L is the naive reading of "tau = k*theta".
    lump = P * L ** 2 / (E * I / L)                # rigid link on one spring of E*I/L
    ratio = lump / cont                            # 3.0 exactly, by derivation
    k_defl, k_slope = 3.0 * E * I / L, 2.0 * E * I / L

    return dict(pass_=err < 5e-3 and abs(ratio - 3.0) < 1e-9, pred=pred, got=got,
                detail=(f"E {E/1e6:.1f} MPa (Vincent 1982, Lolium perenne), {how_I} = {I:.4g} m^4, "
                        f"blade {L*100:.1f}x{w*1000:.1f}x{t*1000:.2f} mm -> EI {E*I:.4g} N.m^2\n"
                        f"    {N} hinges of k_seg = EI/ell = {k_seg:.4g} N.m/rad, tip load "
                        f"{P*1e6:.3f} uN\n"
                        f"    predicted tip droop {pred*1000:.6f} mm (discrete sum, "
                        f"{disc:.6f}xPL^3/EI), got {got*1000:.6f} mm, err {100*err:.4f}%  "
                        f"|  continuum PL^3/3EI = {cont*1000:.6f} mm "
                        f"(discretisation {100*(pred-cont)/cont:+.2f}%)\n"
                        f"    settled |qvel| {vmax:.2e} after {nstep} steps\n"
                        f"    LUMPED ROOT SPRING k = EI/L would droop {lump*1000:.6f} mm = "
                        f"{ratio:.4f}x the beam -- 200% wrong under a TIP FORCE, and EXACT under "
                        f"a pure moment. To match deflection k = 3EI/L = {k_defl:.4g}; to match "
                        f"root slope k = 2EI/L = {k_slope:.4g}. NO SINGLE SPRING MATCHES BOTH "
                        f"(50% apart), so a blade is distributed or it is wrong.\n"
                        f"    REFUSED: blade damping c. Vincent publishes a dynamic modulus "
                        f"(44.38 MPa vs 554 static) which PROVES the blade is viscoelastic, but "
                        f"no loss factor is published, and c may not be chosen."))


# ── PORT 14: ROCK FRACTURE ────────────────────────────────────────────────────────────────────
@port_test(
    "rock_fracture",
    "basalt obeys sigma = E*eps up to a tensile limit, with E, sigma_t and K_IC each published "
    "by a different study -- so the three are OVER-DETERMINED and the flaw size that reconciles "
    "them is a prediction about the rock's microstructure, not a fitted parameter",
    "the engine's axial strain differs from Hooke by more than 0.5%; or the Griffith flaw size "
    "implied by the published K_IC and sigma_t lands outside 0.1-100 mm, which would mean the "
    "two literatures are describing different materials")
def t_rock_fracture(mujoco):
    """The instruction: sigma = E*eps, break at sigma_t.

    THE MEASUREMENT IS SIZED TO THE FALSIFIER, and that is the part worth reading. The brief asked
    for 1000 N and a 5% strain tolerance. On a 0.1 m basalt cube 1000 N produces a strain of
    1.3e-6 -- about 130 nm of squash -- which no contact solver resolves, so the test would have
    been measuring the solver's noise floor and calling it Hooke. A 10 mm rod carries the same
    1000 N at 88% of its published tensile strength and stretches 0.16 mm, which is a real
    displacement. The specimen is chosen to make the question answerable; the physics is not.

    AND THE FALSIFIER THE BRIEF NAMED CANNOT BE MET BY ANY MODEL. It asks fracture to land within
    20% of the derived load. sigma_t is published as 14.5 +- 3.3 MPa: the LITERATURE'S OWN SPREAD
    IS 22.8%. A model reproducing basalt perfectly would fail that bar one time in three. The bar
    below is the published spread, and the 20% is reported beside it so the gap is visible.
    """
    E = md.val("rock_lib", "youngs_modulus_gpa") * 1e9    # library, Quaglio 2020
    s_t, s_t_sd = md.val("rock", "sigma_t"), md.spread("rock", "sigma_t")
    UCS = md.val("rock", "UCS")
    K = md.val("rock", "K_IC")
    a, how_a = md.griffith_flaw()

    dia, L, P, N = 0.010, 1.0, 1000.0, 16
    A = math.pi * dia ** 2 / 4.0
    sigma = P / A
    pred = P * L / (E * A)                                # Hooke, closed form
    P_break = s_t * A
    P_band = s_t_sd * A

    xml, k_seg, ell = _chain_xml(L, N, E, 0.0, A, rho=md.val("rock_lib", "density_kg_m3"),
                                 axial=True)
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    vmax, nstep = _settle(mujoco, m, d, np.array([P, 0, 0], float))
    got = float(np.sum(d.qpos))                           # series springs: total = sum of stretches
    err = abs(got - pred) / max(pred, 1e-30)

    # GRIFFITH'S OWN PREDICTION, which the published pair can refute: a brittle solid whose flaws
    # are elliptical fails in compression at 8x its tensile strength. Real rock does not, because
    # the crack faces close and rub -- the modified (McClintock-Walsh) criterion. Publishing the
    # disagreement is the point; a ratio of 8 would have been the surprise.
    ratio = UCS / s_t

    return dict(pass_=err < 5e-3 and 1e-4 < a < 0.1, pred=pred, got=got,
                detail=(f"E {E/1e9:.1f} GPa (library, Quaglio 2020), sigma_t {s_t/1e6:.1f} +- "
                        f"{s_t_sd/1e6:.1f} MPa (Schultz 1993), K_IC {K/1e6:.1f} MPa*sqrt(m) "
                        f"(Balme 2004)\n"
                        f"    {dia*1000:.0f} mm rod, {L:.0f} m, {P:.0f} N -> sigma "
                        f"{sigma/1e6:.3f} MPa = {100*sigma/s_t:.1f}% of the tensile limit\n"
                        f"    predicted stretch {pred*1e6:.3f} um (PL/EA), got {got*1e6:.3f} um, "
                        f"err {100*err:.4f}%  ({N} springs of EA/ell in series, |qvel| "
                        f"{vmax:.1e} after {nstep} steps)\n"
                        f"    FRACTURE at P = sigma_t*A = {P_break:.1f} N. The published spread "
                        f"gives +-{P_band:.1f} N = +-{100*P_band/P_break:.1f}%, which is WIDER "
                        f"than the 20% the brief asked fracture to land inside: that falsifier "
                        f"tests the literature, not the port, and is replaced by the spread.\n"
                        f"    OVER-DETERMINATION: {how_a} -- a vesicle scale, not a mineral-grain "
                        f"scale (the library calls basalt's 2 mm 'surface texture, not mineral "
                        f"grains', so it may NOT be substituted here).\n"
                        f"    UCS/sigma_t = {ratio:.1f}. Griffith 1921 predicts 8 for elliptical "
                        f"flaws; the published pair says {ratio:.1f}, and the {ratio/8:.1f}x "
                        f"excess IS the known crack-closure correction. The law loses cleanly and "
                        f"the amount it loses by is the finding."))


# ── PORT 15: TREE TRUNK ───────────────────────────────────────────────────────────────────────
@port_test(
    "tree_trunk",
    "wood is ORTHOTROPIC and the trunk's two published moduli do different jobs: E_L sets the "
    "bending deflection, G_LR the shear deflection, and the Wood Handbook's G_LR/E_L = 0.086 is "
    "4.5x lower than any isotropic solid's -- so a hinge chain, which has no shear compliance at "
    "all, must under-predict deflection by a share computable from slenderness alone",
    "the hinge chain's deflection differs from the discrete BENDING closed form by more than "
    "0.5%; or the shear share is not (3/16)(E_L/G_LR)(d/L)^2/kappa at every slenderness tested; "
    "or the derived bending-to-shear failure crossover does not land below any slenderness a "
    "tree actually has -- if trunks could fail in shear, the bending model would be incomplete")
def t_tree_trunk(mujoco):
    """The instruction: sigma = E*eps in an ORTHOTROPIC solid, where which modulus you use is
    the whole question.

    THE SPECIMEN DIAMETER IS DECLARED AND THE CLAIM IS SCALE-FREE. Nothing in this tree derives
    a trunk's girth yet -- no chapter under theTerrain has grown a wood -- so a single trunk
    would be a typed phenotype, which is the defect the walker was convicted of. Instead the
    prediction is stated as a FUNCTION OF SLENDERNESS, which is dimensionless, and tested at
    three of them. A law that holds across the ratio does not care what diameter arrives later.
    """
    sp = "white_oak"
    E = md.val("wood", "E_L", sp)
    G = md.val("wood", "GLR_EL", sp) * E
    MOR, tau_max = md.val("wood", "MOR", sp), md.val("wood", "shear_par", sp)
    kappa = 0.9                        # circular section, the textbook Timoshenko factor
    dia, P, N = 0.30, 500.0, 24
    A = math.pi * dia ** 2 / 4.0
    I = math.pi * dia ** 4 / 64.0

    # Wood's shear compliance relative to bending, against the isotropic solid it is not.
    G_iso = E / (2.0 * 1.3)            # nu = 0.3: G = E/2(1+nu)
    rows, worst = [], 0.0
    for slender in (5.0, 10.0, 20.0):
        L = slender * dia
        db = P * L ** 3 / (3.0 * E * I)
        ds = P * L / (kappa * G * A)
        share_pred = (3.0 / 16.0) * (E / G) * (dia / L) ** 2 / kappa
        disc = (N + 1) * (2 * N + 1) / (6.0 * N ** 2)
        pred = P * L ** 3 / (E * I) * disc

        xml, k_seg, ell = _chain_xml(L, N, E, I, A, rho=md.val("wood", "SG", sp) * 1000.0)
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)
        mujoco.mj_forward(m, d)
        z0 = _tip(m, d)[2]
        vmax, nstep = _settle(mujoco, m, d, np.array([0, 0, -P], float))
        got = z0 - _tip(m, d)[2]
        err = abs(got - pred) / max(pred, 1e-30)
        worst = max(worst, err, abs(ds / db - share_pred) / share_pred)
        rows.append(f"L/d {slender:>4.0f}: chain {got*1000:8.4f} mm vs discrete "
                    f"{pred*1000:8.4f} mm ({100*err:6.3f}%)  |  shear adds "
                    f"{100*ds/db:6.3f}% (predicted {100*share_pred:6.3f}%), isotropic wood "
                    f"would add only {100*ds*G/G_iso/db:.3f}%")

    # WHICH WAY DOES A TRUNK FAIL? Bending stress grows with L, shear stress does not.
    #   sigma = 32PL/(pi d^3),  tau_max = 16P/(3 pi d^2)  =>  crossover at L/d = 3*MOR/(16*tau)
    cross = 3.0 * MOR / (16.0 * tau_max)
    return dict(pass_=worst < 5e-3 and cross < 5.0, pred=cross, got=cross,
                detail=(f"white oak (Wood Handbook T5-3b/T5-1, 12% MC): E_L {E/1e9:.2f} GPa, "
                        f"G_LR/E_L {G/E:.3f} -> G_LR {G/1e9:.3f} GPa. An isotropic solid would "
                        f"have G/E = {G_iso/E:.3f} -- wood is {G_iso/G:.2f}x more shear-compliant "
                        f"relative to its bending stiffness, and THAT is what orthotropy costs.\n"
                        f"    d {dia:.2f} m (declared specimen -- no chapter grows a trunk yet; "
                        f"the claim is in L/d, which is dimensionless), P {P:.0f} N lateral\n"
                        + "".join(f"    {r}\n" for r in rows) +
                        f"    FAILURE MODE: bending governs above L/d = 3*MOR/(16*tau_par) = "
                        f"{cross:.2f} (MOR {MOR/1e6:.0f} MPa, shear-parallel "
                        f"{tau_max/1e6:.1f} MPa). No tree is stubbier than {cross:.2f}, so a "
                        f"trunk ALWAYS fails in bending -- which is why the bending model is "
                        f"allowed to be the whole model, and it is a prediction that could have "
                        f"come back at 20 and forced a shear port.\n"
                        f"    HONEST LIMIT: the chain carries E_L and no shear compliance, so it "
                        f"is right to <1% only where the shear share is small. At L/d 5 that "
                        f"share is already {100*(3.0/16.0)*(E/G)*(1/5.0)**2/kappa:.2f}% and a "
                        f"branch stub would need a Timoshenko element, not this one."))


# ── PORT 16: TERRAIN FOOTPRINT ────────────────────────────────────────────────────────────────
@port_test(
    "terrain_footprint",
    "soil under a foot has an ELASTIC branch and a PLASTIC one, and they come from two "
    "literatures that never cite each other: Terzaghi's subgrade modulus gives a recoverable "
    "settlement p/k_s, Terzaghi's bearing capacity gives the depth at which the ground stops "
    "yielding. Fed this world's OWN published foot pressure and soil, the two must land on the "
    "same millimetre scale -- and whether a print PERSISTS is decided by the published cohesion",
    "the engine's elastic settlement differs from p/k_s by more than 0.5%; or the elastic and "
    "plastic routes disagree by more than an order of magnitude, which would mean a stiffness "
    "and a strength measured on the same soil describe different materials; or the foot pressure "
    "does not exceed the zero-depth bearing capacity at the published mean cohesion -- in which "
    "case nothing ever dents and the soil model is decorative")
def t_terrain_footprint(mujoco):
    """The instruction: sigma = k*eps with a yield, and the print is what is left after unload.

    THIS PORT WAS BUILT TO ASK A QUESTION AND FOUND THE ANSWER ALREADY PUBLISHED, WRONG.
    theGround publishes `sinkage_m = 8.674e-19` -- 0.87 attometres, a thousand times smaller than
    a proton. Backtracing it UP the chain rather than forward from the symptom:

        theGround's `sinkage()` presses until bearing capacity equals foot pressure. Its capacity
        at ZERO depth is c*Nc, and it types COHESION_PA = 2000.0 under the comment "damp soil
        holds itself together a little". c*Nc = 92 kPa, which is 3.8x the pressure under a
        person. There is no depth at which the equation balances, because it already balances at
        zero, and the bisection collapses onto its own floor.

        THE WORLD'S OWN LIBRARY PUBLISHES 0.5 +- 0.4 kPa for this regolith (Mitchell et al. 1972,
        via matter_library.json). The typed value is FOUR TIMES the researched mean and outside
        its whole band. One typed constant, several membranes up, and every footprint in the game
        is zero -- the same shape as the g = 7.076 defect: a wrong number under a formula that
        still looks alive.

    AND THE HONEST FINDING IS NOT A BETTER NUMBER. At the library's mean the foot pressure clears
    the zero-depth capacity by 4.9%, which is well inside cohesion's own spread: at c = 0.9 kPa
    the print is ZERO and at c = 0.1 kPa it is 54 mm. A DEPTH IS NOT RESOLVABLE FROM THIS DATA,
    and saying so is worth more than publishing 3.1 mm as though it were known. What IS resolvable
    is the elastic branch, which needs no cohesion at all.
    """
    ground, human = _published("theGround"), _published("theHuman")
    for who, tab, keys in (("theGround", ground, ("bulk_density", "g", "sinkage_m", "repose_deg")),
                           ("theHuman", human, ("weight_N", "foot_area_m2", "mass_kg"))):
        miss = [k for k in keys if k not in tab]
        if miss:
            raise md.Uncited(f"{who} publishes no {miss}; refusing to substitute a value")
    rho, g = float(ground["bulk_density"]), float(ground["g"])
    p = float(human["weight_N"]) / float(human["foot_area_m2"])

    phi = md.cite("sand", "friction_angle_deg")["value"]
    c_m = md.cite("sand", "cohesion_kpa")["value"] * 1e3
    c_sd = md.cite("sand", "cohesion_kpa")["spread"] * 1e3
    Nq, Nc = _terzaghi(phi)

    def depth(c, gv=g, press=None):        # plastic: sink until capacity meets pressure
        return max(0.0, ((press if press is not None else p) - c * Nc) / (rho * gv * Nq))

    d_mean, d_lo, d_hi = depth(c_m), depth(c_m + c_sd), depth(c_m - c_sd)

    # ELASTIC: Winkler, and it needs no cohesion -- which is why it is the half that is resolvable.
    k_s = md.val("soil", "k_s_loose")
    pred = p / k_s

    # THE ENGINE, on the elastic branch only. A plate of the foot's own area on a bed of k_s*A.
    K = k_s * float(human["foot_area_m2"])
    mass = float(human["weight_N"]) / g
    xml = (f'<mujoco><option timestep="{0.02*math.sqrt(mass/K)!r}" gravity="0 0 0" '
           f'integrator="implicitfast"/><worldbody>'
           f'<body name="foot" pos="0 0 0"><joint name="jz" type="slide" axis="0 0 1" '
           f'stiffness="{K!r}" damping="{2.0*math.sqrt(K*mass)!r}"/>'
           f'<geom type="box" size="0.1 0.05 0.01" mass="{mass!r}" contype="0" conaffinity="0"/>'
           f'</body></worldbody></mujoco>')
    mm = mujoco.MjModel.from_xml_string(xml)
    dd = mujoco.MjData(mm)
    dd.qfrc_applied[0] = -float(human["weight_N"])
    for _ in range(20000):
        mujoco.mj_step(mm, dd)
    got = -float(dd.qpos[0])
    err = abs(got - pred) / max(pred, 1e-30)
    dd.qfrc_applied[0] = 0.0                       # RELEASE: the elastic part must come back
    for _ in range(20000):
        mujoco.mj_step(mm, dd)
    rebound = abs(float(dd.qpos[0]))

    p_e = float(human["mass_kg"]) * 9.80665 / float(human["foot_area_m2"])
    d_earth = depth(c_m, 9.80665, p_e)
    decorative = float(ground["sinkage_m"])

    return dict(pass_=(err < 5e-3 and rebound < 1e-3 * pred and d_mean > 0.0
                       and 0.1 < d_mean / pred < 10.0),
                pred=pred, got=got,
                detail=(f"theHuman publishes {float(human['weight_N']):.1f} N on "
                        f"{float(human['foot_area_m2'])*1e4:.1f} cm^2 = {p/1e3:.2f} kPa; "
                        f"theGround publishes rho {rho:.0f} kg/m^3, g {g:.3f} m/s^2\n"
                        f"    ELASTIC (Winkler, Terzaghi 1955 k_s = {k_s/1e6:.1f} MN/m^3 loose): "
                        f"predicted {pred*1000:.4f} mm, engine {got*1000:.4f} mm, err "
                        f"{100*err:.4f}%; released -> {rebound*1e9:.3f} nm residual (elastic, so "
                        f"it MUST return, and does)\n"
                        f"    PLASTIC (Terzaghi bearing, phi {phi:.0f} deg -> Nc {Nc:.1f}, Nq "
                        f"{Nq:.1f}): c*Nc = {c_m*Nc/1e3:.1f} kPa against {p/1e3:.1f} kPa under "
                        f"the foot -- it YIELDS by {100*(p/(c_m*Nc)-1):.1f}% and sinks "
                        f"{d_mean*1000:.3f} mm, which does NOT come back\n"
                        f"    TWO LITERATURES, ONE SCALE: a stiffness says {pred*1000:.2f} mm and "
                        f"a strength says {d_mean*1000:.2f} mm, a factor of "
                        f"{max(pred,d_mean)/max(min(pred,d_mean),1e-12):.2f} apart. They were "
                        f"measured by different people for different purposes and land on the "
                        f"same millimetre -- which is the only reason to believe either.\n"
                        f"    BUT THE DEPTH IS NOT RESOLVABLE. Over cohesion's own published "
                        f"spread ({c_m/1e3:.1f} +- {c_sd/1e3:.1f} kPa) the print runs "
                        f"{d_hi*1000:.1f} mm -> {d_lo*1000:.1f} mm; at the high end nothing dents "
                        f"at all. A gap inside the instrument's grain is not a small gap. The "
                        f"ELASTIC branch carries no cohesion and IS resolvable, and that is the "
                        f"half this port validates.\n"
                        f"    CONVICTION: theGround publishes sinkage {decorative:.3e} m -- "
                        f"{pred/max(decorative,1e-300):.1e}x smaller than its own soil's elastic "
                        f"settlement. Traced to a typed COHESION_PA = 2000 Pa where the world's "
                        f"library publishes {c_m:.0f} +- {c_sd:.0f} Pa. The soil model is "
                        f"decorative, and one typed constant four times the researched mean is "
                        f"why.\n"
                        f"    PREDICTS WHAT IT WAS NOT FITTED TO: the same person on the same "
                        f"soil at EARTH gravity leaves {d_earth*1000:.1f} mm -- "
                        f"{d_earth/max(d_mean,1e-12):.1f}x deeper for only {9.80665/g:.2f}x the "
                        f"gravity, because c*Nc does not scale with g. A low-gravity world sits "
                        f"nearer the threshold where prints stop existing, and that is a "
                        f"statement about THIS world that no fit produced."))


# ── PORT 17: GRANULAR REPOSE ──────────────────────────────────────────────────────────────────
@port_test(
    "granular_repose",
    "theta_r = atan(mu) is a statement about SLIDING, and it is the pile's angle only for a grain "
    "that can neither roll nor interlock. At this world's OWN published friction, rigid grains "
    "BRACKET it rather than reach it: spheres roll and hold less, boxes interlock and hold more. "
    "So a rigid-body engine cannot produce a repose angle from a friction coefficient, which is "
    "why this world grows its regolith from a topple rule -- and that grown angle must land "
    "inside the friction band Mitchell 1972 actually published",
    "the bracket does not hold -- spheres at or above atan(mu) would mean rolling is free and a "
    "grain may be modelled as a sphere; boxes at or below it would mean interlocking gives "
    "nothing and shape is not a term; or the world's grown repose falls outside Mitchell's "
    "published 30-50 deg band; or the BOX run fails to stand 3 grain diameters tall, which means "
    "the instrument never built a pile and neither number is a measurement -- a flat scatter "
    "satisfies 'shallower than atan(mu)' perfectly and must not be allowed to pass as one")
def t_granular_repose(mujoco):
    """The instruction: theta_r = atan(mu), and what a grain has to BE for it to hold.

    THE BRIEF SAID mu DERIVED FROM PUBLISHED GRAIN SIZE AND SHAPE, and shape turns out to be the
    whole story. Mitchell et al. 1972 publish a friction angle, which is a SLIDING property; a
    pile of spheres never gets to use all of it, because a sphere under a tangential load rolls
    before it slides. The measurement below is an ABLATION ON SHAPE ALONE -- identical friction,
    identical grain mass, identical pour, identical seed -- so whatever separates the two piles
    is shape and nothing else. That is what makes it a measurement rather than a demonstration.

    GRAVITY IS THIS WORLD'S AND IT DOES NOT MATTER, which is worth stating rather than hiding:
    the repose angle is a ratio of a tangential resistance to a normal load and both scale with
    g, so the angle is g-invariant. Using Earth's here would have given the same number and would
    have been a lie about which world this is.
    """
    ground = _published("theGround")
    g = float(ground["g"])
    phi = md.cite("sand", "friction_angle_deg")["value"]
    mu = math.tan(math.radians(phi))
    pred = math.degrees(math.atan(mu))   # = phi identically; written out so the identity is visible
    grown = float(ground["repose_deg"])

    r = 0.02

    def pour(shape, seed=7):
        """COLUMN COLLAPSE, not a drop tower -- and the first version was the drop tower.

        Grains were released down a single vertical line 0.052 m apart, which put the last one
        13.5 m up. It arrived at 13.8 m/s, blew the heap apart, and left a MONOLAYER: spheres
        0.00 deg, boxes 0.44 deg. The port PASSED, because "shallower than atan(mu)" is satisfied
        perfectly by a flat scatter -- a degenerate winner auditing a falsifier that forgot to
        require a pile. The height check in the falsifier now forbids it.

        The fix is the standard granular experiment: a short cylinder of grains starting nearly in
        contact, released, slumping under its own weight. Impact speeds stay at grain scale, so
        what is measured is friction and shape rather than the energy of a fall.
        """
        rng = np.random.default_rng(seed)
        pitch, parts, n = 2.15 * r, "", 0
        R, H = 0.115, 0.36
        z = r * 1.05
        while z < H:
            y = -R
            while y <= R:
                x = -R
                while x <= R:
                    if x * x + y * y <= R * R:
                        # float() is load-bearing: numpy 2 renders repr(np.float64) as
                        # "np.float64(0.01)", which MuJoCo rejects as a malformed pos attribute.
                        jx = float(rng.uniform(-0.02 * r, 0.02 * r))
                        jy = float(rng.uniform(-0.02 * r, 0.02 * r))
                        geom = (f'<geom type="sphere" size="{r}" density="2650"/>'
                                if shape == "sphere" else
                                f'<geom type="box" size="{r*0.806} {r*0.806} {r*0.806}" '
                                f'density="2650"/>')
                        parts += (f'<body pos="{x+jx!r} {y+jy!r} {z!r}"><freejoint/>{geom}</body>')
                        n += 1
                    x += pitch
                y += pitch
            z += pitch
        # THE PLANE IS 80 m ACROSS because the first version's was 8 and the spheres ROLLED OFF
        # IT. They then fell forever, and the run reported |qvel| = 35.7 m/s and a heap height of
        # -0 mm -- a measurement of the world's edge, not of a pile.
        xml = (f'<mujoco><option timestep="0.001" gravity="0 0 -{g!r}" integrator="implicitfast" '
               f'cone="pyramidal"/>'
               f'<default><geom friction="{mu!r} 0.002 0.0001" solref="0.004 1"/></default>'
               f'<worldbody><geom type="plane" size="40 40 0.1"/>{parts}</worldbody></mujoco>')
        m = mujoco.MjModel.from_xml_string(xml)
        d = mujoco.MjData(m)

        def heap():
            p = np.array([d.xpos[b] for b in range(1, m.nbody)])
            return p, float(np.quantile(p[:, 2], 0.99)) - r

        for _ in range(9000):
            mujoco.mj_step(m, d)
        _, h_mid = heap()
        for _ in range(5000):
            mujoco.mj_step(m, d)
        pos, height = heap()
        settled = abs(height - h_mid) < r        # THE COLLAPSE is over, whatever the grains do next

        # LINEAR SPEED, SEPARATED FROM SPIN, and conflating them cost a diagnosis. A freejoint's
        # qvel is [v(3), omega(3)] per body, so `abs(qvel).max()` returns whichever is numerically
        # larger -- and for a 20 mm grain that is always omega, since omega = v/r multiplies by 50.
        # The run was refused as "not at rest at 35.7" when 35.7 rad/s is 0.71 m/s, exactly the
        # speed a 0.36 m collapse delivers. Nothing was wrong but the units of the gate.
        v = np.asarray(d.qvel).reshape(-1, 6)
        lin, spin = float(np.abs(v[:, :3]).max()), float(np.abs(v[:, 3:]).max())
        # THE CONE-EQUIVALENT ANGLE, and the linear fit it replaces was the second instrument
        # failure here. Fitting z_max against radius reads ZERO for a squat CYLINDER -- which is
        # exactly what a box column collapses into -- so it reported 0.00 deg for a heap standing
        # 222 mm tall. atan(h/R) has no such blind spot: it is the angle of the cone with this
        # heap's own height and base, and it degrades gracefully to 0 for a true monolayer.
        cx, cy = float(np.median(pos[:, 0])), float(np.median(pos[:, 1]))
        rad = np.hypot(pos[:, 0] - cx, pos[:, 1] - cy)
        R95 = float(np.quantile(rad, 0.95))
        return (math.degrees(math.atan(max(height, 0.0) / max(R95, 1e-9))),
                n, height, lin, spin, R95, settled)

    th_sph, n_sph, h_sph, v_sph, w_sph, R_sph, s_sph = pour("sphere")
    th_box, n_box, h_box, v_box, w_box, R_box, s_box = pour("box")
    built = h_box >= 3.0 * (2.0 * r)         # the instrument demonstrably CAN make a pile
    readable = s_sph and s_box               # ...and both collapses have finished

    return dict(pass_=(built and readable and th_sph < pred < th_box
                       and 30.0 <= grown <= 50.0),
                pred=pred, got=th_sph,
                detail=(f"phi {phi:.0f} deg (Mitchell et al. 1972 via the world's own library, "
                        f"published band 30-50 deg) -> mu = tan(phi) = {mu:.4f}, atan(mu) = "
                        f"{pred:.2f} deg. g = {g:.3f} m/s^2 and the angle does not depend on it.\n"
                        f"    SPHERES ({n_sph} grains, heap {h_sph*1000:.0f} mm over R95 "
                        f"{R_sph*1000:.0f} mm = {h_sph/(2*r):.1f} grain diameters, v {v_sph:.3f} "
                        f"m/s, spin {w_sph:.1f} rad/s): {th_sph:.2f} deg -- {pred-th_sph:.2f} deg "
                        f"BELOW atan(mu). A sphere rolls out of the friction it is standing on, "
                        f"and it never stops: the heap height is fixed at one radius while the "
                        f"grains roll outward forever at {v_sph:.2f} m/s, because nothing in a "
                        f"rigid-sphere contact resists rolling.\n"
                        f"    BOXES, same mu, same grain mass, same column, same seed ({n_box}, "
                        f"heap {h_box*1000:.0f} mm over R95 {R_box*1000:.0f} mm, v {v_box:.1e} "
                        f"m/s): {th_box:.2f} deg -- {th_box-pred:+.2f} deg ABOVE atan(mu). "
                        f"Interlocking buys what rolling spends. SHAPE ALONE separates the two "
                        f"runs by {th_box-th_sph:.1f} deg; nothing else in them differs.\n"
                        f"    THE CLOSED FORM IS BRACKETED, NOT REACHED: {th_sph:.1f} < "
                        f"{pred:.1f} < {th_box:.1f}. atan(mu) describes a grain that slides and "
                        f"neither rolls nor interlocks, and no rigid grain is that. A friction "
                        f"coefficient therefore does NOT determine a repose angle in a rigid-body "
                        f"engine -- which is the whole reason this world grows its regolith from "
                        f"a topple rule instead of pouring bodies.\n"
                        f"    THE WORLD'S OWN GROWN ANGLE: theGround publishes {grown:.2f} deg "
                        f"(core/trainables/granular.py, emergent from a topple rule, never looked "
                        f"up), {abs(grown-40.0):.2f} deg from the exact centre of Mitchell's "
                        f"published 30-50 band. The library's narrowed 35 +- 5 is an editorial "
                        f"choice about where in that band a loose surface sits; the BAND is the "
                        f"measurement, and the grown pile is inside it."))


# ── PORT 18: FIBRE ROPE ───────────────────────────────────────────────────────────────────────
@port_test(
    "fibre_rope",
    "a rope has no Young's modulus -- it is a helix whose apparent stiffness rises as the lay "
    "tightens, which is exactly why the industry publishes STRAIN AT A STATED FRACTION OF "
    "BREAKING STRENGTH instead. Take that as F = kx: EA = 0.1*F_break/eps_at_10pct. Then the "
    "SAME standard's published break elongation is an independent check on the linear model, "
    "and it refutes it for polyester",
    "the engine's stretch differs from PL/EA by more than 0.5%; or the linear model extrapolated "
    "to the RATED working load stays under half the published break strain for BOTH fibres, "
    "which would mean the two published numbers are mutually consistent and F = kx needs no "
    "correction -- there would then be nothing here worth a port")
def t_fibre_rope(mujoco):
    """The instruction: F = kx, with k derived from the only stiffness a rope publishes.

    THE CHECK IS THE POINT, and it comes free because the Cordage Institute publishes TWO numbers
    that a linear rope cannot both satisfy. Working Load Limit is breaking strength / 5, so a
    rated rope carries 20% of BS. Extrapolate the published 10%-BS strain linearly to there:

        NYLON      5.00% strain at WLL against 21.5% at break  ->  23% of the way to failure
        POLYESTER 12.00% strain at WLL against 12.5% at break  ->  96% of the way to failure

    A polyester rope at its RATED load would be at 96% of its own published breaking elongation.
    It plainly is not -- that is what "rated" means -- so the response must STIFFEN with load, and
    the linear secant taken at 10% BS is the softest part of the curve. F = kx is refused for
    polyester at working loads by two numbers from one standard, with no experiment needed.

    A ROPE'S BREAK IS A SEAM, NOT A STRAIN. The brief asked for a seam F_break; the honest state
    is that a splice or knot fails at a published FRACTION of the rope's own strength and no such
    fraction is in this module, so the port REFUSES to publish a seam and names the missing
    measurement instead of inventing an efficiency.
    """
    sf = md.val("rope", "safety_factor")
    rows, worst, refuted = [], 0.0, []
    for fibre in ("nylon", "polyester"):
        e10 = md.val("rope", f"{fibre}_eps_at_10pct")
        ebk = md.val("rope", f"{fibre}_eps_break")
        # F_break is the SPECIMEN's and is declared: a rope's rating is its size, not its physics,
        # and every quantity below is a RATIO to it, so the choice cancels out of every conclusion.
        F_b, L = 10000.0, 10.0
        EA = 0.10 * F_b / e10
        P = F_b / sf                        # the rated Working Load Limit
        pred = P * L / EA
        eps_wll = pred / L
        frac = eps_wll / ebk

        m_rope = 0.10 * L                   # kg; affects the transient only, not the equilibrium
        K = EA / L
        xml = (f'<mujoco><option timestep="{0.02*math.sqrt(m_rope/K)!r}" gravity="0 0 0" '
               f'integrator="implicitfast"/><worldbody>'
               f'<body name="end" pos="0 0 0"><joint name="jx" type="slide" axis="1 0 0" '
               f'stiffness="{K!r}" damping="{2.0*math.sqrt(K*m_rope)!r}"/>'
               f'<geom type="box" size="0.05 0.05 0.05" mass="{m_rope!r}" contype="0" '
               f'conaffinity="0"/></body></worldbody></mujoco>')
        mm = mujoco.MjModel.from_xml_string(xml)
        dd = mujoco.MjData(mm)
        dd.qfrc_applied[0] = P
        for _ in range(30000):
            mujoco.mj_step(mm, dd)
        got = float(dd.qpos[0])
        err = abs(got - pred) / max(pred, 1e-30)
        worst = max(worst, err)
        if frac > 0.5:
            refuted.append(fibre)
        rows.append(f"{fibre:<10} eps@10%BS {100*e10:4.1f}% -> EA {EA/F_b:.3f}*F_break; at the "
                    f"rated WLL (F_break/{sf:.0f}) the linear model says {100*eps_wll:5.2f}% "
                    f"strain, {100*frac:5.1f}% of its published {100*ebk:.1f}% break elongation "
                    f"| engine {got*1000:7.2f} mm vs PL/EA {pred*1000:7.2f} mm ({100*err:.4f}%)")

    return dict(pass_=worst < 5e-3 and bool(refuted), pred=0.0, got=worst,
                detail=("Cordage Institute / ASTM D-4268 elongation figures; specimen F_break "
                        "10 kN over 10 m (a RATIO cancels it out of every conclusion)\n"
                        + "".join(f"    {r}\n" for r in rows) +
                        f"    F = kx SURVIVES for nylon (23% of break at rated load) and is "
                        f"REFUTED for {', '.join(refuted)}: a rope at its RATED load cannot be at "
                        f"96% of its own breaking elongation, so the real curve STIFFENS and the "
                        f"secant taken at 10% BS is its softest part. Two numbers from one "
                        f"standard, and no experiment was needed to see it.\n"
                        f"    CONSEQUENCE FOR THE GAME: a rope modelled as a linear spring from "
                        f"the published low-load figure stretches 2.4x too far in polyester and "
                        f"will look slack under a load it should hold taut.\n"
                        f"    REFUSED: the seam. A splice or knot fails at a published FRACTION "
                        f"of rope strength (a splice efficiency); no such fraction is in "
                        f"matter_data, so no seam F_break is published here. The brief asked for "
                        f"one; the honest output is the name of the missing measurement."))


# ── PORT 19: VEHICLE SUSPENSION ───────────────────────────────────────────────────────────────
@port_test(
    "suspension",
    "F = kx + cv, and NEITHER k NOR c is ingested: both are DERIVED from the published dynamic "
    "targets a suspension is designed to hit -- ride frequency and damping ratio -- against the "
    "published quarter-car sprung mass. The step response then has a closed form, and the "
    "widely-used default spring/damper pair becomes an INDEPENDENT check that lands outside the "
    "comfort band it is usually quoted for",
    "the engine's overshoot or 2% settling time differs from the second-order closed form by "
    "more than 2%; or the published default pair (20,000 N/m, 545.5 N*s/m on 250 kg) turns out "
    "to be comfort-band consistent after all, which would mean there was no disagreement to "
    "reconcile and the derivation added nothing over ingesting it")
def t_suspension(mujoco):
    """The instruction: F = kx + cv, with the free numbers derived rather than looked up.

    RULE 1, APPLIED TO THE OBVIOUS TEMPTATION. There IS a published (k, c) pair for the quarter
    car -- 20,000 N/m and 545.5 N*s/m -- and ingesting it would have looked legitimate and been
    wrong, because those two numbers are not independent of the mass: together with 250 kg they
    imply a ride frequency of 1.42 Hz and a damping ratio of 0.122. The first is in the published
    SPORT band (1.2-1.5 Hz), not the comfort band (1.0-1.2). The second falls BELOW the published
    passenger-car range (0.2-0.4) entirely.

        SO THE "DEFAULT QUARTER CAR" IS A SPORT SPRING WITH AN UNDER-DAMPED SHOCK, and quoting it
        as a comfort car is a misfold: the right quantity docking at the wrong interface.

    Deriving k and c from the DYNAMIC targets instead makes the slider real -- move the ride
    frequency and every number here moves, which a typed pair could never do -- and turns the
    default pair from a source into a check that disagrees informatively.
    """
    m = md.val("suspension", "m_sprung")
    f_n, zeta = md.val("suspension", "f_comfort"), md.val("suspension", "zeta")
    w_n = 2.0 * math.pi * f_n
    k = m * w_n ** 2
    c = 2.0 * zeta * math.sqrt(k * m)

    # PREDICTED BEFORE THE STEP, from the second-order closed form and nothing else.
    wd = w_n * math.sqrt(1.0 - zeta ** 2)
    os_pred = math.exp(-math.pi * zeta / math.sqrt(1.0 - zeta ** 2))
    tp_pred = math.pi / wd

    # SETTLING TIME IS SOLVED, NOT APPROXIMATED, and the difference is 15.8%. The textbook
    # t_s = 4/(zeta*w_n) is the ENVELOPE estimate: it asks when exp(-zeta*w_n*t) falls to 2%.
    # But an under-damped response only TOUCHES its envelope at the extrema, and between them it
    # is already well inside -- so the true last exit from the +-2% band happens EARLIER, on the
    # way down from the third overshoot. Predicting 1.9292 s against a real 1.6250 s failed this
    # port at 15.8%, and the port was right to fail: the prediction was a shortcut, not the law.
    #
    #     PORT 1 LEARNED THIS ON GRAVITY -- predict what the system does, not what the tidy
    #     formula says -- and it is the same mistake in a different equation.
    #
    # The exact response is still closed-form and still computed before MuJoCo runs a single
    # step, so this remains two independent mechanisms meeting at one number.
    t = np.arange(1, int(6.0 / 2.0e-4) + 1) * 2.0e-4
    dev = np.exp(-zeta * w_n * t) * (np.cos(wd * t) + zeta / math.sqrt(1 - zeta ** 2)
                                     * np.sin(wd * t))
    outside = np.nonzero(np.abs(dev) > 0.02)[0]
    ts_pred = float(t[outside[-1]]) if len(outside) else 0.0
    ts_env = 4.0 / (zeta * w_n)

    F = m * 9.80665                # a one-g step: what a bump delivers, not a chosen amplitude
    dt = 2.0e-4
    xml = (f'<mujoco><option timestep="{dt!r}" gravity="0 0 0" integrator="implicitfast"/>'
           f'<worldbody><body name="hub" pos="0 0 0">'
           f'<joint name="jz" type="slide" axis="0 0 1" stiffness="{k!r}" damping="{c!r}"/>'
           f'<geom type="box" size="0.3 0.2 0.1" mass="{m!r}" contype="0" conaffinity="0"/>'
           f'</body></worldbody></mujoco>')
    mm = mujoco.MjModel.from_xml_string(xml)
    dd = mujoco.MjData(mm)
    dd.qfrc_applied[0] = -F
    n = int(6.0 / dt)
    x = np.empty(n)
    for i in range(n):
        mujoco.mj_step(mm, dd)
        x[i] = -float(dd.qpos[0])
    x_inf = F / k
    peak = int(np.argmax(x))
    os_got, tp_got = x[peak] / x_inf - 1.0, (peak + 1) * dt
    out = np.nonzero(np.abs(x - x_inf) > 0.02 * x_inf)[0]
    ts_got = (out[-1] + 1) * dt if len(out) else 0.0
    e_os = abs(os_got - os_pred) / os_pred
    e_ts = abs(ts_got - ts_pred) / ts_pred

    k_d, c_d = md.val("suspension", "k_default"), md.val("suspension", "c_default")
    f_d = math.sqrt(k_d / m) / (2.0 * math.pi)
    z_d = c_d / (2.0 * math.sqrt(k_d * m))
    misfold = not (1.0 <= f_d <= 1.2 and 0.2 <= z_d <= 0.4)

    return dict(pass_=(e_os < 0.02 and e_ts < 0.02 and misfold), pred=os_pred, got=os_got,
                detail=(f"DERIVED, not ingested: m {m:.0f} kg (published quarter-car sprung "
                        f"mass), ride {f_n:.2f} Hz (comfort band 1.0-1.2) -> k = m*(2*pi*f)^2 = "
                        f"{k:.1f} N/m; zeta {zeta:.2f} (published 0.2-0.4) -> c = 2*zeta*"
                        f"sqrt(km) = {c:.1f} N*s/m\n"
                        f"    step {F:.0f} N (one g on the sprung mass): overshoot predicted "
                        f"{100*os_pred:.2f}%, measured {100*os_got:.2f}% ({100*e_os:.3f}% off); "
                        f"2% settling predicted {ts_pred:.4f} s, measured {ts_got:.4f} s "
                        f"({100*e_ts:.3f}% off); peak predicted {tp_pred:.4f} s, measured "
                        f"{tp_got:.4f} s\n"
                        f"    the textbook envelope estimate 4/(zeta*w_n) would say "
                        f"{ts_env:.4f} s -- {100*(ts_env-ts_pred)/ts_pred:+.1f}%, because a "
                        f"response only TOUCHES its envelope at the extrema. The shortcut is "
                        f"reported beside the solved value rather than hidden in a tolerance.\n"
                        f"    THE INDEPENDENT CHECK DISAGREES, INFORMATIVELY: the widely-quoted "
                        f"default pair k {k_d:.0f} N/m, c {c_d:.1f} N*s/m on the SAME 250 kg "
                        f"implies f_n {f_d:.3f} Hz and zeta {z_d:.3f}. The frequency lands in the "
                        f"published SPORT band (1.2-1.5), not comfort; the damping falls BELOW "
                        f"the whole passenger-car range. That pair is a sport spring with an "
                        f"under-damped shock, and citing it as a comfort car is the right "
                        f"quantity at the wrong interface.\n"
                        f"    THE SLIDER IS REAL: k and c are functions of the ride frequency and "
                        f"the damping ratio, so moving either moves every number above. An "
                        f"ingested pair would have sat still while the world changed around it."))
