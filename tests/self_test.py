from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
commands = [
    [sys.executable, str(ROOT/"issuer/license_tool.py"), "--help"],
    [sys.executable, str(ROOT/"client/verify_license.py"), "--help"],
    [sys.executable, str(ROOT/"client/launcher.py"), "--help"],
    [sys.executable, str(ROOT/"tests/adversarial_lab.py"), "--help"],
]
for c in commands:
    r = subprocess.run(c)
    if r.returncode:
        raise SystemExit(r.returncode)
print("Self-test CLI: OK")
