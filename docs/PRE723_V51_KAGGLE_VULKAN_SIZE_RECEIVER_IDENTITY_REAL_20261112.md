# PRE723 — V51 Vulkan: origem do tamanho de enabled_extensions, ponteiro e contagem de retry (2026-11-12)

## Execução e integridade

- GitHub Actions [**43299482411**](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43299482411) **completed/success**; notebook Kaggle privado isolado `juniklx/nfsmw-pre723-v51-size-receiver`; fonte real V51 autenticada pelo pipeline PRE704/PRE99; sem compilação, patch ou APK.
- GitHub artifact **13981890515**; relatórios `PRE723_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE723_KAGGLE_REMOTE.json` idênticos, `status=PASS_PRE723_V51_SIZE_RECEIVER_AUDIT`, ZIP CRC `PASS`.
- ZIP `NFSMW_PRE723_REAL_KAGGLE_VERIFIED_43299482411.zip`: **44.662 bytes**, SHA-256 **`439562f6a4983b5de0d032895780c70c27e1ccd1cb0d0f3a984a450c89e1fcf8`**, arquivado no [Drive e conferido por segundo download](https://drive.google.com/file/d/1Q5DNLmPjeFfdXLCL2JXNyKrsK_wkflnE/view).
- Fonte autenticada `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp`, SHA-256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`. **Não** comprova equivalência com ELF na V51 instalada/assinada.

## Resultados verificados exclusivamente por inspeção lexical/hashed

| Linha | Achado específico | Limite |
|---|---|---|
| **355** | O identificador alimentando a conversão de `enabledExtensionCount` em 535 recebe **diretamente** `enabled_extensions.size()`; `line355_size_is_direct_assignment_rhs=true`. Há exatamente um candidato de atribuição e um receptor `.size()`. | Tamanho numérico runtime não obtido; possível fluxo condicional não analisado por AST. |
| **455** | `enabled_extensions.emplace_back(...)`, única candidata de método mutador desse receptor localizada entre linhas **356–537** no recorte lexical. | Não demonstra se ramo foi executado em runtime, nem para qual nome de extensão. |
| **500** | `enabledExtensionCount` é calculado com `enabled_extensions.size()`, mesmo receptor textual de 355. | Valor real não observado. |
| **501** | `ppEnabledExtensionNames` recebe `enabled_extensions.data()`, mesmo receptor textual de 355 e 500. | Sem lifetime, tipo/reserva ou validade real de ponteiro confirmados. |
| **535** | `enabledExtensionCount` recebe a expressão compatível com conversão funcional para tipo inteiro do identificador simples cuja única atribuição textual antecedente (250–534) foi identificada em 355; ocorrências do identificador no recorte 355–537: **355 e 535**. | Sem análise de alias, efeitos indiretos, AST/CFG ou prova de que foi tomada a segunda chamada `vkCreateInstance`. |

Identidade textual confirmada:
- Hash SHA-256 do receptor `.size()` em **355**, de `.size()` em **500** e do receptor `.data()` em **501**: `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2`.
- `line355_size_receiver_matches_pointer501=true`, `line355_size_receiver_matches_line500_vector=true`, `line500_size_receiver_matches_pointer501=true`, `line355_size_receiver_matches_enabled_extensions=true`, `line355_size_receiver_matches_requested_extensions=false`.
- Quatro referências textuais ao receptor entre **355–537**: **355, 455, 500, 501**. Única candidata a mutação: **455**, `emplace_back`, sem atribuições diretas ao vetor nem mutação por subíndice detectadas.
- A variável intermediária usada em 535 conserva hash `86c85370ee87c37522fc4c13dc46993675fd475d776fcdd58c65d9a2fcf81fc4`, herdado do PRE722.
- `private_identifiers_exported=false`, `source_text_exported=false` no JSON Kaggle.

**Interpretação plausível, NÃO prova de fluxo efetivo:** o código salva a contagem de `enabled_extensions` em 355; mais adiante pode acrescentar uma extensão por `emplace_back` em 455; o primeiro `vkCreateInstance` pode então usar o tamanho completo obtido em 500; uma segunda tentativa pode restaurar a contagem inicial em 535 e usar somente um **prefixo** da lista via `.data()`. Esta seria uma estratégia possível de fallback intencional, não necessariamente um erro. A semântica de array/count do Vulkan favorece esta interpretação, mas a auditoria não observou nem comprovou os valores reais, a condição do retry ou a estabilidade do ponteiro.

**Sem confirmação**: equivalência fonte↔ELF da APK assinada, AST/CFG de C++ real, definição/tipo completo da coleção, endereço e lifetime de ponteiros, conteúdo das extensões habilitadas no Galaxy S24 FE, `VK_GOOGLE_display_timing` habilitado, erro de contagem ou ponteiro, alteração de FPS. `stale_pointer_bug_proven=false` e `extension_count_mismatch_proven=false` permanecem assim.

## Próximo gate PRE724

Determinar sob qual condição a mutação `emplace_back` da linha **455** ocorre e se é aplicada antes da primeira chamada `vkCreateInstance` 523; auditar o condicionamento e a separação de blocos de **523–537** para estabelecer se o par `count,data` da segunda chamada usa intencionalmente um prefixo da coleção, e testar a interpretação em **código sintético independente** antes de cogitar qualquer patch. Se houver headers reais e toolchain autenticados, preferir AST/CFG real; caso contrário, limitar a conclusão à lexicografia. Não alterar V51 sem defeito demonstrado.

**Preservação:** V51 Android `io.github.nfsmwrecomp` `versionCode=51`, assinatura permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Nenhuma V52 criada; nenhum patch, chave, configuração de 1920×1080, shaders, efeitos, física, touch, iPega PG-9076, saves, FPS limite ou proteções térmicas alterado. **Nenhum ganho de FPS demonstrado.**

**STATUS:** `PRE723_REAL_KAGGLE_PASS; SIZE355_EQUALS_ENABLED_EXTENSIONS_VECTOR_500_501_LEXICALLY; EMPLACE_BACK455_SINGLE_MUTATION_CANDIDATE; COUNT535_REUSES_SIZE_SNAPSHOT355; PREFIX_RETRY_HYPOTHESIS_ONLY; NO_CPP_AST_OR_RUNTIME; NO_PROVEN_COUNT_POINTER_BUG; V51_INTACT; NO_V52; NO_FPS_GAIN`.
