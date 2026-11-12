# PRE703 — auditoria de fonte V51 para VK_GOOGLE_display_timing (preparada; Colab pendente)

**Estado em 2026-11-12:** `PRE703_PY_COMPILE_PASS`; `PRE703_SYNTHETIC_7_PASS`; `PRE703_REAL_COLAB_SOURCE_NOT_YET_AUDITED`; sem APK V52.

## Evidência motivadora
A PRE702 foi executada no Galaxy S24 FE; o usuário enviou `PRE702_SUMMARY.txt` reportando 165 extensões e **`VK_GOOGLE_display_timing=ADVERTISED`** junto a `VK_KHR_swapchain=ADVERTISED`, e **`VK_EXT_present_timing=NOT_ADVERTISED`**. O JSON bruto com SHA256 informado `f61716212d02d557838c03c7b7297fdc8977fe8454b032c8033f8d76bf995496`, 116.765 bytes, ainda **não** foi enviado para conferência independente. Ver [checkpoint PRE702](PRE702_V51_VULKAN_DEVICE_EXTENSION_PREFLIGHT_READONLY_20261112.md).

Segundo a [especificação Khronos](https://docs.vulkan.org/refpages/latest/refpages/source/VK_GOOGLE_display_timing.html), `VK_GOOGLE_display_timing` exige `VK_KHR_swapchain` e oferece `vkGetPastPresentationTimingGOOGLE` e `vkGetRefreshCycleDurationGOOGLE`; a consulta entrega `VkPastPresentationTimingGOOGLE` com `presentID`, `actualPresentTime`, `earliestPresentTime` e `presentMargin`, usando [relógio monotônico](https://docs.vulkan.org/refpages/latest/refpages/source/vkGetPastPresentationTimingGOOGLE.html). O simples anúncio não habilita o recurso no jogo nem valida clock interdomínio/pareamento com SurfaceFlinger. `VK_KHR_present_wait2` [não fornece timing pixel-accurate](https://docs.vulkan.org/refpages/latest/refpages/source/VK_KHR_present_wait2.html), nem substitui a consulta GOOGLE.

## Auditoria preparada sem escrever no código

- [Script público de auditoria somente leitura](https://github.com/Juniklx/nfsmw-actions-teste/blob/main/automation/colab/nfsmw_pre703_v51_google_timing_source_audit.py), commit `9574d15cb4200c072a2ef985bd54eef1ce5badcd`, 5.806 bytes, SHA256 **`de0cd136c61465a898228275ccc6342f344d23e7999042c03e4c15f93ea15330`**.
- [Ferramentas ZIP no Drive](https://drive.google.com/file/d/1xki9QI1GDr51TuyPsYo7zWEOzE_3KAYh/view) (4.143 bytes, ZIP CRC PASS local), SHA256 **`3a1c9abb78fb69ffc73ebff1f4be5185e23d46e78509292cca8673fa45c4887b`**; inclui script e guia Colab.
- [Guia Colab no Drive](https://drive.google.com/file/d/1sVWP2AyqVCHIJMUo1m9w-7aoAvIx4uHK/view).
- `py_compile` e sete invariantes locais `--self-test` aprovados. **Sem execução real Colab**.

O script lê somente os bytes da fonte ativa `/content/nfsmw_build/NFSMW-Recompiled-Mobile-main/nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` (e header opcional), compara SHA256 com a **receita V51 autenticada** `68998a1db81e9743197e446a5f8dacbf8d3dbcc2a51e4a7e6dac476b87d88c48` do PRE697, e indexa ocorrências de nomes de função/extensão por número de linha. Salva **apenas** JSON agregado com nome único no Drive `06_Logs_e_Medicoes`. `BLOCK_...` significa que é proibido inferir layout e aplicar patch. **Igualdade de código-fonte da receita não significa equivalência byte a byte com `libmain.so` assinada**. O script não imprime nem modifica código, chaves, Gradle ou arquivos antigos.

## Próxima decisão após execução real

Reconciliar fingerprints e âncoras, estudar o local de `vkCreateDevice` e swapchain/presentação. Se viável, discutir posteriormente instrumentação diagnóstica reversível em versão **incrementada e assinada pela mesma chave**, ativando apenas consulta de feedback, com overhead limitado e IDs comuns; não mudar `MAILBOX` ou `desiredPresentTime` na experiência de medição inicial. O colab ainda não executou qualquer gate; qualquer build V52 permanece **não iniciada**.

Preservar V51, package `io.github.nfsmwrecomp`, certificado SHA-256 `1ba7bda576cca036f8cb18f496bf7b04e65ff76da43d5c788291059d930d104b`, resolução interna 1920×1080, 60 FPS cap do ensaio PRE700, alvo máximo 120 FPS, gráficos/shaders/efeitos/física, touch/PG-9076, saves e proteções térmicas.

**STATUS:** `PRE702_GOOGLE_TIMING_REPORTED_ADVERTISED; PRE703_SOURCE_READONLY_SCRIPT_STAGED; COLAB_NOT_EXECUTED; NO_CAUSALITY; NO_FPS_GAIN; NO_NEW_APK`.


---

## Correção de ambiente — Kaggle é o executor atual (12/11/2026)

**Retificação importante solicitada pelo usuário:** a seção original PRE703 acima foi criada por engano para Google Colab. O fluxo atual usa **Kaggle Notebook `juniklx/nfsmw`**, com scripts de `automation/kaggle` e sincronização seletiva dos logs para o Google Drive. O caminho `/content/nfsmw_build` e `google.colab.drive.mount` **não são válidos para a execução atual**. **NÃO executar** o comando/célula de Colab PRE703 fornecido anteriormente.

Substituto preparado em [`automation/kaggle/nfsmw_pre703_v51_source_readonly.py`](../automation/kaggle/nfsmw_pre703_v51_source_readonly.py), commit `9dec0fa46a958f22a9c18f33f500b6052082776a`. Executar em uma célula Python do Kaggle usando URL `raw.githubusercontent.com` pinada nesse commit, sem Google Drive mount. O script tenta localizar `nativo/sdk/src/ui/vulkan/vulkan_presenter.cpp` em `/kaggle/working` e `/kaggle/input`, ou aceita `--source-root` **somente quando já existe fonte autenticada no workspace**. Salva `NFSMW_PRE703_KAGGLE_SOURCE_AUDIT_*.json` em `/kaggle/working/NFSMW_Kaggle_Logs`, que é o diretório esperado pelo fluxo Kaggle AutoLog conhecido; não assumir que o upload ao Drive ocorreu sem conferir. Não lê segredos, não baixa snapshots, não recompila ou modifica APK.

**Gate fail-closed:** nenhum candidato -> `BLOCK_NO_SOURCE_IN_KAGGLE`; muitos -> `BLOCK_MULTIPLE_SOURCE_CANDIDATES`; hash divergente -> `BLOCK_SOURCE_NOT_AUTHENTICATED_AS_V51_RECIPE`; correspondência hash/âncora -> apenas `PASS_V51_RECIPE_SOURCE_ONLY`, não equivalência com ELF assinado nem acesso efetivo a timestamps GPU. **Não restaurar por conta própria um backup V20/V50 como se fosse V51**, não aplicar patch sem hash. PRE703 ainda não executada no Kaggle real.

A sonda anterior de Colab permanece apenas como arquivo histórico para auditabilidade, **substituída** pela versão Kaggle. A correção de ambiente não muda o resultado real da PRE702 (extensão `VK_GOOGLE_display_timing` anunciada segundo resumo enviado pelo usuário) nem autoriza V52 ou alteração de segurança térmica, gráficos, saves ou chave permanente.
