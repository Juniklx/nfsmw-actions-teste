# PRE704 — V51 VkDevice / extensão de apresentação, Kaggle automático: resultado real

**Data (UTC):** 2026-11-12. **Status:** `PRE704_REAL_KAGGLE_LEXICAL_AUDIT_PASS`; nenhuma build ou mudança no telefone.

## Evidência de execução

- [GitHub Actions run 43186999052](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43186999052), disparado pelo request `automation/kaggle/pre704_requests/pre704_20261112_v51_vkdevice_ext_readonly.json` e concluído `completed/success` (todos os passos, incluindo autenticação, kernel privado, polling e validação remota).
- [Workflow PRE704](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre704-v51-device-extensions-kaggle-readonly.yml) mantém notebook privado isolado `juniklx/nfsmw-pre704-v51-device-ext-readonly`, GPU/internet desabilitadas. **Não executou** o notebook principal `juniklx/nfsmw`.
- [ZIP real do Kaggle preservado em Google Drive](https://drive.google.com/file/d/1dLJJu7CASK6hHxPb0spb7GO0BuKL5ZpS/view), `NFSMW_PRE704_REAL_KAGGLE_VERIFIED_43186999052.zip`, **5.620 bytes**, SHA256 **`46eb9b4f57e77332a6a39602147b18674a97ae0369a26a2a35c718352a625a66`**, CRC ZIP PASS, hash de download de volta do Drive idêntico ao artifact GitHub `13927849680`. O pacote contém dois JSONs sanitizados, com conteúdo semântico idêntico; **não contém fontes, segredos, APK ou ROM**.
- JSON remoto: `stage=PRE704_V51_KAGGLE_DEVICE_EXTENSION_SOURCE_READONLY`, `status=PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_LEXICAL_ONLY`, `github_run_id=43186999052`, `github_run_attempt=1`, `completed_utc=2026-11-12T08:57:29.021263+00:00`, **30 arquivos** autenticados da receita, `source_to_signed_elf_equivalence=UNVERIFIED`.
- Cadeia de autenticidade: PRE99 SHA256 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`; presenter `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`; backend `b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385`. Verificados no runner e no relatório remoto. Não significam equivalência byte a byte da `libmain.so` assinada.

## Resultados técnicos: âncoras lexicais, não configuração runtime

| Arquivo da receita V51 | Âncora | Números de linha |
|---|---|---|
| `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` | `vkCreateDevice` | **811** |
| mesmo | `vkEnumerateDeviceExtensionProperties` | **267, 276** |
| mesmo | `ppEnabledExtensionNames` | **306, 569** |
| mesmo | `enabledExtensionCount` | **305, 567** |
| mesmo | `vkGetPhysicalDeviceFeatures2` | **405** |
| `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp` | `ppEnabledExtensionNames` | **501, 641** |
| mesmo | `enabledExtensionCount` | **500, 535, 639** |
| `nativo/sdk/include/rex/ui/vulkan/device.h` | `VK_KHR_swapchain` | **237** |
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | `vkQueuePresentKHR` / `vkCreateSwapchainKHR` | **10 linhas / 1871** |

Agregado dos 30 arquivos: `VK_GOOGLE_display_timing` **0**, `VK_GOOGLE_DISPLAY_TIMING_EXTENSION_NAME` **0**, `vkGetPastPresentationTimingGOOGLE` **0**, `VK_EXT_present_timing` **0**, `VK_KHR_present_id2` **0**. Outras contagens: `vkCreateDevice=1`, `vkEnumerateDeviceExtensionProperties=2`, `enabledExtensionCount=5`, `ppEnabledExtensionNames=4`, `vkQueuePresentKHR=11`, `vkGetDeviceProcAddr=11`.

**Interpretação precisa:** a PRE702 do usuário reporta `VK_GOOGLE_display_timing=ADVERTISED` no driver Samsung Xclipse 940. A PRE703/704 confirma que as fontes **pesquisadas** não usam explicitamente o nome da extensão nem a função de consulta. Porém o código pode construir listas genéricas ou importar extensões dinamicamente; a auditoria foi lexical e cobre um conjunto selecionado de 30 arquivos, **não demonstra que a extensão não esteja habilitada em `VkDevice` instalado ou que o driver seja culpado da cadência 8/25ms**. Requer leitura semântica das regiões acima, e depois verificação runtime/feature bits, se apropriado.

**Próximo gate proposto PRE705:** auditoria read-only dos blocos de criação/enumeracão de `VkDevice` em `vulkan_device.cpp`, `vulkan_instance.cpp` e, se necessário, no código de inicialização do jogo; registrar formação de vetores/listas de `ppEnabledExtensionNames` e relação instance-vs-device, sem patch, build ou acesso à assinatura. Só após isso considerar um diagnóstico reversível que habilite `VK_GOOGLE_display_timing` opcionalmente e consulte `vkGetPastPresentationTimingGOOGLE`, sem alterar `MAILBOX`/pacing original na experiência baseline.

**Preservação:** V51 instalada, `versionCode=51`, `io.github.nfsmwrecomp`, SHA256 do certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; resolução interna 1920×1080, cap observado de 60FPS (meta até 120), gráficos, shaders/efeitos/física, controles touch/iPega PG-9076, saves e proteção térmica. `runtime_vk_device_enabled_extensions=NOT_VERIFIED`, `runtime_timestamps_captured=false`, `fps_gain_proven=false`, `source_or_apk_modified=false`, `signing_material_accessed=false`.
