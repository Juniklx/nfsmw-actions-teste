# PRE711 — ligações lexicais entre operandos Vulkan, for, c_str e push_back da V51

**Data:** 2026-11-12 (Bahia). **Gate aprovado:** `PASS_PRE711_AUTHENTICATED_BOUNDED_RELATIONSHIPS_READONLY`. Apenas auditoria de fonte autenticada; **não é AST/CFG, execução Vulkan no S24 FE ou demonstração de desempenho**.

## Execuções e preservação

- Primeira tentativa [GitHub Actions 43224913196](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43224913196): `completed/failure` no passo `Local syntax and synthetic gates`, erro de separação de aspas triplas e `def code` no gerador Python; não restaurou a fonte V51 nem iniciou Kaggle. Ajuste de formatação restrito ao gerador. Preservar para rastreabilidade.
- Reexecução [GitHub Actions 43225072682](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43225072682): `completed/success`, preflight de código aprovado, fonte autenticada, notebook privado **isolado** `juniklx/nfsmw-pre711-v51-operand-links-readonly` submetido e executado no Kaggle, JSON remoto conferido/arquivado. O notebook principal `juniklx/nfsmw` não foi executado.
- Resultado remoto: `completed_utc=2026-11-12T13:14:14.467467+00:00`; `stage=PRE711_V51_KAGGLE_OPERAND_LINKS_READONLY`; `analysis_type=PRE711_BOUNDED_SOURCE_OPERAND_LINKS_ONLY`; `pre711_operand_links.stage=PRE711_V51_BOUNDED_OPERAND_LINKS`, `authenticated_source_sha_checks=true`, `runtime_enabled_extensions=NOT_VERIFIED`.
- [ZIP real PRE711 no Google Drive](https://drive.google.com/file/d/17xx-38nXR-NAHKfRsLRdb7eCf8N1PT_Q/view), `NFSMW_PRE711_REAL_KAGGLE_VERIFIED_43225072682.zip`: **23.668 bytes**, SHA-256 `176de77e864d46a7c91d2188d6e43d389ae8733543a6fc698caf5c7fafbb1c92`, CRC ZIP PASS, SHA idêntico após leitura de volta do Drive. Artifact GitHub `13947413302`, contendo exclusivamente dois JSONs sanitizados, sem código-fonte completo, APK ou segredos. Backup do contexto anterior: [Drive](https://drive.google.com/file/d/1rUeaGb27KUSukBVa-74bXMEAavEsL0Uu/view).

## Evidências novas

A PRE711 reusa os hashes autenticados da V51 e **confere novamente as expressões** extraídas nas PRE708–PRE710 antes de analisar. Arquivos: `nativo/sdk/src/ui/vulkan/vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`; `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`. Receita do presenter `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`.

| Elemento | Dispositivo | Instância |
|---|---|---|
| `for` de intervalo | Linha 283: variável reconhecida, sem tipo C++ resolvido | Linha 445: variável com o **mesmo hash**, coleção de origem com hash distinto |
| `if` inicial | 286–288: `continue;` confirmado; `==` com lado esquerdo identificado por SHA | 448–450: mesma condição/hash; `continue;` |
| Operando direito de `==` | Contém `requested_extensions` | Também contém `requested_extensions`; hash igual |
| Objeto receptor de `->membro.c_str()` | O hash do **identificador lexical antes de `->`** coincide com o do lado esquerdo de `==` | Exatamente a mesma relação e hashes |
| Receptor `c_str` vs variável `for` | **Nomes textualmente diferentes**, `linked_to_for_variable=false` | **Nomes textualmente diferentes**, `false` |
| `if` negado | Começa com `!`; acesso a membro, sinal `<` ou `>`; não menciona diretamente `requested_extensions` nem a variável do laço | Mesmos indicadores textuais |
| `push_back` no segundo bloco | **0** | **1**; receptor **não é** `enabled_extensions`, `requested_extensions` ou variável do laço |

**Relação relevante:** hash lexical do operando esquerdo do `==` = hash lexical do identificador receptor de `->membro.c_str()`: `713c5af21cf990a57247175956dc7ec22f8806850c84b8b7ffc0c956f76f8a3e`. É evidência de **mesma grafia da expressão lexical identificada** no recorte; não prova que a variável mantenha o mesmo ponteiro/valor em runtime, pois o tipo, atribuições/aliases e fluxo completo não foram demonstrados. Hash do outro operando: `16623b1f061edee7d79f80f3212688aca49d97d2a39d4edcd363d4aee75eef70`; ele **contém** `requested_extensions`, mas a semântica do seu cálculo não foi totalmente resolvida.

O receptor de `c_str` usa acesso `->` e um membro cujo nome bruto foi intencionalmente omitido no JSON. A variável declarada no `for` tem o mesmo identificador/hash nas duas fontes, mas não é o receptor lexical do `c_str`. Os contêineres percorridos no `for` têm hashes diferentes nos arquivos, compatível com contextos separados de dispositivo/instância. `push_back` extra na instância escreve em um receptor diferente das três referências reconhecidas; o nome, os argumentos e o tipo C++ não foram divulgados nem provados.

**Interpretação:** O `continue;` está no primeiro bloco antes das inserções, e o primeiro predicado faz uma comparação `==` cujo lado direito contém `requested_extensions`. Isso sustenta um possível caminho de filtragem, **não comprova** quais extensões são solicitadas, negadas ou habilitadas. O segundo predicado continua sem semântica resolvida; `<`/`>` pode ser template.

## Limitações e próximo gate

- `pre711_operand_links.cpp_ast_or_cfg_proven=false`;
- `runtime_enabled_extensions=NOT_VERIFIED`;
- `installed_apk_binary_identity=UNVERIFIED`;
- `vk_google_display_timing_enabled=NOT_VERIFIED`;
- `source_exported=false`, `signing_material_accessed=false`, `apk_built=false`, `apk_modified=false`, `fps_gain_proven=false`.

**PRE712 proposta:** inspecionar somente leitura a atribuição ou alias entre variável de iteração do `for` e o identificador receptor usado no `==` / `c_str`, além do alvo de `push_back` e o membro/função da condição negada. Ser conservador com macros, sobrecargas, templates, inferência de tipo e lifetime: caso não sejam recuperáveis sem AST, retornar `NOT_VERIFIED`. Só depois decidir sobre uma build diagnóstica **nova, separada e assinada com certificado permanente**, com instrumentação dos nomes de extensões efetivamente passados ao Vulkan sem modificar o comportamento e com fallback seguro; nenhuma instrumentação foi aplicada agora.

**Baseline preservado:** V51 instalada, `io.github.nfsmwrecomp`, `versionCode=51`, certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, shaders/efeitos/física, touch/iPega PG-9076 e limites térmicos intactos. PRE702 informou `VK_GOOGLE_display_timing=ADVERTISED` no driver, mas não houve prova de habilitação na APK, timestamps ou ganho de FPS. **Sem V52.**

**STATUS:** `PRE711_KAGGLE_PASS_AFTER_LOCAL_SYNTAX_FIX; LEFT_EQ_IDENTIFIER_EQUALS_CSTR_RECEIVER_TEXT; RHS_REFERENCES_REQUESTED_EXTENSIONS; CSTR_RECEIVER_DIFFERS_FROM_LOOP_VARIABLE; INSTANCE_HAS_SEPARATE_PUSH_BACK; PREDICATE_RUNTIME_UNKNOWN; DRIVE_ZIP_CRC_SHA_PASS; V51_UNCHANGED; NO_V52; NO_FPS_GAIN`.
