# PRE721 — V51 Vulkan: correspondência entre for 531, membro 532 e conversão na contagem 535 (2026-11-12)

## Execução e integridade

- GitHub Actions: [run **43291927672**](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43291927672), **completed/success**; notebook Kaggle privado e isolado `juniklx/nfsmw-pre721-v51-call-range-readonly`, usando as fontes autenticadas da V51 e receita PRE704/PRE99; nenhum build.
- GitHub artifact **13977671162**, arquivos `PRE721_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE721_KAGGLE_REMOTE.json`. Ambos conferidos e com relatório PRE721 `PASS_PRE721_V51_BOUNDED_CALL_RANGE_LINKAGE_AUDIT`; CRC ZIP `PASS`.
- [ZIP arquivado e lido novamente no Drive](https://drive.google.com/file/d/1lLR-ftdbJHXyrCtADBVENABW2FzZlkge/view), nome `NFSMW_PRE721_REAL_KAGGLE_VERIFIED_43291927672.zip`, **42.760 bytes** e SHA-256 **`73caf38329372625825509cffbd1c7489b2c5c28ebf2038ccc26f4a7bfc0e673`**. Fonte `vulkan_instance.cpp` já autenticada com hash SHA-256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`; não equivale a provar identidade da biblioteca assinada.

## Resultados verificados da auditoria lexical

| Âncora | Evidência validada | Limitação |
|---|---|---|
| `for` linha **531** | Receptor lexical/hash confirmado igual ao PRE720: `2e6d217b3f4a4491525e03b10a29c57b770c3ddc19148a50ffac044f8403f75a`. A variável do `for` foi isolada por hash `b0da28ada6e2f605fb8ee401c411ca8ed7b3c8b7a903ce1100f361b569808e22`. | Nenhuma identidade de objetos via alias, nenhum AST. |
| Referências prévias do receptor `for` 531 | **Cinco ocorrências** detectadas entre linhas 250 e 530, precisamente **360, 363, 368, 403 e 404**; a linha 360 contém token `map` ou `unordered_map`, a 403 contém `auto` ou `decltype` e `=`. | Token `map` não prova o tipo do receptor; regex não prova definição/declarador ou escopo efetivo. |
| Atribuição da linha **532** | Padrão `IDENT.MEMBER = false` reconhecido; SHA-256 do receptor igual ao da variável do `for` da linha 531. `access_is_dot=true`; `receiver_matches_loop_variable=true`; `rhs_is_boolean_false=true`. Hash do membro `16367aacb67a4a017c8da8ab95682ccb390863780f7114dda0a0e0c55644c7c4`. | A escrita ao membro é um candidato lexical, não prova de qual extensão/flag foi realmente desabilitada. |
| Contagem `enabledExtensionCount` linha **535** | Expressão com identificador à esquerda e um argumento dentro de parênteses, sem sufixo; o identificador corresponde a **grafia de tipo inteiro** segundo lista restrita do analisador: `callee_is_integer_type_spelling=true`. SHA-256 do identificador `b30614e9380070358db8cda08b5e33b4a2fa84a1ef0b4d7e728b21df4839e6f8`, argumento único SHA-256 `86c85370ee87c37522fc4c13dc46993675fd475d776fcdd58c65d9a2fcf81fc4`. | **Compatível com conversão funcional a tipo inteiro**, mas sem AST não declarar qual entidade sintática efetiva nem o valor convertido. Não é uma prova de chamada de função calculadora da contagem. |
| Argumento único de 535 | Não contém menção textual ao receptor nem à variável do `for` 531; não apresenta `obj.metodo(...)` ou `obj->metodo(...)` segundo extrator. | Pode referir outra variável de contagem ou expressão: origem do argumento **não resolvida**. |

**Interpretação conservadora:** PRE721 reduz a ambiguidade lexical do PRE720 e conecta com confiança textual o `for` 531 à atribuição `MEMBER=false` na linha 532. O valor atribuído a `enabledExtensionCount` na linha 535 parece envolver conversão para inteiro de um único argumento; não foi demonstrada relação causal com a mudança de flags, nem desacordo entre a contagem e `ppEnabledExtensionNames`.

## Confiabilidade e próximo gate

Não houve compilação, teste Vulkan runtime, APK V52, modificação da V51, leitura da chave de assinatura, alteração da assinatura, 1920×1080, shaders, efeitos, física, touch, iPega PG-9076, saves, limite de FPS ou limiares térmicos. `stale_pointer_bug_proven=false`; `real_extension_count_mismatch_proven=false`; `runtime_enabled_extension_count=NOT_VERIFIED`; `source_to_signed_elf_equivalence=UNVERIFIED`. **Nenhum ganho de FPS comprovado.**

**PRE722 sugerido:** investigar a origem textual e as operações associadas ao **argumento único da conversão na linha 535**: separar identificador simples, chamada/aritmética e relação com o total de nomes apontados por `ppEnabledExtensionNames`, sem exportar fonte privada e sem presumir habilitação runtime. Caso não haja toolchain e headers suficientes para AST, manter `NOT_VERIFIED`. Somente propor patch se aparecer evidência de defeito.

**STATUS:** `PRE721_REAL_KAGGLE_PASS; LOOP531_MEMBER532_FALSE_LEXICAL_LINK_CONFIRMED; COUNT535_INTEGER_TYPE_SPELLING_WITH_ONE_ARGUMENT; COUNT_ARGUMENT_ORIGIN_UNRESOLVED; NO_STALE_POINTER_BUG_PROVEN; SOURCE_SIGNED_ELF_UNVERIFIED; V51_INTACT; NO_V52; NO_FPS_GAIN`.
