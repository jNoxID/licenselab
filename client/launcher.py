from __future__ import annotations
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from licenselab.client.verify_license import verify_document, LicenseError

def command_for(target: Path, extra: list[str]) -> list[str]:
    suffix = target.suffix.lower()
    if suffix == ".py":
        return [sys.executable, str(target), *extra]
    if suffix == ".sh":
        if os.name == "nt":
            raise RuntimeError(".sh nécessite Bash/WSL sous Windows.")
        return ["bash", str(target), *extra]
    if suffix == ".exe":
        if os.name != "nt":
            raise RuntimeError("Un .exe Windows n'est pas exécuté nativement sur Linux. Testez-le dans une VM Windows.")
        return [str(target), *extra]
    if os.name != "nt" and os.access(target, os.X_OK):
        return [str(target), *extra]
    raise RuntimeError("Type de programme non reconnu ou fichier non exécutable.")

def main():
    ap = argparse.ArgumentParser(description="Launcher sous licence pour vos propres applications.")
    ap.add_argument("target")
    ap.add_argument("--license", required=True)
    ap.add_argument("--app", required=True)
    ap.add_argument("--feature", default="basic")
    # Les arguments du programme cible suivent un séparateur explicite --.
    argv = sys.argv[1:]
    if "--" in argv:
        separator = argv.index("--")
        launcher_args, target_args = argv[:separator], argv[separator + 1:]
    else:
        launcher_args, target_args = argv, []
    a = ap.parse_args(launcher_args)
    a.args = target_args

    target = Path(a.target).expanduser().resolve()
    if not target.is_file():
        print("Programme introuvable.", file=sys.stderr)
        return 2
    try:
        payload = verify_document(a.license, a.app, a.feature)
    except Exception as e:
        print(f"Licence refusée: {e}", file=sys.stderr)
        return 3

    print(f"Licence OK: {payload['license_id']} / {payload['plan']}")
    try:
        cp = subprocess.run(command_for(target, a.args), cwd=str(target.parent))
        return cp.returncode
    except (OSError, RuntimeError) as e:
        print(f"Échec du lancement: {e}", file=sys.stderr)
        return 4

if __name__ == "__main__":
    raise SystemExit(main())
