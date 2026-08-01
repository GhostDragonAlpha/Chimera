"""measured.py -- where a body's numbers come from, so no membrane has to invent one.

THE PROBLEM THIS EXISTS FOR. Membranes were carrying anthropometry as module constants with comments
saying "measured" -- `LEG_MASS_FRAC = 0.161`, `COM_FRAC = 0.575`, `EYE_FRAC = 0.936`. A comment is not
a citation, and this project already has a name for that failure: a literal wearing a comment. It is
the one class of defect no checker can catch, because nothing can read a comment and tell whether it
is true.

Worse, it is the wrong METHOD. The manual's own rule is TRAIN IT, DON'T HAND-TUNE IT: if a feature is
DATA -- and anthropometry is data -- it is not to be reasoned out. It is to be measured.

So this module holds the SOURCES and nothing else. It states, for every number, who measured it, on
how many people, by what technique, and in what year. A membrane asks for a fraction and gets one it
can cite. `compare()` puts the two independent sources side by side, and where they disagree it says
so rather than picking.

THREE SOURCES, DELIBERATELY:

  de LEVA (1996) -- adjustments to Zatsiorsky-Seluyanov's segment inertia parameters, J.Biomech 29,
      1223-1230. Zatsiorsky et al. measured 100 living young adults by GAMMA-RAY SCANNING; de Leva
      re-referenced their landmarks to joint centres, which is what biomechanics actually uses.
      This supersedes Dempster (1955), whose figures came from EIGHT CADAVERS and are still the ones
      most often quoted -- including, until now, by this repo.

  myo_sim -- the MyoSuite musculoskeletal model already vendored in this project. 60 rigid bodies
      with mass AND full inertia tensors, 114 joints with measured range of motion, 550 muscle
      elements. It is the body this studio has already trained a walk on: myobody_gait_meta.npy
      records STAND_Z = 0.9802 m and OMEGA0 = 3.1883 rad/s measured off it.

  VAN CRIEKINGE et al. (2023) -- a normative 3D gait dataset of 246 healthy adults aged 18-91,
      walking at three self-selected speeds on an instrumented treadmill: joint angles, moments,
      powers, ground reaction force and spatiotemporal parameters, averaged over every valid stride
      and grouped by sex and age decade. CC BY 4.0, OSF doi 10.17605/OSF.IO/T72CW. This is the
      MOVEMENT source, and it retires `swing * sin(phase)`.

WHAT IS STILL NOT SOURCED, and is written down here rather than hidden in a membrane:

  SEGMENT LENGTHS above the leg -- thigh/shank/foot splits and eye height as fractions of stature.
      LEG LENGTH ITSELF IS NOW MEASURED (`leg_over_stature`, 246 adults); the rest are still typed.
      ANSUR II is in the repo and can close them.
  RESPIRATORY AND THERMAL figures -- tidal volume, FRC, alveolar CO2 thresholds, metabolic heat.
      theBreath and theSweep carry these as literals. A physiology source is needed and none is here.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import re
from pathlib import Path

_HERE = Path(__file__).resolve().parent
MYO = _HERE.parent / "vendor" / "myo_sim"

# ════════════════════════════════════════════════════════════════════════════════════════════════
#  SOURCE 1 -- de LEVA (1996)
# ════════════════════════════════════════════════════════════════════════════════════════════════
# Zatsiorsky, Seluyanov & Chugunova measured 100 living young adults (Caucasian, college-aged) by
# gamma-ray scanning; de Leva adjusted the reference landmarks to joint centres. Journal of
# Biomechanics 29(9):1223-1230, 1996.
#
# EVERY NUMBER BELOW IS A PUBLISHED TABLE VALUE. That is what makes it a legal literal: it is a
# measurement of the world, reproducible from the paper, and it reads the same in any story.
DE_LEVA = {
    # segment: (mass fraction of body, CoM from proximal as fraction of segment length,
    #           radii of gyration about the CoM as fractions of segment length: (x, y, z))
    "head":      {"m": (0.0668, 0.0694), "com": (0.4841, 0.5002),
                  "gyr": ((0.271, 0.295, 0.261), (0.303, 0.315, 0.261))},
    "trunk":     {"m": (0.4257, 0.4346), "com": (0.4964, 0.5138),
                  "gyr": ((0.307, 0.292, 0.147), (0.328, 0.306, 0.169))},
    "upper_arm": {"m": (0.0255, 0.0271), "com": (0.5754, 0.5772),
                  "gyr": ((0.278, 0.260, 0.148), (0.285, 0.269, 0.158))},
    "forearm":   {"m": (0.0138, 0.0162), "com": (0.4559, 0.4574),
                  "gyr": ((0.261, 0.257, 0.094), (0.276, 0.265, 0.121))},
    "hand":      {"m": (0.0056, 0.0061), "com": (0.7474, 0.7900),
                  "gyr": ((0.631, 0.454, 0.335), (0.628, 0.513, 0.401))},
    "thigh":     {"m": (0.1478, 0.1416), "com": (0.3612, 0.4095),
                  "gyr": ((0.369, 0.364, 0.162), (0.329, 0.329, 0.149))},
    "shank":     {"m": (0.0481, 0.0433), "com": (0.4352, 0.4395),
                  "gyr": ((0.267, 0.263, 0.092), (0.251, 0.246, 0.102))},
    "foot":      {"m": (0.0129, 0.0137), "com": (0.4014, 0.4415),
                  "gyr": ((0.299, 0.279, 0.139), (0.257, 0.245, 0.124))},
}
DE_LEVA_CITE = ("de Leva P (1996) Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters. "
                "J Biomech 29(9):1223-1230. Underlying data: gamma-ray scanning, 100 living adults.")
_SEX = {"female": 0, "male": 1}


def segment(name: str, sex: str = "male") -> dict:
    """A segment's measured inertial parameters, with the citation attached to the answer.

    Returning the source alongside the number is the point: a caller cannot use this and then write
    a comment claiming it came from somewhere else, because the provenance travels with the value."""
    i = _SEX[sex]
    s = DE_LEVA[name]
    return {"mass_frac": s["m"][i], "com_frac": s["com"][i], "gyration": s["gyr"][i],
            "source": DE_LEVA_CITE, "sex": sex, "segment": name}


def limb_mass_frac(*names, sex: str = "male") -> float:
    """The mass of a limb, as the sum of the segments that make it. Spelled out rather than looked
    up, because "one leg" is not a segment anybody measured -- it is thigh + shank + foot, and which
    of those you include is exactly where two sources drift apart."""
    return sum(DE_LEVA[n]["m"][_SEX[sex]] for n in names)


def leg_inertia_about_hip(height_m, body_mass_kg, thigh_frac, shank_frac, foot_frac,
                          sex: str = "male") -> dict:
    """THE SWINGING LEG AS A REAL COMPOUND PENDULUM, composed from three measured segments.

    theHuman approximated the whole leg as ONE rod: a single mass at a guessed 0.447 of the way down,
    with a radius of gyration of "about 0.326 of its length". Both numbers were assertions, and the
    mass they scaled was Dempster's 0.161 from eight cadavers.

    de Leva measured each segment separately, so the composite can be built rather than guessed:

        I_hip = SUM over segments of  m_i * (k_i^2 + d_i^2)

    where d_i is each segment's own centre of mass measured from the HIP, and k_i its radius of
    gyration about that centre. The parallel-axis theorem does the rest, and nothing is approximated
    except the segment LENGTHS, which are still this repo's and are flagged in UNSOURCED.

    This is what sets the swing period, which sets cadence, which is most of what a walk looks like."""
    i = _SEX[sex]
    Lt, Ls, Lf = (float(thigh_frac) * height_m, float(shank_frac) * height_m,
                  float(foot_frac) * height_m)
    parts = []
    # thigh: CoM measured down the thigh from the hip
    mt = DE_LEVA["thigh"]["m"][i] * body_mass_kg
    dt = DE_LEVA["thigh"]["com"][i] * Lt
    kt = DE_LEVA["thigh"]["gyr"][i][0] * Lt
    parts.append(("thigh", mt, dt, kt))
    # shank: its CoM is down the shank from the KNEE, so from the hip it is a thigh further
    ms = DE_LEVA["shank"]["m"][i] * body_mass_kg
    ds = Lt + DE_LEVA["shank"]["com"][i] * Ls
    ks = DE_LEVA["shank"]["gyr"][i][0] * Ls
    parts.append(("shank", ms, ds, ks))
    # foot: hangs at the ankle, and lies roughly ACROSS the leg axis rather than along it, so its
    # distance from the hip is the leg's length and not the leg plus the foot.
    mf = DE_LEVA["foot"]["m"][i] * body_mass_kg
    df = Lt + Ls
    kf = DE_LEVA["foot"]["gyr"][i][0] * Lf
    parts.append(("foot", mf, df, kf))

    I = sum(m * (k * k + d * d) for _, m, d, k in parts)
    m_leg = sum(m for _, m, _, _ in parts)
    d_com = sum(m * d for _, m, d, _ in parts) / m_leg
    return {"I_hip_kgm2": I, "leg_mass_kg": m_leg, "leg_com_from_hip_m": d_com,
            "leg_mass_frac": m_leg / body_mass_kg,
            "segments": [{"name": n, "mass_kg": m, "com_from_hip_m": d, "gyration_m": k}
                         for n, m, d, k in parts],
            "source": DE_LEVA_CITE,
            "lengths_are_sourced": False}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  SOURCE 2 -- the model already in this repo
# ════════════════════════════════════════════════════════════════════════════════════════════════
_MYO_CACHE = None


def myo_body(model: str = "leg/myolegs.xml") -> dict:
    """One NAMED model's bodies, with mass and inertia, plus its joints and their measured ranges.

    SCOPED TO ONE MODEL ON PURPOSE, and the first version was not. Scanning every XML under myo_sim
    and keeping the first definition of each name returned femur_r = 6.257 kg, because the same body
    name appears in several sub-models at different scalings. Read from `leg/myolegs.xml` it is
    8.400 kg -- a 34% difference produced entirely by which file the walk happened to reach first.
    A model is a body; mixing two of them is measuring a chimera, which is funny here and still wrong.

    Returns {"segments": {...}, "joints": {...}, "total_mass_kg": float, "model": str}. The total is
    what makes a fraction computable: an absolute mass means nothing without the body it belongs to."""
    global _MYO_CACHE
    if _MYO_CACHE is not None and _MYO_CACHE.get("model") == model:
        return _MYO_CACHE
    segs, joints = {}, {}
    root_file = MYO / model
    files = [root_file]
    if root_file.exists():
        try:
            for inc in re.findall(r'<include file="([^"]+)"',
                                  root_file.read_text(encoding="utf-8", errors="replace")):
                q = (root_file.parent / inc).resolve()
                if q.exists():
                    files.append(q)
        except OSError:
            pass
    if root_file.exists():
        for p in files:
            try:
                root = ET.parse(p).getroot()
            except Exception:
                continue
            for b in root.iter("body"):
                nm = b.get("name")
                inr = b.find("inertial")
                if not nm or inr is None or not inr.get("mass"):
                    continue
                if nm in segs:
                    continue                       # first definition wins; duplicates are includes
                di = inr.get("diaginertia", "")
                segs[nm] = {"mass": float(inr.get("mass")),
                            "diaginertia": tuple(float(v) for v in di.split()) if di else None,
                            "file": p.name}
            for j in root.iter("joint"):
                nm, rg = j.get("name"), j.get("range")
                if nm and rg and nm not in joints:
                    try:
                        lo, hi = (float(v) for v in rg.split())
                        joints[nm] = (lo, hi)
                    except ValueError:
                        continue
    _MYO_CACHE = {"segments": segs, "joints": joints, "model": model,
                  "total_mass_kg": sum(v["mass"] for v in segs.values()),
                  "source": f"MyoSuite myo_sim, vendored at vendor/myo_sim, model {model}"}
    return _MYO_CACHE


def myo_mass(*names) -> float:
    """Summed mass of named bodies in the model. Raises on a name that is not there rather than
    returning zero, because a silent zero is how a limb goes missing."""
    segs = myo_body()["segments"]
    out = 0.0
    for n in names:
        if n not in segs:
            raise KeyError(f"{n!r} is not a body in myo_sim; have e.g. {sorted(segs)[:6]}")
        out += segs[n]["mass"]
    return out


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  THE COMPARISON -- two independent measurements of one body
# ════════════════════════════════════════════════════════════════════════════════════════════════
def compare(sex: str = "male") -> list:
    """Put the published table beside the vendored model, as FRACTIONS of each one's own body.

    THIS DOES NOT PICK A WINNER. Two independent measurements of the same quantity is the strongest
    position available, and disagreement is information -- averaging it away throws that information
    out. What this does is turn the disagreement into a number instead of an absence."""
    b = myo_body()
    tot = b["total_mass_kg"] or 1.0
    segs = b["segments"]
    pairs = (("thigh", ("femur_r",)), ("shank", ("tibia_r",)), ("foot", ("calcn_r",)))
    rows = []
    for name, myo_names in pairs:
        if not all(n in segs for n in myo_names):
            continue
        mk = sum(segs[n]["mass"] for n in myo_names)
        mf = mk / tot
        df = DE_LEVA[name]["m"][_SEX[sex]]
        rows.append({"segment": name, "myo_kg": mk, "myo_frac": mf, "de_leva_frac": df,
                     "disagreement_pct": 100.0 * (df - mf) / mf,
                     "myo_total_kg": tot})
    return rows


def leg_mass_check(body_mass_kg: float, sex: str = "male") -> dict:
    """THE CHECK THAT CAUGHT theHuman. Its `LEG_MASS_FRAC = 0.161` is Dempster (1955), measured on
    EIGHT CADAVERS and still the most-quoted figure anywhere. de Leva's living-subject data gives
    thigh + shank + foot for a male as 0.1416 + 0.0433 + 0.0137. The difference is not rounding."""
    dempster = 0.161
    deleva = limb_mass_frac("thigh", "shank", "foot", sex=sex)
    return {"dempster_1955_frac": dempster,
            "de_leva_1996_frac": deleva,
            "disagreement_pct": 100.0 * (deleva - dempster) / dempster,
            "dempster_kg": dempster * body_mass_kg,
            "de_leva_kg": deleva * body_mass_kg,
            "why": ("Dempster measured 8 cadavers in 1955; Zatsiorsky measured 100 living adults by "
                    "gamma-ray scan. A leg's mass sets the swing period, which sets cadence."),
            "source": DE_LEVA_CITE}


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  SOURCE 3 -- 246 ADULTS WALKING
# ════════════════════════════════════════════════════════════════════════════════════════════════
# Van Criekinge, Saeys, Truijen et al. (2023): a normative 3D gait dataset of 246 healthy adults
# aged 18-91, at three self-selected speeds, CC BY 4.0, OSF doi 10.17605/OSF.IO/T72CW. Ingested by
# `tools/ingest_gait_osf.py` into story/data/gait_normative.json; run it with --check to prove the
# committed table still matches the spreadsheets it came from.
#
# WHAT THIS REPLACES. `swing * sin(phase)`, with swing = 0.42 rad. A sine is not a hip: it is
# symmetric, it has one peak, and it puts a foot down for exactly half the cycle, which is why the
# first walk here had no double support at all. A real hip curve is asymmetric, and the knee has TWO
# flexion peaks -- one of them a 18-degree wave during STANCE, which is the mechanism theAnkle named
# as the reason its vault was too tall.
GAIT_JSON = _HERE / "data" / "gait_normative.json"
_GAIT_CACHE = None

# THE DIRECTIONS THE TREADMILL NEVER MEASURED. The OSF dataset is 246 adults walking FORWARD; a body
# also backs up and sidesteps, and those gaits are different shapes (a trailing leg CROSSES in a
# sidestep). CMU MoCap walked them in a hallway; tools/ingest_gait_cmu_directional.py distils the
# trials into story/data/gait_directional.json. Forward is deliberately NOT in it: one subject does
# not outrank 246.
DIRECTIONAL_JSON = _HERE / "data" / "gait_directional.json"
_DIR_CACHE = None


def gait_directional() -> dict:
    """The CMU-measured directional gaits (backward, sidestep left/right), loaded once.

    Same rule as gait_data(): raise if missing rather than walk on zeros."""
    global _DIR_CACHE
    if _DIR_CACHE is None:
        if not DIRECTIONAL_JSON.exists():
            raise FileNotFoundError(
                f"{DIRECTIONAL_JSON} is missing. Run: python tools/ingest_gait_cmu_directional.py")
        import json
        _DIR_CACHE = json.loads(DIRECTIONAL_JSON.read_text(encoding="utf8"))
    return _DIR_CACHE

# The twelve groups: six age decades, men and women. AGE AND SEX ARE DIALS HERE -- turn one and the
# curve changes shape, because 246 people are not one person.
GAIT_GROUPS = [f"{s}_{a}" for a in ("18-29", "30-39", "40-49", "50-59", "60-69", "70+")
               for s in ("m", "w")]
GAIT_SPEEDS = ("slow", "comf", "fast")


def gait_data() -> dict:
    """The whole table, loaded once. Raises if it is missing rather than returning empty defaults --
    a membrane that silently walks on {} would walk on zeros and look like a corpse."""
    global _GAIT_CACHE
    if _GAIT_CACHE is None:
        if not GAIT_JSON.exists():
            raise FileNotFoundError(
                f"{GAIT_JSON} is missing. Run: python tools/ingest_gait_osf.py")
        import json
        _GAIT_CACHE = json.loads(GAIT_JSON.read_text(encoding="utf8"))
    return _GAIT_CACHE


def gait_group(sex: str = "male", age: float = 30.0) -> str:
    """Which measured group a body belongs to. A body has an age and a sex; this says whose data
    describes it, instead of every caller quietly picking young men."""
    s = "m" if str(sex).lower().startswith("m") else "w"
    a = float(age)
    band = ("18-29" if a < 30 else "30-39" if a < 40 else "40-49" if a < 50
            else "50-59" if a < 60 else "60-69" if a < 70 else "70+")
    return f"{s}_{band}"


def gait_curve(param: str, speed: str = "comf", group: str = "m_18-29") -> dict:
    """One measured curve: 100 samples of the gait cycle, mean and SD, in the source's own units.

    SAMPLE 100 IS SAMPLE 1. Both are heel strike of the same leg -- the source counts the closing
    event as well as the opening one, and measured they agree to 0.01 degrees against a typical
    step of 0.08 to 1.4. So the curve has 99 distinct intervals, not 100, and anything that treats
    it as 100 gets a stutter exactly at heel strike. This project has already paid for that mistake
    once, in theSweep, where `% 1.0` snapped a transient back to its start. It is handled here, once,
    so no membrane has to know."""
    d = gait_data()
    if speed not in d["speeds"]:
        raise KeyError(f"speed {speed!r}; have {sorted(d['speeds'])}")
    cs = d["speeds"][speed]["curves"]
    if param not in cs:
        raise KeyError(f"no measured curve {param!r}; have {sorted(cs)}")
    if group not in cs[param]:
        raise KeyError(f"no group {group!r}; have {GAIT_GROUPS}")
    c = cs[param][group]
    return {"mean": c["mean"], "sd": c["sd"], "unit": d["curve_units"][param],
            "sign": d["curve_sign"][param], "param": param, "speed": speed, "group": group,
            "source": d["source"], "closes_at_sample_100": True}


def gait_sample(param: str, u: float, speed: str = "comf", group: str = "m_18-29") -> float:
    """The measured value at phase u of the cycle, u = 0 at heel strike, wrapping at 1.

    Linear between the measured samples. Nothing is smoothed or fitted: 246 people averaged over
    every valid stride is already smoother than anything a curve fit would add, and a fit would be
    this code's opinion laid over their measurement."""
    m = gait_curve(param, speed, group)["mean"]
    x = (float(u) % 1.0) * 99.0          # 99 intervals, because sample 100 closes onto sample 1
    i = int(x)
    f = x - i
    a = m[i] if m[i] is not None else 0.0
    b = m[i + 1] if i + 1 < 100 and m[i + 1] is not None else m[0]
    return a + (b - a) * f


def gait_scalar(name: str, speed: str = "comf", group: str = "m_18-29"):
    """One spatiotemporal group value as (mean, SD): cadence, stride length, step width, stance
    time, double-support time, foot clearance. Names are the source's, units included, e.g.
    'R.Step.Width [m]'. `gait_scalars()` lists them.

    ONE CORRECTION TO THE SOURCE, MEASURED FROM THE SOURCE'S OWN DATA (2026-08-01).
    Description_parameters.docx defines `R.Foot.Clear [cm]` as "the MAXIMUM distance between right
    toe marker and the ground during swing phase", and says it twice, once per leg. THE DATA SAYS
    OTHERWISE, and the data wins. Across the three self-selected speeds:

        R.Stride.Length   +42.2%          R.Foot.Clear   +2.1%
        R.Step.Length     +43.9%          R.Step.Width   +0.3%
        Cadence           +30.3%

    A maximum toe height is a kinematic consequence of swing excursion and must scale with the
    stride. This does not move -- it sits with STEP WIDTH, the other regulated speed-invariant
    safety parameter, which is exactly the company minimum toe clearance keeps and nowhere near
    where a peak belongs. Its magnitude agrees too: 2.08-2.13 cm is textbook MTC, while a 2 cm
    MAXIMUM swing clearance is physically impossible -- you would catch your foot every stride.

    SO `Foot.Clear` IS MINIMUM TOE CLEARANCE and must be compared against a swing-phase LOCAL
    minimum (tools/gait_witness.py does). Comparing it against a global swing minimum instead is
    what sent three investigations after the body -- the smallest clearance in swing is always
    zero, at toe-off, because that is what leaving the ground means."""
    d = gait_data()
    tab = d["speeds"][speed]["spatiotemporal"]
    if name not in tab:
        raise KeyError(f"no spatiotemporal parameter {name!r}; have {sorted(tab)}")
    m, s = tab[name][group]
    return m, s


def gait_scalars(speed: str = "comf") -> list:
    return sorted(gait_data()["speeds"][speed]["spatiotemporal"])


def gait_duty(speed: str = "comf", group: str = "m_18-29") -> dict:
    """DUTY FACTOR AND DOUBLE SUPPORT, measured, not asserted -- computed from the source's own
    stance, stride and double-support times rather than typed as 0.60.

    These two numbers are what separate a walk from a run and from a sled: duty is the fraction of
    the cycle a foot is down, and double support is the overlap where both are. Without overlap
    there is no walk, only two abutting hops."""
    stance, _ = gait_scalar("R.Stance.Time [s]", speed, group)
    stride, _ = gait_scalar("R.Stride.Time [s]", speed, group)
    bip_r, _ = gait_scalar("R.Bipedal [s]", speed, group)
    bip_l, _ = gait_scalar("L.Bipedal [s]", speed, group)
    return {"duty": stance / stride,
            "double_support_frac": (bip_r + bip_l) / stride,
            "stance_s": stance, "stride_s": stride,
            "source": gait_data()["source"]}


def gait_walking_speed(speed: str = "comf", group: str = "m_18-29") -> float:
    """How fast that condition actually was, in m/s. 'comfortable' is not a speed until measured."""
    return gait_scalar("Walking.Speed [m/s]", speed, group)[0]


def gait_sample_at_speed(param: str, u: float, v_ms: float, group: str = "m_18-29") -> float:
    """THE SPEED DIAL. The measured curve at an arbitrary walking speed, interpolated between the
    three conditions the study actually ran.

    Three measured speeds make speed CONTINUOUS rather than a switch between animations: push the
    stick further and the hip's real curve changes shape, because it was measured changing shape.
    Outside the measured range it clamps -- extrapolating a body past the fastest walk anybody in
    the study did would be inventing data, and this module exists so that nobody has to."""
    pts = sorted((gait_walking_speed(s, group), s) for s in GAIT_SPEEDS)
    v = float(v_ms)
    if v <= pts[0][0]:
        return gait_sample(param, u, pts[0][1], group)
    if v >= pts[-1][0]:
        return gait_sample(param, u, pts[-1][1], group)
    for (v0, s0), (v1, s1) in zip(pts, pts[1:]):
        if v0 <= v <= v1:
            w = (v - v0) / max(v1 - v0, 1e-9)
            return (gait_sample(param, u, s0, group) * (1.0 - w)
                    + gait_sample(param, u, s1, group) * w)
    return gait_sample(param, u, "comf", group)


def leg_over_stature(sex: str = "male") -> tuple:
    """LEG LENGTH AS A FRACTION OF STATURE, measured on the 246 -- (mean, SD, n).

    This closes a hole that had nothing behind it: the story carried the fraction as a constant read
    off one model. 246 people give 0.5246 +- 0.0167, and the SD is the point -- it is what makes a
    long-legged or short-legged body a legal body rather than an error."""
    d = gait_data()["cohort"]
    key = {"male": "leg_over_stature_men", "female": "leg_over_stature_women"}.get(sex,
                                                                                  "leg_over_stature")
    m, s, n = d[key]
    return m, s, n


def gait_cohort() -> dict:
    """Who was measured: 246 adults, 122 men and 124 women, 18 to 91, with mass, stature and leg
    length. A curve without its cohort is an anonymous claim."""
    return dict(gait_data()["cohort"])


# ════════════════════════════════════════════════════════════════════════════════════════════════
#  WHAT IS NOT SOURCED -- stated as data, so it can be queried rather than remembered
# ════════════════════════════════════════════════════════════════════════════════════════════════
UNSOURCED = [
    {"what": "segment LENGTHS above the leg -- thigh/shank/foot splits, eye height",
     "used_by": "theHuman.THIGH_FRAC/SHANK_FRAC/FOOT_LEN_FRAC/EYE_FRAC, aHuman's limb radii",
     "currently": "typed constants attributed to Dempster in comments",
     "available": "ANSUR II (6,068 subjects, 93 measurements, public domain), IN THIS REPO at "
                  "research_references/human/ANSUR_II_{MALE,FEMALE}_Public.csv",
     "note": "LEG LENGTH as a fraction of stature is now MEASURED -- see leg_over_stature(): "
             "0.5246 +- 0.0167 over 246 adults. These are the fractions still standing on nothing.",
     "status": "NOT INGESTED"},
    {"what": "respiratory and thermal physiology",
     "used_by": "theBreath (RQ, tidal, VE, pCO2 limits), theSweep (water output), aHuman (metabolic W)",
     "currently": "literals with citation-shaped comments",
     "available": "NASA-STD-3001 / life-support handbooks give consumable rates with provenance",
     "status": "NOT SOURCED"},
]


def segment_fractions(sex="M", total=None):
    """THIGH, SHANK AND ANKLE DROP AS FRACTIONS OF STATURE -- measured, not Dempster's eight cadavers.

    UNSOURCED has listed these since it was written: "segment LENGTHS above the leg -- thigh/shank/
    foot splits ... typed constants attributed to Dempster in comments ... NOT INGESTED", with the
    remedy named in the same entry and already in this repo. This ingests it.

    THREE ANSUR II LANDMARKS AND TWO SUBTRACTIONS. trochanterion (the hip), lateral femoral
    epicondyle (the knee), lateral malleolus (the ankle), all heights above the floor:

        thigh = trochanterion - epicondyle        shank = epicondyle - malleolus
        ankle drop = malleolus                    (a foot has thickness)

    AND THEY CLOSE, WHICH IS THE POINT. thigh + shank + drop = trochanterion height exactly, because
    they are differences of the same measured heights on the same 6,068 people rather than three
    fractions gathered from different places and hoped to be compatible. Dempster's do not close:
    0.245 + 0.246 = 0.491 against a leg the same document calls 0.530, and the 0.039 left over was
    named "ankle drop" to absorb the difference.

    MEASURED (medians): thigh 0.2325 M / 0.2331 F, against Dempster's 0.245 -- a 5% shorter thigh.
    That is not a small correction to a decorative number: the swinging foot's height above the
    ground is a small difference between large lengths, so the whole segment error lands on it."""
    import csv as _csv, statistics as _st
    import os
    _d = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "research_references", "human")
    f = os.path.join(_d, "ANSUR_II_%s_Public.csv"
                     % ("MALE" if str(sex).upper().startswith("M") else "FEMALE"))
    rows = list(_csv.DictReader(open(f, encoding="latin-1")))

    def med(c):
        return _st.median([float(r[c]) for r in rows if r.get(c) not in (None, "", ".")])

    S, tr, ep, ma = med("stature"), med("trochanterionheight"),         med("lateralfemoralepicondyleheight"), med("lateralmalleolusheight")
    # ── ONE LEG LENGTH, AND EACH SOURCE GIVES WHAT IT MEASURED BEST ──────────────────────────
    # ANSUR's landmark is the TROCHANTERION -- a bump you can feel on the femur. The HIP JOINT
    # CENTRE sits medial and superior to it, so trochanterion height is NOT hip-joint height, and
    # ingesting these raw put a third leg length into a model that already had two:
    #
    #     0.5123  thigh + shank + drop      (ANSUR, trochanterion)
    #     0.5300  LEG_FRAC                  (Dempster, hip JOINT)
    #     0.5243  leg_over_stature()        (the 246 the gait curves come from)
    #
    # 3.11 cm apart, in a body whose foot was missing its ground by 4.12 cm. The bones did not add
    # up to the leg they hang from, and no amount of work on the ankle or the toe could fix that.
    #
    # SO EACH SOURCE CONTRIBUTES ITS OWN STRENGTH. ANSUR measured 6,068 people and is authoritative
    # for the PROPORTIONS -- how the leg divides. leg_over_stature() measured the same 246 adults
    # the walk curves were recorded on and is authoritative for the TOTAL. Scaling the splits onto
    # that total keeps both and invents neither, and it absorbs the trochanterion-to-joint offset
    # in the only direction anatomy allows: upward.
    if total is not None:
        k = float(total) / ((tr - ma) / S + ma / S)
        return {"thigh_frac": (tr - ep) / S * k, "shank_frac": (ep - ma) / S * k,
                "ankle_drop_frac": ma / S * k, "hip_height_frac": float(total),
                "scaled_to": float(total), "raw_trochanterion_frac": tr / S,
                "n": len(rows), "source": "ANSUR II proportions scaled onto the measured leg length"}
    return {"thigh_frac": (tr - ep) / S, "shank_frac": (ep - ma) / S,
            "ankle_drop_frac": ma / S, "hip_height_frac": tr / S,
            "n": len(rows), "source": "ANSUR II medians (trochanterion / lateral femoral "
                                      "epicondyle / lateral malleolus heights)"}
