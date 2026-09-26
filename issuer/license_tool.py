from __future__ import annotations
import argparse
import base64
import json
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from cryptography.hazmat.primitives import serialization  # type: ignore[import-not-found]
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Le paquet 'cryptography' est requis. Installez-le avec: pip install cryptography"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from licenselab.common import canonical_bytes

KEYS = ROOT / "keys"
LICENSES = ROOT / "licenses"
PRIVATE = KEYS / "private.pem"
PUBLIC = KEYS / "public.pem"

def utcnow():
    return datetime.now(timezone.utc)

def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def init_keys(force=False):
    KEYS.mkdir(exist_ok=True)
    if (PRIVATE.exists() or PUBLIC.exists()) and not force:
        raise SystemExit("Clés déjà présentes. Utilisez --force uniquement pour un nouveau laboratoire.")
    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    PRIVATE.write_bytes(private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    PUBLIC.write_bytes(public.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    try:
        PRIVATE.chmod(0o600)
    except OSError:
        pass
    print(f"Clé privée : {PRIVATE}")
    print(f"Clé publique: {PUBLIC}")
    print("IMPORTANT: ne distribuez jamais private.pem.")

def load_private():
    if not PRIVATE.exists():
        raise SystemExit("Clé privée absente. Lancez d'abord: python issuer/license_tool.py init")
    key = serialization.load_pem_private_key(PRIVATE.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("La clé privée n'est pas Ed25519.")
    return key

def create_license(args):
    if args.days <= 0:
        raise SystemExit("--days doit être > 0.")
    now = utcnow()
    license_id = "LIC-" + secrets.token_hex(6).upper()
    default_features = {
        "free": ["basic"],
        "pro": ["basic", "premium", "export", "advanced"],
    }
    features = args.feature or default_features[args.plan]
    payload = {
        "schema": 1,
        "license_id": license_id,
        "app": args.app,
        "plan": args.plan,
        "features": sorted(set(features)),
        "device_id": args.device,
        "issued_at": iso(now),
        "expires_at": iso(now + timedelta(days=args.days)),
    }
    signature = load_private().sign(canonical_bytes(payload))
    doc = {
        "payload": payload,
        "signature": base64.b64encode(signature).decode("ascii"),
        "algorithm": "Ed25519",
    }
    LICENSES.mkdir(exist_ok=True)
    out = LICENSES / f"{license_id}.json"
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)

def show(args):
    p = Path(args.file)
    print(json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2, ensure_ascii=False))

def main():
    ap = argparse.ArgumentParser(description="Outil éditeur de licences Ed25519.")
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init", help="Générer les clés Ed25519.")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=lambda a: init_keys(a.force))

    p = sp.add_parser("create", help="Créer une licence signée.")
    p.add_argument("--app", required=True)
    p.add_argument("--plan", choices=["free", "pro"], default="pro")
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--device", required=True)
    p.add_argument("--feature", action="append", help="Répétable. Remplace les features par défaut.")
    p.set_defaults(func=create_license)

    p = sp.add_parser("show", help="Afficher une licence.")
    p.add_argument("file")
    p.set_defaults(func=show)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
