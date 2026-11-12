# PRE710 — V51 Vulkan: corpo do guard e origem lexical de c_str (Kaggle real)

**Data:** 2026-11-12. **Gate:** `PASS_AUTHENTICATED_V51_GUARD_STATEMENTS_LEXICAL_ONLY`; **não comprova habilitação runtime, vínculo à libmain.so assinada nem ganho de FPS**.

## Execução verificada

- [GitHub Actions run 43219894609](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43219894609), `completed/success`. Testes locais de sintaxe e gates sintéticos, restauração e autenticação da receita de fonte V51, geração/execução do notebook Kaggle privado isolado `juniklx/nfsmw-pre710-v51-guards-and-lookup-readonly` e conferência do JSON remoto concluídos. Notebook original `juniklx/nfsmw` não executado.
- `github_run_id=43219894609`; `completed_utc=2026-11-12T12:45:32.156920+00:00`; `stage=PRE710_V51_KAGGLE_EXTENSION_LOOKUP_GUARDS_READONLY`; `analysis_type=PRE710_BOUNDED_GUARD_STATEMENTS_AND_CSTR_RECEIVER_ONLY`.
- Fontes da receita autenticada: `vulkan_device.cpp` SHA256 `24b04ab68d6300977756a1cb55a805b9654963696e7102af8ce1be4e9f072a38`; `vulkan_instance.cpp` `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`; presenter `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48`. Assinatura binária APK `libmain.so` **não comparada byte a byte**.
- Relatório ZIP: [NFSMW_PRE710_REAL_KAGGLE_VERIFIED_43219894609.zip no Google Drive](https://drive.google.com/file/d/1DOX5NT8nwKaLQxASWNbg2LaJabCwnKrF/view); **21.752 bytes**, SHA256 `9884cfca5e61a403432237d2c579e44078f1d0696230152da428df50a1c8508c`; CRC ZIP válido e readback Drive SHA idêntico. Artifact GitHub `13945733010`. Contém somente dois relatórios JSON sanitizados; sem código-fonte completo, APK, ROM ou segredos.

## Achados novos da análise somente leitura

| Estrutura | Dispositivo, `vulkan_device.cpp` | Instância, `vulkan_instance.cpp` |
|---|---|---|
| Laço lexical próximo | `for` baseado em intervalo, linha **283**, contém token `const`; tipo/variável de iteração não resolvidos | `for` baseado em intervalo, linha **445**, contém `const`; tipo/variável não resolvidos |
| Primeiro `if` | Condição na **286**, contém `requested_extensions` e comparação `==`; corpo **287–288** contém `continue;` | Condição na **448**, mesmo hash de expressão, corpo **449–450** contém `continue;` |
| Segundo `if` | Condição **290** inicia `!`; corpo **291–293** contém `emplace_back` e atribuição | Condição **454** igual textualmente; corpo **455–458** contém `emplace_back`, atribuição **e `push_back`** |
| Argumento inserido | `emplace_back` **291**, uma chamada `c_str()`; receptor lexical com dois identificadores ligados por acesso a membro; hash do receptor `8ea40e38cf1beaded3c63af2b84a862f1003f29a2c126a65a727fda9cb3154a1` | `emplace_back` **455**, mesma expressão e mesmo hash do receptor |
| Igualdade textual | Condições primeiro/segundo `if` e argumento de inserção têm SHA iguais entre os arquivos | Os corpos dos `if` e os laços não têm SHA idênticos; igualdade de flags não equivale a identidade do código |

A presença de `continue;` dentro do primeiro `if` é compatível com filtragem: se o ramo for percorrido em um laço C++, a iteração atual termina antes da inserção posterior. O escopo lexical PRE709 já mostrou que as inserções 291/455 estão dentro dos segundos `if`, não dos primeiros. **Ainda não temos AST/CFG completos nem valores dos predicados em execução.**

A primeira condição contém `requested_extensions` e `==`, mas a análise **não** reconheceu chamadas explícitas a `std::find`, `.find`, `.contains`, `.count` ou `.end` na expressão. Não presumir semântica exata de `==` sem ler seus operandos. A segunda condição começa com `!`, e símbolos `<`/`>` são ambíguos em C++ (possíveis templates ou operadores). Não inferir predicado de suporte sem identificar a função/método.

O argumento de `c_str()` foi refinado: **cadeia lexical de dois identificadores ligados por acesso a membro**, com mesmo SHA em ambos os arquivos. **Os nomes de receptor foram intencionalmente omitidos**; não está provada a propriedade/tipo/lifetime ou o valor da extensão. A operação `push_back` adicional no bloco da instância é um indício estrutural, não prova de qual coleção ou extensão ela manipula.

## Limites e próximo gate

`full_cpp_ast_or_cfg_proven=false`, `runtime_extension_names=NOT_VERIFIED`, `source_to_signed_elf_equivalence=UNVERIFIED`, `raw_cpp_source_exported=false`, `private_signing_material_accessed=false`, `apk_modified=false`, `fps_gain_proven=false`. PRE702 declarou `VK_GOOGLE_display_timing=ADVERTISED` no driver Xclipse 940; isso **não prova** solicitação/habilitação dessa extensão no `VkDevice`, uso de suas funções ou timestamps.

**PRE711 proposta:** auditoria source-only autenticada que associe os dois membros do receptor `c_str()` à variável de iteração/struct e identifique de maneira segura o operando do `==`, a condição negada e o destino de `push_back`. Se possível, extrair metadados de AST C++ com toolchain do SDK preservado, sem exportar fonte privado nem assumir que macros/aliases estejam resolvidos. Qualquer instrumentação em APK diagnóstica é **decisão futura distinta**, com fallback compatível e sem habilitar extensão a cegas.

**Base mantida:** V51 instalada, pacote `io.github.nfsmwrecomp`, `versionCode=51`, certificado permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, 1920×1080, shaders/efeitos/física, touch/iPega PG-9076, saves e proteção térmica. Nenhuma V52, alteração de MAILBOX ou ganho FPS comprovado.

**STATUS:** `PRE710_REAL_KAGGLE_PASS; FIRST_GUARDS_HAVE_CONTINUE; SECOND_GUARDS_HAVE_EMPLACE; INSTANCE_SECOND_BODY_PUSH_BACK_EXTRA; C_STR_MEMBER_RECEIVER_2_IDENTIFIERS_SHA_EQUAL; REQUESTED_EXTENSIONS_EQ; EXACT_PREDICATE_NOT_RESOLVED; RUNTIME_UNVERIFIED; NO_V52; NO_FPS_GAIN`.
