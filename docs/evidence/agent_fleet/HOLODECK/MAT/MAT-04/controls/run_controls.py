"""run_controls.py -- executes preregistered R1-R4 (holodeck-mat-04) against
the reference model in one process; writes checks/*.txt with measured values,
verbatim refusals and post-state assertions. Read-only over the rest of the
tree. Exit 0 iff every preregistered row reaches its full N/N.

Usage: python controls/run_controls.py
"""
from __future__ import annotations

import dataclasses
import math
import random
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "reference"))
sys.path.insert(0, str(HERE.parent.parents[1] / "MATH" / "MATH-01" / "reference"))

import mat04_reference_model as mat  # noqa: E402
import math01_reference_model as m01  # noqa: E402

OUT = HERE.parent / "checks"
OUT.mkdir(exist_ok=True)

# ---- the declared fixture, recomputed INDEPENDENTLY here by exact Fractions --
# (the control derives the truth from L, A, E itself; the model never holds it)
L_GAUGE = Fraction(1, 10)            # 0.1 m
A_AREA = Fraction(1, 10000)          # 1e-4 m^2
E_YOUNG = Fraction(2_000_000_000)    # 2.0e9 Pa
K_TRUE = L_GAUGE / (A_AREA * E_YOUNG)        # = 1/2000000 = 5.0e-7 m/N
D0_TRUE = Fraction(2, 100000)                # 2.0e-5 m
SIGMA = 5.0e-6                       # m, declared noise scale
TRAIN_LOADS = (10.0, 25.0, 40.0, 70.0, 85.0, 100.0)
HELD_LOAD = 55.0                     # strictly interior
FIXTURE_SEED = 20260911
DESIGN_A = (10.0, 10.1)
DESIGN_B = (10.0, 100.0)
TABLE_T4 = 2.7764451051977987        # published two-sided 95% table value

BASE_SHA = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, cwd=str(HERE)).stdout.strip()

DESIGN_TRAINING = mat.DesignSpec("training_6", ("load", "one"))


def m_of(d_fraction_or_float):
    """metres -> observation stated in mm (exercises the declared 'mm'
    conversion path of the MATH-01 registry)."""
    return float(d_fraction_or_float) * 1e3, "mm"


def make_experiments(loads, noises, sigma=SIGMA):
    exps = []
    for i, (f, n) in enumerate(zip(loads, noises)):
        d_true = float(K_TRUE) * f + float(D0_TRUE)
        val, unit = m_of(d_true + n)
        exps.append(mat.Experiment(f"train_{i:02d}_F{f:g}", mat.load_n(f),
                                   val, unit, sigma * 1e3))
    return exps


class Rows:
    """Row recorder for one evidence file."""

    def __init__(self, title):
        self.title = title
        self.lines = [title, "=" * 72]
        self.lines.append(f"base: {BASE_SHA}")
        self.passed = 0
        self.failed = 0
        self.failures = []

    def note(self, *lines):
        self.lines.extend("       " + ln for ln in lines)

    def row(self, name, ok, detail):
        status = "PASS" if ok else "FAIL"
        self.lines.append(f"[{status}] {name}")
        for line in detail:
            self.lines.append("       " + line)
        if ok:
            self.passed += 1
        else:
            self.failed += 1
            self.failures.append(name)

    def finish(self, path):
        total = self.passed + self.failed
        self.lines.append("")
        self.lines.append(f"RESULT {path.name}: {self.passed}/{total} "
                          f"(failed: {self.failures if self.failures else 'none'})")
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"wrote {path}: {self.passed}/{total}")
        return self.failed == 0


def refusal_reason(fn, *args, **kwargs):
    """Call fn; return (raised?, reason-or-None, repr-of-what-happened)."""
    try:
        result = fn(*args, **kwargs)
    except mat.Mat04Refusal as r:
        return True, r.reason, f"Mat04Refusal(reason={r.reason!r}, " \
                               f"message={r.message!r})"
    except Exception as exc:  # any other crash is a failure, recorded verbatim
        return False, None, f"UNEXPECTED {type(exc).__name__}: {exc!r}"
    return False, None, f"NO REFUSAL; returned {result!r}"


# ============================== R1 ============================================
r1 = Rows("R1 positive identifications (mat04_reference_model) -- "
          "thresholds from PREREGISTRATION.txt + AMENDMENT 1")
fit_train = None
k_ci = d0_ci = None
band_fixture = None
held_exp_fixture = None
all_r1_ok = True

# (a) seeded fixture: 95% CIs contain the exactly-derived truths
# RNG stream (documented order): seed 20260911, draws 1-6 = training noise,
# draw 7 = the held-out observation's noise (R1(h) rebuilds this stream).
_rng_fixture = random.Random(FIXTURE_SEED)
noises = [_rng_fixture.gauss(0, SIGMA) for _ in TRAIN_LOADS]
held_noise_fixture = _rng_fixture.gauss(0, SIGMA)
r1.note(f"fixture noise stream: seed {FIXTURE_SEED}, draws 1-6 training "
        f"gauss(0, {SIGMA}), draw 7 held-out",
        "training noises: " + repr(noises),
        f"held-out noise (draw 7): {held_noise_fixture!r}")
try:
    fit_train = mat.fit(make_experiments(TRAIN_LOADS, noises),
                        DESIGN_TRAINING)
    k_ci, d0_ci = mat.confidence_intervals(fit_train)
    ok_a = (k_ci[0] <= float(K_TRUE) <= k_ci[1]
            and d0_ci[0] <= float(D0_TRUE) <= d0_ci[1])
    r1.row("R1(a) CI-contains-truth", ok_a, [
        f"K_TRUE (control, exact Fraction) = {K_TRUE} = {float(K_TRUE)!r}",
        f"D0_TRUE = {float(D0_TRUE)!r}",
        f"k_hat = {fit_train.theta[0]!r}, 95% CI = ({k_ci[0]!r}, {k_ci[1]!r})",
        f"d0_hat = {fit_train.theta[1]!r}, 95% CI = ({d0_ci[0]!r}, {d0_ci[1]!r})",
        f"dof = {fit_train.dof}, n = {fit_train.n}, "
        f"s2 = {fit_train.s2!r}"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(a) CI-contains-truth", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (b) covariance SPD: scale-free SPD of the parameter-covariance FORM
#     C = s2*(F^T F)^-1 for BOTH designs A and B (s2 > 0, so C00 > 0 iff
#     n/det > 0 and det(C) > 0 iff 1/det > 0), measured from the model's
#     exact determinant outputs; PLUS numeric SPD of the training fit's cov.
try:
    _name, _det, dets = mat.choose_design({"A": list(DESIGN_A),
                                           "B": list(DESIGN_B)})
    spdx = []
    for nm, loads in (("A", DESIGN_A), ("B", DESIGN_B)):
        det = dets[nm]
        n = len(loads)
        # scale-free SPD criterion for C = s2*inv(G), s2 > 0:
        c00_pos = (Fraction(n) / det) > 0
        det_pos = (Fraction(1) / det) > 0
        spdx.append((nm, float(det), bool(c00_pos and det_pos)))
    cov = fit_train.cov
    num_spd = cov[0][0] > 0 and (cov[0][0] * cov[1][1]
                                 - cov[0][1] * cov[1][0]) > 0
    ok_b = all(s[2] for s in spdx) and num_spd
    r1.row("R1(b) covariance SPD", ok_b, [
        "scale-free SPD of C = s2*(F^T F)^-1 (s2 > 0):",
        *[f"  design {nm}: det(F^T F) exact = {det!r} -> "
          f"C00>0 and det(C)>0: {ok}" for nm, det, ok in spdx],
        f"training_6 numeric cov = {cov!r}",
        f"numeric SPD (C00>0, det>0): {num_spd}"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(b) covariance SPD", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (c) rho_B vs the control's independent exact closed form (AMENDMENT 1 sign)
try:
    rho_b = mat.design_correlation(list(DESIGN_B))
    closed_b = -11 / math.sqrt(202)
    loads6 = [f for f in TRAIN_LOADS]
    corr_consistent = (abs(fit_train.corr[0][1]
                           - mat.design_correlation(loads6)) <= 1e-12)
    ok_c = (abs(rho_b - closed_b) <= 1e-9 and -0.8 < rho_b < 0.0
            and corr_consistent)
    r1.row("R1(c) rho_B closed form + sign", ok_c, [
        f"model design_correlation(B) = {rho_b!r}",
        f"control closed form -11/sqrt(202) = {closed_b!r}",
        f"|diff| = {abs(rho_b - closed_b)!r} (threshold 1e-9 absolute)",
        f"sign band -0.8 < rho_B < 0: {-0.8 < rho_b < 0.0}",
        f"fit.corr(training_6) = {fit_train.corr[0][1]!r} equals "
        f"design_correlation(loads_6) within 1e-12: {corr_consistent}"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(c) rho_B closed form + sign", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (d) rho_A vs its closed form (AMENDMENT 1 sign)
try:
    rho_a = mat.design_correlation(list(DESIGN_A))
    closed_a = -(Fraction(201, 10)
                 / math.sqrt(float(Fraction(20201, 50))))
    ok_d = abs(rho_a - closed_a) <= 1e-9 and rho_a < -0.999
    r1.row("R1(d) rho_A closed form + sign", ok_d, [
        f"model design_correlation(A) = {rho_a!r}",
        f"control closed form -(201/10)/sqrt(20201/50) = {closed_a!r}",
        f"|diff| = {abs(rho_a - closed_a)!r} (threshold 1e-9 absolute)",
        f"rho_A < -0.999: {rho_a < -0.999}"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(d) rho_A closed form + sign", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (e) D-optimality: dets, ratio, winner
try:
    name, det_best, dets = mat.choose_design({"A": list(DESIGN_A),
                                              "B": list(DESIGN_B)})
    det_a, det_b = float(dets["A"]), float(dets["B"])
    rel = lambda got, want: abs(got - want) / abs(want)
    ok_e = (name == "B"
            and rel(det_a, 0.01) <= 1e-6 and rel(det_b, 8100.0) <= 1e-6
            and rel(det_b / det_a, 810000.0) <= 1e-6)
    r1.row("R1(e) D-optimal design", ok_e, [
        f"choose_design winner = {name!r} (predicted B)",
        f"det(A) measured = {dets['A']!r} float {det_a!r} "
        f"(target 0.01, rel {rel(det_a, 0.01)!r})",
        f"det(B) measured = {dets['B']!r} float {det_b!r} "
        f"(target 8100, rel {rel(det_b, 8100.0)!r})",
        f"ratio det_B/det_A = {det_b / det_a!r} "
        f"(target 810000, rel {rel(det_b / det_a, 810000.0)!r})"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(e) D-optimal design", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (f) t quantile vs the published table (the model contains no table)
try:
    t4 = mat.t_two_sided(4)
    rel_err = abs(t4 - TABLE_T4) / TABLE_T4
    ok_f = rel_err <= 1e-9
    r1.row("R1(f) t_{0.975,4} vs table", ok_f, [
        f"model t_two_sided(4) = {t4!r}",
        f"published table = {TABLE_T4!r}",
        f"relative error = {rel_err!r} (threshold 1e-9 relative)"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(f) t_{0.975,4} vs table", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (g) coverage: 200 replications at nominal 95%; band [180, 200]
try:
    covered = 0
    for i in range(200):
        rng = random.Random(FIXTURE_SEED + i)
        tn = [rng.gauss(0, SIGMA) for _ in TRAIN_LOADS]
        fr_i = mat.fit(make_experiments(TRAIN_LOADS, tn), DESIGN_TRAINING)
        d_true_star = float(K_TRUE) * HELD_LOAD + float(D0_TRUE)
        obs_star = d_true_star + rng.gauss(0, SIGMA)
        ho = mat.Experiment(f"held_{i}", mat.load_n(HELD_LOAD),
                            obs_star * 1e3, "mm", SIGMA * 1e3)
        band = mat.declare_predictive_band(fr_i, mat.load_n(HELD_LOAD))
        v = mat.judge(band, ho)
        covered += 1 if v.verdict == "AGREES" else 0
    surprise = (covered == 200)
    ok_g = 180 <= covered <= 200
    r1.row("R1(g) held-out coverage", ok_g, [
        f"200 replications, seeds {FIXTURE_SEED}..{FIXTURE_SEED + 199}, "
        f"each refits and redeclares the 95% band before judging",
        f"covered = {covered}/200 (derived 3-sigma binomial band "
        f"[180, 200]; mean 190, sd 3.082)",
        f"SURPRISE note (covered == 200): {surprise}"
        + (" -- a 95% band covering 100% of replications suggests "
           "overconservative bands; reported, not celebrated" if surprise
           else "")])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(g) held-out coverage", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

# (h) card prediction on the fixture + MATH-01 composition (cited)
try:
    # same documented stream as (a): 6 training draws, then draw 7
    _rng_h = random.Random(FIXTURE_SEED)
    _ = [_rng_h.gauss(0, SIGMA) for _ in TRAIN_LOADS]
    obs_star = (float(K_TRUE) * HELD_LOAD + float(D0_TRUE)
                + _rng_h.gauss(0, SIGMA))
    held_exp_fixture = mat.Experiment("held_55", mat.load_n(HELD_LOAD),
                                      obs_star * 1e3, "mm", SIGMA * 1e3)
    band_fixture = mat.declare_predictive_band(fit_train,
                                               mat.load_n(HELD_LOAD))
    v_h = mat.judge(band_fixture, held_exp_fixture)
    comp = mat.PARAM_DIM_K * mat.LOAD_DIM == mat.OBS_DIM
    ok_h = (v_h.verdict == "AGREES"
            and band_fixture.half_width.dimension == m01.Dimension.M
            and comp)
    r1.row("R1(h) card prediction fixture + composition", ok_h, [
        f"band mean = {band_fixture.mean.value!r} m, half-width = "
        f"{band_fixture.half_width.value!r} m at F* = {HELD_LOAD} N",
        f"half_width.dimension = {band_fixture.half_width.dimension!r} "
        "(must be Dimension L)",
        f"observed = {obs_star!r} m -> verdict {v_h.verdict!r}, "
        f"distance = {v_h.distance!r}",
        "MATH-01 composition (cited): dim(k) x dim(F) == dim(d): "
        f"{mat.PARAM_DIM_K} * {mat.LOAD_DIM} == {mat.OBS_DIM} -> {comp}"])
except Exception as exc:
    all_r1_ok = False
    r1.row("R1(h) card prediction fixture + composition", False,
           [f"UNEXPECTED {type(exc).__name__}: {exc!r}"])

r1_ok = r1.finish(OUT / "r1_identification.txt")
all_r1_ok = all_r1_ok and r1_ok

# ============================== R2 ============================================
r2 = Rows("R2 inverse-problem negatives -- named refusals, verbatim reasons, "
          "post-state assertions")

theta_before = fit_train.theta
corr_before = fit_train.corr


def exp_furlong():
    return mat.Experiment("bad_unit", mat.load_n(40.0), 0.05, "furlong",
                          SIGMA * 1e3)


def exp_nan():
    return mat.Experiment("bad_nan", mat.load_n(40.0), float("nan"), "mm",
                          SIGMA * 1e3)


def exp_force():
    return mat.Experiment("bad_force", mat.load_n(40.0), 40.0, "N",
                          SIGMA * 1e3)


def exp_neg_sigma():
    return mat.Experiment("bad_sigma", mat.load_n(40.0), 0.05, "mm", -1e-6)


base_exps = make_experiments(TRAIN_LOADS, noises)

cases = [
    ("R2(a) undeclared unit", lambda: mat.fit([exp_furlong()] + base_exps[1:],
                                              DESIGN_TRAINING),
     "undeclared_observation_unit"),
    ("R2(b) nonfinite observation", lambda: mat.fit([exp_nan()] + base_exps[1:],
                                                    DESIGN_TRAINING),
     "nonfinite_observation"),
    ("R2(c) metre-newton pose", lambda: mat.fit([exp_force()] + base_exps[1:],
                                                DESIGN_TRAINING),
     "dimension_mismatch"),
    ("R2(d) rank-deficient design",
     lambda: mat.fit(make_experiments((40.0, 40.0), (0.0, 0.0)),
                     mat.DesignSpec("dup", ("load", "one"))),
     "rank_deficient_design"),
    ("R2(e) negative noise sigma",
     lambda: mat.fit([exp_neg_sigma()] + base_exps[1:], DESIGN_TRAINING),
     "invalid_noise_sigma"),
]
for name, fn, want in cases:
    raised, reason, detail = refusal_reason(fn)
    unchanged = (fit_train.theta == theta_before
                 and fit_train.corr == corr_before)
    r2.row(name, raised and reason == want and unchanged, [
        f"expected refusal reason: {want!r}",
        f"observed: {detail}",
        f"post-state: prior fit theta/cov/corr unchanged: {unchanged}"])

# R2(f) empty held-out ledger
raised, reason, detail = refusal_reason(mat.validate, fit_train, [])
r2.row("R2(f) empty held-out set", raised and reason == "no_heldout_evidence",
       ["expected refusal reason: 'no_heldout_evidence'",
        f"observed: {detail}",
        "post-state: no verdict returned (refusal raised)"])

# R2(g) training experiment offered as held-out
train_first = make_experiments(TRAIN_LOADS, noises)[0]
band_train = mat.declare_predictive_band(fit_train, train_first.load)
raised, reason, detail = refusal_reason(mat.judge, band_train, train_first)
r2.row("R2(g) held-out overlaps training",
       raised and reason == "heldout_overlaps_training",
       ["expected refusal reason: 'heldout_overlaps_training'",
        f"observed: {detail}",
        f"post-state: no verdict returned (refusal raised)"])

r2_ok = r2.finish(OUT / "r2_negatives.txt")

# ============================== R3 ============================================
r3 = Rows("R3 CARD FALSIFIER probes -- training-fit success posing as "
          "predictive material validation (card falsifier: 'Training-fit "
          "success is called predictive material validation')")

# (a) validate with no held-out data + closed verdict vocabulary
raised, reason, detail = refusal_reason(mat.validate, fit_train, [])
vocab = list(mat.Verdict.VALUES) if hasattr(mat.Verdict, "VALUES") else []
vocab_ok = (set(vocab) == {"AGREES", "DISAGREES"}
            and "VALIDATED" not in vocab and "OK" not in vocab)
r3.row("R3(a) no held-out data -> refusal; closed vocabulary",
       raised and reason == "no_heldout_evidence" and vocab_ok,
       ["expected refusal reason: 'no_heldout_evidence'",
        f"observed: {detail}",
        f"verdict vocabulary (model constant): {vocab!r}",
        f"closed {{AGREES, DISAGREES}} and no VALIDATED/OK label: {vocab_ok}"])

# (b) the PERFECT training fit (n == p, residuals zero) still refuses
perfect_exps = []
for f in DESIGN_B:  # 2 loads, 2 parameters: exact interpolation
    d_true = float(K_TRUE) * f + float(D0_TRUE)
    perfect_exps.append(mat.Experiment(f"perf_F{f:g}", mat.load_n(f),
                                       d_true * 1e3, "mm", SIGMA * 1e3))
fr_perfect = mat.fit(perfect_exps, mat.DesignSpec("perfect_2",
                                                  ("load", "one")))
ho_perfect = mat.Experiment("held_perfect", mat.load_n(HELD_LOAD),
                            (float(K_TRUE) * HELD_LOAD
                             + float(D0_TRUE)) * 1e3, "mm", SIGMA * 1e3)
raised_v, reason_v, detail_v = refusal_reason(mat.validate, fr_perfect,
                                              [ho_perfect])
raised_b, reason_b, detail_b = refusal_reason(mat.declare_predictive_band,
                                              fr_perfect, mat.load_n(HELD_LOAD))
d_vals = [e.obs_si() for e in perfect_exps]
pred_vals = [fr_perfect.theta[0] * float(e.load.value)
             + fr_perfect.theta[1] for e in perfect_exps]
resid_norm = math.sqrt(sum((d - p) ** 2 for d, p in zip(d_vals, pred_vals)))
r2sq = 1.0 - (resid_norm ** 2) / sum(d * d for d in d_vals)
ok_b = (raised_v and reason_v == "no_dof_for_uncertainty"
        and raised_b and reason_b == "no_dof_for_uncertainty"
        and fr_perfect.dof == 0 and fr_perfect.s2 is None)
r3.row("R3(b) perfect training fit is NOT validation", ok_b, [
    f"perfect fit: n = {fr_perfect.n}, dof = {fr_perfect.dof}, "
    f"s2 = {fr_perfect.s2!r}",
    f"training residuals vanish: |resid| = {resid_norm!r}, "
    f"R^2 = {r2sq!r} (training-fit SUCCESS by every fit metric)",
    f"validate(held-out) observed: {detail_v}",
    f"declare_predictive_band observed: {detail_b}",
    "post-state: no verdict exists for the perfect fit (both refusals)"])

# (c) forced disagreement: observed 10 declared sigmas outside the band
_far = mat.Experiment("held_far", mat.load_n(HELD_LOAD),
                      (float(K_TRUE) * HELD_LOAD + float(D0_TRUE)
                       + 10.0 * SIGMA) * 1e3, "mm", SIGMA * 1e3)
v_far = mat.judge(band_fixture, _far)
ok_c = (v_far.verdict == "DISAGREES"
        and v_far.distance > v_far.half_width)
r3.row("R3(c) verdict is computed (DISAGREES at 10 sigma)", ok_c, [
    f"observed = band mean + 10*sigma; verdict = {v_far.verdict!r}",
    f"distance = {v_far.distance!r} > half-width = {v_far.half_width!r}"])

# (d) post-refusal state: reason carried verbatim; no global verdict ledger
mod_state = [n for n in dir(mat)
             if isinstance(getattr(mat, n, None), (list, dict))
             and "verdict" in n.lower()]
ok_d = (reason == "no_heldout_evidence" and not mod_state)
r3.row("R3(d) refusal verbatim; no verdict store", ok_d, [
    f"refusal reason captured verbatim: {reason!r}",
    f"module-level verdict stores (must be none): {mod_state!r}",
    "post-state: the refused validation recorded nothing anywhere"])

r3_ok = r3.finish(OUT / "r3_falsifier_pose.txt")

# ============================== R4 ============================================
r4 = Rows("R4 immutability / determinism")

# (a) frozen FitResult
try:
    fit_train.theta = (0.0, 0.0)
    raised_a, note_a = False, "assignment SUCCEEDED (not frozen!)"
except dataclasses.FrozenInstanceError as err:
    raised_a, note_a = True, f"FrozenInstanceError: {err!r}"
except Exception as err:
    raised_a, note_a = True, f"{type(err).__name__}: {err!r} (frozen)"
unchanged_a = fit_train.theta == theta_before
r4.row("R4(a) FitResult frozen", raised_a and unchanged_a,
       [f"attribute assignment: {note_a}",
        f"theta unchanged after: {unchanged_a}"])

# (b) bit-determinism of an identical refit
fr_again = mat.fit(make_experiments(TRAIN_LOADS, noises), DESIGN_TRAINING)
identical = (fr_again.theta == fit_train.theta
             and fr_again.cov == fit_train.cov
             and fr_again.corr == fit_train.corr)
r4.row("R4(b) determinism", identical, [
    f"theta identical: {fr_again.theta == fit_train.theta}",
    f"cov identical: {fr_again.cov == fit_train.cov}",
    f"corr identical: {fr_again.corr == fit_train.corr}",
    f"theta = {fit_train.theta!r}"])

# (c) Prediction frozen; band unchanged across the judge reveal
try:
    band_fixture.half_width = m01.Quantity(0.0, m01.Dimension.M)
    raised_c, note_c = False, "assignment SUCCEEDED (not frozen!)"
except dataclasses.FrozenInstanceError as err:
    raised_c, note_c = True, f"FrozenInstanceError: {err!r}"
except Exception as err:
    raised_c, note_c = True, f"{type(err).__name__}: {err!r} (frozen)"
half_before = band_fixture.half_width.value
_ = mat.judge(band_fixture, held_exp_fixture)
half_after = band_fixture.half_width.value
r4.row("R4(c) Prediction frozen; no post-hoc widening",
       raised_c and half_before == half_after,
       [f"attribute assignment: {note_c}",
        f"half-width before judge = {half_before!r}, "
        f"after judge = {half_after!r}, identical: "
        f"{half_before == half_after}"])

# (d) defensive copy of the caller's ledger
ledger = make_experiments(TRAIN_LOADS, noises)
fr_copy = mat.fit(ledger, DESIGN_TRAINING)
loads_snapshot = fr_copy.loads
n_snapshot = fr_copy.n
ledger.append(mat.Experiment("late_intruder", mat.load_n(999.0),
                             1.0, "mm", SIGMA * 1e3))
r4.row("R4(d) defensive copy", (fr_copy.n == n_snapshot
                                and fr_copy.loads == loads_snapshot), [
    f"caller appended an experiment after fit(); stored n = {fr_copy.n} "
    f"(snapshot {n_snapshot})",
    f"stored loads unchanged: {fr_copy.loads == loads_snapshot}"])

r4_ok = r4.finish(OUT / "r4_immutability.txt")

# ============================ scoreboard ======================================
_model_lines = sum(1 for _ in open(HERE.parent / "reference"
                                   / "mat04_reference_model.py",
                                   encoding="utf-8"))
summary = ["R1-R4 scoreboard (holodeck-mat-04 gen 1)",
           f"  R1 positive identifications : {'8/8' if r1_ok else 'MISS'}",
           f"  R2 inverse-problem negatives: {'7/7' if r2_ok else 'MISS'}",
           f"  R3 card-falsifier poses     : {'4/4' if r3_ok else 'MISS'}",
           f"  R4 immutability/determinism : {'4/4' if r4_ok else 'MISS'}",
           "",
           f"base: {BASE_SHA}",
           f"model: reference/mat04_reference_model.py "
           f"({_model_lines} lines)"]
(OUT / "scoreboard.txt").write_text("\n".join(summary) + "\n",
                                    encoding="utf-8")
print("\n".join(summary))

sys.exit(0 if (r1_ok and r2_ok and r3_ok and r4_ok) else 1)
