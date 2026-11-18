#!/usr/bin/env python3
r"""
Noms officiels des objets, lus dans les textes du jeu installé (rien n'est copié dans le projet à part
les noms eux-mêmes).

Le jeu range les textes de l'inventaire dans nativePC\arc\id\e_rom\ingamecommon\ingamecommon_<langue>.arc,
entrée « ItemMes_<langue> » (format GMD du moteur MT Framework, compressé zlib). La clé « itemNNN0 » donne le
nom de l'objet d'id NNN (« item0170 » = id 17, « Munitions pour pistolet ») ; « itemNNN1 » est sa description.
Certains noms dépendent d'une condition du jeu : « <FC 0x06 46 itemkeyhouse00 itemkeyarmor> » renvoie à deux
autres clés ; on garde alors les deux noms, séparés par « / ».

Utilisation :
    python noms_jeu.py                  (affiche la table id -> nom, français et anglais)
    python noms_jeu.py --ecrire         (complète l'onglet « Objets » du tableur ; copie de sauvegarde avant)
"""
import argparse
import re
import shutil
import struct
import sys
import zlib
from datetime import datetime
from pathlib import Path

LANGUES_JEU = {"fr": "fre", "en": "eng", "ja": "jpn", "es": "spa", "de": "ger", "it": "ita",
               "zh": "chS", "zh_t": "chT"}
CHEMIN_ARC = r"nativePC\arc\id\e_rom\ingamecommon\ingamecommon_{l}.arc"
ID_MAX = 255


def _entree_arc(chemin, fin_nom):
    """Contenu décompressé de l'entrée d'une archive ARC (v7) dont le nom finit par fin_nom."""
    f = Path(chemin).read_bytes()
    if f[:4] != b"ARC\0":
        raise ValueError(f"archive inattendue : {chemin}")
    n = struct.unpack_from("<H", f, 6)[0]
    for i in range(n):
        off = 8 + 80 * i
        nom = f[off:off + 64].split(b"\0")[0].decode("latin1")
        _, taille_c, _, debut = struct.unpack_from("<IIII", f, off + 64)
        if nom.endswith(fin_nom):
            return zlib.decompress(f[debut:debut + taille_c])
    raise KeyError(fin_nom)


def _lire_gmd(donnees):
    """{clé: texte} d'un fichier GMD (version 2 : clés puis textes, séparés par des zéros)."""
    if donnees[:4] != b"GMD\0":
        raise ValueError("fichier de textes inattendu")
    nb = struct.unpack_from("<I", donnees, 0x14)[0]
    t_cles, t_txt = struct.unpack_from("<II", donnees, 0x1C)
    textes = donnees[len(donnees) - t_txt:].split(b"\0")[:nb]
    cles = donnees[len(donnees) - t_txt - t_cles:len(donnees) - t_txt].split(b"\0")[:nb]
    encodage = "utf-8"
    try:
        b"".join(textes).decode("utf-8")
    except UnicodeDecodeError:
        encodage = "cp1252"                       # textes européens du jeu
    return {c.decode("latin1"): t.decode(encodage, "replace") for c, t in zip(cles, textes)}


def _nettoyer(texte, table, profondeur=0):
    m = re.fullmatch(r"\s*<FC 0x06 \d+ (\S+) (\S+)>\s*", texte)
    if m and profondeur < 3:                     # nom conditionnel : les deux possibilités
        noms = []
        for cle in m.groups():
            n = _nettoyer(table.get(cle, ""), table, profondeur + 1)
            if n and n not in noms:
                noms.append(n)
        return " / ".join(noms)
    texte = re.sub(r"<[^>]*>", "", texte)        # balises de couleur, etc.
    return " ".join(texte.split())


def lire_noms(dossier_jeu, langue="fr"):
    """{id: nom} des objets dans la langue demandée (code de l'application : fr, en, ja…)."""
    l = LANGUES_JEU.get(langue, langue)
    table = _lire_gmd(_entree_arc(Path(dossier_jeu) / CHEMIN_ARC.format(l=l), f"ItemMes_{l}"))
    noms = {}
    for i in range(1, ID_MAX + 1):
        brut = table.get(f"item{i:03d}0")
        if brut:
            nom = _nettoyer(brut, table)
            if nom:
                noms[i] = nom
    return noms


# ------------------------------------------------------------------ tableur

ESSAIS = ("(à identifier)", "(à nommer)", "")


def completer_tableur(chemin, noms_fr, noms_en, dire=print):
    """Onglet « Objets » : colonnes « Nom en jeu (FR/EN) » pour chaque id ; noms provisoires remplacés ;
    ids du jeu absents ajoutés. Les formules de l'onglet « Emplacements » sont étendues aux nouvelles lignes."""
    from openpyxl import load_workbook
    wb = load_workbook(chemin)
    ws = wb["Objets"]
    ws.cell(1, 6).value = "Nom en jeu (FR)"
    ws.cell(1, 7).value = "Nom en jeu (EN)"
    lignes = {ws.cell(r, 1).value: r for r in range(2, ws.max_row + 1) if isinstance(ws.cell(r, 1).value, int)}
    nommes, ajoutes = [], []
    for ident, r in sorted(lignes.items()):
        if ident in noms_fr:
            ws.cell(r, 6).value = noms_fr[ident]
            ws.cell(r, 7).value = noms_en.get(ident)
            if (ws.cell(r, 3).value or "").strip() in ESSAIS:
                ws.cell(r, 3).value = noms_fr[ident]
                nommes.append(ident)
    libre = max(lignes.values(), default=1) + 1
    for ident in sorted(set(noms_fr) - set(lignes)):
        ws.cell(libre, 1).value = ident
        ws.cell(libre, 2).value = f"=DEC2HEX(A{libre})"
        ws.cell(libre, 3).value = noms_fr[ident]
        ws.cell(libre, 4).value = "nom du jeu"
        ws.cell(libre, 5).value = "Nom tiré des textes du jeu (ItemMes) ; jamais relevé à un emplacement."
        ws.cell(libre, 6).value = noms_fr[ident]
        ws.cell(libre, 7).value = noms_en.get(ident)
        ajoutes.append(ident)
        libre += 1
    # formules de recherche du nom : $52 -> $300 (place pour tous les objets du jeu)
    em = wb["Emplacements"]
    for ligne in em.iter_rows():
        for c in ligne:
            if isinstance(c.value, str) and "Objets!" in c.value:
                c.value = re.sub(r"(Objets!\$[A-Z]\$2:\$[A-Z]\$)52\b", r"\g<1>300", c.value)
    wb.save(chemin)
    dire(f"Objets nommés : {nommes or 'aucun'}")
    dire(f"Objets ajoutés depuis le jeu : {len(ajoutes)}")
    return nommes, ajoutes


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import generateur_seed as gen
    ap = argparse.ArgumentParser(description="Noms officiels des objets, lus dans les textes du jeu")
    ap.add_argument("--dossier-jeu", help="dossier du jeu (sinon cherché dans les bibliothèques Steam)")
    ap.add_argument("--fichier", default=str(Path(__file__).resolve().parent.parent / gen.FICHIER_PAR_DEFAUT))
    ap.add_argument("--ecrire", action="store_true", help="complète l'onglet « Objets » du tableur")
    args = ap.parse_args()
    jeu = Path(args.dossier_jeu) if args.dossier_jeu else gen.trouver_dossier_jeu()
    if not jeu:
        sys.exit("Jeu introuvable : indique --dossier-jeu.")
    fr, en = lire_noms(jeu, "fr"), lire_noms(jeu, "en")
    if not args.ecrire:
        for i in sorted(fr):
            print(f"{i:4}  {fr[i]}  |  {en.get(i, '')}")
        return
    tableur = Path(args.fichier)
    copie = tableur.parent / "sauvegardes" / f"{tableur.stem}_avant_noms_jeu_{datetime.now():%Y%m%d_%H%M}.xlsx"
    copie.parent.mkdir(exist_ok=True)
    shutil.copy2(tableur, copie)
    print(f"Copie de sauvegarde : {copie}")
    completer_tableur(tableur, fr, en)


if __name__ == "__main__":
    main()
