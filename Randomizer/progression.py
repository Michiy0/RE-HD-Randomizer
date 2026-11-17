#!/usr/bin/env python3
r"""
Barres d'avancement des relevés, affichées sur la page GitHub (README).

Calcul, à partir du tableur :
  - pour chaque personnage et difficulté : pièces relevées en NOUVELLE partie (onglet « Pièces relevées »,
    « Nouvelle partie = oui ») sur le nombre total de pièces (onglet « Pièces »). C'est le pourcentage.
    Les pièces visitées en partie déjà commencée sont montrées en plus pâle (relevé incomplet).
  - armes bonus (onglet « Bonus ») : lignes dont l'ID objet est connu, sur toutes les lignes.

Produit images/progression.svg et remplace la section du README comprise entre
<!-- progression:debut --> et <!-- progression:fin -->.

    python Randomizer\progression.py            (appelé aussi par preparer_publication.py)
"""
import argparse
import re
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from openpyxl import load_workbook

RACINE = Path(__file__).resolve().parent.parent
PERSONNAGES = ("Chris", "Jill")
DIFFICULTES = ("Très facile", "Facile", "Normal", "Difficile", "Real Survival")
DEBUT, FIN = "<!-- progression:debut -->", "<!-- progression:fin -->"

# mêmes couleurs que l'application
FOND, CARTE, BORD = "#15171c", "#1e2128", "#2c313b"
TEXTE, DISCRET, ACCENT, PALE, VIDE = "#e7e9ee", "#8a909c", "#b3262e", "#5a2a2e", "#262a33"
POLICE = "Segoe UI, Helvetica, Arial, sans-serif"


def calculer(fichier):
    wb = load_workbook(fichier, data_only=True)
    total_pieces = sum(1 for r in wb["Pièces"].iter_rows(min_row=2, values_only=True) if r[0])
    scenarios = {(p, d): {"completes": set(), "visitees": set(), "objets": 0}
                 for p in PERSONNAGES for d in DIFFICULTES}

    if "Pièces relevées" in wb.sheetnames:
        for piece, _, perso, diff, nouvelle, *_ in wb["Pièces relevées"].iter_rows(min_row=2, values_only=True):
            s = scenarios.get((str(perso or "Chris"), str(diff or "Normal")))
            if piece and s is not None:
                (s["completes"] if nouvelle == "oui" else s["visitees"]).add(str(piece).lower())
    for ligne in wb["Emplacements"].iter_rows(min_row=2, values_only=True):
        ligne = tuple(ligne) + (None,) * 14
        s = scenarios.get((str(ligne[12] or "Chris"), str(ligne[13] or "Normal")))
        if ligne[1] and ligne[4] is not None and s is not None:
            s["objets"] += 1

    bonus = []
    if "Bonus" in wb.sheetnames:
        bonus = [r for r in wb["Bonus"].iter_rows(min_row=2, values_only=True) if r[0]]
    return {
        "total_pieces": total_pieces,
        "scenarios": {k: {"completes": len(v["completes"]),
                          "visitees": len(v["visitees"] - v["completes"]),
                          "objets": v["objets"]} for k, v in scenarios.items()},
        "bonus_total": len(bonus),
        "bonus_connus": sum(1 for r in bonus if r[3] not in (None, "")),
    }


def dessiner_svg(res, date):
    largeur, x_label, x_barre, l_barre, x_texte = 800, 28, 200, 300, 520
    haut_ligne, y0 = 30, 92
    lignes = [(p, d) for p in PERSONNAGES for d in DIFFICULTES]
    hauteur = y0 + len(lignes) * haut_ligne + 22 + 26
    t = res["total_pieces"] or 1
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" '
         f'viewBox="0 0 {largeur} {hauteur}" font-family="{POLICE}" role="img" '
         f'aria-label="Avancement des relevés du randomizer">',
         f'<rect width="{largeur}" height="{hauteur}" rx="14" fill="{FOND}"/>',
         f'<rect x="8" y="8" width="{largeur - 16}" height="{hauteur - 16}" rx="10" fill="{CARTE}" stroke="{BORD}"/>',
         f'<text x="{x_label}" y="44" font-size="20" font-weight="700" fill="{TEXTE}">Avancement des relevés</text>',
         f'<text x="{x_label}" y="66" font-size="12" fill="{DISCRET}">Pièces relevées en nouvelle partie, sur '
         f'{res["total_pieces"]} pièces · mis à jour le {escape(date)}</text>',
         # légende
         f'<rect x="{largeur - 252}" y="36" width="12" height="12" rx="3" fill="{ACCENT}"/>'
         f'<text x="{largeur - 234}" y="46" font-size="12" fill="{DISCRET}">complète</text>',
         f'<rect x="{largeur - 160}" y="36" width="12" height="12" rx="3" fill="{PALE}"/>'
         f'<text x="{largeur - 142}" y="46" font-size="12" fill="{DISCRET}">partie commencée</text>']

    def barre(y, part_pleine, part_pale):
        o.append(f'<rect x="{x_barre}" y="{y - 11}" width="{l_barre}" height="12" rx="6" fill="{VIDE}"/>')
        lp, lpale = round(l_barre * part_pleine), round(l_barre * (part_pleine + part_pale))
        if lpale > 0:
            o.append(f'<rect x="{x_barre}" y="{y - 11}" width="{max(lpale, 6)}" height="12" rx="6" fill="{PALE}"/>')
        if lp > 0:
            o.append(f'<rect x="{x_barre}" y="{y - 11}" width="{max(lp, 6)}" height="12" rx="6" fill="{ACCENT}"/>')

    y = y0
    perso_precedent = None
    for p, d in lignes:
        s = res["scenarios"][(p, d)]
        nom = p if p != perso_precedent else ""
        perso_precedent = p
        o.append(f'<text x="{x_label}" y="{y}" font-size="14" font-weight="700" fill="{TEXTE}">{escape(nom)}</text>')
        o.append(f'<text x="{x_label + 52}" y="{y}" font-size="14" fill="{TEXTE}">{escape(d)}</text>')
        barre(y, s["completes"] / t, s["visitees"] / t)
        pct = round(100 * s["completes"] / t)
        detail = f'{s["completes"]}/{res["total_pieces"]}'
        if s["visitees"]:
            detail += f' · +{s["visitees"]} visitées'
        if s["objets"]:
            detail += f' · {s["objets"]} objets'
        o.append(f'<text x="{x_texte}" y="{y}" font-size="14" font-weight="700" fill="{TEXTE}">{pct} %</text>')
        o.append(f'<text x="{x_texte + 46}" y="{y}" font-size="12" fill="{DISCRET}">{escape(detail)}</text>')
        y += haut_ligne
        if d == DIFFICULTES[-1] and p != PERSONNAGES[-1]:
            o.append(f'<line x1="{x_label}" y1="{y - 20}" x2="{largeur - x_label}" y2="{y - 20}" stroke="{BORD}"/>')

    y += 22
    o.append(f'<line x1="{x_label}" y1="{y - 30}" x2="{largeur - x_label}" y2="{y - 30}" stroke="{BORD}"/>')
    o.append(f'<text x="{x_label}" y="{y}" font-size="14" font-weight="700" fill="{TEXTE}">Armes bonus</text>')
    if res["bonus_total"]:
        barre(y, res["bonus_connus"] / res["bonus_total"], 0)
        o.append(f'<text x="{x_texte}" y="{y}" font-size="14" font-weight="700" fill="{TEXTE}">'
                 f'{res["bonus_connus"]}/{res["bonus_total"]}</text>')
        o.append(f'<text x="{x_texte + 46}" y="{y}" font-size="12" fill="{DISCRET}">identifiées</text>')
    else:
        barre(y, 0, 0)
        o.append(f'<text x="{x_texte}" y="{y}" font-size="12" fill="{DISCRET}">liste à compléter</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def bloc_readme(res, date, chemin_image):
    t = res["total_pieces"]
    lignes = [DEBUT, "",
              f'<img src="{chemin_image}" alt="Avancement des relevés" width="800">', "",
              "<details><summary>Détail (texte)</summary>", "",
              "| Personnage | Difficulté | Pièces complètes | Visitées (partie commencée) | Objets relevés |",
              "|---|---|---|---|---|"]
    for (p, d), s in res["scenarios"].items():
        lignes.append(f"| {p} | {d} | {s['completes']}/{t} ({round(100 * s['completes'] / (t or 1))} %) "
                      f"| {s['visitees']} | {s['objets']} |")
    bonus = (f"{res['bonus_connus']}/{res['bonus_total']} identifiées" if res["bonus_total"]
             else "liste à compléter")
    lignes += ["", f"Armes bonus : {bonus}. Mis à jour le {date}.", "", "</details>", "", FIN]
    return "\n".join(lignes)


def mettre_a_jour(fichier, readme, image, chemin_image_readme="images/progression.svg"):
    res = calculer(fichier)
    date = datetime.now().strftime("%d/%m/%Y")
    image.parent.mkdir(parents=True, exist_ok=True)
    image.write_text(dessiner_svg(res, date), encoding="utf-8", newline="\n")
    brut = readme.read_bytes()
    crlf = b"\r\n" in brut
    texte = brut.decode("utf-8").replace("\r\n", "\n")
    bloc = bloc_readme(res, date, chemin_image_readme)
    motif = re.compile(re.escape(DEBUT) + r".*?" + re.escape(FIN), re.S)
    if not motif.search(texte):
        raise SystemExit(f"Balises {DEBUT} … {FIN} absentes de {readme}")
    texte = motif.sub(lambda _: bloc, texte)
    readme.write_bytes((texte.replace("\n", "\r\n") if crlf else texte).encode("utf-8"))
    return res


def main():
    ap = argparse.ArgumentParser(description="Met à jour les barres d'avancement du README")
    ap.add_argument("--fichier", default=str(RACINE / "donnees_randomizer_RE1.xlsx"))
    ap.add_argument("--readme", default=str(RACINE / "README.md"))
    ap.add_argument("--image", default=str(RACINE / "images" / "progression.svg"))
    args = ap.parse_args()
    res = mettre_a_jour(Path(args.fichier), Path(args.readme), Path(args.image))
    for (p, d), s in res["scenarios"].items():
        if s["completes"] or s["visitees"] or s["objets"]:
            print(f"{p} / {d} : {s['completes']}/{res['total_pieces']} complètes, +{s['visitees']} visitées, "
                  f"{s['objets']} objets")
    print(f"Armes bonus : {res['bonus_connus']}/{res['bonus_total']}")
    print(f"Écrit : {args.image} et la section du README")


if __name__ == "__main__":
    main()
