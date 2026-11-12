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
