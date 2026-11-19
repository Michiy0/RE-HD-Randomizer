@echo off
rem Compile la DLL du randomizer (32 bits) avec GCC de MSYS2.
rem Prerequis une seule fois :  C:\msys64\usr\bin\pacman.exe -S mingw-w64-i686-gcc
setlocal
cd /d "%~dp0"
set PATH=C:\msys64\mingw32\bin;%PATH%
gcc -O2 -s -Wall -shared -static-libgcc -Wl,--no-insert-timestamp -o xinput1_4.dll randomizer.c xinput1_4.def
if errorlevel 1 (
    echo ECHEC de la compilation.
    exit /b 1
)
echo OK : %~dp0xinput1_4.dll
