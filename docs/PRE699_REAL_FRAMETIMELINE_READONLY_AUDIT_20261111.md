# PRE699 — FrameTimeline real no S24 FE: auditoria observacional sem alteração de APK

**Data:** 2026-11-11. **Resultado:** `TRACE_SHA_AND_PROTO_PARSE_PASS`; `NFSMW_SURFACEVIEW_FRAMES_NOT_IDENTIFIED`; `NO_FPS_GAIN_PROVEN`.

## Evidência real recebida e conferida

Arquivos fornecidos pelo usuário: `PRE699_STATUS.txt`, `PRE699_FRAMETIMELINE_CONFIG.pbtxt` e trace `nfsmw_pre699_20261111_234310.perfetto-trace`. Hash SHA-256 do trace: `e442e71638c6fee95bf620031db6ed3a99deb9303aeddea55b92c44aaeb9f9b9`, tamanho `1.103.742` bytes, idênticos ao manifesto. Configuração pediu `20.000ms` e `android.surfaceflinger.frametimeline`. O trace **não foi publicado no GitHub** por conter informação sobre outros processos.

Análise local, **sem Trace Processor oficial**, usando leitura restrita do wire-format protobuf conforme os esquemas Perfetto, validou:

- `15.010` pacotes Perfetto, `14.996` eventos FrameTimeline cobrindo `19,984957s`; relógio `BOOTTIME` (ID 6).
- `1.368` eventos `ExpectedDisplayFrameStart`, `1.373` `ActualDisplayFrameStart`, `2.377` `ExpectedSurfaceFrameStart`, `2.380` `ActualSurfaceFrameStart`, `7.498` `FrameEnd`.
- `7.498/7.498` cookies início/fim conferidos, sem faltas/duplicações.
- Janela Android `VRI-io.github.nfsmwrecomp/io.github.nfsmwrecomp.GameActivity`: `673` registros esperados e `673` efetivos, correspondência `673/673` entre tokens de superfície esperados/efetivos e `673/673` tokens de exibição presentes. Intervalo dessa janela `9,367614s`; mediana entre inícios efetivos `8,339551ms`; `11` intervalos >33ms. **Isso não mede os quadros do jogo**; registra a janela `VRI`.
- **0 eventos com nome de camada `SurfaceView` do NFSMW** na fonte FrameTimeline capturada. Esta ausência de etiqueta/evento **não prova que a SurfaceView deixou de renderizar**. O Perfetto documenta a limitação do suporte a SurfaceView.

O arquivo `PRE699_STATUS.txt` indicava `PRE699_TRACE=RECORDED_NOT_ANALYZED`; esta análise de estrutura agora está concluída separadamente. Não houve saída `dumpsys SurfaceFlinger --latency` **da mesma captura**, nem timestamps do guest vblank, `vkQueuePresentKHR`, GPU ou fences. Portanto não há pareamento quadro-a-quadro com PRE694/PRE695, prova de causa da alternância 8↔25ms, nem FPS médio do motor.

## Arquivos arquivados no Drive, sem trace bruto

- [Pacote ZIP sanitizado](https://drive.google.com/file/d/1lgazb5evLiKbsKwRAN172JeDtBeYqigF/view): `NFSMW_PRE699_SANITIZED_ANALYSIS_20261111.zip`, 7.267 bytes, SHA256 `a09568081555e229b44ec4186a2bbad47724fcdbc0a4a925492c1d72f9e801ab`. Inclui Markdown, JSON agregado e script offline; ZIP CRC PASS.
- [Relatório Markdown](https://drive.google.com/file/d/1Xk2b1itItjCTAFidFdMx4ss2MnE4W82O/view): `NFSMW_PRE699_READONLY_REPORT_20261111.md`, 5.366 bytes, SHA256 `f4ec1d9c0b8d6040a4c8fc5cce22b3d47c80cccc92e6ce86bc777595c0e1b0db`.

Fontes do esquema: [TracePacket](https://android.googlesource.com/platform/external/perfetto/+/master/protos/perfetto/trace/trace_packet.proto), [FrameTimelineEvent](https://android.googlesource.com/platform/external/perfetto/+/master/protos/perfetto/trace/android/frame_timeline_event.proto) e [suporte FrameTimeline a SurfaceView](https://perfetto.dev/docs/data-sources/frametimeline).

## Próximo gate proposto (PRE700, não executado)

Retomar a medição específica da `SurfaceView` real do NFSMW com o coletor PRE690 já validado e a versão V51 intacta, em cena/condições controladas; não tentar substituir a medição do jogo pelas timelines `VRI` do Android. Se for considerada uma segunda coleta simultânea, validar clocks e correspondência entre timelines antes de atribuir latência a Vulkan, GPU ou compositor. Avaliar dados antes de autorizar qualquer patch/otimização.

**Restrições preservadas:** `io.github.nfsmwrecomp`, versionCode `51`, certificado permanente, resolução interna 1920×1080, cap do teste 60 FPS e alvo futuro 120, shaders/efeitos/física, touch/iPega PG-9076, saves e proteção térmica. Sem APK V52, sem rebuild, sem mudança de driver, sem ganho comprovado.
