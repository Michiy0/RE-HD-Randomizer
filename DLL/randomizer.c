/*
 * randomizer.c : randomizer Resident Evil HD Remaster sans Cheat Engine (version 0.1)
 *
 * Cible : bhd.exe Steam de 9 640 360 octets
 *         (SHA-256 39B840663E4B1A6835C60CBD176E4EE6C21B9197FC2C2DD733F2A7C36A0B429A).
 *
 * Principe (le même que appliquer_seed.lua, déjà validé en jeu) :
 *   - un point d'arrêt matériel (registre de débogage DR0) sur bhd.exe+1512ED, l'endroit où le jeu
 *     va lire l'objet posé que le joueur ramasse (EAX = structure de l'objet) ;
 *   - quand il se déclenche, on identifie l'emplacement (pièce + 8 valeurs fixes en +0x10..+0x2C)
 *     et, si la seed prévoit un autre objet, on écrit (id << 16) | quantité en +0x34.
 *   Le code du jeu n'est jamais modifié : sur le disque il est chiffré par la protection Steam,
 *   on ne peut donc pas y poser un détour sans connaître les octets déchiffrés.
 *
 * Chargement : la DLL se fait passer pour xinput1_4.dll (le jeu l'importe, et dinput8.dll est
 * déjà occupé par BhdTool). Toutes les fonctions XInput sont transmises à la vraie DLL de Windows.
 *
 * Fichiers, tous dans le dossier du jeu :
 *   randomizer.ini            (facultatif) [Randomizer] Actif=1  Seed=randomizer_seed.lua
 *   randomizer_seed.lua       seed produite par generateur_seed.py (le fichier seed_<n>.lua renommé)
 *   randomizer_journal.txt    ce que fait la DLL : seed chargée, remplacements, objets non répertoriés
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <ctype.h>

#define TAILLE_BHD_EXE  9640360u             /* seule version prise en charge */
#define BASE_JEU        0x400000u            /* bhd.exe n'utilise pas l'ASLR */
#define ADR_LECTURE     (BASE_JEU + 0x1512EDu)
#define ADR_PTR_PARTIE  (BASE_JEU + 0x8F2F28u)
#define OFF_ZONE        0xE472Cu
#define OFF_PIECE       0xE4730u

#define MAX_EMPLACEMENTS 2048
#define MAX_THREADS      1024

typedef struct {
    DWORD piece;
    DWORD empreinte[8];
    DWORD id, qte;
} Emplacement;

static Emplacement g_seed[MAX_EMPLACEMENTS];
static int   g_nb;
static long  g_graine = -1;
static int   g_armes = -1;               /* -1 inconnu, 0 non, 1 oui */

static char  g_dossier[MAX_PATH];        /* dossier du jeu, avec la barre oblique finale */
static char  g_journal[MAX_PATH];
static CRITICAL_SECTION g_verrou_journal;

static volatile LONG g_actif;            /* 1 : point d'arrêt armé */
static volatile LONG g_coupe;            /* 1 : garde-fou déclenché, on désarme tout */
static DWORD g_fenetre_debut, g_fenetre_compte, g_messages;

/* ------------------------------------------------------------------ journal */

static void journal(const char *fmt, ...)
{
    char ligne[1024];
    SYSTEMTIME t;
    int n;
    va_list ap;
    HANDLE f;
    DWORD ecrit;

    GetLocalTime(&t);
    n = _snprintf(ligne, sizeof ligne - 2, "%02d:%02d:%02d\t", t.wHour, t.wMinute, t.wSecond);
    va_start(ap, fmt);
    n += _vsnprintf(ligne + n, sizeof ligne - 2 - n, fmt, ap);
    va_end(ap);
    if (n < 0 || n > (int)sizeof ligne - 2) n = (int)sizeof ligne - 2;
    ligne[n++] = '\r';
    ligne[n++] = '\n';

    EnterCriticalSection(&g_verrou_journal);
    f = CreateFileA(g_journal, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                    OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        WriteFile(f, ligne, (DWORD)n, &ecrit, NULL);
        CloseHandle(f);
    }
    LeaveCriticalSection(&g_verrou_journal);
}

/* ------------------------------------------------------------- lecture seed */

/* Lit le fichier seed_<n>.lua produit par generateur_seed.py. On ne fait pas un vrai analyseur
 * Lua : chaque ligne contenant « piece = » donne, dans l'ordre, 11 nombres :
 * pièce, 8 valeurs d'empreinte, id, quantité. */
static int lire_nombres(const char *ligne, DWORD *sortie, int max)
{
    int n = 0;
    const char *p = ligne;
    while (*p && n < max) {
        int debut_mot = (p == ligne) || !(isalnum((unsigned char)p[-1]) || p[-1] == '_');
        if (debut_mot && isdigit((unsigned char)*p)) {
            char *fin;
            sortie[n++] = (DWORD)strtoul(p, &fin, 0);   /* base 0 : gère 0x... et le décimal */
            p = fin;
        } else {
            p++;
        }
    }
    return n;
}

static int charger_seed(const char *chemin)
{
    FILE *f = fopen(chemin, "rb");
    char ligne[1024];
    if (!f) return 0;
    g_nb = 0;
    while (fgets(ligne, sizeof ligne, f)) {
        if (strstr(ligne, "piece =")) {
            DWORD v[12];
            if (lire_nombres(ligne, v, 12) == 11 && g_nb < MAX_EMPLACEMENTS) {
                Emplacement *e = &g_seed[g_nb++];
                e->piece = v[0];
                memcpy(e->empreinte, &v[1], sizeof e->empreinte);
                e->id = v[9];
                e->qte = v[10];
            } else {
                journal("Ligne de seed ignoree (format inattendu) : %.200s", ligne);
            }
        } else if (strstr(ligne, "graine =")) {
            DWORD v[1];
            if (lire_nombres(ligne, v, 1) == 1) g_graine = (long)v[0];
        } else if (strstr(ligne, "armes_aleatoires =")) {
            g_armes = strstr(ligne, "true") ? 1 : (strstr(ligne, "false") ? 0 : -1);
        }
    }
    fclose(f);
    return 1;
}

/* ------------------------------------------------------ accès mémoire sûr */

static int lisible(const void *adr, SIZE_T taille, int ecriture)
{
    MEMORY_BASIC_INFORMATION mbi;
    DWORD ok = ecriture
        ? (PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY)
        : (PAGE_READONLY | PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READ |
           PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY);
    if (!adr || !VirtualQuery(adr, &mbi, sizeof mbi)) return 0;
    if (mbi.State != MEM_COMMIT || !(mbi.Protect & ok) || (mbi.Protect & PAGE_GUARD)) return 0;
    return (ULONG_PTR)adr + taille <= (ULONG_PTR)mbi.BaseAddress + mbi.RegionSize;
}

static int piece_actuelle(DWORD *piece)
{
    DWORD p;
    if (!lisible((void *)ADR_PTR_PARTIE, 4, 0)) return 0;
    p = *(DWORD *)ADR_PTR_PARTIE;
    if (!p || !lisible((void *)(p + OFF_ZONE), 8, 0)) return 0;
    *piece = (*(DWORD *)(p + OFF_ZONE)) * 256u + *(DWORD *)(p + OFF_PIECE);
    return 1;
}

/* ------------------------------------------------- traitement du ramassage */

static void traiter_objet(DWORD structure)
{
    DWORD piece, valeurs[8], maintenant = GetTickCount();
    int i;

    /* garde-fou repris du script Lua : plus de 30 déclenchements en 2 s = quelque chose cloche */
    if (maintenant - g_fenetre_debut > 2000) { g_fenetre_debut = maintenant; g_fenetre_compte = 0; }
    if (++g_fenetre_compte > 30) {
        if (!g_coupe) {
            InterlockedExchange(&g_coupe, 1);
            journal("GARDE-FOU : trop de declenchements, randomizer coupe. Recharge ta sauvegarde.");
        }
        return;
    }

    if (!piece_actuelle(&piece)) return;
    if (!lisible((void *)(structure + 0x10), 0x28, 0)) return;
    memcpy(valeurs, (void *)(structure + 0x10), sizeof valeurs);

    for (i = 0; i < g_nb; i++) {
        const Emplacement *e = &g_seed[i];
        if (e->piece == piece && memcmp(e->empreinte, valeurs, sizeof valeurs) == 0) {
            if (lisible((void *)(structure + 0x34), 4, 1)) {
                *(volatile DWORD *)(structure + 0x34) = (e->id << 16) | (e->qte & 0xFFFF);
                if (g_messages < 500) {
                    g_messages++;
                    journal("Piece %X : objet remplace par id %lu (quantite %lu)",
                            piece, (unsigned long)e->id, (unsigned long)e->qte);
                }
            }
            return;
        }
    }

    {
        DWORD courant = lisible((void *)(structure + 0x34), 4, 0) ? *(DWORD *)(structure + 0x34) : 0;
        journal("Non repertorie\tpiece=%X\tid=%lu\tqte=%lu\tvaleurs=%X:%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X",
                piece, (unsigned long)(courant >> 16), (unsigned long)(courant & 0xFFFF), piece,
                valeurs[0], valeurs[1], valeurs[2], valeurs[3],
                valeurs[4], valeurs[5], valeurs[6], valeurs[7]);
    }
}

static LONG CALLBACK gestionnaire(EXCEPTION_POINTERS *ep)
{
    CONTEXT *c = ep->ContextRecord;
    if (ep->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP || c->Eip != ADR_LECTURE)
        return EXCEPTION_CONTINUE_SEARCH;
    if (!g_coupe) traiter_objet(c->Eax);
    if (g_coupe) {                         /* on retire le point d'arrêt de ce thread tout de suite */
        c->Dr0 = 0;
        c->Dr7 &= ~3u;
    }
    c->EFlags |= 0x10000;                  /* RF : exécuter l'instruction sans redéclencher */
    return EXCEPTION_CONTINUE_EXECUTION;
}

/* ------------------------------------------- armement des threads du jeu */

static DWORD g_threads_armes[MAX_THREADS];
static int   g_nb_threads;

static int deja_arme(DWORD tid)
{
    int i;
    for (i = 0; i < g_nb_threads; i++) if (g_threads_armes[i] == tid) return 1;
    return 0;
}

static void regler_thread(DWORD tid, int armer)
{
    HANDLE h = OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_SUSPEND_RESUME, FALSE, tid);
    CONTEXT c;
    if (!h) return;
    if (SuspendThread(h) != (DWORD)-1) {
        memset(&c, 0, sizeof c);
        c.ContextFlags = CONTEXT_DEBUG_REGISTERS;
        if (GetThreadContext(h, &c)) {
            if (armer) {
                c.Dr0 = ADR_LECTURE;
                c.Dr7 = (c.Dr7 & ~0x000F0003u) | 1u;   /* L0 = 1, exécution, longueur 1 */
            } else if (c.Dr0 == ADR_LECTURE) {
                c.Dr0 = 0;
                c.Dr7 &= ~3u;
            }
            SetThreadContext(h, &c);
        }
        ResumeThread(h);
    }
    CloseHandle(h);
}

static void parcourir_threads(int armer)
{
    DWORD moi = GetCurrentThreadId(), pid = GetCurrentProcessId();
    THREADENTRY32 te;
    HANDLE s = CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (s == INVALID_HANDLE_VALUE) return;
    te.dwSize = sizeof te;
    if (Thread32First(s, &te)) {
        do {
            if (te.th32OwnerProcessID != pid || te.th32ThreadID == moi) continue;
            if (armer) {
                if (deja_arme(te.th32ThreadID)) continue;
                regler_thread(te.th32ThreadID, 1);
                if (g_nb_threads < MAX_THREADS) g_threads_armes[g_nb_threads++] = te.th32ThreadID;
            } else {
                regler_thread(te.th32ThreadID, 0);
            }
        } while (Thread32Next(s, &te));
    }
    CloseHandle(s);
}

static BOOL CALLBACK chercher_fenetre(HWND w, LPARAM trouve)
{
    DWORD pid;
    GetWindowThreadProcessId(w, &pid);
    if (pid == GetCurrentProcessId() && IsWindowVisible(w)) { *(int *)trouve = 1; return FALSE; }
    return TRUE;
}

static DWORD WINAPI surveillance(LPVOID inutile)
{
    int fenetre = 0;
    (void)inutile;

    /* On attend que le jeu soit vraiment lancé (fenêtre visible) : avant, la protection Steam
     * déchiffre encore le code et n'aime pas forcément les registres de débogage. */
    while (!fenetre) {
        Sleep(500);
        EnumWindows(chercher_fenetre, (LPARAM)&fenetre);
    }
    Sleep(3000);

    AddVectoredExceptionHandler(1, gestionnaire);
    InterlockedExchange(&g_actif, 1);
    journal("Point d'arret pose en bhd.exe+1512ED.");

    for (;;) {
        if (g_coupe) {
            parcourir_threads(0);
            journal("Points d'arret retires de tous les threads.");
            return 0;
        }
        parcourir_threads(1);              /* arme les threads créés depuis le dernier passage */
        Sleep(1000);
    }
}

/* ------------------------------------------------------------ démarrage */

static void demarrer(void)
{
    char ini[MAX_PATH], seed[MAX_PATH], chemin_seed[MAX_PATH], *barre;

    GetModuleFileNameA(NULL, g_dossier, MAX_PATH);
    barre = strrchr(g_dossier, '\\');
    if (barre) barre[1] = 0;
    _snprintf(g_journal, MAX_PATH, "%srandomizer_journal.txt", g_dossier);
    _snprintf(ini, MAX_PATH, "%srandomizer.ini", g_dossier);

    journal("---- Randomizer RE HD v0.1 : demarrage");
    {
        /* Les adresses ne valent que pour une version précise de bhd.exe : sur une autre version,
         * on ne pose rien (le jeu tourne normalement, XInput reste transmis). */
        char exe[MAX_PATH];
        WIN32_FILE_ATTRIBUTE_DATA infos;
        GetModuleFileNameA(NULL, exe, MAX_PATH);
        if (!GetFileAttributesExA(exe, GetFileExInfoStandard, &infos) ||
            infos.nFileSizeHigh != 0 || infos.nFileSizeLow != TAILLE_BHD_EXE) {
            journal("Version du jeu non prise en charge (%s, %lu octets au lieu de %lu) : randomizer inactif.",
                    exe, (unsigned long)infos.nFileSizeLow, (unsigned long)TAILLE_BHD_EXE);
            return;
        }
    }
    if (!GetPrivateProfileIntA("Randomizer", "Actif", 1, ini)) {
        journal("Desactive dans randomizer.ini (Actif=0).");
        return;
    }
    GetPrivateProfileStringA("Randomizer", "Seed", "randomizer_seed.lua", seed, MAX_PATH, ini);
    if (seed[0] && (seed[1] == ':' || seed[0] == '\\'))
        lstrcpynA(chemin_seed, seed, MAX_PATH);
    else
        _snprintf(chemin_seed, MAX_PATH, "%s%s", g_dossier, seed);

    if (!charger_seed(chemin_seed)) {
        journal("Seed introuvable : %s. Le jeu tourne sans randomizer.", chemin_seed);
        return;
    }
    journal("Seed %ld chargee : %d emplacements, armes aleatoires : %s. Fichier : %s",
            g_graine, g_nb, g_armes == 1 ? "OUI" : g_armes == 0 ? "non" : "inconnu", chemin_seed);
    if (g_nb == 0) return;

    CloseHandle(CreateThread(NULL, 0, surveillance, NULL, 0, NULL));
}

/* -------------------------------------- transmission vers le vrai XInput */

static HMODULE g_xinput;

static FARPROC vraie(const char *nom)
{
    if (!g_xinput) {
        char chemin[MAX_PATH];
        UINT n = GetSystemDirectoryA(chemin, MAX_PATH);   /* SysWOW64 pour un jeu 32 bits */
        lstrcpynA(chemin + n, "\\xinput1_4.dll", MAX_PATH - n);
        g_xinput = LoadLibraryA(chemin);
        if (!g_xinput) return NULL;
    }
    return GetProcAddress(g_xinput, nom);
}

#define TRANSMETTRE(nom_export, cle, type_ret, defaut, params, args)          \
    typedef type_ret (WINAPI *T_##nom_export) params;                        \
    type_ret WINAPI nom_export params                  \
    {                                                                        \
        static T_##nom_export f;                                             \
        if (!f) f = (T_##nom_export)vraie(cle);                              \
        return f ? f args : defaut;                                          \
    }

TRANSMETTRE(XInputGetState,              "XInputGetState",              DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, void *b), (a, b))
TRANSMETTRE(XInputSetState,              "XInputSetState",              DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, void *b), (a, b))
TRANSMETTRE(XInputGetCapabilities,       "XInputGetCapabilities",       DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, DWORD b, void *c), (a, b, c))
TRANSMETTRE(XInputGetBatteryInformation, "XInputGetBatteryInformation", DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, BYTE b, void *c), (a, b, c))
TRANSMETTRE(XInputGetKeystroke,          "XInputGetKeystroke",          DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, DWORD b, void *c), (a, b, c))
TRANSMETTRE(XInputGetAudioDeviceIds,     "XInputGetAudioDeviceIds",     DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, void *b, void *c, void *d, void *e), (a, b, c, d, e))
/* fonctions non documentées, exportées seulement par numéro */
TRANSMETTRE(XInputGetStateEx,            (const char *)100,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, void *b), (a, b))
TRANSMETTRE(XInputWaitForGuideButton,    (const char *)101,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, DWORD b, void *c), (a, b, c))
TRANSMETTRE(XInputCancelGuideButtonWait, (const char *)102,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a), (a))
TRANSMETTRE(XInputPowerOffController,    (const char *)103,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a), (a))
TRANSMETTRE(XInputGetBaseBusInformation, (const char *)104,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, void *b), (a, b))
TRANSMETTRE(XInputGetCapabilitiesEx,     (const char *)108,             DWORD, ERROR_DEVICE_NOT_CONNECTED, (DWORD a, DWORD b, DWORD c, void *d), (a, b, c, d))

typedef void (WINAPI *T_XInputEnable)(BOOL);
void WINAPI XInputEnable(BOOL actif)
{
    static T_XInputEnable f;
    if (!f) f = (T_XInputEnable)vraie("XInputEnable");
    if (f) f(actif);
}

/* ------------------------------------------------------------------ DllMain */

BOOL WINAPI DllMain(HINSTANCE inst, DWORD raison, LPVOID reserve)
{
    (void)reserve;
    if (raison == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(inst);
        InitializeCriticalSection(&g_verrou_journal);
        demarrer();
    }
    return TRUE;
}
