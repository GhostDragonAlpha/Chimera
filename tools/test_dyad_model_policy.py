"""CPU-only falsifiers for the permanent DYAD model policy.

All LM Studio metadata and inference transports are mocked. No model is loaded,
evicted, reconfigured, or called by this module.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "ChimeraEngine"
if str(ENGINE) not in sys.path:
    sys.path.insert(0, str(ENGINE))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import senses  # noqa: E402
from tools import dyad_model as cli  # noqa: E402


MODEL_ID = "qwen3.8-27b-nvfp4-mtp"
MODEL_PATH = (
    "esatapedico/Qwen3.8-27B-NVFP4-MTP-GGUF/"
    "Qwen3.8-27B-NVFP4-MTP-VERY-LOW.gguf"
)


class _Response:
    def __init__(self, payload):
        self._data = json.dumps(payload).encode("utf-8")
        self.status = 200

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _Gateway:
    def __init__(self, response_model=MODEL_ID, include_model=True):
        self.ADOPT_RESIDENT = True
        self.calls = []
        self.response_model = response_model
        self.include_model = include_model

    def lm_urlopen(self, req, timeout, agent):
        body = json.loads(req.data)
        self.calls.append(
            {
                "body": body,
                "timeout": timeout,
                "agent": agent,
                "adopt_resident": self.ADOPT_RESIDENT,
            }
        )
        payload = {
            "choices": [
                {"message": {"content": "seen"}, "finish_reason": "stop"}
            ]
        }
        if self.include_model:
            payload["model"] = self.response_model
        return _Response(payload)


def _policy(model_id=MODEL_ID):
    return {
        "schema": "chimera-dyad-model-policy-v1",
        "mode": "fixed",
        "model_id": model_id,
        "model_relative_path": MODEL_PATH,
    }


class PermanentDyadPolicyTests(unittest.TestCase):
    def setUp(self):
        senses._SERVED = None
        senses._FINISH = None
        senses._ACTIVE_MODEL = None

    def assertReason(self, reason, call):
        with self.assertRaises(senses.DyadModelFailure) as caught:
            call()
        self.assertEqual(caught.exception.reason, reason)

    def test_checked_in_policy_is_exact_and_independent_of_saved_or_env(self):
        policy = senses._dyad_policy()
        self.assertEqual(policy, _policy())
        self.assertEqual(senses.VISION_BACKEND, "lmstudio")

        with tempfile.TemporaryDirectory() as td:
            stale_saved = Path(td) / "Saved" / "dyad_model.txt"
            stale_saved.parent.mkdir()
            stale_saved.write_text("wrong-loaded-model\n", encoding="utf-8")
            # The old attribute and environment values are deliberate adversarial
            # inputs. Neither is part of the permanent selection path.
            with mock.patch.object(senses, "_DYAD_MODEL_FILE", stale_saved, create=True), \
                    mock.patch.dict(
                        os.environ,
                        {
                            "CHIMERA_SENSES_MODEL": "wrong-env-model",
                            "CHIMERA_VISION_BACKEND": "ollama",
                        },
                    ):
                self.assertEqual(senses.dyad_model(), MODEL_ID)
                self.assertEqual(senses.VISION_BACKEND, "lmstudio")

    def test_policy_is_read_fresh_on_every_call(self):
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "dyad_model_policy.json"
            policy_path.write_text(json.dumps(_policy()), encoding="utf-8")
            with mock.patch.object(senses, "_DYAD_POLICY_FILE", policy_path):
                self.assertEqual(senses.dyad_model(), MODEL_ID)
                changed = _policy("operator-changed-policy")
                policy_path.write_text(json.dumps(changed), encoding="utf-8")
                self.assertEqual(senses.dyad_model(), "operator-changed-policy")

    def test_wrong_resident_cannot_retarget_permanent_dyad_request(self):
        gateway = _Gateway()
        with mock.patch.object(senses, "_loaded_model_ids",
                               return_value=["wrong-loaded-model", MODEL_ID]), \
                mock.patch.object(senses, "_lm_gateway", return_value=gateway):
            answer = senses._post_lmstudio(
                [{"type": "text", "text": "probe"}],
                timeout=None,
                temperature=0.2,
                max_tokens=17,
            )
        self.assertEqual(answer, "seen")
        self.assertEqual(len(gateway.calls), 1)
        call = gateway.calls[0]
        self.assertEqual(call["body"]["model"], MODEL_ID)
        self.assertFalse(call["adopt_resident"])
        self.assertIsNone(call["timeout"])
        self.assertEqual(call["agent"], "senses")
        self.assertEqual(senses._last_served_model(), MODEL_ID)
        self.assertEqual(senses.last_finish_reason(), "stop")

    def test_required_model_missing_rejects_before_transport_and_clears_stale_identity(self):
        senses._SERVED = "stale-model"
        senses._FINISH = "stale-finish"
        gateway = _Gateway()
        with mock.patch.object(senses, "_loaded_model_ids",
                               return_value=["wrong-loaded-model"]), \
                mock.patch.object(senses, "_lm_gateway", return_value=gateway):
            self.assertReason(
                senses.DyadModelReason.REQUIRED_MODEL_NOT_LOADED,
                lambda: senses._post_lmstudio([], None, 0.2, 17),
            )
        self.assertEqual(gateway.calls, [])
        self.assertIsNone(senses._last_served_model())
        self.assertIsNone(senses.last_finish_reason())

    def test_wrong_or_missing_response_identity_is_rejected_without_stale_proof(self):
        for gateway, reason in (
            (_Gateway(response_model="wrong-served-model"),
             senses.DyadModelReason.RESPONSE_MODEL_WRONG),
            (_Gateway(include_model=False),
             senses.DyadModelReason.RESPONSE_MODEL_MISSING),
        ):
            with self.subTest(reason=reason):
                senses._SERVED = "stale-model"
                senses._FINISH = "stale-finish"
                with mock.patch.object(senses, "_loaded_model_ids",
                                       return_value=[MODEL_ID]), \
                        mock.patch.object(senses, "_lm_gateway", return_value=gateway):
                    self.assertReason(
                        reason,
                        lambda: senses._post_lmstudio([], None, 0.2, 17),
                    )
                self.assertIsNone(senses._last_served_model())
                self.assertIsNone(senses.last_finish_reason())

    def test_resident_model_never_falls_back_to_on_disk_and_reports_ambiguity(self):
        cases = (
            ([{"id": MODEL_ID, "state": "not-loaded"}], None),
            ([{"id": MODEL_ID}], None),
            ([{"id": MODEL_ID, "state": "loaded"}], MODEL_ID),
            ([{"id": MODEL_ID, "state": "loaded"},
              {"id": "other", "state": "loaded"}], None),
        )
        for records, expected in cases:
            with self.subTest(records=records):
                with mock.patch.object(
                    senses.urllib.request,
                    "urlopen",
                    return_value=_Response({"data": records}),
                ):
                    self.assertEqual(senses.resident_model(), expected)

    def test_available_and_can_see_name_missing_policy_model_without_inference(self):
        with mock.patch.object(senses, "_loaded_model_ids",
                               return_value=["wrong-loaded-model"]), \
                mock.patch.object(senses, "_post") as post:
            self.assertFalse(senses.available())
            ok, served, reason = senses.can_see()
        self.assertFalse(ok)
        self.assertIsNone(served)
        self.assertIn(senses.DyadModelReason.REQUIRED_MODEL_NOT_LOADED, reason)
        post.assert_not_called()

    def test_non_lmstudio_backend_override_is_named_refusal_and_clears_identity(self):
        senses._SERVED = "stale-model"
        senses._FINISH = "stale-finish"
        with mock.patch.dict(os.environ, {"CHIMERA_VISION_BACKEND": "ollama"}), \
                mock.patch.object(senses, "_post_lmstudio") as post:
            self.assertReason(
                senses.DyadModelReason.BACKEND_FORBIDDEN,
                lambda: senses._post([], None),
            )
        post.assert_not_called()
        self.assertIsNone(senses._last_served_model())
        self.assertIsNone(senses.last_finish_reason())

    def test_ensure_eye_never_loads_or_reconfigures(self):
        with mock.patch.object(senses, "_loaded_model_ids", return_value=[]), \
                mock.patch.dict(sys.modules, {"eye_control": mock.Mock()}):
            self.assertFalse(senses.ensure_eye())
            sys.modules["eye_control"].load.assert_not_called()

    def test_private_gateway_change_does_not_mutate_non_dyad_gateway(self):
        with mock.patch.dict(os.environ, {"CHIMERA_LM_ADOPT": "1"}):
            non_dyad_gateway = senses._lm_gateway()
        self.assertTrue(non_dyad_gateway.ADOPT_RESIDENT)
        dyad_gateway = _Gateway()
        with mock.patch.object(senses, "_loaded_model_ids", return_value=[MODEL_ID]), \
                mock.patch.object(senses, "_lm_gateway", return_value=dyad_gateway):
            senses._post_lmstudio([], None, 0.2, 17)
        self.assertFalse(dyad_gateway.ADOPT_RESIDENT)
        self.assertTrue(non_dyad_gateway.ADOPT_RESIDENT)

    def test_one_image_wall_remains_enforced(self):
        image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}
        senses._enforce_image_wall([image])
        with self.assertRaises(ValueError):
            senses._enforce_image_wall([image, image])

    def test_runtime_setter_and_cli_refuse_alternatives_without_writing_saved(self):
        self.assertReason(
            senses.DyadModelReason.POLICY_PERMANENT,
            lambda: senses.set_dyad_model("auto"),
        )
        with tempfile.TemporaryDirectory() as td:
            policy_path = Path(td) / "dyad_model_policy.json"
            policy_path.write_text(json.dumps(_policy()), encoding="utf-8")
            saved = Path(td) / "Saved" / "dyad_model.txt"
            stdout = io.StringIO()
            with mock.patch.object(cli, "POLICY", policy_path), \
                    mock.patch.object(cli, "loaded_ids", return_value=[MODEL_ID]), \
                    mock.patch("sys.stdout", stdout):
                self.assertEqual(cli.main(["auto"]), 2)
                self.assertEqual(cli.main(["wrong-model"]), 2)
                self.assertEqual(cli.main([MODEL_ID]), 0)
            self.assertFalse(saved.exists())
            self.assertIn("dyad_model_policy_permanent", stdout.getvalue())
            self.assertIn("no file was written", stdout.getvalue())

    def test_invalid_or_missing_policy_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "policy.json"
            with mock.patch.object(senses, "_DYAD_POLICY_FILE", path):
                self.assertReason(
                    senses.DyadModelReason.POLICY_MISSING, senses.dyad_model
                )
                path.write_text(json.dumps({"mode": "auto"}), encoding="utf-8")
                self.assertReason(
                    senses.DyadModelReason.POLICY_INVALID, senses.dyad_model
                )


if __name__ == "__main__":
    unittest.main()
