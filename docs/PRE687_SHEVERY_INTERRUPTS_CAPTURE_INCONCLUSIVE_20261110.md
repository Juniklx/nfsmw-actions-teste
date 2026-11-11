# PRE687 — interrupções do Shevery informadas pelo usuário (2026-11-10, Bahia)

## Correção essencial de interpretação

O usuário confirmou explicitamente que, durante o teste PRE687, **Shevery abriu inesperadamente duas vezes** e ele voltou ao NFSMW após cada abertura. A amostra NÃO foi uma captura contínua de 90s com o NFSMW ininterruptamente em primeiro plano.

Arquivos originais recebidos no chat:
- `nfsmw.log`, 788.568 bytes, SHA256 `ced48603d4260d58047a56bfcc0ae434c2fda348b792fe48a379fa470762f317`; de 23:50:52.866 a 23:54:44.743.
- `NFSMW_PRE687_CAPTURE_20261110_235045.status.txt`, 28.819 bytes, SHA256 `f0bd15f5e3a2a6984350af21c6675afa1587b88592bc8106ef5196896f9030fd`.

## Eventos demonstrados no log real

- 23:52:39.304: `VulkanPresenter: Presentation to the swapchain image has been dropped as the swapchain or the surface has become outdated`; swapchain Vulkan MAILBOX 1920x1080 criada novamente às 23:52:39.342.
- 23:54:11.756: segunda perda por superfície desatualizada; swapchain recriada às 23:54:11.779.
- 23:54:28.778: vigilante do motor alerta **5 segundos sem progresso** em nenhuma das 17 threads monitoradas; 23:54:43.803 alerta **20 segundos**. Isso é um alerta real do vigia, mas não prova deadlock/bug independente porque houve duas transições inesperadas de app.
- O script PRE687 foi armado às ~23:50:45 com `arm 110 90`: acionamento da coleta programado para ~23:52:35; dump previsto para ~23:54:05. As duas recriações de superfície ocorreram poucos segundos depois dessas transições de medição. **Correlação temporal relevante, não demonstração causal.**

## SurfaceFlinger status — dados parciais, gate não aprovado

- `PRE687_STAGE=WAIT_BEFORE_GAMEPLAY delay_seconds=110` e `PRE687_STAGE=CAPTURING duration_seconds=90` constam no status, mas encerra com `PRE687_NO_LABELED_PRESENT_TO_PRESENT_HISTOGRAM=TRUE`; `PRE687_CAPTURE_SUCCESS` e `PRE687_CAPTURE_OUTPUT` não estão presentes.
- O status contém uma saída bruta de múltiplas camadas, embora o coletor tivesse sido projetado para salvar somente a camada do jogo. **Não publicar esse arquivo em repositório ou Actions público.**
- Dados recuperáveis para SurfaceView NFSMW: `displayRefreshRate=120 fps`, `renderRate=120 fps`, `totalFrames=5346`, `averageFPS=62.241`, histograma rotulado `present2present`: 8ms=491, 16ms=4321, 24ms=229, 25ms=239, 33ms=7. Total de todos os buckets = 5346. Esses números incluem interrupções; não são frame pacing limpo do carro parado.
- Nenhum relatório `PRE687_PRESENT2PRESENT_*.txt` foi confirmado.

## Decisão técnica

PRE687 = **INCONCLUSIVE / CONTAMINATED_BY_EXTERNAL_APP_SWITCHES_AND_CAPTURE_FAILURE**. Não promover como PASS ou prova de defeito permanente no renderizador; não concluir que o Shevery causou o watchdog, apenas que pode ter provocado perdas de superfície. A V51 PRE652, pacote, assinatura permanente, gráficos/1080p, saves, controles e limites térmicos não foram alterados.

Próximo passo: captura controlada usando `adb shell dumpsys SurfaceFlinger --timestats` via conexão ADB confiável que não ative a interface do Shevery durante o jogo, com captura mínima, intervalos rotulados e novo `nfsmw.log` da mesma sessão. Verificar ADB/permissões antes de iniciar e manter arquivos brutos privados. Se vigia de 5s/20s reaparecer **sem** trocas de aplicativo, investigar o travamento em gate separado; não corrigir preventivamente por patch.

Status PRE687: TWO_SHEVERY_FOREGROUND_INTERRUPTS_USER_CONFIRMED; TWO_VULKAN_SURFACE_RECREATIONS_OBSERVED; WATCHDOG_5S_20S_OBSERVED; CAPTURE_NOT_COMPLETED; NO_NEW_APK; NO_FPS_GAIN.
