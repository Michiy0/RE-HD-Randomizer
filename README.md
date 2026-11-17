# Randomizer — Resident Evil HD Remaster (PC / Steam)

**[⬇ Télécharger la dernière version](https://github.com/Michiy0/RE-HD-Randomizer/releases)** ·
[English](#english) · [Signaler un problème](https://github.com/Michiy0/RE-HD-Randomizer/issues)

Mélange les objets du manoir à chaque partie. Une **graine** (un simple nombre) donne toujours le même
mélange : on peut jouer à plusieurs sur la même seed et comparer.

> Projet de fan, **non officiel**, sans lien avec Capcom. Aucun fichier du jeu n'est inclus : il faut
> posséder Resident Evil HD Remaster sur Steam.

## En bref

- **Les objets changent de place** : munitions, herbes, rubans encreurs, poignards… Les clés et objets de
  quête restent à leur place, la partie reste toujours finissable.
- **Une application simple** : on installe le randomizer, on choisit ses options, on génère une seed, et
  c'est prêt. Un clic suffit pour revenir au jeu d'origine.
- **Sans Cheat Engine** : une petite DLL se charge avec le jeu et fait le travail. Le code du jeu n'est
  jamais modifié.
- **Windows et Steam Deck** : application Windows, et application Linux native pour le Steam Deck.
- **7 langues** : français, anglais, japonais, espagnol, portugais, russe et chinois (langue du système
  par défaut).
- **Projet communautaire** : chaque joueur peut aider à relever les objets du jeu, grâce à un mode relevé
  intégré.

## État : version 0.6 (test)

| Pris en charge | À venir |
|---|---|
| Chris, difficulté Normal | Jill, autres difficultés |
| 34 emplacements d'objets posés : munitions, herbes, rubans encreurs, poignards, trousses de premiers secours | Clés et objets de quête (avec une logique qui garantit que la partie reste finissable) |
| Option **armes aléatoires** (le pistolet du hall est mélangé lui aussi) | Davantage d'emplacements, armes bonus |
| Windows ; Steam Deck / Linux (application) | Confirmation du fonctionnement en jeu sur Steam Deck |

**Version du jeu requise** : la version Steam actuelle de `bhd.exe` (9 640 360 octets, SHA-256
`39B840663E4B1A6835C60CBD176E4EE6C21B9197FC2C2DD733F2A7C36A0B429A`). L'application le vérifie ; sur une
autre version, le randomizer se met en veille et le jeu reste intact.

## Avancement des relevés

Pourcentage de pièces relevées en **nouvelle partie** pour chaque personnage et difficulté
(voir [Aider le projet](#aider-le-projet)). Mis à jour à chaque version.

<!-- progression:debut -->

<img src="images/progression.svg" alt="Avancement des relevés" width="800">

<details><summary>Détail (texte)</summary>

| Personnage | Difficulté | Pièces complètes | Visitées (partie commencée) | Objets relevés |
|---|---|---|---|---|
| Chris | Très facile | 0/118 (0 %) | 0 | 0 |
| Chris | Facile | 0/118 (0 %) | 0 | 0 |
| Chris | Normal | 0/118 (0 %) | 26 | 73 |
| Chris | Difficile | 0/118 (0 %) | 0 | 0 |
| Chris | Real Survival | 0/118 (0 %) | 0 | 0 |
| Jill | Très facile | 0/118 (0 %) | 0 | 0 |
| Jill | Facile | 0/118 (0 %) | 0 | 0 |
| Jill | Normal | 0/118 (0 %) | 0 | 0 |
| Jill | Difficile | 0/118 (0 %) | 0 | 0 |
| Jill | Real Survival | 0/118 (0 %) | 0 | 0 |

Armes bonus : liste à compléter. Mis à jour le 17/11/2026.

</details>

<!-- progression:fin -->

## Installation

### Windows

1. Télécharge `RandomizerREHD-v….zip` dans les **[Releases](https://github.com/Michiy0/RE-HD-Randomizer/releases)**
   et extrais-le où tu veux.
2. Lance `RandomizerREHD.exe`. Le dossier du jeu est trouvé automatiquement (sinon : **Parcourir…**).
3. Clique **Installer la DLL** (une seule fois).
4. Choisis tes options, puis **Générer la seed** (laisse cochée « Installer la seed dans le jeu »).
5. Lance le jeu depuis Steam : **nouvelle partie, Chris, Normal**.

Pour changer de seed : en générer une nouvelle, puis relancer le jeu.

> **SmartScreen / antivirus** : l'exe n'est pas signé (projet amateur). Windows peut afficher « Windows a
> protégé votre ordinateur » → *Informations complémentaires* → *Exécuter quand même*. Certains antivirus
> peuvent aussi signaler la DLL par erreur : elle utilise un point d'arrêt matériel (comme Cheat Engine)
> pour repérer l'objet ramassé. Tout le code source est dans ce dépôt.

### Steam Deck / Linux

L'application existe en version **Linux native** (pas besoin de Proton pour elle) ; le jeu, lui, tourne
toujours avec Proton.

1. En **mode Bureau**, télécharge `RandomizerREHD-v…-linux.tar.gz` et extrais-le.
2. Double-clique sur `RandomizerREHD-linux` (si besoin : clic droit → *Propriétés* → *Permissions* →
   « Est exécutable »). Le jeu est trouvé dans la bibliothèque Steam, carte SD comprise.
3. Clique **Installer la DLL**, puis **Copier** l'option de lancement affichée dans la carte *Jeu*, et
   colle-la une fois dans Steam (*Propriétés du jeu → Options de lancement*) :
   ```
   WINEDLLOVERRIDES="xinput1_4=n,b" %command%
   ```
4. **Générer la seed**, puis lance le jeu.

> Le fonctionnement de la DLL dans le jeu sous Proton n'a pas encore été confirmé sur un vrai Steam
> Deck : un retour (bouton **Journal du jeu**) est le bienvenu, qu'il marche ou non.

### Revenir au jeu d'origine

Dans l'application : **Désinstaller la DLL** (sur Steam Deck, retire aussi l'option de lancement).
« Supprimer la seed installée » retire seulement la seed : sans seed, la DLL ne change rien au jeu.

## Utilisation

L'application a trois onglets, et un sélecteur de langue en haut à droite (« Automatique » = langue du
système, anglais sinon).

- **Randomizer** — tout pour jouer, dans l'ordre :
  - *Jeu* : dossier du jeu, état du randomizer et de la seed installée, installer / mettre à jour /
    désinstaller la DLL ;
  - *Partie* : personnage et difficulté ;
  - *Options* : armes aléatoires, graine (ou « Au hasard ») — même graine + mêmes options = même résultat ;
  - **Générer la seed** : écrit la seed dans le dossier `seeds` et l'installe dans le jeu.
- **Spoiler** — la liste complète des changements (« pièce : objet d'origine → nouvel objet »), cachée
  tant qu'on ne coche pas *Afficher le spoiler*. Elle montre la dernière seed générée, ou celle installée.
- **Aider le projet** — le mode relevé et les barres d'avancement (voir plus bas).

### Compatibilité

- **BhdTool** : compatible (il utilise `dinput8.dll`, le randomizer `xinput1_4.dll`).
- **Autre mod qui installe un `xinput1_4.dll`** : incompatible. L'application le détecte et n'y touche
  jamais.
- **Cheat Engine** : ne pas lancer `appliquer_seed.lua` en même temps (même point d'arrêt).

## Aider le projet

Le randomizer ne mélange que les objets déjà **relevés**. Tout le monde peut aider en jouant :

1. Onglet **Aider le projet** → coche **Mode relevé** (DLL installée).
2. Lance une **nouvelle partie** : les objets déjà ramassés n'existent plus en mémoire.
3. Visite les pièces sans rien ramasser ; reste environ 2 secondes dans chacune. La DLL note les objets
   présents dans le journal du jeu (petite saccade d'environ 0,3 s à l'entrée d'une pièce).
4. Ouvre le journal (bouton **Journal du jeu**) et joins-le à une
   [issue](https://github.com/Michiy0/RE-HD-Randomizer/issues), en précisant le personnage et la difficulté.

Les traductions ont été faites pour le projet : si tu parles une des 7 langues et vois une erreur,
signale-la aussi (les textes sont dans `Randomizer/textes.py`).

## Signaler un problème

Ouvre une [issue](https://github.com/Michiy0/RE-HD-Randomizer/issues) en joignant `randomizer_journal.txt`
(bouton **Journal du jeu**), avec la graine, les options, ta plateforme (Windows ou Steam Deck) et ce qui
s'est passé.

---

## Pour les développeurs

### Comment ça marche

- **L'application** (`Randomizer/application.py`, Python + Tk) tire une seed à partir du tableur
  `donnees_randomizer_RE1.xlsx` (emplacements relevés en jeu) et l'écrit dans le dossier du jeu sous le
  nom `randomizer_seed.lua`. Toute la logique est dans `generateur_seed.py`, utilisable aussi en ligne de
  commande.
- **La DLL** (`DLL/randomizer.c`) se fait passer pour `xinput1_4.dll` et transmet toutes les fonctions
  manette à la vraie DLL de Windows. Elle pose un **point d'arrêt matériel** sur `bhd.exe+1512ED` (lecture
  de l'objet ramassé) et, si l'emplacement est dans la seed, remplace l'identifiant et la quantité. Un
  emplacement est reconnu par sa pièce et son **empreinte** : les 4 coins (x, z) de sa zone de ramassage,
  identiques sur tous les PC.
- **Le mode relevé** (`Releve=1` dans `randomizer.ini`) repère à l'entrée de chaque pièce les objets posés
  en mémoire grâce à leur signature (`00C233F4` / `00C2286C`), sans rien ramasser.
- `bhd.exe` est protégé par SteamStub (code chiffré sur le disque) : la DLL ne modifie jamais le code et
  se met en veille sur une autre version du jeu.

### Contenu du dépôt

```
donnees_randomizer_RE1.xlsx   données : pièces, objets, emplacements, pièces relevées, bonus
DLL/                          la DLL (randomizer.c, xinput1_4.def) et ses scripts de compilation
Randomizer/
  application.py              l'application (3 onglets, 7 langues)
  generateur_seed.py          génération des seeds (aussi en ligne de commande)
  importer_journal.py         importe les journaux de relevés dans le tableur
  progression.py              barres d'avancement de ce README
  textes.py                   toutes les traductions
  construire_exe.bat / construire_linux.sh, creer_icone.py, icônes
outils/cheat_engine/          anciens scripts Cheat Engine (relevés manuels)
preparer_publication.py       prépare le dépôt, le zip Windows et l'archive Linux
```

### Construire

- **Windows** — Python 3 (`pip install openpyxl pyinstaller`) et GCC 32 bits de MSYS2
  (`pacman -S mingw-w64-i686-gcc`) :
  ```bat
  DLL\compiler.bat
  Randomizer\construire_exe.bat
  ```
- **Linux** (ou WSL ; Ubuntu 22.04 conseillé pour rester compatible avec le Steam Deck) —
  `sudo apt install python3 python3-venv python3-tk gcc-mingw-w64-i686` :
  ```sh
  sh DLL/compiler.sh
  sh Randomizer/construire_linux.sh
  ```
- **Sans compiler** : `python Randomizer/application.py`, ou en ligne de commande
  `python Randomizer/generateur_seed.py 12345 --armes-aleatoires --installer`.
- **Importer des relevés** :
  `python Randomizer/importer_journal.py journal.txt --personnage Chris --difficulte Normal --nouvelle-partie --ecrire`
  (sans `--nouvelle-partie` si la partie était déjà commencée : les pièces comptent alors comme visitées).

## Crédits

- Noms et liaisons des pièces : `rooms.json` de **BhdTool** (eleval, GPLv3).
- Informations sur les verrous : **Evil Resource**.
- Inspiré des randomizers de la communauté (BioRand, ancien randomizer de Benn Powell).

## Licence

GPLv3 — voir [LICENSE](LICENSE).

---

## English

Item randomizer for **Resident Evil HD Remaster (Steam)**. Unofficial fan project; no game files included.

- **What it does**: shuffles the mansion's items (ammo, herbs, ink ribbons, daggers…) from a **seed** —
  same seed, same result. Keys and quest items stay in place, so the game is always completable.
- **Status — version 0.6 (test)**: Chris / Normal, 34 placed-item locations, optional *random weapons*.
  Jill, other difficulties, keys and bonus weapons are planned.
- **Easy to use**: a small app (3 tabs: *Randomizer*, *Spoiler*, *Help the project*) installs the
  randomizer, generates seeds and brings back the original game in one click. No Cheat Engine needed.
- **7 languages**: English, French, Japanese, Spanish, Portuguese, Russian and Chinese (system language
  by default; selector at the top right).
- **Requires** the current Steam `bhd.exe` (9,640,360 bytes, SHA-256 above). On any other version the
  randomizer stays inactive and the game is untouched.

**Windows**: download `RandomizerREHD-v….zip` from the
[Releases](https://github.com/Michiy0/RE-HD-Randomizer/releases), run `RandomizerREHD.exe`, click
*Install the DLL*, then *Generate seed*, and start a new game as Chris (Normal). The exe is unsigned:
SmartScreen may warn; some antivirus tools may flag the DLL because it uses a hardware breakpoint. The
full source is in this repository.

**Steam Deck / Linux**: in Desktop Mode, extract `RandomizerREHD-v…-linux.tar.gz` and run
`RandomizerREHD-linux` (native Linux app). Click *Install the DLL*, then *Copy* the launch option and
paste it once in Steam (*game Properties → Launch Options*): `WINEDLLOVERRIDES="xinput1_4=n,b" %command%`.
The DLL has not been confirmed in-game on a real Steam Deck yet — feedback is welcome.

**Uninstall**: *Uninstall the DLL* in the app. Works alongside BhdTool.

**Help the project**: in the *Help the project* tab, enable *Survey mode*, start a new game and walk
through the rooms without picking anything up; then attach the game log to an
[issue](https://github.com/Michiy0/RE-HD-Randomizer/issues) (state your character and difficulty).
Translation fixes are welcome too.

**Bug reports**: attach `randomizer_journal.txt` (*Game log* button) to an issue, with the seed, options
and platform. License: GPLv3.
