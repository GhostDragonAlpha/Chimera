"""input_settings.py -- M-U04: supported input settings, persisted and refusing.

U04, verbatim (completion map line 106): "Sensitivity, inversion and bindings
needed for the selected controls work and persist." Constraint, verbatim:
"Keyboard/mouse baseline; controller support is an explicit product decision"
-- no controller support lives here.

THE SETTINGS MODEL (frozen in agents/U04_settings/PREREGISTRATION.md before
this build; the mapper file is READ-ONLY -- U01's, consumed, never edited):
  * bindings  -- physical input name -> action, exactly the mapper's own
    table shape (input_mapper.DEFAULT_BINDINGS / its constructor's
    `bindings=` parameter). Legal actions: the four selected controls
    (ACTIONS) plus U01's registered-refusal actions (sprint/jump), which stay
    legal to bind and refuse BY NAME at runtime.
  * sensitivity -- per axis over AXES = ("yaw",): rad/s of yaw demand per
    mouse count per 50 ms interval -- the mapper's own conversion
    (`_yaw_demand`: counts * sensitivity / INTERVAL_S). Range (0.0,
    SENS_YAW_MAX], with SENS_YAW_MAX = OMEGA_MAX_RAD_S * INTERVAL_MS / 1000
    = 0.08 DERIVED: one count in one interval exactly saturating the declared
    steer bound. Default = U01's frozen SENS_RAD_PER_COUNT = 0.002
    (imported, never redeclared). Movement has NO sensitivity: the walk
    demand is binary at the seam's frozen band ceiling -- a declared limit.
  * inversion -- per axis, booleans. invert.yaw negates the yaw DELTA scale
    (the applied mapper sensitivity becomes -sensitivity, per U01's
    integration note); it does NOT swap turn_left/turn_right keys -- a key
    swap is a REMAP, an ordinary data edit of the bindings table (values-only,
    measured by U01's F5).

THE PERSISTENCE CONTRACT (frozen): a versioned JSON file,
schema id "chimera.monkey_input.v1" (F01's chimera.<thing>.v<N> naming,
U01's integration-note suggestion), at a declared path. Atomic save: canonical
UTF-8 bytes -> temp file in the DESTINATION directory -> flush + fsync ->
os.replace (atomic rename); temp cleaned up on failure. Load is TOTAL and
refusing: every possible file content resolves to either (the declared
settings, status "loaded") or (U01's default settings + a NAMED refusal list)
-- never a partial accept, never a silent default, never a write from load.
Absent file = "first_run" defaults, nothing created. Corrupt JSON, duplicate
JSON keys anywhere (Python's json otherwise silently last-wins),
NaN/Infinity literals, unknown schema/version, unknown or missing keys, wrong
types (booleans are NOT numbers), unknown actions/axes, out-of-coverage or
out-of-range values: EACH refuses by machine code + human detail.

THE SEAM PROTECTION RULE (U01's note, structural here): settings values can
NEVER write the seam's own numbers. (1) The schema's key set is fixed -- a
file carrying "v_max_in_band_m_s", "omega_max_rad_s", "interval_ms",
"hold_ticks", ... arrives as an unknown key and refuses by name; (2) the
apply surface is only `mapper.bindings = dict(...)` and
`mapper.sensitivity = +-sensitivity` -- the mapper's own declared data
inputs (constructor parameters, input_mapper.py:174-182); no module attribute
of input_mapper or command_record is ever assigned; (3) the sensitivity
ceiling is DERIVED from the seam's numbers, so the setting exists only inside
the space the seam already bounds. A sensitivity of 100x scales INPUT deltas;
the band ceiling and steer bound are the mapper's own clamp, reused, never
bypassed.

Headless, CPU-only: no clock, no window, no engine import, no desktop input.
The mapper integration finding (for the coordinator, recorded in the
handoff notes): the mapper ALREADY exposes both hooks this module needs --
bindings-as-data and the delta-scale (`InputMapper.sensitivity`, consumed at
each boundary in `_yaw_demand`, input_mapper.py:325) -- so NO mapper addition
is required; the "delta-scaling hook" named in the brief IS
`InputMapper.sensitivity` itself.
"""
from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]                    # the repo/worktree root
for _p in (str(_ROOT), str(_HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# THE MAPPER'S OWN NUMBERS -- imported, never redeclared: a second copy of a
# frozen constant is exactly where a silent divergence lives (U01's own law,
# input_mapper.py:49-57; the seam's constants come via the mapper's re-exports).
import input_mapper as IM                   # noqa: E402

__all__ = [
    "InputSettings", "Refusal", "LoadResult", "SaveResult",
    "SCHEMA_ID", "AXES", "YAW", "SENS_YAW_MAX_RAD_PER_COUNT",
    "KNOWN_ACTIONS", "SELECTED_ACTIONS", "DEFAULT_SETTINGS_PATH",
    "default_settings", "load_settings", "save_settings",
    "apply_settings", "configured_mapper", "canonical_bytes",
]

SCHEMA_ID = "chimera.monkey_input.v1"       # F01's chimera.<thing>.v<N> naming

YAW = "yaw"
AXES = (YAW,)                # the ONLY continuous input axis in the keyboard/
                             # mouse baseline (mouse X). Movement is a binary
                             # demand at the seam's frozen band ceiling -- no
                             # movement sensitivity exists to expose (prereg).

# DERIVED, not tuned: the sensitivity at which ONE mouse count in ONE 50 ms
# interval exactly saturates the declared input-side steer bound. Above it the
# scale is degenerate (every count saturates); the mapper's clamp is the bound.
SENS_YAW_MAX_RAD_PER_COUNT = IM.OMEGA_MAX_RAD_S * IM.INTERVAL_MS / 1000.0

SELECTED_ACTIONS = tuple(IM.ACTIONS)          # forward/backward/turn_left/turn_right
KNOWN_ACTIONS = SELECTED_ACTIONS + tuple(IM.REFUSALS)  # + sprint/jump (refuse BY NAME)

DEFAULT_SETTINGS_PATH = (_HERE.parent / "data" / "settings"
                         / "monkey_input_settings.json")

_REQUIRED_KEYS = frozenset({"schema", "bindings", "sensitivity", "invert"})


# ── the settings object ──────────────────────────────────────────────────────
@dataclass(frozen=True)
class InputSettings:
    """One frozen settings vector: bindings + per-axis sensitivity + inversion.

    Equality is structural (dataclass): round-trip save->load must reproduce
    EXACTLY this object's values (F4). `bindings` is copied on construction
    so no caller can mutate a settings vector after the fact.
    """

    bindings: dict
    sensitivity: float
    invert_yaw: bool = False

    def __post_init__(self):
        object.__setattr__(self, "bindings", dict(self.bindings))

    def signed_sensitivity(self) -> float:
        """The yaw delta-scale the mapper actually consumes (the inversion)."""
        return -self.sensitivity if self.invert_yaw else self.sensitivity

    def to_document(self) -> dict:
        """The exact v1 document this settings vector saves as."""
        return {
            "schema": SCHEMA_ID,
            "bindings": dict(self.bindings),
            "sensitivity": {YAW: self.sensitivity},
            "invert": {YAW: bool(self.invert_yaw)},
        }


def default_settings() -> InputSettings:
    """U01's exact baseline: his bindings table (deep copy), his baseline
    sensitivity, no inversion. This is what first run gets and what every
    refusal falls back to -- NEVER a partial blend."""
    return InputSettings(bindings=dict(IM.DEFAULT_BINDINGS),
                         sensitivity=IM.SENS_RAD_PER_COUNT,
                         invert_yaw=False)


# ── named refusals (the parser's law: refuse BY NAME, never a silent zero) ───
@dataclass(frozen=True)
class Refusal:
    code: str        # machine-readable, one per offense class (see codes below)
    detail: str      # human-readable, names the offense


class _DuplicateKeyRefused(ValueError):
    """Raised inside json parsing: a duplicate object key would silently
    last-win (campaign prereg law: duplicate JSON keys are refused)."""

    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


class _NonFiniteRefused(ValueError):
    """Raised inside json parsing: a NaN/Infinity JSON extension literal.
    Non-finite numbers never parse (campaign prereg law)."""

    def __init__(self, token: str):
        super().__init__(token)
        self.token = token


def _pairs_refusing_duplicates(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise _DuplicateKeyRefused(key)
        seen[key] = value
    return seen


def _refuse_constant(token):
    raise _NonFiniteRefused(token)


# ── the refusing validator (total: any document -> settings or refusals) ─────
def _validate(document):
    """Validate an already-parsed JSON document against the frozen v1 schema.

    Returns (settings, refusals): refusals non-empty => settings is the
    DEFAULTS (never a partial accept). Every refusal names its offense.
    """
    refusals: list[Refusal] = []

    if not isinstance(document, dict):
        return default_settings(), [Refusal(
            "root_not_object",
            f"the settings document must be a JSON object, found "
            f"{type(document).__name__}")]

    # exact key set: missing AND unknown keys refuse by name. A file carrying
    # a seam constant's name ("v_max_in_band_m_s", "interval_ms", ...) is an
    # unknown key HERE -- this is layer (1) of the seam-protection rule.
    for key in sorted(_REQUIRED_KEYS - set(document)):
        refusals.append(Refusal("key_missing", f"required key {key!r} is missing"))
    for key in sorted(set(document) - _REQUIRED_KEYS):
        refusals.append(Refusal(
            "key_unknown",
            f"unknown key {key!r} -- the v1 schema refuses what it cannot "
            f"name (seam constants like 'v_max_in_band_m_s' or 'interval_ms' "
            f"are NOT settings and can never enter through this file)"))

    # schema id: exact string match, else named refusal (no silent migration;
    # R02 owns migration when an actual supported prior save requires it).
    schema = document.get("schema")
    if not isinstance(schema, str):
        refusals.append(Refusal(
            "schema_type",
            f"'schema' must be the string {SCHEMA_ID!r}, found "
            f"{type(schema).__name__}"))
    elif schema != SCHEMA_ID:
        refusals.append(Refusal(
            "schema_unknown",
            f"unknown schema {schema!r}; this loader opens exactly "
            f"{SCHEMA_ID!r} -- a newer/older schema refuses by name rather "
            f"than being silently accepted"))

    bindings, b_refusals = _validate_bindings(document.get("bindings"))
    refusals.extend(b_refusals)
    sensitivity, s_refusals = _validate_axis_number(
        document.get("sensitivity"), "sensitivity",
        low_exclusive=0.0, high_inclusive=SENS_YAW_MAX_RAD_PER_COUNT,
        range_detail=(f"0 < sensitivity.yaw <= {SENS_YAW_MAX_RAD_PER_COUNT!r} "
                      f"rad per count (derived: one count in one "
                      f"{IM.INTERVAL_MS} ms interval exactly saturating the "
                      f"{IM.OMEGA_MAX_RAD_S!r} rad/s steer bound); the default "
                      f"is U01's baseline {IM.SENS_RAD_PER_COUNT!r}"))
    refusals.extend(s_refusals)
    invert, i_refusals = _validate_axis_bool(document.get("invert"), "invert")
    refusals.extend(i_refusals)

    if refusals:
        return default_settings(), refusals
    return InputSettings(bindings=bindings, sensitivity=sensitivity,
                         invert_yaw=invert), []


def _validate_bindings(value):
    if not isinstance(value, dict):
        return None, [Refusal(
            "bindings_type",
            f"'bindings' must be a JSON object of physical-name -> action, "
            f"found {type(value).__name__}")]
    refusals = []
    clean: dict[str, str] = {}
    for name, action in value.items():
        if not isinstance(name, str) or not name:
            refusals.append(Refusal(
                "binding_name_invalid",
                f"binding physical names must be non-empty strings, found "
                f"{name!r}"))
            continue
        if not isinstance(action, str) or not action:
            refusals.append(Refusal(
                "binding_type",
                f"binding {name!r} must map to a non-empty action string, "
                f"found {action!r}"))
            continue
        if action not in KNOWN_ACTIONS:
            refusals.append(Refusal(
                "action_unknown",
                f"binding {name!r} -> unknown action {action!r}; the known "
                f"actions are {sorted(KNOWN_ACTIONS)} (the grammar refuses "
                f"what it cannot name, parser.py:130-132 precedent)"))
            continue
        clean[name] = action
    # COVERAGE (U04's own words): the four selected controls must WORK after
    # loading settings -- a file that leaves one with NO binding refuses.
    for action in SELECTED_ACTIONS:
        if not any(a == action for a in clean.values()):
            refusals.append(Refusal(
                "action_unbound",
                f"no physical input is bound to selected action {action!r} -- "
                f"the selected controls must work after settings load "
                f"(alias bindings are legal; a total absence is not)"))
    return (clean, refusals) if not refusals else (None, refusals)


def _validate_axis_number(value, key, *, low_exclusive, high_inclusive,
                          range_detail):
    if not isinstance(value, dict):
        return None, [Refusal(
            f"{key}_type",
            f"{key!r} must be a per-axis JSON object keyed by axis "
            f"({sorted(AXES)}), found {type(value).__name__}")]
    refusals = []
    for axis in sorted(set(value) - set(AXES)):
        refusals.append(Refusal(
            "axis_unknown",
            f"{key!r} names unknown axis {axis!r}; the keyboard/mouse "
            f"baseline declares exactly the axes {sorted(AXES)} -- a newer "
            f"schema adds axes by a new prereg, never silently"))
    if YAW not in value:
        refusals.append(Refusal(
            "axis_missing",
            f"{key!r} must declare the {YAW!r} axis (the only continuous "
            f"input axis in the keyboard/mouse baseline)"))
        return None, refusals
    raw = value[YAW]
    if isinstance(raw, bool):                 # bool IS an int in Python --
        refusals.append(Refusal(              # refuse it explicitly
            f"{key}_type",
            f"{key}.yaw must be a JSON number, found boolean {raw!r} "
            f"(booleans are not numbers)"))
    elif not isinstance(raw, (int, float)):
        refusals.append(Refusal(
            f"{key}_type",
            f"{key}.yaw must be a JSON number, found "
            f"{type(raw).__name__} {raw!r}"))
    else:
        x = float(raw)
        if not math.isfinite(x):              # e.g. JSON "1e400" -> inf
            refusals.append(Refusal(
                "value_not_finite",
                f"{key}.yaw must be finite, found {raw!r} (NaN/Infinity are "
                f"refused at the lexer and by magnitude)"))
        elif not (low_exclusive < x <= high_inclusive):
            refusals.append(Refusal(
                "value_out_of_range",
                f"{key}.yaw = {raw!r} is outside the declared range "
                f"[{range_detail}]"))
            return None, refusals
        elif not refusals:
            return x, []
    return None, refusals


def _validate_axis_bool(value, key):
    if not isinstance(value, dict):
        return None, [Refusal(
            f"{key}_type",
            f"{key!r} must be a per-axis JSON object keyed by axis "
            f"({sorted(AXES)}), found {type(value).__name__}")]
    refusals = []
    for axis in sorted(set(value) - set(AXES)):
        refusals.append(Refusal(
            "axis_unknown",
            f"{key!r} names unknown axis {axis!r}; the keyboard/mouse "
            f"baseline declares exactly the axes {sorted(AXES)}"))
    if YAW not in value:
        refusals.append(Refusal(
            "axis_missing",
            f"{key!r} must declare the {YAW!r} axis"))
        return None, refusals
    raw = value[YAW]
    if not isinstance(raw, bool):
        refusals.append(Refusal(
            f"{key}_type",
            f"{key}.yaw must be a JSON boolean, found "
            f"{type(raw).__name__} {raw!r}"))
        return None, refusals
    return raw, []


# ── load: total, refusing, never writing ─────────────────────────────────────
@dataclass(frozen=True)
class LoadResult:
    settings: InputSettings
    status: str                 # "loaded" | "first_run" | "refused"
    refusals: tuple = ()
    path: Path = None

    @property
    def ok(self) -> bool:
        return self.status == "loaded"


def load_settings(path) -> LoadResult:
    """Load settings from `path` under the frozen persistence contract.

    Absent file -> (defaults, "first_run", no refusals) and NOTHING is
    created (load never writes). Any content problem -> (defaults, "refused",
    named refusals). Never a partial accept, never a silent default.
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return LoadResult(default_settings(), "first_run", (), path)
    except IsADirectoryError as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("io_error",
                                   f"settings path is a directory, not a "
                                   f"file: {path} ({exc})"),), path)
    except OSError as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("io_error",
                                   f"settings file could not be read: {path} "
                                   f"({exc})"),), path)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("json_corrupt",
                                   f"settings file is not valid UTF-8: "
                                   f"{exc}"),), path)
    try:
        document = json.loads(text, object_pairs_hook=_pairs_refusing_duplicates,
                              parse_constant=_refuse_constant)
    except _DuplicateKeyRefused as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("key_duplicate",
                                   f"duplicate JSON key {exc.key!r} -- JSON "
                                   f"would silently last-win; the file is "
                                   f"refused whole"),), path)
    except _NonFiniteRefused as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("not_finite_json",
                                   f"non-finite JSON literal {exc.token!r} "
                                   f"(NaN/Infinity are not numbers this "
                                   f"schema accepts)"),), path)
    except json.JSONDecodeError as exc:
        return LoadResult(default_settings(), "refused",
                          (Refusal("json_corrupt",
                                   f"settings file is not valid JSON: "
                                   f"{exc}"),), path)

    settings, refusals = _validate(document)
    status = "loaded" if not refusals else "refused"
    return LoadResult(settings, status, tuple(refusals), path)


# ── save: canonical bytes, atomic temp+rename ────────────────────────────────
def canonical_bytes(settings: InputSettings) -> bytes:
    """The deterministic v1 document bytes (sorted keys, fixed separators,
    one trailing newline). Two saves of equal settings are byte-identical."""
    return (json.dumps(settings.to_document(), sort_keys=True,
                       ensure_ascii=False, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


@dataclass(frozen=True)
class SaveResult:
    path: Path
    bytes_written: int
    atomic: bool


def save_settings(settings: InputSettings, path) -> SaveResult:
    """Atomically write `settings` to `path` (temp file in the SAME directory,
    flush + fsync, os.replace). The temp file is removed on any failure so no
    partial settings file is ever observable under the real name."""
    path = Path(path)
    payload = canonical_bytes(settings)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)   # explicit save: creating
    #                                              # the declared dir is the
    #                                              # caller's named action.
    tmp = directory / f".{path.name}.tmp-{os.getpid()}"
    try:
        with open(tmp, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)                      # atomic on POSIX and Windows
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    return SaveResult(path, len(payload), atomic=True)


# ── the mapper integration surface (the mapper file stays READ-ONLY) ─────────
def apply_settings(settings: InputSettings, mapper):
    """Feed a settings vector to a live InputMapper through its OWN declared
    data inputs -- and nothing else:

      mapper.bindings     = a fresh dict of physical-name -> action
      mapper.sensitivity  = the signed yaw delta-scale (+-sensitivity)

    These are exactly U01's constructor parameters (input_mapper.py:174-182);
    F5 measured that such data edits change emitted VALUES only. No module
    attribute of input_mapper or command_record is ever assigned here -- the
    seam's numbers are not input's to write (the seam-protection rule).
    Returns the mapper for chaining.
    """
    mapper.bindings = dict(settings.bindings)
    mapper.sensitivity = settings.signed_sensitivity()
    return mapper


def configured_mapper(sink, settings: InputSettings, **kwargs):
    """Build a settings-configured InputMapper in one call (headless: any
    injected tick_source passes straight through)."""
    return apply_settings(settings, IM.InputMapper(sink, **kwargs))
