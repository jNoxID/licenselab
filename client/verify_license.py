from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from licenselab.common import load_public_key, verify_signature
from licenselab.client.device_id import get_device_id

class LicenseError(Exception):
    pass

def parse_time(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def verify_document(path: str | Path, expected_app: str, required_feature: str | None = None,
                    device_id: str | None = None, now: datetime | None = None) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = doc.get("payload")
    signature = doc.get("signature")
    if not isinstance(payload, dict) or not isinstance(signature, str):
        raise LicenseError("Format de licence invalide.")
    if doc.get("algorithm") != "Ed25519":
        raise LicenseError("Algorithme non autorisé.")
    if not verify_signature(payload, signature, load_public_key()):
        raise LicenseError("Signature cryptographique invalide.")
    if payload.get("schema") != 1:
        raise LicenseError("Version de licence non prise en charge.")
    if payload.get("app") != expected_app:
        raise LicenseError("Licence prévue pour une autre application.")
    current_device = device_id or get_device_id()
    if payload.get("device_id") != current_device:
        raise LicenseError("Licence associée à une autre machine.")
    current = now or datetime.now(timezone.utc)
    try:
        issued = parse_time(payload["issued_at"])
        expires = parse_time(payload["expires_at"])
    except (KeyError, ValueError):
        raise LicenseError("Dates de licence invalides.")
    if current < issued:
        raise LicenseError("Licence pas encore valide / horloge incohérente.")
    if current >= expires:
        raise LicenseError("Licence expirée.")
    if payload.get("plan") not in {"free", "pro"}:
        raise LicenseError("Plan inconnu.")
    features = payload.get("features")
    if not isinstance(features, list) or not all(isinstance(x, str) for x in features):
        raise LicenseError("Liste de fonctionnalités invalide.")
    if required_feature and required_feature not in features:
        raise LicenseError(f"Fonctionnalité absente: {required_feature}")
    return payload

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("license")
    ap.add_argument("--app", required=True)
    ap.add_argument("--feature")
    args = ap.parse_args()
    try:
        p = verify_document(args.license, args.app, args.feature)
        print(f"OK - {p['license_id']} - plan={p['plan']} - expire={p['expires_at']}")
        return 0
    except (LicenseError, OSError, json.JSONDecodeError) as e:
        print(f"REFUSÉ - {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
