# PRE577_HANDOFF_PRE573_ON_DEVICE_LOG_MARCEK_20261109

**Data:** 2026-11-09, horários locais America/Bahia. **Entrada:** `nfsmw.log` fornecido pelo usuário nesta conversa após captura de tela da sessão com fragmentos PRE573 aplicados no Galaxy S24 FE. Arquivo analisado localmente de 154.955 bytes, 854 linhas, SHA256 `5ef32c7a3cab4f6219a34a0f790d37b50570d7797e63a9cd108d12bb38eed2e0`. O arquivo original do usuário permanece no chat; **não foi enviado ao GitHub nem ao Drive por esta análise**. A captura mostra textualmente `MARCEK está corrompido.`; o log NÃO contém essa string.

## Evidências positivas no log

- `01:31:37.986`: VFS montou com sucesso `/storage/emulated/0/NFSMW_PTBR` como `\\Device\\Harddisk0\\Partition1`, 22 entradas, **somente leitura**. Este é o caminho real observado no telefone para os arquivos do jogo PT-BR, e substitui a incerteza do checkpoint PRE574 sobre o GAME_ROOT; não significa que a APK tenha inspecionado o hash do ZDIR/ZZDATA.
- `01:31:39.397`: leitura registrada de 5.018.060 bytes de `NFS\\ZZDATA4.BIN` no offset **37.898.240**, além de leituras de outros arquivos de recurso. Não existe marcador direto no log confirmando leitura do **setor 0 / primeiros 698.368 bytes** alterados pela PRE573 ou aceitação da coleção `engine/bmwm3gtr_upgrade_engine_pre499`.
- `01:31:46.869` até `01:31:50.668`: `MARCEK` aparece como entrada de save `rmcsave`, **um arquivo de 62.688 bytes**. A camada de arquivos registrou **quatro aberturas** `XamContentCreate` com `resultado 00000000` (sucesso), fechamento e quatro cópias internas do perfil para `saves/MARCEK/actual`. **Abertura do contêiner != validação do formato/checksum/conteúdo da carreira pelo guest.** Não afirmar que save esteja íntegro nem irremediavelmente danificado.
- `01:31:37.904`: gamertag configurada `User`, que não precisa ser igual ao nome da carreira `MARCEK`; nenhuma causalidade estabelecida.
- `01:31:37.218`: renderização interna **1920×1080**, `limite de FPS 60`, modo de vídeo informado 1280×720/60 Hz. A meta do projeto de cap 120 FPS não é configuração ativa nesta sessão; não confundir com ganho de FPS.
- `01:32:08.952`: `[pausa] juego y audio en pausa (segundo plano)`; após isso, watchdog registrou paradas de cinco segundos às `01:32:14` e `01:32:21`, breve retorno às `01:32:15`, e 20 segundos às `01:32:36`. **Não atribuir ao patch nem classificá-los como travamento definitivo**, pois o aplicativo já estava em segundo plano.
- Warnings `NtCreateFile FAILED` (por exemplo `D:\\GLOBAL\\ATTRIBUTES.BIN`) e ausência de arquivos soltos são compatíveis com busca de arquivo direto seguida de recursos nos arquivos ZZDATA; sem erro de loader guest específico, não afirmar que tais warnings sejam causa da corrupção.

## Conclusões conservadoras

1. `PRE573_DEVICE_SCRIPT=APPLIED_REPORTED_BY_USER`. O sucesso de aplicação por hashes foi **saída fornecida pelo usuário**, sem readback remoto dos ativos do S24 FE.
2. `V48_STARTED_UI_AND_MOUNTED_PTBR=OBSERVED_IN_LOG_AND_SCREENSHOT`. O jogo chegou à interface que mostra corrupção do perfil.
3. `SAVE_CONTAINER_OPEN_SUCCEEDED=true`; `SAVE_PAYLOAD_INTEGRITY_PROVEN=false`; `MARCEK_PERMANENTLY_CORRUPTED_PROVEN=false`; `PROFILE_CANNOT_LOAD=OBSERVED_IN_SCREENSHOT`.
4. `PRE573_GUEST_NEW_ATTRIBUTE_COLLECTION_ACCEPTED=NOT_PROVEN`; `BMW_ENGINE_LEVEL_UNLOCKED=NOT_PROVEN`; `BMW_TUNABLE=NOT_PROVEN`; `PRE573_CAUSED_SAVE_WARNING=NOT_PROVEN`.
5. **Próximo teste A/B obrigatório para causalidade:** fechar totalmente a V48, executar a restauração verificada `pre573_restore_bmw_ptbr_shevery.sh` contra o `GAME_ROOT` **observado** `/storage/emulated/0/NFSMW_PTBR`; conferir `PRE573_RESTORE=ORIGINAIS_VERIFICADOS`, sem apagar nenhum save; reabrir a mesma V48 com arquivos PT-BR originais e selecionar `MARCEK`. Se carregar, hipótese de incompatibilidade dos recursos experimentais ganha força (não é prova isolada de qual campo/ponteiro); se permanecer corrompido, o problema persiste sem o patch e exige análise do save/compatibilidade. Registrar screenshot e novo `nfsmw.log`. O usuário aceita criar outro save depois, mas não declarou intenção de excluir automaticamente `MARCEK`.

## Segurança e integridade

Não alterar APK V48 PRE452, package `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, Nitro PRE398, controle físico PG9076/touch, qualidade/1920×1080/física/proteções térmicas. O `PRE573` deve manter os backups de `ZDIR.BIN` e `ZZDATA4.BIN`; não reutilizar nenhum script de aplicação antes de confirmar o estado atual. **Este checkpoint foi derivado de log e captura e não executou comandos no aparelho.**
