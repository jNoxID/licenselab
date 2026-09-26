# License Lab V2 — Ed25519 / FREE-PRO / Device binding

Laboratoire local pour tester le système de licence de VOS PROPRES applications.
Compatible Windows 11, Kali Linux, Debian et Ubuntu.

## Ce que fait le projet

- Génère une paire Ed25519.
- Garde la clé privée côté "éditeur".
- Génère un Device ID pseudonyme.
- Crée des licences FREE/PRO signées.
- Vérifie signature, expiration, application, Device ID et fonctionnalités.
- Lance une application uniquement si la licence est valide.
- Accepte `.py`, `.sh`, exécutables Linux et `.exe` sous Windows.
- Contient un banc de tests "hostile" NON destructif qui falsifie des COPIES de licences
  afin de vérifier que les altérations sont détectées.
- Ne patche/modifie pas les exécutables.

## 1 — Installation Linux (Kali/Debian/Ubuntu)

```bash
sudo apt update
sudo apt install -y python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 2 — Installation Windows 11 / Git Bash

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3 — Initialisation

```bash
python issuer/license_tool.py init
python client/device_id.py
```

Copiez le Device ID affiché.

## 4 — Créer une licence PRO

Linux/macOS :

```bash
DEVICE_ID="$(python client/device_id.py)"
python issuer/license_tool.py create --app demo --plan pro --days 30 --device "$DEVICE_ID"
```

Windows/Git Bash :

```bash
DEVICE_ID="$(python client/device_id.py)"
python issuer/license_tool.py create --app demo --plan pro --days 30 --device "$DEVICE_ID"
```

Le chemin du fichier de licence est affiché.

## 5 — Vérifier

```bash
python client/verify_license.py licenses/LIC-XXXXXXXX.json --app demo
```

## 6 — Tester l'application Python fournie

```bash
python client/launcher.py examples/demo_app.py --license licenses/LIC-XXXXXXXX.json --app demo
```

## 7 — Banc de tests "attaquant"

Ce script ne touche PAS à votre programme. Il fabrique des copies falsifiées de la licence :
plan FREE -> PRO, expiration, Device ID, feature ajoutée, payload modifié, signature corrompue.

```bash
python tests/adversarial_lab.py licenses/LIC-XXXXXXXX.json --app demo
```

Chaque falsification doit être REFUSÉE.

## 8 — Tester votre propre programme

Windows :

```bash
python client/launcher.py "C:/MesApps/MonApp.exe" --license licenses/LIC-XXXXXXXX.json --app MonApp
```

Linux :

```bash
python client/launcher.py "/opt/monapp/monapp" --license licenses/LIC-XXXXXXXX.json --app MonApp
```

Python :

```bash
python client/launcher.py "./mon_app.py" --license licenses/LIC-XXXXXXXX.json --app MonApp
```

## Architecture de sécurité

`keys/private.pem` est le secret de signature. Ne le distribuez jamais.
`keys/public.pem` est destiné au client.

Une protection par launcher n'empêche pas quelqu'un de lancer directement un EXE autonome.
Pour une application de production, faites dépendre les fonctions Premium de la validation
dans votre propre code et, pour les actifs réellement sensibles, privilégiez une autorisation
ou un service côté serveur.

## Test sur deux VM

VM A (éditeur):

- `issuer/`
- `keys/private.pem`
- création des licences

VM B (client hostile):

- votre application
- `client/`
- `keys/public.pem`
- licence signée

Ne copiez jamais `private.pem` sur la VM cliente.

## Correctif de livraison V2.1

Le launcher accepte les options après le chemin cible, comme dans les exemples.
Les arguments propres à l'application doivent suivre `--` :

```bash
python client/launcher.py examples/demo_app.py --license licenses/LIC-XXXXXXXX.json --app demo -- --option-cible valeur
```

Remplacez `LIC-XXXXXXXX.json` par le nom réellement affiché lors de la création.
Pour lancer MonApp, créez d'abord une licence avec `--app MonApp`.
Python 3.10 ou supérieur est requis. Les dépendances ne sont pas embarquées :
`pip install -r requirements.txt` nécessite un accès à une source de paquets.
Les dossiers `keys/` et `licenses/` sont initialement vides : créez vos propres clés.

### Vérification automatique complète

```bash
python tests/integration_test.py
```

Ce test travaille dans une copie temporaire du projet, génère ses propres clés,
teste FREE/PRO, les droits Premium, l'expiration et le lancement,
puis exécute les six scénarios de falsification. Il ne remplace pas vos clés.

### Limites

Le Device ID est une empreinte de laboratoire, pas une attestation matérielle.
Une VM clonée peut conserver les mêmes identifiants. La date repose sur
l'horloge locale : le laboratoire ne protège pas contre son recul ni contre
la modification du code client ou le remplacement de sa clé publique.
Le test « autre machine » simule une empreinte différente ; il ne crée pas de VM.
Les tests ont été exécutés sous Linux ; Windows 11 doit être validé sur votre VM.

### Empreinte machine V2.1

L'empreinte utilise maintenant MachineGuid sous Windows et machine-id sous Linux.
À défaut, un identifiant persiste dans `~/.license-lab/device-id` pour le compte courant.
Le calcul change par rapport à V2 : régénérez les licences avec le nouveau Device ID.
Ne supprimez pas cet identifiant de secours si vous souhaitez conserver vos licences.
