"""K01-CLIMB-20261001 physics battery (PREREGISTRATION.md, frozen at
commit cdfaa8cc1535dbe723097aa1277385aeb2aa79d3, bytes sha256 227a06c8...).

Executes the preregistered K01 experiment at the pin:

- P1 APPROACH-SEAM ``approach_terminates_at_declared_seam``: the declared
  scaffold approach script (labeled SCAFFOLD; DERIVATION gap 10
  honest-absent treatment) drives the certified line from the F05 minimum
  envelope boundary to the declared trunk-adjacent terminal window; the
  solver runs every approach tick over the trunk-only fixture scene and the
  records must show ZERO trunk contacts before the declared contact phase
  (no snap-to-tree, K06 anti-snap upstream declaration) and ZERO undeclared
  contact sites.
- P2 CONTACT ESTABLISHMENT ``declared_pads_establish_stick_class``: the
  DECLARED pad set (G04 fixture class, n=3) pressed at the sealed F03 S1
  operating point on trunk_01.lateral across the frozen 240-tick
  grasp-attempt window; per-tick jn/jt, press impulse, stick/slip class;
  FB2 zero-mu negative control must SLIDE with the G04 slide reading.
- P3 GRASP-WRAP OF THE RECORDED CONFIGURATION
  ``recorded_config_grasp_refused``: PREDICTED REFUSAL. B1/B2 re-derived at
  run from the pinned grasp-geometry bytes; observing the refusal SUPPORTS
  the prediction; the falsifier (a sustained recorded-config grasp) would
  contradict the wrap model/span records and is preserved as a records
  discrepancy, never a win.
- P4 ACHIEVABLE-APERTURE GRASP ``anatomical_grasp_undecidable``: honest
  absent (x_aperture/x_reach, recorded from the pinned G04 named-absent
  table); no synthetic constant occupies the absent slot.
- P5 STATIC HOLD ``scene_n3_hold_closes_at_placeholder``: PREDICTED CLOSURE
  at placeholder mu=0.6 ONLY; PREDICTED NON-CLOSURE at the declared
  scenario parameter mu=0.41 with the recorded slip recursion as the named
  failure discriminator (not a harness error). 20-tick hold window (G07
  hold precedent).
- P6 TRANSFER ``transfer_out_of_scope_nonclosing``: the B5 bound
  re-derived at run and recorded as the reason NO transfer phase runs.

REFINEMENT CHECKS: every threshold is DERIVED AT RUN from hash-asserted
pinned bytes (no hand-copied constants); derived values are additionally
value-matched against the numeric tokens of the pinned corpus bytes
(mismatch = refusal ``threshold_pin_mismatch``). The five RETRACTED
defective static quotes are re-derived arithmetically (the mu_true/0.6 and
n=1 mis-conventions) and asserted ABSENT from every emitted receipt byte.

Interfaces, imported at run time, hash-asserted, never forked: the solver
MAT2-M06 ``chimera.local_contact.v1``; the grip physics + fixture MAT2-G04
``grip_contact.py`` (PR #298 revision); the observation seam MAT2-G05
``contact_support_obs.py`` (PR #300 revision). Captures run through the
embedded standing capture-gate template (capture_card/, pinned verbatim by
TEMPLATE_MANIFEST.json); the card view-spec hash was pinned in
card_prereg.json BEFORE capture.

CPU-only, stdlib (+ numpy for the template gate), deterministic; no RNG,
no wall clock in trace/receipt. Exit codes: 0 all predictions SUPPORTED;
3 a falsifier fired (receipt still written; preserve, never tune);
4 a harness refusal (pin drift, threshold mismatch, undeclared contact).
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(HERE))

SCHEMA = 'chimera.k01_battery.v1'

PREREG_COMMIT = 'cdfaa8cc1535dbe723097aa1277385aeb2aa79d3'
PREREG_SHA256 = ('227a06c83180b68846b921e3ea36a0b594b5395d331fd487d9c36cdac'
                 '764a65e')
BASE_SHA = PREREG_COMMIT

# ---- pinned interface modules (imported, hash-asserted, never forked) ----
G04_MODULE_REL = '../MAT2-G04/grip_contact.py'
G04_MODULE_SHA256 = ('0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b'
                     '4173d69245')
G05_MODULE_REL = '../MAT2-G05/contact_support_obs.py'
G05_MODULE_SHA256 = ('3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e'
                     '4f31c46bd3')

# ---- git-tree pins (package files, from the sealed base) -----------------
GIT_PINS = {
    'PREREGISTRATION.md': PREREG_SHA256,
    G04_MODULE_REL: G04_MODULE_SHA256,
    G05_MODULE_REL: G05_MODULE_SHA256,
    '../MAT2-M06/local_contact.py':
        '1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc',
    '../MAT2-M06/test_local_contact.py':
        'b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77',
    '../MAT2-M06/contact_law.json':
        '583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b',
    '../MAT2-G04/test_g04_checks.py':
        'a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1',
    '../MAT2-G04/falsifier_receipt.json':
        '04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2',
    '../MAT2-G05/test_g05_checks.py':
        '83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b',
    '../MAT2-F03/assets/trunk_01_mesh.json':
        '3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7',
    'capture_card/TEMPLATE_MANIFEST.json':
        '1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7',
    # regression-mode inputs (the UNMODIFIED upstream suites' data)
    '../MAT2-M06/author_contact.py':
        'fe287648c14f7e553a0ef09ad8299244bce54d32cb2611564421b8151ded3f08',
    '../MAT2-M06/run_experiments.py':
        '9221cb6a74850cf80fb27b9baa7d5bbd2ea774f882e721dbb2c4a0b7549a554b',
    '../MAT2-M06/experiment_receipt.json':
        '2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397',
    '../MAT2-M06/PREREGISTRATION.md':
        '8c81b21cb4c879e1351bf43053dc7509c1e899b0fa5909602aa7154100e041e5',
    '../MAT2-M06/contact_display.json':
        'c4b8f4c4efc3718513fce9fdc62e17fb546143df79e7d7421a9fb4e82f4c6e22',
    '../MAT2-M02/monkey_arm_independent_meshes.json':
        '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834',
    '../MAT2-M02/independent_shape_regions.json':
        '0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e',
    '../MAT2-M02/monkey_arm_regions.json':
        '15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1',
    '../MAT2-G04/experiment_receipt.json':
        '0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8',
    '../MAT2-G04/experiment_trace.json':
        '044516a19bb4d08066dae6cd6132e22a181023fa3c6934d33b4705c2d0f9d621',
    '../MAT2-G04/determinism_receipt.json':
        '44f4f030b2fc958a52ee0c974e16ba36f2895aff7b364bb0e3aa1f6ec13b7347',
    '../MAT2-G04/regression_receipt.json':
        '7f33c6f121f36943c58ef13b1ecd6f0989d45341f2151a2c9920f69b5e0be039',
    '../MAT2-G05/experiment_receipt.json':
        '468185796db949ffd97b7e390de4adbc80aef74d1021445a8cfa28a74ef3dfbe',
    '../MAT2-G05/experiment_trace.json':
        'ef7d8aea22ebf40ebf1a903144337c6daf22f9941e25a1c9e6b05fae60030c77',
    '../MAT2-G05/determinism_receipt.json':
        '3782f81ed5bdde9eb1d73820daa7454360d1fe18c422de373324b7a20742728f',
    '../MAT2-G05/regression_receipt.json':
        '74d9be18c0fb0bfc42450147a58cf52b33bfbf2b9db9b5c2f85da246691e77f7',
    '../MAT2-G05/falsifier_receipt.json':
        '77f5e4d52ddd1e985fedab4505f59154d3c882d49dddd28011f4653d9ca6cf67',
}

# ---- host pins (verified against the prereg section 7 pins, 2026-10-01) --
HOST_ROOT = 'E:/ChimeraWork/monkey-coordination/'
HOST_PINS = {
    HOST_ROOT + 'climb-derivation/DERIVATION.md':
        'da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9',
    HOST_ROOT + 'climb-derivation/climb_derivation.py':
        'be1510dd3273fbc87d728b70bd65931a2381fee551fbf8f92da23cc9e31df237',
    HOST_ROOT + 'climb-derivation/derivation_output.txt':
        '534ac1f3dfe98bbfb14636704132ca192ca92f47e23cf1f065f9bd5032e2d73f',
    HOST_ROOT + 'climb-derivation/grasp-geometry/grasp_geometry.py':
        'e5614b3120dc9d663c204acf6a5db21f11e5c27c7616911f07eb385eee2cfc97',
    HOST_ROOT + 'climb-derivation/grasp-geometry/derivation_output.txt':
        '955956538d8b2e5236e77e14752352dd51c45065a1c5be8222efaa777965a4db',
    HOST_ROOT + 'climb-derivation/grasp-geometry/SGT_GEOMETRY_REVIEW.md':
        '30a2d6aeb6ed1059c1e416a7aa39ab3285cd3fa12013e8141dab20288a3ebc3b',
    HOST_ROOT + 'sensitivity/SCOPE_LABELS_ranked_table_20261001.md':
        'efe83ee027a5467af2349392469424a766dfb1eeadb4a3c373e1cd6d198590e4',
    HOST_ROOT + 'assembly-identity/ASSEMBLY_IDENTITY.md':
        '2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035',
    HOST_ROOT + 'evidence-store/MAT2-G01/report/REPORT.md':
        'e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9',
    HOST_ROOT + 'evidence-store/MAT2-G01/numerical/feasibility_receipt.json':
        '4061d8ec604ddea5dfbdf605f0244874129a69a88d771d4f593c7a927c16be42',
    HOST_ROOT + 'evidence-store/MAT2-F05/source/FRICTION_SOURCES.md':
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
    HOST_ROOT + 'evidence-store/MAT2-D-MASSREG/numerical/mass_register.json':
        '61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a',
    HOST_ROOT + 'evidence-store/MAT2-W04/numerical/w04_certificate.json':
        '07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598',
    HOST_ROOT + 'evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json':
        'be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29',
    HOST_ROOT + 'evidence-store/MAT2-B07/unclassified/adoption_record.json':
        'f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199',
    HOST_ROOT + 'b07-prereqs/RUNTIME_CONTRACT.md':
        'f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c',
    HOST_ROOT + 'w10_evidence_receipt.json':
        '0e9c6de57665529d962a5ff3ec3fcf964a2283b9f7a665ad9abb160151bb7405',
    HOST_ROOT + 'capture-gate-template/README.md':
        '331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6',
    HOST_ROOT + 'capture-gate-template/TEMPLATE_MANIFEST.json':
        '1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7',
    HOST_ROOT + 'evidence-store/MAT2-G04/report/REPORT.md':
        'dfca5b5556efe018ca09be4577bf6fbb5df38bb5c9ebc33d15bd18646ba349c8',
}

# ---- frozen windows (prereg section 10; G04/G07 precedents) --------------
APPROACH_HORIZON_TICKS = 10500   # certified run horizon bound
GRASP_ATTEMPT_TICKS = 240        # 0.8 s per arm
HOLD_TICKS = 20                  # G07 20-tick hold precedent
CONTROL_TICKS = 40               # zero-mu control window (G04 slide precedent
#                                mapped 20 press + 20 release: the pinned G04
#                                FB2 reading 0.05150250000055512 m is the
#                                20-tick full-press slide; declared BEFORE
#                                the run in this package, never tuned after).
READING_N = ('scene', 3)         # the certified n=3 line
CONTROL_N = ('band_mid', 3)      # the G04 zero-mu control configuration
MU_PLACEHOLDER_S = None          # taken from pinned modules (0.6), never
MU_PLACEHOLDER_K = None          # hand-copied here (set in derive()).
MU_SCENARIO = 0.41               # THE DECLARED SCENARIO PARAMETER (prereg
#   section 3: human-analogue transfer value, Gerhardt et al. 2008
#   natural-dry volar forearm on textile; NOT monkey-bark; UNMEASURED;
#   single-coefficient reading: mu_s = mu_k = 0.41, declared BEFORE run).

# ---- the declared SCAFFOLD approach (gap 10 honest-absent treatment) -----
SCAFFOLD = {
    'label': 'SCAFFOLD (declared; DERIVATION gap 10 honest-absent; no corpus '
             'number predicts approach completion - prereg B8)',
    'start_base_to_trunk_axis_m': 2.0,     # the F05 placement-law minimum
    'approach_speed_mps': 0.1,             # declared scaffold speed
    'terminal_window_m': [0.30, 0.45],     # declared trunk-adjacent window;
    #   inside the G06 declared fixture reach envelope 0.5 m; NOT derived
    #   from anatomy (x_reach ABSENT; prereg B10/A1).
    'horizon_ticks': APPROACH_HORIZON_TICKS,
    'anti_assist_law': 'the seam may not set any state the solver would '
                       'refuse; the contact phase begins only from the '
                       'sealed G04 fixture placement',
}

WIN_JN = 1e-9           # N*s, jn == P (sealed G04 window)
WIN_RECURSION_V = 1e-9  # m/s, slip/free-fall velocity recursion (sealed)
WIN_DISP = 1e-9         # m, displacement recursion (sealed)
WIN_RELEASE_SCALE = 1e-10  # N*s per kg (sealed G04 amendment a2 bar)
WIN_ZERO_MU_PIN = 1e-9  # m, derived control slide vs pinned G04 reading

CONTACT_SITES_DECLARED = ('trunk_01.lateral', 'grip.pad_0', 'grip.pad_1',
                          'grip.pad_2')


class K01Refusal(ValueError):
    """Named harness refusal; receipts still written (exit 4)."""


def require(ok, code, detail=''):
    if not ok:
        raise K01Refusal(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# pin gate
# ---------------------------------------------------------------------------

def verify_pins():
    """Assert every git-tree and host pin by sha256. Refusals:
    input_pin_missing / input_pin_drift."""
    rows = []
    for rel, expect in sorted(GIT_PINS.items()):
        path = (HERE / rel).resolve()
        if not path.exists():
            raise K01Refusal('input_pin_missing:' + str(path))
        got = sha256_file(path)
        require(got == expect, 'input_pin_drift:' + str(path), got)
        rows.append({'path': rel, 'sha256': got, 'class': 'git_tree'})
    for path, expect in sorted(HOST_PINS.items()):
        p = pathlib.Path(path)
        if not p.exists():
            raise K01Refusal('input_pin_missing:' + path)
        got = sha256_file(p)
        require(got == expect, 'input_pin_drift:' + path, got)
        rows.append({'path': path, 'sha256': got, 'class': 'host_lane'})
    base = os.environ.get('CHIMERA_BASE_SHA')
    require(base in (None, BASE_SHA), 'base_sha_env_mismatch', str(base))
    return rows


def load_pinned_module(rel, expected_sha, name):
    path = (HERE / rel).resolve()
    if not path.exists():
        raise K01Refusal('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise K01Refusal('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def exec_pinned_script(path, expected_sha, name):
    """Exec a pinned lane script for its constants (prints go to the log).
    Returns the namespace with attribute access."""
    raw = pathlib.Path(path).read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise K01Refusal('interface_pin_drift:' + got)
    namespace = {'__name__': name, '__file__': str(path)}
    stdout = io.StringIO()
    saved = sys.stdout
    sys.stdout = stdout
    try:
        exec(compile(raw, str(path), 'exec'), namespace)
    finally:
        sys.stdout = saved
    namespace['_printed_output'] = stdout.getvalue()
    return _Namespace(namespace)


class _Namespace:
    """Attribute access over an exec namespace (pinned script constants)."""

    def __init__(self, mapping):
        self._mapping = dict(mapping)

    def __getattr__(self, name):
        try:
            return self._mapping[name]
        except KeyError:
            raise AttributeError(name) from None

    def get(self, name, default=None):
        return self._mapping.get(name, default)

    def items(self):
        return self._mapping.items()


# ---------------------------------------------------------------------------
# run-time threshold derivation from pinned bytes
# ---------------------------------------------------------------------------

def numeric_tokens(text):
    """Every numeric literal token in a text (for value-match presence)."""
    tokens = []
    current = []
    for ch in text:
        if ch in '0123456789.eE+-':
            current.append(ch)
        else:
            if current:
                tokens.append(''.join(current))
                current = []
    if current:
        tokens.append(''.join(current))
    parsed = []
    for tok in tokens:
        try:
            val = float(tok)
        except ValueError:
            continue
        if math.isfinite(val):
            parsed.append(val)
    return parsed


def value_present(value, tokens):
    """True iff value matches (==) some numeric token of the pinned bytes."""
    return any(tok == value for tok in tokens)


def derive(cd, gg, lc, gc):
    """Every quoted threshold, derived at run from pinned module constants."""
    d = {}
    d['dt_s'] = lc.DT
    d['g_record'] = lc.G
    d['g_standard'] = cd.G_STD
    d['mu_placeholder_s'] = cd.MU_S
    d['mu_placeholder_k'] = cd.MU_K
    d['mu_scenario_declared'] = MU_SCENARIO
    d['jn_press_ns'] = cd.JN
    d['press_n'] = cd.JN / cd.DT
    d['m_scene_kg'] = cd.M_SCENE
    d['band_kg'] = dict(cd.M_BAND)
    d['trunk_radius_m'] = gg.TRUNK_R
    d['trunk_diameter_m'] = gg.TRUNK_D
    d['fingertip_span_m'] = gg.SPAN_SEALED
    d['fa_band'] = list(cd.F_A_BAND)
    d['reach_envelope_m'] = cd.REACH_ENVELOPE

    press = cd.JN / cd.DT   # 60.0 N declared fixture press (jn/DT)

    def static_req_std(m, n, mu):
        # sealed G01 closed form P_req = W/(n*mu), standard-g canonical
        return (m * cd.G_STD) / (n * mu)

    def static_req_rec(m, n, mu):
        return (m * cd.G_REC) / (n * mu)

    def mu_crit_std(m, n):
        # TRUE static closure threshold mu >= W/(n*(jn/DT)) (DERIVATION
        # section 7 correction; the sealed G01 rows are the std-g authority)
        return (m * cd.G_STD) / (n * press)

    def mu_crit_rec(m, n):
        return (m * cd.G_REC) / (n * press)

    d['p_req_scene_n3_std_N'] = static_req_std(cd.M_SCENE, 3, cd.MU_S)
    d['p_req_scene_n3_rec_N'] = static_req_rec(cd.M_SCENE, 3, cd.MU_S)
    d['mu_crit_scene_n3_std'] = mu_crit_std(cd.M_SCENE, 3)
    d['mu_crit_scene_n3_rec'] = mu_crit_rec(cd.M_SCENE, 3)
    d['static_table_std'] = {
        '%s|n=%d' % (name, n): mu_crit_std(m, n)
        for name, m in list(cd.M_BAND.items()) + [('scene', cd.M_SCENE)]
        for n in (2, 3)}
    d['static_table_rec'] = {
        '%s|n=%d' % (name, n): mu_crit_rec(m, n)
        for name, m in list(cd.M_BAND.items()) + [('scene', cd.M_SCENE)]
        for n in (2, 3)}

    def transfer_req(m, n):
        return (m / (n - 1)) * cd.G_REC * cd.DT

    d['cap_ns_placeholder'] = cd.MU_S * cd.JN
    d['transfer_req_scene_n3_ns'] = transfer_req(cd.M_SCENE, 3)
    d['transfer_req_scene_n2_ns'] = transfer_req(cd.M_SCENE, 2)
    d['transfer_req_band_lo_n3_ns'] = transfer_req(cd.M_BAND['band_lo'], 3)
    d['cap_ns_at_scenario_mu'] = MU_SCENARIO * cd.JN
    d['transfer_table'] = {
        '%s|n=%d' % (name, n): transfer_req(m, n)
        for name, m in list(cd.M_BAND.items()) + [('scene', cd.M_SCENE)]
        for n in (2, 3)}

    # B1/B2 wrap/pincer forms (grasp-geometry law, Sergeant-reviewed)
    alpha = math.atan(cd.MU_S)
    d['wrap_margin_m'] = gg.SPAN_SEALED - gg.TRUNK_D
    d['friction_half_angle_rad'] = alpha
    d['pincer_chord_min_m'] = gg.TRUNK_D * math.cos(alpha)
    d['pincer_mu_crit'] = math.tan(math.acos(gg.SPAN_SEALED / gg.TRUNK_D))
    d['span_subtends_deg'] = math.degrees(
        2.0 * math.asin(gg.SPAN_SEALED / gg.TRUNK_D))

    # zero-mu control closed form (the G04 slide precedent, derived)
    share = cd.M_BAND['band_mid'] / 3
    d['zero_mu_control'] = {
        'reading': '%s|n=3|mu=0' % CONTROL_N[0],
        'pad_share_kg': share,
        'hold_ticks': 20,
        'disp_hold_closed_form_m':
            lc.G * (lc.DT ** 2) * (20 * 21 / 2),
    }

    # The five RETRACTED defective static quotes, re-derived arithmetically
    # from the sealed constants (DERIVATION section 7 retraction: they were
    # the mu_true/0.6 mis-convention rows and two n=1 values). Their VALUES
    # must not appear in any emitted artifact; only these arithmetic forms
    # exist here, and the receipts assert their absence.
    press = cd.JN / cd.DT
    d['_defective_literal_forms'] = {
        'band_n2_lo_mu_true_over_point_six':
            (cd.M_BAND['band_lo'] * cd.G_STD) / (2 * 0.6) / press,
        'band_n2_mid_n1_value': (cd.M_BAND['band_mid'] * cd.G_STD) / press,
        'band_n2_hi_n1_value': (cd.M_BAND['band_hi'] * cd.G_STD) / press,
        'scene_n2_mu_true_over_point_six':
            (cd.M_SCENE * cd.G_STD) / (2 * 0.6) / press,
        'scene_n3_mu_true_over_point_six':
            (cd.M_SCENE * cd.G_STD) / (3 * 0.6) / press,
    }
    return d


# ---------------------------------------------------------------------------
# the arms
# ---------------------------------------------------------------------------

def initial_pad_verts(gc, geom, n):
    """Declared pad placement (pinned fixture builders), per channel."""
    facets = gc.channel_facets(geom, n)
    out = []
    for _ti, cen, nrm in facets:
        ey, ez = gc.orthobasis(nrm)
        origin = gc.vadd(cen, gc.vscale(nrm, gc.PAD_OFFSET_M))
        out.append([list(v) for v in gc.place_tetra(origin, nrm, ey, ez)])
    return out


def run_approach(lc, gc, geom, trace_rows):
    """P1: the declared scaffold approach leg (solver ticks, trunk-only
    fixture scene; the fixture hand enters only at the declared contact
    phase). Records zero trunk contacts pre-seam."""
    trunk = lc.Body(body_id='trunk_01.lateral',
                    surface_id='trunk_01.lateral',
                    matter_id=gc.TRUNK_MATTER, mass_kg=1.0,
                    mu_s=gc.TRUNK_MU_S, mu_k=gc.TRUNK_MU_K,
                    thickness_m=gc.SOLID_THICKNESS_M,
                    vertices=list(geom['vertices_m06']),
                    triangles=[geom['triangles'][i]
                               for i in geom['lateral_indices']],
                    pinned=True)
    lo, hi = SCAFFOLD['terminal_window_m']
    start = SCAFFOLD['start_base_to_trunk_axis_m']
    speed = SCAFFOLD['approach_speed_mps']
    rows = []
    terminal = None
    for tick in range(1, SCAFFOLD['horizon_ticks'] + 1):
        distance = start - speed * lc.DT * tick
        records, ledger = lc.solve_tick([trunk])
        sites = sorted(set(
            (r['surface_a'], r['surface_b']) for r in records))
        require(not records, 'premature_trunk_contact',
                {'tick': tick, 'sites': sites})
        entry = {'tick': tick, 't_seconds': tick * lc.DT,
                 'base_distance_m': distance, 'trunk_contact_count': 0,
                 'contact_sites': sites}
        if terminal is None and distance <= hi:
            require(distance >= lo, 'approach_window_skipped',
                    {'tick': tick, 'distance': distance})
            terminal = dict(entry)
            terminal['terminated'] = True
            rows.append(entry)
            break
        rows.append(entry)
    require(terminal is not None,
            'approach_window_not_reached_within_horizon',
            SCAFFOLD['horizon_ticks'])
    trace_rows['approach'] = rows
    return {
        'terminal_tick': terminal['tick'],
        'terminal_distance_m': terminal['base_distance_m'],
        'window': [lo, hi],
        'inside_window': lo <= terminal['base_distance_m'] <= hi,
        'ticks_used': len(rows),
        'horizon_ticks': SCAFFOLD['horizon_ticks'],
        'pre_seam_trunk_contacts': 0,
        'script': {k: v for k, v in SCAFFOLD.items()},
        'walk_state_at_termination':
            'certified-sealed (W10 acceptance head c31a14b6cf5357df070985ab8'
            '3d0c040e824eee2, receipt 0e9c6de5...; NOT re-claimed and no '
            'walking policy executed in this fixture; the certified line '
            'enters the contact phase as the declared 10.037998 kg pad '
            'share)',
    }


def phase_rows(rows, phase):
    """Keyed per-phase extractor (G07 pattern): refuses unknown/empty."""
    require(phase in ('hold', 'release', 'approach'),
            'unknown_phase:' + str(phase))
    out = [r for r in rows if r['phase'] == phase]
    require(out, 'empty_phase:' + str(phase))
    return out


def run_arm(g05, gc, lc, geom, reading, n, scenario_id, trace_rows,
            mu_s=None, mu_k=None, hold=None, release=None, press=None):
    """One observed scenario arm through the sealed G05 seam (which
    cross-validates the G05 loop bit-identical against gc.run_scenario)."""
    kwargs = {}
    if mu_s is not None:
        kwargs['mu_s'] = mu_s
    if mu_k is not None:
        kwargs['mu_k'] = mu_k
    if hold is not None:
        kwargs['hold_ticks'] = hold
    if release is not None:
        kwargs['release_ticks'] = release
    if press is not None:
        kwargs['press_ns'] = press
    reading_kg = dict(gc.READINGS_KG)[reading]
    header, rows, seam, z0, centroids = g05.observe_and_deliver(
        gc, lc, geom, reading_kg, n, scenario_id=scenario_id, **kwargs)
    share = reading_kg / n
    trace_rows[scenario_id] = {
        'header': header, 'rows': rows,
        'initial_centroid_z': z0, 'seam_census': seam.census(),
    }
    return {'header': header, 'rows': rows, 'share_kg': share,
            'z0': z0, 'centroids': centroids}


def pad_states(arm, n, phase='hold'):
    """(final tick modes, cumulative disp) per pad from recorded rows of
    the given phase (hold-end by default: the capture states are the
    hold-window states, e.g. the control's pinned FB2 20-tick press
    slide, not its release end)."""
    rows = phase_rows(arm['rows'], phase)
    last = rows[-1]
    modes = [p['mode'] for p in last['pads']]
    disp = [p['disp_down_m_cum'] for p in last['pads']]
    return modes, disp


def check_press_envelope(arm, press_ns, phases=('hold',)):
    """Per-tick press impulse inside the sealed fixture envelope (jn == P,
    G04 window WIN_JN) over the given phases; returns worst |jn - P|."""
    worst = 0.0
    for phase in phases:
        for row in phase_rows(arm['rows'], phase):
            for pad in row['pads']:
                worst = max(worst, abs(pad['jn_sum_Ns'] - press_ns))
    require(worst <= WIN_JN, 'press_impulse_outside_envelope', worst)
    return worst


def check_slip_recursion(arm, share, mu_k, press_ns, lc):
    """The slip recursion discriminator: vt_post(k) == k*(g*DT - mu_k*P/m)
    (from tick 1) and disp_tick(k) == v(k)*DT after tick 1 (G04 sealed
    windows). Returns worst residuals."""
    g, dt = lc.G, lc.DT
    dv = g * dt - mu_k * press_ns / share
    worst_v = 0.0
    worst_d = 0.0
    rows = phase_rows(arm['rows'], 'hold')
    for k, row in enumerate(rows, start=1):
        for pad in row['pads']:
            require(pad['mode'] == 'slip', 'expected_slip_mode',
                    {'tick': row['tick'], 'mode': pad['mode']})
            worst_v = max(worst_v, abs(pad['vt_post_mps'] - k * dv))
            if k >= 2:
                worst_d = max(worst_d, abs(pad['disp_tick_m'] - k * dv * dt))
    require(worst_v <= WIN_RECURSION_V, 'slip_recursion_violation', worst_v)
    require(worst_d <= WIN_DISP, 'disp_recursion_violation', worst_d)
    return {'dv_per_tick_mps': dv, 'worst_v_residual_mps': worst_v,
            'worst_disp_residual_m': worst_d}


def check_freefall_release(arm, share, lc):
    """Release leg: velocity recursion v(k)-v(k-1) == g*DT; jn/jt under the
    share-scaled a2 bars."""
    g, dt = lc.G, lc.DT
    rows = phase_rows(arm['rows'], 'release')
    worst_v = 0.0
    worst_j = 0.0
    prev = None
    for row in rows:
        for pad in row['pads']:
            worst_j = max(worst_j, pad['jn_sum_Ns'], pad['jt_sum_Ns'])
        vt = max(pad['vt_post_mps'] for pad in row['pads'])
        if prev is not None:
            worst_v = max(worst_v, abs(vt - prev - g * dt))
        prev = vt
    require(worst_v <= WIN_RECURSION_V, 'freefall_recursion_violation',
            worst_v)
    require(worst_j <= share * WIN_RELEASE_SCALE,
            'release_not_clean', worst_j)
    return {'worst_v_residual_mps': worst_v, 'worst_release_impulse_Ns':
            worst_j, 'bar_Ns': share * WIN_RELEASE_SCALE}


def check_stick_window(arm, n, ticks):
    """Every hold tick: every available channel recorded stick."""
    rows = phase_rows(arm['rows'], 'hold')
    require(len(rows) >= ticks, 'hold_window_short', len(rows))
    for row in rows[:ticks]:
        for pad in row['pads'][:n]:
            require(pad['mode'] == 'stick', 'expected_stick_mode',
                    {'tick': row['tick'], 'mode': pad['mode']})
    return True


def site_census(arms):
    """Zero undeclared contact sites across every recorded contact."""
    declared = set(CONTACT_SITES_DECLARED)
    census = {'declared_sites': sorted(declared), 'records': 0,
              'undeclared': []}
    for name, arm in arms.items():
        for row in arm['rows']:
            for pad in row['pads']:
                census['records'] += 1
                for surface in pad['surfaces']:
                    if surface not in declared:
                        census['undeclared'].append(
                            {'arm': name, 'tick': row['tick'],
                             'surface': surface})
    require(not census['undeclared'], 'undeclared_contact_site',
            census['undeclared'][:5])
    return census


def pad_verts_after(arm, verts0, disp):
    """Recorded-state pad vertex sets: pinned placement translated by the
    measured cumulative displacement (translation-only kinematics;
    cross-checked against the seam's measured centroids)."""
    out = []
    for k, verts in enumerate(verts0):
        out.append([[v[0], v[1], v[2] - disp[k]] for v in verts])
    return out


def check_centroid_consistency(arm, z0, disp, n, row_index=None):
    """Measured pad centroid z must equal z0 - disp at the SAME tick the
    disp was read from (translation-only kinematics, G05 field law)."""
    worst = 0.0
    centroids = arm['centroids'][row_index if row_index is not None
                                 else len(arm['centroids']) - 1]
    for k in range(n):
        measured = centroids[k][2]
        expected = z0[k] - disp[k]
        worst = max(worst, abs(measured - expected))
    require(worst <= WIN_DISP, 'centroid_state_mismatch', worst)
    return worst
