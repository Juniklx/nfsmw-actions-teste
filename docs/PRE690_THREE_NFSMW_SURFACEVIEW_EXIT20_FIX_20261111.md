# PRE690 — correção do erro SurfaceView duplicada (2026-11-11, S24 FE)

## Evidência real enviada pelo usuário

Trecho do arquivo `NFSMW_PRE690_CAPTURE_20261111_054416.status.txt`:

```text
PRE690_STAGE=WAIT delay_s=110
PRE690_MATCHING_NFSMW_LAYERS=3
PRE690_WORKER_EXIT_CODE=20
```

**Diagnóstico verificado:** o coletor publicado originalmente exigia exatamente 1 `SurfaceView[io.github.nfsmwrecomp/` e abortou **antes** de limpar o histórico, capturar a sequência `--latency` ou gerar o arquivo `ORDERED_PRESENT`. Isso não demonstra qualquer travamento do NFSMW, bug Vulkan, instabilidade de FPS ou degradação gráfica. Nenhum arquivo PRE690 de coleta foi encontrado na pasta privada de logs do Drive neste checkpoint; o status foi fornecido diretamente no chat pelo usuário.

A presença de 3 SurfaceViews pode incluir instâncias antigas, mas **não foi comprovado que duas sejam antigas**. Não selecionar superficialmente a de maior identificador, último nome na lista ou primeira posição.

## Correção publicada no mesmo coletor

Script: `automation/termux/nfsmw_pre690_ordered_latency_adb.sh`, commit de correção `eac91a4fde87b3174d16578378b5b32759415345`. Em vez de rejeitar todas as camadas múltiplas, a rotina:

1. Obtém os nomes de SurfaceView pertencentes ao pacote, sem arquivar outras camadas.
2. Consulta `dumpsys SurfaceFlinger --latency` em cada camada para obter o maior timestamp válido de apresentação real.
3. Aguarda 2 segundos, repete a consulta e identifica as camadas cujo timestamp avançou.
4. **Apenas se exatamente uma camada avançou**, passa a capturar o histórico exclusivamente dessa SurfaceView. Caso 0 ou 2+ avancem, falha de forma segura com `PRE690_LAYER_AMBIGUOUS_OR_INACTIVE_ABORT=TRUE` e código 20. Sem escrita do `ORDERED_PRESENT`.
5. Logs de diagnóstico informam `PRE690_MATCHING_NFSMW_LAYERS`, `PRE690_LAYER_{n}_ADVANCING`, `PRE690_ADVANCING_NFSMW_LAYERS`. Nenhum nome de outro app é salvo.

Não há alteração na APK V51, manifest, assinatura, gráficos Vulkan, 1080p, limite 60 FPS, controles, saves, física, frequência do painel nem proteções térmicas.

## Verificação e próximo passo

Workflow de teste offline atualizado em `.github/workflows/nfsmw-pre690-ordered-latency-synthetic.yml`; testes sintéticos solicitados pelo commit `63d53643fd3055e5317c7cca93ebfe85e0e426df`. O teste inclui 1 camada avançando; 2 camadas avançando (aborto seguro); e 3 camadas, sendo 2 sem progresso e 1 avançando (seleção segura). **O resultado da execução no GitHub ainda não foi confirmado**; não declarar PASS do novo coletor no Galaxy.

Para novo ensaio, usuário precisa baixar novamente o script atualizado e executar `preflight` e `arm 110 30` (ou `arm 110 60`). Salvar/compartilhar o novo `NFSMW_PRE690_CAPTURE_*.status.txt`; se houver `ORDERED_PRESENT`, compartilhar junto com `nfsmw.log` da mesma sessão. Se todas as três SurfaceViews avançarem, continuar sem seleção automática e investigar critérios por atividade de camada. Não repetir teste sem que o usuário deseje/autorize.

**Baseline:** V51 PRE652, `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; nenhum patch gráfico ou ganho FPS comprovado.

Status PRE690: REAL_DEVICE_ATTEMPT_ABORTED_3_SURFACEVIEWS; COLLECTOR_FIXED_WITH_UNIQUE_PROGRESS_CHECK; NEW_SYNTHETIC_CI_PENDING; RETEST_PENDING; NO_APK; NO_FPS_GAIN.
