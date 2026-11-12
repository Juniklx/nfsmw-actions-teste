# PRE713 — Vulkan V51: `find`, sentinela `cend`, predicado negado e destino de `push_back`

**Data:** 2026-11-12. **Resultado:** `PASS_PRE713_AUTHENTICATED_V51_LEXICAL_FIND_SENTINEL`, **somente fonte autenticada, sem AST/CFG nem execução Vulkan no telefone**.

## Evidências de execução

- [GitHub Actions run 43251310836](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43251310836) `completed/success`. Autenticação da receita PRE99/PRE704 de V51, gerador PRE713, execução de notebook Kaggle privado isolado `juniklx/nfsmw-pre713-v51-find-sentinels-readonly`, recuperação do relatório remoto e verificação do JSON pelo workflow passaram. Notebook original `juniklx/nfsmw` não executado.
- JSON remoto: `github_run_id=43251310836`, `github_run_attempt=1`, `completed_utc=2026-11-12T15:47:34.503321+00:00`; `files_scanned=30`; `stage=PRE713_V51_KAGGLE_FIND_SENTINELS_READONLY`, `status=PASS_PRE713_AUTHENTICATED_V51_LEXICAL_FIND_SENTINEL`, `analysis_type=PRE713_BOUNDED_FIND_SENTINEL_NEGATION_PUSHBACK_ONLY`.
- [Relatório ZIP sanitizado no Google Drive](https://drive.google.com/file/d/10nu55RIypGJYxKLyI8XO9Jeal1T_KP4J/view) `NFSMW_PRE713_REAL_KAGGLE_VERIFIED_43251310836.zip`, **26.350 bytes**, SHA-256 `18f2f1d2017ceb295e725011c4b32b95d3438550b9d90ff65b4c0d0fd9ea9607`, CRC ZIP válido, SHA idêntico após recuperação do Drive; artifact GitHub `13960090114`. Contém apenas `PRE713_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE713_KAGGLE_REMOTE.json`, sem fonte bruta, APK, ROM ou segredos.
- Fontes V51 preservam fingerprints PIN das PRE704–712: `vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`; `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`; presenter SHA256 `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`. **Nenhum cotejo binário da `libmain.so` instalada realizado.**

## Achados técnicos delimitados

| Ponto de fonte autenticada | `VkDevice`, `vulkan_device.cpp` | `VkInstance`, `vulkan_instance.cpp` |
|---|---|---|
| `for` de propriedades | linha 283 | linha 445 |
| `requested_extensions.find(...)` | expressão anterior ao `if` 286, chamada de membro confirmada | expressão anterior ao `if` 448, chamada de membro confirmada |
| Argumento de `find` | menciona identificador da iteração e `extensionName`, acesso por membro; o conteúdo real não foi exportado | mesmos indicadores e SHA |
| Operando direito do `==` | **`requested_extensions.cend()` reconhecido lexicalmente** na condição 286 | **`requested_extensions.cend()` reconhecido lexicalmente** na condição 448 |
| Primeiro `if` | corpo 287–288 contém `continue;` | corpo 449–450 contém `continue;` |
| Predicado negado antes de inserir | linha 290; contém acesso `->`, `<` ou `>`, menciona alias; forma classificada `NEGATED_COMPLEX_OR_UNKNOWN` | linha 454; mesmos indicadores; sem callee reconhecido |
| `push_back` adicional | zero no bloco | um no bloco de inserção; **linha 356** contém uma referência anterior ao mesmo identificador, marcada `STD_CONTAINER_TYPE_TOKEN` |

O hash do inicializador `.find` é `b94b1b3f12bb9e8ac209527e3761a34130a056070054733d70511afff299f1cd` em ambos os caminhos. O SHA lexical do operando direito do `==` é `16623b1f061edee7d79f80f3212688aca49d97d2a39d4edcd363d4aee75eef70`; token `cend` é confirmado. O objeto receptor de `.find` corresponde nominalmente a `requested_extensions`, enquanto o argumento menciona `extensionName` da variável do laço. Junto ao `continue;`, **é forte evidência estrutural de um filtro por extensões solicitadas**, mas não substitui prova de tipos C++, sobrecargas ou caminhos alcançados em runtime.

A PRE713 **não reconheceu o callee da segunda condição negada**, que apresenta tokens `->` e `<`/`>`; classificada `NEGATED_COMPLEX_OR_UNKNOWN`. Esses caracteres não são prova de comparação relacional: podem fazer parte de templates C++. Não afirmar o predicado nem quais extensões ele permite.

O receptor da operação `push_back` da instância tem SHA textual `46959009deed2c90f0a4d3c93c3bd4f86ded118c80c88fe5250138e3f3fe6fe7`. Em vez da janela curta da PRE712 (nenhuma definição candidata), a busca no **prefixo integral anterior à chamada** encontrou **uma referência na linha 356**, com token de tipo de contêiner padrão C++, porém **não confirmou o tipo específico**, duração, alocação, conteúdo, nem o destino Vulkan final.

## Limites de segurança e próximo gate

`cpp_ast_and_cfg_proven=false`, `raw_source_exported=false`, `runtime_enabled_extensions=NOT_VERIFIED`, `source_to_signed_elf_equivalence=UNVERIFIED`, `vk_google_display_timing_enabled=NOT_VERIFIED`, `apk_built=false`, `apk_modified=false`, `secret_accessed=false`, `fps_gain_proven=false`. O anúncio `VK_GOOGLE_display_timing=ADVERTISED` em PRE702 não prova que a APK a requisitou ou habilitou. Nenhum timestamp Vulkan do jogo foi capturado.

**PRE714 proposta:** verificar, ainda só leitura, a **expressão C++ exata da segunda condição negada** e distinguir possíveis `std::` templates, método de par/iterator, função booleana ou operador `!`; e verificar na **linha 356** a espécie de contêiner de `push_back` e sua relação com `VkInstanceCreateInfo` sem exportar fonte privada. Se a classificação lexical continuar ambígua, usar AST/Clang com as dependências do SDK autenticadas ou registrar `NOT_VERIFIED`. Não habilitar `VK_GOOGLE_display_timing`, não criar V52 por suposição.

**Preservar:** APK V51 instalada, pacote `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, gráficos/shaders/física, touch/iPega PG-9076, saves e proteções térmicas. Não reduzir qualidade nem alterar `MAILBOX`; nenhum FPS ganho comprovado.

**STATUS:** `PRE713_REAL_KAGGLE_PASS; REQUESTED_EXTENSIONS_MEMBER_FIND; ARG_LOOP_EXTENSIONNAME; EQUALITY_RHS_REQUESTED_EXTENSIONS_CEND; FIRST_IF_CONTINUE; SECOND_IF_NEGATED_COMPLEX_UNRESOLVED; INSTANCE_PUSH_RECEIVER_REFERENCE_LINE_356_STD_CONTAINER; DRIVER_RUNTIME_NOT_VERIFIED; V51_INTACT; NO_V52; NO_FPS_GAIN`.
