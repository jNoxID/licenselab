"""Empreinte locale de laboratoire (ne constitue pas une attestation matérielle)."""
from __future__ import annotations
import hashlib
import os
import platform
from pathlib import Path
import uuid


def machine_token() -> str:
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
                value = winreg.QueryValueEx(key, "MachineGuid")[0]
                if isinstance(value, str) and value.strip():
                    return "windows:" + value.strip()
        except OSError:
            pass
    else:
        for filename in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                value = Path(filename).read_text().strip()
                if value:
                    return "linux:" + value
            except OSError:
                pass
    # Certaines VM/conteneurs n'ont ni identifiant système ni adresse MAC stable.
    # Le secours est alors propre au compte utilisateur et persiste entre processus.
    folder = Path.home() / ".license-lab"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / "device-id"
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        with os.fdopen(fd, "w") as output:
            output.write(str(uuid.uuid4()))
    value = path.read_text().strip()
    if not value:
        raise RuntimeError("Identifiant local vide ; restaurez le fichier device-id.")
    return "account:" + value


def get_device_id() -> str:
    raw = "license-lab-v2|" + platform.system() + "|" + machine_token()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print(get_device_id())
