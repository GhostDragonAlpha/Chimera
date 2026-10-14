"""The served page script must parse as JavaScript (audit lesson 2026-09-28).

DEFECT-1 on master a2effe9a: two stray lines (`next();` / `}`) were left after
`pace()` in the PAGE template (blame 762995aa). The browser's
`new Function(script.textContent)` then threw ``SyntaxError: Unexpected token
'function'``, so NOTHING page-level ran: no honesty banner (state()), no
tick()/tickGlass() frame polling, no drag-orbit/wheel/keyboard bindings, no
pose/WALK/capture handlers - while the server API answered honestly the whole
time. This check pins every <script> block of the served PAGE template to a
real JS-engine parse (node on PATH; skipped when node is absent).
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.product_viewer.server import PAGE

_PARSE_SNIPPET = (
    "const fs=require('fs');"
    "try{new Function(fs.readFileSync(process.argv[1],'utf8'));"
    "console.log('PARSE OK');}"
    "catch(e){console.error(e.constructor.name+': '+e.message);process.exit(1);}"
)


def js_parses(script_text: str) -> tuple[bool, str]:
    """Parse script_text exactly like the page does: new Function(body)."""
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node not on PATH")
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8",
                                     delete=False) as f:
        f.write(script_text)
        path = f.name
    try:
        p = subprocess.run([node, "-e", _PARSE_SNIPPET, path],
                           capture_output=True, text=True, timeout=60)
        return p.returncode == 0, (p.stdout + p.stderr).strip()
    finally:
        Path(path).unlink(missing_ok=True)


class PageScriptParses(unittest.TestCase):
    def test_check_catches_bad_script(self):
        # Negative control: the parse check must be able to FAIL, otherwise a
        # green run proves nothing (the defect shipped green for weeks).
        ok, detail = js_parses("next();\n}")
        self.assertFalse(ok)
        self.assertIn("SyntaxError", detail)

    def test_every_script_block_in_page_parses(self):
        scripts = re.findall(r"<script>(.*?)</script>", PAGE, re.S)
        self.assertTrue(scripts, "PAGE template lost its <script> block")
        for i, js in enumerate(scripts):
            with self.subTest(script=i):
                ok, detail = js_parses(js)
                self.assertTrue(
                    ok,
                    f"served page script {i} fails new Function parse: {detail}")


if __name__ == "__main__":
    unittest.main()
