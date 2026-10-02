"""K02-STATIC-HOLD-20261002 physics battery (PREREGISTRATION.md, frozen at
commit 19d0cff806969ac2ae4bf485576006c8c4091ade, committed bytes sha256
40cb161d7386cc0c46ea0a15cd3d001c364e8bbd5ee4dc6f5d91df71a021814b).

Executes the preregistered K02 experiment at the pin (the goal's hold +
release behaviors at the declared parameters, on the certified n=3 fixture
contact line K01 measured):

- P1 HOLD PERSISTENCE ``hold_persists_all_declared_windows_placeholder``:
  stick persistence of the certified n=3 fixture line across the declared
  windows W20/W100/W300 (20/100/300 ticks at DT=0.005 s; seconds are
  ANNOTATION computed from the frozen tick counts) at placeholder
  mu=0.6/0.4; per-channel stick class per tick; per-channel press
  jn = 0.3 N*s within the 1e-9 N*s bar every press tick; per-channel
  cumulative hold creep recorded per window. HONEST FAILURE MODE (THE
  FALSIFIER): a non-stick tick in any channel inside any declared window at
  placeholder mu - recorded (creep-driven contact break on the longest
  windows is a recorded persistence boundary, NEVER tuned), with the slip
  recursion as the named discriminator.
- P2 LOAD PATH ``load_path_within_declared_ceiling``: thresholds re-derived
  at run from the pinned bytes and value-matched (mismatch = refusal
  ``threshold_pin_mismatch``): P_req std-g 54.68840727038889 N (rec-g
  54.70708910000001) <= 60.0 N declared press; margin 5.311592729611107 N;
  closure thresholds mu >= 0.5468840727038888 std-g / 0.5470708910000001
  rec-g, both INSIDE the declared F-A band [0.3, 1.0]; per-channel friction
  limit 36.0 N rec-g / 35.98770642201834 N std-g vs per-channel weight share
  32.81304436223334 N std-g; boundary agreement solver-vs-closed-form-vs-B4
  on the declared comparison arms (W20 placeholder stick, 0.41 slip).
- P3 HOLD ENERGY/IMPULSE LEDGER ``hold_energy_ledger_closes``: in EVERY
  declared window at placeholder mu: (a) IDENTITY gravity work ==
  friction losses within the declared 1e-9 J cross-window gate; (b)
  REFERENCE the W20 window reproduces the pinned G07 scene|n=3 ledger
  (press 0.8069338128977511 J / gravity 0.24150444483195008 J / friction
  0.24150444482831965 J) within 1e-9 J; (c) RATE the W100/W300 per-tick
  press rate stays within the DECLARED 1% band of the measured W20
  reference rate (G07-pinned 0.040346690644887555 J/tick); impulse ledger
  per channel: jn = 0.3 N*s/tick inside the same 1e-9 bar, window press
  impulse = ticks x 0.3 x 3 channels.
- P4 RELEASE-TO-GROUND ``release_free_fall_identity``: release from the
  held (stick) state, the G07 structure (20 hold + 40 release ticks):
  W_press == 0.0 J EXACTLY every release tick; jn/jt fall to the
  share-scaled noise bar (1e-10 N*s/kg); free-fall recursion
  v(k)-v(k-1) == g*DT within 1e-9 m/s; gravity work == KE gain within
  1e-9 J; terminal speed == 40*g_rec*DT within 1e-9 m/s; fall displacement
  vs the G07-sealed same-class reading 0.20110499999871972 m within 1e-9 m;
  every post-release contact event RECORDED (tick, site, jn/jt) with the
  G07 law that CCD facet contacts are recorded, NEVER support. HONEST-ABSENT:
  NO impact/landing model exists; post-contact dynamics UNDECIDABLE.
- P5 THE DECLARED PARAMETER ARM ``mu041_hold_nonclose_slip_recursion``:
  at the DECLARED SCENARIO PARAMETER mu=0.41 (labeled on every use:
  human-analogue transfer, NOT monkey-bark, UNMEASURED): PREDICTED
  NON-CLOSE - all three channels slip, the slip recursion is the named
  failure discriminator (K01-sealed dv 0.012289681856880237 m/s per tick,
  K01-class window displacement). OBSERVING THE SLIP SUPPORTS P5. THE
  FALSIFIER: a sustained static hold at 0.41 (a records discrepancy, never
  a win). Completes the SUSTAIN diagnostic; the playable hold objective
  stays open (prereg section 0.3 objective law).
- P6 FENCED ``transfer_and_n4_fenced_not_run``: NO transfer phase and NO
  n=4 shape run; the B5 scene-line bound 0.24618190095000003 > 0.18 N*s at
  n=3 (and at 0.41 band_lo n=3 0.13243500000000002 > 0.12299999999999998)
  is recorded as the reason, never misread as a hold/contact/release
  refusal.

REFINEMENT CHECKS: every threshold is DERIVED AT RUN from hash-asserted
pinned bytes (no hand-copied constants); derived values are additionally
value-matched against the numeric tokens of the pinned corpus bytes
(mismatch = refusal ``threshold_pin_mismatch``). The five RETRACTED
defective static quotes are re-derived arithmetically and asserted ABSENT
from every emitted receipt byte.

Interfaces, imported at run time, hash-asserted, never forked: the solver
MAT2-M06 ``chimera.local_contact.v1``; the grip physics + fixture MAT2-G04
``grip_contact.py`` (PR #298 revision); the observation seam MAT2-G05
``contact_support_obs.py`` (PR #300 revision); the G07 sealed account
observer ``release_fall_account.py`` (evidence-store sealed bytes) whose
``observe_with_account`` builds the exact discrete energy ledger. Captures
run through the embedded standing capture-gate template (capture_card/,
byte-identical per TEMPLATE_MANIFEST.json); the card view-spec hash was
pinned in card_prereg.json BEFORE capture.

MERGED-TIP BASIS (prereg section 1 build line): the implementation base is
the committed prereg commit 19d0cff8 (its tree = the merged K01 tip
d100e87c tree PLUS the committed K02 prereg file alone, verified at
dispatch: ``git diff --stat d100e87c 19d0cff8`` lists exactly the one
prereg file). The package files are materialized from that base by the
sealed create(); every git-tree pin below is the merged line's content
hash; CHIMERA_BASE_SHA must equal BASE_SHA. The merged tip commit hash is
recorded as MERGED_TIP and verified transitively by this pin set - a
cached ref is never claimed as remote freshness.

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
sys.path.insert(0, str(HERE))

SCHEMA = 'chimera.k02_battery.v1'
TRACE_SCHEMA = 'chimera.k02_trace.v1'

PREREG_COMMIT = '19d0cff806969ac2ae4bf485576006c8c4091ade'
PREREG_SHA256 = ('40cb161d7386cc0c46ea0a15cd3d001c364e8bbd5ee4dc6f5d91df71a'
                 '021814b')
BASE_SHA = PREREG_COMMIT
MERGED_TIP = 'd100e87c67dfbbd34f5eac41a271fca094bd2639'
MERGED_TIP_NOTE = (
    'the base commit 19d0cff8 is the committed K02 prereg ALONE on top of '
    'the merged K01 tip d100e87c (PR #315); the publisher refreshed '
    'origin/review/K02-STATIC-HOLD-20261002 to 19d0cff8 and the merged tip '
    'is in the local object database (verified at dispatch: rev-parse of '
    'the pin and of its parent; git diff d100e87c..19d0cff8 = the one '
    'prereg file). The package inputs are materialized from that base by '
    'the sealed create(); the git-tree pins below are the merged line '
    'content hashes; CHIMERA_BASE_SHA is asserted == BASE_SHA. A cached '
    'ref is not a claim of remote freshness (NO_WORKTREES build line).')

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

# ---- host pins (the K02 frozen prereg section 7 pins, verified 2026-10-02)
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
    'E:/PythonChimera/tools/monkey_campaign/MONKEY_COMPLETION_MAP.md':
        '0e3984578b0cae38ab435daaa77cc10559cceeadbaf9885c3f31b979a362ecae',
    HOST_ROOT + 'evidence-store/MAT2-G01/report/REPORT.md':
        'e6d6c432680e503d5a70a1903ed59b52d5044cb8d3c7934da3b0db8acf3293a9',
    HOST_ROOT + 'evidence-store/MAT2-G07/numerical/experiment_receipt.json':
        'c539617b098190918187d9a7dcbb0a5e33a85998adaa58f6b781703bbdeb88f8',
    HOST_ROOT + 'evidence-store/MAT2-G07/report/REPORT.md':
        '34a4a095e1f4b3e5c87160a77e399c5c27a38202c1ad3675b0bcbf70d4b956a1',
    HOST_ROOT + 'evidence-store/MAT2-G07/source/release_fall_account.py':
        '78b5cc66f7019fa181765eb0366fe6c98525941840f57723d0ae99cb55b2a8c5',
    HOST_ROOT + 'evidence-store/MAT2-F05/source/FRICTION_SOURCES.md':
        '336118e929bd0b4fb067db5a448dc2e348fed073007787635549a4cf1cf5868b',
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
    HOST_ROOT + 'capture-gate-template/README.md':
        '331939f3156ca6158956e53c557cc324a3eeb0aa6a381b5170ec5ea83175ddb6',
    HOST_ROOT + 'capture-gate-template/TEMPLATE_MANIFEST.json':
        '1c4d1dcad9af98c73e1aa4ebb46bff6359b9992e390b38c37fae578e779a59a7',
    # K01 sealed receipts (the measurement authority consumed by this card)
    'E:/ChimeraWork/task-runner/results/'
    '97f2145b45cb4f99a8073a772f4092bf/receipt.json':
        'f0af6968cf9f063062a20536bb4de3460382c92e66dc1654f5b7b4396c7efbc1',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/k01_experiment_receipt.json':
        'ee1b26fc8e3eda1f2a95f75806cb1caed44805aa8787698e92f09bad69304dd5',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/k01_trace.json':
        '2f342339863e41f9ce8a8b1d11e34740827442dfaa1b88c3942d85260739dc45',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/determinism_receipt.json':
        'db5a74a99d0c4fd2de1a39bf2e8f0d97cdb2f2652cad0b8be767af5e354c8c81',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/capture_summary.json':
        '78620b8de478d2ab96435e663b69fae39704a6f1e40c8c4f25b3af0a8eb2c726',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/named_checks_receipt.json':
        'faeeaab9424a1348b918ee200c3038b204cd4f7c725cac503914d405bda3253a',
    'E:/ChimeraWork/task-runner/results/97f2145b45cb4f99a8073a772f4092bf/'
    'artifacts/outputs/regression_receipt.json':
        '20bc18b0c83866f3455f73b8288b76a6cd3f1cd0eec2f2b1dfbc1c7634e48c56',
}

K01_RESULTS = ('E:/ChimeraWork/task-runner/results/'
               '97f2145b45cb4f99a8073a772f4092bf/artifacts/outputs/')
K01_RECEIPT_REL = K01_RESULTS + 'k01_experiment_receipt.json'

# ---- frozen windows (K02 prereg sections 1/10; the G07/K01 precedents) ---
HOLD_W20_TICKS = 20    # the K01/G07 20-tick reference window (0.1 s)
HOLD_W100_TICKS = 100  # (0.5 s)
HOLD_W300_TICKS = 300  # (1.5 s); the declared longest window
MU041_TICKS = 20       # the declared-parameter diagnostic arm (K01
#                       comparability window)
RELEASE_HOLD_TICKS = 20   # the G07 release structure: hold 20
RELEASE_FALL_TICKS = 40   # + release 40 (0.2 s)
DECLARED_WINDOWS = (('W20', HOLD_W20_TICKS), ('W100', HOLD_W100_TICKS),
                    ('W300', HOLD_W300_TICKS))
READING_N = ('scene', 3)   # the certified n=3 line
MU_PLACEHOLDER_S = None    # taken from pinned modules (0.6), never
MU_PLACEHOLDER_K = None    # hand-copied here (set in derive()).
MU_SCENARIO = 0.41         # THE DECLARED SCENARIO PARAMETER (prereg
#   section 3: human-analogue transfer value, Gerhardt et al. 2008
#   natural-dry volar forearm on textile; NOT monkey-bark; UNMEASURED;
#   single-coefficient reading: mu_s = mu_k = 0.41, declared BEFORE run).

# ---- declared tolerance windows (frozen before the run) ------------------
WIN_JN = 1e-9             # N*s, jn == P per channel-tick (K01 precedent)
WIN_RECURSION_V = 1e-9    # m/s, slip/free-fall velocity recursion (sealed)
WIN_DISP = 1e-9           # m, displacement windows (sealed)
WIN_RELEASE_SCALE = 1e-10  # N*s per kg (sealed G07/K01 release bar)
WIN_ENERGY_IDENTITY = 1e-9   # J, K02 declared cross-window ledger gate
WIN_G07_REFERENCE = 1e-9     # J, W20 vs pinned G07 ledger reference
WIN_G07_FALL = 1e-9          # m, release fall vs G07 same-class reading
WIN_RATE_BAND = 0.01         # declared 1% press-rate persistence band
WIN_K01_CLASS = 1e-9         # m / m/s, K01-sealed 0.41-arm class match
WIN_TOKEN = 1e-12            # relative, derived-vs-pinned float form match

CONTACT_SITES_DECLARED = ('trunk_01.lateral', 'grip.pad_0', 'grip.pad_1',
                          'grip.pad_2')


class K02Refusal(ValueError):
    """Named harness refusal; receipts still written (exit 4)."""


def require(ok, code, detail=''):
    if not ok:
        raise K02Refusal(code + (': ' + str(detail) if detail != '' else ''))


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

def verify_template_manifest():
    """Assert every embedded capture-template file against the manifest
    (template modules are never forked or edited)."""
    manifest = json.loads((HERE / 'capture_card/TEMPLATE_MANIFEST.json')
                          .read_bytes().decode('utf-8'))
    rows = []
    for rel, expect in sorted(manifest['files'].items()):
        path = HERE / 'capture_card' / rel
        if not path.exists():
            raise K02Refusal('template_pin_missing:' + rel)
        got = sha256_file(path)
        require(got == expect, 'template_pin_drift:' + rel, got)
        rows.append({'path': 'capture_card/' + rel, 'sha256': got,
                     'class': 'template_manifest'})
    return rows


def verify_pins():
    """Assert every git-tree and host pin by sha256. Refusals:
    input_pin_missing / input_pin_drift."""
    rows = []
    for rel, expect in sorted(GIT_PINS.items()):
        path = (HERE / rel).resolve()
        if not path.exists():
            raise K02Refusal('input_pin_missing:' + str(path))
        got = sha256_file(path)
        require(got == expect, 'input_pin_drift:' + str(path), got)
        rows.append({'path': rel, 'sha256': got, 'class': 'git_tree'})
    for path, expect in sorted(HOST_PINS.items()):
        p = pathlib.Path(path)
        if not p.exists():
            raise K02Refusal('input_pin_missing:' + path)
        got = sha256_file(p)
        require(got == expect, 'input_pin_drift:' + path, got)
        rows.append({'path': path, 'sha256': got, 'class': 'host_lane'})
    base = os.environ.get('CHIMERA_BASE_SHA')
    require(base in (None, BASE_SHA), 'base_sha_env_mismatch', str(base))
    return rows


def load_pinned_module(rel, expected_sha, name):
    path = (HERE / rel).resolve()
    if not path.exists():
        raise K02Refusal('interface_pin_missing:' + str(path))
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise K02Refusal('interface_pin_drift:' + got)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_pinned_host_module(path_str, expected_sha, name):
    """Import a pinned HOST lane module (absolute path, hash-asserted)."""
    path = pathlib.Path(path_str)
    if not path.exists():
        raise K02Refusal('interface_pin_missing:' + path_str)
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    if got != expected_sha:
        raise K02Refusal('interface_pin_drift:' + got)
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
        raise K02Refusal('interface_pin_drift:' + got)
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


def load_pinned_json(path_str, expected_sha):
    path = pathlib.Path(path_str)
    require(path.exists(), 'input_pin_missing:' + path_str)
    raw = path.read_bytes()
    got = sha256_bytes(raw)
    require(got == expected_sha, 'input_pin_drift:' + path_str, got)
    return json.loads(raw.decode('utf-8'))


def g07_scene_n3_ledger(g07_receipt):
    """The pinned G07 scene|n=3 hold/release ledger, read at the exact key
    paths of the sealed receipt (never hand-copied)."""
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
        'windows': g07_receipt['measurement']['windows'],
        'g_mps2': g07_receipt['measurement']['g_mps2'],
        'dt_s': g07_receipt['measurement']['dt_s'],
    }


def k01_authority(k01_receipt):
    """The pinned K01 sealed measurements this card consumes (JSON-exact
    extraction from the hash-pinned K01 receipt)."""
    ac = k01_receipt['arm_checks']
    p5 = k01_receipt['verdicts'][
        'P5_scene_n3_hold_closes_at_placeholder']['evidence']
    return {
        'k01_base_sha': k01_receipt['base_sha'],
        'k01_preregistration_sha256': k01_receipt['preregistration_sha256'],
        'slip_dv_per_tick_mps':
            ac['hold_mu041']['slip_recursion']['dv_per_tick_mps'],
        'slip_worst_v_residual_mps':
            ac['hold_mu041']['slip_recursion']['worst_v_residual_mps'],
        'slip_worst_disp_residual_m':
            ac['hold_mu041']['slip_recursion']['worst_disp_residual_m'],
        'slip_measured_disp_down_m':
            list(p5['mu_0_41_declared_scenario_parameter'][
                'measured_disp_down_m']),
        'hold06_press_worst_Ns': p5['mu_0_6']['press_worst_Ns'],
        'zero_mu_disp_hold_measured_m':
            list(ac['zero_mu_control']['disp_hold_measured_m']),
        'zero_mu_release': ac['zero_mu_control']['release'],
    }


def derive(cd, gg, lc, gc, g07_ledger, k01_auth, massreg):
    """Every quoted threshold, derived at run from pinned bytes/records."""
    d = {}
    d['dt_s'] = lc.DT
    d['g_record'] = lc.G
    d['g_standard'] = cd.G_STD
    d['cadence_hz'] = 1.0 / lc.DT
    d['mu_placeholder_s'] = cd.MU_S
    d['mu_placeholder_k'] = cd.MU_K
    d['mu_scenario_declared'] = MU_SCENARIO
    d['jn_press_ns'] = cd.JN
    d['press_n'] = cd.JN / cd.DT
    d['m_scene_kg'] = cd.M_SCENE
    d['band_kg'] = dict(cd.M_BAND)
    d['trunk_radius_m'] = gg.TRUNK_R
    d['trunk_diameter_m'] = gg.TRUNK_D
    d['fa_band'] = list(cd.F_A_BAND)
    d['reach_envelope_m'] = cd.REACH_ENVELOPE

    press = cd.JN / cd.DT   # 60.0 N declared fixture press (jn/DT)

    # P2: the static law (scene n=3 at the placeholder), dual arithmetic
    d['p_req_scene_n3_std_N'] = (cd.M_SCENE * cd.G_STD) / (3 * cd.MU_S)
    d['p_req_scene_n3_rec_N'] = (cd.M_SCENE * lc.G) / (3 * cd.MU_S)
    d['hold_margin_std_N'] = press - d['p_req_scene_n3_std_N']
    d['mu_crit_scene_n3_std'] = (cd.M_SCENE * cd.G_STD) / (3 * press)
    d['mu_crit_scene_n3_rec'] = (cd.M_SCENE * lc.G) / (3 * press)
    d['mu_crit_inside_fa_band'] = bool(
        cd.F_A_BAND[0] <= d['mu_crit_scene_n3_std'] <= cd.F_A_BAND[1]
        and cd.F_A_BAND[0] <= d['mu_crit_scene_n3_rec'] <= cd.F_A_BAND[1])
    # per-channel friction limit at the operating point vs weight share
    d['friction_limit_rec_N'] = cd.MU_S * press
    d['friction_limit_std_N'] = cd.MU_S * press * (cd.G_STD / lc.G)
    # the certified weight line: mass register builder sum -> weight ->
    # per-channel share (the RUNTIME_CONTRACT-declared chain)
    builder_sum_kg = massreg['totals']['builder_order_sum_kg']['value']
    d['builder_order_sum_kg'] = builder_sum_kg
    d['weight_N_std'] = builder_sum_kg * cd.G_STD
    d['weight_share_std_N'] = d['weight_N_std'] / 3
    d['weight_share_rec_N'] = (builder_sum_kg * lc.G) / 3
    d['load_path_holds'] = bool(
        d['p_req_scene_n3_std_N'] <= press
        and d['p_req_scene_n3_rec_N'] <= press
        and d['friction_limit_rec_N'] > d['weight_share_rec_N']
        and d['friction_limit_std_N'] > d['weight_share_std_N'])

    # P6 fence arithmetic (recorded; nothing transfer-shaped runs)
    def transfer_req(m, n):
        return (m / (n - 1)) * lc.G * lc.DT

    d['cap_ns_placeholder'] = cd.MU_S * cd.JN
    d['transfer_req_scene_n3_ns'] = transfer_req(cd.M_SCENE, 3)
    d['transfer_req_scene_n2_ns'] = transfer_req(cd.M_SCENE, 2)
    d['transfer_req_band_lo_n3_ns'] = transfer_req(cd.M_BAND['band_lo'], 3)
    d['cap_ns_at_scenario_mu'] = MU_SCENARIO * cd.JN

    # the five RETRACTED defective static quotes, re-derived arithmetically
    # from the sealed constants (DERIVATION section 7 retraction). Their
    # VALUES must not appear in any emitted artifact; only these arithmetic
    # forms exist here, and the receipts assert their absence.
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

    # the pinned G07 scene|n=3 reference (read from the sealed receipt) and
    # the derived annotations whose tokens are value-matched to the corpus
    d['g07_reference'] = {
        'source_schema': 'chimera.g07_release_fall_receipt.v1',
        'hold_ticks': g07_ledger['hold_ticks'],
        'release_ticks': g07_ledger['release_ticks'],
        'w20_press_J': g07_ledger['hold_work_press_J'],
        'w20_gravity_J': g07_ledger['hold_work_gravity_J'],
        'w20_friction_J': g07_ledger['hold_loss_solver_J'],
        'w20_press_rate_J_per_tick':
            g07_ledger['hold_work_press_J'] / g07_ledger['hold_ticks'],
        'release_gravity_J': g07_ledger['release_work_gravity_J'],
        'release_ke_J': g07_ledger['release_ke_delta_J'],
        'release_press_J_exact_zero': g07_ledger['release_work_press_J'],
        'identity_delta_hold_J': abs(
            g07_ledger['hold_work_gravity_J']
            - g07_ledger['hold_loss_solver_J']),
        'g_record': g07_ledger['g_mps2'],
        'dt_s': g07_ledger['dt_s'],
        'terminal_mps_derived':
            g07_ledger['release_ticks'] * g07_ledger['g_mps2']
            * g07_ledger['dt_s'],
        'fall_closed_form_m':
            (g07_ledger['g_mps2'] * g07_ledger['dt_s'] ** 2
             * (g07_ledger['release_ticks']
                * (g07_ledger['release_ticks'] + 1) // 2)),
    }
    # G07-declared receipt windows (the reference's own tolerances)
    d['g07_receipt_windows'] = g07_ledger['windows']

    # the pinned K01 sealed 0.41-arm authority (JSON-exact extraction)
    d['k01_authority'] = k01_auth
    # the derived declared-parameter slip recursion (from pinned constants;
    # the K01-sealed form dv = g*DT - mu_k*P/m with P the per-tick press
    # IMPULSE and m the per-channel share)
    share = cd.M_SCENE / 3
    d['mu041_derived'] = {
        'share_kg': share,
        'dv_per_tick_mps':
            lc.G * lc.DT - MU_SCENARIO * cd.JN / share,
        'hold_ticks': MU041_TICKS,
    }
    # the zero-mu control closed form (K01 provenance anchor; the control
    # arm itself is NOT re-run by this card - K01 owns that measurement)
    d['zero_mu_provenance'] = {
        'closed_form_20t_m': lc.G * (lc.DT ** 2) * (20 * 21 / 2),
        'k01_measured_m': k01_auth['zero_mu_disp_hold_measured_m'],
    }
    return d


def annotations(d):
    """Seconds annotations computed FROM the frozen tick counts (the K01
    finding-1 class of annotation mismatch is declared impossible here)."""
    dt = d['dt_s']
    return {
        'w20_seconds': HOLD_W20_TICKS * dt,
        'w100_seconds': HOLD_W100_TICKS * dt,
        'w300_seconds': HOLD_W300_TICKS * dt,
        'mu041_seconds': MU041_TICKS * dt,
        'release_hold_seconds': RELEASE_HOLD_TICKS * dt,
        'release_fall_seconds': RELEASE_FALL_TICKS * dt,
        'cadence_hz': d['cadence_hz'],
    }


# ---------------------------------------------------------------------------
# the arms (through the sealed G07 account observer; rows cross-checked
# BIT-IDENTICAL against gc.run_scenario)
# ---------------------------------------------------------------------------

def run_window(rfa, g05, gc, lc, geom, scenario_id, trace, hold_ticks,
               release_ticks, mu_s, mu_k, press_ns):
    """One observed arm: the G07 account loop + the pinned-runner
    cross-check (rows BIT-IDENTICAL to gc.run_scenario, refusal
    observer_drift). Returns the arm record."""
    kwargs = dict(mu_s=mu_s, mu_k=mu_k, press_ns=press_ns,
                  hold_ticks=hold_ticks, release_ticks=release_ticks)
    reading_kg = dict(gc.READINGS_KG)[READING_N[0]]
    header, rows, acct_rows, centroids = rfa.observe_with_account(
        g05, gc, lc, geom, reading_kg, READING_N[1], scenario_id, **kwargs)
    header_ref, rows_ref = gc.run_scenario(
        lc, geom, reading_kg, READING_N[1], scenario_id=scenario_id,
        **kwargs)
    rfa.cross_check_rows(header, rows, header_ref, rows_ref, scenario_id)
    trace[scenario_id] = {'header': header, 'rows': rows,
                          'acct_rows': acct_rows, 'centroids': centroids,
                          'observer_cross_check':
                          'rows bit-identical to gc.run_scenario '
                          '(cross_check_rows; observer_drift law)'}
    share = reading_kg / READING_N[1]
    return {'header': header, 'rows': rows, 'acct_rows': acct_rows,
            'centroids': centroids, 'share_kg': share}


def phase_rows(rows, phase):
    """Keyed per-phase extractor (G07 pattern): refuses unknown/empty."""
    require(phase in ('hold', 'release'), 'unknown_phase:' + str(phase))
    out = [r for r in rows if r['phase'] == phase]
    require(out, 'empty_phase:' + str(phase))
    return out


def phase_acct(acct_rows, phase):
    require(phase in ('hold', 'release'), 'unknown_phase:' + str(phase))
    out = [r for r in acct_rows if r['phase'] == phase]
    require(out, 'empty_acct_phase:' + str(phase))
    return out


def window_ledger(acct_rows, phase):
    """The per-window energy/impulse ledger: summed per-pad per-tick works
    over the phase, from the recorded account rows (the G07 account
    construction), plus the identity closure and the press-impulse sum."""
    sel = phase_acct(acct_rows, phase)
    sums = {'work_press_J': 0.0, 'work_gravity_J': 0.0,
            'loss_solver_J': 0.0, 'work_friction_J': 0.0,
            'work_contact_J': 0.0, 'work_weld_J': 0.0,
            'ke_delta_J': 0.0}
    per_pad = None
    ticks = 0
    for r in sel:
        ticks += 1
        for p in r['pads']:
            for k in sums:
                key = {'loss_solver_J': 'loss_solver_J'}.get(k, k)
                if k == 'ke_delta_J':
                    sums[k] += p['ke_after_J'] - p['ke_start_J']
                else:
                    sums[k] += p[key]
            if per_pad is None:
                per_pad = {}
            per_pad[p['pad']] = per_pad.get(p['pad'], 0.0)
            per_pad[p['pad']] += p['work_press_J']
    identity_delta_J = abs(sums['work_gravity_J'] - sums['loss_solver_J'])
    return {'phase': phase, 'ticks': ticks, 'sums': sums,
            'press_per_pad_J': per_pad,
            'identity_gravity_minus_friction_J': identity_delta_J}


def stick_records(rows, ticks):
    """Per-channel stick/slip/no-contact census over the first ``ticks``
    hold ticks. RECORDS a placeholder-window break; never raises (the P1
    falsifier path is a recorded outcome, never a harness refusal)."""
    sel = phase_rows(rows, 'hold')
    require(len(sel) >= ticks, 'hold_window_short', len(sel))
    census = {'ticks_checked': ticks,
              'slip_ticks': [0] * 3, 'no_contact_ticks': [0] * 3,
              'stick_ticks': [0] * 3, 'first_break': None,
              'stick_all': True}
    for row in sel[:ticks]:
        for k, pad in enumerate(row['pads'][:3]):
            mode = pad['mode']
            if mode == 'stick':
                census['stick_ticks'][k] += 1
            else:
                census['stick_all'] = False
                if mode == 'slip':
                    census['slip_ticks'][k] += 1
                else:
                    census['no_contact_ticks'][k] += 1
                if census['first_break'] is None:
                    census['first_break'] = {
                        'tick': row['tick'], 'channel': k, 'mode': mode,
                        'jn_sum_Ns': pad['jn_sum_Ns'],
                        'jt_sum_Ns': pad['jt_sum_Ns'],
                        'disp_down_m_cum': pad.get('disp_down_m_cum')}
    return census


def press_envelope(rows, press_ns, ticks, phase='hold'):
    """Worst |jn - P| per channel-tick over the first ``ticks`` ticks of
    the phase (RECORDED metric; enforcement is the verdicts' duty so a
    contact break is a recorded falsifier, never a harness refusal)."""
    sel = phase_rows(rows, phase)
    worst = 0.0
    for row in sel[:ticks]:
        for pad in row['pads']:
            worst = max(worst, abs(pad['jn_sum_Ns'] - press_ns))
    return worst


def window_press_impulse(rows, press_ns, ticks):
    """Per-window press impulse: recorded sum vs the exact arithmetic
    ticks x P x 3 channels, with the scaled per-channel-tick bar."""
    sel = phase_rows(rows, 'hold')
    recorded = 0.0
    for row in sel[:ticks]:
        for pad in row['pads']:
            recorded += pad['jn_sum_Ns']
    expected = ticks * press_ns * 3
    return {'recorded_Ns': recorded, 'expected_Ns': expected,
            'deviation_Ns': abs(recorded - expected),
            'bar_Ns': 3 * ticks * WIN_JN,
            'inside_bar': bool(abs(recorded - expected)
                               <= 3 * ticks * WIN_JN)}


def check_slip_recursion(rows, share, mu_k, press_ns, lc):
    """The slip recursion discriminator (K01-sealed form): vt_post(k) ==
    k*(g*DT - mu_k*P/m) from tick 1, disp_tick(k) == v(k)*DT after tick 1.
    Raises on a violation (this arm PREDICTS slip; the discriminator must
    close)."""
    g, dt = lc.G, lc.DT
    dv = g * dt - mu_k * press_ns / share
    worst_v = 0.0
    worst_d = 0.0
    sel = phase_rows(rows, 'hold')
    for k, row in enumerate(sel, start=1):
        for pad in row['pads']:
            require(pad['mode'] == 'slip', 'expected_slip_mode',
                    {'tick': row['tick'], 'mode': pad['mode']})
            worst_v = max(worst_v, abs(pad['vt_post_mps'] - k * dv))
            if k >= 2:
                worst_d = max(worst_d,
                              abs(pad['disp_tick_m'] - k * dv * dt))
    require(worst_v <= WIN_RECURSION_V, 'slip_recursion_violation', worst_v)
    require(worst_d <= WIN_DISP, 'disp_recursion_violation', worst_d)
    return {'dv_per_tick_mps': dv, 'worst_v_residual_mps': worst_v,
            'worst_disp_residual_m': worst_d}


def release_leg_checks(acct_rows, rows, share, lc):
    """P4: the release leg from the held state (G07 structure). Returns the
    recorded evidence; raises only on HARNESS-class violations (the account
    observer already enforced the per-tick identities). The support law:
    every post-release contact event is RECORDED and classified; a
    SUPPORTING event is the P4 falsifier (verdict path, never silent)."""
    g, dt = lc.G, lc.DT
    sel = phase_acct(acct_rows, 'release')
    rows_rel = phase_rows(rows, 'release')
    worst_j = 0.0
    zero_press_exact = True
    for r in sel:
        for p in r['pads']:
            if p['work_press_J'] != 0.0:
                zero_press_exact = False
            worst_j = max(worst_j, abs(p['work_press_J']))
    # recorded impulses per pad per tick (rows carry jn/jt sums). A
    # post-release contact EVENT is a pad-tick whose recorded impulse
    # EXCEEDS the share-scaled bar or whose mode is a contact mode;
    # sub-bar float noise is the G07 clean-release class (release_account
    # bars it) and is not an event.
    bar = share * WIN_RELEASE_SCALE
    worst_imp = 0.0
    ground_events = []
    for row in rows_rel:
        for pad in row['pads']:
            worst_imp = max(worst_imp, pad['jn_sum_Ns'], pad['jt_sum_Ns'])
            if pad['mode'] != 'no_contact' \
                    or pad['jn_sum_Ns'] > bar or pad['jt_sum_Ns'] > bar:
                ground_events.append({
                    'tick': row['tick'], 'site': pad['pad'],
                    'jn_sum_Ns': pad['jn_sum_Ns'],
                    'jt_sum_Ns': pad['jt_sum_Ns'],
                    'mode': pad['mode'], 'surfaces': pad['surfaces'],
                    'vt_post_mps': pad['vt_post_mps']})
    # free-fall velocity recursion on unobstructed release ticks, in the
    # G07 release_account convention: v_down = -vz grows by g*DT per tick
    worst_v = 0.0
    prev = None
    obstructed_ticks = []
    for i, r in enumerate(sel):
        for p in r['pads']:
            if not p['unobstructed']:
                obstructed_ticks.append({'tick': r['tick'],
                                         'pad': p['pad']})
        v_down = -max(p['vz_after_mps'] for p in r['pads'])
        if prev is not None:
            worst_v = max(worst_v, abs(v_down - prev - g * dt))
        prev = v_down
    # gravity work vs KE gain over the release phase (per pad, summed)
    w_grav = sum(p['work_gravity_J'] for r in sel for p in r['pads'])
    ke_gain = sum(p['ke_after_J'] - p['ke_start_J']
                  for r in sel for p in r['pads'])
    ke_identity_delta_J = abs(w_grav - ke_gain)
    # terminal speed vs 40*g*DT (magnitudes; vz is negative downward) and
    # the fall displacement
    last = sel[-1]
    v_term_down = max(-p['vz_after_mps'] for p in last['pads'])
    v_start_rec = max(-p['vz_start_mps'] for p in sel[0]['pads'])
    terminal_mps_derived = len(sel) * g * dt
    terminal_delta = abs(v_term_down - terminal_mps_derived)
    # fall displacement: per-pad centroid drop across the release phase,
    # from the recorded per-tick downward displacements
    fall_per_pad = [0.0] * 3
    for r in sel:
        for i, p in enumerate(r['pads']):
            fall_per_pad[i] += p['disp_down_tick_m']
    fall_measured_m = max(fall_per_pad)
    # a supporting post-release contact = the P4 falsifier (recorded; the
    # G07 law: CCD facet contacts are recorded, NEVER support)
    supporting = []
    for ev in ground_events:
        weight_tick_Ns = (share * g * dt)
        if ev['jn_sum_Ns'] > 0.9 * weight_tick_Ns:
            supporting.append(ev)
    return {
        'release_ticks': len(sel),
        'w_press_zero_exact_every_release_tick': zero_press_exact,
        'worst_abs_press_work_J': worst_j,
        'worst_release_impulse_Ns': worst_imp,
        'release_bar_Ns': share * WIN_RELEASE_SCALE,
        'impulses_inside_bar': bool(worst_imp <= share * WIN_RELEASE_SCALE),
        'freefall_worst_v_residual_mps': worst_v,
        'obstructed_release_ticks': obstructed_ticks,
        'gravity_work_J': w_grav,
        'ke_gain_J': ke_gain,
        'ke_identity_delta_J': ke_identity_delta_J,
        'release_start_vz_down_mps_recorded': v_start_rec,
        'terminal_v_down_mps_recorded': v_term_down,
        'terminal_mps_derived': terminal_mps_derived,
        'terminal_delta_mps': terminal_delta,
        'recording_conventions':
            'free-fall recursion on v_down = -vz (the G07 release_account '
            'convention); terminal speed compared by magnitude; a '
            'post-release contact EVENT is a pad-tick above the '
            'share-scaled bar (sub-bar float noise is the G07 '
            'clean-release class, barred by release_account)',
        'fall_per_pad_m': fall_per_pad,
        'fall_measured_m': fall_measured_m,
        'ground_contact_events': ground_events,
        'ground_contact_count': len(ground_events),
        'supporting_post_release_contacts': supporting,
        'impact_model': 'ABSENT (honest-absent; post-contact dynamics '
                        'UNDECIDABLE, prereg section 8 A3)',
    }


def check_stick_assertion_bites(rows, ticks):
    """The discriminator-bites selftest: asserting stick on a slipping
    trace must FAIL. Returns True iff the stick assertion refuses."""
    try:
        sel = phase_rows(rows, 'hold')
        for row in sel[:ticks]:
            for pad in row['pads'][:3]:
                require(pad['mode'] == 'stick', 'expected_stick_mode',
                        {'tick': row['tick'], 'mode': pad['mode']})
    except K02Refusal:
        return True
    return False


def initial_pad_verts(gc, geom, n):
    """Declared pad placement (pinned fixture builders), per channel."""
    facets = gc.channel_facets(geom, n)
    out = []
    for _ti, cen, nrm in facets:
        ey, ez = gc.orthobasis(nrm)
        origin = gc.vadd(cen, gc.vscale(nrm, gc.PAD_OFFSET_M))
        out.append([list(v) for v in gc.place_tetra(origin, nrm, ey, ez)])
    return out


def pad_verts_after(rows, verts0, disp):
    """Recorded-state pad vertex sets: pinned placement translated by the
    measured cumulative displacement (translation-only kinematics)."""
    out = []
    for k, verts in enumerate(verts0):
        out.append([[v[0], v[1], v[2] - disp[k]] for v in verts])
    return out


def final_disp(rows, n, phase='hold'):
    sel = phase_rows(rows, phase)
    return [p['disp_down_m_cum'] for p in sel[-1]['pads'][:n]]


def final_modes(rows, n, phase='hold'):
    sel = phase_rows(rows, phase)
    return [p['mode'] for p in sel[-1]['pads'][:n]]


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


def check_centroid_consistency(centroids, z0, disp, n, row_index=None):
    """Measured pad centroid z must equal z0 - disp at the SAME tick the
    disp was read from (translation-only kinematics, G05 field law)."""
    worst = 0.0
    idx = len(centroids) - 1 if row_index is None else row_index
    tick_centroids = centroids[idx]
    for k in range(n):
        measured = tick_centroids[k][2]
        expected = z0[k] - disp[k]
        worst = max(worst, abs(measured - expected))
    require(worst <= WIN_DISP, 'centroid_state_mismatch', worst)
    return worst
