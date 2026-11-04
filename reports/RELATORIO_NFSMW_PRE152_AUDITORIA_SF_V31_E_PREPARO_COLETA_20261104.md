# NFSMW PRE152 — Auditoria SurfaceFlinger/WSI e preparação de medição V31

**Data:** 2026-11-04. **Estado:** auditoria documental e testes locais concluídos; **coleta PRE152 no Galaxy S24 FE ainda não executada**. Nenhuma APK V32 gerada ou alteração no jogo.

## Referência real preservada

- Base: PRE151, construída a partir dos três arquivos PRE150 capturados no Galaxy S24 FE, com `versionCode=31` comprovado, sessões de 20:11:49 a 20:17:03.
- Em PRE151: `Thermal Status` 0→1→2→3, `SKIN` até 45,1 °C, FPS C2 **estimado** 117,59→72,60 entre 20:13:30 e 20:16:50, custo GPU 6,90→11,40 ms/Swap. A carga da cena não foi constante; isso não quantifica efeito térmico causal.
- Em PRE151: `vkQueuePresentKHR` médio 3,050 ms dos 50 blocos de 600 frames, ~95,1% de `PaintAndPresent` e **não** do frame completo. Não pode ser removido sem analisar sincronização.
- A V31 usa swapchain Vulkan 1920×1080, apresentação `MAILBOX` e quatro imagens **solicitadas** (não confirmadas como concedidas).

## Auditoria da documentação e código AOSP

1. Android Developers documenta `dumpsys SurfaceFlinger --timestats -clear -enable` para começar a capturar, `-dump` para obter FPS médio e histograma `presentToPresent` e `-disable` para encerrar. O resultado possui seções `layerName`; **a camada do jogo deve ser identificada por nome**, não confundida com a UI de outro processo. Fonte: https://developer.android.com/topic/performance/issues/slow-session .
2. A fonte AOSP `SurfaceFlinger.cpp` contém despachantes para `--list`, `--latency` e `--timestats`. `--latency` consulta uma camada cujo nome corresponde a `getName()` e expõe estatísticas de frames; não é a mesma coisa que o contador `presentados` do motor. Fonte: https://android.googlesource.com/platform/frameworks/native/+/792ea80280c156b738730db0289f66b6cfd7326a/services/surfaceflinger/SurfaceFlinger.cpp .
3. O AOSP `TimeStats.cpp` confirma `-enable`, `-dump`, `-clear`, `-disable`. Ativar e limpar o TimeStats **muda contadores globais de diagnóstico do sistema temporariamente**. Este procedimento não manipula VSYNC, modo de apresentação, frequências, configuração gráfica nem limites térmicos, mas pode interferir em outros perfiladores. Não executá-lo simultaneamente com outro monitor do SurfaceFlinger. Fonte: https://android.googlesource.com/platform/frameworks/native/+/master/services/surfaceflinger/TimeStats/TimeStats.cpp .
4. A documentação de Frame Pacing distingue `buffer stuffing`/fila de frames da GPU: filas cheias podem bloquear chamadas Vulkan, mas **isso permanece apenas hipótese para as esperas PRE151**. Não instalar Swappy ou habilitar `present_thread` sem conferir integração na fonte exata e medir resultado. Fonte: https://developer.android.com/games/sdk/frame-pacing .
5. `VK_EXT_present_timing` foi documentada para Android 17/API 37, mas **não foi verificada no driver nem habilitada no binário V31**. Não é uma solução ativável apenas pelo nome. Fonte: https://developer.android.com/games/develop/vulkan/frame-pacing-extensions .

## Script produzido: PRE152, medida pareada por camada sem rebuild

- Arquivo: `nfsmw_pre152_v31_surfaceflinger_pareado.sh`. SHA-256 `18324df2bfd8cff12e982262a93b294e97e1c0bf91d9f01360e7bdfc00c08ba4` (verificar valor do arquivo final antes de distribuir).
- Executa **uma sessão** `sh ~/rish -c` para verificar UID shell 2000 e `versionCode=31`; inicia o jogo da mesma forma comprovada na PRE148 com **única** flag `--present_perfil_pintado`.
- Usa `SurfaceFlinger --timestats -clear -enable` e amostras `-dump` a cada 20 s (240 s por padrão). Do dump global, mantém no relatório apenas as seções de camada contendo `io.github.nfsmwrecomp` e os campos de tempo/FPS pertinentes; também coleta status térmico, temperaturas HAL atuais, leituras pontuais GPU e dados atuais de bateria. **Não preservar estatísticas de outros apps**.
- Tenta `--timestats -disable` tanto ao fim quanto no `trap EXIT` em erros/sinais. **Se o processo shell for morto à força, a limpeza não é garantida**; neste caso é necessário confirmar ou aplicar manualmente `-disable` via Shizuku.
- Saída gravada diretamente em `/sdcard/Download/nfsmw_pre152_v31_surfaceflinger_*.txt`, evitando fragmentação `stdout`/`stderr` observada na PRE150. Não altera o `nfsmw.log`; este deve ser preservado separadamente.
- Esta instrumentação **não foi testada no aparelho**. Samsung/Android 17 pode não permitir a leitura dos contadores ou pode usar formato diferente do AOSP. `STATUS_FINAL=COLETA_ENCERRADA` significa que a rotina terminou, **não** que a camada foi localizada ou que o FPS foi validado. Conferir `SF_LAYER_METRICS` e `layerName` antes de calcular.

## Verificações realizadas neste ambiente

- `bash -n` para o script PRE152: **PASS**.
- Simulação isolada do fluxo shell, com `rish`, `id`, `am`, `dumpsys` e `sleep` substituídos por comandos falsos: `versionCode=31` produziu 3 amostras, filtrou somente a camada do jogo, concluiu e chamou `-disable`; `versionCode=30` terminou com código 11 **antes de iniciar jogo ou TimeStats**. Esses testes não atestam compatibilidade com a ROM Samsung.
- Parser `nfsmw_pre152_analisar_timestats.py`: `py_compile` PASS; fixture com `totalFrames` 500→900 em 20 s produziu 20 FPS; reinício 900→2 foi corretamente rejeitado. Não é uma medição do telefone.

## Procedimento quando for possível realizar teste no telefone

1. Galaxy S24 FE com a **V31 instalada**, Shizuku ativo e arquivo salvo em Downloads; jogo fechado e sem outro perfilador SurfaceFlinger ativo. Mesmo cenário de direção com carro parado e configurações inalteradas.
2. No Termux: `bash ~/storage/downloads/nfsmw_pre152_v31_surfaceflinger_pareado.sh 240 20`.
3. Jogar durante a captura; depois, enviar `/sdcard/Download/nfsmw_pre152_v31_surfaceflinger_*.txt` e `nfsmw.log` da mesma sessão. Se a sessão foi interrompida e o TimeStats ficou ativo, encerrar com Shizuku e `dumpsys SurfaceFlinger --timestats -disable`.
4. Aplicar o parser e comparar diferenças **por camada e por intervalo cronológico** com o C2 do motor, GPU e térmica. Não somar GPU e `vkQueuePresentKHR` nem afirmar que o SurfaceFlinger efetivamente mostra todos os `presentados` sem conferir a camada.

## Restrições preservadas

Sem patch na árvore, sem APK V32, sem mudança no certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, pacote `io.github.nfsmwrecomp`, 1920×1080, limite 120 FPS, shaders/efeitos, física, PG-9076, configuração térmica ou sync Vulkan. O próximo APK, **somente se justificado**, exigirá `versionCode>31` e a mesma assinatura.

**Pendências:** teste real do PRE152 no aparelho; atualização do `CONTEXTO_NFSMW.md` canônico no Drive continua bloqueada na gravação. Relatórios PRE151 e este PRE152 podem ser arquivados separadamente sem substituir o contexto até haver autorização de escrita comprovada.
