# DLL du randomizer (sans Cheat Engine) — v0.1

## Installation
Le plus simple : `Randomizer\dist\RandomizerREHD.exe`, bouton « Installer la DLL », puis « Générer la seed »
(case « Installer la seed dans le jeu » cochée).

À la main, dans le dossier du jeu (`...\steamapps\common\Resident Evil Biohazard HD REMASTER\`) :
1. copier `xinput1_4.dll` ;
2. installer une seed : `python generateur_seed.py 12345 --installer` (ajouter `--armes-aleatoires` si
   voulu). Le générateur trouve le dossier du jeu tout seul et y écrit `randomizer_seed.lua`
   (sinon : `--dossier-jeu "chemin"`, ou copier à la main `seed_<n>.lua` renommé `randomizer_seed.lua`).
   Relancer le jeu après chaque nouvelle seed.

Facultatif : `randomizer.ini` pour choisir un autre fichier ou désactiver sans rien supprimer :
```ini
[Randomizer]
Actif=1
Seed=randomizer_seed.lua
```

## Désinstallation
Supprimer `xinput1_4.dll` du dossier du jeu (le jeu reprend alors la DLL XInput de Windows).

## Journal
`randomizer_journal.txt` (dossier du jeu) : seed chargée, remplacements, objets non répertoriés
(même format d'empreinte que `journal_non_repertorie.txt`), garde-fou.

## Mode relevé (Releve=1)
Case « Mode relevé » dans l'application, ou `Releve=1` dans `randomizer.ini`. À chaque nouvelle pièce
(1,5 s après l'arrivée), la DLL cherche en mémoire les objets posés encore présents et les note dans
`randomizer_journal.txt` (lignes `Releve auto` : pièce, id, quantité, numéro dans la pièce, empreinte),
sans rien ramasser. Chaque objet n'est noté qu'une fois par lancement. Petite saccade (~0,3 s) à
l'entrée des pièces. Les objets déjà ramassés n'existent plus : relevé complet = nouvelle partie.
Le journal s'importe ensuite avec `importer_journal.py`.

## Mode diagnostic (pour les relevés)
`Diagnostic=1` dans `randomizer.ini` : à chaque objet examiné ou ramassé (60 au plus par lancement), la
DLL écrit dans `randomizer_diagnostic.txt` l'adresse de la structure de l'objet, sa position par rapport
à la structure de partie, les registres, le haut de la pile et la mémoire autour (−0x100 à +0x400).
Sans effet sur le jeu ; fonctionne aussi sans seed installée.

## Importer des journaux dans le tableur
`python Randomizer\importer_journal.py randomizer_journal.txt [autres journaux…]` montre les nouveaux
emplacements ; ajouter `--ecrire` (et éventuellement `--source "nom du testeur"`) pour les ajouter à
l'onglet « Emplacements ». Lit aussi les journaux des scripts Cheat Engine. Doublons ignorés, sauvegarde
automatique dans `sauvegardes\`.

## Points à savoir
- Ne pas lancer `appliquer_seed.lua` dans Cheat Engine en même temps : les deux utilisent le même
  point d'arrêt matériel (DR0).
- Le point d'arrêt est posé ~3 s après l'apparition de la fenêtre du jeu.
- Compatible BhdTool (qui reste `dinput8.dll`).

## Compiler
`compiler.bat` (GCC 32 bits de MSYS2 : `C:\msys64\usr\bin\pacman.exe -S mingw-w64-i686-gcc`).
