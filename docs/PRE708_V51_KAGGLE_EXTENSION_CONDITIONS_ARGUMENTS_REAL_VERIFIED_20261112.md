# PRE708 — V51 Vulkan: sintaxe de condições e argumentos de extensões (Kaggle real)

**Data:** 2026-11-12. **Status de auditoria autenticada:** `PASS_AUTHENTICATED_V51_CONDITION_ARGUMENT_SYNTAX_ONLY`; **não é prova de habilitação de uma extensão em `VkDevice` nem medição de FPS**.

## Execução e integridade

- [GitHub Actions run 43210595351](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43210595351), `completed/success`. Testes de sintaxe, autenticação da receita V51 (PRE99/PRE431/PRE638/PRE648), geração do notebook **privado isolado** `juniklx/nfsmw-pre708-v51-condition-syntax-readonly`, envio e execução Kaggle, recuperação do JSON remoto e validação final passaram. O notebook original `juniklx/nfsmw` **não foi executado**.
- Fonte autenticada com mesmos hashes das PRE704–707: `vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`, `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`, presenter SHA256 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`. Equivalência dessa receita à `libmain.so` assinada: **UNVERIFIED**.
- Kaggle remoto: `github_run_id=43210595351`, `github_run_attempt=1`, `completed_utc=2026-11-12T11:38:05.071831+00:00`, `stage=PRE708_V51_KAGGLE_CONDITION_ARGUMENT_SYNTAX_READONLY`, `status=PASS_AUTHENTICATED_V51_CONDITION_ARGUMENT_SYNTAX_ONLY`, `analysis_type=PRE708_BOUNDED_CONDITION_ARGUMENT_SYNTAX_ONLY_NOT_RUNTIME`.
- Relatório: [ZIP PRE708 real no Drive](https://drive.google.com/file/d/10lJqtUaF7jFit-u3ONX5Sgh6EBpfpIkn/view) `NFSMW_PRE708_REAL_KAGGLE_VERIFIED_43210595351.zip`, **16.700 bytes**, SHA256 `e41988008a803255013e6d5cb51822d09c4da8a6eec1421013e7729e5d00c0e7`; ZIP CRC PASS, SHA idêntico no readback Drive; artifact GitHub `13940124531`. Inclui dois JSONs sanitizados, não contém código-fonte integral, ROM, APK, credenciais ou senha.

## Achados lexical-estruturais

| Elemento | Arquivo `vulkan_device.cpp` | Arquivo `vulkan_instance.cpp` | Interpretação limitada |
|---|---|---|---|
| Condição inicial | linha **286**, SHA `855367983d6164c66714f83c60fc92c68271e1547283677fd01c76c7ec50fc2b` | linha **448**, mesmo SHA | expressão contém identificador `requested_extensions` e operador `==`; lista solicitada é uma pista, **sem fluxo de controle provado** |
| Condição posterior | linha **290**, SHA `6b69196d79db66e22ffbfb61aeee3d24bf1c539854803787e50ffa2a486caf78` | linha **454**, mesmo SHA | começa com `!`; parser coletou `>`, que **pode ser fechamento de template**, não comparação |
| Argumento de `emplace_back` | linha **291**, SHA `5e9aba2cc3ede92a6fe6f4c348054d73d72e6427d39c824b3e29aa7d3b66f9d9` | linha **455**, mesmo SHA | expressão contém chamada `c_str()`; o argumento concreto de runtime não foi recuperado |

- Quatro condições e dois argumentos foram extraídos pelo leitor de parênteses de escopo limitado (`bounded_expressions_extracted=true`). Isso permite comparar **texto de expressão** entre os dois arquivos sem divulgar conteúdo completo.
- **Não** confundir igualdade de SHA de expressão com identidade dos objetos/vetores. `enabled_extensions` é um contêiner local do dispositivo e outro da instância.
- As PRE706/707 encontraram as listas `enabled_extensions`, os `for` próximos (dispositivo linha 283; instância 445), `emplace_back` (291;455) e `enabledExtensionCount`/`ppEnabledExtensionNames` (`305/306` e `500/501`). PRE708 **não prova AST, guarda efetiva, alinhamento de blocos ou listas selecionadas**, e não resolve completamente os operandos.
- O driver Xclipse 940 anunciava `VK_GOOGLE_display_timing` no relatório de dispositivo PRE702 fornecido pelo usuário, enquanto a receita auditada ainda não a referencia explicitamente nos 30 fontes selecionados. Anúncio não prova solicitação/habilitação; não há timestamps Vulkan coletados.

## Limites e próximo gate

`pre708_conditions.cpp_ast_proven=false`, `guard_nesting_proven=false`, `device_extensions_requested=NOT_VERIFIED`, `device_enabled_extension_names=NOT_VERIFIED`, `runtime_vk_device_enabled_extensions=NOT_VERIFIED`, `source_to_signed_elf_equivalence=UNVERIFIED`, `fps_gain_proven=false`. Nenhuma APK, fonte compilada, driver, gráfico ou política térmica foi alterado.

**PRE709 proposta:** auditoria sem patch para esclarecer por que as condições mencionam `requested_extensions` e qual objeto fornece o argumento `c_str()`, com análise conservadora de escopo C++/blocos; evitar interpretar caracteres `>` de templates como operadores relacionais. Em seguida, avaliar se `VK_GOOGLE_display_timing` exigiria inserção condicional na lista com fallback e medição runtime, **não habilitar automaticamente**.

Preservar APK V51 (`io.github.nfsmwrecomp`, `versionCode=51`), certificado SHA-256 permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, shaders/efeitos/física, touch/iPega PG-9076, saves e proteções térmicas. Cap no ensaio PRE700 de 60 FPS; meta posterior de até 120 FPS. **Nenhuma V52 compilada, nenhuma melhoria de FPS comprovada.**

**STATUS:** `PRE708_REAL_KAGGLE_PASS; CONDITIONAL_EXPRESSION_HASHES_IDENTICAL; REQUESTED_EXTENSIONS_TOKEN_IN_FIRST_IF; NEGATED_SECOND_IF; EMPLACE_ARGUMENT_C_STR; TEMPLATE_GT_AMBIGUOUS; CPP_AST_NOT_VERIFIED; RUNTIME_EXTENSIONS_NOT_VERIFIED; NO_V52; NO_FPS_GAIN`.
