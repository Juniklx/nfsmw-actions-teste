# PRE720 — Classificação lexical do for 531 e RHS da contagem Vulkan 535 (2026-11-12)

## Execução e artefatos autenticados

- [GitHub Actions 43290032934](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43290032934) = **completed/success**; notebook Kaggle **privado e isolado** `juniklx/nfsmw-pre720-v51-range-rhs-readonly`, fonte V51 autenticada via receita PRE704 e PRE99. Artefato GitHub **13976588429**, contendo somente `PRE720_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE720_KAGGLE_REMOTE.json`.
- [ZIP PRE720 no Drive](https://drive.google.com/file/d/1MrdFPHzhrqADhBiZmyn1HEl1Fbz0KFMP/view): `NFSMW_PRE720_REAL_KAGGLE_VERIFIED_43290032934.zip`, **40.764 bytes**, SHA-256 **`e78ea6810d48e61da2276c84d4ab73debf7e21afd7702e0d9032171a62505030`**, ZIP CRC PASS, hash e tamanho coincidentes após readback do Drive.
- `status=PASS_PRE720_V51_RANGE531_COUNT535_LEXICAL_CLASSIFIED`; fonte `vulkan_instance.cpp` autenticada anteriormente por SHA-256 **`700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`**; nenhuma fonte C++ bruta, nome privado de identificador, APK ou credencial exportada.

## Achados verificáveis

| Âncora | Evidência na fonte autenticada | Limite |
|---|---|---|
| `for` linha **531** | Cabeçalho extraído e separado corretamente em declaração `lhs` e expressão de intervalo `rhs`, distinguindo `::` de `:`. **RHS é identificador simples**; hash SHA-256 `2e6d217b3f4a4491525e03b10a29c57b770c3ddc19148a50ffac044f8403f75a`. | Identificador **diferente** do vetor inicial que fornece `ppEnabledExtensionNames` (SHA `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2`). Não resolve identidade de objetos por alias, tipo real ou valores runtime. |
| Declaração do `for` **531** | Qualificação lexical de namespace `::`, referência `&`, sem token `auto` e sem *structured binding* `[a,b]`; hash sanitizado da declaração `42ed68e34a1c823890d7b9e86ae9e59d84b47daa1d04269560ea3ab1ec5419f3`. | Tipo C++ real não recuperado. |
| Corpo do `for` linha **532** | Detectados operador de atribuição `=` e acesso a membro `.` ou `->`; sem forma lexical de chamada `IDENT(` ou `if` nessa linha. | Atribuição a membro **candidata**, sem resolver objeto, campo, alias ou impacto no vetor de extensões. |
| Campo `enabledExtensionCount` linha **535** | RHS conserva SHA-256 `8f5964768424bf7699be0278af1d970200a0fe023d98e404d597bc761c528968` do PRE719. Categoria lexical **`function_or_method_call_shape`**, não identificador simples, nem literal inteiro, nem `.size()` explícito; também sem token `std::` ou `VK_`. | Uma expressão com `IDENT(...)` pode ser chamada de função **ou cast funcional em C++**; não afirmar callee real, operação ou valor efetivo da contagem. |
| Controle `for` linha **528** | RHS identificador simples (SHA `46959009deed2c90f0a4d3c93c3bd4f86ded118c80c88fe5250138e3f3fe6fe7`) diferente do RHS do `for` 531 e do vetor inicial de nomes. | Não comprova destino de flags `bool*` em runtime. |

**O que a auditoria não comprovou:** sem AST/CFG C++ real, lifetime de ponteiro, equivalência entre fonte e ELF da APK assinada, erro ou sucesso de `vkCreateInstance` runtime, identidade de extension set na V51, habilitação de `VK_GOOGLE_display_timing`, falha de ponteiro ou incompatibilidade real de contagem; marcadores conservadores `stale_pointer_bug_proven=false` e `extension_count_mismatch_proven=false`.

## Próximo gate PRE721

Investigar somente a assinatura textual e o argumento de `IDENT(...)` na linha **535**, cotejar com escopo e declaração antecedente do identificador usado na linha **531** e da atribuição de membro na **532**, por hashes sem exportar nomes ou código. Se AST real com headers e toolchain autenticados não for viável, manter `NOT_VERIFIED`. Não sugerir patch até identificar erro real e impacto na APK.

**V51 preservada:** Android `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`; nenhum build V52, alteração de assinatura, jogo, saves, 1920×1080, shaders, efeitos, física, controles, FPS limite ou proteção térmica. **Nenhum ganho de FPS demonstrado.**

**STATUS:** `PRE720_REAL_KAGGLE_PASS; LOOP531_RANGE_PARSER_FIXED; LOOP531_SIMPLE_IDENTIFIER_DIFFERENT_FROM_ENABLED_EXTENSION_VECTOR; LINE532_MEMBER_ASSIGNMENT_CANDIDATE; COUNT535_FUNCTION_OR_FUNCTIONAL_CAST_SHAPE; CPP_AST_RUNTIME_NOT_VERIFIED; NO_POINTER_BUG_PROVEN; V51_INTACT; NO_V52; NO_FPS_GAIN`.
