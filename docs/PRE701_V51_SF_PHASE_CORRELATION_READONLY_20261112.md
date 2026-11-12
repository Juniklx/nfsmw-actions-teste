# PRE701 A — V51/SurfaceView: auditoria de fase dos três timestamps, sem APK

**Data:** 2026-11-12. **Status:** `PRE701_REAL_SAME_SESSION_OFFLINE_PASS`; `PRE701_SYNTHETIC_10_PASS`; `NO_CAUSALITY`; `NO_V52`.

## Dados reais reutilizados

Evidência: arquivo **privado** `nfsmw3.zip`, SHA256 `fc09b22f46d4ac74d8582bd09dd884c53b4f361b3d6fec3684ccc64b11636a18`, coletado no S24 FE, APK `io.github.nfsmwrecomp` versionCode **51**, driver **SamsungProprietary** e Vulkan Xclipse 940, resolução interna **1920×1080**, cap **60 FPS**, tela 120Hz. A PRE700 já verificara CRC/hashes e uma só `SurfaceView` avançando. A PRE701 analisou a mesma captura, sem teste novo no telefone, código nativo ou mudança de configuração.

2.279 quadros únicos (triplas `desired/actualPresent/ready`), 2.278 intervalos; **uma lacuna de aquisição de 999,482344 ms excluída**, restando **2.277** intervalos contínuos. Cada intervalo foi classificado pelo múltiplo inteiro mais próximo de 8.333.333 ns da tela, sem inferir estado de CPU/GPU.

| Timestamp | 1 tick | 2 ticks | 3 ticks | 4, 5, 6 ticks | Irregulares (≠2 ticks) |
|---|---:|---:|---:|---:|---:|
| `desired` | 1 | **2.274** | 2 | 0 | **3** |
| `ready` | 60 | **2.158** | 59 | 0 | **119** |
| `actualPresent` | 246 | **1.788** | 240 | 3 | **489** |

Das **489** irregularidades de `actualPresent`, **459 (93,865%)** coexistiram com `ready` regular (2 ticks) e **487** com `desired` regular. Apenas **30** irregularidades simultâneas de `actualPresent` e `ready`; `ready` irregular com `actualPresent` regular ocorreu **89** vezes. Transições diretas `actualPresent` 1→3 ticks **122**, 3→1 **146** (268). Offset temporal por quadro `actualPresent−desired`: mediana **19,039961 ms**, p05 **14,629761 ms**, p95 **23,638086 ms**; não confundir offset com custo exclusivo de composição.

## Inferência permitida e limites

Há **desacoplamento temporal observável** entre cadência desejada/pronta e a apresentação efetiva. O sinal de irregularidade está mais forte no `actualPresent`, mas **a diferença não atribui culpa** ao SurfaceFlinger, à fila Vulkan, MAILBOX, Samsung, vblank virtual, GPU ou proteção térmica. `ready` não é um carimbo comprovado de `vkQueuePresentKHR`; `actual−ready` não é custo de serviço exclusivo. Não há ID unívoco Vulkan ↔ SurfaceFlinger, nem relógios calibrados com guest vblank; a PRE699 produziu eventos de janela `VRI` em vez de `SurfaceView`. Não há medida nova de FPS nem prova de otimização.

## Arquivos preservados

- [ZIP sanitizado Drive](https://drive.google.com/file/d/1fWouXVnLPDvmubkt664d9dD687xBkW1U/view) `NFSMW_PRE701_PHASE_A_SANITIZED_20261112.zip`, **8.397 bytes**, SHA256 `7c02065f7897b64afbbc7cd52a43f50f38b46c6bed3b124db42d89c2706b3c14`, CRC PASS.
- [Relatório Markdown Drive](https://drive.google.com/file/d/1I3RHJxrDY6up3GbRz3VufDngUqQEb866/view) `NFSMW_PRE701_PHASE_A_REPORT_20261112.md`, **5.650 bytes**, SHA256 `46ae753d2ef446ee67caf4c31a9cdbdb2338f25bbfb703bd5f7ff42826279a33`.
- ZIP inclui JSON real agregado (`PRE701_PHASE_A_REAL_AGGREGATES_20261112.json`, 1.850 bytes), analisador Python stdlib que exige hash do ZIP privado e valida manifestos, e **10 testes sintéticos** cobrindo pares 1/3, linha regular, lacuna, campos inválidos e ambiguidade. Os testes passaram localmente, **não em GitHub Actions nem no Galaxy**. Não publicar `nfsmw3.zip`, `nfsmw.log` ou frame-level dump no repositório.

## Próximo gate proposto: PRE702 (não executado)

Consultar sem modificar a APK se o **driver Vulkan de dispositivo realmente instalado** anuncia `VK_GOOGLE_display_timing` e/ou `VK_EXT_present_timing` junto a pré-requisitos de recursos. Android 17 descreve ambas, mas não garante que este driver as implemente. Se presentes e após avaliar overhead, discutir **instrumentação diagnóstica reversível em build separada** com IDs próprios e timestamps `CLOCK_MONOTONIC`, não utilizar FrameTimeline `BOOTTIME` como se tivesse mesmo epoch sem `ClockSnapshot`.

Fontes oficiais verificadas: [Android Vulkan frame pacing](https://developer.android.com/games/develop/vulkan/frame-pacing-extensions); [Vulkan VK_EXT_present_timing](https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_present_timing.html); [Perfetto clock sync](https://perfetto.dev/docs/concepts/clock-sync); [FrameTimeline](https://perfetto.dev/docs/data-sources/frametimeline).

**Preservar:** V51 instalada, package `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, opções gráficas/física, iPega/touch, saves, segurança térmica, e cap 60 na medição (meta futura 120 sem degradação). Não criar V52 ou declarar ganho de FPS.
