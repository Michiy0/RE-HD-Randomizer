@echo off
rem Construit Resident Evil HD Remaster Randomizer.exe (un seul fichier) avec PyInstaller.
rem Prerequis une seule fois :  python -m pip install pyinstaller openpyxl
rem Le tableur et la DLL sont embarques ; s'ils sont aussi poses a cote de l'exe,
rem ce sont ces copies-la qui sont utilisees (mise a jour des donnees sans reconstruire).
setlocal
cd /d "%~dp0"
if not exist "%~dp0icone.ico" python "%~dp0creer_icone.py"
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Resident Evil HD Remaster Randomizer" ^
    --icon "%~dp0icone.ico" --add-data "%~dp0icone.ico;." --add-data "%~dp0logo_entete.png;." ^
    --distpath "%~dp0dist" --workpath "%TEMP%\rehdr_randomizer_build" --specpath "%TEMP%\rehdr_randomizer_build" ^
    --add-data "%~dp0..\donnees_randomizer_RE1.xlsx;." ^
    --add-data "%~dp0..\DLL\xinput1_4.dll;." ^
    application.py
if errorlevel 1 (
    echo ECHEC de la construction.
    exit /b 1
)
echo OK : %~dp0dist\Resident Evil HD Remaster Randomizer.exe
