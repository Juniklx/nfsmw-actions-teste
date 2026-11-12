# PRE706 — VkDevice/VkInstance: origem dos contêineres de extensões na receita V51

**Data:** 2026-11-12. **Resultado final autenticado:** `PASS_AUTHENTICATED_V51_EXTENSION_CONTAINER_PROVENANCE_INDICATORS_ONLY` (Kaggle remoto, auditoria somente leitura). A validação é **lexical/estrutural de fonte**, e não uma captura da lista habilitada no Android.

## Cadeia de execução e falhas preservadas

1. [Run 43192574595](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43192574595): origem autenticada e notebook Kaggle concluído, mas auditoria `FAIL_CLOSED` por `LookupError` na decodificação `utf8-sig` (codificação Python inválida). Relatório sanitizado preservado no [Drive](https://drive.google.com/file/d/1Y7ddAyrJdBReG95VAROi2aIO5Z3zIxR-/view), 5.499 bytes, SHA256 `f7b614965d9b20a0aac57d89d0042043142ab4afd55e637708f13e3859d936a5`; não foi falha da fonte V51. Corrigido para `utf-8-sig` e acrescido teste de regressão, commit `5ef95b6c0454ed455c0cc3fd1082b70fb054c47d`.
2. [Run 43193116985](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43193116985): `completed/success` para a sonda estrutural, mas a expressão de `enabledExtensionCount` **não foi resolvida** (`count_container_name=null`); `ppEnabledExtensionNames` identificou `enabled_extensions`. Não confundir gate genérico PASS com proveniência resolvida. JSON preservado no [Drive](https://drive.google.com/file/d/113d2RJ6SktNN7n9qQJ1ujH64vGoF-D0x/view), 13.200 bytes, SHA256 `aaf14b6241fe337ca62d061c2503e24bf93358558419ebba9a3b27753d0e18dd`. Acrescentado parser conservador de receptor `.size()` com cast e gate que exige correspondência de identificador `.size()/.data()` em cada arquivo, commits `04db04ffaa8de3087fdcaf3b5e545ec8e8ac39bd` e `338b036108614093f150313b9fd3d2a3892cbeaf`.
3. **[Run final 43193776062](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43193776062): `completed/success`**, testes sintéticos, autenticação V51, notebook Kaggle **privado isolado**, `kernels push`, `kernels status`, `kernels output`, validação do JSON e artifact. Notebook original `juniklx/nfsmw` não executado. O relatório confirmou as duas listas locais e a correspondência de receptores nos campos de criação.

### Preservação do relatório final

- Artifact GitHub ID `13931603547`, ZIP [NFSMW_PRE706_STRICT_REAL_KAGGLE_43193776062.zip no Drive](https://drive.google.com/file/d/1H-zBixyKHwCAtwl6Hs1eOAVRb5tTofGK/view), 13.634 bytes, SHA-256 **`dbb9f8f609d53fca260d5137388427a2a5d700882e13405c6b51afdc5c300ef3`**, ZIP CRC PASS e readback SHA idêntico. Contém `PRE706_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE706_KAGGLE_REMOTE.json`; não contém código-fonte bruto, ROM/ISO, APK nem segredos.
- JSON remoto: `stage=PRE706_V51_KAGGLE_DEVICE_EXTENSION_ORIGINS_READONLY`, `status=PASS_AUTHENTICATED_V51_EXTENSION_CONTAINER_PROVENANCE_INDICATORS_ONLY`, `github_run_id=43193776062`, `completed_utc=2026-11-12T09:43:29.854110+00:00`; `files_scanned=30`, `source_hashes_verified=true`; `complete_cpp_dataflow_proven=false`, `runtime_extension_list=NOT_VERIFIED`.
- Fonte da receita V51 autenticada pela cadeia PRE99, com presenter SHA256 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`; SHA de `vulkan_device.cpp`: `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`; SHA de `vulkan_instance.cpp`: `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`. Não há prova de igualdade binária com `libmain.so` da APK assinada.

## Achados estruturais

| Fonte V51 | Contêiner local | Origem/inserção (linha) | Contagem | Ponteiro usado no create-info |
|---|---|---|---|---|
| `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` | `enabled_extensions` | declaração com tipo visível **264**; `CONTAINER_ADD` **291** | `enabledExtensionCount` **305**, `.size()` | `ppEnabledExtensionNames` **306**, `.data()` |
| `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp` | `enabled_extensions` (outro contexto local) | `CONTAINER_ADD` **455** | `enabledExtensionCount` **500**, `.size()` | `ppEnabledExtensionNames` **501**, `.data()` |

Os receptores das chamadas `.size()` e `.data()` coincidem em **cada** arquivo, respectivamente. Isso não significa identidade entre os dois contêineres, nem define quais nomes entraram neles. A rotina reporta indicadores de linha e SHA, sem exportar código-fonte integral. `vkCreateDevice` aparece na linha **811** do arquivo de dispositivo; não afirmar relação de chamadas ou domínio de vida sem análise adicional.

**Limite central:** a PRE706 não reconstitui todos os caminhos de controle, condições, conteúdo dinâmico de `enabled_extensions` ou lista efetivamente habilitada na APK instalada. O relatório assinala `complete_cpp_dataflow_proven=false`, `runtime_vk_device_enabled_extensions=NOT_VERIFIED`, `runtime_timestamps_captured=false`, `fps_gain_proven=false`. O conjunto de 30 arquivos não contém referências lexicais a `VK_GOOGLE_display_timing`; o driver Xclipse 940 apenas **anunciou** suporte na PRE702 segundo relatório do usuário. Isso não prova habilitação nem causa dos intervalos de `actualPresent`.

## Próximo gate PRE707

Auditar **apenas por leitura** o filtro/condição que leva à inserção `enabled_extensions` em `vulkan_device.cpp` (trecho próximo de 264–306) e `vulkan_instance.cpp` (próximo de 455–501), sem exportar fonte ou chaves e sem inferir execução runtime. Distinguir extensões **anunciadas, solicitadas, aceitas e habilitadas**. Só considerar instrumentação diagnóstica reversível após fechar o fluxo de inicialização, fallback e detecção de suporte. Não mudar `MAILBOX`, pacing, cap FPS, gráficos, shaders, física, controles, saves, limites térmicos ou assinatura.

**Base preservada:** APK V51 instalada, `versionCode=51`, pacote `io.github.nfsmwrecomp`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, cap 60 FPS no ensaio PRE700 (alvo futuro até 120 FPS). **Nenhuma V52 compilada nem ganho FPS provado.**
