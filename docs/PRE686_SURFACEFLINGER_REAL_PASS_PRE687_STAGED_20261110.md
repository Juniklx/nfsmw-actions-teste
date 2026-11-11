# PRE686 — SurfaceView frame pacing verificado; PRE687 preparada

Data: 2026-11-10 (Bahia, Brasil).

## PRE686 observada

- Medição no Samsung Galaxy S24 FE 22:46:06–22:51:52, `SurfaceFlinger --timestats` e log de jogo correspondente.
- Auditoria automática em GitHub Actions **run 42943062931**, job **130269212470**, **completed/success**.
- Os dois arquivos de origem foram guardados exclusivamente na pasta **privada** `NFSMW_Android/06_Logs_e_Medicoes` do Google Drive, IDs `1TF6_N3Vt1resirvtlvx5ei2dpFXY7im3` (SurfaceFlinger) e `1BTs-Xf680UGlnVpRPC6nwT4RG7Yq_OAR` (nfsmw.log).
- PINs: SHA256 do SurfaceFlinger `50f94cfe3b91c19f36312b6d00054fa292fb43050d0529745c40dc0ebe2421e8`; SHA256 log `2bf6a248629d124904049faa4aa55f4e230639d620a2a752509898c857b26ef4`.
- Camada real: `SurfaceView[io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity]`, **19672** quadros e `averageFPS=61.918`. Os vários layers VRI/Splash Screen não representam o FPS do jogo.
- Histograma atribuído a `present2present` pela correspondência ÚNICA da sua média ponderada ao `averageFPS`: 8ms=1943, 16ms=15698, 24ms=770, 25ms=999 e 33ms=52. O coletor anterior descartou **literalmente os nomes** dos histogramas; a atribuição é inferida, não leitura direta do rótulo. Os grupos 8ms e 24–25ms somados são 3712/19672 (18,869%).
- O log motor da mesma sessão confirmou 1920×1080, cap 60 e Vulkan MAILBOX; após a cinemática (22:47:22) FPS estimado por `presentados` permaneceu ~60, com tempo GPU de 9,24 a 10,52 ms/Swap entre os blocos observados.
- O conjunto SurfaceFlinger inclui menus/carregamento/cinemática. A distribuição global **não prova alternância entre intervalos**, nem que irregularidades ocorreram na fase estável com carro parado. O padrão quantizado 8/16/24ms é compatível com refresh 120Hz como hipótese, mas a taxa de atualização real não foi coletada.
- ZIP relatório local e JSON privado: Drive ID `16rEKreccpsaTV5qlrFyrZiNYAIpZIBFw`, 4688 bytes SHA256 `75c57eb14f1ccb37d9c21e96db747c9dad13a05f9e107d2a98bfbe4503e55911`.
- ZIP do replay em Actions privado: Drive ID `1uHWMR8cbxzInRVE5NaKfJ4xHCm42JdId`, 1549 bytes SHA256 `da77ac0abd9593b1a9d9d75838905ea6649b43a27a6bab583c850a11fd60cef2`.
- Backup do contexto antes do adendo: Drive ID `1mhVV5LyqpCUn27Qwxk9x6eKBT0yCLpDm`, SHA256 `ece8bc86c700df98ef4adbb53be49c87a363d2ef0a924b8c231e29c85a71cb79`. Contexto canônico atualizado **no mesmo ID**, tamanho 1.142.027 bytes SHA256 `03c9fa667321752046c10ce30aff1ec7de33769acc106de6fa94aee422d61329`, readback verificado.

## PRE687 — somente instrumento preparado

- Script `automation/termux/nfsmw_pre687_timed_surfaceflinger.sh` disponível neste repo e na pasta privada `03_Scripts_e_Patches` Drive ID `1jo38KLdEAoIVeFniogp1ZAkvWiWeoglt`.
- `bash -n` **PASS** e teste sintético local **PASS** para extração do histograma rotulado, preservação de `displayConfigStats` opcional e exclusão de outros apps. Sem teste real no S24 FE.
- Protocolo sugestivo: **armar antes de abrir o jogo** com `arm 110 90`; aguardar 110 segundos para carregar e terminar a primeira cinemática, coletar 90 segundos no carro parado automaticamente, sem trocar de app durante o intervalo. Atrasos reais da cena podem mudar, portanto checar novo log.
- O `worker` encerra os contadores ao terminar. Caso Termux seja suspenso em segundo plano, a coleta pode ficar incompleta. O script não muda gráficos, FPS cap, APK, assinatura, CPU/GPU clocks ou proteções térmicas.
- Não usar 120Hz como valor confirmado antes de capturar o status `displayConfigStats` e os registros de janela.

**Estado:** PRE686 REAL_SURFACEVIEW_PASS/ACTIONS_PASS; PRE687 SCRIPT_SYNTHETIC_ONLY; FPS_GAIN_UNPROVEN; APK_V51_PRESERVED.
