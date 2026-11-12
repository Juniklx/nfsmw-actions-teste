# PRE719 — Rastreamento lexical de mutações e contagem Vulkan na V51 (2026-11-12)

## Execução, proveniência e integridade

- [GitHub Actions PRE719 #43287455419](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43287455419): **completed/success**. Kaggle privado isolado `juniklx/nfsmw-pre719-v51-pointer-count-readonly` executou o relatório `PRE719_V51_KAGGLE_VALIDATED_SUMMARY.json` com `status=PASS_PRE719_V51_BOUNDED_POINTER_COUNT_MUTATION_AUDIT`.
- GitHub artifact **13976066246**: `NFSMW_PRE719_KAGGLE_REMOTE.json` e `PRE719_V51_KAGGLE_VALIDATED_SUMMARY.json`; nenhum código-fonte completo, APK ou credencial exportado.
- [ZIP PRE719 no Drive](https://drive.google.com/file/d/1dQhKZbUzfRxucpWUVFjiIvRCmf_WD3XW/view): `NFSMW_PRE719_REAL_KAGGLE_VERIFIED_43287455419.zip`, **39.468 bytes**, **SHA-256 `3f812b9cd8825b67dbc8e9e20c177f909093563cd5a76ad453aa344df7b54c41`**; CRC passou; download de volta do Drive manteve tamanho e SHA. Origem: fontes V51 autenticadas com hash de instância `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`.

## Achados do intervalo de fonte `vulkan_instance.cpp` 523–540

| Verificação | Resultado |
|---|---|
| Chamadas `vkCreateInstance` | Linhas **523** e **537**, ancoradas pelo PRE717 |
| Cabeçalho `for` da linha **528** | Intervalo reconhecido lexicalmente; hash da coleção `46959009deed2c90f0a4d3c93c3bd4f86ded118c80c88fe5250138e3f3fe6fe7`, igual ao vetor `std::vector<bool*>` do PRE716 e **diferente** do vetor inicial de nomes de extensão `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2` |
| Cabeçalho `for` da linha **531** | Intervalo reconhecido lexicalmente, mas lado direito não é um identificador simples no extrator; coleção efetiva não resolvida |
| Atribuição `enabledExtensionCount` linha **535** | Existe. SHA-256 da expressão à direita `8f5964768424bf7699be0278af1d970200a0fe023d98e404d597bc761c528968`; padrão `identificador simples` = falso; sem `.size()`, subtração ou cast `static_cast` pelo extrator. Não reconstruir o valor por suposição |
| Atribuição de `ppEnabledExtensionNames` entre 523–537 | **Zero ocorrências lexicais** de `campo = ...` |
| Operações mutantes `.push_back`, `.erase`, `.clear`, `.insert`, `.resize`, `.reserve`, `.assign`, `.swap`, `.pop_back`, `.emplace_back` no intervalo | **Zero candidatos detectados pelos padrões**; não prova ausência de mutação indireta |
| Atribuições indexadas `identificador[...] = ...` no intervalo | **Zero candidatos detectados**; não prova ausência de outras formas de atualização |
| AST/CFG, tempo de vida dos ponteiros, execução | **Não verificados**. `pointer_validity_at_second_call=NOT_VERIFIED` e `effective_extension_count_at_second_call=NOT_VERIFIED` |

A conclusão defensável é restrita: o padrão de mutação explícita no intervalo não foi encontrado, e não se confirmou risco de ponteiro obsoleto, realocação, disparo efetivo do fallback ou contagem inadequada.

## Conservação da V51 e próximo gate

Sem nova APK, versão V52, alteração da assinatura permanente, acesso a chave, redução de 1920×1080, remoção de shaders/efeitos, mudança no iPega PG-9076, nos controles touch, física, save, ou política térmica. Sem ganho de FPS comprovado.

**PRE720 sugerido:** investigar a forma lexical precisa do segundo `for` (linha 531) e a categoria da expressão de `enabledExtensionCount` (linha 535): literal inteiro, membro, operador, chamada ou estrutura, sem exportar código-fonte ou inferir a validade de ponteiros. Preferir análise AST autenticada quando toolchain/includes reais estiverem disponíveis; de outro modo manter `NOT_VERIFIED`.

**STATUS:** `PRE719_REAL_KAGGLE_PASS; VECTOR_BOOL_PTR_LOOP528_HASH_MATCH; LOOP531_RANGE_RECEIVER_UNRESOLVED; COUNT535_NONTRIVIAL_RHS; NO_DIRECT_VECTOR_MUTATION_OR_INDEXED_ASSIGNMENT_523_540; NO_POINTER_REASSIGNMENT_523_537; POINTER_RUNTIME_NOT_VERIFIED; SOURCE_ELF_EQUIVALENCE_UNVERIFIED; V51_INTACT; NO_FPS_GAIN`.
