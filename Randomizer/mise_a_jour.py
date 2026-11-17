"""
Mise à jour automatique de l'application à partir des Releases GitHub du projet.

1. chercher()   : demande à GitHub la liste des Releases ; renvoie ses infos si elle est plus récente
                  et qu'elle contient l'archive de ce système (…-windows.zip ou …-linux.tar.gz).
2. telecharger(): télécharge l'archive (taille et empreinte SHA-256 vérifiées quand GitHub les donne)
                  et en extrait le programme à côté de l'actuel (« <nom>.nouveau »).
3. remplacer_et_relancer(): met le nouveau programme à la place de l'ancien et le lance.
   Sous Windows, un .exe en cours d'exécution ne peut pas être écrasé mais peut être renommé :
   l'ancien devient « <nom>.ancien », supprimé au démarrage suivant (nettoyer()).

Seule l'adresse publique de l'API GitHub est contactée, sans aucune donnée personnelle.
Variable d'environnement RANDOMIZER_SANS_MAJ=1 : aucune vérification (tests).
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

DEPOT = "Michiy0/RE-HD-Randomizer"
API = f"https://api.github.com/repos/{DEPOT}/releases?per_page=20"
AGENT = "RandomizerREHD-maj"
SOUS_WINDOWS = sys.platform == "win32"
SUFFIXE = "-windows.zip" if SOUS_WINDOWS else "-linux.tar.gz"
HOTES_PERMIS = ("github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com")


def version_vers_tuple(texte):
    """« v0.6.2 » -> (0, 6, 2) ; None si ce n'est pas un numéro de version."""
    m = re.fullmatch(r"v?(\d+(?:\.\d+)*)", (texte or "").strip())
    return tuple(int(x) for x in m.group(1).split(".")) if m else None


def plus_recente(distante, locale):
    a, b = version_vers_tuple(distante), version_vers_tuple(locale)
    if a is None or b is None:
        return False
    n = max(len(a), len(b))
    return a + (0,) * (n - len(a)) > b + (0,) * (n - len(b))


def programme_actuel():
    """Chemin du programme compilé ; None quand on lance le script Python (pas de mise à jour auto)."""
    return Path(sys.executable).resolve() if getattr(sys, "frozen", False) else None


def _ouvrir(url, delai):
    hote = urllib.parse.urlsplit(url).hostname or ""
    if not (url.startswith("https://") and (hote in HOTES_PERMIS or hote == "api.github.com")):
        raise ValueError(f"adresse refusée : {url}")
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/octet-stream"
                                               if "api.github.com" not in url else "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=delai)


def chercher(version_locale, delai=6):
    """Infos de la mise à jour disponible, ou None (à jour, hors ligne, pas d'archive pour ce système…)."""
    if os.environ.get("RANDOMIZER_SANS_MAJ"):
        return None
    try:
        with _ouvrir(API, delai) as r:
            versions = json.load(r)
    except Exception:
        return None
    # les versions de test sont publiées en « pré-version » : on les prend aussi (pas les brouillons)
    candidates = [v for v in versions if isinstance(v, dict) and not v.get("draft")
                  and version_vers_tuple(v.get("tag_name")) and plus_recente(v["tag_name"], version_locale)]
    candidates.sort(key=lambda v: version_vers_tuple(v["tag_name"]), reverse=True)
    for rel in candidates:                     # la plus récente qui a une archive pour ce système
        for a in rel.get("assets", []):
            if a.get("name", "").endswith(SUFFIXE):
                digest = a.get("digest") or ""
                return {"version": rel["tag_name"].lstrip("v"), "page": rel.get("html_url"),
                        "url": a.get("browser_download_url"), "nom": a["name"], "taille": a.get("size"),
                        "sha256": digest[7:].lower() if digest.startswith("sha256:") else None}
    return None


def telecharger(info, cible, progres=lambda fraction: None):
    """Télécharge l'archive, la vérifie et en extrait le programme en « <cible>.nouveau ». Renvoie ce chemin."""
    nouveau = cible.with_name(cible.name + ".nouveau")
    with tempfile.TemporaryDirectory(prefix="randomizer_maj_") as tmp:
        archive = Path(tmp) / info["nom"]
        h = hashlib.sha256()
        with _ouvrir(info["url"], 30) as r, open(archive, "wb") as f:
            total = info.get("taille") or int(r.headers.get("Content-Length") or 0)
            recu = 0
            while True:
                bloc = r.read(1 << 16)
                if not bloc:
                    break
                f.write(bloc)
                h.update(bloc)
                recu += len(bloc)
                if total:
                    progres(min(recu / total, 1.0))
        if info.get("taille") and recu != info["taille"]:
            raise IOError(f"téléchargement incomplet ({recu} / {info['taille']} octets)")
        if info.get("sha256") and h.hexdigest() != info["sha256"]:
            raise IOError("empreinte SHA-256 différente de celle annoncée par GitHub")
        donnees = _extraire(archive)
    nouveau.write_bytes(donnees)
    if not SOUS_WINDOWS:
        os.chmod(nouveau, 0o755)
    return nouveau


def _extraire(archive):
    """Contenu du programme dans l'archive (RandomizerREHD.exe ou RandomizerREHD-linux), à la racine
    ou dans un dossier de premier niveau. Rien n'est écrit sur le disque à partir des noms de l'archive."""
    def bon(nom, attendu):
        parties = nom.replace("\\", "/").lstrip("./").split("/")
        return len(parties) <= 2 and parties[-1] == attendu
    if archive.name.endswith(".zip"):
        with zipfile.ZipFile(archive) as z:
            noms = [n for n in z.namelist() if bon(n, "RandomizerREHD.exe")]
            if len(noms) != 1:
                raise IOError("programme introuvable dans l'archive")
            return z.read(noms[0])
    with tarfile.open(archive, "r:gz") as t:
        membres = [m for m in t.getmembers() if m.isfile() and bon(m.name, "RandomizerREHD-linux")]
        if len(membres) != 1:
            raise IOError("programme introuvable dans l'archive")
        return t.extractfile(membres[0]).read()


def remplacer_et_relancer(nouveau, cible):
    """Met le nouveau programme à la place de l'ancien et le démarre. L'appelant doit ensuite quitter."""
    if SOUS_WINDOWS:
        ancien = cible.with_name(cible.name + ".ancien")
        if ancien.exists():
            ancien.unlink()
        os.replace(cible, ancien)              # permis sur un .exe en cours d'exécution
        try:
            os.replace(nouveau, cible)
        except OSError:
            os.replace(ancien, cible)          # on remet l'ancien en place
            raise
    else:
        os.replace(nouveau, cible)             # permis sous Linux même pendant l'exécution
    env = dict(os.environ)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"  # le nouveau programme ne doit pas réutiliser nos fichiers
    options = {"creationflags": subprocess.DETACHED_PROCESS} if SOUS_WINDOWS else {"start_new_session": True}
    subprocess.Popen([str(cible)], cwd=str(cible.parent), env=env, close_fds=True, **options)


def nettoyer():
    """Supprime l'ancien programme laissé par une mise à jour (au démarrage)."""
    cible = programme_actuel()
    if not cible:
        return
    for suffixe in (".ancien", ".nouveau"):
        p = cible.with_name(cible.name + suffixe)
        for _ in range(20):                    # l'ancien peut mettre un instant à se fermer
            try:
                if p.exists():
                    p.unlink()
                break
            except OSError:
                import time
                time.sleep(0.25)


if __name__ == "__main__":
    print(chercher(sys.argv[1] if len(sys.argv) > 1 else "0.0"))
