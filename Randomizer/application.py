"""
Application du randomizer Resident Evil HD Remaster : génère et installe une seed en quelques clics.

Toute la logique est dans generateur_seed.py (partagée avec la ligne de commande) ; ce fichier ne fait
que l'interface. Les options pas encore prises en charge sont visibles mais grisées (« à venir »).

Lancer sans compiler :  python application.py
Construire le .exe   :  construire_exe.bat
"""
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

import generateur_seed as gen
import progression
import textes

VERSION = "0.6.1"
TAILLE_BHD_EXE = 9640360
URL_DEPOT = "https://github.com/Michiy0/RE-HD-Randomizer"
SHA256_BHD_EXE = "39B840663E4B1A6835C60CBD176E4EE6C21B9197FC2C2DD733F2A7C36A0B429A"
TITRE = f"Randomizer RE HD Remaster v{VERSION}"
SOUS_WINDOWS = sys.platform == "win32"
# Le jeu tourne sous Proton sur Linux / Steam Deck : la DLL doit être préférée à celle de Proton.
OPTION_PROTON = 'WINEDLLOVERRIDES="xinput1_4=n,b" %command%'


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


def lire_option_ini(dossier, cle):
    """Valeur d'une option de la section [Randomizer] de randomizer.ini (None si absente)."""
    ini = Path(dossier) / "randomizer.ini"
    if not ini.exists():
        return None
    section = False
    for ligne in ini.read_text(encoding="utf-8", errors="replace").splitlines():
        l = ligne.strip()
        if l.startswith("["):
            section = l.lower() == "[randomizer]"
        elif section and not l.startswith(";") and "=" in l and l.split("=", 1)[0].strip().lower() == cle.lower():
            return l.split("=", 1)[1].strip()
    return None


def ecrire_option_ini(dossier, cle, valeur):
    """Règle (ou retire si valeur est None) une option de [Randomizer] en gardant le reste du fichier."""
    ini = Path(dossier) / "randomizer.ini"
    lignes = ini.read_text(encoding="utf-8", errors="replace").splitlines() if ini.exists() else []
    if not any(l.strip().lower() == "[randomizer]" for l in lignes):
        lignes = ["[Randomizer]"] + lignes
    resultat, section, fait = [], False, False
    for ligne in lignes:
        l = ligne.strip()
        if l.startswith("["):
            if section and not fait and valeur is not None:
                resultat.append(f"{cle}={valeur}")
                fait = True
            section = l.lower() == "[randomizer]"
        elif section and not l.startswith(";") and "=" in l and l.split("=", 1)[0].strip().lower() == cle.lower():
            if valeur is not None and not fait:
                resultat.append(f"{cle}={valeur}")
                fait = True
            continue
        resultat.append(ligne)
    if section and not fait and valeur is not None:
        resultat.append(f"{cle}={valeur}")
    ini.write_text("\r\n".join(resultat) + "\r\n", encoding="utf-8", newline="")


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
    if getattr(racine, "_images_style", None):        # déjà créés : le thème est simplement réappliqué
        return
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
                gripcount=0, width=8 if SOUS_WINDOWS else 14)
    s.map("Mince.Vertical.TScrollbar", background=[("active", "#4a505c")],
          lightcolor=[("active", "#4a505c")], darkcolor=[("active", "#4a505c")])
    # onglets : plats, sans pointillés de focus, l'onglet actif prend la couleur des cartes
    s.configure("TNotebook", background=c["fond"], borderwidth=0, bordercolor=c["fond"],
                lightcolor=c["fond"], darkcolor=c["fond"], tabmargins=(0, 0, 0, 0))
    s.layout("TNotebook.Tab", [("Notebook.tab", {"sticky": "nswe", "children": [
        ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
            ("Notebook.label", {"side": "top", "sticky": ""})]})]})])
    s.configure("TNotebook.Tab", background=c["fond"], foreground=c["discret"], padding=(18, 9),
                font=(POLICE, 10, "bold"), borderwidth=0, bordercolor=c["fond"], lightcolor=c["fond"],
                darkcolor=c["fond"])
    s.map("TNotebook.Tab", background=[("selected", c["carte"]), ("active", c["survol"])],
          foreground=[("selected", c["texte"]), ("active", c["texte"])],
          bordercolor=[("selected", c["bord"])], lightcolor=[("selected", c["carte"])],
          darkcolor=[("selected", c["carte"])])
    # liste déroulante (sélecteur de langue)
    s.configure("TCombobox", fieldbackground=c["champ"], background=c["champ"], foreground=c["texte"],
                arrowcolor=c["texte"], bordercolor=c["bord"], lightcolor=c["champ"], darkcolor=c["champ"],
                padding=(8, 4))
    s.map("TCombobox", fieldbackground=[("readonly", c["champ"])], foreground=[("readonly", c["texte"])],
          selectbackground=[("readonly", c["champ"])], selectforeground=[("readonly", c["texte"])],
          background=[("active", c["survol"])], bordercolor=[("focus", c["accent"])])
    racine.option_add("*TCombobox*Listbox.background", c["champ"])
    racine.option_add("*TCombobox*Listbox.foreground", c["texte"])
    racine.option_add("*TCombobox*Listbox.selectBackground", c["accent"])
    racine.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    racine.option_add("*TCombobox*Listbox.font", (POLICE, 10))


# Polices candidates, de la préférée à la plus courante (Windows puis Linux / Steam Deck)
CANDIDATES_POLICES = {
    "base": ("Segoe UI", "Noto Sans", "Cantarell", "DejaVu Sans", "Helvetica"),
    "ja": ("Yu Gothic UI", "Noto Sans CJK JP", "Noto Sans JP", "IPAGothic", "Droid Sans Fallback", "Helvetica"),
    "zh": ("Microsoft YaHei UI", "Noto Sans CJK SC", "Noto Sans SC", "WenQuanYi Micro Hei", "Droid Sans Fallback",
           "Helvetica"),
    "mono": ("Consolas", "DejaVu Sans Mono", "Noto Sans Mono", "Liberation Mono", "Courier"),
}
POLICE_MONO = "Consolas"


def premiere_police(candidates):
    """Première police installée de la liste (la dernière, générique, sinon)."""
    try:
        installees = set(tkfont.families())
    except tk.TclError:
        installees = set()
    return next((p for p in candidates if p in installees), candidates[-1])


def choisir_police(langue):
    """Polices de l'interface : une police avec idéogrammes pour le japonais et le chinois."""
    global POLICE, POLICE_MONO
    POLICE = premiere_police(CANDIDATES_POLICES.get(langue if langue in ("ja", "zh") else "base"))
    POLICE_MONO = premiere_police(CANDIDATES_POLICES["mono"])


def ouvrir(chemin):
    """Ouvre un fichier ou un dossier avec le programme du système."""
    if SOUS_WINDOWS:
        os.startfile(chemin)
    else:
        subprocess.Popen(["xdg-open", str(chemin)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fichier_preferences():
    if os.environ.get("APPDATA"):
        base = Path(os.environ["APPDATA"])
    else:                                       # Linux : ~/.config
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "RandomizerREHD" / "preferences.ini"


def lire_langue():
    """Préférence enregistrée : « auto » (langue de Windows) ou un code de langue. « auto » par défaut."""
    try:
        for ligne in fichier_preferences().read_text(encoding="utf-8").splitlines():
            if ligne.startswith("langue="):
                code = ligne.split("=", 1)[1].strip()
                if code == "auto" or code in textes.LANGUES:
                    return code
    except OSError:
        pass
    return "auto"


def langue_effective(preference):
    """Langue réellement utilisée : la langue de Windows si « auto » (anglais si elle n'est pas proposée)."""
    return textes.langue_systeme() if preference == "auto" else preference


def enregistrer_langue(code):
    try:
        f = fichier_preferences()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f"langue={code}\n", encoding="utf-8")
    except OSError:
        pass                        # préférence perdue, sans gravité


class Defilable(ttk.Frame):
    """Zone qui défile verticalement quand son contenu dépasse (petits écrans, Steam Deck 1280×800).
    Le contenu se place dans .interieur ; la barre n'apparaît que si elle sert."""

    def __init__(self, parent):
        super().__init__(parent)
        self.toile = tk.Canvas(self, bg=COULEURS["fond"], highlightthickness=0, borderwidth=0,
                               yscrollincrement=24)
        self.barre = ttk.Scrollbar(self, orient="vertical", style="Mince.Vertical.TScrollbar",
                                   command=self.toile.yview)
        self.interieur = ttk.Frame(self.toile)
        self._fenetre = self.toile.create_window(0, 0, window=self.interieur, anchor="nw")
        self.toile.configure(yscrollcommand=self._regler_barre)
        self.toile.pack(side="left", fill="both", expand=True)
        self.interieur.bind("<Configure>", lambda _: self.toile.configure(scrollregion=self.toile.bbox("all")))
        self.toile.bind("<Configure>", lambda e: self.toile.itemconfigure(self._fenetre, width=e.width))

    def _regler_barre(self, debut, fin):
        self.barre.set(debut, fin)
        utile = float(debut) > 0 or float(fin) < 1
        if utile and not self.barre.winfo_ismapped():
            self.barre.pack(side="right", fill="y", padx=(6, 0), before=self.toile)
        elif not utile and self.barre.winfo_ismapped():
            self.barre.pack_forget()

    def defiler(self, pas):
        if self.toile.yview() != (0.0, 1.0):
            self.toile.yview_scroll(pas, "units")


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
        # taille adaptée à l'écran : le Steam Deck (1280×800, barre des tâches comprise) laisse ~720 px
        largeur_ecran, hauteur_ecran = self.winfo_screenwidth(), self.winfo_screenheight()
        self.minsize(640, 480)
        self.geometry(f"{min(780, largeur_ecran - 40)}x{min(880, hauteur_ecran - 80)}")
        icone = trouver_ressource("icone.ico" if SOUS_WINDOWS else "icone.png", ("",))
        if icone:
            try:
                if SOUS_WINDOWS:
                    self.iconbitmap(default=str(icone))   # barre de titre et barre des tâches
                else:
                    self._icone = tk.PhotoImage(file=str(icone))
                    self.iconphoto(True, self._icone)
            except tk.TclError:
                pass
        self.preference_langue = lire_langue()                 # « auto » ou un code de langue
        self.langue = tk.StringVar(value=langue_effective(self.preference_langue))
        choisir_police(self.langue.get())
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
        self.releve = tk.BooleanVar(value=False)
        self.etat_jeu = tk.StringVar()             # résumé texte de l'état (utilisé par les tests)
        self.dossier_seeds = dossier_programme() / "seeds"
        self.dernier_resultat = None               # (messages, spoiler, ok) de la dernière génération

        self.construire()
        self.dossier_jeu.trace_add("write", lambda *_: self.actualiser_etat())
        self.actualiser_etat()
        self.afficher_resultat()
        barre_titre_sombre(self)
        # molette (Windows) et molette / pavé tactile (Linux) : fait défiler la zone sous le pointeur
        self.bind_all("<MouseWheel>", lambda e: self.molette(e, -1 if e.delta > 0 else 1))
        self.bind_all("<Button-4>", lambda e: self.molette(e, -1))
        self.bind_all("<Button-5>", lambda e: self.molette(e, 1))

    def molette(self, evenement, sens):
        w = self.winfo_containing(evenement.x_root, evenement.y_root)
        while w is not None:
            if isinstance(w, (tk.Text, ttk.Combobox)):   # ils défilent déjà tout seuls
                return
            if isinstance(w, Defilable):
                w.defiler(3 * sens)
                return
            w = w.master

    def t(self, cle, **valeurs):
        """Texte dans la langue choisie."""
        return textes.tr(cle, self.langue.get(), **valeurs)

    # ------------------------------------------------------------------ interface
    def carte(self, parent, titre):
        """Section à fond légèrement plus clair, avec un petit titre en capitales."""
        cadre = ttk.Frame(parent, style="Carte.TFrame", padding=(16, 12, 16, 14))
        ttk.Label(cadre, text=titre.upper(), style="Section.TLabel").pack(anchor="w", pady=(0, 8))
        interieur = ttk.Frame(cadre, style="Carte.TFrame", borderwidth=0)
        interieur.pack(fill="both", expand=True)
        return cadre, interieur

    def police_texte(self):
        """Police des zones de texte : Consolas (latin, cyrillique) ou la police de la langue."""
        return (POLICE_MONO, 10) if self.langue.get() not in ("ja", "zh") else (POLICE, 10)

    def construire(self):
        self.racine = racine = ttk.Frame(self, padding=(20, 16, 20, 20))
        racine.pack(fill="both", expand=True)

        entete = ttk.Frame(racine)
        entete.pack(fill="x", pady=(0, 12))
        ttk.Label(entete, text="Randomizer", style="Titre.TLabel").pack(side="left")
        ttk.Label(entete, text=f"Resident Evil HD Remaster  ·  v{VERSION}",
                  style="SousTitre.TLabel").pack(side="left", padx=(12, 0), pady=(10, 0))
        # sélecteur de langue, en haut à droite
        auto = f"{self.t('langue_auto')} ({textes.LANGUES[textes.langue_systeme()]})"
        noms = [auto] + list(textes.LANGUES.values())
        self.choix_langue = ttk.Combobox(entete, values=noms, state="readonly", font=(POLICE, 10),
                                         width=max(12, len(auto) + 2))
        self.choix_langue.set(auto if self.preference_langue == "auto" else textes.LANGUES[self.langue.get()])
        self.choix_langue.pack(side="right", pady=(8, 0))
        self.choix_langue.bind("<<ComboboxSelected>>", lambda _: self.changer_langue())
        if SOUS_WINDOWS:                            # sous Linux, pas toujours de police d'emoji
            ttk.Label(entete, text="🌐", style="SousTitre.TLabel").pack(side="right", padx=(0, 6), pady=(8, 0))

        self.onglets = ttk.Notebook(racine)
        self.onglets.pack(fill="both", expand=True)
        page_jeu = ttk.Frame(self.onglets, padding=(0, 14, 0, 0))
        page_spoiler = ttk.Frame(self.onglets, padding=(0, 14, 0, 0))
        page_aide = ttk.Frame(self.onglets, padding=(0, 14, 0, 0))
        self.onglets.add(page_jeu, text=self.t("onglet_randomizer"))
        self.onglets.add(page_spoiler, text=self.t("onglet_spoiler"))
        self.onglets.add(page_aide, text=self.t("onglet_aide"))
        self.construire_randomizer(page_jeu)
        self.construire_spoiler(page_spoiler)
        self.construire_aide(page_aide)

        if not self.donnees:
            self.ecrire(self.t("donnees_absentes", fichier=gen.FICHIER_PAR_DEFAUT))
            self.bouton_generer.state(["disabled"])
        else:
            self.ecrire(self.t("pret"))

    def changer_langue(self):
        i = self.choix_langue.current()            # 0 = automatique, puis les langues dans l'ordre
        preference = "auto" if i <= 0 else textes.ORDRE[i - 1]
        code = langue_effective(preference)
        if preference == self.preference_langue and code == self.langue.get():
            return
        onglet = self.onglets.index("current")
        self.preference_langue = preference
        self.langue.set(code)
        enregistrer_langue(preference)
        choisir_police(code)
        appliquer_style(self)                       # polices du thème dans la nouvelle langue
        self.racine.destroy()                       # on reconstruit la fenêtre : les choix sont gardés
        self.construire()
        self.onglets.select(onglet)
        self.actualiser_etat()
        self.afficher_resultat()

    # --- onglet « Randomizer » : de quoi jouer, dans l'ordre (DLL, puis options, puis génération)
    def construire_randomizer(self, page):
        # les cartes défilent si l'écran est petit ; le bouton Générer et le journal restent visibles en bas
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)
        defile = Defilable(page)
        defile.grid(row=0, column=0, sticky="nsew")
        cadre = defile.interieur
        cadre.columnconfigure(0, weight=1, uniform="col")
        cadre.columnconfigure(1, weight=1, uniform="col")

        # --- Jeu (en premier : on installe la DLL avant de générer une seed)
        jeu, j = self.carte(cadre, self.t("carte_jeu"))
        jeu.grid(row=0, column=0, columnspan=2, sticky="nsew")
        j.columnconfigure(0, weight=1)
        ttk.Entry(j, textvariable=self.dossier_jeu).grid(row=0, column=0, sticky="ew")
        ttk.Button(j, text=self.t("parcourir"), command=self.choisir_dossier).grid(row=0, column=1, padx=(8, 0))
        etats = ttk.Frame(j, style="Carte.TFrame", borderwidth=0)
        etats.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.badge_dll = ttk.Label(etats, style="Neutre.TLabel")
        self.badge_dll.pack(side="left")
        self.badge_seed = ttk.Label(etats, style="Neutre.TLabel")
        self.badge_seed.pack(side="left", padx=(24, 0))
        self.badge_version = ttk.Label(j, style="Alerte.TLabel", wraplength=640, justify="left")
        self.badge_version.grid(row=2, column=0, columnspan=2, sticky="w")
        gestion = ttk.Frame(j, style="Carte.TFrame", borderwidth=0)
        gestion.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.bouton_dll = ttk.Button(gestion, text=self.t("installer_dll"), command=self.installer_dll)
        self.bouton_dll.pack(side="left")
        self.bouton_retirer_dll = ttk.Button(gestion, text=self.t("desinstaller_dll"), style="Danger.TButton",
                                             command=self.retirer_dll)
        self.bouton_retirer_dll.pack(side="left", padx=8)
        self.bouton_retirer_seed = ttk.Button(gestion, text=self.t("supprimer_seed"),
                                              style="Danger.TButton", command=self.retirer_seed)
        self.bouton_retirer_seed.pack(side="left")
        ttk.Label(j, text=self.t("note_desinstaller"),
                  style="Note.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))
        if not SOUS_WINDOWS or os.environ.get("RANDOMIZER_LINUX"):
            # Sous Linux / Steam Deck, le jeu passe par Proton : l'option de lancement fait charger notre DLL
            ttk.Label(j, text=self.t("proton_titre"), style="Carte.TLabel").grid(
                row=5, column=0, columnspan=2, sticky="w", pady=(12, 2))
            option = ttk.Entry(j, font=(POLICE_MONO, 10))
            option.insert(0, OPTION_PROTON)
            option.state(["readonly"])
            option.grid(row=6, column=0, sticky="ew")
            ttk.Button(j, text=self.t("copier"), command=self.copier_option_proton).grid(
                row=6, column=1, padx=(8, 0))
            ttk.Label(j, text=self.t("proton_note"), style="Note.TLabel", wraplength=640,
                      justify="left").grid(row=7, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # --- Partie
        partie, p = self.carte(cadre, self.t("carte_partie"))
        partie.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(16, 0))
        p.columnconfigure(1, weight=1)
        a_venir = f"  · {self.t('a_venir')}"
        ttk.Label(p, text=self.t("personnage"), style="Carte.TLabel").grid(row=0, column=0, sticky="w")
        for i, (nom, dispo) in enumerate((("Chris", True), ("Jill", False))):
            ttk.Radiobutton(p, text=nom if dispo else nom + a_venir, value=nom, variable=self.personnage,
                            state="normal" if dispo else "disabled").grid(row=1 + i, column=0, sticky="w")
        ttk.Label(p, text=self.t("difficulte"), style="Carte.TLabel").grid(row=0, column=1, sticky="w",
                                                                         padx=(24, 0))
        for i, nom in enumerate(("Très facile", "Facile", "Normal", "Difficile", "Real Survival")):
            dispo = nom == "Normal"
            libelle = self.t(f"diff_{nom}")
            ttk.Radiobutton(p, text=libelle if dispo else libelle + a_venir, value=nom,
                            variable=self.difficulte, state="normal" if dispo else "disabled"
                            ).grid(row=1 + i, column=1, sticky="w", padx=(24, 0))

        # --- Options
        options, o = self.carte(cadre, self.t("carte_options"))
        options.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(16, 0))
        ttk.Checkbutton(o, text=self.t("armes_aleatoires"), variable=self.armes).pack(anchor="w")
        ttk.Label(o, text=self.t("note_armes"), style="Note.TLabel", wraplength=280,
                  justify="left").pack(anchor="w", padx=(27, 0))
        ttk.Checkbutton(o, text=self.t("cles_aleatoires") + a_venir, variable=self.cles,
                        state="disabled").pack(anchor="w", pady=(6, 0))
        ttk.Label(o, text=self.t("graine"), style="Carte.TLabel").pack(anchor="w", pady=(14, 4))
        ligne = ttk.Frame(o, style="Carte.TFrame", borderwidth=0)
        ligne.pack(anchor="w", fill="x")
        ttk.Entry(ligne, textvariable=self.graine, width=14, font=(POLICE, 11)).pack(side="left")
        ttk.Button(ligne, text=self.t("au_hasard"),
                   command=lambda: self.graine.set(str(gen.tirer_graine()))).pack(side="left", padx=(8, 0))
        ttk.Label(o, text=self.t("note_graine"), style="Note.TLabel", wraplength=280,
                  justify="left").pack(anchor="w", pady=(6, 0))

        # --- Actions
        boutons = ttk.Frame(page)
        boutons.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        self.bouton_generer = ttk.Button(boutons, text=self.t("generer"), style="Accent.TButton",
                                         command=self.generer)
        self.bouton_generer.pack(side="left")
        ttk.Checkbutton(boutons, text=self.t("installer_seed_case"), style="Fond.TCheckbutton",
                        variable=self.installer).pack(side="left", padx=(16, 0))
        ttk.Button(boutons, text=self.t("dossier_seeds"),
                   command=self.ouvrir_seeds).pack(side="right")

        # --- Journal de l'application
        zone = tk.Frame(page, bg=COULEURS["bord"], padx=1, pady=1)
        zone.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        self.journal = tk.Text(zone, width=1, height=5, wrap="word", state="disabled", font=self.police_texte(),
                               bg=COULEURS["journal"], fg=COULEURS["texte"], insertbackground=COULEURS["texte"],
                               selectbackground=COULEURS["accent"], relief="flat", borderwidth=0,
                               padx=12, pady=10, highlightthickness=0)
        defil = ttk.Scrollbar(zone, orient="vertical", style="Mince.Vertical.TScrollbar",
                              command=self.journal.yview)
        self.journal.configure(yscrollcommand=defil.set)
        defil.pack(side="right", fill="y")
        self.journal.pack(side="left", fill="both", expand=True)

    # --- onglet « Spoiler » : la liste complète des changements, cachée tant qu'on ne coche pas
    def construire_spoiler(self, cadre):
        cadre.columnconfigure(0, weight=1)
        cadre.rowconfigure(0, weight=1)
        carte, s = self.carte(cadre, self.t("carte_spoiler"))
        carte.grid(row=0, column=0, sticky="nsew")
        ttk.Checkbutton(s, text=self.t("afficher_spoiler"), variable=self.afficher_spoiler,
                        command=self.afficher_resultat).pack(anchor="w")
        self.note_spoiler = ttk.Label(s, style="Note.TLabel", wraplength=660, justify="left")
        self.note_spoiler.pack(anchor="w", padx=(27, 0), pady=(2, 10))
        zone = tk.Frame(s, bg=COULEURS["bord"], padx=1, pady=1)
        zone.pack(fill="both", expand=True)
        self.zone_spoiler = tk.Text(zone, width=1, height=10, wrap="word", state="disabled",
                                    font=self.police_texte(), bg=COULEURS["journal"], fg=COULEURS["texte"],
                                    selectbackground=COULEURS["accent"], relief="flat", borderwidth=0,
                                    padx=12, pady=10, highlightthickness=0)
        defil = ttk.Scrollbar(zone, orient="vertical", style="Mince.Vertical.TScrollbar",
                              command=self.zone_spoiler.yview)
        self.zone_spoiler.configure(yscrollcommand=defil.set)
        defil.pack(side="right", fill="y")
        self.zone_spoiler.pack(side="left", fill="both", expand=True)

    def spoiler_actuel(self):
        """(titre, texte) du spoiler : dernière seed générée, sinon celle installée dans le jeu."""
        if self.dernier_resultat and self.dernier_resultat[1]:
            return self.t("spoiler_genere"), self.dernier_resultat[1]
        dossier = self.dossier_jeu.get()
        seed = gen.seed_installee(dossier) if dossier and Path(dossier).exists() else None
        if seed:
            fichier = self.dossier_seeds / f"seed_{seed[0]}{'_armes' if seed[1] else ''}_spoiler.txt"
            if fichier.exists():
                return self.t("spoiler_installe"), fichier.read_text(encoding="utf-8")
        return None, None

    # --- onglet « Aider le projet » : mode relevé et avancement des relevés
    def construire_aide(self, page):
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)
        defile = Defilable(page)
        defile.grid(row=0, column=0, sticky="nsew")
        cadre = defile.interieur
        cadre.columnconfigure(0, weight=1)

        releve, r = self.carte(cadre, self.t("carte_releve"))
        releve.grid(row=0, column=0, sticky="nsew")
        ttk.Label(r, text=self.t("releve_intro"), style="Carte.TLabel", wraplength=640, justify="left"
                  ).pack(anchor="w", fill="x")
        self.case_releve = ttk.Checkbutton(r, text=self.t("releve_case"),
                                           variable=self.releve, command=self.basculer_releve)
        self.case_releve.pack(anchor="w", pady=(10, 2))
        for etape in ("etape1", "etape2", "etape3", "etape4"):
            ttk.Label(r, text=self.t(etape), style="Note.TLabel", wraplength=610,
                      justify="left").pack(anchor="w", padx=(27, 0), pady=1)
        ttk.Label(r, text=self.t("releve_saccade"), style="Note.TLabel", wraplength=610,
                  justify="left").pack(anchor="w", padx=(27, 0), pady=(6, 0))
        liens = ttk.Frame(r, style="Carte.TFrame", borderwidth=0)
        liens.pack(anchor="w", pady=(12, 0))
        ttk.Button(liens, text=self.t("journal_du_jeu"), command=self.ouvrir_journal).pack(side="left")
        ttk.Button(liens, text=self.t("signaler_github"),
                   command=lambda: webbrowser.open(URL_DEPOT + "/issues")).pack(side="left", padx=(8, 0))

        avancement, a = self.carte(cadre, self.t("carte_avancement"))
        avancement.grid(row=1, column=0, sticky="nsew", pady=(16, 0))
        cadre.rowconfigure(1, weight=1)
        self.toile = tk.Canvas(a, bg=COULEURS["carte"], highlightthickness=0, height=330)
        self.toile.pack(fill="both", expand=True)
        self.note_avancement = ttk.Label(a, style="Note.TLabel", wraplength=660, justify="left")
        self.note_avancement.pack(anchor="w", pady=(6, 0))
        self.avancement = None
        if self.donnees:
            try:
                self.avancement = progression.calculer(self.donnees)
            except Exception as e:  # données illisibles : on l'affiche sans bloquer l'application
                self.note_avancement.configure(text=self.t("avancement_indispo", e=e))
        self.toile.bind("<Configure>", lambda _: self.dessiner_avancement())

    def dessiner_avancement(self):
        """Mêmes barres que sur la page GitHub (calculées par progression.py)."""
        c, t = COULEURS, self.toile
        t.delete("all")
        res = self.avancement
        if not res:
            return
        largeur = max(t.winfo_width(), 400)
        x_perso, x_diff, x_barre = 0, 56, 196
        x_pct = largeur - 210
        l_barre = max(x_pct - x_barre - 18, 60)
        total = res["total_pieces"] or 1
        y = 12

        def barre(y, plein, pale):
            t.create_rectangle(x_barre, y - 5, x_barre + l_barre, y + 5, fill=c["champ"], outline="")
            if pale > 0:
                t.create_rectangle(x_barre, y - 5, x_barre + max(round(l_barre * (plein + pale)), 4), y + 5,
                                   fill="#5a2a2e", outline="")
            if plein > 0:
                t.create_rectangle(x_barre, y - 5, x_barre + max(round(l_barre * plein), 4), y + 5,
                                   fill=c["accent"], outline="")

        precedent = None
        for (perso, diff), s in res["scenarios"].items():
            if precedent and perso != precedent:
                t.create_line(0, y - 13, largeur, y - 13, fill=c["bord"])
            if perso != precedent:
                t.create_text(x_perso, y, text=perso, anchor="w", fill=c["texte"], font=(POLICE, 10, "bold"))
            precedent = perso
            t.create_text(x_diff, y, text=self.t(f"diff_{diff}"), anchor="w", fill=c["texte"], font=(POLICE, 10))
            barre(y, s["completes"] / total, s["visitees"] / total)
            t.create_text(x_pct, y, text=f"{round(100 * s['completes'] / total)} %", anchor="w",
                          fill=c["texte"], font=(POLICE, 10, "bold"))
            detail = f"{s['completes']}/{res['total_pieces']}"
            if s["visitees"]:
                detail += self.t("visitees", n=s["visitees"])
            t.create_text(x_pct + 44, y, text=detail, anchor="w", fill=c["discret"], font=(POLICE, 9))
            y += 26
        t.create_line(0, y - 13, largeur, y - 13, fill=c["bord"])
        y += 6
        t.create_text(x_perso, y, text=self.t("armes_bonus"), anchor="w", fill=c["texte"],
                      font=(POLICE, 10, "bold"))
        if res["bonus_total"]:
            barre(y, res["bonus_connus"] / res["bonus_total"], 0)
            t.create_text(x_pct, y, text=self.t("bonus_identifiees", a=res["bonus_connus"], b=res["bonus_total"]),
                          anchor="w", fill=c["texte"], font=(POLICE, 10, "bold"))
        else:
            barre(y, 0, 0)
            t.create_text(x_pct, y, text=self.t("liste_a_completer"), anchor="w", fill=c["discret"],
                          font=(POLICE, 9))
        self.note_avancement.configure(text=self.t("note_avancement", total=res["total_pieces"], version=VERSION))

    # ------------------------------------------------------------------ actions
    def ecrire(self, texte, effacer=False):
        self.journal.configure(state="normal")
        if effacer:
            self.journal.delete("1.0", "end")
        self.journal.insert("end", texte + "\n")
        self.journal.see("end")
        self.journal.configure(state="disabled")

    def choisir_dossier(self):
        d = filedialog.askdirectory(title=self.t("choisir_dossier"), initialdir=self.dossier_jeu.get() or None)
        if d:
            self.dossier_jeu.set(str(Path(d)))

    def actualiser_etat(self):
        d = Path(self.dossier_jeu.get()) if self.dossier_jeu.get() else None
        if not d or not (d / "bhd.exe").exists():
            self.etat_jeu.set("Jeu introuvable : indique le dossier qui contient bhd.exe.")
            self.badge_dll.configure(text=self.t("badge_jeu_introuvable"), style="Alerte.TLabel")
            self.badge_seed.configure(text="")
            self.badge_version.configure(text="")
            for b in (self.bouton_dll, self.bouton_retirer_dll, self.bouton_retirer_seed, self.case_releve):
                b.state(["disabled"])
            return
        self.case_releve.state(["!disabled"])
        self.releve.set(lire_option_ini(d, "Releve") == "1")
        dll = d / "xinput1_4.dll"
        dll_ok = dll.exists()
        etranger = dll_ok and not est_notre_dll(dll)
        seed = gen.seed_installee(d)
        if etranger:
            self.badge_dll.configure(text=self.t("badge_autre_dll"), style="Alerte.TLabel")
        elif dll_ok:
            self.badge_dll.configure(text=self.t("badge_installe"), style="Ok.TLabel")
        else:
            self.badge_dll.configure(text=self.t("badge_origine"), style="Neutre.TLabel")
        self.badge_version.configure(text="" if version_jeu_ok(d) else self.t("badge_version"))
        if seed:
            self.badge_seed.configure(text=self.t("badge_seed", graine=seed[0],
                                                  armes=self.t("badge_armes") if seed[1] else ""),
                                      style="Ok.TLabel")
        else:
            self.badge_seed.configure(text=self.t("badge_aucune_seed"), style="Neutre.TLabel")
        # résumé texte (non affiché, gardé en français pour les tests)
        self.etat_jeu.set(
            "DLL du randomizer : " + ("installée" if dll_ok and not etranger else
                                      "un AUTRE xinput1_4.dll est présent (pas celui du randomizer)"
                                      if etranger else "NON installée (jeu d'origine)") + "\n"
            f"Seed installée : {f'{seed[0]}' + (' (armes)' if seed[1] else '') if seed else 'aucune'}")
        self.bouton_dll.configure(text=self.t("maj_dll") if dll_ok and not etranger else self.t("installer_dll"))
        self.bouton_dll.state(["!disabled"] if self.dll and not etranger else ["disabled"])
        self.bouton_retirer_dll.state(["!disabled"] if dll_ok and not etranger else ["disabled"])
        self.bouton_retirer_seed.state(["!disabled"] if seed else ["disabled"])

    def basculer_releve(self):
        d = Path(self.dossier_jeu.get())
        actif = self.releve.get()
        try:
            ecrire_option_ini(d, "Releve", "1" if actif else None)
        except OSError as e:
            messagebox.showerror(TITRE, self.t("err_ini", e=e))
            self.releve.set(not actif)
            return
        if actif:
            self.ecrire(self.t("releve_active")
                        + ("" if (d / "xinput1_4.dll").exists() else self.t("releve_dll_absente")), effacer=True)
        else:
            self.ecrire(self.t("releve_desactive"), effacer=True)

    def supprimer(self, fichier, cle_message):
        try:
            fichier.unlink()
            self.ecrire(self.t(cle_message, chemin=fichier), effacer=True)
        except FileNotFoundError:
            pass
        except OSError as e:
            messagebox.showerror(TITRE, self.t("err_supprimer", nom=fichier.name, e=e))
        self.actualiser_etat()

    def retirer_dll(self):
        dll = Path(self.dossier_jeu.get()) / "xinput1_4.dll"
        if not est_notre_dll(dll):        # sécurité : ne jamais supprimer la DLL d'un autre mod
            messagebox.showwarning(TITRE, self.t("pas_notre_dll"))
            self.actualiser_etat()
            return
        if messagebox.askyesno(TITRE, self.t("confirmer_desinstaller")):
            self.supprimer(dll, "dll_supprimee")
            if not dll.exists():
                self.ecrire(self.t("sans_randomizer"))

    def retirer_seed(self):
        cible = Path(self.dossier_jeu.get()) / gen.NOM_SEED_JEU
        seed = gen.seed_installee(cible.parent)
        if seed and messagebox.askyesno(TITRE, self.t("confirmer_supprimer_seed", graine=seed[0],
                                                      armes=self.t("avec_armes") if seed[1] else "")):
            self.supprimer(cible, "seed_supprimee")

    def installer_dll(self):
        cible = Path(self.dossier_jeu.get()) / "xinput1_4.dll"
        if not version_jeu_ok(cible.parent) and not messagebox.askyesno(TITRE, self.t("version_confirmer")):
            return
        try:
            shutil.copyfile(self.dll, cible)
            self.ecrire(self.t("dll_installee", chemin=cible))
        except OSError as e:
            messagebox.showerror(TITRE, self.t("err_copier_dll", e=e))
        self.actualiser_etat()

    def copier_option_proton(self):
        self.clipboard_clear()
        self.clipboard_append(OPTION_PROTON)
        self.ecrire(self.t("copie_ok"), effacer=True)

    def ouvrir_journal(self):
        journal = Path(self.dossier_jeu.get()) / "randomizer_journal.txt"
        if journal.exists():
            ouvrir(journal)
        else:
            messagebox.showinfo(TITRE, self.t("pas_de_journal"))

    def ouvrir_seeds(self):
        self.dossier_seeds.mkdir(parents=True, exist_ok=True)
        ouvrir(self.dossier_seeds)

    def generer(self):
        try:
            graine = int(self.graine.get().strip())
            if graine < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(TITRE, self.t("graine_invalide"))
            return
        installer = self.installer.get()
        if installer and not (Path(self.dossier_jeu.get()) / "bhd.exe").exists():
            messagebox.showwarning(TITRE, self.t("dossier_introuvable"))
            return

        self.bouton_generer.state(["disabled"])
        self.ecrire(self.t("generation"), effacer=True)
        messages, spoiler = [], []
        langue = self.langue.get()

        def travail():
            try:
                ok = gen.produire(graine, self.armes.get(), self.donnees, self.dossier_seeds,
                                  installer, self.dossier_jeu.get() or None, messages.append,
                                  personnage=self.personnage.get(), difficulte=self.difficulte.get(),
                                  langue=langue, dire_spoiler=spoiler.append)
            except Exception as e:  # on affiche l'erreur plutôt que de fermer l'application
                messages.append(textes.tr("erreur", langue, e=e))
                ok = False
            self.after(0, lambda: self.fin_generation(messages, spoiler[0] if spoiler else None, ok))

        threading.Thread(target=travail, daemon=True).start()

    def fin_generation(self, messages, spoiler, ok):
        self.dernier_resultat = (messages, spoiler, ok)
        self.afficher_resultat()
        self.bouton_generer.state(["!disabled"])
        self.actualiser_etat()

    def afficher_resultat(self):
        """Journal de l'onglet Randomizer : résumé seulement (deux premières lignes du spoiler).
        Onglet Spoiler : liste complète, si la case est cochée."""
        if self.dernier_resultat:
            messages, spoiler, ok = self.dernier_resultat
            lignes = []
            if spoiler:
                lignes.append("\n".join(spoiler.splitlines()[:2]) + "\n" + self.t("renvoi_spoiler"))
            lignes += messages
            self.ecrire("\n".join(lignes), effacer=True)
            if not ok:
                self.ecrire("\n" + self.t("echec_generation"))
        titre, texte = self.spoiler_actuel()
        if texte is None:
            note, contenu = self.t("spoiler_aucun"), ""
        elif self.afficher_spoiler.get():
            note, contenu = titre, texte
        else:
            note, contenu = self.t("spoiler_masque", titre=titre), ""
        self.note_spoiler.configure(text=note)
        self.zone_spoiler.configure(state="normal")
        self.zone_spoiler.delete("1.0", "end")
        self.zone_spoiler.insert("end", contenu)
        self.zone_spoiler.configure(state="disabled")

if __name__ == "__main__":
    Application().mainloop()
