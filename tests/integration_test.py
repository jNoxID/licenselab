"""Scénario réel dans une copie temporaire, sans toucher aux clés utilisateur."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    with tempfile.TemporaryDirectory(prefix="license-integration-") as tmp:
        root = Path(tmp) / "lab"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(
            "keys", "licenses", ".venv", "__pycache__", "*.pyc"))

        def run(*args, expected=0):
            result = subprocess.run([sys.executable, *args], cwd=root,
                                    text=True, capture_output=True)
            if result.returncode != expected:
                raise AssertionError(f"{args}: code {result.returncode}\n"
                                     f"{result.stdout}\n{result.stderr}")
            return result.stdout.strip()

        run("issuer/license_tool.py", "init")
        device = run("client/device_id.py")
        for plan in ("free", "pro"):
            license_path = run("issuer/license_tool.py", "create", "--app", "demo",
                               "--plan", plan, "--days", "30", "--device", device)
            run("client/verify_license.py", license_path, "--app", "demo")
            run("client/verify_license.py", license_path, "--app", "other", expected=1)
            run("client/verify_license.py", license_path, "--app", "demo",
                "--feature", "premium", expected=0 if plan == "pro" else 1)
            run("client/launcher.py", "examples/demo_app.py", "--license",
                license_path, "--app", "demo")
            # Vérifie que les options de la cible restent distinctes de celles du launcher.
            target = root / "examples" / "check_args.py"
            target.write_text("import sys\nassert sys.argv[1:] == ['--app', 'target']\n")
            run("client/launcher.py", str(target), "--license", license_path,
                "--app", "demo", "--", "--app", "target")
            code = '''import sys
from datetime import timedelta
from client.verify_license import verify_document, parse_time, LicenseError
p = verify_document(sys.argv[1], 'demo')
for now in (parse_time(p['expires_at']), parse_time(p['issued_at']) - timedelta(seconds=1)):
    try:
        verify_document(sys.argv[1], 'demo', now=now)
    except LicenseError:
        continue
    raise AssertionError('Date invalide acceptée')
'''
            run("-c", code, license_path)
            print(f"[OK] {plan.upper()}: validation, droits, dates, application et launcher")
            print(run("tests/adversarial_lab.py", license_path, "--app", "demo"))
        run("tests/self_test.py")
        print("[OK] Tous les tests d'intégration ont réussi.")


if __name__ == "__main__":
    main()
