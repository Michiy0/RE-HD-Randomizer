#!/bin/sh
# Construit RandomizerREHD-linux (un seul fichier, à lancer sur Linux ou Steam Deck en mode Bureau).
# Prérequis une seule fois (Ubuntu / WSL) :
#   sudo apt install python3 python3-venv python3-tk gcc-mingw-w64-i686
# Le script crée son propre environnement Python (openpyxl, pyinstaller) dans ~/.randomizer-venv.
set -e
cd "$(dirname "$0")"
ICI="$(pwd)"

[ -f ../DLL/xinput1_4.dll ] || sh ../DLL/compiler.sh
[ -f icone.png ] || python3 creer_icone.py

VENV="$HOME/.randomizer-venv"
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet openpyxl pyinstaller
fi

"$VENV/bin/python" -m PyInstaller --noconfirm --clean --onefile --windowed --name RandomizerREHD-linux \
    --distpath "$ICI/dist" --workpath /tmp/randomizer_build --specpath /tmp/randomizer_build \
    --add-data "$ICI/../donnees_randomizer_RE1.xlsx:." \
    --add-data "$ICI/../DLL/xinput1_4.dll:." \
    --add-data "$ICI/icone.png:." \
    application.py
echo "OK : $ICI/dist/RandomizerREHD-linux"
