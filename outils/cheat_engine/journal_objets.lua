-- journal_objets.lua  (version 1, NON TESTEE : à essayer et à corriger ensemble)
-- Pour Resident Evil HD Remaster, bhd.exe de 9 640 360 octets (version Steam actuelle).
--
-- Ce que fait ce script : à chaque fois que tu interagis avec un objet dans le jeu,
-- il écrit une ligne dans le fichier journal_objets.txt (sur ton Bureau) avec :
--   l'heure, la pièce (zone/numéro, identifiant hexadécimal), le type de ramassage,
--   l'identifiant et la quantité de l'objet, et des valeurs fixes de sa structure.
-- Le jeu ne s'arrête plus : le script le relance tout seul.
--
-- Mode d'emploi :
--   1. Dans le Memory Viewer, retire tous les anciens points d'arrêt (clic sur la ligne, F5).
--   2. Cheat Engine attaché à bhd.exe, jeu lancé (partie chargée).
--   3. Dans Cheat Engine : Table > Show Cheat Table Lua Script (ou Ctrl+Alt+L), colle ce script,
--      puis clique sur "Execute script".
--   4. Joue : interagis avec les objets (même si tu refuses de les prendre).
--   5. Pour arrêter : tape  arreterJournal()  dans la fenêtre Lua et valide.

local base = getAddress('bhd.exe')
local CHEMIN = (os.getenv('USERPROFILE') or 'C:') .. '\\Desktop\\journal_objets.txt'

local BP_POSE   = base + 0x1512ED   -- lecture de l'identifiant d'un objet "posé" (EAX = structure de l'objet)
local BP_DIRECT = base + 0x15128A   -- objet "direct" (EAX = identifiant, comme l'emblème)
local PTR_PARTIE = base + 0x8F2F28  -- pointeur vers la structure de partie (zone +E472C, pièce +E4730)

local function u32(a)
  local v = readInteger(a)
  if v == nil then return nil end
  return v & 0xFFFFFFFF
end

local function hex8(v)
  if v == nil then return '????????' end
  return string.format('%08X', v)
end

local function reg(nom32, nom64)
  local v = _G[nom32]
  if v == nil then v = _G[nom64] end
  if v == nil then return nil end
  return v & 0xFFFFFFFF
end

local function piece()
  local p = u32(PTR_PARTIE)
  if p == nil or p == 0 then return '?', '?', '???' end
  local z = u32(p + 0xE472C)
  local r = u32(p + 0xE4730)
  if z == nil or r == nil then return '?', '?', '???' end
  return z, r, string.format('%X', z * 256 + r)
end

local function ecrire(ligne)
  local f = io.open(CHEMIN, 'a')
  if f then
    f:write(ligne .. '\n')
    f:close()
  else
    print('Impossible d\'ecrire dans ' .. CHEMIN)
  end
end

local function traiter()
  local eip = reg('EIP', 'RIP')
  local z, r, id_piece = piece()
  local heure = os.date('%H:%M:%S')

  if eip == ((BP_POSE) & 0xFFFFFFFF) then
    local e = reg('EAX', 'RAX')
    local v = u32(e + 0x34)
    local qte, ident = 0, 0
    if v ~= nil then qte = v & 0xFFFF; ident = (v >> 16) & 0xFFFF end
    local brut = {}
    for off = 0x10, 0x2C, 4 do brut[#brut + 1] = hex8(u32(e + off)) end
    ecrire(string.format('%s\tpiece=%s (zone %s, n %s)\tchemin=pose\tid=%d (0x%X)\tqte=%d\tstruct=%X\tbrut10-2C=%s',
      heure, id_piece, tostring(z), tostring(r), ident, ident, qte, e, table.concat(brut, ' ')))
  elseif eip == ((BP_DIRECT) & 0xFFFFFFFF) then
    local ident = reg('EAX', 'RAX') or 0
    local s = reg('ESI', 'RSI')
    local qte = 0
    if s ~= nil then qte = u32(s + 0x6254) or 0 end
    ecrire(string.format('%s\tpiece=%s (zone %s, n %s)\tchemin=direct\tid=%d (0x%X)\tqte=%d',
      heure, id_piece, tostring(z), tostring(r), ident, ident, qte))
  end
end

function debugger_onBreakpoint()
  local ok, err = pcall(traiter)
  if not ok then print('Erreur du journal : ' .. tostring(err)) end
  debug_continueFromBreakpoint(co_run)
  return 1
end

function arreterJournal()
  pcall(function() debug_removeBreakpoint(BP_POSE) end)
  pcall(function() debug_removeBreakpoint(BP_DIRECT) end)
  print('Journal arrete.')
end

ecrire('# --- nouvelle session ' .. os.date('%Y-%m-%d %H:%M:%S') .. ' ---')
pcall(debugProcess)
debug_setBreakpoint(BP_POSE, 1, bptExecute)
debug_setBreakpoint(BP_DIRECT, 1, bptExecute)
print('Journal actif. Fichier : ' .. CHEMIN)
