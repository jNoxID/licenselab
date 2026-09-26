from __future__ import annotations
import base64
import json
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path(__file__).resolve().parent
PUBLIC_KEY_PATH = ROOT / "keys" / "public.pem"

def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

def load_public_key(path: Path = PUBLIC_KEY_PATH) -> Ed25519PublicKey:
    data = path.read_bytes()
    key = serialization.load_pem_public_key(data)
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("La clé publique n'est pas Ed25519.")
    return key

def verify_signature(payload: dict, signature_b64: str, public_key: Ed25519PublicKey) -> bool:
    try:
        sig = base64.b64decode(signature_b64, validate=True)
        public_key.verify(sig, canonical_bytes(payload))
        return True
    except (InvalidSignature, ValueError):
        return False
