# PRE707 — análise somente leitura dos filtros próximos à inserção de extensões Vulkan V51

**Data UTC:** 2026-11-12. **Gate remoto:** `PASS_AUTHENTICATED_V51_EXTENSION_SELECTION_SITES_LEXICAL_ONLY`. **Não é habilitação de extensão Vulkan nem execução da APK.**

## Execução e origem

- [GitHub Actions run 43208095222](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43208095222) `completed/success`: testes sintéticos, obtenção e autenticação da receita V51 no runner GitHub, gerador e `kaggle kernels push` para notebook **privado isolado** `juniklx/nfsmw-pre707-v51-ext-guards-readonly`, execução e recuperação do relatório remoto, validação final.
- Notebook principal `juniklx/nfsmw` **não executado**. GPU e internet desativadas no notebook isolado. Nenhum patch, build, APK ou segredo de assinatura acessado.
- [Relatório real ZIP no Google Drive](https://drive.google.com/file/d/1k2kTpbuCdIpluS-kgYi-a3-mB7HWYWyQ/view) `NFSMW_PRE707_REAL_KAGGLE_VERIFIED_43208095222.zip`, **15.192 bytes**, SHA-256 **`5b88ce4bff2f820b51bed80f96846cde3d217e3786e89bad00615cf1741c3d46`**, ZIP CRC PASS, download de conferência Drive com o mesmo SHA, dois JSONs sanitizados. Artifact GitHub `13938948296`.
- JSON do Kaggle: `github_run_id=43208095222`, `github_run_attempt=1`, `completed_utc=2026-11-12T11:21:03.619683+00:00`, `status=PASS_AUTHENTICATED_V51_EXTENSION_SELECTION_SITES_LEXICAL_ONLY`, `files_scanned=30`; campo `analysis_type=PRE707_LEXICAL_INSERTION_AND_NEARBY_CONTROL_INDICATORS`.
- Receita autenticada V51 obtida via PRE99/PRE431/PRE638/PRE648 e hashes fixos dos arquivos Vulkan, conforme PRE704/705/706. **Equivalência byte a byte com `libmain.so` assinada: `UNVERIFIED`.**

## Evidências estruturais verificadas

| Arquivo autenticado | Laço próximo | Condição `if` imediatamente anterior | Inserção no contêiner | Destino de create-info |
|---|---:|---:|---:|---|
| `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` | `for` 283 | `if` 290 | `enabled_extensions.emplace_back(...)` 291 | `enabledExtensionCount` 305, `ppEnabledExtensionNames` 306 |
| `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp` | `for` 445 | `if` 454 | `enabled_extensions.emplace_back(...)` 455 | `enabledExtensionCount` 500, `ppEnabledExtensionNames` 501 |

- No caminho do **dispositivo**, `vkEnumerateDeviceExtensionProperties` aparece nas linhas 267 e 276; `VkExtensionProperties` 275 e 283; identificados `if` 269, 274, 276, 286, 290 e `for` 283. `if` 290 apresenta operador de comparação textual, mas operandos não foram resolvidos.
- No caminho da **instância**, `VkExtensionProperties` aparece na linha 445; identificados `if` 432, 440, 448, 454 e `for` 445. `if` 454 também apresenta operador de comparação textual, sem resolução dos operandos.
- As duas inserções usam `emplace_back`, com hash SHA-256 igual para o texto do argumento (**`eb7fdf5fcfe59f0604026b046733e16b6e11cf6889f2876c4c2a6d26703ce01f`**); classificador devolveu `COMPLEX_OR_MULTILINE` e não demonstrou identidade dos valores runtime.
- Nenhum literal `VK_GOOGLE_display_timing` encontrado nos arquivos auditados nas PRE703–707; PRE702 do usuário indicou anúncio pelo driver Xclipse 940. O anúncio é distinto de solicitação ou habilitação em `VkDevice`.

**Limite da PRE707:** os `if` e `for` foram identificados por proximidade de linha, **sem AST ou análise de aninhamento**. Não provar que o `if` 290 ou 454 guarda de fato `emplace_back`, nem quais condições, cadeias de chamada, opções/fallbacks, argumentos reais ou extensões resultantes. O relatório declara `scope=LEXICAL_PROXIMITY_ONLY_NO_CPP_AST`, `filter_semantics_proven=false`, `complete_dataflow_proven=false`, `runtime_enabled_extensions=NOT_VERIFIED`, `vulkan_device_creation_success=NOT_INFERRED`, `fps_gain_proven=false`.

## PRE708 — próximo gate seguro

Investigar **somente por leitura** o significado dos operandos dos `if` nas linhas 290/454 e a expressão passada a `emplace_back`, através de resumos estruturais sanitizados da fonte V51 com SHA e, se viável, análise de escopo/braces que diferencie condição efetiva de simples vizinhança. Determinar se o código escolhe extensões por lista de desejadas, por lista anunciada ou outra condição **sem afirmar runtime**. Depois estudar fallback opcional de `VK_GOOGLE_display_timing`, ainda sem patch.

**Base preservada:** APK instalada V51 `io.github.nfsmwrecomp` `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. 1920×1080, cap da medição PRE700 60 FPS (meta de até 120), gráficos/shaders/efeitos/física, touch/iPega PG-9076, saves, proteção térmica. **Nenhuma V52 compilada ou ganho de FPS provado.**

**STATUS FINAL:** `PRE707_REAL_KAGGLE_PASS; AUTH_SOURCE_V51_PASS; DEVICE_IF_290_NEAR_EMPLACE_291; INSTANCE_IF_454_NEAR_EMPLACE_455; SAME_ARGUMENT_TEXT_SHA; FILTER_SEMANTICS_UNPROVEN; RUNTIME_EXTENSIONS_NOT_VERIFIED; NO_V52; NO_FPS_GAIN`.
