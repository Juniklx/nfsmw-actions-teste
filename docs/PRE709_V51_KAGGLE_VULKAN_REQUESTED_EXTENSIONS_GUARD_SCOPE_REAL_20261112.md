# PRE709 — escopo dos filtros Vulkan e referências requested_extensions na fonte V51

**Data:** 2026-11-12. **Resultado remoto:** `PASS_AUTHENTICATED_V51_EXTENSION_LOOKUP_GUARDS_LEXICAL_ONLY`. Escopo: fonte autenticada, leitura, indicadores textuais/braces; sem execução da APK ou prova de extensão habilitada.

## Execução verificada

- [GitHub Actions 43212432518](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43212432518): `completed/success`, com sintaxe e testes sintéticos, replay autenticado da receita V51, preparação e execução de notebook Kaggle **privado isolado** `juniklx/nfsmw-pre709-v51-guards-and-lookup-readonly`, download do JSON remoto e validação pelo workflow. Não executou `juniklx/nfsmw`.
- JSON: `stage=PRE709_V51_KAGGLE_EXTENSION_LOOKUP_GUARDS_READONLY`, `github_run_id=43212432518`, `completed_utc=2026-11-12T11:50:55.642238+00:00`, `files_scanned=30`, `status=PASS_AUTHENTICATED_V51_EXTENSION_LOOKUP_GUARDS_LEXICAL_ONLY`, `analysis_type=PRE709_BOUNDED_SOURCE_LOOKUP_AND_LEXICAL_SCOPE_ONLY`.
- Fontes autenticadas com os hashes das PRE704–708: `vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`, `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`, presenter `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`. Igualdade com `libmain.so` da APK instalada: **UNVERIFIED**.
- [ZIP real no Drive](https://drive.google.com/file/d/1DJha4D0CmpqS035RbTHznBlPR4ihDEaG/view) `NFSMW_PRE709_REAL_KAGGLE_VERIFIED_43212432518.zip`, **19.094 bytes**, SHA256 `bc898448a9034a8f1b8ff70844bb4829cd12d1bb02b10d7da18e1b07a43768ea`, ZIP CRC PASS, SHA idêntico no readback do Drive, artifact GitHub `13942256700`. Contém somente dois JSONs sanitizados.

## Escopo de chaves recuperado: evidência nova

| Arquivo | Primeiro if | Bloco lexical do primeiro if | Segundo if | Bloco lexical do segundo if | Linha emplace_back |
|---|---:|---|---:|---|---:|
| `vulkan_device.cpp` | 286 | 286–288: **não contém** a inserção 291 | 290 | 290–293: **contém** a inserção 291 | 291 |
| `vulkan_instance.cpp` | 448 | 448–450: **não contém** a inserção 455 | 454 | 454–458: **contém** a inserção 455 | 455 |

Resultado do parser de chaves e parênteses: `BRACED_LEXICAL_SCOPE_ONLY` para os quatro `if`; `brace_contains_target_line_start=false` nos primeiros blocos, `true` nos segundos. O parser mascara comentários e strings e recusa diretivas/macros em recorte; não é AST C++, não resolve `else`, macros nem valores runtime. **Não inferir do primeiro if a causa real de retorno/pulo ou o valor do predicado.**

- `requested_extensions` é mencionado nas linhas **285/286** do dispositivo e **447/448** da instância, com uso de membro e comparação `==` na primeira condição. O reconhecedor de `find/count/contains` não encontrou padrão explícito na expressão: `requested_extensions_membership_lookup=false`. Isso **não prova ausência de checagem** em outra função ou outra expressão.
- Segunda condição nas linhas **290/454** começa com `!`; sintaxe `<` e `>` continua ambígua como possível **template C++**, não operador relacional provado. Nomes operandos concretos ainda não foram resolvidos.
- Argumento em `enabled_extensions.emplace_back(...)` nas linhas **291/455** contém método `c_str()`. A expressão possui o mesmo hash em ambos os arquivos, mas **não permite identificar o objeto de onde vêm os bytes do nome sem resolver a expressão e o contexto de vida do objeto**.
- Comparação de expressões: 3/3 pares de hashes idênticos entre dispositivo e instância (primeira condição, segunda condição, argumento). Os contêineres de dispositivo e instância são distintos apesar da sintaxe similar.

## Limitações obrigatórias

`complete_cpp_control_flow_proven=false`; `full_cpp_semantics_proven=false`; `macros_and_unbraced_guards_exhaustively_resolved=false`; `runtime_enabled_extensions=NOT_VERIFIED`; `signed_apk_binary_equivalence=UNVERIFIED`; `fps_gain_proven=false`. A extensão `VK_GOOGLE_display_timing` foi anunciada pelo driver do S24 FE segundo PRE702, mas não há prova de solicitação/habilitação na APK V51 ou timestamps GPU.

## PRE710 — próximo gate proposto

Em fonte V51 autenticada, inspecionar **somente leitura**, com esquema sanitizado, o comportamento do primeiro bloco `if` (286–288 / 448–450), o objeto usado pela segunda condição negada e o receptor de `c_str()`, com classificação controlada de statements (por exemplo `continue` vs `return` vs outros), sem exportar código bruto ou concluir semântica além do evidenciado. Só considerar habilitação opcional de `VK_GOOGLE_display_timing` com fallback após compreender como `requested_extensions` é construída e testada; a primeira prova de habilitação exigiria instrumentação runtime autorizada em release diagnóstica separada.

**Base preservada:** V51 instalada `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, gráficos 1920×1080, shaders, efeitos e física, touch/iPega PG-9076, saves, restrições térmicas; cap 60 FPS no ensaio PRE700, objetivo futuro de até 120 FPS. **Sem V52 nem ganho comprovado.**

**STATUS:** `PRE709_REAL_KAGGLE_PASS; V51_SOURCE_AUTHENTICATED; FIRST_IF_BRACED_EXCLUDES_INSERT; SECOND_IF_BRACED_CONTAINS_INSERT; REQUESTED_EXTENSIONS_REFERENCES_FOUND; C_STR_ARGUMENT_FOUND; RUNTIME_UNVERIFIED; NO_V52; NO_FPS_GAIN`.
