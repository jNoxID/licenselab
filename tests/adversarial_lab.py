from __future__ import annotations
import argparse
import base64
import copy
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from licenselab.client.verify_license import verify_document, LicenseError
from licenselab.client.device_id import get_device_id

def save(doc, folder, name):
    p = Path(folder) / name
    p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return p

def expect_rejected(path, app, label, device=None):
    try:
        verify_document(path, app, device_id=device)
        print(f"[ECHEC] {label}: falsification acceptée")
        return False
    except Exception as e:
        print(f"[OK]    {label}: refusée ({e})")
        return True

def main():
    ap = argparse.ArgumentParser(description="Tests non destructifs contre des copies de licence.")
    ap.add_argument("license")
    ap.add_argument("--app", required=True)
    args = ap.parse_args()

    original = json.loads(Path(args.license).read_text(encoding="utf-8"))
    try:
        p = verify_document(args.license, args.app)
        print(f"Licence originale valide: {p['license_id']}")
    except Exception as e:
        print(f"La licence de départ doit être valide sur cette machine: {e}", file=sys.stderr)
        return 2

    results = []
    with tempfile.TemporaryDirectory(prefix="license-lab-") as td:
        d = copy.deepcopy(original)
        d["payload"]["plan"] = "pro" if d["payload"].get("plan") != "pro" else "free"
        results.append(expect_rejected(save(d, td, "tamper_plan.json"), args.app, "Modification du plan"))

        d = copy.deepcopy(original)
        d["payload"]["features"] = sorted(set(d["payload"].get("features", []) + ["forged-premium"]))
        results.append(expect_rejected(save(d, td, "tamper_features.json"), args.app, "Ajout d'une feature"))

        d = copy.deepcopy(original)
        d["payload"]["expires_at"] = "2099-12-31T23:59:59Z"
        results.append(expect_rejected(save(d, td, "tamper_expiry.json"), args.app, "Modification expiration"))

        d = copy.deepcopy(original)
        d["payload"]["device_id"] = "0" * 64
        results.append(expect_rejected(save(d, td, "tamper_device.json"), args.app, "Modification Device ID"))

        d = copy.deepcopy(original)
        raw = bytearray(base64.b64decode(d["signature"]))
        raw[0] ^= 0x01
        d["signature"] = base64.b64encode(bytes(raw)).decode()
        results.append(expect_rejected(save(d, td, "bad_signature.json"), args.app, "Signature corrompue"))

        # Simulation de copie vers une autre machine sans modifier la licence:
        fake_other_device = "f" * 64
        pth = save(copy.deepcopy(original), td, "copied_license.json")
        results.append(expect_rejected(pth, args.app, "Copie vers une autre machine", device=fake_other_device))

    passed = sum(results)
    print(f"\nRésultat: {passed}/{len(results)} tests hostiles refusés comme attendu.")
    return 0 if all(results) else 1

if __name__ == "__main__":
    raise SystemExit(main())
