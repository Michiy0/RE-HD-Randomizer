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
#ifndef ADR_PTR_PARTIE
#define ADR_PTR_PARTIE  (BASE_JEU + 0x8F2F28u)
#endif
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
static int   g_visible_seed;              /* objets_visibles = true dans la seed */

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
        } else if (strstr(ligne, "objets_visibles =")) {
            g_visible_seed = strstr(ligne, "true") ? 1 : 0;
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

/* ----------------------------------------- objets visibles (Visible=1 dans randomizer.ini)
 *
 * Trouvé le 17/11/2026 dans le code du jeu : chaque pièce place ses objets en appelant
 * bhd.exe+819E0 (« SpawnItem ») avec, sur la pile : +4 = id, +8 = position, +0C = angle, +10 = quantité,
 * +18 = numéro de l'événement de la pièce (room\aev). Cette fonction crée le modèle 3D posé par terre à partir
 * de l'id (bhd.exe+E77F0), puis écrit id et quantité dans l'événement (bhd.exe+802E0). En remplaçant l'id et
 * la quantité À L'ENTRÉE de la fonction, le jeu crée lui-même le bon modèle et le bon objet à ramasser.
 * L'emplacement est reconnu comme au ramassage : pièce + zone de ramassage de l'événement (+0x10..+0x2C). */
#ifndef ADR_SPAWN
#define ADR_SPAWN       (BASE_JEU + 0x819E0u)
#endif
#ifndef ADR_SCENE
#define ADR_SCENE       (BASE_JEU + 0x8F2FC8u)   /* objet « scène » ; +0x3A0 = liste des événements */
#endif
static int g_visible;

static const Emplacement *chercher_emplacement(DWORD piece, const DWORD *valeurs)
{
    int i;
    for (i = 0; i < g_nb; i++)
        if (g_seed[i].piece == piece && memcmp(g_seed[i].empreinte, valeurs, 8 * sizeof(DWORD)) == 0)
            return &g_seed[i];
    return NULL;
}

/* Le modèle 3D d'un objet posé (arc\model\item\iNNNp.arc, NNN = id sur 3 chiffres) n'est chargé que s'il
 * figure dans la liste de ressources de la pièce. Ces listes sont dans une table modifiable du jeu : une
 * table par zone (1 à 5), une entrée par pièce, qui pointe vers une liste de noms terminée par 0
 * (ex. pièce 105 : pl02, wep03, em15, i015p, i069p, i068p…). Sans le modèle, le jeu plante en cherchant
 * nativePC\model\item\iNNN\iNNNp.mod (test du 17/11/2026). Au lancement, on ajoute donc à chaque pièce les
 * modèles des objets que la seed y place ; un objet sans fichier de modèle n'est pas remplacé par terre
 * (seulement au ramassage, comme avant). */
static const struct { DWORD table, dernier; } g_tables_pieces[5] = {
    { BASE_JEU + 0x8B7718u, 0x1C }, { BASE_JEU + 0x8B7A00u, 0x1C }, { BASE_JEU + 0x8B7C90u, 0x1A },
    { BASE_JEU + 0x8B7E48u, 0x12 }, { BASE_JEU + 0x8B8090u, 0x15 } };
static char g_noms_modeles[MAX_EMPLACEMENTS][8];
static BYTE g_modele_ok[MAX_EMPLACEMENTS];

static int liste_contient(const DWORD *liste, int n, const char *nom)
{
    int k;
    for (k = 0; k < n; k++)
        if (lisible((void *)liste[k], 8, 0) && lstrcmpiA((const char *)liste[k], nom) == 0) return 1;
    return 0;
}

static void ajouter_modeles(void)
{
    int i, j, pieces = 0, ajouts = 0, sans_modele = 0;
    for (i = 0; i < g_nb; i++) {
        DWORD piece = g_seed[i].piece, zone = piece >> 8, salle = piece & 0xFF, *case_table, *ancienne, *neuve;
        int n = 0, nouveaux = 0, deja_vue = 0;
        for (j = 0; j < i; j++) if (g_seed[j].piece == piece) { deja_vue = 1; break; }
        if (deja_vue) continue;                         /* une seule fois par pièce */
        if (zone < 1 || zone > 5 || salle > g_tables_pieces[zone - 1].dernier) continue;
        case_table = (DWORD *)(g_tables_pieces[zone - 1].table + salle * 4);
        if (!lisible(case_table, 4, 1)) continue;
        ancienne = (DWORD *)*case_table;
        if (ancienne) while (n < 256 && lisible(&ancienne[n], 4, 0) && ancienne[n]) n++;
        neuve = (DWORD *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, (n + 64 + 1) * sizeof(DWORD));
        if (!neuve) continue;
        if (n) memcpy(neuve, ancienne, n * sizeof(DWORD));
        for (j = i; j < g_nb; j++) {                    /* tous les emplacements de cette pièce */
            char chemin[MAX_PATH];
            if (g_seed[j].piece != piece) continue;
            _snprintf(g_noms_modeles[j], sizeof g_noms_modeles[j], "i%03lup", (unsigned long)g_seed[j].id);
            _snprintf(chemin, MAX_PATH, "%snativePC\\arc\\model\\item\\%s.arc", g_dossier, g_noms_modeles[j]);
            if (GetFileAttributesA(chemin) == INVALID_FILE_ATTRIBUTES) { sans_modele++; continue; }
            g_modele_ok[j] = 1;
            if (liste_contient(neuve, n + nouveaux, g_noms_modeles[j]) || nouveaux >= 64) continue;
            neuve[n + nouveaux++] = (DWORD)g_noms_modeles[j];
        }
        if (nouveaux) {
            *case_table = (DWORD)neuve;                 /* la table est dans .data : modifiable */
            pieces++;
            ajouts += nouveaux;
        } else {
            HeapFree(GetProcessHeap(), 0, neuve);
        }
    }
    journal("Objets visibles : %d modele(s) ajoute(s) dans %d piece(s) ; %d emplacement(s) sans modele "
            "(remplaces seulement au ramassage).", ajouts, pieces, sans_modele);
}

/* Appelée à l'entrée de SpawnItem (ESP = adresse de retour). */
static void remplacer_au_placement(CONTEXT *c)
{
    DWORD esp = c->Esp, scene, liste, nb, tableau, evt, piece, valeurs[8], ancien_id, ancienne_qte, idx;
    const Emplacement *e;

    if (!lisible((void *)esp, 0x20, 1) || !lisible((void *)ADR_SCENE, 4, 0)) return;
    scene = *(DWORD *)ADR_SCENE;
    if (!scene || !lisible((void *)(scene + 0x3A0 + 0xD4), 0x10, 0)) return;
    liste = scene + 0x3A0;
    nb = *(DWORD *)(liste + 0xD4);
    tableau = *(DWORD *)(liste + 0xE0);
    idx = *(DWORD *)(esp + 0x18);
    if (idx >= nb || !lisible((void *)(tableau + idx * 4), 4, 0)) return;
    evt = *(DWORD *)(tableau + idx * 4);
    if (!lisible((void *)(evt + 0x10), 0x20, 0) || !piece_actuelle(&piece)) return;
    memcpy(valeurs, (void *)(evt + 0x10), sizeof valeurs);
    e = chercher_emplacement(piece, valeurs);
    if (!e || !g_modele_ok[e - g_seed]) return;        /* pas de modèle chargé : on laisse l'objet d'origine */
    ancien_id = *(DWORD *)(esp + 0x04);
    ancienne_qte = *(DWORD *)(esp + 0x10);
    *(DWORD *)(esp + 0x04) = e->id;
    *(DWORD *)(esp + 0x10) = e->qte;
    if (g_messages < 500) {
        g_messages++;
        journal("Piece %X : objet pose remplace (evenement %lu) : id %lu x%lu -> id %lu x%lu", piece,
                (unsigned long)idx, (unsigned long)ancien_id, (unsigned long)ancienne_qte,
                (unsigned long)e->id, (unsigned long)e->qte);
    }
}

/* ------------------------------------------------ mode diagnostic (relevés) */

/* Activé par Diagnostic=1 dans randomizer.ini. À chaque objet examiné ou ramassé, écrit dans
 * randomizer_diagnostic.txt de quoi retrouver le tableau des objets de la pièce : adresse de la
 * structure (et sa position dans la structure de partie), registres, haut de la pile et mémoire
 * autour de l'objet. Aucun effet sur le jeu. */
static int  g_diagnostic;
static char g_fichier_diag[MAX_PATH];
static int  g_nb_diag;
#define MAX_DIAG       60
#define DIAG_AVANT     0x100
#define DIAG_APRES     0x400

static void diag_ajouter(char *tampon, int *n, int taille, const char *fmt, ...)
{
    va_list ap;
    int k;
    if (*n >= taille - 1) return;
    va_start(ap, fmt);
    k = _vsnprintf(tampon + *n, taille - 1 - *n, fmt, ap);
    va_end(ap);
    *n = (k < 0 || *n + k > taille - 1) ? taille - 1 : *n + k;
}

static void diagnostiquer(const CONTEXT *c)
{
    static char t[24576];
    int n = 0, i;
    DWORD piece = 0, partie = 0, s = c->Eax, adr, ecrit;
    SYSTEMTIME h;
    HANDLE f;

    if (g_nb_diag >= MAX_DIAG) return;
    g_nb_diag++;
    GetLocalTime(&h);
    piece_actuelle(&piece);
    if (lisible((void *)ADR_PTR_PARTIE, 4, 0)) partie = *(DWORD *)ADR_PTR_PARTIE;

    diag_ajouter(t, &n, sizeof t, "==== releve %d  %02d:%02d:%02d  piece=%X\r\n", g_nb_diag,
                 h.wHour, h.wMinute, h.wSecond, piece);
    diag_ajouter(t, &n, sizeof t, "struct(EAX)=%08X  partie=%08X  struct-partie=%s%X\r\n", s, partie,
                 s >= partie ? "+" : "-", s >= partie ? s - partie : partie - s);
    if (lisible((void *)(s + 0x34), 4, 0))
        diag_ajouter(t, &n, sizeof t, "id=%u qte=%u\r\n", *(DWORD *)(s + 0x34) >> 16, *(DWORD *)(s + 0x34) & 0xFFFF);
    diag_ajouter(t, &n, sizeof t, "EBX=%08X ECX=%08X EDX=%08X ESI=%08X EDI=%08X EBP=%08X ESP=%08X\r\n",
                 c->Ebx, c->Ecx, c->Edx, c->Esi, c->Edi, c->Ebp, c->Esp);
    diag_ajouter(t, &n, sizeof t, "pile:");
    for (i = 0; i < 16; i++) {
        adr = c->Esp + 4 * i;
        if (lisible((void *)adr, 4, 0)) diag_ajouter(t, &n, sizeof t, " %08X", *(DWORD *)adr);
    }
    diag_ajouter(t, &n, sizeof t, "\r\nmemoire (decalage par rapport a la structure) :\r\n");
    for (adr = s > DIAG_AVANT ? s - DIAG_AVANT : 0; adr < s + DIAG_APRES; adr += 16) {
        const BYTE *o = (const BYTE *)adr;
        diag_ajouter(t, &n, sizeof t, "%c%04X ", adr >= s ? '+' : '-', adr >= s ? adr - s : s - adr);
        if (!lisible(o, 16, 0)) { diag_ajouter(t, &n, sizeof t, " (illisible)\r\n"); continue; }
        for (i = 0; i < 16; i += 4)
            diag_ajouter(t, &n, sizeof t, " %08X", *(const DWORD *)(o + i));
        diag_ajouter(t, &n, sizeof t, "\r\n");
    }
    diag_ajouter(t, &n, sizeof t, "\r\n");

    f = CreateFileA(g_fichier_diag, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                    OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        WriteFile(f, t, (DWORD)n, &ecrit, NULL);
        CloseHandle(f);
    }
}

/* ------------------------------- diagnostic : recherches dans la mémoire */

/* Signature des objets posés ramassables (adresses dans les données de bhd.exe, fixes car pas d'ASLR) :
 * +0x00 = 00C233F4 et +0x08 = 00C2286C. +0x10..+0x2C = zone de ramassage (4 coins x,z) = empreinte,
 * +0x34 = (id << 16) | quantité, +0x3C = numéro de l'objet dans la pièce. */
#define SIGNATURE_OBJET   0x00C233F4u
#define SIGNATURE_OBJET2  0x00C2286Cu
#define MAX_TROUVES       128
#define MAX_SCANS         40

static HINSTANCE g_inst;                 /* notre DLL : exclue des recherches */
static int g_nb_scans;

/* Copie la mémoire avec ReadProcessMemory : une zone qui disparaît pendant la lecture donne un échec,
 * pas un plantage du jeu. */
static int copier(DWORD adr, void *dest, DWORD taille)
{
    SIZE_T lu = 0;
    return ReadProcessMemory(GetCurrentProcess(), (LPCVOID)adr, dest, taille, &lu) && lu == taille;
}

typedef void (*Visiteur)(DWORD base, const BYTE *tampon, DWORD taille, void *ctx);

static void parcourir_memoire(Visiteur visiter, void *ctx)
{
    static BYTE tampon[65536];
    MEMORY_BASIC_INFORMATION mbi;
    DWORD adr = 0x10000;
    const DWORD ecriture = PAGE_READWRITE | PAGE_WRITECOPY | PAGE_EXECUTE_READWRITE | PAGE_EXECUTE_WRITECOPY;

    while (adr < 0xFFFE0000u && VirtualQuery((LPCVOID)adr, &mbi, sizeof mbi)) {
        DWORD base = (DWORD)mbi.BaseAddress, fin = base + (DWORD)mbi.RegionSize, a;
        if (fin <= adr) break;                                 /* fin de l'espace d'adressage */
        if (mbi.State == MEM_COMMIT && (mbi.Protect & ecriture) && !(mbi.Protect & PAGE_GUARD)
            && mbi.AllocationBase != (PVOID)g_inst) {
            for (a = base; a < fin; a += sizeof tampon) {
                DWORD n = fin - a < sizeof tampon ? fin - a : sizeof tampon;
                if (copier(a, tampon, n)) visiter(a, tampon, n, ctx);
            }
        }
        adr = fin;
    }
}

typedef struct { DWORD adr[MAX_TROUVES]; int nb; DWORD cible; } Trouves;

static void visiter_signature(DWORD base, const BYTE *t, DWORD n, void *ctx)
{
    Trouves *r = (Trouves *)ctx;
    DWORD i;
    for (i = 0; i + 12 <= n; i += 16)
        if (*(const DWORD *)(t + i) == SIGNATURE_OBJET && *(const DWORD *)(t + i + 8) == SIGNATURE_OBJET2
            && r->nb < MAX_TROUVES)
            r->adr[r->nb++] = base + i;
}

static void visiter_pointeur(DWORD base, const BYTE *t, DWORD n, void *ctx)
{
    Trouves *r = (Trouves *)ctx;
    DWORD i;
    for (i = 0; i + 4 <= n; i += 4)
        if (*(const DWORD *)(t + i) == r->cible && r->nb < MAX_TROUVES)
            r->adr[r->nb++] = base + i;
}

static void ecrire_diag(const char *t, int n)
{
    DWORD ecrit;
    HANDLE f = CreateFileA(g_fichier_diag, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                           OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f != INVALID_HANDLE_VALUE) {
        WriteFile(f, t, (DWORD)n, &ecrit, NULL);
        CloseHandle(f);
    }
}

/* Pieges=1 dans randomizer.ini : pièges en écriture (désactivés par défaut). Résultat du 17/11/2026 : les
 * objets d'une pièce sont LIBÉRÉS quand on la quitte (leur mémoire sert ensuite à décompresser sons et
 * textures) ; ils ne sont pas réutilisés, donc les pièges posés sur eux n'attrapent pas leur création. */
static int g_pieges;

/* Liste tous les objets posés présents en mémoire (appelé peu après un changement de pièce). */
static void scanner_piece(DWORD piece)
{
    DWORD reels[3];
    int nb_reels = 0;
    static Trouves r;
    static char t[65536];
    int n = 0, k, i;
    SYSTEMTIME h;
    DWORD debut = GetTickCount();

    if (g_nb_scans >= MAX_SCANS) return;
    g_nb_scans++;
    r.nb = 0;
    parcourir_memoire(visiter_signature, &r);
    GetLocalTime(&h);
    diag_ajouter(t, &n, sizeof t, "==== scan %d  %02d:%02d:%02d  piece=%X : %d objet(s) a la signature (%lu ms)\r\n",
                 g_nb_scans, h.wHour, h.wMinute, h.wSecond, piece, r.nb, (unsigned long)(GetTickCount() - debut));
    for (k = 0; k < r.nb; k++) {
        DWORD o[0x70 / 4];                     /* -0x30 .. +0x40 */
        if (!copier(r.adr[k] - 0x30, o, sizeof o)) {
            diag_ajouter(t, &n, sizeof t, "obj %08X  (illisible)\r\n", r.adr[k]);
            continue;
        }
        diag_ajouter(t, &n, sizeof t, "obj %08X  id=%u qte=%u num=%u  +30=%08X +0C=%08X  valeurs=%X:",
                     r.adr[k], o[(0x30 + 0x34) / 4] >> 16, o[(0x30 + 0x34) / 4] & 0xFFFF, o[(0x30 + 0x3C) / 4],
                     o[(0x30 + 0x30) / 4], o[(0x30 + 0x0C) / 4], piece);
        for (i = 0; i < 8; i++)
            diag_ajouter(t, &n, sizeof t, i ? ",%08X" : "%08X", o[(0x30 + 0x10) / 4 + i]);
        diag_ajouter(t, &n, sizeof t, "\r\n    entete:");
        for (i = 0; i < 12; i++) diag_ajouter(t, &n, sizeof t, " %08X", o[i]);
        diag_ajouter(t, &n, sizeof t, "\r\n    +40..4F:");
        for (i = 0; i < 4; i++) diag_ajouter(t, &n, sizeof t, " %08X", o[(0x30 + 0x30) / 4 + i]);
        diag_ajouter(t, &n, sizeof t, "\r\n");
        /* vrai objet (même test que le mode relevé) : candidat pour les pièges en écriture */
        if ((o[(0x30 + 0x30) / 4] & 0xFF) == 0x04 && (o[(0x30 + 0x30) / 4] >> 16) != 0
            && (o[(0x30 + 0x34) / 4] >> 16) != 0 && nb_reels < 3)
            reels[nb_reels++] = r.adr[k];
    }
    if (nb_reels) {
        diag_ajouter(t, &n, sizeof t, "vrais objets :");
        for (i = 0; i < nb_reels; i++) diag_ajouter(t, &n, sizeof t, " %08X+34", reels[i]);
        diag_ajouter(t, &n, sizeof t, "\r\n");
    }
    diag_ajouter(t, &n, sizeof t, "\r\n");
    ecrire_diag(t, n);
}

/* Cherche qui pointe vers l'objet ramassé (pour trouver la liste des objets de la pièce). */
typedef struct { DWORD s, partie, ebx, ecx, esi, edi, piece, zone[8], id_qte, num; } Ramassage;
static Ramassage g_file[16];
static volatile LONG g_file_ecrit, g_file_lu;

static const char *repere(DWORD a, const Ramassage *p, DWORD *decalage)
{
    struct { const char *nom; DWORD v; } refs[] = {
        { "partie", p->partie }, { "ECX", p->ecx }, { "ESI", p->esi }, { "EBX", p->ebx }, { "EDI", p->edi } };
    int i;
    for (i = 0; i < 5; i++)
        if (refs[i].v && a >= refs[i].v && a - refs[i].v < 0x200000) { *decalage = a - refs[i].v; return refs[i].nom; }
    return NULL;
}

static void chercher_pointeurs(const Ramassage *p)
{
    static Trouves r;
    static char t[32768];
    int n = 0, k, i;
    DWORD debut = GetTickCount();

    r.nb = 0;
    r.cible = p->s;
    parcourir_memoire(visiter_pointeur, &r);
    diag_ajouter(t, &n, sizeof t, "==== pointeurs vers l'objet %08X (piece %X) : %d trouve(s) (%lu ms)\r\n",
                 p->s, p->piece, r.nb, (unsigned long)(GetTickCount() - debut));
    for (k = 0; k < r.nb; k++) {
        DWORD v[16], dec = 0;
        const char *nom = repere(r.adr[k], p, &dec);
        diag_ajouter(t, &n, sizeof t, "a %08X", r.adr[k]);
        if (nom) diag_ajouter(t, &n, sizeof t, " (= %s+%X)", nom, dec);
        if (copier(r.adr[k] - 0x20, v, sizeof v)) {
            diag_ajouter(t, &n, sizeof t, "\r\n   -20:");
            for (i = 0; i < 16; i++) diag_ajouter(t, &n, sizeof t, i == 8 ? " |%08X" : " %08X", v[i]);
        }
        diag_ajouter(t, &n, sizeof t, "\r\n");
    }
    diag_ajouter(t, &n, sizeof t, "\r\n");
    ecrire_diag(t, n);
}

static void noter_ramassage(const CONTEXT *c)
{
    LONG i = InterlockedIncrement(&g_file_ecrit) - 1;
    Ramassage *p;
    if (i - g_file_lu >= 16) return;                 /* file pleine : tant pis pour ce relevé */
    p = &g_file[i & 15];
    p->s = c->Eax; p->ebx = c->Ebx; p->ecx = c->Ecx; p->esi = c->Esi; p->edi = c->Edi;
    p->partie = lisible((void *)ADR_PTR_PARTIE, 4, 0) ? *(DWORD *)ADR_PTR_PARTIE : 0;
    p->piece = 0;
    piece_actuelle(&p->piece);
    memset(p->zone, 0, sizeof p->zone);
    p->id_qte = p->num = 0;
    if (lisible((void *)(c->Eax + 0x10), 0x30, 0)) {
        memcpy(p->zone, (void *)(c->Eax + 0x10), sizeof p->zone);
        p->num = *(DWORD *)(c->Eax + 0x30);
        p->id_qte = *(DWORD *)(c->Eax + 0x34);
    }
}

/* ------------------------------------------- diagnostic : origine de l'objet ramassé */

/* D'où le jeu tire-t-il l'objet posé ? On cherche dans toute la mémoire les autres copies de sa zone de
 * ramassage : en flottants (x1, z1 consécutifs, comme dans l'objet) et en entiers 16 bits arrondis (format
 * des scripts de pièce du Resident Evil d'origine). Une copie hors du tas, ou dans une zone qui contient
 * aussi l'id et la quantité, est sans doute le « script » de la pièce : en le modifiant avant la création
 * des objets, le jeu afficherait le nouvel objet par terre et dans l'aperçu. */
typedef struct { DWORD adr[48]; BYTE type[48]; int nb; DWORD f1, f2, objet; WORD e1, e2; } Origines;

static void visiter_origine(DWORD base, const BYTE *t, DWORD n, void *ctx)
{
    Origines *r = (Origines *)ctx;
    DWORD i;
    for (i = 0; i + 8 <= n && r->nb < 48; i += 2) {
        DWORD a = base + i;
        if (a >= r->objet && a < r->objet + 0x40) continue;          /* l'objet lui-même */
        if ((i & 3) == 0 && *(const DWORD *)(t + i) == r->f1 && *(const DWORD *)(t + i + 4) == r->f2) {
            r->adr[r->nb] = a; r->type[r->nb++] = 'f';
        } else if (*(const WORD *)(t + i) == r->e1 && *(const WORD *)(t + i + 2) == r->e2 && r->nb < 40) {
            r->adr[r->nb] = a; r->type[r->nb++] = 'e';
        }
    }
}

static WORD flottant_vers_entier(DWORD bits)
{
    union { DWORD d; float f; } u;
    u.d = bits;
    return (WORD)(short)(u.f < 0 ? u.f - 0.5f : u.f + 0.5f);
}

static void chercher_origine(const Ramassage *p)
{
    static Origines r;
    static char t[49152];
    int n = 0, k, i;
    DWORD debut = GetTickCount();

    if (!p->zone[0] && !p->zone[1]) return;
    memset(&r, 0, sizeof r);
    r.f1 = p->zone[0]; r.f2 = p->zone[1]; r.objet = p->s;
    r.e1 = flottant_vers_entier(p->zone[0]); r.e2 = flottant_vers_entier(p->zone[1]);
    parcourir_memoire(visiter_origine, &r);
    diag_ajouter(t, &n, sizeof t, "==== origine de l'objet %08X (piece %X, id=%u qte=%u, +30=%08X) : %d copie(s) "
                 "de la zone (x1=%08X z1=%08X ; entiers %d, %d) (%lu ms)\r\n", p->s, p->piece, p->id_qte >> 16,
                 p->id_qte & 0xFFFF, p->num, r.nb, r.f1, r.f2, (short)r.e1, (short)r.e2,
                 (unsigned long)(GetTickCount() - debut));
    for (k = 0; k < r.nb; k++) {
        MEMORY_BASIC_INFORMATION mbi;
        BYTE v[0xA0];
        const char *sorte = "?";
        if (VirtualQuery((LPCVOID)r.adr[k], &mbi, sizeof mbi))
            sorte = mbi.Type == MEM_IMAGE ? "image" : mbi.Type == MEM_MAPPED ? "fichier" : "tas";
        diag_ajouter(t, &n, sizeof t, "%c %08X  [%s, base %08X]", r.type[k], r.adr[k], sorte,
                     (DWORD)mbi.AllocationBase);
        if (copier(r.adr[k] - 0x40, v, sizeof v)) {
            for (i = 0; i < (int)sizeof v; i += 4) {
                if (i % 32 == 0) diag_ajouter(t, &n, sizeof t, "\r\n   %c%02X:", i < 0x40 ? '-' : '+',
                                              i < 0x40 ? 0x40 - i : i - 0x40);
                diag_ajouter(t, &n, sizeof t, i == 0x40 ? " |%08X" : " %08X", *(DWORD *)(v + i));
            }
        }
        diag_ajouter(t, &n, sizeof t, "\r\n");
    }
    diag_ajouter(t, &n, sizeof t, "\r\n");
    ecrire_diag(t, n);
}

/* ------------------------------------------- diagnostic : pièges en écriture (Diagnostic=1)
 *
 * Constat du 17/11/2026 : la zone de ramassage n'existe nulle part ailleurs en mémoire (ni script de pièce
 * en flottants, ni en entiers). En revanche, les objets posés sont RÉUTILISÉS d'une pièce à l'autre : le
 * même objet 1C23D3A0 portait le chargeur de la pièce 112, puis celui de la pièce 214. Le jeu les remplit
 * donc à chaque entrée dans une pièce. On pose des points d'arrêt matériels « en écriture » (DR1 à DR3) sur
 * l'id/quantité (+0x34) de trois objets de la pièce : à la pièce suivante, le processeur s'arrête juste
 * après l'écriture et on note l'instruction (EIP), les registres et la mémoire qu'ils désignent. Les
 * registres doivent montrer d'où viennent l'id et la quantité (le vrai « script » de la pièce), et le code
 * trouvé est l'endroit où l'on pourra changer l'objet AVANT que son modèle 3D soit chargé. */
#define MAX_PIEGES        40      /* écritures notées au plus (sur toute la partie) */
#define MAX_PAR_EIP       3       /* au plus 3 notes pour une même instruction */
#define MAX_DECLENCHEMENTS 20000  /* garde-fou : au-delà, on retire les pièges */

static volatile DWORD g_veille[3];            /* DR1..DR3 : adresses surveillées, 0 = libre */
static volatile DWORD g_veille_cond[3];       /* 0 = exécution, 0xD = écriture de 4 octets */

/* v0.7.3-dev : point d'arrêt en EXÉCUTION (DR1) dans la boucle qui crée les objets de la pièce à partir de
 * room\aev\r<pièce> (bhd.exe+8026B : ESI = l'objet tout juste copié, id/quantité encore à 0). Pour chaque
 * objet de type 4 (objet à ramasser), on pose un piège en écriture (DR2 ou DR3) sur son +0x34 : on voit
 * alors QUI écrit l'id et la quantité, et d'où il les tire. */
#ifndef ADR_AEV
#define ADR_AEV        (BASE_JEU + 0x8026Bu)
#endif
#define MAX_AEV_NOTES  64
static DWORD g_aev_notes[MAX_AEV_NOTES][4];    /* objet, +30, +34, pièce */
static volatile LONG g_nb_aev, g_aev_lu, g_aev_items;
static volatile LONG  g_veille_changee;        /* 1 : réarmer tous les threads */
static volatile LONG  g_declenchements;

typedef struct {
    DWORD tick, piece, eip, slot, adr, valeur, regs[8];   /* EAX EBX ECX EDX ESI EDI EBP ESP */
    BYTE  code[0x40];                                   /* 0x30 octets avant EIP, 0x10 après */
    DWORD pile[16];
    DWORD objet[0x40 / 4];                              /* l'objet entier (adr - 0x34) */
    DWORD autour[8][0x60 / 4];                          /* -0x20..+0x40 autour de chaque registre */
    BYTE  autour_ok[8];
} Ecriture;
static Ecriture g_ecritures[MAX_PIEGES];
static volatile LONG g_ecr_ecrit, g_ecr_lu;
static DWORD g_eip_vus[64], g_eip_compte[64];
static int   g_nb_eip;

static int compter_eip(DWORD eip)                    /* nombre de fois déjà noté (puis +1) */
{
    int i;
    for (i = 0; i < g_nb_eip; i++) if (g_eip_vus[i] == eip) return (int)g_eip_compte[i]++;
    if (g_nb_eip < 64) { g_eip_vus[g_nb_eip] = eip; g_eip_compte[g_nb_eip++] = 1; }
    return 0;
}

static DWORD taille_dll(void)                        /* taille de notre DLL en mémoire */
{
    const IMAGE_DOS_HEADER *d = (const IMAGE_DOS_HEADER *)g_inst;
    return ((const IMAGE_NT_HEADERS *)((const BYTE *)d + d->e_lfanew))->OptionalHeader.SizeOfImage;
}

/* Appelée par le gestionnaire d'exceptions, dans le thread du jeu : copie seulement, rien d'écrit sur disque. */
static void noter_ecriture(const CONTEXT *c, int slot)
{
    Ecriture *e;
    LONG i;
    int k;
    DWORD adr = g_veille[slot - 1], regs[8];

    if (c->Eip - (DWORD)g_inst < taille_dll()) return;  /* nos propres écritures (remplacement) */

    if (InterlockedIncrement(&g_declenchements) > MAX_DECLENCHEMENTS) {
        g_veille[0] = g_veille[1] = g_veille[2] = 0;
        InterlockedExchange(&g_veille_changee, 1);
        return;
    }
    if (g_ecr_ecrit >= MAX_PIEGES || compter_eip(c->Eip) >= MAX_PAR_EIP) return;
    i = InterlockedIncrement(&g_ecr_ecrit) - 1;
    if (i >= MAX_PIEGES) return;
    e = &g_ecritures[i];
    memset(e, 0, sizeof *e);
    e->tick = GetTickCount();
    piece_actuelle(&e->piece);
    e->eip = c->Eip; e->slot = (DWORD)slot; e->adr = adr;
    regs[0] = c->Eax; regs[1] = c->Ebx; regs[2] = c->Ecx; regs[3] = c->Edx;
    regs[4] = c->Esi; regs[5] = c->Edi; regs[6] = c->Ebp; regs[7] = c->Esp;
    memcpy(e->regs, regs, sizeof regs);
    if (lisible((void *)adr, 4, 0)) e->valeur = *(DWORD *)adr;
    if (lisible((void *)(c->Eip - 0x30), sizeof e->code, 0)) memcpy(e->code, (void *)(c->Eip - 0x30), sizeof e->code);
    if (lisible((void *)c->Esp, sizeof e->pile, 0)) memcpy(e->pile, (void *)c->Esp, sizeof e->pile);
    if (lisible((void *)(adr - 0x34), sizeof e->objet, 0)) memcpy(e->objet, (void *)(adr - 0x34), sizeof e->objet);
    for (k = 0; k < 8; k++)
        if (regs[k] >= 0x10000 && lisible((void *)(regs[k] - 0x20), sizeof e->autour[k], 0)) {
            memcpy(e->autour[k], (void *)(regs[k] - 0x20), sizeof e->autour[k]);
            e->autour_ok[k] = 1;
        }
}

/* Appelée quand le jeu vient de créer un objet de la pièce (ESI). Objet à ramasser (type 4) : piège en
 * écriture sur son +0x34, posé tout de suite dans ce thread et ensuite dans tous les autres. */
static void nouvel_objet_aev(CONTEXT *c)
{
    DWORD o = c->Esi, slot, idx;
    LONG i = InterlockedIncrement(&g_nb_aev) - 1;
    if (!lisible((void *)o, 0x40, 0)) return;
    if (i < MAX_AEV_NOTES) {
        g_aev_notes[i][0] = o;
        g_aev_notes[i][1] = *(DWORD *)(o + 0x30);
        g_aev_notes[i][2] = *(DWORD *)(o + 0x34);
        g_aev_notes[i][3] = 0;
        piece_actuelle(&g_aev_notes[i][3]);
    }
    if ((*(DWORD *)(o + 0x30) & 0xFF) != 4 || g_ecr_ecrit >= MAX_PIEGES) return;
    idx = 1 + ((DWORD)InterlockedIncrement(&g_aev_items) & 1);   /* g_veille[1] ou [2] : DR2 ou DR3 */
    slot = idx + 1;
    g_veille[idx] = o + 0x34;
    g_veille_cond[idx] = 0xD;
    (&c->Dr0)[slot] = o + 0x34;
    c->Dr7 = (c->Dr7 & ~((3u << (2 * slot)) | (0xFu << (16 + 4 * slot))))
             | (1u << (2 * slot)) | (0xDu << (16 + 4 * slot));
    InterlockedExchange(&g_veille_changee, 1);
}

/* Écrit les écritures notées dans randomizer_diagnostic.txt (thread de surveillance). */
static void ecrire_pieges(void)
{
    static const char *noms[8] = { "EAX", "EBX", "ECX", "EDX", "ESI", "EDI", "EBP", "ESP" };
    static char t[24576];
    while (g_aev_lu < g_nb_aev && g_aev_lu < MAX_AEV_NOTES) {
        const DWORD *a = g_aev_notes[g_aev_lu];
        int n = 0;
        diag_ajouter(t, &n, sizeof t, "creation objet %ld : %08X  piece=%X  +30=%08X  +34=%08X%s\r\n",
                     g_aev_lu + 1, a[0], a[3], a[1], a[2], (a[1] & 0xFF) == 4 ? "  (objet a ramasser : piege pose)" : "");
        ecrire_diag(t, n);
        InterlockedIncrement(&g_aev_lu);
    }
    while (g_ecr_lu < g_ecr_ecrit && g_ecr_lu < MAX_PIEGES) {
        const Ecriture *e = &g_ecritures[g_ecr_lu];
        int n = 0, i, k;
        SYSTEMTIME h;
        GetLocalTime(&h);
        diag_ajouter(t, &n, sizeof t, "==== ecriture %ld  %02d:%02d:%02d  piece=%X  DR%lu  objet %08X+34 <- %08X "
                     "(id=%u qte=%u)  EIP=bhd.exe+%X\r\n", g_ecr_lu + 1, h.wHour, h.wMinute, h.wSecond, e->piece,
                     e->slot, e->adr - 0x34, e->valeur, e->valeur >> 16, e->valeur & 0xFFFF, e->eip - BASE_JEU);
        diag_ajouter(t, &n, sizeof t, "regs:");
        for (k = 0; k < 8; k++) diag_ajouter(t, &n, sizeof t, " %s=%08X", noms[k], e->regs[k]);
        diag_ajouter(t, &n, sizeof t, "\r\ncode (EIP-30 .. EIP+10):");
        for (i = 0; i < (int)sizeof e->code; i++)
            diag_ajouter(t, &n, sizeof t, i == 0x30 ? " |%02X" : (i % 16 == 0 ? "\r\n   %02X" : " %02X"), e->code[i]);
        diag_ajouter(t, &n, sizeof t, "\r\npile:");
        for (i = 0; i < 16; i++) {
            DWORD v = e->pile[i];
            if (v >= BASE_JEU && v < BASE_JEU + 0x1000000u) diag_ajouter(t, &n, sizeof t, " [bhd+%X]", v - BASE_JEU);
            else diag_ajouter(t, &n, sizeof t, " %08X", v);
        }
        diag_ajouter(t, &n, sizeof t, "\r\nobjet:");
        for (i = 0; i < 0x40 / 4; i++) {
            if (i % 8 == 0) diag_ajouter(t, &n, sizeof t, "\r\n   +%02X:", i * 4);
            diag_ajouter(t, &n, sizeof t, " %08X", e->objet[i]);
        }
        for (k = 0; k < 8; k++) {
            if (!e->autour_ok[k]) continue;
            diag_ajouter(t, &n, sizeof t, "\r\n%s (%08X) -20..+40:", noms[k], e->regs[k]);
            for (i = 0; i < 0x60 / 4; i++) {
                if (i % 8 == 0) diag_ajouter(t, &n, sizeof t, "\r\n   %c%02X:", i < 8 ? '-' : '+',
                                             i < 8 ? 0x20 - i * 4 : i * 4 - 0x20);
                diag_ajouter(t, &n, sizeof t, i == 8 ? " |%08X" : " %08X", e->autour[k][i]);
            }
        }
        diag_ajouter(t, &n, sizeof t, "\r\n\r\n");
        ecrire_diag(t, n);
        InterlockedIncrement(&g_ecr_lu);
    }
}

/* --------------------------------------------- mode relevé (Releve=1) */

/* À chaque nouvelle pièce, note dans le journal les objets posés encore présents, sans rien ramasser.
 * Seuls les vrais objets sont gardés : type 4 en +0x30 (octet bas), numéro d'objet de la pièce non nul
 * (+0x30, 16 bits hauts) et id non nul. Les « jumeaux » (+0x30 = 00000004) et autres zones sont écartés.
 * Validé le 17/11/2026 : 112 → 3 objets, 214 → 4 objets, retour en 112 → 3 objets, sans objet fantôme. */
static int g_releve;
#define MAX_DEJA_NOTES 4096
static DWORD g_deja_notes[MAX_DEJA_NOTES];
static int   g_nb_deja_notes;

static int est_objet_reel(const DWORD *o)        /* o = les 0x40 premiers octets de l'objet */
{
    return (o[0x30 / 4] & 0xFF) == 0x04 && (o[0x30 / 4] >> 16) != 0 && (o[0x34 / 4] >> 16) != 0;
}

static DWORD empreinte_cle(DWORD piece, const DWORD *zone)
{
    DWORD h = 2166136261u ^ piece;                  /* FNV-1a sur la pièce et les 8 valeurs */
    int i;
    for (i = 0; i < 8; i++) { h ^= zone[i]; h *= 16777619u; }
    return h ? h : 1;
}

static int deja_note(DWORD cle)
{
    int i;
    for (i = 0; i < g_nb_deja_notes; i++) if (g_deja_notes[i] == cle) return 1;
    if (g_nb_deja_notes < MAX_DEJA_NOTES) g_deja_notes[g_nb_deja_notes++] = cle;
    return 0;
}

/* Événements de la pièce courante (liste [scène]+0x3A0 : nombre en +0xD4, tableau en +0xE0). Seuls ces
 * objets appartiennent vraiment à la pièce : les autres sont des « fantômes » de la pièce précédente, encore
 * en mémoire au moment du relevé (constaté le 18/11/2026 : l'herbe de l'escalier est notée en 118, 204, 20B).
 * Renvoie le nombre d'adresses lues, ou -1 si la liste est illisible (on ne filtre pas alors). */
#define MAX_EVENEMENTS 512
static int evenements_piece(DWORD *adresses)
{
    DWORD scene, liste, nb, tableau;
    if (!lisible((void *)ADR_SCENE, 4, 0)) return -1;
    scene = *(DWORD *)ADR_SCENE;
    if (!scene || !lisible((void *)(scene + 0x3A0 + 0xD4), 0x10, 0)) return -1;
    liste = scene + 0x3A0;
    nb = *(DWORD *)(liste + 0xD4);
    tableau = *(DWORD *)(liste + 0xE0);
    if (nb == 0 || nb > MAX_EVENEMENTS || !lisible((void *)tableau, nb * 4, 0)) return -1;
    memcpy(adresses, (void *)tableau, nb * 4);
    return (int)nb;
}

static int dans_liste(DWORD adresse, const DWORD *liste, int nb)
{
    int i;
    for (i = 0; i < nb; i++) if (liste[i] == adresse) return 1;
    return 0;
}

static void releve_piece(DWORD piece)
{
    static Trouves r;
    static DWORD evts[MAX_EVENEMENTS];
    int k, reels = 0, nouveaux = 0, fantomes = 0, nb_evts;
    DWORD debut = GetTickCount();

    r.nb = 0;
    parcourir_memoire(visiter_signature, &r);
    nb_evts = evenements_piece(evts);
    for (k = 0; k < r.nb; k++) {
        DWORD o[0x40 / 4];
        if (!copier(r.adr[k], o, sizeof o) || !est_objet_reel(o)) continue;
        if (nb_evts >= 0 && !dans_liste(r.adr[k], evts, nb_evts)) { fantomes++; continue; }
        reels++;
        if (deja_note(empreinte_cle(piece, &o[0x10 / 4]))) continue;
        nouveaux++;
        journal("Releve auto\tpiece=%X\tid=%u\tqte=%u\tnum=%u\tobj=%X\tvaleurs=%X:%08X,%08X,%08X,%08X,%08X,%08X,%08X,%08X",
                piece, o[0x34 / 4] >> 16, o[0x34 / 4] & 0xFFFF, o[0x3C / 4], o[0x30 / 4] >> 16, piece,
                o[4], o[5], o[6], o[7], o[8], o[9], o[10], o[11]);
    }
    journal("Releve piece %X : %d objet(s) present(s), %d nouveau(x)%s (%lu ms)", piece, reels, nouveaux,
            nb_evts < 0 ? ", liste des evenements illisible" :
            fantomes ? ", fantome(s) ecarte(s)" : "", (unsigned long)(GetTickCount() - debut));
    if (fantomes) journal("Releve piece %X : %d objet(s) d'une autre piece ignore(s).", piece, fantomes);
}

/* Appelée régulièrement par le thread de surveillance (modes diagnostic et relevé). */
static void diagnostic_periodique(void)
{
    static DWORD derniere_piece = 0xFFFFFFFF, piece_stable, depuis;
    DWORD piece;

    if (g_diagnostic) ecrire_pieges();
    while (g_diagnostic && g_file_lu < g_file_ecrit) {
        chercher_pointeurs(&g_file[g_file_lu & 15]);
        chercher_origine(&g_file[g_file_lu & 15]);
        InterlockedIncrement(&g_file_lu);
    }
    if (!piece_actuelle(&piece) || piece == 0) return;   /* 0 : chargement ou menu */
    if (piece != piece_stable) { piece_stable = piece; depuis = GetTickCount(); return; }
    /* pièce stable depuis 1,5 s et différente de la dernière traitée */
    if (piece != derniere_piece && GetTickCount() - depuis >= 1500) {
        derniere_piece = piece;
        if (g_releve) releve_piece(piece);
        if (g_diagnostic) scanner_piece(piece);
    }
}

static LONG CALLBACK gestionnaire(EXCEPTION_POINTERS *ep)
{
    CONTEXT *c = ep->ContextRecord;
    if (ep->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP)
        return EXCEPTION_CONTINUE_SEARCH;
    if (c->Eip == ADR_SPAWN && g_veille[0] == ADR_SPAWN) {   /* placement d'un objet (Visible=1) */
        c->Dr6 = 0;
        if (!g_coupe) remplacer_au_placement(c);
        c->EFlags |= 0x10000;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (c->Eip == ADR_AEV && g_veille[0] == ADR_AEV) {   /* création d'un objet de la pièce (diagnostic) */
        c->Dr6 = 0;
        nouvel_objet_aev(c);
        c->EFlags |= 0x10000;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if ((c->Dr6 & 0xCu) && c->Eip != ADR_LECTURE) {     /* piège en écriture DR2/DR3 (diagnostic) */
        DWORD dr6 = c->Dr6;
        c->Dr6 = 0;
        if (dr6 & 4u) noter_ecriture(c, 2);
        if (dr6 & 8u) noter_ecriture(c, 3);
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    if (c->Eip != ADR_LECTURE)
        return EXCEPTION_CONTINUE_SEARCH;
    if (g_diagnostic && !g_coupe) {                    /* avant tout remplacement */
        diagnostiquer(c);
        noter_ramassage(c);                            /* recherche faite plus tard, hors du jeu */
    }
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
                int i;
                c.Dr0 = ADR_LECTURE;
                c.Dr7 = (c.Dr7 & ~0x000F0003u) | 1u;   /* L0 = 1, exécution, longueur 1 */
                /* pièges en écriture (diagnostic) : DRi = adresse, Li = 1, RWi = 01 (écriture), LENi = 11 (4 o) */
                c.Dr7 &= ~0xFFF000FCu;
                for (i = 1; i <= 3; i++) {
                    DWORD a = g_veille[i - 1];
                    (&c.Dr0)[i] = a;
                    if (a) c.Dr7 |= (1u << (2 * i)) | (g_veille_cond[i - 1] << (16 + 4 * i));
                }
            } else {
                if (c.Dr0 == ADR_LECTURE) { c.Dr0 = 0; c.Dr7 &= ~3u; }
                c.Dr1 = c.Dr2 = c.Dr3 = 0;
                c.Dr7 &= ~0xFFF000FCu;
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
                if (armer == 1 && deja_arme(te.th32ThreadID)) continue;
                if (deja_arme(te.th32ThreadID)) { regler_thread(te.th32ThreadID, 1); continue; }
                regler_thread(te.th32ThreadID, 1);
                if (g_nb_threads < MAX_THREADS) g_threads_armes[g_nb_threads++] = te.th32ThreadID;
            } else {
                regler_thread(te.th32ThreadID, 0);
            }
        } while (Thread32Next(s, &te));
    }
    CloseHandle(s);
}

/* Diagnostic : copie unique du code de bhd.exe tel qu'il est en mémoire (déchiffré par la protection
 * Steam) dans bhd_memoire.bin, pour l'étudier hors du jeu : trouver le code qui crée les objets posés et
 * celui qui charge leur modèle 3D. Fichier personnel, jamais publié. */
static void vider_image(void)
{
    static BYTE tampon[65536];
    char chemin[MAX_PATH];
    const IMAGE_DOS_HEADER *d = (const IMAGE_DOS_HEADER *)BASE_JEU;
    DWORD taille, a, ecrit, illisibles = 0;
    HANDLE f;

    _snprintf(chemin, MAX_PATH, "%sbhd_memoire.bin", g_dossier);
    if (GetFileAttributesA(chemin) != INVALID_FILE_ATTRIBUTES) return;      /* déjà fait */
    if (!lisible(d, sizeof *d, 0) || !lisible((const BYTE *)d + d->e_lfanew, sizeof(IMAGE_NT_HEADERS), 0)) return;
    taille = ((const IMAGE_NT_HEADERS *)((const BYTE *)d + d->e_lfanew))->OptionalHeader.SizeOfImage;
    f = CreateFileA(chemin, GENERIC_WRITE, 0, NULL, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, NULL);
    if (f == INVALID_HANDLE_VALUE) return;
    for (a = 0; a < taille; a += sizeof tampon) {
        DWORD n = taille - a < sizeof tampon ? taille - a : sizeof tampon, p;
        for (p = 0; p < n; p += 4096) {                     /* page par page : une page illisible = zéros */
            DWORD m = n - p < 4096 ? n - p : 4096;
            if (!copier(BASE_JEU + a + p, tampon + p, m)) { memset(tampon + p, 0, m); illisibles++; }
        }
        WriteFile(f, tampon, n, &ecrit, NULL);
    }
    CloseHandle(f);
    journal("Image de bhd.exe copiee dans bhd_memoire.bin : %lu octets (%lu page(s) illisible(s)).",
            (unsigned long)taille, (unsigned long)illisibles);
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
    unsigned tour;
    (void)inutile;

    /* On attend que le jeu soit vraiment lancé (fenêtre visible) : avant, la protection Steam
     * déchiffre encore le code et n'aime pas forcément les registres de débogage. */
    while (!fenetre) {
        Sleep(500);
        EnumWindows(chercher_fenetre, (LPARAM)&fenetre);
    }
    Sleep(3000);

    if (g_diagnostic) vider_image();
    if (g_visible) ajouter_modeles();             /* écran titre : aucune pièce n'est encore chargée */
    AddVectoredExceptionHandler(1, gestionnaire);
    InterlockedExchange(&g_actif, 1);
    journal("Point d'arret pose en bhd.exe+1512ED.");

    for (tour = 0;; tour++) {
        if (g_coupe) {
            parcourir_threads(0);
            journal("Points d'arret retires de tous les threads.");
            return 0;
        }
        if (InterlockedExchange(&g_veille_changee, 0)) parcourir_threads(2);   /* pièges déplacés */
        else if (tour % 4 == 0) parcourir_threads(1);   /* arme les threads créés depuis le dernier passage */
        if (g_diagnostic || g_releve) diagnostic_periodique();
        Sleep(250);
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

    journal("---- Randomizer RE HD v0.8.4 : demarrage");
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

    g_diagnostic = GetPrivateProfileIntA("Randomizer", "Diagnostic", 0, ini);
    if (g_diagnostic) {
        _snprintf(g_fichier_diag, MAX_PATH, "%srandomizer_diagnostic.txt", g_dossier);
        journal("Mode diagnostic actif : details dans randomizer_diagnostic.txt (%d releves au plus).", MAX_DIAG);
    }
    g_pieges = g_diagnostic && GetPrivateProfileIntA("Randomizer", "Pieges", 0, ini);
    g_releve = GetPrivateProfileIntA("Randomizer", "Releve", 0, ini);
    if (g_releve)
        journal("Mode releve actif : les objets de chaque nouvelle piece sont notes ici (lignes Releve auto).");

    if (!charger_seed(chemin_seed)) {
        journal("Seed introuvable : %s. Le jeu tourne sans randomizer%s.", chemin_seed,
                g_diagnostic || g_releve ? " (releve ou diagnostic seul)" : "");
        if (!g_diagnostic && !g_releve) return;
    } else {
        journal("Seed %ld chargee : %d emplacements, armes aleatoires : %s. Fichier : %s",
                g_graine, g_nb, g_armes == 1 ? "OUI" : g_armes == 0 ? "non" : "inconnu", chemin_seed);
    }
    if (g_nb == 0 && !g_diagnostic && !g_releve) return;

    /* Objets visibles : option choisie à la génération (dans la seed) ; Visible=0/1 dans randomizer.ini
     * la remplace. Le mode relevé doit voir les objets d'origine : il la désactive. */
    g_visible = GetPrivateProfileIntA("Randomizer", "Visible", -1, ini);
    if (g_visible < 0) g_visible = g_visible_seed;
    if (g_visible && g_releve) {
        g_visible = 0;
        journal("Objets visibles desactives pendant le mode releve (les objets d'origine doivent etre notes).");
    }
    if (g_visible && g_nb == 0) g_visible = 0;
    if (g_visible) {                              /* prioritaire sur les pièges du diagnostic (même DR1) */
        g_pieges = 0;
        g_veille[0] = ADR_SPAWN;                  /* DR1 : exécution */
        g_veille_cond[0] = 0;
        journal("Objets visibles : les objets poses sont remplaces avant la creation de leur modele.");
    }
    if (g_pieges) {
        g_veille[0] = ADR_AEV;                    /* DR1 : exécution */
        g_veille_cond[0] = 0;
        journal("Pieges actifs : creation des objets de piece (bhd.exe+8026B) puis ecriture de leur id.");
    }

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
        g_inst = inst;
        InitializeCriticalSection(&g_verrou_journal);
        demarrer();
    }
    return TRUE;
}
