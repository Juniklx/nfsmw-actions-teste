# PRE724 — Vulkan V51: condição de inclusão opcional e bloco lexical de retry (2026-11-12)

## Proveniência, tentativas e integridade

- **Primeira tentativa:** GitHub Actions [43301309571](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43301309571), `completed/failure`. O notebook Kaggle retornou JSON com `failure_type=KeyError`, `failure_phase=SOURCE_AUDIT` e status PRE723 herdado, **portanto PRE724 não foi validada**. Causa: a transformação do gerador trocou por engano uma referência a `report['pre723_size_receiver_identity_audit']` por `report['pre724_size_receiver_identity_audit']`, que não existia. O artefato foi preservado explicitamente como [PRE724_FIRST_ATTEMPT_NOT_APPROVED_43301309571.zip](https://drive.google.com/file/d/1v-KQtbWEJaisBdVHjX4nAdXueT3K1NqM/view), 22.388 bytes, SHA-256 `3d709304abc654c528587fb326ccbad6c90f9b0f5a8f74a58841c03a3c223ad6`.
- **Correção pontual do gerador:** commit `f4f67f715b1e06a0207f4ac2a4e7a27c8b74c3c9`, apenas o identificador da chave herdada. Nenhuma fonte do jogo alterada.
- **Execução aprovada:** GitHub Actions [43302155832](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43302155832), `completed/success`; Kaggle privado isolado `juniklx/nfsmw-pre724-v51-optional-retry`. Arquivo GitHub **13981114259**.
- **JSONs:** `PRE724_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE724_KAGGLE_REMOTE.json`, byte a byte idênticos, `status=PASS_PRE724_V51_OPTIONAL_RETRY_LEXICAL_AUDIT`. ZIP CRC `PASS`, **45.970 bytes**, SHA-256 **`0a65b85cc99fe48803329d253604c7934c162ddd49514b16b27f089335da56c5`**. [ZIP no Drive, baixado novamente para verificação](https://drive.google.com/file/d/1Z2QMuhV_vzL8rcfuzE91FLA7w-H2fGFE/view).
- Fonte autenticada: `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp`, SHA-256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04` (PRE704/PRE706). Não se demonstrou igualdade binária com a `libmain.so` da V51 assinada.

## Constatações verificadas — somente análise lexical, não AST/CFG

| Linha | Achado | Ressalva |
|---|---|---|
| **454–458** | `if` com negação e acesso a `->second`, escopo lexical abre em 454 e fecha em 458, envolvendo `enabled_extensions.emplace_back(...)` na **455**. | O `if` só é avaliado em runtime se o programa passar pelo trecho; nome/valor real da extensão não foi verificado. |
| **523** | Primeira chamada lexical `vkCreateInstance` após a inserção opcional no código-fonte. | Não prova que a inserção tenha sido executada ou que a chamada tenha retornado erro. |
| **525–538** | `if` de tratamento de erro, condição com `VK_ERROR_EXTENSION_NOT_PRESENT` e `VK_ERROR_LAYER_NOT_PRESENT`; abre chaves em 526 e fecha em 538. | Validação de escopo por contagem lexical de chaves; não por AST/CFG completo. |
| **535** | Dentro do escopo, única atribuição textual a `enabledExtensionCount` entre as duas chamadas `vkCreateInstance`; usa conversão funcional do identificador obtido de `enabled_extensions.size()` na 355 (PRE722/PRE723). | Valor concreto do campo e integridade do ponteiro não medidos. |
| **537** | Segunda chamada `vkCreateInstance`, lexicalmente dentro do bloco condicional da linha 525. | **Não comprova que o retry foi realizado em runtime**. |

Outras verificações:
- Os argumentos das chamadas em 523 e 537 têm o mesmo SHA-256 `6e6d4abda4348a13b95cb47349c5f5b338d05cf7edc03e03b7b3f73a7522d353`; igualdade textual não é igualdade de estado em runtime.
- Atribuições textuais diretas ao campo `enabledExtensionCount` entre chamadas: **[535]**. Ao campo `ppEnabledExtensionNames`: **nenhuma** entre 523 e 537.
- O receptor de `.size()` na 355, `.size()` na 500 e `.data()` na 501 permanece lexicalmente o mesmo `enabled_extensions` (hash `f996732e4a7287c4f12912a9aaedcff05bb02b1eda622f3cf2f980c9466a62c2`, conforme PRE723).
- O conjunto de operações diretas de mutação desse vetor no recorte 356–537 tem apenas o candidato `emplace_back` na 455, conforme a sonda limitada PRE723. Não exclui mutações indiretas.
- Um modelo **sintético Python**, com lista inicial de 2 elementos e terceiro elemento opcional, confirmou que a contagem original seleciona o prefixo de 2. Isso **não executa fonte real C++**, não usa Vulkan nem analisa Android.

## Interpretação e limites

A estrutura textual é **compatível com fallback**: inserção condicional de extensão, primeira chamada `vkCreateInstance` e, em erro de extensão/camada, restauração da contagem original e segunda chamada com o mesmo objeto `VkInstanceCreateInfo` presumido lexicalmente. O ponteiro originalmente obtido de `.data()` não é reatribuído diretamente entre as chamadas. Como o contador controla quantos nomes são lidos a partir do ponteiro, um prefixo de extensão pode ser intencional e válido. **Não inferir defeito nem correção necessária apenas desta organização textual.**

Não foi confirmado: tipo/escopo C++ por AST real, ordem e valor de extensões executadas, se `vkCreateInstance` falhou, se retry ocorreu no Galaxy, tipo/permanência dos ponteiros, flags Vulkan, habilitação de `VK_GOOGLE_display_timing` ou qualquer melhoria de FPS. `stale_pointer_bug_proven=false` e `extension_count_mismatch_proven=false`.

## Próximo gate PRE725

Identificar em fonte autenticada (sem publicar seu texto ou identificadores privados) **qual extensão/condição está associada ao `emplace_back` 455**, se ela é extensão de *instância* ou de *dispositivo*, e se a própria condição dá suporte a uma política de fallback. Reavaliar o valor da inspeção lexical ante a necessidade de dados Vulkan runtime no S24 FE; se a validação pedir AST real, exigir toolchain/headers autenticados e não chamar regex de AST. Não gerar patch sem bug identificado.

**Preservação:** V51 Android `io.github.nfsmwrecomp` (`versionCode=51`), SHA-256 do certificado permanente `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`. Sem V52, modificação de fontes, assinatura, gráficos (1920×1080, shaders, efeitos), física, touch, iPega PG-9076, saves, limite de FPS ou proteções térmicas. **Nenhum ganho de FPS comprovado.**

**STATUS:** `PRE724_REAL_KAGGLE_PASS_AFTER_ONE_KEY_FIX; OPTIONAL_EMPLACE455_INSIDE_IF454; VKCREATE523; IF525_HAS_TWO_VK_ERROR_CLASSES; COUNT_RESET535_AND_RETRY537_INSIDE_IF525; POINTER_FIELD_NOT_REASSIGNED_DIRECTLY; SYNTHETIC_PREFIX_ONLY; REAL_CPP_AST_AND_RUNTIME_NOT_VERIFIED; NO_PROVEN_VULKAN_BUG; V51_INTACT; NO_V52; NO_FPS_GAIN`.
