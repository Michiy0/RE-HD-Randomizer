-- appliquer_seed.lua  (version 2, testée et validée en jeu)
-- Ancienne méthode, avec Cheat Engine. La méthode normale est maintenant la DLL (voir README) :
-- ne pas utiliser les deux en même temps.
-- Pour Resident Evil HD Remaster, bhd.exe de 9 640 360 octets (version Steam actuelle),
-- partie Chris en difficulté Normal.
--
-- Changement par rapport à la version 1 : le script ne modifie plus les registres (ce qui faisait boucler
-- le jeu). Il écrit directement le nouvel objet dans la structure de l'objet, juste AVANT que le jeu
-- ne la lise (point d'arrêt bhd.exe+1512ED, le même que celui du journal, qui fonctionne bien).
-- Un garde-fou arrête le script tout seul s'il se déclenche trop souvent.
--
-- Ce que fait ce script : à chaque interaction avec un objet posé dans une pièce, il identifie
-- l'emplacement (numéro de pièce + 8 valeurs fixes de la structure de l'objet) et, si la seed prévoit
-- un autre objet pour cet emplacement, remplace l'identifiant et la quantité dans la structure.
-- Les objets qu'il ne connaît pas sont laissés tels quels et notés dans journal_non_repertorie.txt
-- (sur le Bureau).
--
-- Mode d'emploi :
--   1. Génère une seed :  python generateur_seed.py 12345   (crée seed_12345.lua)
--   2. Copie seed_12345.lua sur ton Bureau (ou change SEED_FICHIER plus bas).
--   3. Arrête les autres scripts :  arreterJournal()  arreterTest()  arreterSeed()  puis  debugger_onBreakpoint = nil
--      Retire aussi les points d'arrêt manuels du Memory Viewer.
--   4. Jeu lancé et partie chargée, Cheat Engine attaché à bhd.exe :
--      Table > Show Cheat Table Lua Script (Ctrl+Alt+L), colle ce script, "Execute script".
--   5. Joue. Pour arrêter : arreterSeed()  puis  debugger_onBreakpoint = nil

SEED_FICHIER = (os.getenv('USERPROFILE') or 'C:') .. '\\Desktop\\seed_12345.lua'
JOURNAL      = (os.getenv('USERPROFILE') or 'C:') .. '\\Desktop\\journal_non_repertorie.txt'

local base       = getAddress('bhd.exe')
local BP_LECTURE = base + 0x1512ED   -- juste avant la lecture de l'identifiant (EAX = structure de l'objet)
local PTR_PARTIE = base + 0x8F2F28   -- structure de partie (zone +E472C, pièce +E4730)

local charger, erreur = loadfile(SEED_FICHIER)
if charger == nil then
  print('Seed introuvable ou illisible : ' .. tostring(erreur))
  return
end
local seed = charger()
local table_seed = {}
local function cle(piece, valeurs)
  local t = {}
  for i = 1, #valeurs do t[i] = string.format('%08X', valeurs[i]) end
  return string.format('%X', piece) .. ':' .. table.concat(t, ',')
end
local nombre = 0
for _, r in ipairs(seed.remplacements) do
  table_seed[cle(r.piece, r.empreinte)] = r
  nombre = nombre + 1
end

local function u32(a)
  local v = readInteger(a)
  if v == nil then return nil end
  return v & 0xFFFFFFFF
end

local function reg(nom32, nom64)
  local v = _G[nom32]
  if v == nil then v = _G[nom64] end
  return v
end

local function piece_actuelle()
  local p = u32(PTR_PARTIE)
  if p == nil or p == 0 then return nil end
  local z = u32(p + 0xE472C)
  local r = u32(p + 0xE4730)
  if z == nil or r == nil then return nil end
  return z * 256 + r
end

local function ecrire(ligne)
  local f = io.open(JOURNAL, 'a')
  if f then f:write(ligne .. '\n'); f:close() end
end

-- garde-fou : si le point d'arrêt se déclenche plus de 30 fois en moins de 2 secondes, on coupe tout
local fenetre_debut, fenetre_compte, messages = os.clock(), 0, 0

function arreterSeed()
  pcall(function() debug_removeBreakpoint(BP_LECTURE) end)
  print('Seed arretee.')
end

function debugger_onBreakpoint()
  local ok, err = pcall(function()
    local maintenant = os.clock()
    if maintenant - fenetre_debut > 2 then fenetre_debut, fenetre_compte = maintenant, 0 end
    fenetre_compte = fenetre_compte + 1
    if fenetre_compte > 30 then
      arreterSeed()
      print('GARDE-FOU : trop de declenchements, seed arretee. Recharge ta sauvegarde.')
      return
    end

    local eip = reg('EIP', 'RIP')
    if eip == nil or (eip & 0xFFFFFFFF) ~= (BP_LECTURE & 0xFFFFFFFF) then return end
    local structure = reg('EAX', 'RAX')
    local piece = piece_actuelle()
    if structure == nil or piece == nil then return end
    structure = structure & 0xFFFFFFFF

    local valeurs = {}
    for off = 0x10, 0x2C, 4 do valeurs[#valeurs + 1] = u32(structure + off) or 0 end
    local r = table_seed[cle(piece, valeurs)]
    if r ~= nil then
      -- quantité dans les 16 bits bas, identifiant dans les 16 bits hauts
      writeInteger(structure + 0x34, (r.id << 16) | (r.qte & 0xFFFF))
      if messages < 50 then
        messages = messages + 1
        print(string.format('Piece %X : objet remplace par id %d (quantite %d)', piece, r.id, r.qte))
      end
    else
      local courant = u32(structure + 0x34) or 0
      ecrire(string.format('%s\tpiece=%X\tid=%d\tvaleurs=%s', os.date('%H:%M:%S'), piece, (courant >> 16) & 0xFFFF, cle(piece, valeurs)))
    end
  end)
  if not ok then print('Erreur : ' .. tostring(err)) end
  debug_continueFromBreakpoint(co_run)
  return 1
end

pcall(debugProcess)
debug_setBreakpoint(BP_LECTURE, 1, bptExecute)
local armes = 'inconnu (ancien fichier de seed)'
if seed.armes_aleatoires == true then armes = 'OUI' elseif seed.armes_aleatoires == false then armes = 'non' end
print(string.format('Seed %s active : %d emplacements, armes aleatoires : %s. Fichier : %s', tostring(seed.graine), nombre, armes, SEED_FICHIER))
