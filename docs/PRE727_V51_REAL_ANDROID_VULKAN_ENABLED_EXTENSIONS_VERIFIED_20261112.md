# PRE727 — V51: extensões Vulkan habilitadas conforme log real do aplicativo (2026-11-12)

## Resultado

**PASS_PRE727_V51_REAL_APP_REPORTED_VULKAN_EXTENSIONS.** Ao contrário das auditorias lexicais PRE703–PRE726, PRE727 usou um **log real preservado de execução no Galaxy S24 FE**. Um workflow GitHub Actions independente autenticou novamente o arquivo bruto no Google Drive por tamanho e SHA-256 antes de analisar as listas.

- [GitHub Actions 43309874406](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43309874406): **completed/success**; validação sintética do parser e avaliação do log real passaram.
- Fonte imutável: [NFSMW_V51_PRE656_LOG_ORIGINAL_20261110_085409_SHA649fbe98.log](https://drive.google.com/file/d/1u5FBEzB8Oi3xi1EH-iIar3aortJ2zrmd/view), **576.129 bytes**, **2.222 linhas**, SHA-256 **`649fbe98116b12ade8032b50267e78dcb251832cd8a566fb3d30380d37e325c7`**. Data do registro: **2026-11-10**, início **08:54:09**.
- O mesmo log já era identificado como V51, fornecido pelo usuário e auditado historicamente na PRE656 e corroborado no contexto PRE657. Isso fornece procedência; o novo procedimento não instala nem executa o jogo novamente.
- Artifact GitHub Actions **13984449722**: `NFSMW_PRE727_REAL_V51_ENABLED_EXTENSIONS_43309874406.zip`, **1.035 bytes**, SHA-256 **`9d5fd40b478eca6a7b2d31b1e9c8b732bd70454dd0585674eaeb4664a0ae1257`**, CRC íntegro, apenas JSON sanitizado. [Cópia no Drive com readback independente](https://drive.google.com/file/d/1V0-8L65bkwR4GsQ_Atb79MKwbAO7dQvf/view).
- Código da auditoria: [`automation/kaggle/pre727_verify_v51_existing_log_enabled_extensions.py`](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/automation/kaggle/pre727_verify_v51_existing_log_enabled_extensions.py), commit `68815d0ece46afbcefcb1a1ccecc41f8d67eace2`; [workflow](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/.github/workflows/nfsmw-pre727-v51-real-log-vulkan-enabled-extensions-readonly.yml), commit `ff3434a6da5b8fc5bf86026e96fb26ceb0ee41d7`. **GitHub Actions executou diretamente a leitura autenticada do Drive**, sem Kaggle, pois este gate analisa log já existente e não exige fonte privada, compilação ou notebook.

## Evidências verificadas no log original

`Vulkan instance API version 1.4.0. Enabled layers and extensions:` na **linha 35**:

| Linha | Nome reportado como extensão habilitada da instância |
|---:|---|
| 36 | `VK_KHR_surface` |
| 37 | `VK_KHR_android_surface` |
| 38 | `VK_EXT_debug_utils` |

`Enabled Vulkan device extensions:` na **linha 42**, após a identificação `Vulkan device 'Samsung Xclipse 940': API 1.3.304` na linha 41:

| Linha | Nome reportado como extensão habilitada do dispositivo |
|---:|---|
| 43 | `VK_EXT_extended_dynamic_state3` |
| 44 | `VK_EXT_memory_budget` |
| 45 | `VK_KHR_swapchain` |

As duas listas são **consecutivas**, delimitadas pelos cabeçalhos e pelas primeiras linhas posteriores sem o formato de extensão. O parser verificou exatamente uma ocorrência de cada cabeçalho, seis nomes sem duplicatas e nenhum texto `VK_GOOGLE_display_timing` em qualquer linha do log.

**Conclusão específica:** na sessão real PRE656 da V51, o jogo **não reportou `VK_GOOGLE_display_timing` como habilitada**. Segundo o resumo PRE702 fornecido pelo usuário, a GPU anunciava `VK_GOOGLE_display_timing=ADVERTISED`; são evidências distintas. Suporte anunciado pela GPU **não é prova de extensão ativada pelo jogo**. Em particular, não assumir que `vkGetPastPresentationTimingGOOGLE` estivesse disponível por essa extensão na V51.

## Limites e interpretação correta

- O relato `Enabled ...` foi **produzido pelo aplicativo** em uma sessão real, não por interceptação independente das estruturas `VkInstanceCreateInfo`/`VkDeviceCreateInfo` na chamada Vulkan.
- `requested_extensions` no runtime, seus ponteiros efetivos, retorno de ambas as chamadas Vulkan e equivalência byte a byte entre fonte V51 e ELF assinado seguem **NOT_VERIFIED**.
- A conclusão de ausência de `VK_GOOGLE_display_timing` refere-se à **lista reportada da sessão PRE656**; não afirmar estado em outras sessões, outros drivers ou versões.
- PRE702 tinha relatório de suporte de extensões a partir de `cmd gpu vkjson`; o JSON bruto não havia sido recebido para hash independente. A existência de suporte foi baseada no resumo do usuário, não em auditoria do binário Vulkan da sessão PRE656.
- Não houve teste de novo driver, alteração da APK V51, patch de fonte, shader, assinatura, modos gráficos, controles ou térmica; tampouco ganho de FPS ou correção de frame pacing. Naquela sessão V51 registrou resolução interna 1920×1080 e **cap real de 60 FPS**, diferente da meta de até 120 FPS.

## Próximo passo — PRE728

Não repetir a auditoria de alias ou habilitação de extensões conhecida. Avaliar tecnicamente **se os dados existentes de Perfetto/SurfaceFlinger (PRE700/PRE701) bastam para o próximo diagnóstico de frame pacing** ou se há necessidade justificável de medições por `VK_GOOGLE_display_timing`. Se esse caminho exigir habilitar extensão na criação do dispositivo, reconhecer que requer modificação controlada, nova build com **versionCode superior a 51**, mesma assinatura permanente e teste no aparelho — **não executar isso automaticamente sem um plano de equivalência e gate técnico**. Sem dados novos, não marcar feature como habilitada.

**Preservação integral:** `io.github.nfsmwrecomp`, V51 `versionCode=51`, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; 1920×1080 internos, gráficos/shaders/efeitos/física, touch, PG-9076, saves e proteções térmicas intactos. Sem V52 ou ganho FPS comprovado.

**STATUS:** `PRE727_REAL_V51_LOG_SHA_PASS; APP_REPORTED_ENABLED_INSTANCE_3; APP_REPORTED_ENABLED_DEVICE_3; VK_GOOGLE_DISPLAY_TIMING_NOT_IN_ENABLED_LIST_PRE656; PRE702_ADVERTISED_USER_REPORT_ONLY; NOT_DIRECT_VKCREATEDEVICE_INTERCEPTION; NO_APK_PATCH; NO_V52; NO_FPS_GAIN`.
