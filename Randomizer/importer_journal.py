#!/usr/bin/env python3
r"""
Importe des journaux de relevés dans l'onglet « Emplacements » du tableur.

Formats reconnus (on peut en donner plusieurs à la fois, de plusieurs testeurs) :
  - randomizer_journal.txt     (DLL)         lignes « Non repertorie … valeurs=PIECE:8 valeurs »
  - journal_non_repertorie.txt (Cheat Engine, appliquer_seed.lua)
  - journal_objets.txt         (Cheat Engine, journal_objets.lua) : « chemin=pose … brut10-2C=8 valeurs »

Un emplacement = une pièce + son empreinte (8 valeurs fixes). Ceux déjà présents dans le tableur, ou en
double dans les journaux, sont ignorés. Les objets « directs » (sans empreinte) ne sont pas importés.
Les identifiants d'objets encore absents de l'onglet « Objets » y sont ajoutés comme « (à nommer) ».
Avant d'écrire, une copie du tableur est faite dans sauvegardes\.

Utilisation :
    python importer_journal.py journal1.txt [journal2.txt …]               (aperçu, rien n'est écrit)
    python importer_journal.py journal1.txt [journal2.txt …] --ecrire      (ajoute au tableur)
    options : --fichier donnees.xlsx   --source "testeur Paul"
"""
import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

FICHIER_PAR_DEFAUT = Path(__file__).resolve().parent.parent / "donnees_randomizer_RE1.xlsx"
HEX8 = r"[0-9A-Fa-f]{8}"
MOTIF_PIECE = re.compile(r"piece=([0-9A-Fa-f]+)")
MOTIF_ID = re.compile(r"\bid=(\d+)")
MOTIF_QTE = re.compile(r"\bqte=(\d+)")
MOTIF_HEURE = re.compile(r"^(\d{2}:\d{2}:\d{2})")
MOTIF_NUM = re.compile(r"\bnum=(\d+)")
MOTIFS_EMPREINTE = (
    re.compile(rf"valeurs=[0-9A-Fa-f]+:((?:{HEX8},){{7}}{HEX8})"),     # DLL et appliquer_seed.lua
    re.compile(rf"brut10-2C=((?:{HEX8}\s+){{7}}{HEX8})"),               # journal_objets.lua
)
MOTIF_EMPREINTE_TABLEUR = re.compile(rf"brut \+0x10\.\.\+0x2C = ((?:{HEX8}\s*){{8}})")

# colonnes de l'onglet « Emplacements » (1 = A)
COL = dict(numero=1, piece=2, nom_piece=3, desc=4, ident=5, nom_obj=6, qte=7, chemin=8, verrou=9,
           statut=10, empreinte=11, remarque=12)


def lire_journal(chemin):
    """Renvoie (relevés, nb de lignes « directes » ignorées)."""
    releves, directs = [], 0
    for ligne in Path(chemin).read_text(encoding="utf-8", errors="replace").splitlines():
        if "chemin=direct" in ligne:
            directs += 1
            continue
        empreinte = None
        for motif in MOTIFS_EMPREINTE:
            m = motif.search(ligne)
            if m:
                empreinte = [v.upper() for v in re.split(r"[,\s]+", m.group(1).strip())]
                break
        p, i = MOTIF_PIECE.search(ligne), MOTIF_ID.search(ligne)
        if not (empreinte and p and i):
            continue
        q, h, num = MOTIF_QTE.search(ligne), MOTIF_HEURE.search(ligne), MOTIF_NUM.search(ligne)
        releves.append({
            "piece": p.group(1).lower(), "id": int(i.group(1)),
            "qte": int(q.group(1)) if q else None,
            "empreinte": empreinte, "heure": h.group(1) if h else "?",
            "fichier": Path(chemin).name,
            "num": int(num.group(1)) if num else None,
            "auto": "Releve auto" in ligne,
        })
    return releves, directs


def deja_connus(ws):
    connus = set()
    for ligne in ws.iter_rows(min_row=2, values_only=True):
        piece, empreinte = ligne[COL["piece"] - 1], ligne[COL["empreinte"] - 1]
        m = MOTIF_EMPREINTE_TABLEUR.search(str(empreinte or ""))
        if piece and m:
            connus.add((str(piece).lower(), tuple(v.upper() for v in m.group(1).split())))
    return connus


def premiere_ligne_libre(ws):
    derniere = max((r for r in range(2, ws.max_row + 1) if ws.cell(r, COL["piece"]).value), default=1)
    return derniere + 1


def formule(colonne_source, onglet, colonne_resultat, ligne, fin):
    return (f'=IFERROR(INDEX({onglet}!${colonne_resultat}$2:${colonne_resultat}${fin},'
            f'MATCH({colonne_source}{ligne},{onglet}!$A$2:$A${fin},0)),"")')


def main():
    ap = argparse.ArgumentParser(description="Importe des journaux de relevés dans le tableur")
    ap.add_argument("journaux", nargs="+", help="fichiers journaux à importer")
    ap.add_argument("--fichier", default=str(FICHIER_PAR_DEFAUT), help="tableur de données")
    ap.add_argument("--source", default="", help="qui a fait le relevé (noté dans les remarques)")
    ap.add_argument("--ecrire", action="store_true", help="écrit dans le tableur (sinon simple aperçu)")
    args = ap.parse_args()

    tableur = Path(args.fichier)
    if not tableur.exists():
        sys.exit(f"Tableur introuvable : {tableur}")
    wb = load_workbook(tableur)
    ws, objets = wb["Emplacements"], wb["Objets"]
    connus = deja_connus(ws)
    noms_pieces = {str(r[0]).lower(): r[3] for r in wb["Pièces"].iter_rows(min_row=2, values_only=True) if r[0]}
    ids_objets = {objets.cell(r, 1).value for r in range(2, objets.max_row + 1)}

    nouveaux, doublons, directs = [], 0, 0
    for j in args.journaux:
        if not Path(j).exists():
            sys.exit(f"Journal introuvable : {j}")
        releves, d = lire_journal(j)
        directs += d
        for r in releves:
            cle = (r["piece"], tuple(r["empreinte"]))
            if cle in connus:
                doublons += 1
                continue
            connus.add(cle)
            nouveaux.append(r)

    print(f"{len(nouveaux)} nouvel(s) emplacement(s), {doublons} déjà connu(s) ou en double"
          + (f", {directs} objet(s) « direct(s) » ignoré(s) (pas d'empreinte)" if directs else "") + ".")
    for r in nouveaux:
        qte = "?" if r["qte"] is None else r["qte"]
        inconnu = "" if r["id"] in ids_objets else "   <- id nouveau"
        print(f"  [{r['piece'].upper():>3}] {noms_pieces.get(r['piece'], '?')}: id {r['id']} x{qte}{inconnu}")
    if not nouveaux:
        return
    if not args.ecrire:
        print("\nAperçu seulement : relance avec --ecrire pour les ajouter au tableur.")
        return

    sauvegarde = tableur.parent / "sauvegardes" / f"{tableur.stem}_avant_import_{datetime.now():%Y-%m-%d_%H%M%S}.xlsx"
    sauvegarde.parent.mkdir(exist_ok=True)
    shutil.copyfile(tableur, sauvegarde)

    ligne = premiere_ligne_libre(ws)
    numero = max((c.value for c in ws["A"][1:] if isinstance(c.value, int)), default=0)
    date = datetime.now().strftime("%d/%m/%Y")
    source = f" par {args.source}" if args.source else ""
    for r in nouveaux:
        numero += 1
        if ws.cell(ligne, COL["numero"]).value is None:
            ws.cell(ligne, COL["numero"]).value = numero
        # Les lignes préparées ont déjà les formules ; au-delà, on les ajoute.
        if not ws.cell(ligne, COL["nom_piece"]).value:
            ws.cell(ligne, COL["nom_piece"]).value = formule(f"B", "Pièces", "D", ligne, 119)
        if not ws.cell(ligne, COL["nom_obj"]).value:
            ws.cell(ligne, COL["nom_obj"]).value = formule(f"E", "Objets", "C", ligne, 52)
        ws.cell(ligne, COL["piece"]).value = r["piece"]
        ws.cell(ligne, COL["desc"]).value = (f"Objet n°{r['num']} de la pièce, position à décrire"
                                             if r["num"] else "(position à décrire)")
        ws.cell(ligne, COL["ident"]).value = r["id"]
        ws.cell(ligne, COL["qte"]).value = r["qte"]
        ws.cell(ligne, COL["chemin"]).value = "posé"
        ws.cell(ligne, COL["statut"]).value = "relevé"
        ws.cell(ligne, COL["empreinte"]).value = "brut +0x10..+0x2C = " + " ".join(r["empreinte"])
        ws.cell(ligne, COL["remarque"]).value = (f"Importé{source} le {date} depuis {r['fichier']} "
                                                 f"(ligne de {r['heure']})."
                                                 + (" Relevé automatique à l'entrée de la pièce." if r["auto"] else "")
                                                 + ("" if r["qte"] is not None else " Quantité absente du journal."))
        ligne += 1

    libre = next((i for i in range(2, objets.max_row + 2) if objets.cell(i, 1).value is None), objets.max_row + 1)
    for ident in sorted({r["id"] for r in nouveaux} - ids_objets):
        exemple = next(r for r in nouveaux if r["id"] == ident)
        objets.cell(libre, 1).value = ident
        objets.cell(libre, 3).value = "(à nommer)"
        objets.cell(libre, 4).value = "vu en jeu"
        qte = "inconnue" if exemple["qte"] is None else exemple["qte"]
        objets.cell(libre, 5).value = (f"Posé en {exemple['piece'].upper()}, quantité {qte} "
                                       f"(import du {date}). Objet à nommer.")
        libre += 1

    wb.calculation.fullCalcOnLoad = True       # Excel recalcule les formules à l'ouverture
    wb.save(tableur)
    print(f"\nAjouté au tableur. Copie de l'ancien fichier : {sauvegarde}")


if __name__ == "__main__":
    main()
