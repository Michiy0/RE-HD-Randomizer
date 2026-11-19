"""
Dessine le logo du randomizer : un dé blanc à points rouges, mordu dans un coin, qui saigne, sur une tuile
sombre à bord rouge. Produit, à partir d'un dessin en 2048 px réduit proprement :
  logo.png (512 px), icone.png (256 px, fenêtre), icone.ico (16 à 256 px, exe), logo_entete.png (40 px).

    python creer_logo.py          (nécessite Pillow : python -m pip install pillow)
"""
from pathlib import Path

from PIL import Image, ImageDraw

ICI = Path(__file__).resolve().parent
TAILLE = 2048
K = TAILLE / 200                     # le dessin est pensé sur une grille de 200 × 200

ROUGE, FOND, CONTOUR = (179, 38, 46), (30, 33, 40), (12, 13, 16)
SANG_FONCE, SANG_NOIR = (143, 31, 36), (90, 20, 24)


def p(x, y):
    return (x * K, y * K)


def bezier(a, c1, c2, b, n=40):
    """Points d'une courbe de Bézier cubique (grille 200)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * b[0]
        y = u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * b[1]
        pts.append((x, y))
    return pts


def quad(a, c, b, n=24):
    return bezier(a, (a[0] + 2 / 3 * (c[0] - a[0]), a[1] + 2 / 3 * (c[1] - a[1])),
                  (b[0] + 2 / 3 * (c[0] - b[0]), b[1] + 2 / 3 * (c[1] - b[1])), b, n)


def trait(d, pts, couleur, largeur):
    """Trait épais à bouts ronds (grille 200)."""
    # (un disque à chaque sommet : jonctions bien rondes, sans les dents de « joint=curve » sur les petits segments)
    pts = [p(*q) for q in pts]
    w = largeur * K
    d.line(pts, fill=couleur, width=round(w))
    for q in pts:
        d.ellipse((q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2), fill=couleur)


def rond(d, cx, cy, r, couleur):
    d.ellipse((*p(cx - r, cy - r), *p(cx + r, cy + r)), fill=couleur)


def dessiner():
    im = Image.new("RGBA", (TAILLE, TAILLE), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # tuile
    d.rounded_rectangle((*p(8, 8), *p(192, 192)), radius=24 * K, fill=ROUGE)
    d.rounded_rectangle((*p(16, 16), *p(184, 184)), radius=18 * K, fill=FOND)
    # ombre du dé
    ombre = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(ombre).rounded_rectangle((*p(49, 50), *p(161, 162)), radius=18 * K, fill=(15, 17, 20, 128))
    im.alpha_composite(ombre)
    # contour du dé, avec la morsure en haut à droite
    morsure = (bezier((114, 44), (114, 54), (122, 60), (130, 58))
               + bezier((130, 58), (130, 68), (140, 74), (148, 70))[1:]
               + bezier((148, 70), (152, 72), (156, 76), (156, 82))[1:])
    contour = ([(62, 44), (114, 44)] + morsure[1:] + [(156, 138)] + quad((156, 138), (156, 156), (138, 156))[1:]
               + [(62, 156)] + quad((62, 156), (44, 156), (44, 138))[1:] + [(44, 62)]
               + quad((44, 62), (44, 44), (62, 44))[1:])
    masque = Image.new("L", im.size, 0)
    ImageDraw.Draw(masque).polygon([p(*q) for q in contour], fill=255)
    degrade = Image.new("RGBA", im.size)
    dd = ImageDraw.Draw(degrade)
    haut, bas = (245, 243, 239), (211, 207, 199)
    for y in range(TAILLE):
        t = min(max((y / K - 44) / 112, 0), 1)
        dd.line([(0, y), (TAILLE, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(haut, bas)) + (255,))
    im.paste(degrade, (0, 0), masque)
    d = ImageDraw.Draw(im)
    trait(d, contour + [contour[1]], CONTOUR, 5)
    # bord de la morsure : chair à vif
    trait(d, morsure, SANG_FONCE, 7)
    trait(d, bezier((116, 48), (118, 54), (124, 58), (130, 58)), SANG_NOIR, 2.5)
    trait(d, bezier((131, 61), (134, 68), (140, 72), (148, 72)), SANG_NOIR, 2.5)
    # reflet
    reflet = Image.new("RGBA", im.size, (0, 0, 0, 0))
    trait(ImageDraw.Draw(reflet), [(58, 54), (84, 52)], (255, 255, 255, 180), 5)
    im.alpha_composite(reflet)
    d = ImageDraw.Draw(im)
    # points et coulures de sang
    for cx, cy in ((72, 72), (100, 100), (72, 128), (128, 128)):
        rond(d, cx, cy, 10, ROUGE)
    trait(d, quad((72, 138), (71, 146), (73, 152)), ROUGE, 5)
    trait(d, quad((128, 138), (130, 150), (127, 160)), ROUGE, 5)
    trait(d, quad((150, 84), (154, 100), (150, 112)), ROUGE, 5)
    rond(d, 150, 116, 4.5, ROUGE)
    rond(d, 127, 164, 4.5, ROUGE)
    return im


if __name__ == "__main__":
    grand = dessiner()
    reduire = lambda n: grand.resize((n, n), Image.LANCZOS)
    reduire(512).save(ICI / "logo.png", optimize=True)
    reduire(256).save(ICI / "icone.png", optimize=True)
    reduire(40).save(ICI / "logo_entete.png", optimize=True)
    reduire(256).save(ICI / "icone.ico", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
    print("logo.png, icone.png, icone.ico et logo_entete.png écrits dans", ICI)
