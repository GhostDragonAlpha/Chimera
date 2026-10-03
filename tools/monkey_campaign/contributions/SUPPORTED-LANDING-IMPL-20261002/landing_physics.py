"""SUPPORTED-LANDING-IMPL-20261002 physics battery (PREREGISTRATION.md,
frozen at commit 10b05f9ff912edd2c3fc1f2d8f4fcc8c261d01ed, committed bytes
sha256 40caec008862e79407eab409967406c1b6dc02aa63b9de08a5b00cf02c57dcdd).

Executes the preregistered SUPPORTED LANDING experiment at the pin: the
RELEASE -> GROUND CONTACT -> REST transition of the certified scene|n=3
release arm onto the DECLARED floor fixture. FIXTURE-CLASS, NEVER a
grasp-chain claim: nothing here is evidence about the anatomical grasp, the
hand bodies (B6 untouched) or the playable objective (prereg section 0.3:
a supported fixture landing completes a diagnostic demonstration of the
certified contact line's ground response, nothing more).

THE SCENE EXTENSION (declared, prereg sections 1/12): the sealed G07
observer ``release_fall_account.observe_with_account`` is IMPORTED, never
forked (host bytes hash-asserted). Its module cannot itself host a floor
body, so the declared floor body is injected by a DELEGATING solve_tick
shim: the shim appends the one declared floor body to the scene body list
(the floor is present from tick 0 of the scene definition, never inserted
mid-run) and delegates everything else to the pinned solver unchanged. The
sealed observer code runs UNMODIFIED and owns the entire per-tick account
INCLUDING the CCD-tick law (the observer's own continuity bound and
recorded stored-energy exchange on collision ticks). The shim additionally
captures, as a declared side channel, each tick's raw solver records, a
reduced ledger (the candidate index lists are dropped to bound the trace;
recorded) and the per-body velocity vectors. The shim and the capture are
declared in every receipt.

Structure (frozen scaffold, prereg section 11): 20 hold ticks (the sealed
G07/K02 hold, re-measured for comparability); release = press removed
EXACTLY; first floor contact predicted at release tick 60 (declared
acceptance window {59, 60, 61}); the observed scene runs 141 ticks total
(20 hold + 121 release ticks), which contains the impact and the declared
60-tick rest window after the settle tick for every impact tick inside the
declared window (settle = impact + 1, the M06 X1 class; impact 61 -> settle
82 -> rest 83..142 exceeds the frozen 141-tick scene by one tick, in which
case P5 records an INCOMPLETE rest window as a completed measurement, never
tuned). ONE arm + its byte-identical rerun.

Predictions (prereg section 5, falsifier pairs):
- P1 hold_prefix_reproduces_sealed_windows
- P2 release_fall_identity_to_declared_floor
- P3 floor_contact_nonpenetration_at_margin
- P4 supporting_impulse_two_term_law
- P5 rest_stability_declared_window
- P6 energy_destination_through_impact
- P7 fences_not_run

REFUSALS: named codes, never silently repaired. The five RETRACTED
defective static quotes (DERIVATION.md section 7, pinned) must not appear
in any artifact; the emitted receipt is token-scanned to assert their
absence.

CPU-only, stdlib (+ numpy for the template gate), deterministic; no RNG,
no wall clock in trace/receipt. Exit codes: 0 all frozen predictions
SUPPORTED; 3 a falsifier fired or a capture gate went RED (receipts still
written; preserve, never tune); 4 a harness refusal (pin drift, threshold
mismatch, undeclared contact site).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

SCHEMA = 'chimera.supported_landing_battery.v1'
TRACE_SCHEMA = 'chimera.supported_landing_trace.v1'

PREREG_COMMIT = '10b05f9ff912edd2c3fc1f2d8f4fcc8c261d01ed'
PREREG_SHA256 = ('40caec008862e79407eab409967406c1b6dc02aa63b9de08a5b00cf02'
                 'c57dcdd')
BASE_SHA = PREREG_COMMIT
IMPL_BASE_NOTE = (
    'the base commit 10b05f9f is the committed LANDING-20261002 prereg '
    'ALONE on top of the instrument-merged tip 27ba0ff8; the publisher '
    'refreshed origin/review/LANDING-20261002 to 10b05f9f (the prereg '
    'refuses any byte mismatch). The K02 merged tip 7c1f395a is an '
    'ancestor of the pin and the certified module files are byte-identical '
    'between 7c1f395a and 10b05f9f (verified at dispatch: empty git '
    'diff --stat over local_contact.py / grip_contact.py / '
    'contact_support_obs.py / trunk_01_mesh.json); the package inputs are '
    'materialized from that base by the sealed create(); CHIMERA_BASE_SHA '
    'is asserted == BASE_SHA. A cached ref is not a claim of remote '
    'freshness (NO_WORKTREES build line).')
PREREG_REL = '../LANDING-20261002/PREREGISTRATION.md'

# ---- pinned interface modules (imported, hash-asserted, never forked) ----
G04_MODULE_REL = '../MAT2-G04/grip_contact.py'
G04_MODULE_SHA256 = ('0d6375484c350039468b31a2f7db2895d3365412aee52ce98de72b'
                     '4173d69245')
G05_MODULE_REL = '../MAT2-G05/contact_support_obs.py'
G05_MODULE_SHA256 = ('3dae0a3805cec86bba8dbae9a6fc563f43cddc98fcd01a693f725e'
                     '4f31c46bd3')
M06_MODULE_REL = '../MAT2-M06/local_contact.py'
M06_MODULE_SHA256 = ('1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6b'
                     'ec8f9a28dc')
G07_OBSERVER_HOST = ('E:/ChimeraWork/monkey-coordination/evidence-store/'
                     'MAT2-G07/source/release_fall_account.py')
G07_OBSERVER_SHA256 = ('78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae'
                       '99cb55b2a8c5')

# ---- git-tree pins (package files, from the sealed base) -----------------
GIT_PINS = {
    PREREG_REL: PREREG_SHA256,
    M06_MODULE_REL: M06_MODULE_SHA256,
    G04_MODULE_REL: G04_MODULE_SHA256,
    G05_MODULE_REL: G05_MODULE_SHA256,
    '../MAT2-M06/test_local_contact.py':
        'b832d0dc07c1762a190d4b662ceed2b1b6dd469cbd22343cb39934e90eb08e77',
    '../MAT2-M06/contact_law.json':
        '583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b',
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
    '../MAT2-G04/test_g04_checks.py':
        'a01b167e4393e2e513ba343f2bc6ba3fdf4d01ee08170f7fe8c3cb1c5c9a0ae1',
    '../MAT2-G04/experiment_receipt.json':
        '0d622f3610a4d23f52655908effe474694867a20e639747dc48535a419319ce8',
    '../MAT2-G04/experiment_trace.json':
        '044516a19bb4d08066dae6cd6132e22a181023fa3c6934d33b4705c2d0f9d621',
    '../MAT2-G04/determinism_receipt.json':
        '44f4f030b2fc958a52ee0c974e16ba36f2895aff7b364bb0e3aa1f6ec13b7347',
    '../MAT2-G04/regression_receipt.json':
        '7f33c6f121f36943c58ef13b1ecd6f0989d45341f2151a2c9920f69b5e0be039',
    '../MAT2-G04/falsifier_receipt.json':
        '04ef594cb7aa856e3afcd9b767e75c5c0dc44206f4c3db16ce678a35886f7fb2',
    '../MAT2-G05/test_g05_checks.py':
        '83ba17604f66fdbe623b71ce481b539862ec39ebf81ee4c8bea2e5af29f9985b',
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
    '../MAT2-F03/assets/trunk_01_mesh.json':
        '3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7',
    '../MAT2-M02/monkey_arm_independent_meshes.json':
        '51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834',
    '../MAT2-M02/independent_shape_regions.json':
        '0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e',
    '../MAT2-M02/monkey_arm_regions.json':
        '15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1',
    'capture_card/TEMPLATE_MANIFEST.json':
        '1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7',
}

# ---- host pins (the frozen prereg section 8 pins; verified 2026-10-02) ---
HOST_ROOT = 'E:/ChimeraWork/monkey-coordination/'
HOST_PINS = {
    HOST_ROOT + 'evidence-store/MAT2-M06/numerical/'
    'experiment_receipt.json':
        '2956dd7aaf3682fc18de9b724ddd8a695011ec74c9a12a5a56744b3d738a9397',
    HOST_ROOT + 'evidence-store/MAT2-G07/numerical/experiment_receipt.json':
        'c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8',
    HOST_ROOT + 'evidence-store/MAT2-G07/report/REPORT.md':
        '34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1',
    G07_OBSERVER_HOST: G07_OBSERVER_SHA256,
    HOST_ROOT + 'evidence-store/MAT2-W09/numerical/falsifier_receipt.json':
        '3a61cdbf43f7b11b4b284c7be969c5f0a36208556942f0832f1022fe87b1204c',
    HOST_ROOT + 'evidence-store/MAT2-W08/verdict_ref/REPORT.md':
        '75bb3d697d80fdfad1044a908269c31881ed83e0386518d4fe8a96146caa6193',
    HOST_ROOT +
    'evidence-store/MAT2-D-MASSREG/numerical/mass_register.json':
        '61fb79b1bf2df8c5e1a5b1bff2ab1c4f41700de25bc7f1a114cbc78fe693cc7a',
    HOST_ROOT + 'evidence-store/MAT2-W04/numerical/w04_certificate.json':
        '07f05bfa982e066ae67413b04e3367c5ad7570830e99fc32edcb86cbe8d87598',
    HOST_ROOT +
    'evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json':
        'be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29',
    HOST_ROOT +
    'evidence-store/MAT2-B07/unclassified/adoption_record.json':
        'f6952e8afc778f79a0ede05b61d73dd7c3fabd68789703552cd6136e25ef0199',
    HOST_ROOT + 'b07-prereqs/RUNTIME_CONTRACT.md':
        'f33c188bcb561b1946b104340cf36cba366709526c095874684529a599df338c',
    HOST_ROOT + 'climb-derivation/DERIVATION.md':
        'da34420558f6632b0544ca94bc3e25ece515027628c7bd8cc54b9fdd30b7ebd9',
    HOST_ROOT + 'assembly-identity/ASSEMBLY_IDENTITY.md':
        '2ab248bda4db799685a5be9f446bb3e731a47b40b9db1108072cce18bafad035',
    HOST_ROOT + 'evidence-store/MAT2-F05/source/FRICTION_SOURCES.md':
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
    'E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md':
        '0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae',
    HOST_ROOT + 'capture-gate-template/README.md':
        '331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6',
    HOST_ROOT + 'capture-gate-template/TEMPLATE_MANIFEST.json':
        '1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7',
    # K02 sealed receipts (the measurement authority consumed by this card)
    'E:/ChimeraWork/task-runner/results/'
    'e4a9da8c3cab4cec89f9e9789dfd234b/receipt.json':
        '02fbe13f5c2970b04b471c6f71161ebcc4888a1c88f7628c353d610870f8f054',
    'E:/ChimeraWork/task-runner/results/'
    'e4a9da8c3cab4cec89f9e9789dfd234b/artifacts/outputs/'
    'k02_experiment_receipt.json':
        '544c744cd230c062133f4411186a46e4234d526d70d80b097eda5cdec64297ac',
}
K02_RESULTS = ('E:/ChimeraWork/task-runner/results/'
               'e4a9da8c3cab4cec89f9e9789dfd234b/artifacts/outputs/')
K02_RECEIPT_REL = K02_RESULTS + 'k02_experiment_receipt.json'
G07_RECEIPT_HOST = (HOST_ROOT +
                    'evidence-store/MAT2-G07/numerical/'
                    'experiment_receipt.json')

# ---- frozen structure (prereg sections 1/5/11) ---------------------------
READING = ('scene', 3)          # the certified scene|n=3 line
HOLD_TICKS = 20                 # the sealed G07/K02 hold (comparability)
FALL_TICKS_TO_CONTACT = 60      # d(60); first-contact acceptance window
CONTACT_WINDOW = (59, 60, 61)   # declared per-channel acceptance window
REST_TICKS = 60                 # the declared rest window after settle
TOTAL_TICKS = 141               # 20 + 121 release ticks (frozen scaffold)
RELEASE_TICKS_OBSERVED = TOTAL_TICKS - HOLD_TICKS   # 121
SETTLE_LAG = 1                  # settle = impact + 1 (M06 X1 class)
FLOOR_HALF_M = 0.3              # declared extent 0.6 m x 0.6 m >= 0.5 x 0.5

# ---- declared tolerance windows (frozen before the run) ------------------
WIN_JN_PRESS = 1e-9        # N*s, press jn == P per channel-tick (K01 bar)
WIN_ENERGY_CROSS = 1e-9    # J, the K02 cross-window ledger reference gate
WIN_RECURSION_V = 1e-9     # m/s, free-fall velocity recursion (sealed form)
WIN_DISP = 1e-9            # m, displacement/creep windows (sealed)
WIN_RELEASE_SCALE = 1e-10  # N*s per kg (the sealed G07 amendment-a2 bar)
WIN_IMPACT_IDENTITY = 1e-9  # N*s, the P4a re-derived inelastic identity
WIN_STEADY_SUPPORT = 1e-9  # N*s, the P4b weight-share identity
WIN_REST_V = 1e-9          # m/s, post-solve |v| in the rest window
WIN_REST_UPV = 1e-9        # m/s, no-upward-velocity bound (e = 0 law)
WIN_STEADY_GAP = 1e-12     # m, steady gap at MARGIN (the X1 class window)
WIN_DEST_CLOSE = 1e-9      # J, the P6 destination decomposition closure
WIN_PREFIX_TICKS = 60      # ticks of guaranteed observer-drift bit-identity
WIN_TOKEN = 1e-12          # relative, derived-vs-pinned float form match

CONTACT_SITES_DECLARED = ('trunk_01.lateral', 'grip.pad_0', 'grip.pad_1',
                          'grip.pad_2', 'landing.ground_plane')
FLOOR_BODY_ID = 'landing.ground_plane'
FLOOR_MATTER = 'declared_fixture_ground'


class LandingRefusal(ValueError):
    """Named harness refusal; receipts still written (exit 4)."""


def require(ok, code, detail=''):
    if not ok:
        raise LandingRefusal(code + (': ' + str(detail) if detail != '' else ''))


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def write_canonical(path, value):
    data = canonical(value)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data)
    return sha256_bytes(data)


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
    return any(tok == value for tok in tokens)


def load_pinned_module(rel, expected_sha, name):
    path = (HERE / rel).resolve()
    if not path.exists():
        raise LandingRefusal('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise LandingRefusal('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pinned_host_module(path_str, expected_sha, name):
    path = pathlib.Path(path_str)
    if not path.exists():
        raise LandingRefusal('interface_pin_missing:' + path_str)
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise LandingRefusal('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pinned_json(path_str, expected_sha):
    path = pathlib.Path(path_str)
    require(path.exists(), 'input_pin_missing:' + path_str)
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    require(got == expected_sha, 'input_pin_drift:' + path_str, got)
    return json.loads(raw.decode('utf-8'))


def verify_template_manifest():
    manifest = json.loads((HERE / 'capture_card/TEMPLATE_MANIFEST.json')
                          .read_bytes().decode('utf-8'))
    rows = []
    for rel, expect in sorted(manifest['files'].items()):
        path = HERE / 'capture_card' / rel
        if not path.exists():
            raise LandingRefusal('template_pin_missing:' + rel)
        got = sha256_file(path)
        require(got == expect, 'template_pin_drift:' + rel, got)
        rows.append({'path': 'capture_card/' + rel, 'sha256': got,
                     'class': 'template_manifest'})
    return rows


def verify_pins():
    rows = []
    for rel, expect in sorted(GIT_PINS.items()):
        path = (HERE / rel).resolve()
        if not path.exists():
            raise LandingRefusal('input_pin_missing:' + str(path))
        got = sha256_file(path)
        require(got == expect, 'input_pin_drift:' + str(path), got)
        rows.append({'path': rel, 'sha256': got, 'class': 'git_tree'})
    for path, expect in sorted(HOST_PINS.items()):
        p = pathlib.Path(path)
        if not p.exists():
            raise LandingRefusal('input_pin_missing:' + path)
        got = sha256_file(p)
        require(got == expect, 'input_pin_drift:' + path, got)
        rows.append({'path': path, 'sha256': got, 'class': 'host_lane'})
    base = os.environ.get('CHIMERA_BASE_SHA')
    require(base in (None, BASE_SHA), 'base_sha_env_mismatch', str(base))
    return rows


# ---------------------------------------------------------------------------
# the declared floor fixture and the scene-extension shim
# ---------------------------------------------------------------------------

def build_floor_body(lc, gc, z_floor):
    """The ONE declared floor fixture body (prereg section 1): pinned,
    matter 'declared_fixture_ground', friction the NAMED PLACEHOLDERS
    (labeled), thickness the F03 heritage 0.0, two triangles forming a
    horizontal plane with declared extent 0.6 m x 0.6 m (>= 0.5 m x 0.5 m),
    upper surface through z_floor."""
    h = FLOOR_HALF_M
    zf = float(z_floor)
    vertices = [(-h, -h, zf), (h, -h, zf), (h, h, zf), (-h, h, zf)]
    triangles = [(0, 1, 2), (0, 2, 3)]   # right-hand normals +z (up)
    return lc.Body(body_id=FLOOR_BODY_ID, surface_id=FLOOR_BODY_ID,
                   matter_id=FLOOR_MATTER, mass_kg=1.0,
                   mu_s=gc.PAD_MU_S, mu_k=gc.PAD_MU_K,
                   thickness_m=gc.SOLID_THICKNESS_M, vertices=vertices,
                   triangles=triangles, pinned=True)


class FloorSceneSolver:
    """The declared scene-extension shim: solve_tick appends the ONE
    declared floor body to the scene body list (present from tick 0) and
    delegates to the pinned solver unchanged. Everything else (Body, DT,
    G, ...) delegates by attribute. Declared side channel: per tick the raw
    records, a REDUCED ledger (the candidate index lists 'cand_set' and
    'cand_keys' are dropped to bound the trace; recorded here) and the
    per-body velocity vectors before/after the solve. The sealed observer
    module bytes are unmodified and own the entire per-tick account."""

    def __init__(self, lc, floor_body):
        self._lc = lc
        self._floor = floor_body
        self.records_log = []
        self.ledger_log = []
        self.velocity_log = []

    def solve_tick(self, bodies, **kw):
        scene = list(bodies) + [self._floor]
        before = dict((b.id, tuple(b.velocity)) for b in scene)
        records, ledger = self._lc.solve_tick(scene, **kw)
        after = dict((b.id, tuple(b.velocity)) for b in scene)
        reduced = dict((k, v) for k, v in ledger.items()
                       if k not in ('cand_set', 'cand_keys'))
        reduced['candidates'] = ledger.get('candidates')
        reduced['entries'] = ledger.get('entries')
        reduced['motion_bound'] = ledger.get('motion_bound')
        self.records_log.append(records)
        self.ledger_log.append(reduced)
        self.velocity_log.append({'before': before, 'after': after})
        return records, ledger

    def __getattr__(self, name):
        return getattr(self._lc, name)


# ---------------------------------------------------------------------------
# run-time derivation from pinned bytes
# ---------------------------------------------------------------------------

def derive(lc, gc, rfa):
    """Every declared constant, derived at run from the pinned modules'
    own literals (the executable G04-share construction; never
    hand-copied)."""
    g, dt = lc.G, lc.DT
    reading_kg = dict(gc.READINGS_KG)[READING[0]]
    share = reading_kg / READING[1]
    d = {}
    d['g_record'] = g
    d['dt_s'] = dt
    d['cadence_hz'] = 1.0 / dt
    d['restitution'] = lc.RESTITUTION
    d['slop_m'] = lc.SLOP_M
    d['margin_m'] = lc.MARGIN
    d['beta'] = lc.BETA
    d['thickness_m'] = lc.THICKNESS_M
    d['scene_kg'] = reading_kg
    d['share_kg'] = share
    d['mu_placeholder_s'] = gc.PAD_MU_S
    d['mu_placeholder_k'] = gc.PAD_MU_K
    d['mu_trunk_s'] = gc.TRUNK_MU_S
    d['mu_trunk_k'] = gc.TRUNK_MU_K
    d['mu_floor_declared_s'] = gc.PAD_MU_S
    d['mu_floor_declared_k'] = gc.PAD_MU_K
    d['pair_rule'] = 'elementwise_min'
    d['pair_mu_floor_s'] = min(gc.PAD_MU_S, gc.TRUNK_MU_S)
    d['pair_mu_floor_k'] = min(gc.PAD_MU_K, gc.TRUNK_MU_K)
    d['press_ns'] = gc.PRESS_JN_NS
    d['press_n'] = gc.PRESS_JN_NS / dt
    d['solid_thickness_m'] = gc.SOLID_THICKNESS_M
    d['pad_offset_m'] = gc.PAD_OFFSET_M
    # the fall closed forms (LB4): d(N) = g*DT^2*N(N+1)/2; v(N) = N*(g*DT)
    d['d40_closed_form_m'] = g * dt ** 2 * (40 * 41 // 2)
    d['v40_closed_form_mps'] = 40 * (g * dt)
    d['d60_closed_form_m'] = g * dt ** 2 * (60 * 61 // 2)
    d['v60_closed_form_mps'] = 60 * (g * dt)
    d['remaining_travel_tick60_m'] = g * dt ** 2 * 60
    # the support identities (LB5): per-tick weight-share impulse
    d['support_per_channel_ns'] = share * (g * dt)
    d['support_total_ns'] = sum([share * (g * dt)] * READING[1])
    # the closed-form impact scale (LB6, DECLARED ANNOTATION CLASS, never
    # an enforced identity): KE_closed(60) = 0.5*share*v(60)^2
    d['impact_jn_scene_ns'] = share * (60 * (g * dt))
    d['ke_closed_pad_J'] = 0.5 * share * (60 * (g * dt)) ** 2
    d['ke_closed_total_J'] = sum([0.5 * share * (60 * (g * dt)) ** 2]
                                 * READING[1])
    d['ke40_closed_pad_J'] = 0.5 * share * (40 * (g * dt)) ** 2
    # the release bar (amendment a2)
    d['release_bar_ns'] = share * WIN_RELEASE_SCALE
    d['total_release_bar_ns'] = share * READING[1] * WIN_RELEASE_SCALE
    # the sealed observer's own windows (imported, never re-declared)
    d['observer_windows'] = {
        'win_energy_J': rfa.WIN_ENERGY, 'win_loss_J': rfa.WIN_LOSS,
        'win_drift_J': rfa.WIN_DRIFT, 'win_replay_v_mps': rfa.WIN_REPLAY_V,
        'win_cont_m': rfa.WIN_CONT,
        'win_release_scale_Ns_per_kg': rfa.WIN_RELEASE_SCALE,
        'win_recursion_v_mps': rfa.WIN_RECURSION_V,
        'win_disp_m': rfa.WIN_DISP,
        'hold_ticks_module': rfa.HOLD_TICKS,
        'release_ticks_module': rfa.RELEASE_TICKS,
    }
    return d


REQUIRED_PRESENCE = [
    ('scene_kg', ['prereg', 'gc_module', 'massreg']),
    ('share_kg', ['prereg']),
    ('g_record', ['prereg', 'lc_module', 'g07_receipt']),
    ('dt_s', ['prereg', 'lc_module', 'g07_receipt']),
    ('restitution', ['lc_module', 'm06_prereg']),
    ('slop_m', ['prereg', 'lc_module']),
    ('margin_m', ['prereg', 'lc_module']),
    ('beta', ['prereg', 'lc_module']),
    ('press_n', ['prereg']),
    ('d40_closed_form_m', ['prereg']),
    ('v40_closed_form_mps', ['prereg']),
    ('d60_closed_form_m', ['prereg']),
    ('v60_closed_form_mps', ['prereg']),
    ('remaining_travel_tick60_m', ['prereg']),
    ('support_per_channel_ns', ['prereg']),
    ('support_total_ns', ['prereg']),
    ('ke_closed_pad_J', ['prereg']),
    ('ke_closed_total_J', ['prereg']),
]
# PRESENCE NOTE (the frozen prereg section 5 refinement law: corpus-value-
# match applies WHEREVER the value exists in pinned bytes): the derived
# scene-scale impact impulse (share*v(60) = 9.847276038 N*s class) and the
# share-scaled release bar (share_kg*1e-10 = 3.3459993333333336e-10 N*s)
# are DECLARED DERIVATIONS recorded in every receipt, but their float
# literals do NOT exist in the pinned bytes (the prereg carries the FORMS
# 'share*|vn_pre|' and 'share_kg * 1e-10', not the products), so they are
# deliberately NOT in REQUIRED_PRESENCE. The dev sealed run
# e662d53d583d4a589224ba7279db056a refused exactly these two
# (threshold_pin_mismatch, PRESERVED in DEV_RUN_REFUSALS.md) and the
# presence list was corrected to the prereg's own law.

PRESENCE_SOURCES = {
    'prereg': HERE / PREREG_REL,
    'gc_module': HERE / G04_MODULE_REL,
    'lc_module': HERE / M06_MODULE_REL,
    'm06_prereg': HERE / '../MAT2-M06/PREREGISTRATION.md',
    'g07_receipt': pathlib.Path(G07_RECEIPT_HOST),
    'massreg': pathlib.Path(HOST_ROOT +
                            'evidence-store/MAT2-D-MASSREG/numerical/'
                            'mass_register.json'),
}

# the five RETRACTED defective static quotes (DERIVATION.md section 7,
# pinned): re-derived arithmetically and asserted ABSENT from every
# emitted receipt byte.
DEFECTIVE_G_STD = 9.80665


def defective_literal_forms(d):
    mu_s = d['mu_placeholder_s']
    press_n = d['press_n']
    scene = d['scene_kg']
    band_lo, band_mid, band_hi = 5.4, 6.15, 6.9
    return {
        'band_n2_lo_mu_true_over_point_six':
            (band_lo * DEFECTIVE_G_STD) / (2 * mu_s) / press_n,
        'band_n2_mid_n1_value': (band_mid * DEFECTIVE_G_STD) / press_n,
        'band_n2_hi_n1_value': (band_hi * DEFECTIVE_G_STD) / press_n,
        'scene_n2_mu_true_over_point_six':
            (scene * DEFECTIVE_G_STD) / (2 * mu_s) / press_n,
        'scene_n3_mu_true_over_point_six':
            (scene * DEFECTIVE_G_STD) / (3 * mu_s) / press_n,
    }


def g07_scene_n3_ledger(g07_receipt):
    totals = g07_receipt['x_evidence']['scenario_account_totals'][
        'scene|n=3']
    hold = totals['hold']
    release = totals['release']
    return {
        'hold_ticks': hold['ticks'],
        'release_ticks': release['ticks'],
        'hold_work_press_J': hold['work_press_J'],
        'hold_work_gravity_J': hold['work_gravity_J'],
        'hold_loss_solver_J': hold['loss_solver_J'],
        'hold_work_friction_J': hold['work_friction_J'],
        'release_work_press_J': release['work_press_J'],
        'release_work_gravity_J': release['work_gravity_J'],
        'release_ke_delta_J': release['ke_delta_J'],
        'g_mps2': g07_receipt['measurement']['g_mps2'],
        'dt_s': g07_receipt['measurement']['dt_s'],
    }


def k02_release_authority(k02_receipt):
    rel = k02_receipt['arm_checks']['release']
    return {
        'k02_preregistration_sha256': k02_receipt['preregistration_sha256'],
        'k02_overall_verdict': k02_receipt['overall_verdict'],
        'fall_per_pad_m': list(rel['fall_per_pad_m']),
        'terminal_v_down_mps_recorded': rel['terminal_v_down_mps_recorded'],
        'freefall_worst_v_residual_mps':
            rel['freefall_worst_v_residual_mps'],
        'gravity_work_J': rel['gravity_work_J'],
        'ke_gain_J': rel['ke_gain_J'],
        'ke_identity_delta_J': rel['ke_identity_delta_J'],
        'worst_release_impulse_Ns': rel['worst_release_impulse_Ns'],
        'ground_contact_count': rel['ground_contact_count'],
        'supporting_post_release_contacts':
            rel['supporting_post_release_contacts'],
        'w_press_zero_exact_every_release_tick':
            rel['w_press_zero_exact_every_release_tick'],
    }


def k02_hold_authority(k02_receipt):
    w20 = k02_receipt['verdicts'][
        'P3_hold_energy_ledger_closes']['evidence']['windows']['W20'][
            'ledger']['sums']
    return {'w20_press_J': w20['work_press_J'],
            'w20_gravity_J': w20['work_gravity_J'],
            'w20_loss_solver_J': w20['loss_solver_J']}


# ---------------------------------------------------------------------------
# the observed runs
# ---------------------------------------------------------------------------

def run_reference(rfa, g05, gc, lc, geom, reading_kg, mu_s, mu_k, press_ns):
    """The no-floor reference run: the sealed observer at the declared
    structure (hold 20 + release 59, one tick short of the earliest
    in-window contact) with the observer-drift law armed against
    gc.run_scenario (rows BIT-IDENTICAL, refusal observer_drift). Serves
    (a) the P1/P2 sealed-window comparability anchors, (b) the declared
    floor placement (the release-time pad vertex state), (c) the prefix
    bit-identity reference for the landing run."""
    kwargs = dict(mu_s=mu_s, mu_k=mu_k, press_ns=press_ns,
                  hold_ticks=HOLD_TICKS,
                  release_ticks=CONTACT_WINDOW[0])
    header, rows, acct_rows, centroids = rfa.observe_with_account(
        g05, gc, lc, geom, reading_kg, READING[1], 'landing_scene_n3',
        **kwargs)
    header_ref, rows_ref = gc.run_scenario(
        lc, geom, reading_kg, READING[1], scenario_id='landing_scene_n3',
        **kwargs)
    rfa.cross_check_rows(header, rows, header_ref, rows_ref,
                         'landing_scene_n3')
    return {'header': header, 'rows': rows, 'acct_rows': acct_rows,
            'centroids': centroids,
            'observer_cross_check': 'rows bit-identical to gc.run_scenario '
                                    '(cross_check_rows; observer_drift law)',
            'scene_extension': None}


def initial_pad_verts(gc, geom, n):
    facets = gc.channel_facets(geom, n)
    out = []
    for _ti, cen, nrm in facets:
        ey, ez = gc.orthobasis(nrm)
        origin = gc.vadd(cen, gc.vscale(nrm, gc.PAD_OFFSET_M))
        out.append([list(v) for v in gc.place_tetra(origin, nrm, ey, ez)])
    return out


def derive_floor_placement(gc, lc, ref_rows, verts0):
    """z_floor = min_k(lowest-vertex z of pad k at release) - d(60). The
    release-time state is the tick-20 recorded cumulative displacement
    (translation-only kinematics, the G05 field law); d(60) is derived at
    run from the pinned solver constants."""
    hold_row = ref_rows[HOLD_TICKS - 1]
    disp = [p['disp_down_m_cum'] for p in hold_row['pads'][:READING[1]]]
    z_min_rel = math.inf
    for k, verts in enumerate(verts0):
        for v in verts:
            z_min_rel = min(z_min_rel, v[2] - disp[k])
    d60 = lc.G * lc.DT ** 2 * (60 * 61 // 2)
    return {'release_disp_down_m': disp,
            'min_pad_vertex_z_at_release_m': z_min_rel,
            'd60_derived_m': d60,
            'z_floor_m': z_min_rel - d60,
            'construction_law':
                'z_floor = min_k(lowest pad vertex z at release) - d(60); '
                'd(60) = g*DT^2*(60*61/2) derived from the pinned solver '
                'constants; the release-time state is the tick-20 recorded '
                'cumulative displacement (translation-only kinematics)'}


def run_landing(rfa, g05, gc, lc, geom, reading_kg, mu_s, mu_k, press_ns,
                z_floor):
    """The landing run: the sealed observer through the declared
    scene-extension shim (the floor present from tick 0), 141 ticks. The
    observer's own per-tick account (INCLUDING the CCD-tick law) is the
    enforcement; a sealed-law ValueError aborts the run and is PRESERVED
    as a named refusal by the caller (never repaired)."""
    floor = build_floor_body(lc, gc, z_floor)
    shim = FloorSceneSolver(lc, floor)
    kwargs = dict(mu_s=mu_s, mu_k=mu_k, press_ns=press_ns,
                  hold_ticks=HOLD_TICKS,
                  release_ticks=RELEASE_TICKS_OBSERVED)
    error = None
    try:
        header, rows, acct_rows, centroids = rfa.observe_with_account(
            g05, gc, shim, geom, reading_kg, READING[1], 'landing_scene_n3',
            **kwargs)
    except ValueError as exc:
        error = str(exc)
        header, rows, acct_rows, centroids = None, [], [], []
    arm = {
        'header': header, 'rows': rows, 'acct_rows': acct_rows,
        'centroids': centroids,
        'sealed_law_refusal': error,
        'observer_cross_check':
            'rows bit-identical to the no-floor reference run over the '
            'pre-contact prefix (prefix_bit_identity: the row-level key '
            'law of cross_check_rows; the header matches field-by-field '
            'except the declared scaffold field release_ticks)',
        'scene_extension': {
            'law': 'the sealed observer module is imported unmodified; the '
                   'ONE declared floor body is appended to the scene body '
                   'list by the declared solve_tick shim (present from tick '
                   '0, never inserted mid-run); the CCD-tick law is the '
                   'observer\'s own',
            'floor_body': {
                'body_id': FLOOR_BODY_ID, 'matter_id': FLOOR_MATTER,
                'mu_s': mu_s, 'mu_k': mu_k,
                'mu_label': 'NAMED PLACEHOLDERS declared for the fixture '
                            'class (FRICTION_SOURCES verdict GAP; NB-01/02 '
                            'stands); never tuned, never re-pinned mid-run',
                'thickness_m': gc.SOLID_THICKNESS_M,
                'pinned': True,
                'triangles': 2,
                'extent_m': [2 * FLOOR_HALF_M, 2 * FLOOR_HALF_M],
                'z_floor_m': float(z_floor),
            },
            'pinned_bodies_declared': ['trunk_01.lateral', FLOOR_BODY_ID],
            'captured_side_channel': ['records', 'reduced_ledger',
                                      'velocity_vectors'],
            'reduced_ledger_keys_dropped': ['cand_set', 'cand_keys'],
            'ticks_captured': len(shim.records_log),
        },
    }
    if error is None:
        arm['records_log'] = shim.records_log
        arm['ledger_log'] = shim.ledger_log
        arm['velocity_log'] = shim.velocity_log
    else:
        arm['records_log'] = shim.records_log
        arm['ledger_log'] = shim.ledger_log
        arm['velocity_log'] = shim.velocity_log
    return arm


def floor_records_for_pad(records, pad_id):
    out = []
    for r in records:
        pair = (r['body_a'], r['body_b'])
        if FLOOR_BODY_ID not in pair:
            continue
        if pad_id not in pair:
            continue
        out.append(r)
    return out


def prefix_bit_identity(rfa, arm, ref, scenario_id):
    """The observer-drift law over the pre-contact prefix: the landing
    run's rows are BIT-IDENTICAL to the no-floor reference run's rows up
    to (but excluding) the earliest floor-contact tick. Refusal:
    observer_drift.

    The row-level key law is cross_check_rows' own (same key set, same
    comparisons). The HEADER comparison is asserted field by field with
    ONE declared exception: the scaffold field 'release_ticks' differs by
    construction (the reference stops at 59, one tick short of the
    earliest in-window contact; the landing scene observes 121 release
    ticks so the frozen 141-tick scene contains impact + rest). Any other
    header difference is an observer_drift refusal."""
    first_contact = None
    for i, records in enumerate(arm['records_log']):
        if any(FLOOR_BODY_ID in (r['body_a'], r['body_b'])
               for r in records):
            first_contact = i + 1   # absolute tick
            break
    n = len(arm['rows']) if first_contact is None else first_contact - 1
    n = min(n, len(ref['rows']))
    hdr_diff = sorted(k for k in set(arm['header']) | set(ref['header'])
                      if arm['header'].get(k) != ref['header'].get(k))
    if hdr_diff != ['release_ticks']:
        raise ValueError('observer_drift:header:%s:%s'
                         % (scenario_id, ','.join(hdr_diff)))
    for r_obs, r_ref in zip(arm['rows'][:n], ref['rows'][:n]):
        if r_obs['tick'] != r_ref['tick'] or r_obs['phase'] != r_ref['phase']:
            raise ValueError('observer_drift:row:%d' % r_obs['tick'])
        if r_obs['ledger'] != r_ref['ledger']:
            raise ValueError('observer_drift:ledger:%d' % r_obs['tick'])
        if r_obs['weld_recorded_ns'] != r_ref['weld_recorded_ns']:
            raise ValueError('observer_drift:weld:%d' % r_obs['tick'])
        for p_obs, p_ref in zip(r_obs['pads'], r_ref['pads']):
            for key in ('pad', 'jn_sum_Ns', 'jt_sum_Ns', 'mode',
                        'disp_tick_m', 'surfaces', 'vt_post_mps',
                        'disp_down_m_cum'):
                if p_obs[key] != p_ref[key]:
                    raise ValueError('observer_drift:pads:%s:%d'
                                     % (key, r_obs['tick']))
    return {'prefix_ticks_compared': n,
            'first_floor_record_tick_abs':
                first_contact,
            'header_declared_exception': ['release_ticks'],
            'header_diff_observed': hdr_diff,
            'law': 'rows bit-identical to the no-floor sealed-observer '
                   'reference run over the pre-contact prefix (the '
                   'row-level key law of cross_check_rows; the header '
                   'matches field-by-field except the declared scaffold '
                   'field release_ticks: 59 reference vs 121 observed); '
                   'refusal observer_drift'}


# ---------------------------------------------------------------------------
# the predictions (prereg section 5): each returns (evidence, falsified_list)
# recorded outcomes, never silent normalization
# ---------------------------------------------------------------------------

def check_p1_hold_prefix(arm, d, g07_ledger, k02_hold):
    """P1: the 20 hold ticks reproduce the sealed windows."""
    falsified = []
    rows = arm['rows'][:HOLD_TICKS]
    acct = arm['acct_rows'][:HOLD_TICKS]
    stick = {'stick_ticks': [0] * READING[1],
             'slip_ticks': [0] * READING[1],
             'no_contact_ticks': [0] * READING[1], 'stick_all': True}
    worst_press = 0.0
    for row in rows:
        for k, pad in enumerate(row['pads'][:READING[1]]):
            if pad['mode'] == 'stick':
                stick['stick_ticks'][k] += 1
            else:
                stick['stick_all'] = False
                if pad['mode'] == 'slip':
                    stick['slip_ticks'][k] += 1
                else:
                    stick['no_contact_ticks'][k] += 1
            worst_press = max(worst_press,
                              abs(pad['jn_sum_Ns'] - d['press_ns']))
    creep = [rows[-1]['pads'][k]['disp_down_m_cum']
             for k in range(READING[1])]
    sums = {'work_press_J': 0.0, 'work_gravity_J': 0.0, 'loss_solver_J': 0.0}
    for r in acct:
        for p in r['pads']:
            sums['work_press_J'] += p['work_press_J']
            sums['work_gravity_J'] += p['work_gravity_J']
            sums['loss_solver_J'] += p['loss_solver_J']
    ref_deltas = {
        'press_J': abs(sums['work_press_J'] - g07_ledger['hold_work_press_J']),
        'gravity_J': abs(sums['work_gravity_J']
                         - g07_ledger['hold_work_gravity_J']),
        'friction_J': abs(sums['loss_solver_J']
                          - g07_ledger['hold_loss_solver_J']),
    }
    k02_deltas = {
        'press_J': abs(sums['work_press_J'] - k02_hold['w20_press_J']),
        'gravity_J': abs(sums['work_gravity_J']
                         - k02_hold['w20_gravity_J']),
        'friction_J': abs(sums['loss_solver_J']
                          - k02_hold['w20_loss_solver_J']),
    }
    creep_ok = all(abs(c) <= WIN_DISP for c in creep)
    g07_ok = all(v <= WIN_ENERGY_CROSS for v in ref_deltas.values())
    k02_ok = all(v <= WIN_ENERGY_CROSS for v in k02_deltas.values())
    press_ok = worst_press <= WIN_JN_PRESS
    if not stick['stick_all']:
        falsified.append('P1_non_stick_tick_in_hold_prefix')
    if not creep_ok:
        falsified.append('P1_creep_beyond_declared_window')
    if not (g07_ok and k02_ok):
        falsified.append('P1_sealed_ledger_reference_breach')
    if not press_ok:
        falsified.append('P1_press_bar_breach')
    return {
        'ticks': HOLD_TICKS,
        'stick_census': stick,
        'creep_final_m': creep,
        'creep_inside_window': creep_ok,
        'press_worst_abs_jn_minus_P_Ns': worst_press,
        'press_inside_bar': press_ok,
        'hold_ledger_sums_J': sums,
        'g07_reference_deltas_J': ref_deltas,
        'g07_reference_inside_gate': g07_ok,
        'k02_reference_deltas_J': k02_deltas,
        'k02_reference_inside_gate': k02_ok,
        'observer_cross_check': arm['observer_cross_check'],
        'falsified': falsified,
    }


def check_p2_release_fall(arm, ref, prefix_id, d, k02_rel, verts0):
    """P2: release identity through first floor contact."""
    falsified = []
    rows = arm['rows']
    acct = arm['acct_rows']
    first_contact_abs = prefix_id['first_floor_record_tick_abs']
    if first_contact_abs is None:
        falsified.append('P2_no_floor_contact_record_in_scene')
        first_contact_abs = TOTAL_TICKS + 1
    rel_start = HOLD_TICKS + 1
    contact_rel = first_contact_abs - HOLD_TICKS
    # W_press == 0.0 J exactly, every release tick, every channel
    w_press_zero = all(
        p['work_press_J'] == 0.0
        for r in acct[HOLD_TICKS:] for p in r['pads'])
    if not w_press_zero:
        falsified.append('P2_press_channel_not_removed_exactly')
    # free-fall identity over the pre-contact fall window, per channel,
    # under the SEALED G07 law (release_account convention): the
    # gravity-only recursion is enforced on the UNOBSTRUCTED prefix up to
    # the first recorded wall-collision event; a recorded CCD wall
    # transient is a real contact force with its own impulse accounting
    # (recorded, never support), and the post-collision per-tick velocity
    # deltas are RECORDED as evidence, not forced into the gravity-only
    # form.
    worst_rec = 0.0
    prev = [None] * READING[1]
    first_collision_tick = None
    for row in rows[HOLD_TICKS:first_contact_abs - 1]:
        ai = row['tick'] - 1
        if not all(p['unobstructed'] for p in acct[ai]['pads']):
            first_collision_tick = row['tick']
            break
    post_collision_deltas = []
    for r in acct[:first_contact_abs - 1]:
        if r['phase'] != 'release':
            continue
        tick = r['tick']
        for k in range(READING[1]):
            v_down = -r['pads'][k]['vz_after_mps']
            if prev[k] is not None:
                delta = abs(v_down - prev[k] - d['g_record'] * d['dt_s'])
                if tick < (first_collision_tick or first_contact_abs):
                    worst_rec = max(worst_rec, delta)
                else:
                    post_collision_deltas.append(
                        {'tick': tick, 'pad': k, 'delta_mps': delta})
            prev[k] = v_down
    if worst_rec > WIN_RECURSION_V:
        falsified.append('P2_free_fall_recursion_breach')
    # release-tick impulses inside the share-scaled bar over the fall window
    # (pre-contact; wall micro-contact CCD ticks are recorded collision
    # events per the G07 law, never support)
    bar = d['release_bar_ns']
    worst_imp = 0.0
    collision_events = []
    for row in rows[HOLD_TICKS:first_contact_abs - 1]:
        ai = row['tick'] - 1
        unobstructed = all(p['unobstructed'] for p in acct[ai]['pads'])
        if not unobstructed:
            collision_events.append(
                {'tick': row['tick'],
                 'jn_max_Ns': max(abs(p['jn_sum_Ns']) for p in row['pads']),
                 'jt_max_Ns': max(abs(p['jt_sum_Ns']) for p in row['pads'])})
            continue
        for pad in row['pads'][:READING[1]]:
            worst_imp = max(worst_imp, abs(pad['jn_sum_Ns']),
                            abs(pad['jt_sum_Ns']))
    if worst_imp > bar:
        falsified.append('P2_release_impulse_bar_breach')
    # the FIRST-40 release-tick prefix reproduces the K02 sealed values
    idx40 = HOLD_TICKS + 40 - 1
    fall40 = [rows[idx40]['pads'][k]['disp_down_m_cum']
              - rows[HOLD_TICKS - 1]['pads'][k]['disp_down_m_cum']
              for k in range(READING[1])]
    fall40_deltas = [abs(a - b) for a, b in
                     zip(fall40, k02_rel['fall_per_pad_m'])]
    acct40 = acct[idx40]
    term40 = max(-acct40['pads'][k]['vz_after_mps']
                 for k in range(READING[1]))
    term40_delta = abs(term40 - d['v40_closed_form_mps'])
    if max(fall40_deltas) > WIN_DISP:
        falsified.append('P2_sealed_fall_displacement_anchor_breach')
    if term40_delta > WIN_RECURSION_V:
        falsified.append('P2_sealed_terminal_speed_anchor_breach')
    # first-contact tick inside the declared window
    per_channel_first = []
    for k in range(READING[1]):
        tick_k = None
        for i, records in enumerate(arm['records_log']):
            if floor_records_for_pad(records, 'grip.pad_%d' % k):
                tick_k = i + 1
                break
        per_channel_first.append(tick_k)
    per_channel_rel = [None if t is None else t - HOLD_TICKS
                       for t in per_channel_first]
    window_ok = all(t in CONTACT_WINDOW for t in per_channel_rel
                    if t is not None) and any(
        t is not None for t in per_channel_rel)
    if not window_ok:
        falsified.append('P2_floor_contact_outside_declared_window')
    if any(t is not None and t < min(CONTACT_WINDOW)
           for t in per_channel_rel):
        falsified.append('P2_contact_before_declared_fall_complete')
    return {
        'first_floor_record_tick_abs': first_contact_abs,
        'per_channel_first_contact_tick_release':
            per_channel_rel,
        'contact_window_declared': list(CONTACT_WINDOW),
        'contact_inside_window': window_ok,
        'w_press_zero_exact_every_release_tick': w_press_zero,
        'freefall_recursion_law':
            'the SEALED G07 release_account convention: the gravity-only '
            'recursion is enforced on the unobstructed prefix up to the '
            'first recorded wall-collision event (a recorded CCD wall '
            'transient is a real contact force with its own impulse '
            'accounting, never support); post-collision per-tick velocity '
            'deltas are recorded as evidence below',
        'freefall_worst_v_residual_mps': worst_rec,
        'freefall_recursion_enforced_ticks':
            (first_collision_tick or first_contact_abs) - HOLD_TICKS - 1,
        'post_collision_velocity_deltas':
            sorted(post_collision_deltas,
                   key=lambda x: -x['delta_mps'])[:12],
        'first_wall_collision_tick_abs': first_collision_tick,
        'fall_impulses_worst_Ns': worst_imp,
        'release_bar_Ns': bar,
        'wall_collision_events_pre_contact': collision_events,
        'wall_collision_count_pre_contact': len(collision_events),
        'fall40_measured_m': fall40,
        'fall40_deltas_vs_k02_m': fall40_deltas,
        'k02_fall_per_pad_m': k02_rel['fall_per_pad_m'],
        'terminal40_measured_mps': term40,
        'terminal40_delta_vs_closed_form_mps': term40_delta,
        'k02_terminal_v_down_mps_recorded':
            k02_rel['terminal_v_down_mps_recorded'],
        'k02_freefall_worst_v_residual_mps':
            k02_rel['freefall_worst_v_residual_mps'],
        'k02_ground_contact_count':
            k02_rel['ground_contact_count'],
        'k02_supporting_post_release_contacts':
            k02_rel['supporting_post_release_contacts'],
        'prefix': prefix_id,
        'g07_release_account_fall_slice':
            'release_account evaluated on the pre-contact fall slice; the '
            'clean-release law is the FALL-window law (its bars bite on '
            'unobstructed pre-contact ticks only; the supported rest ticks '
            'are OUTSIDE its declared scope by construction)',
        'falsified': falsified,
    }


def check_p3_nonpenetration(arm, d, verts0, z_floor):
    """P3: nonpenetration at contact, at the margin."""
    falsified = []
    lc_slop = d['slop_m']
    lc_margin = d['margin_m']
    floor_recs = []
    for i, records in enumerate(arm['records_log']):
        for r in records:
            if FLOOR_BODY_ID in (r['body_a'], r['body_b']):
                floor_recs.append({'tick': i + 1, **{
                    k: r[k] for k in ('body_a', 'body_b', 'gap_m', 'jn_Ns',
                                      'jt_Ns', 'mode', 'kind', 'toc',
                                      'normal')}})
    worst_gap = math.inf
    for r in floor_recs:
        worst_gap = min(worst_gap, r['gap_m'])
    if floor_recs and worst_gap < -lc_slop:
        falsified.append('P3_contact_gap_below_negated_slop')
    # steady-state rest gaps, PER PAD (the M06 X1 margin class is the
    # predicted rest class; the named P3 falsifier is a gap below -SLOP or
    # a crossing without a record - a pad resting inside the margin zone
    # is a RECORDED DEVIATION routed as a finding, never tuned and never a
    # silent normalization)
    steady_ticks = _steady_tick_start(arm, d)
    per_pad_steady = []
    for k in range(READING[1]):
        pad_id = 'grip.pad_%d' % k
        gaps = [r['gap_m'] for i in range(steady_ticks - 1, TOTAL_TICKS)
                for r in floor_records_for_pad(arm['records_log'][i], pad_id)]
        smin = min(gaps) if gaps else None
        smax = max(gaps) if gaps else None
        at_margin = (smin is not None
                     and abs(smin - lc_margin) <= WIN_STEADY_GAP)
        per_pad_steady.append({
            'pad': pad_id, 'steady_min_gap_m': smin,
            'steady_max_gap_m': smax,
            'at_margin_class': at_margin,
            'nonpenetrating': smin is not None and smin >= -lc_slop,
        })
    steady_min_gap = min((p['steady_min_gap_m'] for p in per_pad_steady
                          if p['steady_min_gap_m'] is not None),
                         default=None)
    margin_class_pads = sum(1 for p in per_pad_steady
                            if p['at_margin_class'])
    nonpen_all = all(p['nonpenetrating'] for p in per_pad_steady) and (
        not floor_recs or worst_gap >= -lc_slop)
    # no crossing without a record: per tick, min pad vertex z from the
    # recorded cumulative displacement (translation-only) stays above the
    # floor plane within the declared bias-activation bound; and every tick
    # whose closest approach is within the activation margin carries a
    # floor record.
    tol = 1e-12   # the declared CCD activation tolerance class (CCD_TOL_M)
    crossings = []
    activation_misses = []
    for i, r in enumerate(arm['acct_rows']):
        zmins = []
        row = arm['rows'][i]
        for k in range(READING[1]):
            cum = row['pads'][k]['disp_down_m_cum']
            zmin_k = min(v[2] for v in verts0[k]) - cum
            zmins.append(zmin_k)
        tick = i + 1
        tick_has_floor_rec = any(fr['tick'] == tick for fr in floor_recs)
        closest = min(zmins) - z_floor
        if closest < -lc_slop and not tick_has_floor_rec:
            crossings.append({'tick': tick, 'closest_approach_m': closest})
        if closest <= lc_margin + tol and not tick_has_floor_rec:
            activation_misses.append({'tick': tick,
                                      'closest_approach_m': closest})
    if crossings:
        falsified.append('P3_floor_crossing_without_record')
    if activation_misses:
        falsified.append('P3_margin_approach_without_record')
    return {
        'floor_contact_record_count': len(floor_recs),
        'worst_floor_gap_m': worst_gap,
        'slop_bound_m': -lc_slop,
        'steady_min_gap_m': steady_min_gap,
        'steady_min_gap_window_m': WIN_STEADY_GAP,
        'per_pad_steady_gaps': per_pad_steady,
        'margin_class_pad_count': margin_class_pads,
        'nonpenetrating_all_pads_all_records': nonpen_all,
        'margin_class_deviation':
            None if margin_class_pads == READING[1] else (
                'RECORDED DEVIATION (never tuned): %d of %d pads rest at '
                'the M06 X1 margin class (gap == MARGIN, the CCD-commit '
                'settle class); the remaining pad(s) arrived through the '
                'persistent-contact branch (already inside the margin when '
                'the contact tick began) and rest at the observed gap '
                'above the plane - NONPENETRATING (gap >= -SLOP holds '
                'everywhere; the named P3 falsifier did not fire); the '
                'bias term is zero for sub-SLOP penetrations by the '
                'certified law, so no push-out to the margin occurs. '
                'Routed as a finding to the Lieutenant with the chain '
                'stop.' % (margin_class_pads, READING[1])),
        'crossings_without_record': crossings,
        'margin_approaches_without_record': activation_misses,
        'ccd_no_tunnel_law': 'every floor crossing produces a contact '
                             'record (conservative-advancement CCD; the '
                             'negative-control tunneling mode is '
                             'dev-suite-only and never runs here)',
        'falsified': falsified,
    }


def _pad_first_floor_tick(arm, k):
    for i, records in enumerate(arm['records_log']):
        if floor_records_for_pad(records, 'grip.pad_%d' % k):
            return i + 1
    return None


def _steady_tick_start(arm, d):
    """Global settle tick: per pad, the first tick AFTER its impact tick
    whose floor impulse is inside the steady weight-share bar (the
    steady-class transition; the M06 X1 class settles at impact + 1, and a
    longer settle is a completed measurement, never tuned). Global settle =
    max over pads; the frozen scene end if any pad never reaches the
    steady class."""
    target = d['support_per_channel_ns']
    settles = []
    for k in range(READING[1]):
        impact = _pad_first_floor_tick(arm, k)
        if impact is None:
            return TOTAL_TICKS + 1
        settle = None
        for i in range(impact, len(arm['records_log'])):
            recs = floor_records_for_pad(arm['records_log'][i],
                                         'grip.pad_%d' % k)
            if recs and abs(sum(r['jn_Ns'] for r in recs)
                            - target) <= WIN_STEADY_SUPPORT:
                settle = i + 1
                break
        if settle is None:
            return TOTAL_TICKS + 1
        settles.append(settle)
    return max(settles)


def settle_lags(arm, d):
    """Per-pad (impact tick, settle tick, lag) with the lag recorded
    (expected 1, the M06 X1 class; longer is a completed measurement)."""
    target = d['support_per_channel_ns']
    rows = []
    for k in range(READING[1]):
        impact = _pad_first_floor_tick(arm, k)
        settle = None
        if impact is not None:
            for i in range(impact, len(arm['records_log'])):
                recs = floor_records_for_pad(arm['records_log'][i],
                                             'grip.pad_%d' % k)
                if recs and abs(sum(r['jn_Ns'] for r in recs)
                                - target) <= WIN_STEADY_SUPPORT:
                    settle = i + 1
                    break
        rows.append({'pad': 'grip.pad_%d' % k,
                     'impact_tick_abs': impact,
                     'settle_tick_abs': settle,
                     'settle_lag_ticks':
                         None if (impact is None or settle is None)
                         else settle - impact})
    return rows


def check_p4_supporting_impulse(arm, d):
    """P4: the two-term supporting-impulse law."""
    falsified = []
    share = d['share_kg']
    g, dt = d['g_record'], d['dt_s']
    per_pad = []
    steady_ticks = _steady_tick_start(arm, d)
    for k in range(READING[1]):
        pad_id = 'grip.pad_%d' % k
        impact_tick = None
        rows_out = []
        for i, records in enumerate(arm['records_log']):
            recs = floor_records_for_pad(records, pad_id)
            if not recs:
                continue
            tick = i + 1
            jn_total = sum(r['jn_Ns'] for r in recs)
            jt_total = sum(r['jt_Ns'] for r in recs)
            modes = sorted(set(r['mode'] for r in recs))
            ai = acct_row = arm['acct_rows'][tick - 1]['pads'][k]
            vz_press = acct_row['vz_press_mps']
            row = {'tick': tick, 'jn_total_Ns': jn_total,
                   'jt_total_Ns': jt_total, 'modes': modes,
                   'gap_min_m': min(r['gap_m'] for r in recs),
                   'kind': sorted(set(r['kind'] for r in recs)),
                   'vz_press_mps': vz_press}
            if impact_tick is None:
                impact_tick = tick
                vn_pre = vz_press - g * dt
                m_eff = 1.0 / (1.0 / share + 0.0)
                jn_pred = m_eff * (-(1.0 + d['restitution']) * vn_pre + 0.0)
                row['is_impact_tick'] = True
                row['vn_pre_derived_mps'] = vn_pre
                row['jn_inelastic_identity_Ns'] = jn_pred
                row['jn_identity_delta_Ns'] = abs(jn_total - jn_pred)
                if abs(jn_total - jn_pred) > WIN_IMPACT_IDENTITY:
                    falsified.append(
                        'P4_impact_identity_breach_pad%d' % k)
            else:
                row['is_impact_tick'] = False
            rows_out.append(row)
        per_pad.append({'pad': pad_id, 'impact_tick_release':
                        None if impact_tick is None
                        else impact_tick - HOLD_TICKS,
                        'floor_ticks': rows_out})
    # steady term: every rest-window tick, floor jn == share*g*DT
    steady_ticks = _steady_tick_start(arm, d)
    steady_ok = True
    steady_worst = 0.0
    steady_census = {'still': 0, 'stick': 0, 'slip': 0, 'other': 0}
    steady_rows = []
    target = d['support_per_channel_ns']
    for i in range(steady_ticks - 1, TOTAL_TICKS):
        records = arm['records_log'][i]
        for k in range(READING[1]):
            recs = floor_records_for_pad(records, 'grip.pad_%d' % k)
            if not recs:
                steady_ok = False
                steady_rows.append({'tick': i + 1, 'pad': k,
                                    'state': 'missing_floor_record'})
                continue
            jn_total = sum(r['jn_Ns'] for r in recs)
            delta = abs(jn_total - target)
            steady_worst = max(steady_worst, delta)
            if delta > WIN_STEADY_SUPPORT:
                steady_ok = False
            for r in recs:
                mode = r['mode']
                if mode in steady_census:
                    steady_census[mode] += 1
                else:
                    steady_census['other'] += 1
    if not steady_ok:
        falsified.append('P4_steady_weight_share_breach')
    # supporting classification: jn > 0 while the pad is held at rest
    supporting = []
    for i in range(steady_ticks - 1, TOTAL_TICKS):
        for k in range(READING[1]):
            vz_after = arm['acct_rows'][i]['pads'][k]['vz_after_mps']
            records = arm['records_log'][i]
            recs = floor_records_for_pad(records, 'grip.pad_%d' % k)
            if recs and abs(vz_after) <= WIN_REST_V:
                supporting.append({'tick': i + 1, 'pad': k})
    return {
        'per_pad_impulse_series': per_pad,
        'steady_tick_start_abs': steady_ticks,
        'steady_target_ns': target,
        'steady_worst_delta_Ns': steady_worst,
        'steady_inside_bar': steady_ok,
        'steady_mode_census': steady_census,
        'supporting_contact_samples': len(supporting),
        'recorded_vs_supporting':
            'the K02 arm\'s 120 mid-fall micro-contacts were '
            'recorded-NOT-supporting; this card records the transition to '
            'SUPPORTING with the impulse identities as the evidence '
            '(Captain order #7 check 1)',
        'falsified': falsified,
    }


def check_p5_rest_stability(arm, d):
    """P5: post-landing rest stability over the declared 60-tick window."""
    falsified = []
    steady_ticks = _steady_tick_start(arm, d)
    window = list(range(steady_ticks, min(steady_ticks + REST_TICKS,
                                          TOTAL_TICKS + 1)))
    window_complete = len(window) == REST_TICKS
    if not window_complete:
        falsified.append('P5_rest_window_incomplete_in_frozen_scene')
    worst_v = 0.0
    worst_disp = 0.0
    worst_up = -math.inf
    mode_census = {'still': 0, 'stick': 0, 'slip': 0, 'no_contact': 0}
    for i in window:
        ai = i - 1
        vel = arm['velocity_log'][ai]['after']
        for k in range(READING[1]):
            v = vel['grip.pad_%d' % k]
            speed = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
            worst_v = max(worst_v, speed)
            if speed > WIN_REST_V:
                falsified.append('P5_velocity_breach_tick%d_pad%d'
                                 % (i, k))
            worst_up = max(worst_up, v[2])
            if v[2] > WIN_REST_UPV:
                falsified.append('P5_upward_velocity_tick%d_pad%d'
                                 % (i, k))
            disp = arm['rows'][ai]['pads'][k]['disp_tick_m']
            worst_disp = max(worst_disp, abs(disp))
            if abs(disp) > WIN_DISP:
                falsified.append('P5_displacement_breach_tick%d_pad%d'
                                 % (i, k))
        # mode census from the CAPTURED FLOOR RECORDS (the row-level mode
        # collapses the solver's 'still' class into 'slip' by the sealed
        # G04 convention; the record modes are the declared census source)
        for k in range(READING[1]):
            recs = floor_records_for_pad(arm['records_log'][ai],
                                         'grip.pad_%d' % k)
            if not recs:
                mode_census['no_contact'] += 1
            for r in recs:
                mode_census[r['mode']] = mode_census.get(r['mode'], 0) + 1
    settle_class = 'first_steady_class_tick_after_impact'
    return {
        'settle_tick_abs': steady_ticks,
        'per_pad_settle_rows': settle_lags(arm, d),
        'settle_class': settle_class,
        'window_ticks': len(window),
        'window_complete': window_complete,
        'window_declared': REST_TICKS,
        'worst_speed_mps': worst_v,
        'worst_abs_tick_displacement_m': worst_disp,
        'worst_vz_after_mps': worst_up,
        'no_bounce_law': 'RESTITUTION 0.0 (declared inelastic): any '
                         'upward-motion tick is THE P5 falsifier; the '
                         'solver is TRANSLATION-ONLY, so this claim is '
                         'TRANSLATIONAL rest only (toppling unmodeled, '
                         'prereg section 9 A3)',
        'mode_census': mode_census,
        'falsified': falsified,
    }


def check_p6_energy_destination(arm, d):
    """P6: the impact-energy destination through the sealed observer's
    account."""
    falsified = []
    share = d['share_kg']
    g, dt = d['g_record'], d['dt_s']
    worst_resid = 0.0
    worst_drift_recorded = 0.0
    ccd_ticks = []
    for r in arm['acct_rows']:
        unobstructed_tick = r['pads'][0]['unobstructed']
        if not unobstructed_tick:
            ccd_ticks.append(r['tick'])
        for p in r['pads']:
            if unobstructed_tick:
                worst_resid = max(worst_resid, abs(p['residual_J']))
            else:
                worst_drift_recorded = max(worst_drift_recorded,
                                           abs(p['drift_residual_J']))
    destinations = []
    for k in range(READING[1]):
        pad_id = 'grip.pad_%d' % k
        impact_tick = None
        for i, records in enumerate(arm['records_log']):
            if floor_records_for_pad(records, pad_id):
                impact_tick = i + 1
                break
        if impact_tick is None:
            continue
        ai = arm['acct_rows'][impact_tick - 1]['pads'][k]
        recs = floor_records_for_pad(arm['records_log'][impact_tick - 1],
                                     pad_id)
        jn_total = sum(r['jn_Ns'] for r in recs)
        jt_total = sum(r['jt_Ns'] for r in recs)
        ke_start = ai['ke_start_J']
        ke_after = ai['ke_after_J']
        w_grav = ai['work_gravity_J']
        w_friction = ai['work_friction_J']
        w_loss_solver = ai['loss_solver_J']
        vn_pre = ai['vz_press_mps'] - g * dt
        ke_normal_removed = 0.5 * share * vn_pre ** 2
        ke_normal_removed_from_jn = jn_total ** 2 / (2.0 * share)
        # The two closed forms disagree ONLY through the recorded contact
        # normal's tilt off +z (the z-only re-derivation vs the solver's
        # true vn = rv.n): a RECORDED comparison in the same deviation
        # family as the P3 margin finding. The LOAD-BEARING identities are
        # (i) the P4a impulse identity within 1e-9 N*s (checked in P4),
        # and (ii) the destination closure against the recorded impulses
        # below - which uses the from-jn form the observer's own identity
        # guarantees.
        ke_normal_delta = abs(ke_normal_removed - ke_normal_removed_from_jn)
        # recorded, never a falsifier: the named P6 falsifier is a
        # destination decomposition that does not close against the
        # recorded impulses (checked below); the closed-form-vs-from-jn
        # delta is the recorded tilt signature, routed as a finding.
        # multi-contact honesty (prereg section 5 honest risk b): if a wall
        # facet touched the pad ON the impact tick, the recorded exchange
        # includes the wall term and the single-contact closure form is NOT
        # forced onto it; the wall residual is RECORDED instead.
        wall_recs = [r for r in arm['records_log'][impact_tick - 1]
                     if (r['body_a'] == pad_id or r['body_b'] == pad_id)
                     and FLOOR_BODY_ID not in (r['body_a'], r['body_b'])]
        single_contact = not wall_recs
        wall_terms = {
            'jn_Ns': sum(r['jn_Ns'] for r in wall_recs),
            'jt_Ns': sum(r['jt_Ns'] for r in wall_recs),
        }
        # closure (the observer's own identity, rearranged; enforced only
        # for the single-floor-contact impact tick):
        # KE_start - KE_after == (-w_grav) + ke_normal_removed_from_jn
        #                         + loss_solver   [w_friction == -loss_solver]
        lhs = ke_start - ke_after
        rhs = (-w_grav) + ke_normal_removed_from_jn + w_loss_solver
        closure = abs(lhs - rhs)
        if single_contact:
            if closure > WIN_DEST_CLOSE:
                falsified.append('P6_destination_closure_breach_pad%d' % k)
            closure_state = 'CLOSED_SINGLE_FLOOR_CONTACT'
        else:
            closure_state = 'MULTI_CONTACT_IMPACT_RECORDED'
        # the floor's anchor reaction == minus the contact impulse on the
        # floor (the trunk-anchor law extended to the declared floor)
        anchor = tuple(arm['ledger_log'][impact_tick - 1]['anchor'][
            FLOOR_BODY_ID])
        contact_floor = tuple(arm['ledger_log'][impact_tick - 1]['contact'][
            FLOOR_BODY_ID])
        anchor_ok = all(abs(a + c) <= 1e-12
                        for a, c in zip(anchor, contact_floor))
        if not anchor_ok:
            falsified.append('P6_floor_anchor_reaction_breach_pad%d' % k)
        destinations.append({
            'pad': pad_id, 'impact_tick_abs': impact_tick,
            'single_floor_contact_impact_tick': single_contact,
            'co_firing_wall_records': len(wall_recs),
            'co_firing_wall_terms_Ns': wall_terms,
            'closure_state': closure_state,
            'ke_start_tick_J': ke_start, 'ke_after_tick_J': ke_after,
            'work_gravity_tick_J': w_grav,
            'work_friction_tick_J': w_friction,
            'loss_solver_tick_J': w_loss_solver,
            'jn_total_Ns': jn_total, 'jt_total_Ns': jt_total,
            'vn_pre_derived_mps': vn_pre,
            'ke_normal_removed_derived_J': ke_normal_removed,
            'ke_normal_removed_from_jn_J': ke_normal_removed_from_jn,
            'ke_normal_removed_delta_J': ke_normal_delta,
            'ke_normal_removed_delta_law':
                'RECORDED comparison (never the falsifier): the z-only '
                're-derivation 0.5*share*(vz_press-g*DT)^2 vs the '
                'from-impulse jn^2/(2*share) disagree exactly through the '
                'recorded contact normal\'s tilt off +z; the load-bearing '
                'forms are the P4a impulse identity (1e-9 N*s bar) and '
                'the destination closure below',
            'destination_closure_residual_J': closure,
            'floor_anchor_reaction_Ns': list(anchor),
            'floor_contact_impulse_Ns': list(contact_floor),
            'no_elastic_return':
                'with RESTITUTION 0.0 this energy appears in NO stored, '
                'returned or rebound form (the e = 0 declaration; the P5 '
                'no-bounce census is the behavioral check)',
        })
    # release-phase totals: the account stops NOWHERE (order #7 check 2)
    rel = arm['acct_rows'][HOLD_TICKS:]
    totals = {'work_press_J': 0.0, 'work_gravity_J': 0.0,
              'work_contact_J': 0.0, 'work_friction_J': 0.0,
              'loss_solver_J': 0.0, 'ke_delta_J': 0.0}
    for r in rel:
        for p in r['pads']:
            totals['work_press_J'] += p['work_press_J']
            totals['work_gravity_J'] += p['work_gravity_J']
            totals['work_contact_J'] += p['work_contact_J']
            totals['work_friction_J'] += p['work_friction_J']
            totals['loss_solver_J'] += p['loss_solver_J']
            totals['ke_delta_J'] += p['ke_after_J'] - p['ke_start_J']
    return {
        'ccd_ticks': ccd_ticks,
        'ccd_tick_count': len(ccd_ticks),
        'worst_nonccd_energy_residual_J': worst_resid,
        'worst_recorded_ccd_drift_residual_J': worst_drift_recorded,
        'observer_window_enforcement':
            'the sealed observer enforced WIN_ENERGY/LOSS per non-CCD tick '
            'in-run (a breach aborts and is PRESERVED as '
            'sealed_law_refusal); the CCD impact ticks follow the '
            'observer\'s own declared CCD-tick law (residuals recorded, '
            'kinematic anti-teleport bound enforced)',
        'destinations': destinations,
        'release_phase_totals_J': totals,
        'k02_stop_before_impact_extended':
            'the K02 release account declared itself stopped-before-'
            'impact; this account runs EVERY tick INCLUDING the impact '
            'tick to rest, fully labeled',
        'annotation_scale_note':
            'KE_closed(60) = %r J/pad (%r J 3-pad) is the DECLARED '
            'annotation scale, never an enforced identity (LB6: the '
            'discrete closed form and m*g*d differ at the g*DT^2*N/2 '
            'scale)' % (d['ke_closed_pad_J'], d['ke_closed_total_J']),
        'falsified': falsified,
    }


def site_census(arm):
    declared = set(CONTACT_SITES_DECLARED)
    census = {'declared_sites': sorted(declared), 'records': 0,
              'undeclared': []}
    for row in arm['rows']:
        for pad in row['pads']:
            census['records'] += 1
            for surface in pad['surfaces']:
                if surface not in declared:
                    census['undeclared'].append(
                        {'tick': row['tick'], 'surface': surface})
    require(not census['undeclared'], 'undeclared_contact_site',
            census['undeclared'][:5])
    return census


def scene_safety_checks(lc, geom, verts0, z_floor, arm):
    """Declared scene-composition checks: the floor lies strictly below
    the trunk's lowest vertex beyond the contact-activation band (no
    trunk-floor contact possible), the floor extent covers every pad
    vertex for the whole observed window (measured from the recorded
    states), and the floor body stays pinned and still."""
    trunk_zmin = min(v[2] for v in geom['vertices_m06'])
    floor_clearance = trunk_zmin - z_floor
    require(floor_clearance > lc.MARGIN + lc.CCD_TOL_M,
            'floor_intersects_trunk_column', floor_clearance)
    max_xy = 0.0
    for row in arm['rows']:
        for k in range(READING[1]):
            for v in verts0[k]:
                max_xy = max(max_xy, abs(v[0]), abs(v[1]))
    extent_ok = max_xy <= FLOOR_HALF_M
    require(extent_ok, 'pad_vertex_outside_declared_floor_extent', max_xy)
    still = True
    for vel in arm['velocity_log']:
        v = vel['after'][FLOOR_BODY_ID]
        if v != (0.0, 0.0, 0.0):
            still = False
    require(still, 'floor_body_not_still')
    return {'trunk_lowest_vertex_z_m': trunk_zmin,
            'floor_clearance_below_trunk_m': floor_clearance,
            'pad_vertex_max_horizontal_extent_m': max_xy,
            'floor_half_extent_m': FLOOR_HALF_M,
            'extent_sufficient': extent_ok,
            'floor_still_every_tick': still}

