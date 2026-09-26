"""input_settings_tests.py -- U04's falsifiers, measured (PREREGISTRATION.md).

Headless: temp directories, injected content, no clock, no window, no engine,
no desktop input. The mapper file (input_mapper.py) is READ-ONLY here -- the
tests consume it through U01's declared data surfaces and re-run his bound
checks. The six falsifiers:

  F1  SILENT ACCEPT   every named malformed/adversarial file refuses BY NAME
                      (distinct code + detail) and returns the DEFAULTS --
                      never a partial accept. Corrupt bytes, non-UTF-8,
                      non-object roots, duplicate keys (top level AND inside
                      bindings), NaN/Infinity literals, unknown schema,
                      missing/unknown keys, wrong types (booleans are not
                      numbers), unknown actions/axes, out-of-coverage
                      bindings, out-of-range / non-finite sensitivity.
  F2  SEAM POISON     the fuzz proof: adversarial payloads that carry the
                      SEAM'S OWN CONSTANT NAMES with poisoned values, plus a
                      2000-payload random fuzz, never move a seam constant
                      (input_mapper or command_record module attributes) and
                      never put an emitted record outside U01's bounds.
  F3  ROUND-TRIP      save -> load reproduces settings EXACTLY; save -> load
                      -> save is byte-identical (canonical form); the write
                      is atomic (temp file in the destination dir, os.replace,
                      no residue); a stale/corrupt temp or a corrupted real
                      file never gets silently accepted; load NEVER writes.
  F4  SENSITIVITY     yaw == clamp(counts * s / interval, +-OMEGA) exactly;
                      linearity below the clamp; |yaw_rate| NEVER exceeds
                      OMEGA_MAX_RAD_S across the declared range, at the
                      ceiling, and at 100x baseline (a direct-vector probe --
                      the FILE boundary refuses 100x, which is asserted too).
  F5  BINDINGS        duplicate binding keys refuse BY NAME (never JSON
                      last-wins); unknown actions refuse; a selected control
                      left unbound refuses; aliases stay legal; sprint/jump
                      bindings stay legal and refuse BY NAME at runtime; a
                      settings-driven remap changes emitted values only
                      (U01's F5 re-run through the settings path, conflicts
                      named by the mapper's precedence trace).
  F6  FIRST RUN       an absent file loads as defaults (exactly U01's
                      baseline), status "first_run", creating NOTHING; after
                      one explicit save the same path loads back as
                      "loaded" with identical settings; defaults drive the
                      mapper record-for-record like a plain U01 InputMapper.

    python tools/monkey_campaign/product/input_settings_tests.py
"""
from __future__ import annotations

import copy
import json
import random
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import input_mapper as IM                                  # noqa: E402
import input_settings as S                                 # noqa: E402
from tools.science_funnel.typeb_export import command_record as CR  # noqa: E402
from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
    CommandRecord, V1FamilyAdapter, V_MAX_IN_BAND_M_S as V_MAX,
)

OMEGA = IM.OMEGA_MAX_RAD_S
SEED = 20260924                             # frozen: the run reproduces
FAILURES = []


def check(name, ok, detail=""):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# ── shared harness ───────────────────────────────────────────────────────────
def write_bytes(tmpdir, name, payload: bytes) -> Path:
    p = Path(tmpdir) / name
    p.write_bytes(payload)
    return p


def write_doc(tmpdir, name, doc) -> Path:
    return write_bytes(tmpdir, name, json.dumps(doc).encode("utf-8"))


def v1_doc(bindings=None, yaw=0.002, invert=False, **extra):
    """A schema-valid v1 document (defaults unless overridden)."""
    doc = {"schema": S.SCHEMA_ID,
           "bindings": dict(IM.DEFAULT_BINDINGS) if bindings is None
           else bindings,
           "sensitivity": {"yaw": yaw},
           "invert": {"yaw": invert}}
    doc.update(extra)
    return doc


def refused_as_defaults(path, expected_code=None, expect_detail=None):
    """The F1 invariant, as one assertion: named refusal + EXACT defaults."""
    result = S.load_settings(path)
    ok = (result.status == "refused" and len(result.refusals) >= 1
          and result.settings == S.default_settings())
    if expected_code is not None:
        ok = ok and any(r.code == expected_code for r in result.refusals)
    if expect_detail is not None:
        ok = ok and any(expect_detail in r.detail for r in result.refusals)
    return ok, result


def drive_schedule(mapper, t0=1000):
    """A fixed input schedule (W held + A held + mouse flicks) through a
    mapper; returns every emitted record."""
    recs = []
    mapper.press("W", t0)
    mapper.press("A", t0)
    for i, t in enumerate(range(t0, t0 + 301, 50)):
        recs.extend(mapper.tick(t))
        if i == 2:
            mapper.mouse(1200)
        if i == 4:
            mapper.mouse(-800)
    return recs


def in_bounds(rec) -> bool:
    """U01's F2 bound check, verbatim: finite, v in [0, V_MAX], |yaw| <= OMEGA."""
    return (isinstance(rec, CommandRecord)
            and rec.v_forward == rec.v_forward
            and rec.v_forward not in (float("inf"), float("-inf"))
            and 0.0 <= rec.v_forward <= V_MAX
            and rec.yaw_rate == rec.yaw_rate
            and rec.yaw_rate not in (float("inf"), float("-inf"))
            and abs(rec.yaw_rate) <= OMEGA)


SEAM_SNAPSHOT_ATTRS = (
    "V_MAX_IN_BAND_M_S", "OMEGA_MAX_RAD_S", "INTERVAL_MS", "RELEASE_DECAY_MS",
    "VALID_MS", "EXPIRY_TICKS", "SENS_RAD_PER_COUNT", "PHYSICS_HZ",
    "POLICY_HZ", "HOLD_TICKS", "SOURCE_ID", "ACTIONS",
)
CR_SNAPSHOT_ATTRS = ("V_MAX_IN_BAND_M_S", "HOLD_TICKS", "PHYSICS_HZ",
                     "POLICY_HZ")


def snapshot_seam():
    snap = {f"input_mapper.{a}": getattr(IM, a, "<absent>")
            for a in SEAM_SNAPSHOT_ATTRS}
    snap["input_mapper.DEFAULT_BINDINGS"] = copy.deepcopy(IM.DEFAULT_BINDINGS)
    snap["input_mapper.REFUSALS"] = copy.deepcopy(IM.REFUSALS)
    snap.update({f"command_record.{a}": getattr(CR, a, "<absent>")
                 for a in CR_SNAPSHOT_ATTRS})
    return snap


def seam_unchanged(before) -> tuple[bool, str]:
    after = snapshot_seam()
    for key, value in before.items():
        if after.get(key) != value:
            return False, f"{key}: {value!r} -> {after.get(key)!r}"
    return True, f"{len(before)} seam constants bit-identical"


# ── F1 SILENT ACCEPT ─────────────────────────────────────────────────────────
def falsifier_1():
    print("F1 SILENT ACCEPT: every adversarial file refuses BY NAME + defaults")
    corpus = []          # (case-name, payload, expected-code, expected-detail)

    def case(name, payload, code, detail=""):
        corpus.append((name, payload, code, detail))

    case("corrupt_json_truncated",
         S.canonical_bytes(S.default_settings())[:40], "json_corrupt")
    case("corrupt_json_trailing_garbage",
         (S.canonical_bytes(S.default_settings()) + b"}}}`)."),
         "json_corrupt")
    case("not_utf8_bytes", b'\xff\xfe\x00{"schema": 1}', "json_corrupt")
    case("utf8_bom",
         b"\xef\xbb\xbf" + S.canonical_bytes(S.default_settings()),
         "json_corrupt")
    case("root_is_array", b"[1, 2, 3]", "root_not_object")
    case("root_is_string", b'"chimera.monkey_input.v1"', "root_not_object")
    case("root_is_null", b"null", "root_not_object")
    case("duplicate_top_level_key",
         b'{"schema": "chimera.monkey_input.v1", "schema": '
         b'"chimera.monkey_input.v1", "bindings": {}, "sensitivity": {}, '
         b'"invert": {}}',
         "key_duplicate", "duplicate JSON key 'schema'")
    case("duplicate_key_inside_bindings",
         '{"schema": "chimera.monkey_input.v1", "bindings": '
         '{"W": "forward", "W": "backward", "A": "turn_left", '
         '"D": "turn_right", "S": "backward"}, "sensitivity": '
         '{"yaw": 0.002}, "invert": {"yaw": false}}',
         "key_duplicate", "duplicate JSON key 'W'")
    case("nan_literal",
         json.dumps(v1_doc(yaw=float("nan"))).replace("NaN", "NaN"),
         "not_finite_json", "NaN")
    case("infinity_literal",
         '{"schema": "chimera.monkey_input.v1", "bindings": {"W": "forward"},'
         ' "sensitivity": {"yaw": Infinity}, "invert": {"yaw": false}}',
         "not_finite_json", "Infinity")
    case("unknown_schema_v2",
         json.dumps(v1_doc(schema="chimera.monkey_input.v2")),
         "schema_unknown", "chimera.monkey_input.v2")
    case("schema_other_name",
         json.dumps(v1_doc(schema="monkey_input.settings.v1")),
         "schema_unknown")
    case("schema_not_a_string", json.dumps(v1_doc(schema=1)), "schema_type")
    case("schema_key_missing",
         json.dumps({k: v for k, v in v1_doc().items() if k != "schema"}),
         "key_missing", "'schema'")
    case("key_missing_bindings",
         json.dumps({k: v for k, v in v1_doc().items()
                     if k != "bindings"}),
         "key_missing", "'bindings'")
    case("key_missing_invert",
         json.dumps({k: v for k, v in v1_doc().items() if k != "invert"}),
         "key_missing", "'invert'")
    case("seam_constant_names_as_unknown_keys",
         json.dumps(v1_doc(v_max_in_band_m_s=999.0, omega_max_rad_s=1e9,
                           interval_ms=-50, hold_ticks=1)),
         "key_unknown", "'v_max_in_band_m_s'")
    case("unknown_extra_key", json.dumps(v1_doc(turbo_mode=True)),
         "key_unknown", "'turbo_mode'")
    case("bindings_not_an_object",
         json.dumps(v1_doc(bindings=["W", "forward"])), "bindings_type")
    case("unknown_action",
         json.dumps(v1_doc(bindings={"W": "forward", "A": "turn_left",
                                     "D": "turn_right", "S": "backward",
                                     "C": "duck"})),
         "action_unknown", "'duck'")
    case("binding_value_not_a_string",
         json.dumps(v1_doc(bindings={"W": "forward", "A": "turn_left",
                                     "D": "turn_right", "S": 7})),
         "binding_type", "'S'")
    case("empty_binding_name",
         json.dumps(v1_doc(bindings={"": "forward", "A": "turn_left",
                                     "D": "turn_right"})),
         "binding_name_invalid")
    case("selected_control_left_unbound",
         json.dumps(v1_doc(bindings={"A": "turn_left", "D": "turn_right"})),
         "action_unbound", "'forward'")
    case("sensitivity_not_an_object", json.dumps(v1_doc(yaw=None) |
                                                  {"sensitivity": 0.002}),
         "sensitivity_type")
    case("unknown_axis_pitch",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": 0.002,
                                                 "pitch": 0.5}}),
         "axis_unknown", "'pitch'")
    case("sensitivity_missing_yaw",
         json.dumps({**v1_doc(), "sensitivity": {"pitch": 0.5}}),
         "axis_missing", "'yaw'")
    case("sensitivity_boolean_is_not_a_number",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": True}}),
         "sensitivity_type", "boolean")
    case("sensitivity_string",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": "0.002"}}),
         "sensitivity_type")
    case("sensitivity_1e999_overflows_to_inf",
         # a raw exponent literal: parses to float inf WITHOUT hitting the
         # NaN/Infinity lexer hook -- the magnitude check catches it by name
         '{"schema": "chimera.monkey_input.v1", '
         '"bindings": {"W": "forward"}, "sensitivity": {"yaw": 1e999}, '
         '"invert": {"yaw": false}}',
         "value_not_finite")
    case("sensitivity_zero_is_a_dead_axis",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": 0}}),
         "value_out_of_range")
    case("sensitivity_100x_baseline_is_above_the_derived_ceiling",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": 0.2}}),
         "value_out_of_range", "0.2")
    case("sensitivity_just_over_ceiling",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": 0.080000001}}),
         "value_out_of_range")
    case("sensitivity_negative",
         json.dumps({**v1_doc(), "sensitivity": {"yaw": -0.002}}),
         "value_out_of_range")
    case("invert_not_an_object",
         json.dumps({**v1_doc(), "invert": "yes"}), "invert_type")
    case("invert_value_not_a_boolean",
         json.dumps({**v1_doc(), "invert": {"yaw": 1}}), "invert_type")

    with tempfile.TemporaryDirectory() as tmp:
        bad = []
        for name, payload, code, detail in corpus:
            payload_bytes = (payload.encode("utf-8")
                             if isinstance(payload, str) else payload)
            path = write_bytes(tmp, name.replace(" ", "_") + ".json",
                               payload_bytes)
            ok, result = refused_as_defaults(path, code, detail)
            if not ok:
                bad.append((name, result.status,
                            [(r.code, r.detail) for r in result.refusals]))
        check(f"F1a all {len(corpus)} adversarial files refuse BY NAME and "
              "fall back to the EXACT defaults (never a partial accept)",
              not bad,
              f"{len(corpus)} cases"
              + (f", failures: {bad}" if bad else ""))

        result = S.load_settings(write_bytes(tmp, "probe.json",
                                             b'{"schema": 1.0}'))
        check("F1b each refusal carries a machine code AND a human detail "
              "naming the offense",
              result.status == "refused"
              and all(r.code and r.detail for r in result.refusals),
              "probe refusal: "
              + " | ".join(f"{r.code}: {r.detail}" for r in result.refusals))

        # the refusal list is the DIAGNOSIS, not just the first error:
        multi = v1_doc(schema="other.v1", yaw=-5, turbo=True)
        result = S.load_settings(write_doc(tmp, "multi.json", multi))
        check("F1c one file with several offenses reports EVERY offense",
              result.status == "refused"
              and {r.code for r in result.refusals} >=
              {"schema_unknown", "key_unknown", "value_out_of_range"},
              f"{len(result.refusals)} refusals: "
              f"{[r.code for r in result.refusals]}")

        seen_codes = set()
        for name, payload, code, _ in corpus:
            payload_bytes = (payload.encode("utf-8")
                             if isinstance(payload, str) else payload)
            path = write_bytes(tmp, "sweep_" + name + ".json", payload_bytes)
            res = S.load_settings(path)
            seen_codes |= {r.code for r in res.refusals}
        check("F1d the corpus exercises every declared refusal code",
              {"json_corrupt", "root_not_object", "key_duplicate",
               "not_finite_json", "schema_unknown", "schema_type",
               "key_missing", "key_unknown", "bindings_type",
               "action_unknown", "binding_type", "binding_name_invalid",
               "action_unbound", "sensitivity_type", "axis_unknown",
               "axis_missing", "value_not_finite", "value_out_of_range",
               "invert_type"} <= seen_codes,
              f"{len(seen_codes)} distinct codes: {sorted(seen_codes)}")


# ── F2 SEAM POISON (the fuzz proof) ──────────────────────────────────────────
def falsifier_2():
    print("F2 SEAM POISON: no settings vector alters the seam's constants")
    before = snapshot_seam()
    sink = IM.MockSink()
    mapper = IM.InputMapper(sink)

    # (i) the NAMED payloads: every seam constant's own name as a key,
    # carrying poisoned values -- through the file boundary.
    poison_names = ["v_max_in_band_m_s", "V_MAX_IN_BAND_M_S",
                    "omega_max_rad_s", "OMEGA_MAX_RAD_S", "interval_ms",
                    "INTERVAL_MS", "hold_ticks", "HOLD_TICKS", "expiry_ticks",
                    "valid_ms", "release_decay_ms", "physics_hz", "policy_hz",
                    "sens_rad_per_count", "default_bindings", "actions",
                    "refusals", "source_id", "record_version"]
    poison_values = [1e300, -1e300, 0, -1, "NaN", {"v_forward": 1e9},
                     [0.763625 * 1000], True, None]
    named = 0
    with tempfile.TemporaryDirectory() as tmp:
        for nm in poison_names:
            for pv in poison_values:
                doc = v1_doc()
                doc[nm] = pv
                result = S.load_settings(write_doc(tmp, "poison.json", doc))
                S.apply_settings(result.settings, mapper)
                drive_schedule(mapper)
                named += 1
        ok_named, why = seam_unchanged(before)
        check(f"F2a all {named} named poison payloads (seam-constant key "
              "names x poisoned values) leave the seam untouched",
              ok_named, why)

        # (ii) the 2000-payload random fuzz: half start from a valid doc and
        # mutate (legally or adversarially), half are built from junk pools
        # -- refused or loaded, apply stays inside U01's bounds and the seam
        # never moves.
        rng = random.Random(SEED)
        known_actions = ("forward", "backward", "turn_left", "turn_right")
        bad, loaded, refused_n, records = [], 0, 0, 0
        for i in range(2000):
            t0 = 2000 + 400 * i          # advance the injected clock every
            #                            # iteration: the mapper's 50 ms grid
            #                            # must re-anchor (W+A stay held)
            if rng.random() < 0.5:
                doc = v1_doc()
                for _ in range(rng.randint(0, 2)):
                    part = rng.random()
                    if part < 0.35:                   # legal binding mutation
                        doc["bindings"][rng.choice(
                            list(doc["bindings"]))] = rng.choice(known_actions)
                    elif part < 0.6:                  # legal-ish numbers
                        doc["sensitivity"]["yaw"] = rng.choice(
                            [0.0005, 0.002, 0.01, 0.079, -0.002, 0, 1e400])
                    elif part < 0.8:
                        doc["invert"]["yaw"] = rng.choice(
                            [True, False, "yes", 1])
                    else:                             # a junk extra key
                        doc[rng.choice(["v_max_in_band_m_s", "interval_ms",
                                        "turbo", "omega_max_rad_s"])] = \
                            rng.choice([1e300, -1, {"x": 1}, "0.08"])
            else:
                doc = {rng.choice(["schema", "bindings", "sensitivity",
                                   "invert", "v_max_in_band_m_s", "interval_ms",
                                   "extra", "yaw", "forward"]):
                       rng.choice([1e300, -1e300, 0.002, 0.08, 0.2, -0.002, 0,
                                   1, True, False, None,
                                   "chimera.monkey_input.v1",
                                   "chimera.monkey_input.v9",
                                   {"yaw": 0.002}, {"yaw": True},
                                   {"yaw": 1e400}, ["W"], "forward", "duck",
                                   {"W": "forward"},
                                   dict(IM.DEFAULT_BINDINGS)])
                       for _ in range(rng.randint(1, 5))}
            result = S.load_settings(write_doc(tmp, "fuzz.json", doc))
            loaded += result.status == "loaded"
            refused_n += result.status == "refused"
            S.apply_settings(result.settings, mapper)
            for rec in drive_schedule(mapper, t0=t0):
                records += 1
                if not in_bounds(rec):
                    bad.append((i, rec))
            if mapper.sensitivity != mapper.sensitivity:   # non-finite
                bad.append((i, "non-finite applied sensitivity"))
        ok_fuzz, why = seam_unchanged(before)
        check(f"F2b the 2000-payload fuzz: {loaded} loaded / {refused_n} "
              "refused, every emitted record inside U01's bounds",
              not bad and (loaded + refused_n) == 2000 and ok_fuzz,
              f"{records} records checked, {len(bad)} violations"
              + (f", first: {bad[0]}" if bad else "")
              + ("" if ok_fuzz else f"; {why}"))
        check("F2c the fuzz was not vacuous (it actually loaded some files "
              "and emitted records)",
              loaded > 100 and records > 500,
              f"{loaded} loaded, {records} records")

        # (iii) the DEFAULT_BINDINGS deep-protection probe: apply() hands the
        # mapper a fresh dict -- mutating the mapper's table can never write
        # U01's module constant.
        mapper2 = IM.InputMapper(IM.MockSink())
        S.apply_settings(S.default_settings(), mapper2)
        mapper2.bindings["W"] = "turn_left"
        check("F2d apply() copies the bindings table: mutating the mapper's "
              "dict never writes DEFAULT_BINDINGS",
              IM.DEFAULT_BINDINGS.get("W") == "forward",
              f"DEFAULT_BINDINGS['W'] == {IM.DEFAULT_BINDINGS.get('W')!r}")

    # (iv) the direct-vector probe (defense in depth, BEYOND the file
    # boundary): finite-extreme sensitivities handed straight to
    # apply_settings -- the mapper's own clamp is the bound.
    probe_bad = []
    sink3 = IM.MockSink()
    m3 = IM.InputMapper(sink3)
    m3.press("W", 1000)
    t = 2000
    for sens, invert in ((1e300, False), (-1e300, True), (0.0, False),
                         (-0.002, True), (S.SENS_YAW_MAX_RAD_PER_COUNT, False),
                         (0.2, False)):            # 0.2 == 100x baseline
        vec = S.InputSettings(bindings=dict(IM.DEFAULT_BINDINGS),
                              sensitivity=abs(sens) or 1e-300,
                              invert_yaw=invert)
        S.apply_settings(vec, m3)
        m3.mouse(1_000_000)
        for rec in m3.tick(t):
            if not in_bounds(rec):
                probe_bad.append((sens, invert, rec))
        t += 100
    check("F2e direct-vector probe: even extreme (and 100x) sensitivities "
          "cannot push an emitted record past the seam's bounds",
          not probe_bad, f"{len(sink3.records)} records, "
                         f"{len(probe_bad)} violations"
          + (f", first: {probe_bad[0]}" if probe_bad else ""))


# ── F3 ROUND-TRIP / ATOMIC / LOAD NEVER WRITES ───────────────────────────────
def falsifier_3():
    print("F3 ROUND-TRIP: exact reproduction, byte-identical resave, atomic "
          "write, load never writes")
    custom = S.InputSettings(
        bindings={"W": "backward", "Up": "forward", "S": "forward",
                  "A": "turn_left", "D": "turn_right", "Shift": "sprint"},
        sensitivity=0.006, invert_yaw=True)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "monkey_input_settings.json"

        # load never writes: first_run leaves the directory exactly as it was
        listing_before = sorted(p.name for p in Path(tmp).iterdir())
        result = S.load_settings(path)
        listing_after = sorted(p.name for p in Path(tmp).iterdir())
        check("F3a first_run returns defaults and creates NOTHING on disk",
              result.status == "first_run"
              and result.settings == S.default_settings()
              and listing_before == listing_after)

        S.save_settings(custom, path)
        first_bytes = path.read_bytes()
        loaded = S.load_settings(path)
        check("F3b save -> load reproduces the settings EXACTLY "
              "(bindings, sensitivity bit-exact, inversion)",
              loaded.status == "loaded" and loaded.settings == custom,
              f"sensitivity {loaded.settings.sensitivity!r} vs "
              f"{custom.sensitivity!r}, invert {loaded.settings.invert_yaw}")
        S.save_settings(loaded.settings, path)
        second_bytes = path.read_bytes()
        check("F3c save -> load -> save is BYTE-IDENTICAL (canonical form)",
              first_bytes == second_bytes, f"{len(first_bytes)} bytes")

        # atomic write, observed: os.replace is called with a same-directory
        # temp source; no temp residue remains.
        calls = []
        real_replace = S.os.replace

        def spy(src, dst, *a, **kw):
            calls.append((Path(src), Path(dst)))
            return real_replace(src, dst, *a, **kw)

        S.os.replace = spy
        try:
            S.save_settings(custom, path)
        finally:
            S.os.replace = real_replace
        residue = [p.name for p in Path(tmp).iterdir() if ".tmp-" in p.name]
        atomic_ok = (len(calls) == 1
                     and calls[0][0].parent == calls[0][1].parent
                     == path.parent
                     and calls[0][0].name.startswith("." + path.name + ".tmp-")
                     and not residue)
        check("F3d the write is atomic: same-directory temp -> os.replace, "
              "no temp residue", atomic_ok,
              f"replace {[(s.name, d.name) for s, d in calls]}"
              + (f", residue {residue}" if residue else ""))

        # a stale temp file (an interrupted write from a dead process) is
        # never consulted by load
        stale = Path(tmp) / f".{path.name}.tmp-999999"
        stale.write_bytes(b"{ this was never finished")
        loaded2 = S.load_settings(path)
        check("F3e a stale interrupted-write temp is ignored by load (the "
              "real file wins; the temp is not silently accepted)",
              loaded2.status == "loaded" and loaded2.settings == custom)

        # a corrupted REAL file refuses (never half-parsed through to
        # settings); WHICH code names the offense depends on where the flip
        # lands (a flipped byte can turn a value into a different named
        # refusal) -- the invariant is: refused + EXACT defaults, any flip
        flip_codes = []
        ok = True
        for flip_at in (1, len(first_bytes) // 2, len(first_bytes) - 2):
            corrupted = bytearray(first_bytes)
            corrupted[flip_at] = ord("#")
            bad_path = Path(tmp) / "corrupted.json"
            bad_path.write_bytes(bytes(corrupted))
            res = S.load_settings(bad_path)
            flip_codes.append([r.code for r in res.refusals])
            if not (res.status == "refused" and res.refusals
                    and res.settings == S.default_settings()):
                ok = False
        check("F3f corrupted (bit-flipped at 3 positions) real files refuse "
              "BY NAME and fall back to defaults -- never half-parsed", ok,
              f"flips at head/middle/tail -> codes {flip_codes}")


# ── F4 SENSITIVITY SCALING ───────────────────────────────────────────────────
def falsifier_4():
    print("F4 SENSITIVITY: deltas scale linearly to the clamp; bounds never "
          "exceeded anywhere in the declared range")
    interval_s = IM.INTERVAL_MS / 1000.0
    counts_values = (1, 10, 37, 100, 1000, 5000, 1_000_000)
    sweep = (0.0005, 0.002, 0.004, 0.01, 0.02, 0.05,
             S.SENS_YAW_MAX_RAD_PER_COUNT)      # up to the derived ceiling
    bad_lin, bad_bound, triples = [], [], 0
    for sens in sweep:
        for invert in (False, True):
            sink = IM.MockSink()
            m = IM.InputMapper(sink)
            S.apply_settings(S.InputSettings(
                bindings=dict(IM.DEFAULT_BINDINGS), sensitivity=sens,
                invert_yaw=invert), m)
            m.press("W", 1000)
            sign = -1.0 if invert else 1.0
            for j, counts in enumerate(counts_values):
                m._mouse_counts = float(counts)   # exact injection, no fuzz
                recs = m.tick(2000 + 50 * j)      # each triple: its boundary
                triples += 1
                if not recs:
                    bad_lin.append((sens, invert, counts, "no record"))
                    continue
                yaw = recs[0].yaw_rate
                expected = sign * max(-OMEGA, min(OMEGA,
                                                  counts * sens / interval_s))
                if yaw != expected:
                    bad_lin.append((sens, invert, counts, yaw, expected))
                if not in_bounds(recs[0]):
                    bad_bound.append((sens, invert, counts, yaw))
            m.release_all(10_000)
    check("F4a yaw == clamp(counts * s / interval, +-OMEGA) EXACTLY at every "
          "sweep sensitivity (incl. the derived ceiling), every count load, "
          "both inversion signs; bounds never exceeded",
          not bad_lin and not bad_bound,
          f"{triples} (sensitivity, invert, counts) triples"
          + (f", linear failures: {bad_lin[:3]}" if bad_lin else "")
          + (f", bound failures: {bad_bound[:3]}" if bad_bound else ""))

    # linearity BEFORE the clamp: doubling s doubles the yaw (10 counts,
    # 0.002 -> 0.4 rad/s, unclamped; 0.004 -> 0.8)
    yaws = {}
    for sens in (0.002, 0.004):
        sink = IM.MockSink()
        m = IM.InputMapper(sink)
        S.apply_settings(S.InputSettings(
            bindings=dict(IM.DEFAULT_BINDINGS), sensitivity=sens), m)
        m.press("W", 1000)
        m._mouse_counts = 10.0
        yaws[sens] = m.tick(1500)[0].yaw_rate
    check("F4b doubling the sensitivity doubles the unclamped yaw "
          "(deltas scale; the seam ceiling is not a sensitivity target)",
          abs(yaws[0.004] - 2.0 * yaws[0.002]) < 1e-12,
          f"yaw(0.002)={yaws[0.002]}, yaw(0.004)={yaws[0.004]}")

    # 100x baseline through the mapper: bounds hold (U01's F6f check reused)
    sink = IM.MockSink()
    m = IM.InputMapper(sink)
    S.apply_settings(S.InputSettings(
        bindings=dict(IM.DEFAULT_BINDINGS), sensitivity=0.2), m)
    m.press("W", 1000)
    m.mouse(100_000)                             # a violent flick at 100x
    rec = m.tick(1100)[0]
    check("F4c 100x baseline + a 100k-count flick: |yaw_rate| == the seam's "
          "own steer bound, never beyond it (100x scales INPUT deltas, never "
          "the ceiling)",
          rec.yaw_rate == OMEGA and in_bounds(rec),
          f"yaw {rec.yaw_rate} == OMEGA {OMEGA}")

    # the FILE boundary refuses 100x: the schema, not the clamp, is the wall
    with tempfile.TemporaryDirectory() as tmp:
        ok, result = refused_as_defaults(
            write_doc(tmp, "hundredx.json", v1_doc(yaw=0.2)),
            "value_out_of_range")
        check("F4d the 100x vector is UNREACHABLE through a settings file "
              "(out-of-range refuses by name before any mapper sees it)", ok)

    # inversion flips the SIGN of mouse yaw only; magnitude untouched
    base = S.default_settings()
    sink_p, sink_i = IM.MockSink(), IM.MockSink()
    mp = S.configured_mapper(sink_p, base)
    mi = S.configured_mapper(
        sink_i, S.InputSettings(base.bindings, base.sensitivity,
                                invert_yaw=True))
    for mm in (mp, mi):
        mm.press("W", 1000)
        mm.mouse(20)                             # 20 * 0.002 / 0.05 = 0.8
    yp, yi = mp.tick(1100)[0].yaw_rate, mi.tick(1100)[0].yaw_rate
    check("F4e invert.yaw negates the mouse-driven yaw exactly "
          "(same magnitude, flipped sign, unclamped)",
          yi == -yp and abs(yp - 0.8) < 1e-9, f"+{yp} / {yi}")

    # key-driven records are identical under inversion (inversion is the
    # continuous axis, not a key swap)
    kp = drive_schedule(S.configured_mapper(IM.MockSink(), base))
    ki = drive_schedule(S.configured_mapper(
        IM.MockSink(), S.InputSettings(base.bindings, base.sensitivity,
                                       invert_yaw=True)))
    check("F4f under yaw inversion the A-key's yaw contribution stays "
          "+OMEGA (inversion is the continuous axis, not a key swap)",
          [r.v_forward for r in kp] == [r.v_forward for r in ki]
          and bool(ki) and all(r.yaw_rate >= 0.0 for r in ki),
          f"{len(ki)} records; A-key yaw stays >= 0 under inversion")


# ── F5 BINDINGS ──────────────────────────────────────────────────────────────
def falsifier_5():
    print("F5 BINDINGS: collisions named, unknown actions refused, coverage "
          "enforced, remap values-only")
    with tempfile.TemporaryDirectory() as tmp:
        # duplicate physical key inside bindings: JSON would silently last-win
        dup = ('{"schema": "chimera.monkey_input.v1", "bindings": '
               '{"W": "forward", "W": "backward", "A": "turn_left", '
               '"D": "turn_right", "S": "backward"}, "sensitivity": '
               '{"yaw": 0.002}, "invert": {"yaw": false}}')
        ok, result = refused_as_defaults(
            write_bytes(tmp, "dup.json", dup.encode("utf-8")),
            "key_duplicate", "duplicate JSON key 'W'")
        check("F5a a duplicate binding key refuses BY NAME (never a silent "
              "last-wins to 'backward')", ok,
              f"refusal: {result.refusals[0].detail if result.refusals else '?'}")

        # aliases are LEGAL (U01's W/Up shape) and both drive at runtime
        sink = IM.MockSink()
        m = S.configured_mapper(sink, S.default_settings())
        m.press("W", 1000)
        m.press("Up", 1000)
        rec = m.tick(1000)[0]
        check("F5b alias bindings (two physicals, one action) stay legal "
              "and both drive (W and Up -> the band ceiling)",
              rec.v_forward == V_MAX)

        # sprint/jump bindings stay LEGAL in settings and refuse BY NAME at
        # runtime (U01's registered refusals, through the settings path)
        sink2 = IM.MockSink()
        m2 = S.configured_mapper(sink2, S.default_settings())
        m2.press("Shift", 1000)
        m2.press("Space", 1000)
        m2.tick(1000)
        refused = dict(m2.last_trace.get("refused", []))
        check("F5c sprint/jump bindings load fine and refuse BY NAME at "
              "runtime (the settings path preserves U01's refusals)",
              "sprint" in refused and "jump" in refused
              and len(sink2.records) == 0,
              f"refused {sorted(refused)}")

        # remap through the settings path: values change, the contract does
        # not (U01's F5, re-run through apply_settings)
        sink_def, sink_rem = IM.MockSink(), IM.MockSink()
        md = S.configured_mapper(sink_def, S.default_settings())
        mr = S.configured_mapper(
            sink_rem,
            S.InputSettings(bindings={"W": "backward", "S": "backward",
                                      "A": "turn_left", "D": "turn_right"},
                            sensitivity=0.002))
        md.press("W", 1000); md.tick(1000)
        mr.press("W", 1000); mr.tick(1000)
        rd, rr = sink_def.records[0], sink_rem.records[0]
        adapter = V1FamilyAdapter()
        pd, pr = adapter.project(rd), adapter.project(rr)
        check("F5d a settings-driven remap changes emitted VALUES only: same "
              "record type/version, same bounds, same adapter projection",
              rd.v_forward == V_MAX and rr.v_forward == 0.0
              and rr.record_version == rd.record_version
              and pd["routed_yaw_rate"] is False
              and pr["routed_yaw_rate"] is False)

        # a W-vs-forward collision created by a remap is NAMED by the
        # mapper's own precedence trace (the runtime half of the collision law)
        mrx = S.configured_mapper(
            IM.MockSink(),
            S.InputSettings(bindings={"W": "backward", "Up": "forward",
                                      "S": "backward", "A": "turn_left",
                                      "D": "turn_right"},
                            sensitivity=0.002))
        mrx.press("W", 1000)                 # W remapped to backward
        mrx.press("Up", 1000)                # Up still forward
        r = mrx.tick(1000)
        check("F5e a remap-created backward-vs-forward collision resolves by "
              "U01's precedence AND is named in the trace",
              r[0].v_forward == V_MAX
              and any("forward" in c and "backward" in c
                      for c in mrx.last_trace.get("conflicts", [])),
              f"conflicts {mrx.last_trace.get('conflicts')}")

        # the FILE boundary enforces coverage and action names:
        ok_u, res_u = refused_as_defaults(
            write_doc(tmp, "unbound.json",
                      v1_doc(bindings={"A": "turn_left",
                                       "D": "turn_right"})),
            "action_unbound")
        check("F5f a file leaving a selected control unbound refuses BY NAME",
              ok_u)
        ok_d, _ = refused_as_defaults(
            write_doc(tmp, "duck.json",
                      v1_doc(bindings={"W": "forward", "A": "turn_left",
                                       "D": "turn_right", "S": "backward",
                                       "C": "duck"})),
            "action_unknown")
        check("F5g an unknown action name in a file refuses BY NAME "
              "(the grammar refuses what it cannot name)", ok_d)


# ── F6 FIRST RUN + DEFAULTS ──────────────────────────────────────────────────
def falsifier_6():
    print("F6 FIRST RUN: absent file -> exact U01 defaults, nothing created")
    with tempfile.TemporaryDirectory() as tmp:
        absent = Path(tmp) / "settings.json"
        result = S.load_settings(absent)
        defaults = S.default_settings()
        check("F6a absent file -> status 'first_run' with the DEFAULTS and "
              "no refusals", result.status == "first_run"
              and result.refusals == () and result.settings == defaults)
        check("F6b the defaults ARE U01's baseline: his bindings table, his "
              "baseline sensitivity, no inversion",
              defaults.bindings == dict(IM.DEFAULT_BINDINGS)
              and defaults.sensitivity == IM.SENS_RAD_PER_COUNT
              and defaults.invert_yaw is False
              and not absent.exists(),
              f"sensitivity {defaults.sensitivity!r} == "
              f"SENS_RAD_PER_COUNT {IM.SENS_RAD_PER_COUNT!r}")

        # defaults drive the mapper EXACTLY like a plain U01 InputMapper
        plain = IM.InputMapper(IM.MockSink())
        via_settings = S.configured_mapper(IM.MockSink(), defaults)
        rp, rs = drive_schedule(plain), drive_schedule(via_settings)
        same = (len(rp) == len(rs) and all(
            a.v_forward == b.v_forward and a.yaw_rate == b.yaw_rate
            and a.issued_tick == b.issued_tick and a.source == b.source
            for a, b in zip(rp, rs)))
        check("F6c defaults reproduce a plain U01 mapper's emission "
              "record-for-record (same schedule)",
              same, f"{len(rs)} records identical")

        # after one explicit save, the same path loads as 'loaded'
        S.save_settings(defaults, absent)
        again = S.load_settings(absent)
        check("F6d after one explicit save the same path loads as 'loaded' "
              "with identical settings",
              again.status == "loaded" and again.settings == defaults
              and again.refusals == ())

    # importing the module created nothing in the declared default location
    declared = S.DEFAULT_SETTINGS_PATH
    check("F6e the declared default path was never created by import or by "
          "these tests (nothing writes outside an explicit save)",
          not declared.exists(), f"declared: {declared}")


def main():
    print("input_settings_tests -- U04 falsifiers "
          "(prereg: agents/U04_settings/PREREGISTRATION.md)")
    falsifier_1()
    falsifier_2()
    falsifier_3()
    falsifier_4()
    falsifier_5()
    falsifier_6()
    print()
    if FAILURES:
        print(f"VERDICT: FAIL -- {len(FAILURES)} falsifier check(s) fired: "
              f"{FAILURES}")
        return 1
    print("VERDICT: GREEN -- all falsifier checks passed; the frozen "
          "contract held.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
