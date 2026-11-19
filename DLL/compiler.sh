#!/bin/sh
# Compile la DLL du randomizer (Windows 32 bits) depuis Linux, avec le compilateur croisé MinGW.
# Prérequis une seule fois (Ubuntu / WSL) :  sudo apt install gcc-mingw-w64-i686
set -e
cd "$(dirname "$0")"
i686-w64-mingw32-gcc -O2 -s -Wall -shared -static-libgcc -Wl,--no-insert-timestamp -o xinput1_4.dll randomizer.c xinput1_4.def
echo "OK : $(pwd)/xinput1_4.dll"
