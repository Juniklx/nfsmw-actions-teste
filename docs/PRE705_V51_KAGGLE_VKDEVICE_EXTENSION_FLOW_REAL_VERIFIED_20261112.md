# PRE705 — auditoria automática Kaggle da formação das extensões Vulkan V51

**Data:** 12/11/2026 (UTC). **Status verificado:** `PRE705_REAL_KAGGLE_EXTENSION_FLOW_INDICATORS_PASS`. **Escopo:** análise lexical contextual, sem medição runtime, sem APK ou patch.

## Execução e autenticidade

- [GitHub Actions run 43189687716](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43189687716), `completed/success`, todos os passos aprovados: sintaxe/testes sintéticos, replay de fonte autenticada PRE99/V51, gerador de notebook **Kaggle privado isolado**, `kernels push`, `kernels status`, retorno do relatório remoto por `kernels output` e validação final.
- Notebook `juniklx/nfsmw-pre705-v51-ext-flow-readonly`, `is_private=true`, `enable_gpu=false`, `enable_internet=false`. **Não executou** o notebook principal `juniklx/nfsmw`.
- Artefato GitHub `13930152078`, [ZIP copiado para Drive](https://drive.google.com/file/d/1svYeXzQUNrOYp8xJrIzwJNRqXR4wfXyd/view), `NFSMW_PRE705_REAL_KAGGLE_VERIFIED_43189687716.zip`, 10.954 bytes, SHA-256 `1c34c2eba0c9e2622a56d46d61185b94884b4e9e134373e0c891893423d68870`. ZIP CRC `PASS`; cópia do Drive baixada novamente e mesmo SHA-256; contém `PRE705_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE705_KAGGLE_REMOTE.json`.
- Relatório do notebook: `status=PASS_AUTHENTICATED_V51_DEVICE_EXTENSION_FLOW_INDICATORS_ONLY`, `github_run_id=43189687716`, `github_run_attempt=1`, `completed_utc=2026-11-12T09:16:09.311070+00:00`, `files_scanned=30`, `analysis_type=BOUNDED_LEXICAL_CONTROL_FLOW_INDICATORS_NOT_RUNTIME`.
- Os arquivos derivam da receita autenticada V51 PRE696/PRE704: hash PRE99 `af8e82e198d00656814477fd64b8cc791fada21d937c1aa1cc583e5d37768b39`; `vulkan_presenter.cpp` SHA `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`, `nfsmw_nativo_destinos.cpp` SHA `b70497df49440b469018e7ef7a0e007d39ab5df13aa979edc91f37e1d2d42385`. Fonte **não** provada idêntica à biblioteca `libmain.so` assinada.

## Resultados observados — somente fonte

| Arquivo V51 | Indicadores de código com linha |
|---|---|
| `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` (SHA `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`) | `VkDeviceCreateInfo` 58, 303; enumeração de extensão 267, 276; marcadores de adição de listas 291, 526; `enabledExtensionCount` 305, 567; `ppEnabledExtensionNames` 306, 569; `vkCreateDevice` 811; `vkGetDeviceProcAddr` 828, 836, 852 |
| `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp` (SHA `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`) | `VkInstanceCreateInfo` 487; `enabledExtensionCount` 500, 535, 639; `ppEnabledExtensionNames` 501, 641; `VK_ERROR_EXTENSION_NOT_PRESENT` 526; `vkCreateInstance` em 6 linhas |
| `nativo/sdk/include/rex/ui/vulkan/device.h` | `VK_KHR_swapchain` linha 237 |
| `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` | `vkGetDeviceProcAddr` 607, 609 |

Atribuições no `vulkan_device.cpp` analisadas por forma de expressão, **sem exportar código integral**:
- Linha **305**, `enabledExtensionCount`: `SIZE_CALL` (expressão na mesma linha, contém `.size()`).
- Linha **306**, `ppEnabledExtensionNames`: `ARRAY_DATA` (expressão na mesma linha, contém `.data()`).
- Linhas **567/569**: campos também presentes, mas `OTHER_OR_MULTILINE` na sonda — exige leitura focada para caracterizar de forma confiável.

`vulkan_instance.cpp`, linhas **500/501**, também apresenta `SIZE_CALL`/`ARRAY_DATA`, mas em um **`VkInstanceCreateInfo`** distinto. O SHA-256 das expressões de atribuição dessas linhas coincide com o das linhas 305/306 do dispositivo: isso demonstra texto da expressão idêntico, **não prova** identidade ou conteúdo da lista em tempo de execução.

Os 30 arquivos auditados não apresentam referência textual a `VK_GOOGLE_display_timing`, conforme contador agregado `0`. Isso, somado à PRE702 real reportada no telefone com `VK_GOOGLE_display_timing=ADVERTISED`, motiva instrumentação futura, **mas não demonstra** que a extensão esteja ou não habilitada no `VkDevice` instalado. O parser PRE705 só extrai padrões lexicais/contextuais e limites de ±12 linhas: não prova relações de chamada, execução, dataflow completo ou conteúdo efetivo da lista.

## Segurança e próximos passos

`source_or_apk_modified=false`, `signing_material_accessed=false`, `device_modified=false`, `runtime_vk_device_enabled_extensions=NOT_VERIFIED`, `runtime_timestamps_captured=false`, `fps_gain_proven=false`.

**PRE706 proposta:** auditar somente leitura a procedência dos elementos da lista habilitada em `VkDeviceCreateInfo`, com análise localizada de blocos e modos de falha de extensão opcional. Só então avaliar teste de `VK_GOOGLE_display_timing` na próxima release diagnóstica se justificado, com habilitação condicional e fallback (não modificar `MAILBOX` ou a cadência de apresentação). A APK V51 fica intacta; qualquer futura V52 precisa preservar pacote, certificado permanente, gráficos 1920×1080, física, controles/saves e proteção térmica.

**Status final:** `PRE705_REMOTE_KAGGLE_PASS; AUTHENTICATED_RECIPE_PASS; DEVICE_LIST_SIZE_DATA_SOURCE_INDICATORS; INSTANCE_AND_DEVICE_DIFFERENT_CREATE_INFOS; GOOGLE_TIMING_NAME_NOT_FOUND_IN_30_SOURCES; RUNTIME_NOT_VERIFIED; DRIVE_ZIP_SHA_CRC_PASS; NO_V52; NO_FPS_GAIN`.
