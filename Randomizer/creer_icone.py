"""
Dessine l'icône de l'application (un dé aux points rouges sur une tuile sombre) sans bibliothèque externe.
Produit icone.ico (16 à 256 px, pour l'exe) et icone.png (256 px, pour la fenêtre).

    python creer_icone.py

Depuis la v0.9.0, le logo est le dé mordu qui saigne, dessiné par creer_logo.py (icone.ico, icone.png, logo.png,
logo_entete.png). Ce script ne sert plus que si ces fichiers disparaissent (il redessine alors l'ancien dé).
"""
import struct
import zlib
from pathlib import Path

FOND = (0x1e, 0x21, 0x28)
BORD = (0xb3, 0x26, 0x2e)
DE = (0xee, 0xec, 0xe8)
DE_OMBRE = (0xc9, 0xc6, 0xc0)
POINT = (0xb3, 0x26, 0x2e)


def dist_rect(x, y, cx, cy, demi, r):
    qx, qy = abs(x - cx) - (demi - r), abs(y - cy) - (demi - r)
    return (max(qx, 0) ** 2 + max(qy, 0) ** 2) ** 0.5 + min(max(qx, qy), 0) - r


def melange(dessous, dessus, a):
    return tuple(d * (1 - a) + h * a for d, h in zip(dessous, dessus))


def dessiner(n):
    """Image n×n en coordonnées normalisées (0..1), lissée par couverture de pixel."""
    pixels = []
    px_unite = 1 / n
    for j in range(n):
        for i in range(n):
            x, y = (i + 0.5) / n, (j + 0.5) / n
            couv = lambda d: max(0.0, min(1.0, 0.5 - d / px_unite))
            # tuile de fond, avec liseré rouge
            d_tuile = dist_rect(x, y, 0.5, 0.5, 0.47, 0.11)
            alpha = couv(d_tuile)
            c = melange(BORD, FOND, couv(d_tuile + 0.035))
            # dé : ombre portée puis face
            c = melange(c, (0, 0, 0), 0.35 * couv(dist_rect(x, y, 0.515, 0.53, 0.275, 0.07)))
            d_de = dist_rect(x, y, 0.5, 0.5, 0.275, 0.07)
            face = melange(DE, DE_OMBRE, max(0.0, min(1.0, (y - 0.3) / 0.5)) * 0.6)
            c = melange(c, face, couv(d_de))
            # cinq points
            for px, py in ((0.36, 0.36), (0.64, 0.36), (0.5, 0.5), (0.36, 0.64), (0.64, 0.64)):
                rayon = max(0.06, 1.2 / n)
                c = melange(c, POINT, couv(((x - px) ** 2 + (y - py) ** 2) ** 0.5 - rayon) * couv(d_de))
            pixels.append(tuple(round(v) for v in c) + (round(255 * alpha),))
    return pixels


def png(n, pixels):
    brut = b"".join(b"\x00" + bytes(v for p in pixels[y * n:(y + 1) * n] for v in p) for y in range(n))

    def bloc(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    return (b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
            + bloc(b"IDAT", zlib.compress(brut, 9)) + bloc(b"IEND", b""))


def bmp_ico(n, pixels):
    """Entrée .ico au format bitmap 32 bits (BGRA, lignes de bas en haut, masque ET vide)."""
    entete = struct.pack("<IiiHHIIiiII", 40, n, n * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    lignes = b"".join(bytes(v for r, g, b, a in pixels[y * n:(y + 1) * n] for v in (b, g, r, a))
                      for y in range(n - 1, -1, -1))
    masque = b"\x00" * (((n + 31) // 32) * 4 * n)
    return entete + lignes + masque


def ico(images):
    """Fichier .ico : bitmaps pour les petites tailles, PNG pour 256 px (compatible avec tous les outils)."""
    entete = struct.pack("<HHH", 0, 1, len(images))
    decalage = 6 + 16 * len(images)
    repertoire, donnees = b"", b""
    for n, data in images:
        repertoire += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(data), decalage + len(donnees))
        donnees += data
    return entete + repertoire + donnees


if __name__ == "__main__":
    ici = Path(__file__).resolve().parent
    images = []
    for n in (16, 24, 32, 48, 64, 128, 256):
        pixels = dessiner(n)
        images.append((n, png(n, pixels) if n == 256 else bmp_ico(n, pixels)))
    (ici / "icone.ico").write_bytes(ico(images))
    (ici / "icone.png").write_bytes(images[-1][1])
    print("icone.ico et icone.png écrits dans", ici)
