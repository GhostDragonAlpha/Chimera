import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parent
LAUNCHER = ROOT.parent / "bionic.cmd"


@unittest.skipUnless(os.name == "nt", "Windows batch launcher")
class BionicLauncherTests(unittest.TestCase):
    def invoke(self, model_arg=None, env_model=None):
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            shutil.copy2(LAUNCHER, work / "bionic.cmd")
            capture = work / "captured.txt"
            (work / "pi-lmstudio.bat").write_text(
                "@echo off\r\nsetlocal\r\n>\"%~dp0captured.txt\" echo %*\r\nexit /b 0\r\n",
                encoding="utf-8",
            )
            command = ["cmd.exe", "/d", "/c", str(work / "bionic.cmd"), "session-7", "do work"]
            if model_arg is not None:
                command.append(model_arg)
            env = os.environ.copy()
            if env_model is None:
                env.pop("BIONIC_MODEL", None)
            else:
                env["BIONIC_MODEL"] = env_model
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            return capture.read_text(encoding="utf-8").strip()

    def test_explicit_requested_model_is_forwarded(self):
        args = self.invoke("model-explicit", "model-env")
        self.assertIn('-Model "model-explicit"', args)
        self.assertNotIn("model-env", args)
        self.assertIn('--session-id "session-7"', args)

    def test_environment_requested_model_is_forwarded(self):
        args = self.invoke(env_model="model-env")
        self.assertIn('-Model "model-env"', args)

    def test_no_request_uses_lm_studio_loaded_default(self):
        args = self.invoke()
        self.assertNotIn("-Model", args)
        self.assertIn('--session-id "session-7"', args)

    def test_hardcoded_legacy_model_is_gone(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertNotIn("bartowski/qwen3.8-27b", source)
        self.assertIn("pi-lmstudio.bat", source)


if __name__ == "__main__":
    unittest.main()
