-- test_remplacement.lua  (version 1, NON TESTEE : à essayer et à corriger ensemble)
-- Pour Resident Evil HD Remaster, bhd.exe de 9 640 360 octets (version Steam actuelle).
--
-- Ce que fait ce script : quand tu interagis avec un objet dont l'identifiant vaut ANCIEN,
-- il le remplace par NOUVEAU juste après sa lecture par le jeu (instruction bhd.exe+1512F1,
-- où ECX contient l'identifiant). C'est le même test qu'on faisait à la main avec un point d'arrêt,
-- mais sans toucher aux registres. Le jeu ne s'arrête pas.
--
-- Identifiants connus : 3 pistolet, 17 chargeur, 34 herbe verte, 44 vieille clé, 68 ruban encreur,
--                       101 trousse de premiers secours, 112 poignard.
--
-- Mode d'emploi :
--   1. Arrête d'abord le journal si il tourne :  arreterJournal()   puis   debugger_onBreakpoint = nil
--      Retire aussi tous les points d'arrêt posés à la main dans le Memory Viewer (clic sur la ligne, F5).
--   2. Change les deux valeurs ci-dessous (ANCIEN et NOUVEAU) selon le test.
--   3. Table > Show Cheat Table Lua Script (Ctrl+Alt+L), colle le script, "Execute script".
--   4. Interagis avec un objet d'identifiant ANCIEN : le jeu doit te proposer NOUVEAU.
--   5. Pour arrêter : tape  arreterTest()  puis  debugger_onBreakpoint = nil

ANCIEN  = 112    -- herbe verte
NOUVEAU = 34   -- poignard

local base = getAddress('bhd.exe')
local BP = base + 0x1512F1

local function reg(nom32, nom64)
  local v = _G[nom32]
  if v == nil then v = _G[nom64] end
  return v
end

local function fixer_ecx(valeur)
  if _G['ECX'] ~= nil then ECX = valeur else RCX = valeur end
end

function debugger_onBreakpoint()
  local ok, err = pcall(function()
    local eip = reg('EIP', 'RIP')
    if eip ~= nil and (eip & 0xFFFFFFFF) == (BP & 0xFFFFFFFF) then
      local ecx = reg('ECX', 'RCX')
      if ecx ~= nil and (ecx & 0xFFFF) == ANCIEN then
        fixer_ecx(NOUVEAU)
        print(string.format('Remplacement : %d -> %d', ANCIEN, NOUVEAU))
      else
        print(string.format('Objet %s ignoré (on attend %d)', tostring(ecx), ANCIEN))
      end
    end
  end)
  if not ok then print('Erreur : ' .. tostring(err)) end
  debug_continueFromBreakpoint(co_run)
  return 1
end

function arreterTest()
  pcall(function() debug_removeBreakpoint(BP) end)
  print('Test arrete.')
end

pcall(debugProcess)
debug_setBreakpoint(BP, 1, bptExecute)
print(string.format('Test actif : objet %d remplace par %d (point d\'arret %X)', ANCIEN, NOUVEAU, BP))
