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

## Points à savoir
- Ne pas lancer `appliquer_seed.lua` dans Cheat Engine en même temps : les deux utilisent le même
  point d'arrêt matériel (DR0).
- Le point d'arrêt est posé ~3 s après l'apparition de la fenêtre du jeu.
- Compatible BhdTool (qui reste `dinput8.dll`).

## Compiler
`compiler.bat` (GCC 32 bits de MSYS2 : `C:\msys64\usr\bin\pacman.exe -S mingw-w64-i686-gcc`).
