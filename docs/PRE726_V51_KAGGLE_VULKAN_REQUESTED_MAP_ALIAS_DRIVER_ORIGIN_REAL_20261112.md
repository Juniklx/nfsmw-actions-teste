# PRE726 — V51 Vulkan: cadeia requested_extensions.find → alias → ->first.c_str() (2026-11-12)

## Histórico, autenticação e resultados reais

- **Primeira tentativa:** GitHub Actions [43307018613](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43307018613) `completed/failure`; Kaggle executou a sonda, mas o gate gerou `BLOCK_PRE726_REQUESTED_MAP_ALIAS_ORIGIN_UNRESOLVED` porque seu parser supunha uma forma excessivamente específica para atribuições `auto`. Esse resultado **não foi aprovado**. O JSON do bloqueio preservou as linhas de enumeração; o ZIP de 23.993 bytes tem SHA-256 `877f71b8bcb981a0032cbf07303c2af1bf3371e48ecf1fe55790c3912fb051fe`, [arquivado no Drive](https://drive.google.com/file/d/1sR6Ni46Ecw25Fc9FGu2rBhP6LtCrlzpz/view).
- **Correção pontual:** commit `a672ff78c0f9903a83613019e1a11b2d59f51b15` em `automation/kaggle/pre726_generate_private_v51_kernel.py`; aceitar a atribuição limitada até o ponto e vírgula em vez de exigir `auto ident = requested_extensions.find(...)` na mesma linha. Não altera o código C++ do jogo.
- **Execução aprovada:** GitHub Actions [43307644388](https://github.com/Juniklx/nfsmw-actions-teste/actions/runs/43307644388) `completed/success`; notebook isolado Kaggle privado `juniklx/nfsmw-pre726-v51-requested-driver-origin`; artifact GitHub **13985075924**.
- **Relatório:** `NFSMW_PRE726_REAL_KAGGLE_VERIFIED_43307644388.zip`, **47.980 bytes**, SHA-256 **`6b6cef8af0385b2ab8efe1501a0064ad5562ae1923db9bec457b15a3b47f6bf7`**. CRC `PASS`; `PRE726_V51_KAGGLE_VALIDATED_SUMMARY.json` e `NFSMW_PRE726_KAGGLE_REMOTE.json` são idênticos byte a byte; `status=PASS_PRE726_V51_REQUESTED_MAP_ALIAS_ORIGIN_AUDIT`; [ZIP autenticado, arquivado e baixado novamente do Drive](https://drive.google.com/file/d/12C2kHP0ZAOMONEu2bSt3JFlCnfxVuGzm/view).
- Fonte V51 privada autenticada pela receita PRE704/PRE99. `vulkan_instance.cpp` SHA256 `700a0fa890d593e937d7eab89c6892b05a92470a779be469c5aa796287c3fd04`. **Não há evidência byte a byte** de equivalência da fonte com a `libmain.so` da APK V51 assinada.

## Constatações lexicais verificadas

| Relação | Dispositivo (`vulkan_device.cpp`) | Instância (`vulkan_instance.cpp`) |
|---|---|---|
| Chamadas a enumeradores de extensões Vulkan antes do laço | `vkEnumerateDeviceExtensionProperties` **267, 276** | `vkEnumerateInstanceExtensionProperties` **315, 325, 416, 426** (próximas ao laço: 416, 426) |
| Laço contendo token `VkExtensionProperties` e expressão range com identificador | **283** | **445** |
| Atribuição de alias derivada de `requested_extensions.find(...)`, com `extensionName` no inicializador | **284** | **446** |
| `enabled_extensions.emplace_back(...)` utiliza o **mesmo alias textual** seguido de membro `first` e `.c_str()` | **291** | **455** |

Evidências:
- `requested_find_assignments_in_branch=1` em cada contexto e `requested_find_alias_matches_emplace_cstr_receiver=true` nos dois.
- `cstr_uses_requested_map_first_member=true` nos dois (hash publicado para o membro por PRE711 `a7937b64b8caa58f03721bb6bacf5c78cb235febe0e70b1b84cd99541461a08e`, corresponde à palavra pública `first`; não foi exportado identificador privado).
- `lookup_mentions_extensionName=true`; variável do `for` difere da variável da atribuição `find`. Prefixo lexical registrado por PRE712/PRE713 corrobora a atribuição.
- `Vulkan_driver_extension_enumeration_call_before_loop=true` nas duas fontes, mas **`enumeration_dataflow_to_range_proven=false`**: a mera presença de chamadas antes do laço não confirma, sozinha, a origem exata do contêiner iterado.
- Os dois contextos Vulkan são distintos, mesmo que compartilhem argumento textual semelhante. PRE725 confirmou `VkInstanceCreateInfo` e `vkCreateInstance` para o caso de instância. A verificação de device conta com PRE705–PRE706.

## Interpretação técnica e limites

A análise estabelece a **cadeia lexical** de seleção para listas habilitadas: um registro com `extensionName` é procurado em `requested_extensions`; o alias retornado dessa busca é aquele cujo membro `first` recebe `.c_str()` na inserção de `enabled_extensions`. Isso é consistente com preservar a string da chave do mapa de extensões solicitadas. Não é uma prova de que a busca teve sucesso, de que os ponteiros permaneçam válidos nem de qual valor foi passado ao driver em runtime. As condições que pulam registros não solicitados e a possível estratégia fallback da instância permanecem inferências de estrutura de código, não comportamento executado.

**Não demonstrado:** AST/CFG real, proveniência integral do buffer anunciado pelo driver até o laço, nomes concretos `VK_...` habilitados na V51, habilitação de `VK_GOOGLE_display_timing`, retorno das chamadas Vulkan no Galaxy S24 FE ou ganho de FPS. Nenhuma anomalia Vulkan foi demonstrada que justifique patch.

## Próximo gate PRE727

Priorizar informação realmente nova em vez de repetir regex: verificar com segurança **o que a V51 efetivamente solicita e habilita em runtime**, diferenciando `vkEnumerate...` (suporte anunciado), `requested_extensions` (solicitações da aplicação) e `enabled_extensions` passado a `vkCreateInstance`/`vkCreateDevice`. Primeiro avaliar logs já existentes da V51, sem dados sensíveis ou alterações de app; quando necessário, planejar diagnóstico somente leitura que não exija recompilar a V52. Se não houver dados suficientes, manter `NOT_VERIFIED`, sem afirmar que `VK_GOOGLE_display_timing` está ativada. Outra opção é confirmar o fluxo de dados usando AST real com toolchain autenticada, em vez de apresentar regex como AST.

**Preservação:** APK **V51**, `io.github.nfsmwrecomp`, `versionCode=51`, assinatura permanente SHA256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, gráficos completos 1920×1080, meta 120 FPS, touch, iPega PG-9076, shaders, saves e proteções térmicas. Sem modificação de fonte/APK, sem V52, sem acesso a material de assinatura, sem ganho de FPS comprovado.

**STATUS:** `PRE726_REAL_KAGGLE_PASS_AFTER_BOUNDED_ASSIGNMENT_PARSER_FIX; DRIVER_ENUMERATORS_SEEN; REQUESTED_FIND_ALIAS284_446; ALIAS_MATCHES_CSTR_FIRST_IN_EMPLACE291_455; NOT_AST_CFG; NOT_RUNTIME_ENABLED; SOURCE_SIGNED_ELF_UNVERIFIED; V51_INTACT; NO_V52; NO_FPS_GAIN`.
