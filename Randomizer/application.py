"""
Application du randomizer Resident Evil HD Remaster : génère et installe une seed en quelques clics.

Toute la logique est dans generateur_seed.py (partagée avec la ligne de commande) ; ce fichier ne fait
que l'interface. Les options pas encore prises en charge sont visibles mais grisées (« à venir »).

Lancer sans compiler :  python application.py
Construire le .exe   :  construire_exe.bat
"""
import os
import shutil
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import generateur_seed as gen

VERSION = "0.2"
TAILLE_BHD_EXE = 9640360
SHA256_BHD_EXE = "39B840663E4B1A6835C60CBD176E4EE6C21B9197FC2C2DD733F2A7C36A0B429A"
TITRE = f"Randomizer RE HD Remaster v{VERSION}"


def dossier_programme():
    """Dossier de l'exe (version compilée) ou du script."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def trouver_ressource(nom, sous_dossiers=("", "..", "../DLL", "DLL")):
    """Cherche d'abord à côté du programme (pour pouvoir mettre à jour les données sans recompiler),
    puis dans la copie embarquée dans l'exe."""
    base = dossier_programme()
    for s in sous_dossiers:
        p = (base / s / nom).resolve()
        if p.exists():
            return p
    embarque = getattr(sys, "_MEIPASS", None)
    if embarque and (Path(embarque) / nom).exists():
        return Path(embarque) / nom
    return None


_versions_verifiees = {}


def version_jeu_ok(dossier):
    """Vrai si bhd.exe est exactement la version prise en charge (taille puis SHA-256, mis en cache)."""
    import hashlib
    exe = Path(dossier) / "bhd.exe"
    try:
        etat = exe.stat()
    except OSError:
        return False
    cle = (str(exe), etat.st_size, etat.st_mtime)
    if cle not in _versions_verifiees:
        ok = etat.st_size == TAILLE_BHD_EXE
        if ok:
            h = hashlib.sha256()
            with open(exe, "rb") as f:
                for morceau in iter(lambda: f.read(1 << 20), b""):
                    h.update(morceau)
            ok = h.hexdigest().upper() == SHA256_BHD_EXE
        _versions_verifiees[cle] = ok
    return _versions_verifiees[cle]


def est_notre_dll(chemin):
    """Vrai si ce xinput1_4.dll est celui du randomizer (il contient le texte de son journal)."""
    try:
        return b"Randomizer RE HD" in Path(chemin).read_bytes()
    except OSError:
        return False


# ---------------------------------------------------------------------- style
COULEURS = {
    "fond": "#15171c",        # fond de la fenêtre
    "carte": "#1e2128",       # fond des sections
    "bord": "#2c313b",
    "champ": "#262a33",       # champs de saisie, boutons secondaires
    "survol": "#313643",
    "texte": "#e7e9ee",
    "discret": "#8a909c",
    "grise": "#555b66",
    "accent": "#b3262e",      # rouge sombre
    "accent_survol": "#cf3540",
    "accent_presse": "#8f1d24",
    "ok": "#3fb97a",
    "alerte": "#e0a43a",
    "journal": "#101216",
}
POLICE = "Segoe UI"


def _png(largeur, hauteur, pixels):
    """Encode une liste de pixels RGBA (0..255) en PNG, sans bibliothèque externe."""
    import base64
    import struct
    import zlib
    brut = b"".join(b"\x00" + bytes(v for p in pixels[y * largeur:(y + 1) * largeur] for v in p)
                    for y in range(hauteur))

    def bloc(type_, donnees):
        return struct.pack(">I", len(donnees)) + type_ + donnees + struct.pack(">I", zlib.crc32(type_ + donnees))
    png = (b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", largeur, hauteur, 8, 6, 0, 0, 0))
           + bloc(b"IDAT", zlib.compress(brut)) + bloc(b"IEND", b""))
    return base64.b64encode(png)


def _hex(couleur):
    return tuple(int(couleur[i:i + 2], 16) for i in (1, 3, 5))


def dessiner_indicateur(forme, remplissage, bord, coche=None, taille=18, marge=9):
    """Case (forme 'case') ou bouton radio (forme 'rond') lissés, avec coche ou point blanc."""
    def dist_rect(x, y, r=4.5):
        cx, cy, demi = taille / 2, taille / 2, taille / 2 - 1
        qx, qy = abs(x - cx) - (demi - r), abs(y - cy) - (demi - r)
        return (max(qx, 0) ** 2 + max(qy, 0) ** 2) ** 0.5 + min(max(qx, qy), 0) - r

    def dist_rond(x, y, rayon=None):
        return ((x - taille / 2) ** 2 + (y - taille / 2) ** 2) ** 0.5 - (rayon or taille / 2 - 1)

    def dist_segment(x, y, a, b):
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        return ((x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2) ** 0.5

    forme_dist = dist_rect if forme == "case" else dist_rond
    rf, rb, blanc = _hex(remplissage), _hex(bord), (255, 255, 255)
    pixels = []
    for y in range(taille):
        for x in range(taille):
            px, py = x + 0.5, y + 0.5
            d = forme_dist(px, py)
            couverture = max(0.0, min(1.0, 0.5 - d))
            dans_bord = max(0.0, min(1.0, 0.5 - abs(d + 0.5)))      # anneau de 1 px sur le pourtour
            couleur = tuple(round(f * (1 - dans_bord) + b * dans_bord) for f, b in zip(rf, rb))
            if coche == "coche":
                s = taille / 18
                dc = min(dist_segment(px, py, (4.6 * s, 9.4 * s), (7.6 * s, 12.4 * s)),
                         dist_segment(px, py, (7.6 * s, 12.4 * s), (13.4 * s, 5.8 * s))) - 1.05 * s
                k = max(0.0, min(1.0, 0.5 - dc))
                couleur = tuple(round(c_ * (1 - k) + w * k) for c_, w in zip(couleur, blanc))
            elif coche == "point":
                k = max(0.0, min(1.0, 0.5 - dist_rond(px, py, taille / 2 - 5.5)))
                couleur = tuple(round(c_ * (1 - k) + w * k) for c_, w in zip(couleur, blanc))
            pixels.append(couleur + (round(255 * couverture),))
        pixels.extend([(0, 0, 0, 0)] * marge)          # espace transparent avant le texte
    return _png(taille + marge, taille, pixels)


def creer_indicateurs(racine, style):
    """Remplace les indicateurs « à l'ancienne » de clam par des cases et ronds lissés."""
    c = COULEURS
    racine._images_style = images = {}
    for forme, nom_ttk, marque in (("case", "TCheckbutton", "coche"), ("rond", "TRadiobutton", "point")):
        variantes = {
            "vide": (c["champ"], "#4a505c", None),
            "survol": (c["survol"], "#5d6472", None),
            "plein": (c["accent"], c["accent"], marque),
            "plein_survol": (c["accent_survol"], c["accent_survol"], marque),
            "grise": (c["carte"], "#3a3f49", None),
            "grise_plein": ("#3a3f49", "#3a3f49", marque),
        }
        for cle, (remp, bord, m) in variantes.items():
            images[f"{forme}_{cle}"] = tk.PhotoImage(master=racine, data=dessiner_indicateur(forme, remp, bord, m))
        element = f"Moderne.{forme}.indicator"
        style.element_create(element, "image", images[f"{forme}_vide"],
                             ("disabled", "selected", images[f"{forme}_grise_plein"]),
                             ("disabled", images[f"{forme}_grise"]),
                             ("selected", "active", images[f"{forme}_plein_survol"]),
                             ("selected", images[f"{forme}_plein"]),
                             ("active", images[f"{forme}_survol"]),
                             border=0, sticky="w")
        disposition = [("Checkbutton.padding", {"sticky": "nswe", "children": [
            (element, {"side": "left", "sticky": ""}),
            ("Checkbutton.label", {"side": "left", "sticky": "w", "expand": "1"})]})]
        for nom in (nom_ttk, f"Fond.{nom_ttk}"):
            style.layout(nom, disposition)
        style.configure(nom_ttk, padding=(0, 4))


def appliquer_style(racine):
    c = COULEURS
    racine.configure(bg=c["fond"])
    s = ttk.Style(racine)
    s.theme_use("clam")
    s.configure(".", background=c["fond"], foreground=c["texte"], font=(POLICE, 10),
                bordercolor=c["bord"], lightcolor=c["bord"], darkcolor=c["bord"],
                troughcolor=c["champ"], focuscolor=c["accent"], selectbackground=c["accent"],
                selectforeground="#ffffff", insertcolor=c["texte"])
    s.map(".", foreground=[("disabled", c["grise"])])

    s.configure("TFrame", background=c["fond"])
    s.configure("Carte.TFrame", background=c["carte"], relief="solid", borderwidth=1)
    s.configure("TLabel", background=c["fond"])
    s.configure("Carte.TLabel", background=c["carte"])
    s.configure("Titre.TLabel", font=(POLICE, 20, "bold"), foreground="#ffffff")
    s.configure("SousTitre.TLabel", font=(POLICE, 10), foreground=c["discret"])
    s.configure("Section.TLabel", background=c["carte"], font=(POLICE, 9, "bold"), foreground=c["discret"])
    s.configure("Note.TLabel", background=c["carte"], font=(POLICE, 9), foreground=c["discret"])
    for nom, couleur in (("Ok", c["ok"]), ("Neutre", c["discret"]), ("Alerte", c["alerte"])):
        s.configure(f"{nom}.TLabel", background=c["carte"], foreground=couleur, font=(POLICE, 10))

    for nom in ("TCheckbutton", "TRadiobutton"):
        s.configure(nom, background=c["carte"], indicatorbackground=c["champ"],
                    indicatorforeground="#ffffff", indicatorrelief="flat", indicatormargin=(0, 0, 8, 0),
                    upperbordercolor=c["bord"], lowerbordercolor=c["bord"], padding=(0, 3))
        s.map(nom, background=[("active", c["carte"])],
              indicatorbackground=[("disabled", c["carte"]), ("selected", c["accent"]),
                                   ("active", c["survol"])],
              foreground=[("disabled", c["grise"])])
    creer_indicateurs(racine, s)
    s.configure("Fond.TCheckbutton", background=c["fond"])
    s.map("Fond.TCheckbutton", background=[("active", c["fond"])])
    for nom in ("TCheckbutton", "TRadiobutton", "Fond.TCheckbutton"):
        s.configure(nom, padding=(0, 4))

    s.configure("TEntry", fieldbackground=c["champ"], foreground=c["texte"], padding=(8, 6),
                bordercolor=c["bord"], lightcolor=c["champ"], darkcolor=c["champ"])
    s.map("TEntry", bordercolor=[("focus", c["accent"])], lightcolor=[("focus", c["accent"])])

    s.configure("TButton", background=c["champ"], foreground=c["texte"], padding=(14, 7),
                borderwidth=1, bordercolor=c["bord"], lightcolor=c["champ"], darkcolor=c["champ"],
                focusthickness=0, relief="flat")
    s.map("TButton", background=[("disabled", c["carte"]), ("pressed", c["fond"]), ("active", c["survol"])],
          lightcolor=[("active", c["survol"])], darkcolor=[("active", c["survol"])],
          foreground=[("disabled", c["grise"])])
    s.configure("Accent.TButton", background=c["accent"], foreground="#ffffff", bordercolor=c["accent"],
                lightcolor=c["accent"], darkcolor=c["accent"], font=(POLICE, 11, "bold"), padding=(26, 10))
    s.map("Accent.TButton",
          background=[("disabled", c["champ"]), ("pressed", c["accent_presse"]), ("active", c["accent_survol"])],
          lightcolor=[("active", c["accent_survol"])], darkcolor=[("active", c["accent_survol"])],
          bordercolor=[("active", c["accent_survol"])])
    s.configure("Danger.TButton", foreground="#f08a8f")
    # barre de défilement fine, sans flèches
    s.layout("Mince.Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
    s.configure("Mince.Vertical.TScrollbar", background=c["survol"], troughcolor=c["journal"], borderwidth=0,
                bordercolor=c["journal"], lightcolor=c["survol"], darkcolor=c["survol"], arrowsize=8,
                gripcount=0, width=8)
    s.map("Mince.Vertical.TScrollbar", background=[("active", "#4a505c")],
          lightcolor=[("active", "#4a505c")], darkcolor=[("active", "#4a505c")])


def barre_titre_sombre(fenetre):
    """Barre de titre sombre sous Windows 10/11 (sans effet ailleurs)."""
    try:
        import ctypes
        fenetre.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(fenetre.winfo_id())
        valeur = ctypes.c_int(1)
        for attribut in (20, 19):          # DWMWA_USE_IMMERSIVE_DARK_MODE (récent, puis ancien)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribut, ctypes.byref(valeur), 4) == 0:
                break
    except Exception:
        pass


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITRE)
        self.minsize(720, 700)
        icone = trouver_ressource("icone.ico", ("",))
        if icone:
            try:
                self.iconbitmap(default=str(icone))   # barre de titre et barre des tâches
            except tk.TclError:
                pass
        appliquer_style(self)
        self.donnees = trouver_ressource(gen.FICHIER_PAR_DEFAUT)
        self.dll = trouver_ressource("xinput1_4.dll")

        self.personnage = tk.StringVar(value="Chris")
        self.difficulte = tk.StringVar(value="Normal")
        self.armes = tk.BooleanVar(value=False)
        self.cles = tk.BooleanVar(value=False)
        self.graine = tk.StringVar(value=str(gen.tirer_graine()))
        jeu = gen.trouver_dossier_jeu()
        self.dossier_jeu = tk.StringVar(value=str(jeu) if jeu else "")
        self.installer = tk.BooleanVar(value=True)
        self.afficher_spoiler = tk.BooleanVar(value=False)
        self.etat_jeu = tk.StringVar()
        self.dossier_seeds = dossier_programme() / "seeds"

        self.construire()
        self.dossier_jeu.trace_add("write", lambda *_: self.actualiser_etat())
        self.actualiser_etat()
        barre_titre_sombre(self)

    # ------------------------------------------------------------------ interface
    def carte(self, parent, titre):
        """Section à fond légèrement plus clair, avec un petit titre en capitales."""
        cadre = ttk.Frame(parent, style="Carte.TFrame", padding=(16, 12, 16, 14))
        ttk.Label(cadre, text=titre.upper(), style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        interieur = ttk.Frame(cadre, style="Carte.TFrame", borderwidth=0)
        interieur.pack(fill="both", expand=True)
        return cadre, interieur

    def construire(self):
        cadre = ttk.Frame(self, padding=(20, 16, 20, 20))
        cadre.pack(fill="both", expand=True)
        cadre.columnconfigure(0, weight=1, uniform="col")
        cadre.columnconfigure(1, weight=1, uniform="col")

        entete = ttk.Frame(cadre)
        entete.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(entete, text="Randomizer", style="Titre.TLabel").pack(side="left")
        ttk.Label(entete, text=f"Resident Evil HD Remaster  ·  v{VERSION}",
                  style="SousTitre.TLabel").pack(side="left", padx=(12, 0), pady=(10, 0))

        # --- Partie
        partie, p = self.carte(cadre, "Partie")
        partie.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        p.columnconfigure(1, weight=1)
        ttk.Label(p, text="Personnage", style="Carte.TLabel").grid(row=0, column=0, sticky="w")
        for i, (nom, dispo) in enumerate((("Chris", True), ("Jill  · à venir", False))):
            ttk.Radiobutton(p, text=nom, value=nom.split()[0], variable=self.personnage,
                            state="normal" if dispo else "disabled").grid(row=1 + i, column=0, sticky="w")
        ttk.Label(p, text="Difficulté", style="Carte.TLabel").grid(row=0, column=1, sticky="w", padx=(24, 0))
        for i, nom in enumerate(("Très facile", "Facile", "Normal", "Difficile", "Real Survival")):
            dispo = nom == "Normal"
            ttk.Radiobutton(p, text=nom if dispo else f"{nom}  · à venir", value=nom,
                            variable=self.difficulte, state="normal" if dispo else "disabled"
                            ).grid(row=1 + i, column=1, sticky="w", padx=(24, 0))

        # --- Options
        options, o = self.carte(cadre, "Options")
        options.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        ttk.Checkbutton(o, text="Armes aléatoires", variable=self.armes).pack(anchor="w")
        ttk.Label(o, text="Le pistolet du hall est mélangé lui aussi.",
                  style="Note.TLabel").pack(anchor="w", padx=(26, 0))
        ttk.Checkbutton(o, text="Clés aléatoires  · à venir", variable=self.cles,
                        state="disabled").pack(anchor="w", pady=(6, 0))
        ttk.Label(o, text="Graine", style="Carte.TLabel").pack(anchor="w", pady=(14, 4))
        ligne = ttk.Frame(o, style="Carte.TFrame", borderwidth=0)
        ligne.pack(anchor="w", fill="x")
        ttk.Entry(ligne, textvariable=self.graine, width=14, font=(POLICE, 11)).pack(side="left")
        ttk.Button(ligne, text="Au hasard",
                   command=lambda: self.graine.set(str(gen.tirer_graine()))).pack(side="left", padx=(8, 0))
        ttk.Label(o, text="Même graine + mêmes options = même résultat.",
                  style="Note.TLabel").pack(anchor="w", pady=(6, 0))

        # --- Jeu
        jeu, j = self.carte(cadre, "Jeu")
        jeu.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=(16, 0))
        j.columnconfigure(0, weight=1)
        ttk.Entry(j, textvariable=self.dossier_jeu).grid(row=0, column=0, sticky="ew")
        ttk.Button(j, text="Parcourir…", command=self.choisir_dossier).grid(row=0, column=1, padx=(8, 0))
        etats = ttk.Frame(j, style="Carte.TFrame", borderwidth=0)
        etats.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.badge_dll = ttk.Label(etats, style="Neutre.TLabel")
        self.badge_dll.pack(side="left")
        self.badge_seed = ttk.Label(etats, style="Neutre.TLabel")
        self.badge_seed.pack(side="left", padx=(24, 0))
        self.badge_version = ttk.Label(j, style="Alerte.TLabel")
        self.badge_version.grid(row=5, column=0, columnspan=2, sticky="w")
        gestion = ttk.Frame(j, style="Carte.TFrame", borderwidth=0)
        gestion.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.bouton_dll = ttk.Button(gestion, text="Installer la DLL", command=self.installer_dll)
        self.bouton_dll.pack(side="left")
        self.bouton_retirer_dll = ttk.Button(gestion, text="Désinstaller la DLL", style="Danger.TButton",
                                             command=self.retirer_dll)
        self.bouton_retirer_dll.pack(side="left", padx=8)
        self.bouton_retirer_seed = ttk.Button(gestion, text="Supprimer la seed installée",
                                              style="Danger.TButton", command=self.retirer_seed)
        self.bouton_retirer_seed.pack(side="left")
        ttk.Label(j, text="Désinstaller la DLL suffit pour retrouver le jeu d'origine.",
                  style="Note.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Checkbutton(j, text="Installer la seed dans le jeu après génération",
                        variable=self.installer).grid(row=4, column=0, sticky="w", pady=(8, 0))

        # --- Actions
        boutons = ttk.Frame(cadre)
        boutons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 0))
        self.bouton_generer = ttk.Button(boutons, text="Générer la seed", style="Accent.TButton",
                                         command=self.generer)
        self.bouton_generer.pack(side="left")
        ttk.Button(boutons, text="Dossier des seeds",
                   command=self.ouvrir_seeds).pack(side="left", padx=(10, 0))
        ttk.Button(boutons, text="Journal du jeu",
                   command=self.ouvrir_journal).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(boutons, text="Afficher le spoiler", style="Fond.TCheckbutton",
                        variable=self.afficher_spoiler).pack(side="right")

        # --- Journal
        zone = tk.Frame(cadre, bg=COULEURS["bord"], padx=1, pady=1)
        zone.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        cadre.rowconfigure(4, weight=1)
        self.journal = tk.Text(zone, width=1, height=10, wrap="word", state="disabled", font=("Consolas", 10),
                               bg=COULEURS["journal"], fg=COULEURS["texte"], insertbackground=COULEURS["texte"],
                               selectbackground=COULEURS["accent"], relief="flat", borderwidth=0,
                               padx=12, pady=10, highlightthickness=0)
        defil = ttk.Scrollbar(zone, orient="vertical", style="Mince.Vertical.TScrollbar",
                              command=self.journal.yview)
        self.journal.configure(yscrollcommand=defil.set)
        defil.pack(side="right", fill="y")
        self.journal.pack(side="left", fill="both", expand=True)

        if not self.donnees:
            self.ecrire(f"Fichier de données {gen.FICHIER_PAR_DEFAUT} introuvable : génération impossible.")
            self.bouton_generer.state(["disabled"])
        else:
            self.ecrire("Prêt. Choisis tes options puis « Générer la seed ».")

    # ------------------------------------------------------------------ actions
    def ecrire(self, texte, effacer=False):
        self.journal.configure(state="normal")
        if effacer:
            self.journal.delete("1.0", "end")
        self.journal.insert("end", texte + "\n")
        self.journal.see("end")
        self.journal.configure(state="disabled")

    def choisir_dossier(self):
        d = filedialog.askdirectory(title="Dossier du jeu (celui qui contient bhd.exe)",
                                    initialdir=self.dossier_jeu.get() or None)
        if d:
            self.dossier_jeu.set(str(Path(d)))

    def actualiser_etat(self):
        d = Path(self.dossier_jeu.get()) if self.dossier_jeu.get() else None
        if not d or not (d / "bhd.exe").exists():
            self.etat_jeu.set("Jeu introuvable : indique le dossier qui contient bhd.exe.")
            self.badge_dll.configure(text="●  Jeu introuvable : indique le dossier qui contient bhd.exe",
                                     style="Alerte.TLabel")
            self.badge_seed.configure(text="")
            self.badge_version.configure(text="")
            for b in (self.bouton_dll, self.bouton_retirer_dll, self.bouton_retirer_seed):
                b.state(["disabled"])
            return
        dll = d / "xinput1_4.dll"
        dll_ok = dll.exists()
        etranger = dll_ok and not est_notre_dll(dll)
        seed = gen.seed_installee(d)
        if etranger:
            self.badge_dll.configure(text="●  Un autre xinput1_4.dll est présent", style="Alerte.TLabel")
        elif dll_ok:
            self.badge_dll.configure(text="●  Randomizer installé", style="Ok.TLabel")
        else:
            self.badge_dll.configure(text="●  Jeu d'origine (DLL non installée)", style="Neutre.TLabel")
        self.badge_version.configure(
            text="" if version_jeu_ok(d) else
            "●  Version de bhd.exe non prise en charge : le randomizer restera inactif (jeu inchangé).")
        if seed:
            self.badge_seed.configure(text=f"●  Seed {seed[0]}{' · armes' if seed[1] else ''}", style="Ok.TLabel")
        else:
            self.badge_seed.configure(text="●  Aucune seed installée", style="Neutre.TLabel")
        self.etat_jeu.set(
            "DLL du randomizer : " + ("installée" if dll_ok and not etranger else
                                      "un AUTRE xinput1_4.dll est présent (pas celui du randomizer)"
                                      if etranger else "NON installée (jeu d'origine)") + "\n"
            f"Seed installée : {f'{seed[0]}' + (' (armes)' if seed[1] else '') if seed else 'aucune'}")
        self.bouton_dll.configure(text="Mettre à jour la DLL" if dll_ok and not etranger else "Installer la DLL")
        self.bouton_dll.state(["!disabled"] if self.dll and not etranger else ["disabled"])
        self.bouton_retirer_dll.state(["!disabled"] if dll_ok and not etranger else ["disabled"])
        self.bouton_retirer_seed.state(["!disabled"] if seed else ["disabled"])

    def supprimer(self, fichier, quoi):
        try:
            fichier.unlink()
            self.ecrire(f"{quoi} supprimée : {fichier}", effacer=True)
        except FileNotFoundError:
            pass
        except OSError as e:
            messagebox.showerror(TITRE, f"Impossible de supprimer {fichier.name} :\n{e}\n\n"
                                        "Le jeu est-il encore lancé ? Ferme-le puis réessaie.")
        self.actualiser_etat()

    def retirer_dll(self):
        dll = Path(self.dossier_jeu.get()) / "xinput1_4.dll"
        if not est_notre_dll(dll):        # sécurité : ne jamais supprimer la DLL d'un autre mod
            messagebox.showwarning(TITRE, "Ce xinput1_4.dll n'est pas celui du randomizer : il n'est pas supprimé.")
            self.actualiser_etat()
            return
        if messagebox.askyesno(TITRE, "Désinstaller la DLL du randomizer ?\n\n"
                                      "Le jeu redeviendra le jeu d'origine au prochain lancement. "
                                      "La seed installée est conservée (elle ne sert plus à rien sans la DLL)."):
            self.supprimer(dll, "DLL du randomizer")
            if not dll.exists():
                self.ecrire("Le jeu se lancera sans randomizer. Pour le remettre : « Installer la DLL ».")

    def retirer_seed(self):
        cible = Path(self.dossier_jeu.get()) / gen.NOM_SEED_JEU
        seed = gen.seed_installee(cible.parent)
        if seed and messagebox.askyesno(TITRE, f"Supprimer la seed installée ({seed[0]}"
                                               f"{' avec armes' if seed[1] else ''}) ?\n\n"
                                               "Ses fichiers restent dans le dossier des seeds. "
                                               "Sans seed, la DLL laisse le jeu tel quel."):
            self.supprimer(cible, "Seed installée")

    def installer_dll(self):
        cible = Path(self.dossier_jeu.get()) / "xinput1_4.dll"
        if not version_jeu_ok(cible.parent) and not messagebox.askyesno(
                TITRE, "Ta version de bhd.exe n'est pas celle prise en charge.\n\n"
                       "La DLL restera inactive (le jeu ne sera pas modifié). L'installer quand même ?"):
            return
        try:
            shutil.copyfile(self.dll, cible)
            self.ecrire(f"DLL installée : {cible}\nPour désinstaller : supprimer ce fichier.")
        except OSError as e:
            messagebox.showerror(TITRE, f"Impossible de copier la DLL :\n{e}\n\n"
                                        "Le jeu est-il encore lancé ?")
        self.actualiser_etat()

    def ouvrir_journal(self):
        journal = Path(self.dossier_jeu.get()) / "randomizer_journal.txt"
        if journal.exists():
            os.startfile(journal)
        else:
            messagebox.showinfo(TITRE, "Pas encore de journal : il se crée au premier lancement du jeu "
                                       "avec la DLL installée.")

    def ouvrir_seeds(self):
        self.dossier_seeds.mkdir(parents=True, exist_ok=True)
        os.startfile(self.dossier_seeds)

    def generer(self):
        try:
            graine = int(self.graine.get().strip())
            if graine < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(TITRE, "La graine doit être un nombre entier positif.")
            return
        installer = self.installer.get()
        if installer and not (Path(self.dossier_jeu.get()) / "bhd.exe").exists():
            messagebox.showwarning(TITRE, "Dossier du jeu introuvable : choisis-le, ou décoche l'installation.")
            return

        self.bouton_generer.state(["disabled"])
        self.ecrire("Génération…", effacer=True)
        afficher = self.afficher_spoiler.get()
        messages = []

        def dire(texte):
            # Le premier message est le spoiler complet : sans « Afficher le spoiler », on n'en garde
            # que le résumé (deux premières lignes).
            if not messages and not afficher:
                texte = "\n".join(texte.splitlines()[:2]) + "\n(spoiler masqué : voir le fichier _spoiler.txt)"
            messages.append(texte)

        def travail():
            try:
                ok = gen.produire(graine, self.armes.get(), self.donnees, self.dossier_seeds,
                                  installer, self.dossier_jeu.get() or None, dire)
            except Exception as e:  # on affiche l'erreur plutôt que de fermer l'application
                messages.append(f"ERREUR : {e}")
                ok = False
            self.after(0, lambda: self.fin_generation(messages, ok))

        threading.Thread(target=travail, daemon=True).start()

    def fin_generation(self, messages, ok):
        self.ecrire("\n".join(messages), effacer=True)
        if not ok:
            self.ecrire("\nLa génération ou l'installation a échoué.")
        self.bouton_generer.state(["!disabled"])
        self.actualiser_etat()


if __name__ == "__main__":
    Application().mainloop()
