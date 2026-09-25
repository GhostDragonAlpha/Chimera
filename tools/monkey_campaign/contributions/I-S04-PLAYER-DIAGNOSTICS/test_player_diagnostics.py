"""test_player_diagnostics.py -- I-S04 falsifier harness (stdlib unittest).

The tests read the EXTRACTED PINNED SOURCE BYTES in reference/ (sha256 ledger:
reference/EXTRACTION_LEDGER.json, pinned revision
9afbddcd90164b5544a16fd0bc72278d985eb6e3) with `ast` -- the module's
inventory, its offered actions and its vocabulary are checked against the
real source, not against a transcription of it.

Falsifiers under test (PREREGISTRATION.md):
  F1  player text contains a raw local path        -> build fails
  F2  a message claims an unsupported action       -> build fails
  F3  unknown errors silently report success       -> build fails
plus determinism (same input -> byte-identical output).

Headless, deterministic, bounded: full suite runs in well under 120 s.
"""
from __future__ import annotations

import ast
import json
import pathlib
import re
import unittest

import player_diagnostics as pd

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE / "reference"
INPUT_SETTINGS_SRC = (REF / "input_settings.py").read_text(encoding="utf-8")
SESSION_FLOW_SRC = (REF / "session_flow.py").read_text(encoding="utf-8")
STATE_FEEDBACK_SRC = (REF / "state_feedback.py").read_text(encoding="utf-8")

# Representative refusal details in the pinned details' exact shapes
# (input_settings.py at the pinned revision; the {tok} slots these exercise
# are the templates that interpolate the scrubbed offense token).
SAMPLE_DETAILS = {
    "root_not_object": "the settings document must be a JSON object, found list",
    "key_missing": "required key 'bindings' is missing",
    "key_unknown": ("unknown key 'v_max_in_band_m_s' -- the v1 schema refuses "
                    "what it cannot name"),
    "schema_type": "'schema' must be the string 'chimera.monkey_input.v1', found int",
    "schema_unknown": "unknown schema 'chimera.monkey_input.v9'",
    "bindings_type": "'bindings' must be a JSON object, found list",
    "binding_name_invalid": "binding physical names must be non-empty strings, found 3",
    "binding_type": "binding 'W' must map to a non-empty action string, found ''",
    "action_unknown": "binding 'J' -> unknown action 'dodge'",
    "action_unbound": "no physical input is bound to selected action 'forward'",
    "sensitivity_type": "'sensitivity' must be a per-axis JSON object, found list",
    "invert_type": "'invert' must be a per-axis JSON object, found list",
    "axis_unknown": "'sensitivity' names unknown axis 'pitch'",
    "axis_missing": "'sensitivity' must declare the 'yaw' axis",
    "value_not_finite": "sensitivity.yaw must be finite, found inf",
    "value_out_of_range": "sensitivity.yaw = 99 is outside the declared range",
    "io_error": "settings file could not be read: [Errno 13] Permission denied",
    "json_corrupt": "settings file is not valid JSON: Expecting value: line 1",
    "key_duplicate": "duplicate JSON key 'bindings'",
    "not_finite_json": "non-finite JSON literal 'NaN'",
}
ALL_SETTINGS_CODES = sorted(SAMPLE_DETAILS)


def _literal_first_args(source: str, func_names: tuple[str, ...]) -> set[str]:
    """First-argument string literals of calls named in `func_names`."""
    out: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            name = (func.id if isinstance(func, ast.Name)
                    else getattr(func, "attr", None))
            if name in func_names and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    out.add(arg.value)
    return out


def _literal_assignment(source: str, name: str):
    """The value assigned to a module-level name, evaluated against the
    module's own constant names (the pinned TRANSITIONS keys are tuples of
    names like ATTRACT/PLAYING, not bare literals)."""
    tree = ast.parse(source)
    env: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) for t in node.targets):
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                continue                       # not a pure literal: skip
            for t in node.targets:
                if isinstance(t, ast.Name):
                    env[t.id] = value
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == name
                for t in node.targets):
            expression = ast.Expression(node.value)
            return eval(compile(expression, "<pinned-source>", "eval"),
                        {"__builtins__": {}}, dict(env))
    raise AssertionError(f"no literal assignment to {name!r} found")


def _validators_key_literals(source: str) -> set[str]:
    """The `key` arguments passed to the two axis validators -- the source of
    the two COMPUTED refusal codes f\"{key}_type\" (input_settings.py:299,364)."""
    keys: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            func = node.func
            name = (func.id if isinstance(func, ast.Name)
                    else getattr(func, "attr", None))
            if name in ("_validate_axis_number", "_validate_axis_bool"):
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    keys.add(node.args[1].value)
    return keys


# ── the inventory is exactly the pinned inventory ─────────────────────────────
class InventoryMatchesPinnedSource(unittest.TestCase):
    """No invented codes, no missed codes: the module's inventory is derived
    from the pinned bytes and checked against them, both directions."""

    def test_settings_codes_equal_pinned_refusal_literals_plus_computed(self):
        literals = _literal_first_args(INPUT_SETTINGS_SRC, ("Refusal",))
        derived = {f"{key}_type"
                   for key in _validators_key_literals(INPUT_SETTINGS_SRC)}
        expected = literals | derived
        self.assertEqual(set(pd.KNOWN_SETTINGS_CODES), expected)
        self.assertEqual(len(pd.KNOWN_SETTINGS_CODES), 20)

    def test_every_pinned_code_translates_with_representative_detail(self):
        for code in ALL_SETTINGS_CODES:
            with self.subTest(code=code):
                result = pd.explain_settings_refusal(code, SAMPLE_DETAILS[code])
                self.assertFalse(result.ok)
                self.assertEqual(result.status, "refused")
                self.assertTrue(result.message)
                self.assertTrue(result.actions)          # never a dead end
                self.assertTrue(result.correlation_id)

    def test_flow_kinds_equal_pinned_drop_and_failure_names(self):
        drops = _literal_first_args(SESSION_FLOW_SRC, ("_drop",))
        # restart_failed / exit_failed are last_trace keys (lines 340, 351)
        traced = {node.value for node in ast.walk(ast.parse(SESSION_FLOW_SRC))
                  if isinstance(node, ast.Constant) and isinstance(node.value, str)
                  and node.value in ("restart_failed", "exit_failed")}
        self.assertEqual(set(pd.KNOWN_FLOW_KINDS), drops | traced)
        self.assertEqual(set(pd.KNOWN_FLOW_KINDS),
                         {"key_press", "key_release", "mouse", "decision_tick",
                          "flow_action", "restart_failed", "exit_failed"})


# ── falsifier F2: every offered action is a real pinned transition ───────────
class ActionsAreSupportedByPinnedStates(unittest.TestCase):
    """Every (state, action) pair the module offers is a row of the pinned
    TRANSITIONS table, and every key name in a message is the pinned binding
    of exactly the actions that row's pair names. Nothing else is offered."""

    def setUp(self):
        self.bindings = _literal_assignment(SESSION_FLOW_SRC,
                                            "DEFAULT_FLOW_BINDINGS")
        self.transitions = {tuple(k): v for k, v in
                            _literal_assignment(SESSION_FLOW_SRC,
                                                "TRANSITIONS").items()}
        self.states = _literal_assignment(SESSION_FLOW_SRC, "STATES")

    def _key_tokens(self, message: str) -> set[str]:
        return set(re.findall(r"\b(Return|Escape|R|Q)\b", message))

    def _check(self, result: pd.PlayerDiagnostic):
        pairs = [tuple(p) for p in result.diagnostic["grounding"]]
        for pair in pairs:
            self.assertIn(pair, self.transitions,
                          f"offered {pair} is not a pinned transition (F2)")
        expected_keys = {key for key, action in self.bindings.items()
                         if any(action == pair[1] for pair in pairs)}
        text = result.message + " " + " ".join(result.actions)
        self.assertEqual(self._key_tokens(text), expected_keys,
                         f"keys in {text!r} do not match the offered "
                         f"transition pairs {pairs} (F2)")
        # each action sentence names exactly the key its pair binds
        for pair, sentence in zip(pairs, result.actions):
            key = next(k for k, a in self.bindings.items() if a == pair[1])
            self.assertTrue(sentence.startswith(f"Press {key} "),
                            f"{sentence!r} does not press the bound key "
                            f"{key!r} for {pair}")

    def test_all_flow_messages_offer_only_real_transitions(self):
        # plain drops, per real state (playing cannot produce a drop)
        for kind in ("key_press", "key_release", "mouse", "decision_tick"):
            for state in ("attract", "paused", "exited"):
                with self.subTest(kind=kind, state=state):
                    result = pd.explain_flow_drop(kind, "", state=state)
                    self.assertEqual(result.status, "dropped")
                    self._check(result)
        # the named flow_action no-ops
        for action_state in (("restart", "playing"), ("confirm", "playing"),
                             ("pause", "attract"), ("restart", "attract"),
                             ("pause", "paused")):
            with self.subTest(pair=action_state):
                result = pd.explain_flow_drop(
                    "flow_action", f"{action_state[0]}@{action_state[1]}")
                self.assertEqual(result.status, "dropped")
                self._check(result)
        # failed transitions
        result = pd.explain_flow_drop("restart_failed", "RuntimeError('boot')")
        self.assertEqual(result.status, "failed")
        self._check(result)
        result = pd.explain_flow_drop("exit_failed", "RuntimeError('kill')")
        self.assertEqual(result.status, "failed")
        self._check(result)

    def test_settings_actions_never_claim_keys_or_a_settings_menu(self):
        # At the pinned revision the settings surface is file load + defaults;
        # no key press and no settings screen exists there to promise (F2).
        for code in ALL_SETTINGS_CODES:
            result = pd.explain_settings_refusal(code, SAMPLE_DETAILS[code])
            with self.subTest(code=code):
                self.assertFalse(self._key_tokens(result.message),
                                 "settings message promises a session key")
                for sentence in result.actions:
                    self.assertFalse(self._key_tokens(sentence))
                    self.assertNotIn("settings menu", sentence.lower())
                    self.assertNotIn("settings screen", sentence.lower())

    def test_flow_actions_carry_the_state_in_the_name(self):
        result = pd.explain_flow_drop("flow_action", "restart@playing")
        self.assertEqual(result.name, "flow_action:restart@playing")

    def test_every_state_in_guidance_is_a_pinned_state(self):
        self.assertEqual(set(pd._FLOW_STATE_GUIDANCE), set(self.states))


# ── falsifier F1: the player never receives raw local paths ──────────────────
class PlayerTextNeverContainsPathsOrSecrets(unittest.TestCase):
    PATHY = "ENOENT E:\\repo\\secret\\forest.bin"

    def _all_player_strings(self):
        for code in ALL_SETTINGS_CODES:
            result = pd.explain_settings_refusal(
                code, SAMPLE_DETAILS[code] + " " + self.PATHY)
            yield code, result
        for kind in ("key_press", "key_release", "mouse", "decision_tick"):
            for state in ("attract", "paused", "exited"):
                yield f"{kind}@{state}", pd.explain_flow_drop(
                    kind, self.PATHY, state=state)
        yield "flow_action", pd.explain_flow_drop(
            "flow_action", "restart@playing " + self.PATHY)
        yield "restart_failed", pd.explain_flow_drop(
            "restart_failed", self.PATHY)
        yield "exit_failed", pd.explain_flow_drop("exit_failed", self.PATHY)
        yield "unknown", pd.explain("no_such_identity", self.PATHY)

    def test_card_example_exception_keeps_path_out_of_player_text(self):
        class FakeOSError(Exception):
            pass

        exc = FakeOSError(self.PATHY)
        result = pd.explain_exception(exc)
        for banned in ("E:", "repo", "secret", "forest.bin", "\\"):
            self.assertNotIn(banned, result.message,
                             f"player text leaks {banned!r} (F1)")
        # ...while the developer field retains the original (repr escapes the
        # backslashes, so assert on the fragments that identify it):
        raw = result.diagnostic["raw_detail"]
        self.assertIn("E:", raw)
        self.assertIn("forest.bin", raw)

    def test_offense_token_with_embedded_path_is_scrubbed_or_dropped(self):
        detail = r"required key 'C:\Users\allen\hush\keys.json' is missing"
        result = pd.explain_settings_refusal("key_missing", detail)
        for banned in ("C:", "Users", "allen", "hush", "keys.json", "\\"):
            self.assertNotIn(banned, result.message, "F1")
        self.assertIn(detail, result.diagnostic["raw_detail"])

    def test_no_player_string_anywhere_contains_a_path_shape(self):
        banned = re.compile(
            r"([A-Za-z]:\\|\\\\|%[A-Z_]+%|\$\{?[A-Z_]+\}?)")
        for name, result in self._all_player_strings():
            with self.subTest(identity=name):
                self.assertNotIn("\\", result.message, "F1: backslash")
                self.assertIsNone(banned.search(result.message),
                                  f"F1: path shape in {result.message!r}")
                for sentence in result.actions:
                    self.assertNotIn("\\", sentence)
                    self.assertIsNone(banned.search(sentence))
                self.assertNotIn("allen", result.message.lower())

    def test_scrub_direct(self):
        self.assertEqual(pd.scrub(self.PATHY), "ENOENT [removed]")
        self.assertEqual(pd.scrub(r"see C:\Users\allen\notes.txt now"),
                         "see [removed] now")
        self.assertEqual(pd.scrub("%APPDATA% and ${HOME} and $SECRET x"),
                         "[removed] and [removed] and [removed] x")
        self.assertEqual(pd.scrub("clean text"), "clean text")


# ── falsifier F3: unknown is honest, never success, never a known message ────
class UnknownIsHonest(unittest.TestCase):
    def _assert_unknown(self, result: pd.PlayerDiagnostic):
        self.assertFalse(result.ok)                 # NEVER success
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.actions, ())        # no fabricated action
        self.assertIn("Reference:", result.message)
        self.assertTrue(result.correlation_id)

    def test_unknown_refusal_names_are_not_mapped(self):
        for name in ("totally_unknown_code", "loaded", "first_run",
                     "quiesced", "transitions", "restart_path", "dropped",
                     "FLOW_ACTION", ""):
            with self.subTest(name=name):
                self._assert_unknown(pd.explain(name, "detail here"))
                # ...and never silently re-labeled as a known refusal:
                self.assertNotIn(pd.explain(name).status,
                                 ("refused", "dropped", "failed"))

    def test_untranslatable_flow_identities_get_unknown(self):
        # a drop while playing: the pinned module cannot produce it
        self._assert_unknown(pd.explain_flow_drop("key_press", "W",
                                                  state="playing"))
        # a state outside session_flow.STATES
        self._assert_unknown(pd.explain_flow_drop("key_press", "W",
                                                  state="menu"))
        # a flow_action in a state outside the frozen table
        self._assert_unknown(pd.explain_flow_drop("flow_action",
                                                  "dance@bribery"))

    def test_arbitrary_exception_gets_fallback_not_a_guess(self):
        result = pd.explain_exception(ValueError("frobnicator exploded"))
        self._assert_unknown(result)
        self.assertEqual(result.diagnostic["exception_type"], "ValueError")

    def test_unknown_message_carries_the_correlation_id(self):
        result = pd.explain("nope", "d", nonce="n1")
        self.assertIn(result.correlation_id, result.message)


# ── the U06 honesty law: no forbidden capability claims ──────────────────────
class NoForbiddenCapabilityClaims(unittest.TestCase):
    def test_no_message_contains_state_feedback_forbidden_tokens(self):
        tokens = _literal_assignment(STATE_FEEDBACK_SRC,
                                     "FORBIDDEN_CLAIM_TOKENS")
        self.assertTrue(tokens)     # the extraction itself must be real
        samples = [pd.explain(c, SAMPLE_DETAILS[c]) for c in ALL_SETTINGS_CODES]
        samples += [pd.explain_flow_drop(k, "", state=s)
                    for k in ("key_press", "key_release", "mouse",
                              "decision_tick")
                    for s in ("attract", "paused", "exited")]
        samples += [pd.explain_flow_drop("flow_action", "restart@playing"),
                    pd.explain_flow_drop("restart_failed", "x"),
                    pd.explain_flow_drop("exit_failed", "x"),
                    pd.explain("unknown-thing", "x")]
        for result in samples:
            with self.subTest(name=result.name):
                low = (result.message + " " + " ".join(result.actions)).lower()
                for token in tokens:
                    self.assertNotIn(token.lower(), low,
                                     f"claims forbidden capability {token!r}")


# ── determinism: same input -> byte-identical output ─────────────────────────
class Determinism(unittest.TestCase):
    def _sweep(self, nonce: str) -> dict[str, bytes]:
        out = {}
        for code in ALL_SETTINGS_CODES:
            out[code] = pd.explain_settings_refusal(
                code, SAMPLE_DETAILS[code], nonce=nonce).to_json()
        for kind in ("key_press", "key_release", "mouse", "decision_tick"):
            for state in ("attract", "paused", "exited"):
                out[f"{kind}@{state}"] = pd.explain_flow_drop(
                    kind, "d", state=state, nonce=nonce).to_json()
        out["flow_action"] = pd.explain_flow_drop(
            "flow_action", "restart@playing", nonce=nonce).to_json()
        out["restart_failed"] = pd.explain_flow_drop(
            "restart_failed", "boom", nonce=nonce).to_json()
        out["exit_failed"] = pd.explain_flow_drop(
            "exit_failed", "boom", nonce=nonce).to_json()
        out["unknown"] = pd.explain("mystery", "boom",
                                    nonce=nonce).to_json()
        return out

    def test_full_sweep_is_byte_identical_across_runs(self):
        first = self._sweep("nonce-42")
        second = self._sweep("nonce-42")
        self.assertEqual(first, second)

    def test_nonce_changes_ids_deterministically(self):
        a = self._sweep("nonce-A")
        b = self._sweep("nonce-B")
        self.assertEqual(set(a), set(b))
        for key in a:
            id_a = json.loads(a[key])["correlation_id"]
            id_b = json.loads(b[key])["correlation_id"]
            self.assertNotEqual(id_a, id_b)

    def test_to_json_is_stable_canonical_bytes(self):
        result = pd.explain("key_missing", SAMPLE_DETAILS["key_missing"])
        raw = result.to_json()
        self.assertTrue(raw.endswith(b"\n"))
        record = json.loads(raw.decode("utf-8"))
        self.assertEqual(record["ok"], False)
        self.assertEqual(record["name"], "key_missing")
        self.assertEqual(
            set(record.keys()),
            {"name", "status", "ok", "message", "actions",
             "correlation_id", "diagnostic"})


# ── the shape of the record ───────────────────────────────────────────────────
class RecordShape(unittest.TestCase):
    def test_record_is_jsonable_and_complete(self):
        result = pd.explain_settings_refusal(
            "action_unbound", SAMPLE_DETAILS["action_unbound"], nonce="n")
        record = result.to_record()
        json.dumps(record)                      # must not raise
        self.assertEqual(set(record),
                         {"name", "status", "ok", "message", "actions",
                          "correlation_id", "diagnostic"})
        self.assertEqual(record["diagnostic"]["raw_name"], "action_unbound")
        self.assertIn("input_settings.py", record["diagnostic"]["origin"])

    def test_supported_identities_is_complete_and_deterministic(self):
        names = pd.supported_identities()
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(names, pd.supported_identities())
        self.assertEqual(len(names),
                         len(pd.KNOWN_SETTINGS_CODES)     # 20 refusal codes
                         + 5                              # flow_action pairs
                         + 4 * 3                          # drop@state
                         + 2)                             # failed transitions
        self.assertEqual(len(names), 39)

    def test_correlation_id_shape(self):
        cid = pd.correlation_id("code", "detail", "nonce")
        self.assertRegex(cid, r"^[0-9a-f]{16}$")
        self.assertEqual(cid, pd.correlation_id("code", "detail", "nonce"))
        self.assertNotEqual(cid, pd.correlation_id("code", "detail"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
