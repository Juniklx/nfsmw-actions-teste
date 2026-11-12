# PRE712 — alias, predicado negado e push_back na receita Vulkan V51 autenticada

**Data:** 2026-11-12 (Bahia). **Status:** `PASS_PRE712_V51_AUTHENTICATED_BOUNDED_DATAFLOW_READONLY`.

## Evidência remota
- [GitHub Actions 43246107282](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43246107282): `completed/success`, inclusive autenticação de fonte V51, notebook privado Kaggle `juniklx/nfsmw-pre712-v51-alias-guards-readonly`, verificação do resultado remoto e upload do artefato.
- Kaggle reporta `completed_utc=2026-11-12T15:18:42.518136+00:00`; `stage=PRE712_V51_KAGGLE_ALIAS_GUARDS_READONLY`; `analysis_type=PRE712_BOUNDED_ALIAS_PREDICATE_PUSHBACK_LEXICAL_ONLY`.
- [ZIP sanitizado PRE712 no Drive](https://drive.google.com/file/d/1NY3kfKUUi_48y_5tUrxPt1oqyTD81wcf/view), 25.324 bytes, SHA256 `8c5f4d7da9eedcefc927191c286d564a46e67548eeec38ca72fcce3f24610426`, CRC ZIP válido, SHA recalculado após leitura do Drive; GitHub Artifact ID `13956752485`, dois JSONs (`NFSMW_PRE712_KAGGLE_REMOTE.json`, `PRE712_V51_KAGGLE_VALIDATED_SUMMARY.json`), sem exportar fonte C++, APK ou segredo.
- Antes de executar, foi criado [backup independente do CONTEXTO_NFSMW.md](https://drive.google.com/file/d/1E3yAftxdnwnqMWwm1eMldILlFL2_5AG8/view), preservando o ID canônico original.

## Achados delimitados

A PRE712 usa a mesma cadeia de autenticação PRE99/PRE704 e confirma novamente os hashes de receita V51 e os fingerprints anteriores PRE711. Fontes principais: `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38` e `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`.

| Sonda | Dispositivo | Instância |
|---|---|---|
| `for` / linhas anteriores ao primeiro `if` | 283–285 | 445–447 |
| Atribuição lexical do receptor de `==` e `c_str()` | **1 candidata**, declaração `auto` detectada perto | **1 candidata**, mesmos indicadores e hash |
| Inicializador | Contém chamada a **método `.find(...)`**, `requested_extensions` e variável do `for`; não chama `std::find` diretamente | Idêntico |
| SHA256 textual do inicializador | `b94b1b3f12bb9e8ac209527e3761a34130a056070054733d70511afff299f1cd` | Mesmo hash |
| Comparação `==`, lado direito | Refere-se a `requested_extensions`; teste por `.end()`/ `.size()` **não identificou** esses nomes exatos | Mesma estrutura/hash |
| Predicado do segundo `if` | Começa com negação `!` e **menciona o identificador encontrado anteriormente**; o leitor limitado **não reconheceu o callee** | Mesmo resultado |
| `push_back` no bloco de inserção | Nenhuma chamada | **1** chamada, receptor diferente do alias, variável `for`, `enabled_extensions` e `requested_extensions`; zero definições candidatas na janela local de 40 linhas pelo detector lexical |

A coincidência do inicializador nos dois arquivos sugere uma seleção de elemento por busca `.find(...)`, seguida de filtragem com `continue;`. **Não está provado**, pelo gate, qual o tipo do retorno da busca, qual o valor retornado, o significado do operando direito, o resultado efetivo do predicado negado, nem a semântica da chamada `push_back`. Zero declarações locais detectadas para seu receptor **não** prova ausência de declaração: pode estar fora da janela, ser membro da classe ou não corresponder ao padrão textual.

**Pontos de ambiguidade importantes:** o parser é lexical e limitado; o próprio relatório registra `cpp_ast_and_cfg_proven=false`, `cpp_symbol_binding=NOT_VERIFIED`, `cpp_alias_or_pointer_identity=NOT_VERIFIED`, `cpp_predicate_semantics=NOT_VERIFIED`, `destination_cpp_type=NOT_VERIFIED` e `runtime_enabled_extensions=NOT_VERIFIED`. A PRE711 já havia verificado igualdade do hash textual do operando esquerdo do `==` com o identificador à esquerda de `->membro.c_str()`, mas isso não é prova de lifetime nem identidade do ponteiro no Android.

## Próximo gate PRE713 proposto

Examinar `requested_extensions` e a operação `.find` com resolução conservadora de escopo (possível uso de `.cend()` ou outro sentinela, sem inferir sem inspeção), e ampliar a busca sanitizada da declaração do destino do `push_back` e do formato do predicado negado. Preferir AST/Clang quando houver ambiente comprovado e, caso contrário, marcar `NOT_VERIFIED` ao invés de adivinhar nomes. **Nenhuma V52 deve ser compilada por essa auditoria.**

**Proteções:** recipe V51 autenticada não é prova de equivalência exata com biblioteca `libmain.so` assinada; `installed_apk_binary_identity=UNVERIFIED`. Nenhuma alteração de APK, código, shader, 1920×1080, touch/iPega PG-9076, física, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b` ou limites térmicos. `VK_GOOGLE_display_timing` foi apenas anunciado pelo driver na PRE702; habilitação real, timestamps de apresentação e ganho de FPS seguem **não verificados**. Baseline: pacote `io.github.nfsmwrecomp`, `versionCode=51`, instalado/testado; sem V52.

**STATUS:** `PRE712_AUTHENTICATED_KAGGLE_PASS; AUTO_MEMBER_FIND_INITIALIZER_WITH_REQUESTED_EXTENSIONS_AND_FOR_VAR; EQ_ALIAS_HASH_RETAINED; NEGATED_PREDICATE_CALLEE_UNRESOLVED; INSTANCE_EXTRA_PUSHBACK_DESTINATION_TYPE_UNRESOLVED; SOURCE_ONLY; DRIVE_ZIP_SHA_CRC_VALID; V51_UNCHANGED; NO_V52; NO_FPS_GAIN`.
