# PRE702 — sonda de extensões Vulkan no driver real, somente leitura

**Data:** 2026-11-12. **Status:** `PRE702_SCRIPT_LOCAL_BASH_SYNTAX_PASS; PRE702_14_MOCK_TESTS_PASS; PRE702_REAL_DEVICE_QUERY_PENDING`.

## Problema e estratégia

PRE701 A mostrou na mesma SurfaceView V51: 3/2277 intervalos irregulares de `desired`, 119/2277 de `ready` e 489/2277 de `actualPresent` (459 de `actualPresent` são irregulares quando `ready` é regular). A diferença é observacional e **não identifica** causa no driver/Vulkan/SurfaceFlinger. Antes de criar novo APK ou alterar MAILBOX, é necessário descobrir se a GPU real oferece feedback de apresentação por Vulkan.

A sonda PRE702 usa **`adb shell cmd gpu vkjson`**, um serviço Android usado por testes de conformidade AOSP (VTS/CTS), e interpreta `devices[].properties.deviceName`, `deviceType` e `devices[].extensions[].extensionName`. Evita `vulkaninfo` de Mesa no Termux, que pode enumerar somente CPU/SwiftShader em vez do driver Samsung. Exige `SM-S721B`, shell UID 2000, **exatamente um ADB autorizado**, `io.github.nfsmwrecomp` versão **51**. Aceita um único `deviceName` Samsung/Xclipse que não seja `deviceType==4` (CPU), e **falha fechada** para caso ambíguo, dados incompletos, JSON inválido ou serviço não disponível.

Extensões consultadas nominalmente: `VK_KHR_swapchain`, `VK_GOOGLE_display_timing`, `VK_EXT_present_timing`, `VK_KHR_present_id2`, `VK_KHR_present_wait`, `VK_KHR_present_wait2`, `VK_KHR_present_id` e `VK_EXT_calibrated_timestamps`. **Anúncio de extensão não prova feature bits, suporte operacional, habilitação pelo NFSMW ou timestamps reais.** O script deixa explicitamente `PRE702_EXT_PRESENT_TIMING_FEATURE_BITS=NOT_QUERIED` e `PRE702_NFSMW_ENABLED_EXTENSIONS=NOT_VERIFIED`.

## Artefatos verificados e persistentes

- [ZIP com script, README e 14 casos sintéticos (Drive)](https://drive.google.com/file/d/19rn7S8coBmkfyHgt1xX-c4LF2k6F023t/view): `NFSMW_PRE702_VKJSON_READONLY_TOOLS_20261112.zip`, **6.587 bytes**, SHA256 `3a2133aa9af6f7a66aff164cc7d472ba94fe56978fc88b5e95bf0f6415b5e8ec`, ZIP CRC PASS local.
- Script `nfsmw_pre702_vkjson_readonly.sh`, **5.685 bytes**, SHA256 `b0a59804e3beca13d2547cb1f4d86a9bae9d0eb9fcc3fa244922a4ee9693ad8c`. Embutido no ZIP, também fornecido no chat.
- [README separado Drive](https://drive.google.com/file/d/16WW-GaIqTLnWQSUhQoMMMv_8lFXuS-N3/view), **3.441 bytes**, SHA256 `029403a0f9044bfddd8c1fdb7bd081a89d9c01e6419fdd5e2a43379980c4c613`.
- `nfsmw_pre702_synthetic_tests.py`, SHA256 `e74863e912ff58f12d79d12e67dd1f5af2c895bd3ecd7db33283a951af74bbd4`. `bash -n` e **14 casos sintéticos** (aplicação mock, resultados de extensões presentes/ausentes, seleção de GPU física, versão/modelo/UID/ADB inválidos, somente software, JSON inválido, sem dispositivos, falta de extensões, hardware ambíguo, erro de serviço) aprovados localmente em grupos. **Não testados no Galaxy ou em Actions.**

## Gate real ainda pendente

Termux com ADB previamente funcional: conferir SHA256 do script, `bash <script> preflight` e `bash <script> capture`. A captura gera pasta `~/storage/downloads/NFSMW_PRE702/PRE702_...` e `PRE702_SUMMARY.txt` mais `PRE702_VKJSON_RAW.json`. Compartilhar apenas o SUMMARY inicialmente. RAW contém metadados de hardware e deve permanecer privado; não publicar no GitHub. Se Python 3 não estiver instalado, o script registra `RAW_ONLY_PYTHON3_MISSING` sem afirmar suporte. A consulta ao GPU service não inicia o jogo nem configura feature bits.

Se o hardware anunciar `VK_EXT_present_timing` e `VK_KHR_present_id2`, ainda será necessário consultar `vkGetPhysicalDeviceFeatures2` e recursos da Surface/swapchain; caso contrário, considerar somente `VK_GOOGLE_display_timing` se anunciada. Só então avaliar viabilidade de instrumentação diagnóstica reversível no código Vulkan autenticado da V51, clocks e overhead. Não correlacionar `CLOCK_MONOTONIC` com Perfetto `BOOTTIME` sem mapeamento.

## Fontes públicas consultadas

- [AOSP VTS usa cmd gpu vkjson](https://android.googlesource.com/platform/test/vts/+/3ab3cfe5264fef16d3829036b45f1399630e4b32/tests/gpu_test/src/com/android/gpu/vts/VulkanTest.java)
- [AOSP CTS lê extensões por extensionName](https://android.googlesource.com/platform/cts/+/95760bd0028d5a2e65e84d7fd29e275ae0d313e9/tests/tests/graphics/src/android/graphics/cts/VulkanFeaturesTest.java)
- [Android: Vulkan frame pacing extensions](https://developer.android.com/games/develop/vulkan/frame-pacing-extensions)
- [AOSP: Vulkan system loader](https://source.android.com/docs/core/graphics/implement-vulkan)

**Preservação:** V51 instalada `io.github.nfsmwrecomp`, cert permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução interna 1920×1080, cap 60 durante PRE700 e alvo máximo 120 em ensaios futuros, efeitos/shaders/física, touch/iPega PG-9076, saves, backups e proteções térmicas. **Nenhuma V52, build, alteração no jogo ou melhoria de FPS nesta etapa**.


---

## Resultado real do S24 FE (informado pelo usuário, 12/11/2026)

O usuário executou o script e compartilhou o conteúdo de `PRE702_SUMMARY.txt`. O resultado **é coerente com a saída do parser PRE702**, mas o `PRE702_VKJSON_RAW.json` original **não foi fornecido para conferir independentemente o SHA**. Assim, os números abaixo são **evidência real reportada pelo dispositivo**, sem promover a integridade do JSON bruto a validação independente.

- `PRE702_CAPTURE=PASS_GPU_DEVICE_EXTENSIONS_ENUMERATED`, fonte `ANDROID_SYSTEM_CMD_GPU_VKJSON`; `SM-S721B`, `io.github.nfsmwrecomp`, `versionCode=51`, `ADB_UID=2000`.
- `GPU_NAME=Samsung Xclipse 940`; `deviceType=1.0` (enum Vulkan **integrated GPU**, não CPU/SwiftShader); `vendorID=5197.0`; `driverVersion=104869891.0`; **165 extensões únicas** segundo o script.
- `VK_KHR_swapchain=ADVERTISED`; **`VK_GOOGLE_display_timing=ADVERTISED`**. A extensão GOOGLE depende da KHR swapchain e oferece `vkGetPastPresentationTimingGOOGLE` / `vkGetRefreshCycleDurationGOOGLE`.
- `VK_EXT_present_timing=NOT_ADVERTISED`, logo **não planejar a via EXT** neste driver. `VK_KHR_present_id2=ADVERTISED`, `VK_KHR_present_wait2=ADVERTISED`; `VK_KHR_present_wait=NOT_ADVERTISED`, `VK_KHR_present_id=ADVERTISED`; `VK_EXT_calibrated_timestamps=ADVERTISED`. **`present_wait2` não substitui feedback de `actualPresentTime` por quadro**.
- `PRE702_EXT_PRESENT_TIMING_FEATURE_BITS=NOT_QUERIED`, `PRE702_KHR_PRESENT_ID2_FEATURE_BITS=NOT_QUERIED`, `PRE702_NFSMW_ENABLED_EXTENSIONS=NOT_VERIFIED`, `PRE702_PRESENT_TIMESTAMPS=NOT_CAPTURED`.
- Reportado `PRE702_RAW_SHA256=f61716212d02d557838c03c7b7297fdc8977fe8454b032c8033f8d76bf995496`, `PRE702_RAW_BYTES=116765`. Esses dois valores são **manifesto informado pelo script, não readback externo conferido**.
- `PRE702_APK_OR_DEVICE_SETTINGS_MODIFIED=FALSE` e `PRE702_FPS_GAIN_PROVEN=FALSE`.

**Inferência técnica fundamentada na documentação oficial:** o caminho de diagnóstico preferível é **`VK_GOOGLE_display_timing`**, por seu suporte anunciado no driver. A funcionalidade real ainda exige habilitar a extensão no momento de criação de `VkDevice`, obter ponteiros de função e interrogar a swapchain. Não mudar `desiredPresentTime`/`MAILBOX` apenas por observar disponibilidade. Timestamps Vulkan no Android são `CLOCK_MONOTONIC`; não cruzá-los diretamente com FrameTimeline `BOOTTIME` da PRE699 sem mapeamento e associação de IDs.

**PRE703 proposta:** examinar a árvore ativa da receita V51 na Colab em **modo exclusivamente read-only** (hash exato de `vulkan_presenter.cpp`, locais de criação de device/swapchain e de `vkQueuePresentKHR`, ocorrência de `VK_GOOGLE_display_timing`), sem copiar a fonte integral, sem patches, build ou V52. A receita autenticada V51 tem SHA256 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48` para esse .cpp, mas a correspondência com a lib assinada permanece `UNVERIFIED`. A sonda PRE703 offline foi preparada localmente, com sete invariantes sintéticos aprovados; execução real Colab pendente.

Fontes oficiais consultadas: [VK_GOOGLE_display_timing](https://docs.vulkan.org/refpages/latest/refpages/source/VK_GOOGLE_display_timing.html), [vkGetPastPresentationTimingGOOGLE](https://docs.vulkan.org/refpages/latest/refpages/source/vkGetPastPresentationTimingGOOGLE.html), [VK_KHR_present_wait2](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_present_wait2.html), [Android Vulkan frame pacing](https://developer.android.com/games/develop/vulkan/frame-pacing-extensions).

**STATUS REAL:** `PRE702_REPORTED_DEVICE_ENUMERATION_PASS; GOOGLE_TIMING_ADVERTISED; EXT_TIMING_ABSENT; ACTUAL_VULKAN_TIMING_NOT_CAPTURED; REAL_JSON_RAW_NOT_INDEPENDENTLY_VERIFIED; NO_V52; NO_FPS_GAIN`.
