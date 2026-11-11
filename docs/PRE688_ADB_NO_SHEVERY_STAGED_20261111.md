# PRE688 — coleta alternativa por ADB sem fio, sem Shevery (2026-11-11)

## Motivação verificada

PRE687 não foi uma sessão limpa. O usuário confirmou que Shevery abriu duas vezes e precisou voltar ao NFSMW. No `nfsmw.log` da mesma sessão, Vulkan SurfaceView ficou desatualizada e a swapchain 1920×1080 MAILBOX foi recriada às 23:52:39 e 23:54:11 de 2026-11-10. O vigilante do motor alertou 5s sem progresso às 23:54:28 e 20s às 23:54:43. A causa do alerta não foi determinada.

O `NFSMW_PRE687_CAPTURE_20261110_235045.status.txt` tem `PRE687_NO_LABELED_PRESENT_TO_PRESENT_HISTOGRAM=TRUE`, sem saída `PRE687_CAPTURE_SUCCESS`. Contém dump parcialmente bruto de outras camadas, portanto **NÃO publicar** esse arquivo em GitHub nem em logs de Actions. O `SurfaceView` incluiu `displayRefreshRate=120 fps`, `totalFrames=5346`, `averageFPS=62.241`, mas a amostra foi contaminada por duas interrupções. Não atribuir frames irregulares à condução contínua.

## PRE688: implementação preparada, teste no celular pendente

- Script público de coleta: `automation/termux/nfsmw_pre688_adb_surfaceflinger.sh`.
- GitHub commit: `950a6308585bd16c97db4f6282ccc13f56eaee2d`.
- Fluxo de verificação sintética (nenhum jogo/ISO/segredo) em `.github/workflows/nfsmw-pre688-adb-collector-preflight.yml`, solicitação de execução pelo commit `f9870cda470a4de8c31e1f2b5ef3c50284bf8648`. **Conclusão real do GitHub Actions ainda não consultada/confirmada**.
- A versão local foi examinada com `bash -n` e um ADB sintético: pré-teste shell UID 2000 e modelo SM-S721B; um `SurfaceView` NFSMW aceito; múltiplos `SurfaceView` NFSMW recusados; nomes de outros aplicativos não salvos. Esse teste não é execução real no S24 FE.
- O coletor usa `adb shell dumpsys SurfaceFlinger --timestats -clear -enable`, dorme a duração configurada, obtém `--timestats -dump`, filtra apenas a camada `SurfaceView[io.github.nfsmwrecomp/...` mantendo o **rótulo** `present2present`, e então executa `--timestats -disable` em limpeza. Requer **ADB sem fio já pareado e conectado**; não chama Shevery, rish, Shizuku, root, políticas de temperatura, clocks, opções gráficas ou APK.
- Modos `preflight`, `arm 110 90`, `status` e `abort`. Recusa dispositivo ADB ausente/múltiplo ou UID não shell. Se não houver exatamente uma camada NFSMW e um histograma rotulado, **não promove captura como válida**, não salva dados brutos de outras camadas.
- Setup de ADB sem fio (preparação manual no próprio aparelho): Termux `pkg install android-tools`; em Opções do desenvolvedor > Depuração sem fio usar o IP e porta de pareamento + código mostrado localmente `adb pair IP:PORTA`; depois usar a **porta de conexão distinta** `adb connect IP:PORTA`. Sem compartilhar o código. Opcionalmente `127.0.0.1` se funcionar no aparelho. É necessário que o serviço de depuração permaneça ativo; sucesso não garantido em Samsung/Android atual.
- Fonte pública consultada: Android Developers, `https://developer.android.com/topic/performance/issues/slow-session`. ADB shell lê `present2present` na camada do jogo; o histograma agregado não conserva a ordem dos quadros e não equivale a medição óptica do painel.

## Próximos gates

1. Se o pré-teste ADB real passar e o usuário decidir rodar, capturar no Galaxy S24 FE uma janela de cerca de 90s com o carro parado e sem alternar apps; obter TXT filtrado **e novo** `nfsmw.log` da mesma sessão.
2. Com ambos, confirmar pelo timestamp que não houve recriação Vulkan `surface outdated`, nova abertura inesperada do Shevery ou vigia 5/20s. Se houver, classificar amostra como interrompida e estudar o evento separadamente.
3. Comparar contagem e histograma de `present2present` com contadores internos de Swaps e contexto da corrida. Não propor troca de `MAILBOX`, cap, sincronização, shaders ou frequência do painel sem base concreta e testes controlados.
4. Atualizar o CONTEXTO_NFSMW.md canônico no Drive após conferir o resultado do preflight/execução real; adendo GitHub não substitui alteração com backup e readback.

**Estado de release preservado:** V51 PRE652 `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Não gerada V52, nenhuma mudança de shaders, gráficos 1080p, efeitos, controles, física, saves ou limiares térmicos; nenhuma melhora de FPS demonstrada.

STATUS: PRE687_INTERRUPTED_INCONCLUSIVE; PRE688_ADB_SCRIPT_STAGED; LOCAL_SYNTHETIC_TEST_PASS; GITHUB_AUTOMATED_RUN_RESULT_UNVERIFIED; DEVICE_CAPTURE_PENDING.
