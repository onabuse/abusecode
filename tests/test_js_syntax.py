import shutil
import subprocess
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parents[1] / "static" / "js"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
@pytest.mark.parametrize("script", sorted(JS_DIR.glob("*.js")), ids=lambda p: p.name)
def test_js_module_syntax(script):
    """Catch parse errors that would silently disable every UI handler."""
    proc = subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=script.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
    )
    assert proc.returncode == 0, f"{script.name}:\n{proc.stderr}"
