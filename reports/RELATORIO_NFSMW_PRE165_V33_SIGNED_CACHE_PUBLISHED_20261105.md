# PRE165 — V33 compilada, assinada e publicada (2026-11-05)

## Evidências realmente verificadas

- GitHub workflow run **42065054639**: **success** (final em 2026-11-05 16:58:26 UTC); todos os 22 passos, inclusive compilação/validação, preservação do artefato e caches, concluídos com sucesso.
- Artefato GitHub **13434879981**, nome `nfsmw-pre165-v33-PRE117-PRE128-42065054639` (ZIP); conteúdo: `pre165-report.json` e APK.
- Relatório assinado: `gradle_release_succeeded=true`, `gradle_release_exit_code=0`, `signed_apk_verified=true`, `verification_subphase=APK_ALL_GATES_PASSED`; `pre165_sdl_delay2_applied=true`, `pre157_callback_move_applied=true` e patches PRE117/128/131/133 confirmados no runner.
- APK **47.101.481 bytes**, SHA-256 **`b2c5574d15532f02ca3d84c8d66c162990ace0fa111d7b6e7db9f2c38be15bdf`**; ZIP CRC e SHA dos bytes extraídos novamente verificados fora do runner.
- Package `io.github.nfsmwrecomp`, `versionCode 33`, certificado permanente v2 SHA-256 **`1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`**; 10 bibliotecas ARM64 e assets PAL/USA preservados. `librexruntime.so` SHA-256 `b4b2f7c99aff7ebb3384ed02a7680250b6322fad686d22d8ac4692f4103fcca2` diferente V31/V32.
- APK enviada diretamente via conexão Google Drive à pasta `02_APKs`, ID **`1WVUZAdjJwksCWxcj_fniyfKvuUl6YYLY`**, URL `https://drive.google.com/file/d/1WVUZAdjJwksCWxcj_fniyfKvuUl6YYLY/view`. Drive retornou 47.101.481 bytes; arquivo baixado novamente e SHA-256 comparado byte a byte com fonte.
- Backup ZIP com APK e relatório no Drive, ID **`1u2Lmp9BaotL10x1073hd3V82wkZzcz6y`**, 45.721.770 bytes.
- PRE139 Gradle: cache miss na restauração inicial, política de integridade PASS, 22.832 arquivos / 743.140.785 bytes inspecionados, `actions/cache/save` reportou **Cache saved with key**.
- PRE140 SDK-only `ccache`: cache miss inicial, `cacheable_calls=45`, `hits=0`, `misses=45`; política PASS, 379 arquivos / 7.659.924 bytes, `actions/cache/save` reportou **Cache saved with key**. Economia de tempo ainda **não comprovada**.
- V32 preservada e benchmark PRE163 (60 FPS) continua referência; o valor 60 FPS da configuração ativa precisa ser confirmado depois da atualização.
- **Não realizados:** instalação V33 no S24 FE, execução do jogo, teste touch, PG-9076, validação do delay de 2 ms no log, FPS, temperatura ou autonomia. Não declarar ganho térmico/CPU. A nova pausa pode afetar latência de eventos seguintes.

## Próximo passo

Instalar V33 como atualização **sem desinstalar** V32, preservando dados, e confirmar `versionCode=33`, 1920×1080, teto 60 FPS, abertura, menus e controles. Fazer teste térmico frio com bateria 50–80%, aparelho fora do sol, sem carregar e com o carro parado após primeira cinemática. Coletores antigos PRE159 são específicos a versionCode 32; usar variante de leitura PRE166/V33 para não rejeitar a instalação.
