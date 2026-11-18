#!/usr/bin/env python3
"""
Générateur de seeds (version 0.2) pour le randomizer Resident Evil HD Remaster (Chris, Normal).

Ce que fait cette version :
  - lit les emplacements relevés dans donnees_randomizer_RE1.xlsx (onglet « Emplacements »),
  - mélange entre eux les objets "libres" (chargeur, herbe verte, ruban encreur, trousse de premiers
    secours, poignard), en échangeant les paires (identifiant, quantité),
  - OPTION --armes-aleatoires : le pistolet entre aussi dans le mélange (Chris ne commence qu'avec son
    couteau, il devra trouver son arme à un emplacement quelconque) ; sans cette option il reste dans le hall,
  - laisse toutes les clés, objets inconnus et objets spéciaux à leur place d'origine,
  - écrit trois fichiers :
        seed_<graine>.json / .lua   (ce que lisent les programmes qui s'accrochent au jeu)
        seed_<graine>_spoiler.txt   (la liste lisible : pièce, objet d'origine, nouvel objet)
    Avec --armes-aleatoires, les noms de fichiers portent le suffixe "_armes".

Pourquoi les clés ne bougent pas : les cinq vieilles clés sont identiques entre elles, les mélanger
entre leurs propres emplacements ne changerait rien, et les déplacer ailleurs demande de savoir quelles
pièces sont accessibles avec quoi (la logique des verrous, pas encore écrite).

Utilisation :
    python generateur_seed.py                          (graine tirée au hasard)
    python generateur_seed.py 12345                    (graine choisie : même graine = même résultat)
    python generateur_seed.py 12345 --armes-aleatoires (le pistolet est aussi mélangé)
    python generateur_seed.py 12345 --fichier mon_fichier.xlsx
    python generateur_seed.py 12345 --installer        (copie aussi la seed dans le dossier du jeu,
                                                        sous le nom randomizer_seed.lua lu par la DLL)
    python generateur_seed.py 12345 --installer --dossier-jeu "D:\\Jeux\\RE HD"
                                                       (si le jeu n'est pas trouvé automatiquement)

Il faut Python 3 et la bibliothèque openpyxl (pip install openpyxl).
"""
import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parent))   # textes.py, même avec python -I
from textes import tr  # noqa: E402

FICHIER_PAR_DEFAUT = "donnees_randomizer_RE1.xlsx"

NOMS_OBJETS = {
    3: "Pistolet",
    6: "Fusil",
    17: "Chargeur de pistolet",
    34: "Herbe verte",
    68: "Ruban encreur",
    101: "Trousse de premiers secours",
    112: "Poignard",
}
# Objets toujours mélangés sans risque
IDS_LIBRES_DE_BASE = {17, 34, 68, 101, 112}
# Armes de base du jeu : mélangées seulement avec l'option --armes-aleatoires.
# (clé du nom dans textes.py, id dans le jeu ou None s'il n'est pas encore relevé, personnage ou None = les deux)
ARMES = [
    ("arme_pistolet", 3, None),
    ("arme_fusil_pompe", 6, None),          # salon (116), x6 : récompense de l'énigme du piège, pas un objet de quête
    ("arme_fusil_assaut", None, None),
    ("arme_lance_grenades", None, "Jill"),
    ("arme_lance_flammes", None, "Chris"),
    ("arme_autodefense", None, None),
    ("arme_lance_roquettes", None, None),   # celui de la fin du jeu (une seule roquette), pas le bonus illimité
    ("arme_magnums", None, None),
]
IDS_ARMES = {i for _, i, _ in ARMES if i is not None}

MOTIF_EMPREINTE = re.compile(r"brut \+0x10\.\.\+0x2C = ((?:[0-9A-Fa-f]{8}\s*){8})")


def lire_emplacements(chemin, personnage="Chris", difficulte="Normal"):
    wb = load_workbook(chemin, data_only=True)
    # Noms des pièces lus directement dans l'onglet « Pièces » : la colonne « Pièce » d'Emplacements est
    # une formule, dont le résultat peut manquer si le fichier a été enregistré par un autre programme.
    noms_pieces = {}
    if "Pièces" in wb.sheetnames:
        for ident, _, _, nom, *_ in wb["Pièces"].iter_rows(min_row=2, values_only=True):
            if ident is not None and nom:
                noms_pieces[str(ident).lower()] = nom
    ws = wb["Emplacements"]
    emplacements, ignores = [], []
    for ligne in ws.iter_rows(min_row=2, values_only=True):
        (_, piece, nom_piece, desc, ident, nom_obj, qte, chemin_ramassage,
         verrou, statut, empreinte, remarque, perso, diff) = (list(ligne) + [None] * 14)[:14]
        if ident is None or not piece:
            continue
        # seulement les relevés du scénario demandé (colonne vide = Chris / Normal, les premiers relevés)
        if (str(perso or "Chris"), str(diff or "Normal")) != (personnage, difficulte):
            continue
        m = MOTIF_EMPREINTE.search(empreinte or "")
        fiche = {
            "piece": str(piece).lower(),
            "nom_piece": nom_piece or noms_pieces.get(str(piece).lower(), ""),
            "description": desc or "",
            "id": int(ident),
            "quantite": int(qte) if qte is not None else 0,
            "chemin": chemin_ramassage or "",
            "empreinte": m.group(1).split() if m else None,
        }
        if fiche["chemin"] != "posé" or not fiche["empreinte"]:
            ignores.append((fiche, "pas de valeurs fixes complètes ou pas un objet posé"))
        elif qte is None:
            # sans quantité, on placerait par exemple un chargeur vide ailleurs : on laisse l'objet en place
            fiche["description"] = (fiche["description"] or "") + " (quantité inconnue)"
            ignores.append((fiche, "quantité inconnue"))
        else:
            emplacements.append(fiche)
    return emplacements, ignores


def generer(emplacements, graine, ids_libres):
    rng = random.Random(graine)
    libres = [e for e in emplacements if e["id"] in ids_libres]
    contenus = [(e["id"], e["quantite"]) for e in libres]
    rng.shuffle(contenus)
    resultat = []
    for e, (nouvel_id, nouvelle_qte) in zip(libres, contenus):
        resultat.append({
            "piece": e["piece"],
            "empreinte": e["empreinte"],
            "ancien": {"id": e["id"], "quantite": e["quantite"]},
            "nouveau": {"id": nouvel_id, "quantite": nouvelle_qte},
            "description": e["description"],
            "nom_piece": e["nom_piece"],
        })
    return resultat


def verifier(resultat):
    """Contrôles simples : on ne perd ni ne crée aucun objet."""
    avant = Counter((r["ancien"]["id"], r["ancien"]["quantite"]) for r in resultat)
    apres = Counter((r["nouveau"]["id"], r["nouveau"]["quantite"]) for r in resultat)
    assert avant == apres, "Les objets avant et après ne correspondent pas"
    cles = {(r["piece"], tuple(r["empreinte"])) for r in resultat}
    assert len(cles) == len(resultat), "Deux emplacements ont la même clé d'identification"


NOM_DOSSIER_JEU = "Resident Evil Biohazard HD REMASTER"
NOM_SEED_JEU = "randomizer_seed.lua"


def trouver_dossier_jeu():
    """Cherche le dossier du jeu dans les bibliothèques Steam (registre + libraryfolders.vdf)."""
    racines = []
    try:
        import winreg
        for ruche, cle, valeur in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                                   (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath")):
            try:
                with winreg.OpenKey(ruche, cle) as k:
                    racines.append(Path(winreg.QueryValueEx(k, valeur)[0]))
            except OSError:
                pass
    except ImportError:
        pass
    if sys.platform == "win32":
        racines.append(Path(r"C:\Program Files (x86)\Steam"))
    else:                                   # Linux, Steam Deck (Steam natif ou Flatpak)
        maison = Path.home()
        racines += [maison / ".steam" / "steam", maison / ".steam" / "root", maison / ".local" / "share" / "Steam",
                    maison / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam"]

    bibliotheques = []
    for r in racines:
        bibliotheques.append(r)
        vdf = r / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            for m in re.finditer(r'"path"\s+"([^"]+)"', vdf.read_text(encoding="utf-8", errors="replace")):
                bibliotheques.append(Path(m.group(1).replace("\\\\", "\\")))
    for b in bibliotheques:
        d = b / "steamapps" / "common" / NOM_DOSSIER_JEU
        if (d / "bhd.exe").exists():
            return d
    return None


def seed_installee(dossier):
    """Renvoie (graine, armes) de la seed présente dans le dossier du jeu, ou None."""
    cible = Path(dossier) / NOM_SEED_JEU
    if not cible.exists():
        return None
    texte = cible.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"graine\s*=\s*(\d+)", texte)
    a = re.search(r"armes_aleatoires\s*=\s*(true|false)", texte)
    return (m.group(1) if m else "?", bool(a and a.group(1) == "true"))


def installer_seed(fichier_lua, dossier_jeu, graine, armes, dire=print, langue="fr"):
    dossier = Path(dossier_jeu) if dossier_jeu else trouver_dossier_jeu()
    if dossier is None or not (dossier / "bhd.exe").exists():
        dire(tr("gen_install_impossible", langue))
        return False
    ancienne = seed_installee(dossier)
    cible = dossier / NOM_SEED_JEU
    cible.write_bytes(Path(fichier_lua).read_bytes())
    suffixe = tr("gen_armes", langue)
    dire(tr("gen_installee", langue, graine=graine, armes=suffixe if armes else "", chemin=cible)
         + (tr("gen_remplace", langue, ancienne=f"{ancienne[0]}{suffixe if ancienne[1] else ''}")
            if ancienne else ""))

    ini = dossier / "randomizer.ini"
    if ini.exists():
        texte = ini.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(?im)^\s*Seed\s*=\s*(.+?)\s*$", texte)
        if m and m.group(1).lower() != NOM_SEED_JEU:
            dire(tr("gen_ini_autre", langue, seed=m.group(1), nom=NOM_SEED_JEU))
        if re.search(r"(?im)^\s*Actif\s*=\s*0", texte):
            dire(tr("gen_ini_inactif", langue))
    if not (dossier / "xinput1_4.dll").exists():
        dire(tr("gen_dll_absente", langue))
    dire(tr("gen_relance", langue))
    return True


def tirer_graine():
    return random.SystemRandom().randrange(10**6)


def produire(graine, armes_aleatoires, fichier, dossier_sortie=".", installer=False, dossier_jeu=None,
             dire=print, personnage="Chris", difficulte="Normal", langue="fr", dire_spoiler=None,
             armes_choisies=None, objets_visibles=True):
    """Génère une seed et écrit ses fichiers. Partagé par la ligne de commande et l'application.
    Renvoie True si tout s'est bien passé. langue : langue des messages et du spoiler (textes.py).
    dire_spoiler : si donné, reçoit le spoiler complet (sinon il passe par dire).
    armes_choisies : ids des armes à mélanger avec armes_aleatoires (None = toutes celles connues).
    objets_visibles : la DLL remplace aussi les objets posés (modèle par terre et aperçu) avant ramassage."""
    if not Path(fichier).exists():
        dire(tr("gen_donnees", langue, fichier=fichier))
        return False
    ids_armes = set(IDS_ARMES) if armes_choisies is None else set(armes_choisies) & IDS_ARMES
    armes_aleatoires = bool(armes_aleatoires and ids_armes)   # aucune arme cochée = option sans effet
    ids_libres = set(IDS_LIBRES_DE_BASE) | (ids_armes if armes_aleatoires else set())
    nom = f"seed_{graine}{'_armes' if armes_aleatoires else ''}"
    sortie_dir = Path(dossier_sortie)
    sortie_dir.mkdir(parents=True, exist_ok=True)

    emplacements, ignores = lire_emplacements(fichier, personnage, difficulte)
    if not emplacements:
        dire(tr("gen_aucun", langue, personnage=personnage,
                difficulte=tr(f"diff_{difficulte}", langue)))
        return False
    resultat = generer(emplacements, graine, ids_libres)
    verifier(resultat)

    sortie = {
        "version_jeu": {"taille_bhd_exe": 9640360,
                        "sha256": "39B840663E4B1A6835C60CBD176E4EE6C21B9197FC2C2DD733F2A7C36A0B429A"},
        "personnage": personnage, "difficulte": difficulte,
        "graine": graine, "options": {"armes_aleatoires": armes_aleatoires, "objets_visibles": bool(objets_visibles)},
        "remplacements": resultat,
    }
    (sortie_dir / f"{nom}.json").write_text(json.dumps(sortie, indent=1, ensure_ascii=False), encoding="utf-8")

    # Version Lua : lue par la DLL (randomizer_seed.lua) et par appliquer_seed.lua dans Cheat Engine
    lua = ["-- seed générée par generateur_seed.py : ne pas modifier à la main",
           "return {", f"  graine = {graine},",
           f"  armes_aleatoires = {'true' if armes_aleatoires else 'false'},",
           f"  objets_visibles = {'true' if objets_visibles else 'false'},", "  remplacements = {"]
    for r in resultat:
        emp = ", ".join("0x" + v.upper() for v in r["empreinte"])
        lua.append(f"    {{ piece = 0x{r['piece'].upper()}, empreinte = {{ {emp} }}, "
                   f"id = {r['nouveau']['id']}, qte = {r['nouveau']['quantite']} }},")
    lua += ["  },", "}"]
    fichier_lua = sortie_dir / f"{nom}.lua"
    fichier_lua.write_text("\n".join(lua) + "\n", encoding="utf-8")

    nom_objet = lambda ident: tr(f"objet_{ident}", langue)
    lignes = [tr("gen_resume", langue, graine=graine,
                 armes=tr("gen_oui" if armes_aleatoires else "gen_non", langue)),
              tr("gen_compte", langue, n=len(resultat), m=len(emplacements) - len(resultat),
                 pistolet="" if armes_aleatoires else tr("gen_pistolet", langue)), ""]
    for r in sorted(resultat, key=lambda x: x["piece"]):
        a, n = r["ancien"], r["nouveau"]
        lignes.append(f"[{r['piece'].upper():>3}] {r['nom_piece']}: "
                      f"{nom_objet(a['id'])} x{a['quantite']}  ->  {nom_objet(n['id'])} x{n['quantite']}")
    if ignores:
        lignes += ["", tr("gen_non_utilises", langue)]
        lignes += [f"  - [{f['piece'].upper()}] {f['description']}" for f, _ in ignores]
    (sortie_dir / f"{nom}_spoiler.txt").write_text("\n".join(lignes), encoding="utf-8")
    (dire_spoiler or dire)("\n".join(lignes))
    dire(tr("gen_fichiers", langue, dossier=sortie_dir.resolve(), a=f"{nom}.json", b=f"{nom}.lua",
            c=f"{nom}_spoiler.txt"))
    if installer:
        return installer_seed(fichier_lua, dossier_jeu, graine, armes_aleatoires, dire, langue)
    return True


def main():
    parser = argparse.ArgumentParser(description="Générateur de seeds du randomizer Resident Evil HD Remaster")
    parser.add_argument("graine", nargs="?", type=int, help="numéro de graine (au hasard si absent)")
    parser.add_argument("--armes-aleatoires", action="store_true",
                        help="mélange aussi le pistolet (Chris doit alors trouver son arme)")
    parser.add_argument("--objets-invisibles", action="store_true",
                        help="ne remplace les objets qu'au ramassage (par terre, on voit l'objet d'origine)")
    parser.add_argument("--fichier", default=FICHIER_PAR_DEFAUT, help="tableur de données")
    parser.add_argument("--personnage", default="Chris", choices=("Chris", "Jill"))
    parser.add_argument("--difficulte", default="Normal",
                        choices=("Très facile", "Facile", "Normal", "Difficile", "Real Survival"))
    parser.add_argument("--installer", action="store_true",
                        help=f"copie la seed dans le dossier du jeu sous le nom {NOM_SEED_JEU}")
    parser.add_argument("--dossier-jeu", help="dossier du jeu (sinon cherché dans les bibliothèques Steam)")
    args = parser.parse_args()

    graine = args.graine if args.graine is not None else tirer_graine()
    if not produire(graine, args.armes_aleatoires, args.fichier, ".", args.installer, args.dossier_jeu,
                    personnage=args.personnage, difficulte=args.difficulte,
                    objets_visibles=not args.objets_invisibles):
        sys.exit(1)


if __name__ == "__main__":
    main()

