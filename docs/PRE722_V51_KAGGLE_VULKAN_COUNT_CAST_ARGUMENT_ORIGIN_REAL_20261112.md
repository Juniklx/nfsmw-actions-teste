# PRE722 — V51 Vulkan: origem lexical do argumento da conversão `enabledExtensionCount` linha 535 (2026-11-12)

## Execução e integridade verificadas

- GitHub Actions [**43295701230**](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43295701230): `completed/success`; auditoria na fonte V51 autenticada com notebook Kaggle privado isolado `juniklx/nfsmw-pre722-v51-cast-arg-readonly`. Sem build ou patch.
- Artefato GitHub **13979377934**, nomes `PRE722_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE722_KAGGLE_REMOTE.json`, conteúdo idêntico, `status=PASS_PRE722_V51_CAST_ARGUMENT_ORIGIN_CLASSIFIED`, ZIP CRC `PASS`.
- [ZIP arquivado e conferido por download do Drive](https://drive.google.com/file/d/1MIisqA_GK4UyioUFM3YB-aRyQYlxS396/view): `NFSMW_PRE722_REAL_KAGGLE_VERIFIED_43295701230.zip`, **43.696 bytes**, SHA-256 `e741ee56d3b037f2dd375dd5a720dc3fdb4d972b41a0374c18783c550c283ade`.
- Proveniência da fonte Vulkan V51 `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp`, SHA-256 autenticado pelos PRE704/PRE706 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`; **não demonstra equivalência com o ELF da V51 assinada**.

## Resultado da auditoria lexical

| Linha/escopo | Fato confirmado por hash/regex | Limite |
|---|---|---|
| **535**, campo `enabledExtensionCount` | O argumento único da expressão compatível com conversão funcional para tipo inteiro **é um identificador simples**, SHA-256 `86c85370ee87c37522fc4c13dc46993675fd475d776fcdd58c65d9a2fcf81fc4`, idêntico ao argumento visto no PRE721. Não há aritmética/comparação/ternário dentro desse argumento. | Sem AST; valores e tipo C++ real não validados. |
| Antecedente **355** | **Única referência anterior textual** para esse identificador na faixa de linhas **250–534**. A linha contém operador de atribuição `=` e método `.size()`, sem tokens de mutação `clear/erase/resize/push_back/emplace_back` naquele mesmo trecho. Hash da linha `a85d680debecbe04fecbf381d8250053a10aa7c706e73c1176169130e5f4e478`. | A linha 355 pode relacionar o argumento a uma contagem obtida de `size()`, porém a coleção proprietária da chamada **não foi identificada**. |
| Linhas **485–534** | Nenhuma atribuição textual direta, incremento ou decremento ao identificador do argumento foi encontrada pelo analisador. | Não exclui alias, passagem por referência, alteração indireta ou trechos fora desse recorte. |
| Linha **501**, `ppEnabledExtensionNames` | Receptor de `.data()` identificado e validado com hash `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2`, igual ao vetor inicial já validado no PRE719. O argumento da linha 535 tem **identificador diferente**. | Diferentes identificadores não significam necessariamente objetos C++ independentes. |
| Atribuições de campos entre **499–537** | `enabledExtensionCount` apresenta atribuições textuais nas linhas **500 e 535**; `ppEnabledExtensionNames` na linha **501**, sem outra reatribuição textual direta nesse recorte. | Não comprova coerência entre o ponteiro, o comprimento e objetos em runtime. |

A validação automática confirmou `argument_is_simple_identifier=true`, `argument_preceding_occurrences_total=1`, `line501_pointer_source_matches_pre719=true`, `argument_matches_initial_names_vector=false`, `source_text_exported=false`, `private_identifiers_exported=false`.

**Não afirmar** que a segunda chamada `vkCreateInstance` utiliza necessariamente um tamanho atualizado, que existe contagem divergente ou que a linha 355 representa o mesmo vetor dos ponteiros. A auditoria não usou AST/CFG C++ real, execução Vulkan no Galaxy, prova de ELF de APK, nem identificou o conteúdo das extensões de runtime. `stale_pointer_bug_proven=false`, `count_mismatch_proven=false`, `actual_collection_size_or_runtime_value=NOT_VERIFIED`.

## Próximo gate PRE723

Investigar por hashes e padrões sanitizados o **receptor da chamada `.size()` da linha 355** e sua eventual igualdade lexical com o vetor que fornece `ppEnabledExtensionNames` na linha 501, além dos locais de mutação desse receptor até a linha 537. Distinguir tamanho do contêiner, flags de habilitação e contagem efetivamente passada ao Vulkan; não corrigir sem prova. Recomenda-se AST com headers autenticados se operacionalmente possível, senão `NOT_VERIFIED`.

**Preservação:** V51 instalada, `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Sem APK V52, sem alteração de fontes, shaders, resolução 1920×1080, qualidade gráfica, controles touch/iPega PG-9076, saves ou limites térmicos. **Nenhum ganho de FPS comprovado.**

**STATUS:** `PRE722_REAL_KAGGLE_PASS; COUNT535_SINGLE_SIMPLE_IDENTIFIER_ARG; ARG_LINE355_SIZE_ASSIGNMENT_CANDIDATE; COUNT535_ARG_DIFFERS_FROM_POINTER501_VECTOR; COUNT500_AND_535_ASSIGNMENTS_ONLY; POINTER501_ASSIGNMENT_ONLY; CPP_AST_RUNTIME_NOT_VERIFIED; V51_INTACT; NO_V52; NO_FPS_GAIN`.
