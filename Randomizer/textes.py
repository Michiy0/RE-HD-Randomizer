"""
Textes de l'application et du générateur, en 7 langues.

Chaque entrée : clé -> (français, anglais, japonais, espagnol, portugais, russe, chinois).
Les textes français sont la référence ; les autres ont été traduits pour le projet et peuvent être
améliorés par des locuteurs natifs (il suffit de modifier la chaîne, en gardant les {variables}).

    from textes import tr, LANGUES
    tr("generer", "en")                       -> "Generate seed"
    tr("dll_installee", "ja", chemin="C:\\…")  -> texte avec la variable remplie
"""

LANGUES = {          # code -> nom affiché dans le sélecteur (dans sa propre langue)
    "fr": "Français",
    "en": "English",
    "ja": "日本語",
    "es": "Español",
    "pt": "Português",
    "ru": "Русский",
    "zh": "中文",
}
ORDRE = tuple(LANGUES)
PAR_DEFAUT = "en"

# Police par langue : Segoe UI n'a pas les idéogrammes, on prend la police système adaptée.
POLICES = {"ja": "Yu Gothic UI", "zh": "Microsoft YaHei UI"}

T = {
    # ------------------------------------------------------------ onglets et cartes
    "onglet_randomizer": ("Randomizer", "Randomizer", "ランダマイザー", "Randomizer", "Randomizer",
                          "Рандомайзер", "随机器"),
    "onglet_spoiler": ("Spoiler", "Spoiler", "ネタバレ", "Spoiler", "Spoiler", "Спойлер", "剧透"),
    "onglet_aide": ("Aider le projet", "Help the project", "プロジェクトに協力", "Ayudar al proyecto",
                    "Ajudar o projeto", "Помочь проекту", "协助项目"),
    "carte_jeu": ("Jeu", "Game", "ゲーム", "Juego", "Jogo", "Игра", "游戏"),
    "carte_partie": ("Partie", "Playthrough", "プレイ設定", "Partida", "Partida", "Прохождение", "游戏设置"),
    "carte_options": ("Options", "Options", "オプション", "Opciones", "Opções", "Параметры", "选项"),
    "carte_spoiler": ("Spoiler", "Spoiler", "ネタバレ", "Spoiler", "Spoiler", "Спойлер", "剧透"),
    "carte_releve": ("Mode relevé", "Survey mode", "調査モード", "Modo registro", "Modo levantamento",
                     "Режим сбора данных", "记录模式"),
    "carte_avancement": ("Avancement des relevés", "Survey progress", "調査の進み具合", "Progreso del registro",
                         "Progresso do levantamento", "Прогресс сбора данных", "记录进度"),
    "langue": ("Langue", "Language", "言語", "Idioma", "Idioma", "Язык", "语言"),
    "langue_auto": ("Automatique", "Automatic", "自動", "Automático", "Automático", "Автоматически", "自动"),

    # ------------------------------------------------------------ carte Jeu
    "parcourir": ("Parcourir…", "Browse…", "参照…", "Examinar…", "Procurar…", "Обзор…", "浏览…"),
    "installer_dll": ("Installer la DLL", "Install the DLL", "DLLをインストール", "Instalar la DLL",
                      "Instalar a DLL", "Установить DLL", "安装 DLL"),
    "maj_dll": ("Mettre à jour la DLL", "Update the DLL", "DLLを更新", "Actualizar la DLL", "Atualizar a DLL",
                "Обновить DLL", "更新 DLL"),
    "desinstaller_dll": ("Désinstaller la DLL", "Uninstall the DLL", "DLLをアンインストール", "Desinstalar la DLL",
                         "Desinstalar a DLL", "Удалить DLL", "卸载 DLL"),
    "supprimer_seed": ("Supprimer la seed installée", "Remove the installed seed", "インストール済みのシードを削除",
                       "Eliminar la seed instalada", "Remover a seed instalada", "Удалить установленный сид",
                       "删除已安装的种子"),
    "note_desinstaller": ("Désinstaller la DLL suffit pour retrouver le jeu d'origine.",
                          "Uninstalling the DLL is enough to get the original game back.",
                          "DLLをアンインストールすれば元のゲームに戻ります。",
                          "Desinstalar la DLL basta para recuperar el juego original.",
                          "Desinstalar a DLL basta para voltar ao jogo original.",
                          "Чтобы вернуть исходную игру, достаточно удалить DLL.",
                          "卸载 DLL 即可恢复原版游戏。"),
    "badge_jeu_introuvable": ("●  Jeu introuvable : indique le dossier qui contient bhd.exe",
                              "●  Game not found: choose the folder that contains bhd.exe",
                              "●  ゲームが見つかりません：bhd.exe があるフォルダーを指定してください",
                              "●  Juego no encontrado: indica la carpeta que contiene bhd.exe",
                              "●  Jogo não encontrado: indique a pasta que contém bhd.exe",
                              "●  Игра не найдена: укажите папку с bhd.exe",
                              "●  未找到游戏：请选择包含 bhd.exe 的文件夹"),
    "badge_autre_dll": ("●  Un autre xinput1_4.dll est présent", "●  Another xinput1_4.dll is present",
                        "●  別の xinput1_4.dll があります", "●  Hay otro xinput1_4.dll",
                        "●  Há outro xinput1_4.dll", "●  Обнаружен другой xinput1_4.dll",
                        "●  存在另一个 xinput1_4.dll"),
    "badge_installe": ("●  Randomizer installé", "●  Randomizer installed", "●  ランダマイザー導入済み",
                       "●  Randomizer instalado", "●  Randomizer instalado", "●  Рандомайзер установлен",
                       "●  随机器已安装"),
    "badge_origine": ("●  Jeu d'origine (DLL non installée)", "●  Original game (DLL not installed)",
                      "●  元のゲーム（DLL未インストール）", "●  Juego original (DLL no instalada)",
                      "●  Jogo original (DLL não instalada)", "●  Исходная игра (DLL не установлена)",
                      "●  原版游戏（未安装 DLL）"),
    "badge_version": ("●  Version de bhd.exe non prise en charge : le randomizer restera inactif (jeu inchangé).",
                      "●  Unsupported bhd.exe version: the randomizer will stay inactive (game unchanged).",
                      "●  未対応の bhd.exe のバージョンです：ランダマイザーは動作しません（ゲームは変更されません）。",
                      "●  Versión de bhd.exe no compatible: el randomizer quedará inactivo (juego sin cambios).",
                      "●  Versão do bhd.exe não suportada: o randomizer ficará inativo (jogo inalterado).",
                      "●  Версия bhd.exe не поддерживается: рандомайзер будет неактивен (игра не изменится).",
                      "●  不支持此 bhd.exe 版本：随机器将保持停用（游戏不变）。"),
    "badge_seed": ("●  Seed {graine}{armes}", "●  Seed {graine}{armes}", "●  シード {graine}{armes}",
                   "●  Seed {graine}{armes}", "●  Seed {graine}{armes}", "●  Сид {graine}{armes}",
                   "●  种子 {graine}{armes}"),
    "badge_armes": (" · armes", " · weapons", " · 武器", " · armas", " · armas", " · оружие", " · 武器"),
    "badge_aucune_seed": ("●  Aucune seed installée", "●  No seed installed", "●  シード未インストール",
                          "●  Ninguna seed instalada", "●  Nenhuma seed instalada", "●  Сид не установлен",
                          "●  未安装种子"),

    "proton_titre": ("Steam Deck / Linux : option de lancement du jeu", "Steam Deck / Linux: game launch option",
                     "Steam Deck / Linux：ゲームの起動オプション", "Steam Deck / Linux: opción de lanzamiento del juego",
                     "Steam Deck / Linux: opção de inicialização do jogo",
                     "Steam Deck / Linux: параметр запуска игры", "Steam Deck / Linux：游戏启动选项"),
    "proton_note": ("Le jeu tourne sous Proton : colle cette option une fois dans Steam (Propriétés du jeu → "
                    "Options de lancement) pour que la DLL soit chargée.",
                    "The game runs under Proton: paste this option once in Steam (game Properties → Launch "
                    "Options) so the DLL is loaded.",
                    "ゲームは Proton で動作します：DLL を読み込ませるため、Steam（ゲームのプロパティ → 起動オプション）に"
                    "この設定を一度貼り付けてください。",
                    "El juego funciona con Proton: pega esta opción una vez en Steam (Propiedades del juego → "
                    "Opciones de lanzamiento) para que se cargue la DLL.",
                    "O jogo roda no Proton: cole esta opção uma vez no Steam (Propriedades do jogo → Opções de "
                    "inicialização) para que a DLL seja carregada.",
                    "Игра работает через Proton: один раз вставьте этот параметр в Steam (Свойства игры → "
                    "Параметры запуска), чтобы DLL загружалась.",
                    "游戏通过 Proton 运行：请将此选项粘贴到 Steam（游戏属性 → 启动选项）中一次，以便加载 DLL。"),
    "proton_dinput8": ("Ajouter dinput8.dll (pour BhdTool ou un autre mod qui l'utilise)",
                       "Also load dinput8.dll (for BhdTool or another mod that uses it)",
                       "dinput8.dll も読み込む（BhdTool など、これを使う MOD 用）",
                       "Cargar también dinput8.dll (para BhdTool u otro mod que lo use)",
                       "Carregar também dinput8.dll (para o BhdTool ou outro mod que o use)",
                       "Также загружать dinput8.dll (для BhdTool или другого мода, который её использует)",
                       "同时加载 dinput8.dll（用于 BhdTool 或其他使用它的模组）"),
    "proton_detecte": ("  · détecté dans le dossier du jeu", "  · found in the game folder", "  ・ゲームフォルダーで検出",
                       "  · detectado en la carpeta del juego", "  · detectado na pasta do jogo",
                       "  · найден в папке игры", "  · 已在游戏文件夹中检测到"),
    "copier": ("Copier", "Copy", "コピー", "Copiar", "Copiar", "Копировать", "复制"),
    "copie_ok": ("Option de lancement copiée : colle-la dans Steam, Propriétés du jeu → Options de lancement.",
                 "Launch option copied: paste it in Steam, game Properties → Launch Options.",
                 "起動オプションをコピーしました：Steam のゲームのプロパティ → 起動オプションに貼り付けてください。",
                 "Opción de lanzamiento copiada: pégala en Steam, Propiedades del juego → Opciones de lanzamiento.",
                 "Opção de inicialização copiada: cole-a no Steam, Propriedades do jogo → Opções de inicialização.",
                 "Параметр запуска скопирован: вставьте его в Steam, Свойства игры → Параметры запуска.",
                 "已复制启动选项：请粘贴到 Steam 的 游戏属性 → 启动选项 中。"),

    # ------------------------------------------------------------ carte Partie
    "personnage": ("Personnage", "Character", "キャラクター", "Personaje", "Personagem", "Персонаж", "角色"),
    "difficulte": ("Difficulté", "Difficulty", "難易度", "Dificultad", "Dificuldade", "Сложность", "难度"),
    "a_venir": ("à venir", "coming soon", "近日対応", "próximamente", "em breve", "скоро", "即将推出"),
    "diff_Très facile": ("Très facile", "Very Easy", "ベリーイージー", "Muy fácil", "Muito fácil", "Очень легко",
                         "非常简单"),
    "diff_Facile": ("Facile", "Easy", "イージー", "Fácil", "Fácil", "Легко", "简单"),
    "diff_Normal": ("Normal", "Normal", "ノーマル", "Normal", "Normal", "Нормально", "普通"),
    "diff_Difficile": ("Difficile", "Hard", "ハード", "Difícil", "Difícil", "Сложно", "困难"),
    "diff_Real Survival": ("Real Survival", "Real Survival", "リアルサバイバル", "Real Survival", "Real Survival",
                           "Real Survival", "Real Survival"),

    # ------------------------------------------------------------ carte Options
    "armes_aleatoires": ("Armes aléatoires", "Random weapons", "武器もランダム", "Armas aleatorias",
                         "Armas aleatórias", "Случайное оружие", "随机武器"),
    "note_armes": ("Le pistolet du hall est mélangé lui aussi.", "The handgun in the main hall is shuffled too.",
                   "ホールのハンドガンもシャッフルされます。", "La pistola del vestíbulo también se mezcla.",
                   "A pistola do saguão também é embaralhada.", "Пистолет из главного зала тоже перемешивается.",
                   "大厅里的手枪也会被打乱。"),
    "cles_aleatoires": ("Clés aléatoires", "Random keys", "鍵もランダム", "Llaves aleatorias", "Chaves aleatórias",
                        "Случайные ключи", "随机钥匙"),
    "graine": ("Graine", "Seed", "シード", "Semilla", "Semente", "Сид", "种子"),
    "au_hasard": ("Au hasard", "Random", "ランダム", "Al azar", "Aleatória", "Случайно", "随机"),
    "note_graine": ("Même graine + mêmes options = même résultat.", "Same seed + same options = same result.",
                    "同じシード＋同じオプション＝同じ結果。", "Misma semilla + mismas opciones = mismo resultado.",
                    "Mesma semente + mesmas opções = mesmo resultado.",
                    "Тот же сид + те же параметры = тот же результат.", "相同种子 + 相同选项 = 相同结果。"),

    # ------------------------------------------------------------ actions et journal
    "generer": ("Générer la seed", "Generate seed", "シードを生成", "Generar la seed", "Gerar a seed",
                "Создать сид", "生成种子"),
    "installer_seed_case": ("Installer la seed dans le jeu", "Install the seed in the game",
                            "シードをゲームにインストール", "Instalar la seed en el juego", "Instalar a seed no jogo",
                            "Установить сид в игру", "将种子安装到游戏"),
    "dossier_seeds": ("Dossier des seeds", "Seeds folder", "シードのフォルダー", "Carpeta de seeds",
                      "Pasta das seeds", "Папка сидов", "种子文件夹"),
    "pret": ("Prêt. Installe la DLL si ce n'est pas fait, choisis tes options puis « Générer la seed ».",
             "Ready. Install the DLL if needed, choose your options, then click “Generate seed”.",
             "準備完了。必要なら DLL をインストールし、オプションを選んで「シードを生成」を押してください。",
             "Listo. Instala la DLL si hace falta, elige tus opciones y pulsa «Generar la seed».",
             "Pronto. Instale a DLL se necessário, escolha as opções e clique em “Gerar a seed”.",
             "Готово. Установите DLL при необходимости, выберите параметры и нажмите «Создать сид».",
             "就绪。如有需要请先安装 DLL，选择选项后点击“生成种子”。"),
    "donnees_absentes": ("Fichier de données {fichier} introuvable : génération impossible.",
                         "Data file {fichier} not found: cannot generate.",
                         "データファイル {fichier} が見つかりません：生成できません。",
                         "No se encuentra el archivo de datos {fichier}: no se puede generar.",
                         "Arquivo de dados {fichier} não encontrado: impossível gerar.",
                         "Файл данных {fichier} не найден: создание невозможно.",
                         "找不到数据文件 {fichier}：无法生成。"),
    "generation": ("Génération…", "Generating…", "生成中…", "Generando…", "Gerando…", "Создание…", "生成中…"),
    "erreur": ("ERREUR : {e}", "ERROR: {e}", "エラー：{e}", "ERROR: {e}", "ERRO: {e}", "ОШИБКА: {e}", "错误：{e}"),
    "echec_generation": ("La génération ou l'installation a échoué.", "Generation or installation failed.",
                         "生成またはインストールに失敗しました。", "La generación o la instalación ha fallado.",
                         "A geração ou a instalação falhou.", "Не удалось создать или установить сид.",
                         "生成或安装失败。"),
    "renvoi_spoiler": ("(liste complète des changements : onglet « Spoiler »)",
                       "(full list of changes: “Spoiler” tab)", "（変更の全一覧：「ネタバレ」タブ）",
                       "(lista completa de cambios: pestaña «Spoiler»)",
                       "(lista completa das mudanças: aba “Spoiler”)",
                       "(полный список изменений: вкладка «Спойлер»)", "（完整更改列表：“剧透”标签页）"),

    # ------------------------------------------------------------ onglet Spoiler
    "afficher_spoiler": ("Afficher le spoiler", "Show spoiler", "ネタバレを表示", "Mostrar el spoiler",
                         "Mostrar o spoiler", "Показать спойлер", "显示剧透"),
    "spoiler_aucun": ("Aucune seed générée ou installée pour l'instant.", "No seed generated or installed yet.",
                      "まだシードが生成・インストールされていません。", "Todavía no hay ninguna seed generada o instalada.",
                      "Nenhuma seed gerada ou instalada ainda.", "Пока нет созданного или установленного сида.",
                      "尚未生成或安装种子。"),
    "spoiler_genere": ("Dernière seed générée", "Last generated seed", "最後に生成したシード",
                       "Última seed generada", "Última seed gerada", "Последний созданный сид", "最近生成的种子"),
    "spoiler_installe": ("Seed installée dans le jeu", "Seed installed in the game", "ゲームにインストール済みのシード",
                         "Seed instalada en el juego", "Seed instalada no jogo", "Сид, установленный в игру",
                         "已安装到游戏的种子"),
    "spoiler_masque": ("{titre} : spoiler masqué. Coche la case pour voir quel objet remplace quoi.",
                       "{titre}: spoiler hidden. Tick the box to see which item replaces which.",
                       "{titre}：ネタバレは非表示です。チェックを入れるとどのアイテムが何に置き換わったか表示されます。",
                       "{titre}: spoiler oculto. Marca la casilla para ver qué objeto sustituye a cuál.",
                       "{titre}: spoiler oculto. Marque a caixa para ver qual item substitui qual.",
                       "{titre}: спойлер скрыт. Отметьте флажок, чтобы увидеть, какой предмет чем заменён.",
                       "{titre}：剧透已隐藏。勾选即可查看哪件物品替换了哪件。"),

    # ------------------------------------------------------------ onglet Aider le projet
    "releve_intro": ("Le randomizer ne mélange que les objets déjà relevés. Tu peux aider à compléter la liste en "
                     "jouant : la DLL note les objets de chaque pièce visitée, sans rien changer à ta partie.",
                     "The randomizer only shuffles items that have already been surveyed. You can help complete "
                     "the list by playing: the DLL records the items of every room you visit, without changing "
                     "your game.",
                     "ランダマイザーは調査済みのアイテムだけをシャッフルします。プレイするだけでリスト作りに協力できます："
                     "DLL が訪れた部屋のアイテムを記録します（ゲームには何も影響しません）。",
                     "El randomizer solo mezcla objetos ya registrados. Puedes ayudar a completar la lista "
                     "jugando: la DLL anota los objetos de cada sala que visitas, sin cambiar nada de tu partida.",
                     "O randomizer só embaralha itens já levantados. Você pode ajudar a completar a lista "
                     "jogando: a DLL anota os itens de cada sala visitada, sem alterar nada na sua partida.",
                     "Рандомайзер перемешивает только уже собранные предметы. Вы можете помочь дополнить список, "
                     "просто играя: DLL записывает предметы каждой посещённой комнаты, не меняя вашу игру.",
                     "随机器只会打乱已记录的物品。你可以边玩边帮忙完善列表：DLL 会记录你进入的每个房间里的物品，"
                     "不会改变你的游戏。"),
    "releve_case": ("Activer le mode relevé (au prochain lancement du jeu)",
                    "Enable survey mode (next time the game starts)", "調査モードを有効にする（次回のゲーム起動時）",
                    "Activar el modo registro (en el próximo inicio del juego)",
                    "Ativar o modo levantamento (no próximo início do jogo)",
                    "Включить режим сбора (при следующем запуске игры)", "启用记录模式（下次启动游戏时生效）"),
    "etape1": ("1.  Installe la DLL (onglet Randomizer) et coche la case ci-dessus.",
               "1.  Install the DLL (Randomizer tab) and tick the box above.",
               "1.  DLL をインストールし（ランダマイザータブ）、上のボックスにチェックを入れます。",
               "1.  Instala la DLL (pestaña Randomizer) y marca la casilla de arriba.",
               "1.  Instale a DLL (aba Randomizer) e marque a caixa acima.",
               "1.  Установите DLL (вкладка «Рандомайзер») и отметьте флажок выше.",
               "1.  安装 DLL（随机器标签页）并勾选上方的复选框。"),
    "etape2": ("2.  Lance une NOUVELLE partie : les objets déjà ramassés n'existent plus en mémoire.",
               "2.  Start a NEW game: items already picked up no longer exist in memory.",
               "2.  ニューゲームで始めます：拾ったアイテムはメモリから消えています。",
               "2.  Empieza una partida NUEVA: los objetos ya recogidos ya no existen en memoria.",
               "2.  Comece um jogo NOVO: itens já pegos não existem mais na memória.",
               "2.  Начните НОВУЮ игру: подобранные предметы исчезают из памяти.",
               "2.  开始新游戏：已拾取的物品不再存在于内存中。"),
    "etape3": ("3.  Visite les pièces sans rien ramasser ; reste environ 2 secondes dans chacune.",
               "3.  Visit rooms without picking anything up; stay about 2 seconds in each.",
               "3.  何も拾わずに部屋を回り、各部屋に約2秒とどまります。",
               "3.  Visita las salas sin recoger nada; quédate unos 2 segundos en cada una.",
               "3.  Visite as salas sem pegar nada; fique cerca de 2 segundos em cada uma.",
               "3.  Обходите комнаты, ничего не подбирая; задерживайтесь в каждой примерно на 2 секунды.",
               "3.  进入各个房间但不要拾取任何物品；在每个房间停留约 2 秒。"),
    "etape4": ("4.  Envoie le journal du jeu (bouton ci-dessous) en précisant le personnage et la difficulté.",
               "4.  Send the game log (button below), stating the character and difficulty.",
               "4.  ゲームのログ（下のボタン）を、キャラクターと難易度を添えて送ってください。",
               "4.  Envía el registro del juego (botón de abajo) indicando el personaje y la dificultad.",
               "4.  Envie o registro do jogo (botão abaixo) informando o personagem e a dificuldade.",
               "4.  Отправьте журнал игры (кнопка ниже), указав персонажа и сложность.",
               "4.  发送游戏日志（下方按钮），并注明角色和难度。"),
    "releve_saccade": ("Petite saccade (~0,3 s) en entrant dans une pièce : décoche la case pour jouer normalement.",
                       "Small stutter (~0.3 s) when entering a room: untick the box to play normally.",
                       "部屋に入るときに少しカクつきます（約0.3秒）：普通に遊ぶときはチェックを外してください。",
                       "Pequeño tirón (~0,3 s) al entrar en una sala: desmarca la casilla para jugar con normalidad.",
                       "Pequeno travamento (~0,3 s) ao entrar numa sala: desmarque a caixa para jogar normalmente.",
                       "Небольшое подтормаживание (~0,3 с) при входе в комнату: снимите флажок для обычной игры.",
                       "进入房间时会有轻微卡顿（约 0.3 秒）：正常游玩时请取消勾选。"),
    "journal_du_jeu": ("Journal du jeu", "Game log", "ゲームのログ", "Registro del juego", "Registro do jogo",
                       "Журнал игры", "游戏日志"),
    "signaler_github": ("Signaler / envoyer sur GitHub", "Report / send on GitHub", "GitHub で報告・送信",
                        "Informar / enviar en GitHub", "Reportar / enviar no GitHub", "Сообщить / отправить на GitHub",
                        "在 GitHub 上反馈/发送"),
    "visitees": (" · +{n} visitées", " · +{n} visited", " · +{n} 訪問済み", " · +{n} visitadas", " · +{n} visitadas",
                 " · +{n} посещено", " · +{n} 已访问"),
    "armes_bonus": ("Armes bonus", "Bonus weapons", "ボーナス武器", "Armas extra", "Armas bônus", "Бонусное оружие",
                    "奖励武器"),
    "bonus_identifiees": ("{a}/{b} identifiées", "{a}/{b} identified", "{a}/{b} 判明", "{a}/{b} identificadas",
                          "{a}/{b} identificadas", "{a}/{b} определено", "已识别 {a}/{b}"),
    "liste_a_completer": ("liste à compléter", "list to be completed", "リスト作成中", "lista por completar",
                          "lista a completar", "список пополняется", "列表待完善"),
    "note_avancement": ("Pièces relevées en nouvelle partie, sur {total}. Rouge : complètes · rouge pâle : visitées "
                        "en partie commencée. Données de la version {version} : tes relevés apparaîtront à la "
                        "version suivante.",
                        "Rooms surveyed in a new game, out of {total}. Red: complete · pale red: visited in a game "
                        "already in progress. Data from version {version}: your surveys will appear in the next "
                        "version.",
                        "ニューゲームで調査済みの部屋（全{total}室中）。赤：完了・薄い赤：プレイ途中のデータで訪問済み。"
                        "バージョン{version}のデータです。あなたの調査結果は次のバージョンに反映されます。",
                        "Salas registradas en partida nueva, de {total}. Rojo: completas · rojo claro: visitadas en "
                        "una partida ya empezada. Datos de la versión {version}: tus registros aparecerán en la "
                        "siguiente versión.",
                        "Salas levantadas em jogo novo, de {total}. Vermelho: completas · vermelho claro: visitadas "
                        "num jogo já começado. Dados da versão {version}: seus levantamentos aparecerão na próxima "
                        "versão.",
                        "Комнаты, собранные в новой игре, из {total}. Красный: полностью · бледно-красный: посещены "
                        "в уже начатой игре. Данные версии {version}: ваши данные появятся в следующей версии.",
                        "在新游戏中记录的房间（共 {total} 个）。红色：已完成 · 浅红色：在进行中的存档里访问过。"
                        "数据来自 {version} 版：你的记录会出现在下一版本中。"),
    "avancement_indispo": ("Avancement indisponible : {e}", "Progress unavailable: {e}", "進み具合を表示できません：{e}",
                           "Progreso no disponible: {e}", "Progresso indisponível: {e}", "Прогресс недоступен: {e}",
                           "无法显示进度：{e}"),

    # ------------------------------------------------------------ messages et boîtes de dialogue
    "choisir_dossier": ("Dossier du jeu (celui qui contient bhd.exe)", "Game folder (the one containing bhd.exe)",
                        "ゲームフォルダー（bhd.exe があるフォルダー）", "Carpeta del juego (la que contiene bhd.exe)",
                        "Pasta do jogo (a que contém bhd.exe)", "Папка игры (с файлом bhd.exe)",
                        "游戏文件夹（包含 bhd.exe 的文件夹）"),
    "err_ini": ("Impossible de modifier randomizer.ini :\n{e}", "Cannot modify randomizer.ini:\n{e}",
                "randomizer.ini を変更できません：\n{e}", "No se puede modificar randomizer.ini:\n{e}",
                "Não foi possível modificar randomizer.ini:\n{e}", "Не удалось изменить randomizer.ini:\n{e}",
                "无法修改 randomizer.ini：\n{e}"),
    "releve_active": ("Mode relevé activé (au prochain lancement du jeu). À chaque nouvelle pièce, les objets présents "
                      "sont notés dans le journal du jeu (lignes « Releve auto »).",
                      "Survey mode enabled (next time the game starts). In each new room, the items present are "
                      "written to the game log (“Releve auto” lines).",
                      "調査モードを有効にしました（次回のゲーム起動時から）。新しい部屋に入るたびに、そこにあるアイテムが"
                      "ゲームのログ（「Releve auto」行）に記録されます。",
                      "Modo registro activado (en el próximo inicio del juego). En cada sala nueva, los objetos "
                      "presentes se anotan en el registro del juego (líneas «Releve auto»).",
                      "Modo levantamento ativado (no próximo início do jogo). Em cada sala nova, os itens presentes "
                      "são anotados no registro do jogo (linhas “Releve auto”).",
                      "Режим сбора включён (со следующего запуска игры). В каждой новой комнате предметы "
                      "записываются в журнал игры (строки «Releve auto»).",
                      "已启用记录模式（下次启动游戏时生效）。每进入一个新房间，其中的物品都会写入游戏日志"
                      "（“Releve auto”行）。"),
    "releve_dll_absente": ("\nAttention : la DLL n'est pas installée, clique « Installer la DLL ».",
                           "\nWarning: the DLL is not installed, click “Install the DLL”.",
                           "\n注意：DLL がインストールされていません。「DLLをインストール」を押してください。",
                           "\nAtención: la DLL no está instalada, pulsa «Instalar la DLL».",
                           "\nAtenção: a DLL não está instalada, clique em “Instalar a DLL”.",
                           "\nВнимание: DLL не установлена, нажмите «Установить DLL».",
                           "\n注意：DLL 未安装，请点击“安装 DLL”。"),
    "releve_desactive": ("Mode relevé désactivé (au prochain lancement du jeu).",
                         "Survey mode disabled (next time the game starts).", "調査モードを無効にしました（次回のゲーム起動時から）。",
                         "Modo registro desactivado (en el próximo inicio del juego).",
                         "Modo levantamento desativado (no próximo início do jogo).",
                         "Режим сбора отключён (со следующего запуска игры).", "已停用记录模式（下次启动游戏时生效）。"),
    "dll_supprimee": ("DLL du randomizer supprimée : {chemin}", "Randomizer DLL removed: {chemin}",
                      "ランダマイザーの DLL を削除しました：{chemin}", "DLL del randomizer eliminada: {chemin}",
                      "DLL do randomizer removida: {chemin}", "DLL рандомайзера удалена: {chemin}",
                      "已删除随机器 DLL：{chemin}"),
    "seed_supprimee": ("Seed installée supprimée : {chemin}", "Installed seed removed: {chemin}",
                       "インストール済みのシードを削除しました：{chemin}", "Seed instalada eliminada: {chemin}",
                       "Seed instalada removida: {chemin}", "Установленный сид удалён: {chemin}",
                       "已删除已安装的种子：{chemin}"),
    "err_supprimer": ("Impossible de supprimer {nom} :\n{e}\n\nLe jeu est-il encore lancé ? Ferme-le puis réessaie.",
                      "Cannot delete {nom}:\n{e}\n\nIs the game still running? Close it and try again.",
                      "{nom} を削除できません：\n{e}\n\nゲームが起動したままではありませんか？終了してからもう一度お試しください。",
                      "No se puede eliminar {nom}:\n{e}\n\n¿Sigue abierto el juego? Ciérralo y vuelve a intentarlo.",
                      "Não foi possível excluir {nom}:\n{e}\n\nO jogo ainda está aberto? Feche-o e tente de novo.",
                      "Не удалось удалить {nom}:\n{e}\n\nИгра всё ещё запущена? Закройте её и повторите.",
                      "无法删除 {nom}：\n{e}\n\n游戏是否仍在运行？请关闭后重试。"),
    "pas_notre_dll": ("Ce xinput1_4.dll n'est pas celui du randomizer : il n'est pas supprimé.",
                      "This xinput1_4.dll is not the randomizer's: it was not deleted.",
                      "この xinput1_4.dll はランダマイザーのものではないため、削除しません。",
                      "Este xinput1_4.dll no es el del randomizer: no se ha eliminado.",
                      "Este xinput1_4.dll não é o do randomizer: ele não foi excluído.",
                      "Этот xinput1_4.dll не принадлежит рандомайзеру: он не удалён.",
                      "此 xinput1_4.dll 不是随机器的文件，不会删除。"),
    "confirmer_desinstaller": ("Désinstaller la DLL du randomizer ?\n\nLe jeu redeviendra le jeu d'origine au "
                               "prochain lancement. La seed installée est conservée (elle ne sert plus à rien sans "
                               "la DLL).",
                               "Uninstall the randomizer DLL?\n\nThe game will be the original game again next "
                               "time it starts. The installed seed is kept (it does nothing without the DLL).",
                               "ランダマイザーの DLL をアンインストールしますか？\n\n次回の起動から元のゲームに戻ります。"
                               "インストール済みのシードは残ります（DLL がなければ何もしません）。",
                               "¿Desinstalar la DLL del randomizer?\n\nEl juego volverá a ser el original en el "
                               "próximo inicio. La seed instalada se conserva (sin la DLL no hace nada).",
                               "Desinstalar a DLL do randomizer?\n\nO jogo voltará a ser o original no próximo "
                               "início. A seed instalada é mantida (sem a DLL ela não faz nada).",
                               "Удалить DLL рандомайзера?\n\nПри следующем запуске игра снова станет исходной. "
                               "Установленный сид сохранится (без DLL он ни на что не влияет).",
                               "卸载随机器 DLL？\n\n下次启动时游戏将恢复为原版。已安装的种子会保留（没有 DLL 时不起作用）。"),
    "sans_randomizer": ("Le jeu se lancera sans randomizer. Pour le remettre : « Installer la DLL ».",
                        "The game will start without the randomizer. To bring it back: “Install the DLL”.",
                        "ゲームはランダマイザーなしで起動します。元に戻すには「DLLをインストール」を押してください。",
                        "El juego se iniciará sin randomizer. Para volver a ponerlo: «Instalar la DLL».",
                        "O jogo vai iniciar sem o randomizer. Para recolocá-lo: “Instalar a DLL”.",
                        "Игра запустится без рандомайзера. Чтобы вернуть его: «Установить DLL».",
                        "游戏将在没有随机器的情况下启动。要恢复：点击“安装 DLL”。"),
    "confirmer_supprimer_seed": ("Supprimer la seed installée ({graine}{armes}) ?\n\nSes fichiers restent dans le "
                                 "dossier des seeds. Sans seed, la DLL laisse le jeu tel quel.",
                                 "Remove the installed seed ({graine}{armes})?\n\nIts files stay in the seeds "
                                 "folder. Without a seed, the DLL leaves the game as it is.",
                                 "インストール済みのシード（{graine}{armes}）を削除しますか？\n\nファイルはシードのフォルダーに"
                                 "残ります。シードがなければ DLL はゲームを変更しません。",
                                 "¿Eliminar la seed instalada ({graine}{armes})?\n\nSus archivos se quedan en la "
                                 "carpeta de seeds. Sin seed, la DLL deja el juego tal cual.",
                                 "Remover a seed instalada ({graine}{armes})?\n\nOs arquivos dela continuam na "
                                 "pasta das seeds. Sem seed, a DLL deixa o jogo como está.",
                                 "Удалить установленный сид ({graine}{armes})?\n\nЕго файлы останутся в папке "
                                 "сидов. Без сида DLL не меняет игру.",
                                 "删除已安装的种子（{graine}{armes}）？\n\n其文件仍保留在种子文件夹中。没有种子时，DLL 不会改变游戏。"),
    "avec_armes": (" avec armes", " with weapons", "・武器あり", " con armas", " com armas", " с оружием", "，含武器"),
    "version_confirmer": ("Ta version de bhd.exe n'est pas celle prise en charge.\n\nLa DLL restera inactive (le jeu "
                          "ne sera pas modifié). L'installer quand même ?",
                          "Your bhd.exe version is not the supported one.\n\nThe DLL will stay inactive (the game "
                          "will not be modified). Install it anyway?",
                          "お使いの bhd.exe は対応バージョンではありません。\n\nDLL は動作しません（ゲームは変更されません）。"
                          "それでもインストールしますか？",
                          "Tu versión de bhd.exe no es la compatible.\n\nLa DLL quedará inactiva (el juego no se "
                          "modificará). ¿Instalarla de todos modos?",
                          "Sua versão do bhd.exe não é a suportada.\n\nA DLL ficará inativa (o jogo não será "
                          "modificado). Instalar mesmo assim?",
                          "Ваша версия bhd.exe не поддерживается.\n\nDLL будет неактивна (игра не изменится). "
                          "Всё равно установить?",
                          "你的 bhd.exe 版本不受支持。\n\nDLL 将保持停用（游戏不会被修改）。仍要安装吗？"),
    "dll_installee": ("DLL installée : {chemin}\nPour désinstaller : supprimer ce fichier.",
                      "DLL installed: {chemin}\nTo uninstall: delete this file.",
                      "DLL をインストールしました：{chemin}\nアンインストールするにはこのファイルを削除します。",
                      "DLL instalada: {chemin}\nPara desinstalar: elimina este archivo.",
                      "DLL instalada: {chemin}\nPara desinstalar: exclua este arquivo.",
                      "DLL установлена: {chemin}\nЧтобы удалить: удалите этот файл.",
                      "已安装 DLL：{chemin}\n卸载方法：删除此文件。"),
    "err_copier_dll": ("Impossible de copier la DLL :\n{e}\n\nLe jeu est-il encore lancé ?",
                       "Cannot copy the DLL:\n{e}\n\nIs the game still running?",
                       "DLL をコピーできません：\n{e}\n\nゲームが起動したままではありませんか？",
                       "No se puede copiar la DLL:\n{e}\n\n¿Sigue abierto el juego?",
                       "Não foi possível copiar a DLL:\n{e}\n\nO jogo ainda está aberto?",
                       "Не удалось скопировать DLL:\n{e}\n\nИгра всё ещё запущена?",
                       "无法复制 DLL：\n{e}\n\n游戏是否仍在运行？"),
    "pas_de_journal": ("Pas encore de journal : il se crée au premier lancement du jeu avec la DLL installée.",
                       "No log yet: it is created the first time the game starts with the DLL installed.",
                       "まだログがありません：DLL をインストールしてゲームを初めて起動したときに作成されます。",
                       "Todavía no hay registro: se crea la primera vez que el juego se inicia con la DLL instalada.",
                       "Ainda não há registro: ele é criado na primeira vez que o jogo inicia com a DLL instalada.",
                       "Журнала пока нет: он создаётся при первом запуске игры с установленной DLL.",
                       "还没有日志：安装 DLL 后首次启动游戏时会创建。"),
    "graine_invalide": ("La graine doit être un nombre entier positif.", "The seed must be a positive whole number.",
                        "シードは正の整数で入力してください。", "La semilla debe ser un número entero positivo.",
                        "A semente deve ser um número inteiro positivo.", "Сид должен быть целым положительным числом.",
                        "种子必须是正整数。"),
    "dossier_introuvable": ("Dossier du jeu introuvable : choisis-le, ou décoche l'installation.",
                            "Game folder not found: choose it, or untick the installation.",
                            "ゲームフォルダーが見つかりません：フォルダーを選ぶか、インストールのチェックを外してください。",
                            "No se encuentra la carpeta del juego: elígela o desmarca la instalación.",
                            "Pasta do jogo não encontrada: escolha-a ou desmarque a instalação.",
                            "Папка игры не найдена: выберите её или снимите флажок установки.",
                            "未找到游戏文件夹：请选择文件夹，或取消勾选安装。"),

    # ------------------------------------------------------------ générateur (résumé, spoiler, installation)
    "gen_resume": ("Graine {graine} — armes aléatoires : {armes}", "Seed {graine} — random weapons: {armes}",
                   "シード {graine} — 武器ランダム：{armes}", "Semilla {graine} — armas aleatorias: {armes}",
                   "Semente {graine} — armas aleatórias: {armes}", "Сид {graine} — случайное оружие: {armes}",
                   "种子 {graine} — 随机武器：{armes}"),
    "gen_oui": ("OUI", "YES", "あり", "SÍ", "SIM", "ДА", "是"),
    "gen_non": ("non", "no", "なし", "no", "não", "нет", "否"),
    "gen_compte": ("{n} objets mélangés, {m} laissés à leur place (clés et objets spéciaux{pistolet}).",
                   "{n} items shuffled, {m} left in place (keys and special items{pistolet}).",
                   "{n}個のアイテムをシャッフル、{m}個はそのまま（鍵・特殊アイテム{pistolet}）。",
                   "{n} objetos mezclados, {m} dejados en su sitio (llaves y objetos especiales{pistolet}).",
                   "{n} itens embaralhados, {m} deixados no lugar (chaves e itens especiais{pistolet}).",
                   "Перемешано предметов: {n}, оставлено на месте: {m} (ключи и особые предметы{pistolet}).",
                   "已打乱 {n} 件物品，{m} 件保持原位（钥匙和特殊物品{pistolet}）。"),
    "gen_pistolet": (", pistolet", ", handgun", "・ハンドガン", ", pistola", ", pistola", ", пистолет", "、手枪"),
    "gen_non_utilises": ("Emplacements non utilisés (valeurs fixes incomplètes) :",
                         "Unused locations (incomplete fixed values):", "未使用の配置（固定値が不完全）：",
                         "Ubicaciones no usadas (valores fijos incompletos):",
                         "Locais não usados (valores fixos incompletos):",
                         "Неиспользованные места (неполные постоянные значения):", "未使用的位置（固定值不完整）："),
    "gen_fichiers": ("\nFichiers écrits dans {dossier} : {a}, {b} et {c}\n",
                     "\nFiles written to {dossier}: {a}, {b} and {c}\n", "\n{dossier} に書き出したファイル：{a}、{b}、{c}\n",
                     "\nArchivos escritos en {dossier}: {a}, {b} y {c}\n",
                     "\nArquivos gravados em {dossier}: {a}, {b} e {c}\n",
                     "\nФайлы записаны в {dossier}: {a}, {b} и {c}\n", "\n已写入 {dossier}：{a}、{b} 和 {c}\n"),
    "gen_donnees": ("Fichier de données introuvable : {fichier}", "Data file not found: {fichier}",
                    "データファイルが見つかりません：{fichier}", "No se encuentra el archivo de datos: {fichier}",
                    "Arquivo de dados não encontrado: {fichier}", "Файл данных не найден: {fichier}",
                    "找不到数据文件：{fichier}"),
    "gen_aucun": ("Aucun emplacement relevé pour {personnage} / {difficulte} : rien à mélanger.",
                  "No surveyed locations for {personnage} / {difficulte}: nothing to shuffle.",
                  "{personnage} / {difficulte} の調査済みの配置がありません：シャッフルするものがありません。",
                  "No hay ubicaciones registradas para {personnage} / {difficulte}: nada que mezclar.",
                  "Nenhum local levantado para {personnage} / {difficulte}: nada para embaralhar.",
                  "Нет собранных мест для {personnage} / {difficulte}: перемешивать нечего.",
                  "{personnage} / {difficulte} 没有已记录的位置：没有可打乱的物品。"),
    "gen_install_impossible": ("INSTALLATION IMPOSSIBLE : dossier du jeu introuvable (bhd.exe absent). "
                               "Indique-le avec --dossier-jeu.",
                               "CANNOT INSTALL: game folder not found (no bhd.exe).",
                               "インストールできません：ゲームフォルダーが見つかりません（bhd.exe がありません）。",
                               "NO SE PUEDE INSTALAR: no se encuentra la carpeta del juego (falta bhd.exe).",
                               "IMPOSSÍVEL INSTALAR: pasta do jogo não encontrada (bhd.exe ausente).",
                               "УСТАНОВКА НЕВОЗМОЖНА: папка игры не найдена (нет bhd.exe).",
                               "无法安装：未找到游戏文件夹（缺少 bhd.exe）。"),
    "gen_installee": ("Seed {graine}{armes} installée : {chemin}", "Seed {graine}{armes} installed: {chemin}",
                      "シード {graine}{armes} をインストールしました：{chemin}", "Seed {graine}{armes} instalada: {chemin}",
                      "Seed {graine}{armes} instalada: {chemin}", "Сид {graine}{armes} установлен: {chemin}",
                      "已安装种子 {graine}{armes}：{chemin}"),
    "gen_armes": (" (armes)", " (weapons)", "（武器あり）", " (armas)", " (armas)", " (оружие)", "（含武器）"),
    "gen_remplace": ("  (remplace la seed {ancienne})", "  (replaces seed {ancienne})", "  （シード {ancienne} を置き換え）",
                     "  (sustituye a la seed {ancienne})", "  (substitui a seed {ancienne})",
                     "  (заменяет сид {ancienne})", "  （替换种子 {ancienne}）"),
    "gen_ini_autre": ("ATTENTION : randomizer.ini demande la seed « {seed} », pas {nom}.",
                      "WARNING: randomizer.ini asks for seed “{seed}”, not {nom}.",
                      "注意：randomizer.ini は {nom} ではなくシード「{seed}」を指定しています。",
                      "ATENCIÓN: randomizer.ini pide la seed «{seed}», no {nom}.",
                      "ATENÇÃO: randomizer.ini pede a seed “{seed}”, não {nom}.",
                      "ВНИМАНИЕ: randomizer.ini указывает сид «{seed}», а не {nom}.",
                      "注意：randomizer.ini 指定的种子是“{seed}”，而不是 {nom}。"),
    "gen_ini_inactif": ("ATTENTION : randomizer.ini contient Actif=0, le randomizer est désactivé.",
                        "WARNING: randomizer.ini contains Actif=0, the randomizer is disabled.",
                        "注意：randomizer.ini に Actif=0 があるため、ランダマイザーは無効です。",
                        "ATENCIÓN: randomizer.ini contiene Actif=0, el randomizer está desactivado.",
                        "ATENÇÃO: randomizer.ini contém Actif=0, o randomizer está desativado.",
                        "ВНИМАНИЕ: в randomizer.ini указано Actif=0, рандомайзер отключён.",
                        "注意：randomizer.ini 中有 Actif=0，随机器已停用。"),
    "gen_dll_absente": ("ATTENTION : xinput1_4.dll absent du dossier du jeu, la seed ne sera pas appliquée "
                        "(copie DLL\\xinput1_4.dll).",
                        "WARNING: xinput1_4.dll is missing from the game folder, the seed will not be applied "
                        "(install the DLL).",
                        "注意：ゲームフォルダーに xinput1_4.dll がないため、シードは適用されません（DLL をインストールしてください）。",
                        "ATENCIÓN: falta xinput1_4.dll en la carpeta del juego, la seed no se aplicará "
                        "(instala la DLL).",
                        "ATENÇÃO: xinput1_4.dll não está na pasta do jogo, a seed não será aplicada "
                        "(instale a DLL).",
                        "ВНИМАНИЕ: в папке игры нет xinput1_4.dll, сид не будет применён (установите DLL).",
                        "注意：游戏文件夹中缺少 xinput1_4.dll，种子不会生效（请安装 DLL）。"),
    "gen_relance": ("Relance le jeu pour que la nouvelle seed soit prise en compte.",
                    "Restart the game for the new seed to take effect.", "新しいシードを反映するにはゲームを再起動してください。",
                    "Reinicia el juego para que se aplique la nueva seed.",
                    "Reinicie o jogo para que a nova seed seja aplicada.",
                    "Перезапустите игру, чтобы новый сид вступил в силу.", "重新启动游戏以使新种子生效。"),

    # ------------------------------------------------------------ noms des objets mélangés (spoiler)
    "objet_3": ("Pistolet", "Handgun", "ハンドガン", "Pistola", "Pistola", "Пистолет", "手枪"),
    "objet_17": ("Chargeur de pistolet", "Handgun Bullets", "ハンドガンの弾", "Balas de pistola", "Balas de pistola",
                 "Патроны для пистолета", "手枪子弹"),
    "objet_34": ("Herbe verte", "Green Herb", "グリーンハーブ", "Hierba verde", "Erva verde", "Зелёная трава",
                 "绿色草药"),
    "objet_68": ("Ruban encreur", "Ink Ribbon", "インクリボン", "Cinta de tinta", "Fita de tinta", "Красящая лента",
                 "色带"),
    "objet_101": ("Trousse de premiers secours", "First Aid Box", "救急箱", "Botiquín", "Kit de primeiros socorros",
                  "Аптечка", "急救箱"),
    "objet_112": ("Poignard", "Dagger", "ダガー", "Daga", "Adaga", "Кинжал", "匕首"),
}


def tr(cle, langue="fr", **valeurs):
    """Texte de la clé dans la langue demandée (français si la langue ou la clé manque)."""
    textes = T.get(cle)
    if textes is None:
        return cle
    i = ORDRE.index(langue) if langue in ORDRE else 0
    texte = textes[i] or textes[0]
    return texte.format(**valeurs) if valeurs else texte


def langue_systeme():
    """Langue du système (Windows ou Linux) si elle est disponible, sinon l'anglais."""
    import sys
    if sys.platform != "win32":
        import os
        for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
            valeur = os.environ.get(variable, "")
            if valeur and valeur not in ("C", "POSIX"):
                code = valeur.split(":")[0][:2].lower()
                return code if code in LANGUES else PAR_DEFAUT
        return PAR_DEFAUT
    try:
        import ctypes
        primaire = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
        return {0x0C: "fr", 0x09: "en", 0x11: "ja", 0x0A: "es", 0x16: "pt", 0x19: "ru", 0x04: "zh"}.get(
            primaire, PAR_DEFAUT)
    except Exception:
        return PAR_DEFAUT


def verifier():
    """Contrôle : chaque clé a ses 7 traductions et les mêmes {variables} dans chaque langue."""
    import string
    problemes = []
    for cle, textes in T.items():
        if len(textes) != len(ORDRE):
            problemes.append(f"{cle} : {len(textes)} traductions au lieu de {len(ORDRE)}")
            continue
        ref = {v for _, v, _, _ in string.Formatter().parse(textes[0]) if v}
        for code, texte in zip(ORDRE, textes):
            noms = {v for _, v, _, _ in string.Formatter().parse(texte) if v}
            if noms != ref:
                problemes.append(f"{cle} [{code}] : variables {sorted(noms)} au lieu de {sorted(ref)}")
    return problemes


if __name__ == "__main__":
    p = verifier()
    print("\n".join(p) if p else f"OK : {len(T)} textes × {len(ORDRE)} langues")
