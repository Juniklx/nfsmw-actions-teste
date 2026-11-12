# PRE718 — Rastreio de `VkInstanceCreateInfo` e possível fallback Vulkan (2026-11-12)

## Evidências de execução
- GitHub Actions PRE718 [run 43284212530](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43284212530): **completed/success**, Kaggle privado `juniklx/nfsmw-pre718-v51-pointer-fallback-readonly`.
- Artefato GitHub `13974656360` contém `PRE718_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE718_KAGGLE_REMOTE.json`; saída da fonte real autenticada, com `status=PASS_PRE718_V51_CONSERVATIVE_RETRY_POINTER_AUDIT` e sem exceções internas.
- [ZIP arquivado no Google Drive](https://drive.google.com/file/d/1nDuQDyGHoCL1PLtGBuHFOKO6oxAl3sF6/view), nome `NFSMW_PRE718_REAL_KAGGLE_VERIFIED_43284212530.zip`, tamanho **37.132 bytes**, SHA-256 **`d11aa23b1fb7852821637d223bd882c53a9ae1e5d6f60ffe126dbfd7ca35c393`**, integridade ZIP e hash após readback preservados.
- Fonte de instância autenticada pelo hash exato `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`, derivada da receita autenticada PRE704 / PRE99 e não exportada em texto bruto.

## Resultados lexicais verificáveis na V51
- `vulkan_instance.cpp`, linha **500**: atribuição textual a `enabledExtensionCount` a partir de `IDENT.size()`. Linha **501**: atribuição a `ppEnabledExtensionNames` a partir de `IDENT.data()`. **O mesmo identificador de vetor é usado em ambos**, demonstrado por SHA-256 `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2`.
- Linha **525**: condição extraída contendo `VK_ERROR_EXTENSION_NOT_PRESENT`, `VK_ERROR_LAYER_NOT_PRESENT` e `||`, sem comprovação por CFG.
- Linha **528**: cabeçalho `for` de intervalo extraído; PRE717 conectou lexicalmente sua variável à escrita `*IDENT=false` da linha **529**.
- Linha **531**: segundo cabeçalho `for` de intervalo extraído. O nome `requested_extensions` não aparece literalmente nos cabeçalhos das linhas 528 e 531; isso não prova ausência de alias ou conexão indireta.
- Linha **535**: uma nova atribuição textual a `enabledExtensionCount` existe, mas o extrator não encontrou um receptor de método `.size()` no seu lado direito. Não inferir que o valor foi recalculado por `.size()` diretamente nessa linha.
- No intervalo **523–537**, a auditoria não encontrou nova atribuição textual a `ppEnabledExtensionNames`, nem operações lexicais `.push_back()` ou `.clear()` com o padrão rastreado. O código pode modificar estruturas indiretamente; isso requer investigação separada.
- `vkCreateInstance` em **523** e **537**: argumentos textualmente iguais já confirmados no PRE717. A identificação da variável de resultado para cada chamada não foi resolvida nesta auditoria (campos `instance_create_lhs.assignment_detected=false`).
- Correspondência entre o vetor de nomes inicial e operações de reconstrução no intervalo = **`NOT_VERIFIED`**. Também `real_memory_reallocation=NOT_VERIFIED`.

## Duas tentativas anteriores preservadas
1. [Run 43282944862](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43282944862): preparação autenticada e preflight aprovados, mas `kaggle kernels push` retornou HTTP 400. A reexecução foi feita com slug Kaggle reduzido; causa exata do HTTP 400 não foi comprovada.
2. [Run 43283479274](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43283479274): Kaggle completou e gerou JSON, porém `failure_type=NameError` dentro da sonda PRE718, por referência a módulo do gerador que não existia no notebook isolado; relatório não tinha `pre718_instance_retry_dataflow_audit` e permaneceu `PASS_PRE717`. [ZIP de falha preservado no Drive](https://drive.google.com/file/d/1GkPkvPIt6JlaP5fiaWmXYAgJZrbZAZpL/view), 17.241 bytes, SHA-256 `fd17c9256597f24f7270f5c685a350f055d7c6534474dec244be7335152c1feb`. Correção somente no gerador PRE718, commit `14931512eaf801e00cdf4fda8adf164914d47679`, substituindo a referência por caminho e SHA de fonte autenticados.

## Avaliação conservadora
Segundo a especificação Vulkan, quando `enabledExtensionCount` é maior que zero, `ppEnabledExtensionNames` deve apontar para um vetor válido de nomes de extensão. A ausência de uma nova atribuição textual de ponteiro entre 523–537 **não demonstra** invalidade do ponteiro, porque também não se demonstrou reallocation, alias real ou alteração da memória apontada. `stale_pointer_bug_proven=false`, `runtime_recovery_proven=false`, `full_cpp_ast_or_cfg_proven=false`, `actual_pointer_lifetime_proven=false`, `runtime_instance_extensions=NOT_VERIFIED`, `source_to_signed_apk_elf_equivalence=UNVERIFIED`.

**Sem APK V52**, nenhuma modificação da V51, credenciais/assinatura permanentes preservadas, sem acesso a chaves, sem alterações de 1920x1080, FPS/efeitos/física/PG-9076, sem bypass térmico e sem ganhos de FPS alegados.

## Próxima etapa sugerida — PRE719
Auditar lexicalmente, com escopo de controle mais amplo, o conteúdo das expressões entre 525–537 (especialmente o `for` 531 e o lado direito da atribuição de count em 535), rastrear mecanismos de mutação por índice/iterador/algoritmos e identificar aliases entre vetor de nomes, `ppEnabledExtensionNames` e `VkInstanceCreateInfo`. Priorizar Clang AST real **somente se** headers e toolchain autenticados puderem ser disponibilizados sem exportar código proprietário. Caso contrário, manter `NOT_VERIFIED`.
