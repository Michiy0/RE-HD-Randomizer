"""
Prépare une version publiable du projet dans le dossier publication/ :

  publication/depot/                  les fichiers à mettre sur GitHub (et seulement eux)
  publication/RandomizerREHD-v<x>.zip à joindre à une « Release » GitHub ou à envoyer aux testeurs
                                      (RandomizerREHD.exe + LISEZ-MOI.txt)

Seuls les fichiers de la liste FICHIERS sont copiés : sauvegardes, fichiers du jeu, outils de tiers et
seeds générées ne peuvent pas partir par erreur. Le tableur publié n'a pas l'onglet « Vocabulaire Benn ».
L'exe du zip est construit à partir de ces fichiers publiés (donc avec le tableur publié).

    python preparer_publication.py
"""
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "Randomizer"))
from application import VERSION  # noqa: E402

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "publication"
DEPOT = SORTIE / "depot"

# source (dans ce dossier)  ->  destination (dans le dépôt)
FICHIERS = {
    "README.md": "README.md",
    "LICENSE": "LICENSE",
    ".gitignore": ".gitignore",
    "LISEZ-MOI_testeur.txt": "LISEZ-MOI_testeur.txt",
    "preparer_publication.py": "preparer_publication.py",
    "donnees_randomizer_RE1.xlsx": "donnees_randomizer_RE1.xlsx",
    "DLL/randomizer.c": "DLL/randomizer.c",
    "DLL/xinput1_4.def": "DLL/xinput1_4.def",
    "DLL/compiler.bat": "DLL/compiler.bat",
    "DLL/LISEZMOI.md": "DLL/LISEZMOI.md",
    "Randomizer/application.py": "Randomizer/application.py",
    "Randomizer/generateur_seed.py": "Randomizer/generateur_seed.py",
    "Randomizer/creer_icone.py": "Randomizer/creer_icone.py",
    "Randomizer/construire_exe.bat": "Randomizer/construire_exe.bat",
    "Randomizer/icone.ico": "Randomizer/icone.ico",
    "Randomizer/icone.png": "Randomizer/icone.png",
    "Randomizer/appliquer_seed.lua": "outils/cheat_engine/appliquer_seed.lua",
    "journal_objets.lua": "outils/cheat_engine/journal_objets.lua",
    "test_remplacement.lua": "outils/cheat_engine/test_remplacement.lua",
}
ONGLETS_RETIRES = ["Vocabulaire Benn"]


def nettoyer_tableur(chemin):
    from openpyxl import load_workbook
    wb = load_workbook(chemin)          # formules conservées
    for nom in ONGLETS_RETIRES:
        if nom in wb.sheetnames:
            del wb[nom]
    ws = wb["Lisez-moi"]
    for ligne in range(ws.max_row, 0, -1):
        v = ws.cell(ligne, 1).value
        if isinstance(v, str) and any(v.startswith(n) for n in ONGLETS_RETIRES):
            ws.delete_rows(ligne)
    wb.save(chemin)


def construire_exe(depot):
    """Compile la DLL puis l'exe dans une copie temporaire du dépôt (le dépôt reste propre)."""
    with tempfile.TemporaryDirectory(prefix="randomizer_publication_") as tmp:
        copie = Path(tmp) / "depot"
        shutil.copytree(depot, copie)
        for script in ("DLL/compiler.bat", "Randomizer/construire_exe.bat"):
            r = subprocess.run(["cmd", "/c", str(copie / script)], capture_output=True, text=True,
                               encoding="cp850", errors="replace")
            if r.returncode != 0:
                sys.exit(f"Échec de {script} :\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
        exe = SORTIE / "RandomizerREHD.exe"
        shutil.copyfile(copie / "Randomizer" / "dist" / "RandomizerREHD.exe", exe)
        return exe


def main():
    # On vide le dépôt sauf son historique git (.git), pour que les fichiers retirés de la liste
    # disparaissent aussi du dépôt.
    if DEPOT.exists():
        for element in DEPOT.iterdir():
            if element.name == ".git":
                continue
            shutil.rmtree(element) if element.is_dir() else element.unlink()
    for src, dst in FICHIERS.items():
        cible = DEPOT / dst
        cible.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ICI / src, cible)
    nettoyer_tableur(DEPOT / "donnees_randomizer_RE1.xlsx")
    print(f"Dépôt prêt : {DEPOT} ({len(FICHIERS)} fichiers)")

    exe = construire_exe(DEPOT)
    archive = SORTIE / f"RandomizerREHD-v{VERSION}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(exe, "RandomizerREHD.exe")
        z.write(ICI / "LISEZ-MOI_testeur.txt", "LISEZ-MOI.txt")
    exe.unlink()
    print(f"Archive prête : {archive} ({archive.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
