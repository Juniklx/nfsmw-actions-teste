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
