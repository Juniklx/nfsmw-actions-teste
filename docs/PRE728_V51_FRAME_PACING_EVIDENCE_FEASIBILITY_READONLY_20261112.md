# PRE728 — V51: reconciliação de frame pacing e viabilidade de captura sem V52 (2026-11-12)

## Gate executado: PASS somente para reconciliação de relatórios

**Status: `PASS_PRE728_VERIFIED_SECONDARY_REPORT_RECONCILIATION`.** O [GitHub Actions run 43312069225](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43312069225) concluiu **success**. GitHub Actions leu três fontes de volta do Google Drive por API autenticada e exigiu tamanho e SHA256 exatos, coerência interna das três séries de intervalos e consistência com a PRE727. A etapa não executou Kaggle, nova captura no telefone, instalação, C++, build ou APK.

As fontes verificadas foram:
- [PRE700 relatório real](https://drive.google.com/file/d/1oRoyx0HsbNvsI-jhbQWbvDNZpXoG0bbR/view): 6.977 bytes; SHA-256 `29a34777e0b2de84fcfa847ca47f4a6828cc0a68de3f26d7ac857f3278af033e`.
- [PRE701 fase A](https://drive.google.com/file/d/1I3RHJxrDY6up3GbRz3VufDngUqQEb866/view): 5.650 bytes; SHA-256 `46ae753d2ef446ee67caf4c31a9cdbdb2338f25bbfb703bd5f7ff42826279a33`.
- [PRE727 relatório de listas Vulkan da V51](https://drive.google.com/file/d/1V0-8L65bkwR4GsQ_Atb79MKwbAO7dQvf/view): ZIP 1.035 bytes; SHA-256 `9d5fd40b478eca6a7b2d31b1e9c8b732bd70454dd0585674eaeb4664a0ae1257`, CRC íntegro.

**Importante:** esta PRE728 é uma auditoria **secundária** de três relatórios já auditados. Ela **não** reprocessou os quadros crus do `nfsmw3.zip` da PRE700; o ZIP original não foi localizado entre os resultados relevantes da busca acessível no Drive. A validação primária da captura e da coleta permanece documentada na PRE700/PRE701, não é promovida incorretamente a uma nova captura PRE728.

## Números de uma mesma captura V51

- Dispositivo: Galaxy S24 FE, Samsung Xclipse 940, `io.github.nfsmwrecomp`, `versionCode 51`.
- Resolução interna 1920×1080, **limite do jogo observado em 60 FPS**; display a 120 Hz. Não confundir meta de 120 FPS com esta captura.
- PRE700: 2.279 triplas temporais únicas; após excluir **uma lacuna de aquisição** de aproximadamente 999,482344 ms, **2.277 intervalos contíguos** cobrem uma cadência de **59,991589 apresentações/s**.
- PRE701: `desired` irregulares **3/2.277**; `ready` **119/2.277**; `actualPresent` **489/2.277**. Destes 489, **459** têm `ready` regular e **30** têm `ready` irregular; entre os 119 `ready` irregulares, **89** coincidem com `actualPresent` regular. As contagens conciliam `459+30=489` e `30+89=119`.
- Distribuição da cadência `actualPresent`: **246 intervalos** de aproximadamente um tick (8,33 ms), **1.788** de dois ticks (16,67 ms), **240** de três ticks (25 ms) e **3** de quatro a seis ticks. A irregularidade `actualPresent` ocorreu em **21,48%** dos intervalos; os 459 casos em que `ready` foi regular representam **93,865% dos 489 casos irregulares**.
- A variabilidade de `actualPresent` ser maior que a de `ready` **não prova** que o compositor/SurfaceFlinger seja culpado: `ready` não é o timestamp do retorno de `vkQueuePresentKHR`; não houve pareamento do mesmo quadro entre guest vblank, Vulkan, compositor e hardware.

## O que PRE727 acrescentou

Na execução real PRE656 da V51, o jogo reportou **três extensões de dispositivo habilitadas**: `VK_EXT_extended_dynamic_state3`, `VK_EXT_memory_budget`, `VK_KHR_swapchain`. **Não** reportou `VK_GOOGLE_display_timing` como habilitada. PRE702 informou a extensão como **anunciada pelo driver** a partir de um resumo fornecido pelo usuário; anúncio não é habilitação. Não afirmar que os timestamps de `vkGetPastPresentationTimingGOOGLE` estejam disponíveis na V51, nem que há paridade de fonte com a biblioteca assinada.

## Viabilidade: comparação de caminhos para um próximo experimento

1. **Logs existentes `dumpsys SurfaceFlinger --latency` + C2:** **suficientes para confirmar irregularidade e cadência**, mas insuficientes para identificar qual estágio produziu cada desvio.
2. **Perfetto FrameTimeline:** a [documentação atual do Perfetto](https://perfetto.dev/docs/data-sources/frametimeline) informa explicitamente que **SurfaceViews não são suportadas** nessa funcionalidade; esta captura NFSMW usa uma camada `SurfaceView[...GameActivity]`. Portanto, **não planejar causalidade com base na suposição de que haverá slices/tokens FrameTimeline dessa camada**. Pode-se sondar disponibilidade no aparelho antes de depender dela; ainda não foi capturada prova de suporte para a camada V51.
3. **Perfetto rastreamento de sistema + SurfaceFlinger latency + telemetria térmica sincronizada:** caminho **preferencial sem modificar APK**, condicionado a permissões reais de `shell`/Shizuku, quantidade de eventos acessíveis, captura da mesma cena estática e sincronização de relógios. As fontes oficiais [Perfetto Android tracing](https://perfetto.dev/docs/learning-more/android) e [Clock synchronization](https://perfetto.dev/docs/concepts/clock-sync) documentam mecanismos, **não garantem** que um S24 FE não-root mostre fence individual ou ID de quadro do NFSMW. Sem ClockSnapshot ou pareamento confiável, não juntar timestamps de `BOOTTIME` e `MONOTONIC` diretamente.
4. **Vulkan `VK_GOOGLE_display_timing` ou `VK_EXT_present_timing`:** [documentação oficial do Android](https://developer.android.com/games/develop/vulkan/frame-pacing-extensions) exige habilitação apropriada na criação do dispositivo e recursos suportados. A V51 não reporta GOOGLE habilitada; PRE702 não encontrou EXT anunciado. Uma instrumentação desse tipo demandaria planejamento específico, validação de equivalência, revisão de riscos e nova build assinada corretamente (versionCode superior a 51), **não aprovada neste gate**.

## Decisão e PRE729

**PRE728 não deve se prolongar em novas sondas lexicais repetitivas.** Priorizar **PRE729 de capacidade de captura não invasiva**, testando que ferramentas de `shell`/Shizuku estão disponíveis sem root, verificando presença de dados reais da `SurfaceView`, e preparando coleta simultânea de `SurfaceFlinger --latency` + rastreamento `gfx/sched` e termometria existente. O gate PRE729 primeiro precisa provar que produz dados úteis no S24 FE; **não** afirmar que ele já mediu uma sessão ou identificou culpado.

**Código/execução:**
- [verificador somente leitura](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/automation/kaggle/pre728_verify_v51_pacing_evidence_readonly.py) — commit `3871458ca2a08ac51f66a573c9edcc81a11421ac`;
- [workflow](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre728-v51-pacing-evidence-readonly.yml) — commit `410c48b85dcbe09b59481d7c910751d4fa1e3f8d`;
- [Actions 43312069225](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43312069225), artefato **13985279407**, ZIP **1.262 bytes**, SHA-256 `885f838bbdcb790db0c71bbb33b302aac335bdb4f50a13281ab209ace5da564c`, CRC PASS, JSON sanitizado. [Drive ZIP conferido](https://drive.google.com/file/d/1aodhW5-0Xfe4IN7SQY6i6v-TyGoSlXVZ/view).
- [Backup anterior da fonte canônica](https://drive.google.com/file/d/1U_3gGMpf4WZ9gHQ_nKlNSwgk7xw5HRH1/view): 1.372.051 bytes; SHA-256 `09fecefda6409c9f187025c8d30edc8d65492bd58fa0988e99394cf3cf6b803e`.

**Preservação:** pacote `io.github.nfsmwrecomp`, V51 `versionCode=51`, certificado SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, gráficos completos, shaders, efeitos, física, touch, PG-9076, saves e limites térmicos. Sem código-fonte/apk alterado, sem V52, sem nova assinatura, sem FPS melhorado comprovado.

**STATUS:** `PRE728_SECONDARY_REPORT_SHA_PINNED_PASS; PRE700_PRE701_COUNTS_CONSISTENT; ACTUAL_489_READY_119_DESIRED_3; ACTUAL_IRREG_READY_REG_459; GOOGLE_TIMING_NOT_ENABLED_IN_PRE727_LOG; SURFACEVIEW_FRAMETIMELINE_NOT_ASSURED; NO_PRE700_RAW_REPLAY; ROOT_CAUSE_UNPROVEN; NEXT_PRE729_SHELL_CAPTURE_FEASIBILITY; NO_V52; NO_FPS_GAIN`.
