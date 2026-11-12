# PRE715 — tipos lexicais e precedência C++ no filtro Vulkan autenticado V51

**Data:** 2026-11-12 (Bahia). **Gate real:** `PASS_PRE715_AUTHENTICATED_SOURCE_CPP_PRECEDENCE_SEPARATE_EVIDENCE`. **Somente auditoria source-only; nenhum ELF/AST da aplicação real recompilado, nenhuma APK nova ou medição de FPS.**

## Execução comprovada e arquivos

- [GitHub Actions run 43268860669](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43268860669): **`completed/success`**. Testes locais e sintéticos, restauração/autenticidade da receita V51, submissão/execução do Kaggle **privado isolado** `juniklx/nfsmw-pre715-v51-types-precedence-readonly`, leitura/validação do relatório JSON e arquivamento completos. O notebook principal `juniklx/nfsmw` não foi executado.
- Resultado remoto: `stage=PRE715_V51_KAGGLE_TYPES_PRECEDENCE_READONLY`, `completed_utc=2026-11-12T17:24:53.542236+00:00`, `github_run_id=43268860669`; `pre715_type_precedence_audit.stage=PRE715_V51_CPP_PRECEDENCE_AND_DECLARATION_AUDIT`. Os 30 arquivos de fonte foram autenticados na cadeia PRE704–714.
- [Relatório ZIP no Drive](https://drive.google.com/file/d/1RWv7h2NL9BJ45REHj_PG34dg12Ani4Ct/view) `NFSMW_PRE715_REAL_KAGGLE_VERIFIED_43268860669.zip`: **30.322 bytes**, SHA-256 `62b34aee9d7aa13d9e015f5257f1d134e1bbda8b6f1981e9c72868acb5b0f233`, ZIP CRC PASS; após download de volta do Drive, tamanho, SHA e CRC coincidem com o original. GitHub artifact `13967611150`; contém apenas `PRE715_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE715_KAGGLE_REMOTE.json`, sem fonte C++ completa, APK, ISO/ROM ou credenciais.
- [Backup canônico antes da PRE715](https://drive.google.com/file/d/1YqB_d-_0Qf25H5YFOeFO51iwNIzK8ClB/view), preservado sem substituir histórico.

## Achados de fonte autenticada

| Evidência | `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` | `nativo/sdk/src/ui/vulkan/vulkan_instance.cpp` |
|---|---|---|
| Segundo `if` | Linha **290**, estrutura exata sob o regex conservador `! * IDENT -> second` | Linha **454**, mesma estrutura e SHA |
| Declaração `requested_extensions` no recorte | **Linha 155**, sintaxe `std::unordered_map<...>`, tokens de string/string_view e ponteiro para `bool` anteriores ao identificador, com SHA de linha `f39555a8ff9f7a09acb7cbcea0cbad1ecec1b51be5f7b57cafa591cf5bef53b6` | Entre 265–444 foram reconhecidas 11 referências, **nenhuma declaração tipada** pelo parser; isto não prova ausência em outra região, parâmetro ou header |
| Declaração contêiner de `push_back` | Não se aplica ao bloco | Linha **356** reconhecida lexicalmente como **`std::vector<...bool*> nome;`**, identificador tem **SHA idêntico** ao receptor do `push_back` da linha 456; padrão de declaração simples aprovado |
| Hash da condição | `6b69196d79db66e22ffbfb61aeee3d24bf1c539854803787e50ffa2a486caf78` | Mesmo SHA |

A análise conservadora de `vulkan_instance.cpp` encontra `type_has_bool_pointer=true`, `type_has_const_char_pointer=false`, `type_contains_pointer_syntax=true`, `has_semicolon_terminator=true`; nome do tipo e identificadores não permitidos **não foram exportados**. A linha 356 apresenta `std::vector` com elemento textual `bool*` e o **mesmo nome textual que recebe `push_back` em 456**. Isso é evidência substancial da natureza da coleção auxiliar da instância, mas **não comprova lifetime/ownership nem os valores apontados**.

Na fonte de dispositivo, uma declaração de `requested_extensions` na linha 155 foi associada a `std::unordered_map` contendo tokens `bool*` e string/string_view. Não se afirmou que o tipo C++ completo foi recuperado ou que a mesma declaração rege a instância, cujo prefixo pesquisado não identificou declaração tipada.

## Teste compilado: separar sintético de código real

No notebook Kaggle, havia um compilador C++ disponível e foi **compilado e executado de verdade** um exemplo fixo sem fonte proprietária, com estrutura `bool* second` e expressão `!*iterator->second`. O teste resultou em `SYNTHETIC_CPP_COMPILE_RUN_PASS` (família de compilador `gcc_or_other`): com booleano apontado igual a `false`, expressão verdadeira; com `true`, expressão falsa. A precedência do exemplo é **`!(*(iterator->second))`**. SHA-256 do fixture `932369e604739d9fb08ecb978a01e964ed3f17dc5a6264db8f5444508c29f6e3`. Isso **não equivale a compilar a fonte real, resolver templates/typedefs, inspecionar AST real ou provar execução da APK V51**.

## Restrições e próximo gate

`actual_source_ast_or_cfg_proven=false`, `actual_source_cpp_type_proven=false`, `runtime_enabled_extensions=NOT_VERIFIED`, `source_to_signed_apk_elf_equivalence=UNVERIFIED`, `vk_google_display_timing_enabled=NOT_VERIFIED`, `source_text_exported=false`, `secrets_accessed=false`, `apk_built=false`, `apk_modified=false`, `fps_gain_proven=false`.

**PRE716 sugerida:** confirmar o uso e os apontamentos do `std::vector<bool*>` na instância, incluindo a atribuição após `emplace_back` e a relação com `VkInstanceCreateInfo`, com análise fonte V51 autenticada; localizar no arquivo de instância a origem/tipo de `requested_extensions` fora do recorte de 180 linhas ou nas assinaturas de função/header, se seguro. Se um AST Clang real com includes autenticados não puder ser construído, registrar claramente `NOT_VERIFIED` em vez de inferir. Para verificar extensões realmente habilitadas e latência de apresentação é necessário gate de **instrumentação runtime separado**, não simplesmente esta sonda estática.

**Base preservada:** V51 instalada, `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução interna 1920×1080, shaders/efeitos/física completos, touch/PG-9076 e proteções térmicas. A extensão `VK_GOOGLE_display_timing` foi `ADVERTISED` em PRE702, não habilitada comprovadamente. Sem V52 e sem ganho de FPS comprovado.

**STATUS:** `PRE715_REAL_KAGGLE_PASS; DEVICE_REQUESTED_EXTENSIONS_UNORDERED_MAP_BOOL_PTR_DECL_LINE155_LEXICAL; INSTANCE_VECTOR_BOOL_PTR_DECL_LINE356_MATCHES_PUSHBACK_RECEIVER; SYNTHETIC_CPP_NOT_REAL_SOURCE_PRECEDENCE_VALIDATED; REAL_CPP_AST_NOT_VERIFIED; RUNTIME_NOT_VERIFIED; NO_V52; NO_FPS_GAIN`.
